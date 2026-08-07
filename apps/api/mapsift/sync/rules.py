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


def the_address_of(operation: ClientHalf) -> FeatureAddress | PropertyAddress:
    """The target path an operation addresses, past the wrappers the generator writes (M9)."""
    return operation.root.target.root
