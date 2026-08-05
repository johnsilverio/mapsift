"""Which tenant is in force for a resource, and when the answer is none (M1, T6.1)."""

from collections.abc import Set as AbstractSet
from uuid import UUID


def resolve_tenant(*, member_of: AbstractSet[UUID], resource_tenant: UUID | None) -> UUID | None:
    """The tenant a session may act in for this resource, or None when it holds no claim to it.

    A resource in no tenant the session holds answers exactly as one that does not exist (T6.1).
    """
    return resource_tenant if resource_tenant in member_of else None
