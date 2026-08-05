"""The tenant binding and the guard beside it (ADR-0005 sections 3 and 4).

The wall is the database's. This module puts a tenant in force for one transaction, and refuses to
run a tenant-scoped query when none is.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import TypeVar
from uuid import UUID

from django.db import connection, models, transaction

_ModelT = TypeVar("_ModelT", bound=models.Model)

_bound_tenant: ContextVar[UUID | None] = ContextVar("mapsift_bound_tenant", default=None)


class TenantNotBound(Exception):
    """Raised instead of returning the empty result an unbound query would otherwise get."""


@contextmanager
def tenant_scope(tenant_id: UUID) -> Iterator[None]:
    """Put one tenant in force for one transaction, and guarantee it is gone when that ends."""
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
