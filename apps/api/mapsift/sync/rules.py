"""Pure decisions over a batch of operations, taken on plain envelope data (ADR-0007 section 3)."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from itertools import pairwise
from typing import assert_never
from uuid import UUID

from mapsift.layers.rules import (
    TheCurrentStateOfAFeature,
    WhatALayerDeclares,
    enters_the_operation_queue,
    geometry_is_admissible,
)
from mapsift.sync.envelope import (
    ClientHalf,
    FeatureAddress,
    FeatureCreateOperation,
    FeatureGeometrySetOperation,
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
    """The closed set a refusal names, whose remedies differ (ADR-0010 decision 6's addition of
    2026-08-13, its addition of 2026-09-08 for the third and that of 2026-09-15 for the fourth
    and fifth)."""

    GAP_ABOVE_CURSOR = "gap_above_cursor"
    NO_CURSOR_IN_THIS_DOMAIN = "no_cursor_in_this_domain"
    NO_LAYER_IN_THIS_PROJECT = "no_layer_in_this_project"
    SERVED_LAYER_TAKES_NO_OPERATIONS = "served_layer_takes_no_operations"
    GEOMETRY_OUTSIDE_THE_LAYERS_FAMILY = "geometry_outside_the_layers_family"


class ThisStreamCannotBeContinued(Exception):
    """Raised when a batch does not carry on from where this installation left off (M10, M4).

    Not a `MalformedBatch`: the batch satisfies the contract the boundary declares, and the cursor
    it is measured against needs the tenant bound, so this refusal is taken after the binding and
    the route answers it differently from those (ADR-0010 decision 6's addition of 2026-08-13).

    It names the operation it refused where the operation is the unit of the fault, and names none
    where the container is (that decision's addition of 2026-09-15).
    """

    def __init__(
        self,
        reason: WhyAStreamCannotBeContinued,
        *,
        resend_from_mutation_number: int | None,
        refused_operation_id: UUID | None,
    ) -> None:
        super().__init__(
            f"This installation's stream cannot be continued here ({reason}), the mutation "
            f"number it must resend from is {resend_from_mutation_number} and the operation "
            f"refused is {refused_operation_id} (ADR-0010 decision 6's additions of 2026-08-13 "
            f"and 2026-09-15)."
        )
        self.reason = reason
        self.resend_from_mutation_number = resend_from_mutation_number
        self.refused_operation_id = refused_operation_id


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
    starts_at: int, already_applied: int | None
) -> None:
    """Let a batch through only where it carries on from this installation's cursor (M10, M4).

    A batch at or below the cursor carries on trivially and is the dedup's (T2.3); what is refused
    is a batch opening above the first number the server still needs.
    """
    if already_applied is None and starts_at != THE_FIRST_MUTATION_NUMBER:
        raise ThisStreamCannotBeContinued(
            WhyAStreamCannotBeContinued.NO_CURSOR_IN_THIS_DOMAIN,
            resend_from_mutation_number=None,
            refused_operation_id=None,
        )
    if already_applied is not None and starts_at > already_applied + 1:
        raise ThisStreamCannotBeContinued(
            WhyAStreamCannotBeContinued.GAP_ABOVE_CURSOR,
            resend_from_mutation_number=already_applied + 1,
            refused_operation_id=None,
        )


def this_cursor_has_seen(operation: ClientHalf, already_applied: int | None) -> bool:
    """Whether one operation is at or below a cursor, an absent cursor having seen nothing (T2.3).

    The one boundary both partitions below read, so moving it cannot leave the flush writing an
    operation the trail records as dropped. The absence is `None` rather than a number, because
    zero is the first mutation number and so a legitimate applied value rather than an available
    sentinel (M4's Shape, M10's Shape).
    """
    if already_applied is None:
        return False
    return the_mutation_number_of(operation) <= already_applied


def the_operations_this_cursor_has_not_seen(
    operations: Sequence[ClientHalf], already_applied: int | None
) -> list[ClientHalf]:
    """The operations of a batch above the cursor, which the flush writes (T2.3)."""
    return [
        operation
        for operation in operations
        if not this_cursor_has_seen(operation, already_applied)
    ]


def the_operations_this_cursor_has_already_seen(
    operations: Sequence[ClientHalf], already_applied: int | None
) -> list[ClientHalf]:
    """The operations of a batch at or below the cursor, which the dedup drops (T2.3)."""
    return [
        operation for operation in operations if this_cursor_has_seen(operation, already_applied)
    ]


def the_last_applied_this_flush_leaves(
    operations: Sequence[ClientHalf], already_applied: int | None
) -> int:
    """The number a flush echoes: the highest of the cursor it found and the batch it carried.

    A batch deduplicated away entirely therefore answers with the cursor it did not move (T2.3).
    """
    reached = [the_mutation_number_of(operation) for operation in operations]
    if already_applied is not None:
        reached.append(already_applied)
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
class TheGeometryAnOperationCarries:
    """One operation's declared geometry type beside the layer it files that geometry under."""

    operation_id: UUID
    layer_id: UUID
    geometry_type: str


def the_geometries_this_batch_carries(
    operations: Sequence[ClientHalf],
) -> list[TheGeometryAnOperationCarries]:
    """Every operation of a batch whose payload declares a geometry type, as authored (M2, M9).

    Read from the operations and never from the state they fold to, because that fold keeps one
    geometry per feature and a guard fed from it never sees an earlier one (ADR-0012 decision 3).

    The type is the payload's own declaration and the geometry is never parsed, and an operation
    this cannot read a type out of is absent rather than present carrying nothing, which is what
    scopes the refusal downstream to a payload it can read a family out of (ADR-0010 decision 6's
    addition of 2026-09-15).
    """
    carried = []
    for operation in operations:
        declared = _the_geometry_type_declared_by(operation)
        if declared is None:
            continue
        carried.append(
            TheGeometryAnOperationCarries(
                operation_id=operation.root.operation_id,
                layer_id=the_address_of(operation).layer_id,
                geometry_type=declared,
            )
        )
    return carried


def _the_geometry_type_declared_by(operation: ClientHalf) -> str | None:
    authored = operation.root
    match authored:
        case FeatureCreateOperation():
            return None
        case FeatureGeometrySetOperation():
            geometry = authored.payload.geometry
        case _:
            # A catalog member added later lands here and fails the type check until somebody
            # decides whether it speaks of geometry, which a fallback would decide for them.
            assert_never(authored)

    if not isinstance(geometry, Mapping):
        return None
    declared = geometry.get("type")
    return declared if isinstance(declared, str) else None


def refuse_a_batch_its_layers_do_not_admit(
    operations: Sequence[ClientHalf], declared: Mapping[UUID, WhatALayerDeclares]
) -> None:
    """Let a batch through only where the layers it names admit its operations (M2, M9).

    `declared` answers for the layers this batch names, one its project does not hold being absent.
    """
    # Not three independent checks: the last indexes `declared` by layer and only the first proves
    # every layer is in it. The order is ADR-0010 decision 6's addition of 2026-09-15.
    _refuse_a_layer_this_project_does_not_hold(
        the_layers_this_batch_addresses(operations), declared
    )
    _refuse_an_operation_naming_a_served_layer(declared)
    _refuse_a_geometry_outside_the_family_its_layer_declares(operations, declared)


def _refuse_a_layer_this_project_does_not_hold(
    addressed: frozenset[UUID], declared: Mapping[UUID, WhatALayerDeclares]
) -> None:
    """Refuse the whole batch where it files a feature under a layer this project does not hold.

    Taken here rather than left to the composite reference, whose refusal is an `IntegrityError`
    escaping as a 500 (ADR-0010 decision 6's addition of 2026-09-08). The restart point is null
    because resending reproduces this refusal: the remedy is the layer, not the stream.
    """
    if addressed <= declared.keys():
        return

    raise ThisStreamCannotBeContinued(
        WhyAStreamCannotBeContinued.NO_LAYER_IN_THIS_PROJECT,
        resend_from_mutation_number=None,
        refused_operation_id=None,
    )


def _refuse_an_operation_naming_a_served_layer(
    declared: Mapping[UUID, WhatALayerDeclares],
) -> None:
    """Refuse the whole batch where it names a layer whose features never enter the queue (M2).

    It names no operation, the unit of the fault being the layer rather than any one operation
    naming it (ADR-0010 decision 6's addition of 2026-09-15).
    """
    if all(enters_the_operation_queue(layer.storage_class) for layer in declared.values()):
        return

    raise ThisStreamCannotBeContinued(
        WhyAStreamCannotBeContinued.SERVED_LAYER_TAKES_NO_OPERATIONS,
        resend_from_mutation_number=None,
        refused_operation_id=None,
    )


def _refuse_a_geometry_outside_the_family_its_layer_declares(
    operations: Sequence[ClientHalf], declared: Mapping[UUID, WhatALayerDeclares]
) -> None:
    """Refuse the whole batch where one operation carries a geometry of a family its layer does
    not declare, naming that operation (M2, M9).

    The one refusal that names an operation, because M9's flag-and-retain clause needs a locus a
    reason code cannot carry (ADR-0010 decision 6's addition of 2026-09-15). The batch is refused
    whole all the same, so nothing is discarded (M10).
    """
    for carried in the_geometries_this_batch_carries(operations):
        if geometry_is_admissible(
            layer_kind=declared[carried.layer_id].geometry_kind,
            geometry_type=carried.geometry_type,
        ):
            continue

        raise ThisStreamCannotBeContinued(
            WhyAStreamCannotBeContinued.GEOMETRY_OUTSIDE_THE_LAYERS_FAMILY,
            resend_from_mutation_number=None,
            refused_operation_id=carried.operation_id,
        )


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
        authored = operation.root
        match authored:
            case FeatureCreateOperation():
                # Not an oversight and not a null to record: a create's payload carries nothing
                # beyond the address, so it makes no statement about the geometry at all, while a
                # set carrying null states there is none (ADR-0012 3's addition of 2026-09-09).
                pass
            case FeatureGeometrySetOperation():
                spoken[address.feature_id] = authored.payload.geometry
            case _:
                # A catalog member added later lands here and fails the type check until somebody
                # decides what it leaves in the projection, which a fallback would decide for them.
                assert_never(authored)

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
