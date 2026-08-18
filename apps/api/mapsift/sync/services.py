"""Writes on the sync package's tables: the log an operation only reaches here (M15), the version
row it is ordered by (ADR-0004), and the cursor that says how far a client got (M4)."""

from collections.abc import Sequence
from functools import partial
from uuid import UUID

from django.db import connection, transaction

from mapsift.common.decision_trail import (
    TheDecisionARecordNames,
    correlated_by,
    record_the_decision,
)
from mapsift.sync.envelope import ClientHalf
from mapsift.sync.models import ClientCursor, OperationLogEntry, ProjectVersionCounter
from mapsift.sync.rules import (
    OneUnbrokenStream,
    refuse_a_stream_this_cursor_cannot_continue,
    the_address_of,
    the_last_applied_this_flush_leaves,
    the_one_unbroken_stream_this_batch_carries,
    the_operation_identifiers_in,
    the_operations_this_cursor_has_already_seen,
    the_operations_this_cursor_has_not_seen,
    the_project_every_operation_claims,
    the_tenant_every_operation_claims,
)
from mapsift.sync.selectors import the_cursor_of

# ADR-0004 decision 2's RANGE rule as one statement: it creates the row on first use, adds the
# whole width of the batch to it otherwise, and answers with the top of the range either way.
TAKE_THE_PROJECTS_VERSION_ROW = f"""
    INSERT INTO {ProjectVersionCounter._meta.db_table} AS counter (tenant_id, project_id, version)
    VALUES (%s, %s, %s)
    ON CONFLICT (tenant_id, project_id)
    DO UPDATE SET version = counter.version + EXCLUDED.version
    RETURNING version
"""

# GREATEST reads as redundant beside a caller that has already taken a maximum, and collapsing it
# to EXCLUDED is the defect: a flush that lost a race would lower a cursor another flush raised
# (ADR-0004 decision 2, extension of 2026-08-11).
ADVANCE_THIS_INSTALLATIONS_CURSOR = f"""
    INSERT INTO {ClientCursor._meta.db_table} AS held
        (tenant_id, client_id, project_id, last_applied_mutation_number)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (tenant_id, client_id, project_id)
    DO UPDATE SET last_applied_mutation_number = GREATEST(
        held.last_applied_mutation_number, EXCLUDED.last_applied_mutation_number
    )
"""


def apply_the_flush(operations: list[ClientHalf]) -> int:
    """Apply what this installation has not had applied here, and answer with its last-applied
    mutation number, which is the only thing a client advances its cursor from (T2.3, C12).

    Refuses the whole batch with `ThisStreamCannotBeContinued` and applies nothing at all where
    its stream does not carry on from the cursor this installation left behind (M10, M4).
    """
    stream = the_one_unbroken_stream_this_batch_carries(operations)

    already_applied = the_cursor_of(stream.client_id, stream.project_id)
    refuse_a_stream_this_cursor_cannot_continue(stream.starts_at_mutation_number, already_applied)

    fresh = the_operations_this_cursor_has_not_seen(operations, already_applied)
    last_applied = the_last_applied_this_flush_leaves(operations, already_applied)

    _record_what_this_cursor_had_already_seen(operations, already_applied)
    if not fresh:
        return last_applied

    # Before the append and not after, though "beside the allocation" reads the other way: the
    # order is a contention trade ADR-0004 decision 2 settles in its extension of 2026-08-11.
    _advance_the_cursor_of(stream, last_applied)
    append_to_the_operation_log(fresh, tolerating_a_resend=True)
    # Not the direct call this looks like it should be: logging is not transactional, so a record
    # written here outlives a rollback and the trail then reads *applied* over a database holding
    # nothing (ADR-0011 section 4's extension of 2026-08-17).
    transaction.on_commit(partial(_record_what_this_flush_applied, fresh))
    return last_applied


def append_to_the_operation_log(
    operations: list[ClientHalf], *, tolerating_a_resend: bool = False
) -> None:
    """Append a batch to the log, each entry carrying its place in its project's order (M10).

    An operation the log already holds is refused by its identity constraint unless the caller is
    tolerating a resend, which is the flush path's contract under T2.3 and never the log's own.
    """
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

    OperationLogEntry.objects.bulk_create(entries, ignore_conflicts=tolerating_a_resend)


def _record_what_this_cursor_had_already_seen(
    operations: Sequence[ClientHalf], already_applied: int | None
) -> None:
    """One record per dropped operation, the dedup being the decision that is genuinely per
    operation rather than per flush (ADR-0011 section 4).

    Emitted where it is taken and deliberately not deferred to the commit its sibling waits for,
    on that section's correction of 2026-08-17.
    """
    for operation_id in the_operation_identifiers_in(
        the_operations_this_cursor_has_already_seen(operations, already_applied)
    ):
        with correlated_by(operation_ids=(operation_id,)):
            record_the_decision(TheDecisionARecordNames.FLUSH_DEDUPLICATED)


def _record_what_this_flush_applied(fresh: Sequence[ClientHalf]) -> None:
    """One record for the decision, naming the operations it covers (ADR-0011 section 4)."""
    with correlated_by(operation_ids=the_operation_identifiers_in(fresh)):
        record_the_decision(TheDecisionARecordNames.FLUSH_APPLIED)


def _advance_the_cursor_of(stream: OneUnbrokenStream, last_applied: int) -> None:
    """Raise this installation's cursor to what this flush applied, never lowering it (M4)."""
    with connection.cursor() as cursor:
        cursor.execute(
            ADVANCE_THIS_INSTALLATIONS_CURSOR,
            [stream.tenant_id, stream.client_id, stream.project_id, last_applied],
        )


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
