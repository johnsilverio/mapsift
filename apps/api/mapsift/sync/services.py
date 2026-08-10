"""Writes on the operation log, which is the only place an operation reaches it (M15)."""

from uuid import UUID

from django.db import connection

from mapsift.sync.envelope import ClientHalf
from mapsift.sync.models import OperationLogEntry, ProjectVersionCounter
from mapsift.sync.rules import (
    the_address_of,
    the_project_every_operation_claims,
    the_tenant_every_operation_claims,
)

# ADR-0004 decision 2's RANGE rule as one statement: it creates the row on first use, adds the
# whole width of the batch to it otherwise, and answers with the top of the range either way.
TAKE_THE_PROJECTS_VERSION_ROW = f"""
    INSERT INTO {ProjectVersionCounter._meta.db_table} AS counter (tenant_id, project_id, version)
    VALUES (%s, %s, %s)
    ON CONFLICT (tenant_id, project_id)
    DO UPDATE SET version = counter.version + EXCLUDED.version
    RETURNING version
"""


def append_to_the_operation_log(operations: list[ClientHalf]) -> None:
    """Append a batch to the log, each entry carrying its place in its project's order (M10)."""
    # A list and never a generator inside bulk_create: the allocation below takes the project's
    # row and holds it to the commit, and a generator serialises every operation inside that
    # window (ADR-0004 decision 2, sharpened 2026-08-10).
    entries = [_as_a_log_entry(operation) for operation in operations]

    top = _allocate_the_range_this_flush_needs(
        the_tenant_every_operation_claims(operations),
        the_project_every_operation_claims(operations),
        len(entries),
    )
    for project_version, entry in enumerate(entries, start=top - len(entries) + 1):
        entry.project_version = project_version

    OperationLogEntry.objects.bulk_create(entries)


def _allocate_the_range_this_flush_needs(tenant_id: UUID, project_id: UUID, width: int) -> int:
    """The top of the contiguous range of per-project versions this flush owns (ADR-0004 2)."""
    with connection.cursor() as cursor:
        # The one write in this schema reaching a tenant-owned table without TenantOwnedManager,
        # so an unbound flush is refused by the policy as a privilege rather than by the loud
        # guard ADR-0005 decision 4 puts beside it.
        cursor.execute(TAKE_THE_PROJECTS_VERSION_ROW, [tenant_id, project_id, width])
        allocated: int = cursor.fetchone()[0]
        return allocated


def _as_a_log_entry(operation: ClientHalf) -> OperationLogEntry:
    """One entry with everything the insert needs except its place in the project's order."""
    address = the_address_of(operation)
    return OperationLogEntry(
        tenant_id=address.tenant_id,
        operation_id=operation.root.operation_id,
        client_half=operation.model_dump(mode="json"),
        project_id=address.project_id,
    )
