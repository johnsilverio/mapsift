"""Pure decisions over a batch of operations, taken on plain envelope data (ADR-0007 section 3)."""

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from itertools import pairwise
from uuid import UUID

from mapsift.sync.envelope import ClientHalf, FeatureAddress, PropertyAddress

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
    """The closed set of two a refusal names, whose remedies differ (ADR-0010 decision 6's
    addition of 2026-08-13)."""

    GAP_ABOVE_CURSOR = "gap_above_cursor"
    NO_CURSOR_IN_THIS_DOMAIN = "no_cursor_in_this_domain"


class ThisStreamCannotBeContinued(Exception):
    """Raised when a batch does not carry on from where this installation left off (M10, M4).

    Not a `MalformedBatch`: the batch satisfies the contract the boundary declares, and the cursor
    it is measured against needs the tenant bound, so this refusal is taken after the binding and
    answers `409` rather than `422` (ADR-0010 decision 6's addition of 2026-08-13).
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
        )
    if already_applied is not None and starts_at > already_applied + 1:
        raise ThisStreamCannotBeContinued(
            WhyAStreamCannotBeContinued.GAP_ABOVE_CURSOR,
            resend_from_mutation_number=already_applied + 1,
        )


def the_operations_this_cursor_has_not_seen(
    operations: Sequence[ClientHalf], already_applied: int | None
) -> list[ClientHalf]:
    """The operations of a batch above the cursor, an absent cursor having seen nothing (T2.3).

    The absence is `None` rather than a number, because zero is the first mutation number and so
    a legitimate applied value rather than an available sentinel (M4's Shape, M10's Shape).
    """
    if already_applied is None:
        return list(operations)
    return [
        operation for operation in operations if the_mutation_number_of(operation) > already_applied
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


def the_address_of(operation: ClientHalf) -> FeatureAddress | PropertyAddress:
    """The target path an operation addresses, past the wrappers the generator writes (M9)."""
    return operation.root.target.root


def the_mutation_number_of(operation: ClientHalf) -> int:
    """The per-client axis an operation carries, past the wrappers the generator writes (M10)."""
    return operation.root.mutation_number.root
