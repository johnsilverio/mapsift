"""The bindings and the guards beside them (ADR-0005 sections 3, 4 and 8)."""

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import TypeVar
from uuid import UUID

from django.db import connection, models, transaction

_ModelT = TypeVar("_ModelT", bound=models.Model)

_bound_tenant: ContextVar[UUID | None] = ContextVar("mapsift_bound_tenant", default=None)
_bound_user: ContextVar[UUID | None] = ContextVar("mapsift_bound_user", default=None)


class TenantNotBound(Exception):
    """Raised instead of returning the empty result an unbound query would otherwise get."""


class TenantAlreadyBound(Exception):
    """Raised when a scope opens for a second tenant while one is in force (ADR-0005 section 3)."""


class UserNotBound(Exception):
    """Raised instead of returning the empty result a read keyed on the session user would get."""


class UserAlreadyBound(Exception):
    """Raised when a scope opens for a second user while one is in force (ADR-0005 section 8)."""


@contextmanager
def tenant_scope(tenant_id: UUID) -> Iterator[None]:
    """Put one tenant in force for one transaction, and guarantee it is gone when that ends.

    The binding is made once per request and once per background task (ADR-0005 section 3):
    re-entering with the same tenant is a no-op, a second tenant raises TenantAlreadyBound.
    """
    bound = _bound_tenant.get()
    if bound == tenant_id:
        yield
        return
    if bound is not None:
        raise TenantAlreadyBound(
            "A binding for a second tenant was opened while one is in force, but the binding is "
            "made once per request and once per background task (ADR-0005 section 3), so nesting "
            "is refused rather than restored."
        )

    with transaction.atomic():
        with connection.cursor() as cursor:
            # Both the `true` (is_local) and the placeholder are load-bearing, and a session-scoped
            # or interpolated binding is a measured defect rather than a simpler spelling of this
            # statement (ADR-0005 section 3, measurements D and E).
            cursor.execute("SELECT set_config('mapsift.tenant_id', %s, true)", [str(tenant_id)])

        token = _bound_tenant.set(tenant_id)
        try:
            yield
        finally:
            _bound_tenant.reset(token)


@contextmanager
def user_scope(user_id: UUID) -> Iterator[None]:
    """Put one authenticated user in force for one transaction (ADR-0005 section 8).

    Stands beside the tenant binding rather than replacing it, and is the only one in force at
    login. Bound once per authenticated request: re-entering with the same user is a no-op, a
    second user raises UserAlreadyBound.
    """
    bound = _bound_user.get()
    if bound == user_id:
        yield
        return
    if bound is not None:
        raise UserAlreadyBound(
            "A binding for a second user was opened while one is in force, but the binding is "
            "made once per authenticated request (ADR-0005 section 8, under decision 3), so "
            "nesting is refused rather than restored."
        )

    with transaction.atomic():
        with connection.cursor() as cursor:
            # The `true` and the placeholder are load-bearing here for the reason they are in
            # tenant_scope above (ADR-0005 section 8, under decision 3).
            cursor.execute("SELECT set_config('mapsift.user_id', %s, true)", [str(user_id)])

        token = _bound_user.set(user_id)
        try:
            yield
        finally:
            _bound_user.reset(token)


def session_user_in_force() -> UUID:
    """The authenticated user bound for this transaction, refusing rather than answering without.

    Raises UserNotBound whatever else is bound, because a tenant binding alone answers a
    different question (ADR-0005 section 8).
    """
    user_id = _bound_user.get()
    if user_id is None:
        raise UserNotBound(
            "A read keyed on the session user ran with no user bound, so it would have been "
            "answered from the tenant policy alone rather than refused (ADR-0005 section 8). "
            "Wrap the call in mapsift.common.binding.user_scope."
        )
    return user_id


class TenantOwnedManager(models.Manager[_ModelT]):
    """The manager of a table inside the wall. It refuses to query with no tenant in force."""

    def get_queryset(self) -> models.QuerySet[_ModelT]:
        if _bound_tenant.get() is None:
            raise TenantNotBound(
                "A tenant-scoped query ran with no tenant bound, so it would have been answered "
                "with an empty result rather than refused (ADR-0005 section 4). Wrap the call in "
                "mapsift.common.binding.tenant_scope."
            )
        return super().get_queryset()
