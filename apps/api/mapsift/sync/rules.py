"""Pure decisions over a batch of operations, taken on plain envelope data (ADR-0007 section 3)."""

from collections.abc import Sequence
from uuid import UUID

from mapsift.sync.envelope import ClientHalf, FeatureAddress, PropertyAddress


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
