"""Pure decisions over a batch of operations, taken on plain envelope data (ADR-0007 section 3)."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from itertools import pairwise
from typing import assert_never
from uuid import UUID

from mapsift.layers.rules import (
    GeometryKind,
    TheCurrentStateOfAFeature,
    TheDeclarationsOfALayer,
    enters_the_operation_queue,
    geometry_is_admissible,
)
from mapsift.sync.envelope import (
    ClientHalf,
    FeatureAddress,
    FeatureCreateOperation,
    FeatureGeometrySetOperation,
    FeatureGeometrySetPayload,
    PropertyAddress,
)

THE_FIRST_MUTATION_NUMBER = 0


class MalformedBatch(Exception):
    """A batch refused before anything is verified or bound (ADR-0010 decision 6).

    The base every such refusal carries, so a boundary catches the set instead of listing it.
    """


class OperationsDisagreeOnTheirTenant(MalformedBatch):
    """Raised when one batch addresses more than one tenant (ADR-0010 decision 6)."""


class BatchClaimsNoTenant(MalformedBatch):
    """Raised when a batch carries no operation, so it names no tenant (ADR-0010 decision 6)."""


class OperationsDisagreeOnTheirProject(MalformedBatch):
    """Raised when one batch addresses more than one project (ADR-0010 decision 6)."""


class OperationsDisagreeOnTheirClient(MalformedBatch):
    """Raised when one batch comes from more than one installation (ADR-0010 decision 6)."""


class OperationsAreNotOneContiguousStream(MalformedBatch):
    """Raised when a batch's mutation numbers do not ascend by exactly one at every step (M10).

    One refusal for every way that can happen, a hole and a shuffle and a repeat alike, because a
    client's remedy is the same for all three: go and find the stream it actually authored.
    """


class WhyAStreamCannotBeContinued(StrEnum):
    """The closed set a whole-batch refusal names, both of whose remedies are a resend (ADR-0010
    decision 6's addition of 2026-08-13, as ADR-0014 decision 2 leaves it)."""

    GAP_ABOVE_CURSOR = "gap_above_cursor"
    NO_CURSOR_IN_THIS_DOMAIN = "no_cursor_in_this_domain"


class WhyAnOperationWasRefused(StrEnum):
    """The closed set a verdict on one operation names, whose remedy is on no wire at all: the
    client's queue is append-only, so resending reproduces the answer (ADR-0014 decisions 2 and 6).
    """

    NO_LAYER_IN_THIS_PROJECT = "no_layer_in_this_project"
    SERVED_LAYER_TAKES_NO_OPERATIONS = "served_layer_takes_no_operations"
    GEOMETRY_OUTSIDE_THE_LAYERS_FAMILY = "geometry_outside_the_layers_family"


class ThisStreamCannotBeContinued(Exception):
    """Raised when a batch does not carry on from where this installation left off (M10, M4).

    Not a `MalformedBatch`: the batch satisfies the contract the boundary declares, and the cursor
    it is measured against needs the tenant bound, so this refusal is taken after the binding and
    the route answers it differently from those (ADR-0010 decision 6's addition of 2026-08-13).
    """

    def __init__(
        self,
        reason: WhyAStreamCannotBeContinued,
        *,
        resend_from_mutation_number: int | None,
    ) -> None:
        super().__init__(
            f"This installation's stream cannot be continued here ({reason}), and the mutation "
            f"number it must resend from is {resend_from_mutation_number} (ADR-0010 decision 6's "
            f"addition of 2026-08-13)."
        )
        self.reason = reason
        self.resend_from_mutation_number = resend_from_mutation_number


def the_tenant_every_operation_claims(operations: Sequence[ClientHalf]) -> UUID:
    """The one tenant a batch addresses, refusing rather than reading the first one it finds."""
    claimed = {the_address_of(operation).tenant_id for operation in operations}
    if len(claimed) == 1:
        return claimed.pop()
    if not claimed:
        raise BatchClaimsNoTenant(
            "A batch of no operations names no tenant at all, so there is nothing to verify and "
            "nothing to bind (ADR-0010 decision 6)."
        )
    raise OperationsDisagreeOnTheirTenant(
        f"One batch addressed {len(claimed)} tenants and a flush addresses exactly one "
        f"(ADR-0010 decision 6)."
    )


def the_project_every_operation_claims(operations: Sequence[ClientHalf]) -> UUID:
    """The one project a batch addresses, refusing rather than reading the first one it finds.

    Answers for a batch that already named one tenant, which is what makes an empty one somebody
    else's refusal: it claims no tenant either, and that one is taken first (ADR-0010 decision 6).
    """
    claimed = {the_address_of(operation).project_id for operation in operations}
    if len(claimed) == 1:
        return claimed.pop()
    raise OperationsDisagreeOnTheirProject(
        f"One batch addressed {len(claimed)} projects and a flush addresses exactly one "
        f"(ADR-0010 decision 6's addition of 2026-08-10)."
    )


def the_client_every_operation_claims(operations: Sequence[ClientHalf]) -> UUID:
    """The one installation a batch comes from, refusing rather than reading the first one it finds.

    Answers for a batch that already named one tenant and one project, which is the order
    ADR-0010 decision 6's addition of 2026-08-11 fixes.
    """
    claimed = {operation.root.client_id for operation in operations}
    if len(claimed) == 1:
        return claimed.pop()
    raise OperationsDisagreeOnTheirClient(
        f"One batch came from {len(claimed)} installations and a flush addresses exactly one "
        f"(ADR-0010 decision 6's addition of 2026-08-11)."
    )


def the_mutation_number_this_unbroken_stream_starts_at(operations: Sequence[ClientHalf]) -> int:
    """The number a batch's stream opens on, refusing a batch that is not one unbroken stream.

    Answers for a batch that already named one tenant, one project and one installation, which is
    the order ADR-0010 decision 6's addition of 2026-08-13 fixes.
    """
    numbers = [the_mutation_number_of(operation) for operation in operations]
    for earlier, later in pairwise(numbers):
        if later != earlier + 1:
            raise OperationsAreNotOneContiguousStream(
                f"One batch's mutation numbers ascend by exactly one at every step and these do "
                f"not, {later} following {earlier} (ADR-0010 decision 6's addition of 2026-08-13)."
            )
    return numbers[0]


@dataclass(frozen=True, slots=True)
class OneUnbrokenStream:
    """The flush domain a batch addresses and the mutation number its stream opens on (M10, M4).

    Holding one is the proof that every composition rule passed, because the function below is
    what constructs it (ADR-0010 decision 6).
    """

    tenant_id: UUID
    project_id: UUID
    client_id: UUID
    starts_at_mutation_number: int


def the_one_unbroken_stream_this_batch_carries(
    operations: Sequence[ClientHalf],
) -> OneUnbrokenStream:
    """The one stream a batch carries, refusing a batch that is not one (ADR-0010 decision 6).

    The single place the composition rules are listed, so a sixth is added here alone and every
    caller inherits it in its ratified position.
    """
    # These four look independent and reorderable and are not: the order is contract, ratified in
    # ADR-0010 decision 6 with its additions of 2026-08-11 and 2026-08-13, and moving one hands a
    # batch that breaks two rules the refusal belonging to the other.
    tenant_id = the_tenant_every_operation_claims(operations)
    project_id = the_project_every_operation_claims(operations)
    client_id = the_client_every_operation_claims(operations)
    starts_at = the_mutation_number_this_unbroken_stream_starts_at(operations)

    return OneUnbrokenStream(
        tenant_id=tenant_id,
        project_id=project_id,
        client_id=client_id,
        starts_at_mutation_number=starts_at,
    )


def refuse_a_stream_this_cursor_cannot_continue(
    starts_at: int, already_decided: int | None
) -> None:
    """Let a batch through only where it carries on from this installation's cursor (M10, M4).

    A batch at or below the cursor carries on trivially and is the dedup's (T2.3); what is refused
    is a batch opening above the first number the server still needs.
    """
    if already_decided is None and starts_at != THE_FIRST_MUTATION_NUMBER:
        raise ThisStreamCannotBeContinued(
            WhyAStreamCannotBeContinued.NO_CURSOR_IN_THIS_DOMAIN,
            resend_from_mutation_number=None,
        )
    if already_decided is not None and starts_at > already_decided + 1:
        raise ThisStreamCannotBeContinued(
            WhyAStreamCannotBeContinued.GAP_ABOVE_CURSOR,
            resend_from_mutation_number=already_decided + 1,
        )


def this_cursor_has_seen(operation: ClientHalf, already_decided: int | None) -> bool:
    """Whether one operation is at or below a cursor, an absent cursor having seen nothing (T2.3).

    The one boundary both partitions below read, so moving it cannot leave the flush writing an
    operation the trail records as dropped. The absence is `None` rather than a number, because
    zero is the first mutation number and so a legitimate decided value rather than an available
    sentinel (M4's Shape, M10's Shape).
    """
    if already_decided is None:
        return False
    return the_mutation_number_of(operation) <= already_decided


def the_operations_this_cursor_has_not_seen(
    operations: Sequence[ClientHalf], already_decided: int | None
) -> list[ClientHalf]:
    """The operations of a batch above the cursor, which the flush decides (T2.3)."""
    return [
        operation
        for operation in operations
        if not this_cursor_has_seen(operation, already_decided)
    ]


def the_operations_this_cursor_has_already_seen(
    operations: Sequence[ClientHalf], already_decided: int | None
) -> list[ClientHalf]:
    """The operations of a batch at or below the cursor, which the dedup drops (T2.3)."""
    return [
        operation for operation in operations if this_cursor_has_seen(operation, already_decided)
    ]


def the_last_decided_mutation_number_this_flush_leaves(
    operations: Sequence[ClientHalf], already_decided: int | None
) -> int:
    """The number a flush echoes: the highest of the cursor it found and the batch it carried.

    Decided rather than applied, which is the axis this counts on: the cursor passes an operation
    the flush refused exactly as it passes one it applied, so a refused operation is deduplicated
    on a resend and the stream behind it is never stalled (ADR-0014 decision 5, T2.3, M4).

    A batch deduplicated away entirely therefore answers with the cursor it did not move (T2.3).
    """
    reached = [the_mutation_number_of(operation) for operation in operations]
    if already_decided is not None:
        reached.append(already_decided)
    return max(reached)


def the_operation_identifiers_in(operations: Sequence[ClientHalf]) -> tuple[UUID, ...]:
    """The identifier of every operation in a batch, in the order the client authored them.

    The join key of PRD N9's decision trail, read in one place so a record and a log entry cannot
    disagree about how an operation is named.
    """
    return tuple(operation.root.operation_id for operation in operations)


def the_address_of(operation: ClientHalf) -> FeatureAddress | PropertyAddress:
    """The target path an operation addresses, past the wrappers the generator writes (M9)."""
    return operation.root.target.root


def the_mutation_number_of(operation: ClientHalf) -> int:
    """The per-client axis an operation carries, past the wrappers the generator writes (M10)."""
    return operation.root.mutation_number.root


def the_layers_this_batch_addresses(operations: Sequence[ClientHalf]) -> frozenset[UUID]:
    """Every layer a batch's operations name (M2, M9).

    Read from the operations and never from the state they fold to, because that fold is one row
    per feature and a guard fed from it inherits every loss (ADR-0012 decision 3).
    """
    return frozenset(the_address_of(operation).layer_id for operation in operations)


@dataclass(frozen=True, slots=True)
class TheRefusalOfAnOperation:
    """One operation of a batch the server will not apply, and why (ADR-0014 decision 1)."""

    operation_id: UUID
    mutation_number: int
    reason: WhyAnOperationWasRefused


def the_refusals_this_batch_earns(
    operations: Sequence[ClientHalf],
    *,
    layers_the_project_holds: Mapping[UUID, TheDeclarationsOfALayer],
) -> list[TheRefusalOfAnOperation]:
    """What the server refuses of a batch, one verdict per operation, in the order it was given.

    A refusal here judges what the client authored against server state it could not have known,
    which is the criterion that keeps it off the whole batch: the queue is append-only, so nothing
    the client can send changes the answer, and refusing the batch would stall the stream
    permanently (ADR-0014 decision 1, I2).

    Each operation is judged on the layer it names and the geometry it carries, both read from the
    operation and never from the state the batch folds to, which is the reason
    `the_layers_this_batch_addresses` gives for itself (ADR-0012 decision 3).
    """
    refusals: list[TheRefusalOfAnOperation] = []
    for operation in operations:
        reason = the_reason_an_operation_is_refused_for(operation, layers_the_project_holds)
        if reason is not None:
            refusals.append(
                TheRefusalOfAnOperation(
                    operation_id=operation.root.operation_id,
                    mutation_number=the_mutation_number_of(operation),
                    reason=reason,
                )
            )
    return refusals


def the_reason_an_operation_is_refused_for(
    operation: ClientHalf, layers_the_project_holds: Mapping[UUID, TheDeclarationsOfALayer]
) -> WhyAnOperationWasRefused | None:
    """The one reason an operation is refused for, or None where its layer's declarations admit it.

    An operation failing more than one rule carries the first in the order ADR-0010 decision 6's
    addition of 2026-09-23 fixes as contract: the layer held, then its class, then its family.
    """
    declarations = layers_the_project_holds.get(the_address_of(operation).layer_id)
    if declarations is None:
        return WhyAnOperationWasRefused.NO_LAYER_IN_THIS_PROJECT
    if not enters_the_operation_queue(declarations.storage_class):
        return WhyAnOperationWasRefused.SERVED_LAYER_TAKES_NO_OPERATIONS
    if carries_a_geometry_outside_the_family(operation, declarations.geometry_kind):
        return WhyAnOperationWasRefused.GEOMETRY_OUTSIDE_THE_LAYERS_FAMILY
    return None


def carries_a_geometry_outside_the_family(operation: ClientHalf, family: GeometryKind) -> bool:
    """Whether an operation carries a geometry declaring a type outside a family (M2, M9).

    Read off the declared `type` alone and never by parsing. False for an operation carrying no
    geometry, whether it states nothing of one or states there is none, since neither is outside any
    family; and false for a geometry no type can be read off, which is not checked for a family at
    all (ADR-0010 decision 6's addition of 2026-09-23).
    """
    stated = the_geometry_payload_of(operation)
    if stated is None or stated.geometry is None:
        return False
    declared_type = the_type_a_geometry_declares(stated.geometry)
    if declared_type is None:
        return False
    return not geometry_is_admissible(layer_kind=family, geometry_type=declared_type)


def the_type_a_geometry_declares(geometry: object) -> str | None:
    """The `type` a GeoJSON-shaped structure declares for itself, or None where it declares none
    this rule can read: not a mapping, no `type`, or a `type` that is not a string."""
    if not isinstance(geometry, Mapping):
        return None
    declared = geometry.get("type")
    return declared if isinstance(declared, str) else None


def the_operations_no_refusal_names(
    operations: Sequence[ClientHalf], refusals: Sequence[TheRefusalOfAnOperation]
) -> list[ClientHalf]:
    """The operations of a batch the flush applies, which is every one no verdict refused.

    Nothing is refused for being downstream of a refusal, so this keeps the order it was given and
    drops only what a verdict names (ADR-0014 decision 7).
    """
    refused = {refusal.operation_id for refusal in refusals}
    return [operation for operation in operations if operation.root.operation_id not in refused]


def the_geometry_payload_of(operation: ClientHalf) -> FeatureGeometrySetPayload | None:
    """The payload an operation states its feature's whole geometry in, or None where it states
    nothing about that geometry at all (M9).

    The one place the catalog is read for the geometry an operation carries, so the family check and
    the projection cannot disagree about which operation carried which geometry.
    """
    authored = operation.root
    match authored:
        case FeatureCreateOperation():
            # No payload, never a payload carrying null: a create says nothing of the geometry and
            # leaves the stored column alone, while a set carrying null says there is none and is
            # written (ADR-0012 decision 3's addition of 2026-09-09).
            return None
        case FeatureGeometrySetOperation():
            return authored.payload
        case _:
            # A catalog member added later lands here and fails the type check until somebody
            # decides what geometry it carries, which a fallback would decide for them.
            assert_never(authored)


def the_current_state_this_batch_leaves(
    operations: Sequence[ClientHalf],
) -> list[TheCurrentStateOfAFeature]:
    """The current state a batch leaves behind it, one row per feature its operations address.

    The latest row per target path rather than a fold over deltas, which is what M9's
    whole-geometry rule makes correct (M15, ADR-0012 decision 1). A feature the batch spoke no
    geometry for says so and carries none, leaving the write to decide what that means for a
    column already holding one (that decision's addition of 2026-09-09).
    """
    addressed: dict[UUID, FeatureAddress | PropertyAddress] = {}
    spoken: dict[UUID, object | None] = {}

    for operation in operations:
        address = the_address_of(operation)
        addressed[address.feature_id] = address
        stated = the_geometry_payload_of(operation)
        if stated is not None:
            spoken[address.feature_id] = stated.geometry

    return [
        TheCurrentStateOfAFeature(
            tenant_id=address.tenant_id,
            project_id=address.project_id,
            layer_id=address.layer_id,
            feature_id=feature_id,
            geometry=spoken.get(feature_id),
            the_batch_spoke_of_its_geometry=feature_id in spoken,
        )
        for feature_id, address in addressed.items()
    ]
