"""Writes on the sync package's tables: the log an operation only reaches here (M15), the version
row it is ordered by (ADR-0004), and the cursor that says how far a client got (M4)."""

from collections.abc import Sequence
from dataclasses import dataclass
from functools import partial
from uuid import UUID

from django.db import connection, transaction

from mapsift.common.decision_trail import (
    TheDecisionARecordNames,
    correlated_by,
    record_the_decision,
)
from mapsift.layers.selectors import the_layers_a_project_holds_among
from mapsift.layers.services import project_the_current_state
from mapsift.sync.envelope import ClientHalf, Verdict
from mapsift.sync.models import ClientCursor, OperationLogEntry, ProjectVersionCounter
from mapsift.sync.rules import (
    OneUnbrokenStream,
    TheRefusalOfAnOperation,
    refuse_a_stream_this_cursor_cannot_continue,
    the_address_of,
    the_current_state_this_batch_leaves,
    the_last_decided_mutation_number_this_flush_leaves,
    the_layers_this_batch_addresses,
    the_one_unbroken_stream_this_batch_carries,
    the_operation_identifiers_in,
    the_operations_no_refusal_names,
    the_operations_this_cursor_has_already_seen,
    the_operations_this_cursor_has_not_seen,
    the_project_every_operation_claims,
    the_refusals_this_batch_earns,
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
        (tenant_id, client_id, project_id, last_decided_mutation_number)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (tenant_id, client_id, project_id)
    DO UPDATE SET last_decided_mutation_number = GREATEST(
        held.last_decided_mutation_number, EXCLUDED.last_decided_mutation_number
    )
"""


@dataclass(frozen=True, slots=True)
class WhatTheFlushDecided:
    """The one echo a client advances from, and the verdicts that went with it (T2.3, C12)."""

    last_decided_mutation_number: int
    refusals: tuple[TheRefusalOfAnOperation, ...]


def apply_the_flush(operations: list[ClientHalf]) -> WhatTheFlushDecided:
    """Decide every operation this installation has not had decided here, applying what it can and
    retaining what it refuses, and answer with the last-decided mutation number beside those
    refusals (T2.3, C12, ADR-0014 decisions 1 and 6).

    Refuses the whole batch with `ThisStreamCannotBeContinued` and applies nothing at all where its
    stream does not carry on from the cursor this installation left behind, which is the one
    refusal whose remedy is a resend (M10, M4, ADR-0014 decision 1).
    """
    stream = the_one_unbroken_stream_this_batch_carries(operations)

    already_decided = the_cursor_of(stream.client_id, stream.project_id)
    refuse_a_stream_this_cursor_cannot_continue(stream.starts_at_mutation_number, already_decided)

    fresh = the_operations_this_cursor_has_not_seen(operations, already_decided)
    last_decided = the_last_decided_mutation_number_this_flush_leaves(operations, already_decided)

    _record_what_this_cursor_had_already_seen(operations, already_decided)
    if not fresh:
        return WhatTheFlushDecided(last_decided, ())

    refusals = _the_refusals_this_flush_decides(fresh, stream.project_id)
    applied = the_operations_no_refusal_names(fresh, refusals)

    _project_what_this_flush_applied(applied)
    # Before the append and not after, though "beside the allocation" reads the other way: the
    # order is a contention trade ADR-0004 decision 2 settles in its extension of 2026-08-11.
    _advance_the_cursor_of(stream, last_decided)
    append_to_the_operation_log(fresh, tolerating_a_resend=True, refusals=refusals)
    # Not the direct calls these look like they should be: logging is not transactional, so a
    # record written here outlives a rollback, and both of these assert a write (ADR-0011 section
    # 4's extension of 2026-08-17 as ADR-0014 decision 8 narrows it).
    transaction.on_commit(partial(_record_what_this_flush_applied, applied))
    transaction.on_commit(partial(_record_what_this_flush_refused, refusals))
    return WhatTheFlushDecided(last_decided, refusals)


def append_to_the_operation_log(
    operations: Sequence[ClientHalf],
    *,
    tolerating_a_resend: bool = False,
    refusals: Sequence[TheRefusalOfAnOperation] = (),
) -> None:
    """Append a batch to the log, each entry carrying its place in its project's order (M10) and
    what the server decided about it (ADR-0014 decision 3).

    An operation a refusal names is written refused, with the reason the client was shown; every
    other one is written applied, so a caller appending a batch it applied names no refusal.

    An operation the log already holds is refused by its identity constraint unless the caller is
    tolerating a resend, which is the flush path's contract under T2.3 and never the log's own.
    """
    refused = {refusal.operation_id: refusal for refusal in refusals}
    # A list and never a generator inside bulk_create: the allocation below takes the project's
    # row and holds it to the commit, and a generator serialises every operation inside that
    # window (ADR-0004 decision 2, sharpened 2026-08-10).
    entries = [
        _as_a_log_entry(operation, refused.get(operation.root.operation_id))
        for operation in operations
    ]

    top = _allocate_the_range_this_flush_needs(
        the_tenant_every_operation_claims(operations),
        the_project_every_operation_claims(operations),
        len(entries),
    )
    for project_version, entry in enumerate(entries, start=top - len(entries) + 1):
        entry.project_version = project_version

    OperationLogEntry.objects.bulk_create(entries, ignore_conflicts=tolerating_a_resend)


def _record_what_this_cursor_had_already_seen(
    operations: Sequence[ClientHalf], already_decided: int | None
) -> None:
    """One record per dropped operation, the dedup being the decision that is genuinely per
    operation rather than per flush (ADR-0011 section 4).

    Emitted where it is taken and deliberately not deferred to the commit its siblings wait for,
    on that section's correction of 2026-08-17.
    """
    for operation_id in the_operation_identifiers_in(
        the_operations_this_cursor_has_already_seen(operations, already_decided)
    ):
        with correlated_by(operation_ids=(operation_id,)):
            record_the_decision(TheDecisionARecordNames.FLUSH_DEDUPLICATED)


def _record_what_this_flush_applied(applied: Sequence[ClientHalf]) -> None:
    """One record for the decision, naming the operations it covers (ADR-0011 section 4).

    The applied operations and nothing else, because an identifier carried by this record and by a
    refusal would say the same operation was applied and refused in one transaction (that
    section's addition of 2026-09-17). A flush that applied none of them records none.
    """
    if not applied:
        return

    with correlated_by(operation_ids=the_operation_identifiers_in(applied)):
        record_the_decision(TheDecisionARecordNames.FLUSH_APPLIED)


def _record_what_this_flush_refused(refusals: Sequence[TheRefusalOfAnOperation]) -> None:
    """One record per refused operation, the verdict being the second decision this path takes per
    operation rather than per flush (ADR-0011 section 4's addition of 2026-09-17).

    It carries no status, because the response answered `200` and no status was the refusal's to
    give: inventing one would say a request was refused when an operation was.
    """
    for refusal in refusals:
        with correlated_by(operation_ids=(refusal.operation_id,)):
            record_the_decision(TheDecisionARecordNames.FLUSH_REFUSED, reason=refusal.reason)


def _the_refusals_this_flush_decides(
    operations: Sequence[ClientHalf], project_id: UUID
) -> tuple[TheRefusalOfAnOperation, ...]:
    """What this flush will not apply of the batch it accepted, decided before anything is written.

    A verdict is a pure decision taken ahead of the critical section and never an exception caught
    mid-write, which is what keeps an unexpected failure from being read as a refusal (ADR-0014
    decision 1, ADR-0004 decision 2). The layer is consulted here rather than left to the composite
    reference, whose refusal is an `IntegrityError` escaping as a 500 (ADR-0010 decision 6's
    addition of 2026-09-08, as that of 2026-09-17 moves it).
    """
    addressed = the_layers_this_batch_addresses(operations)
    return tuple(
        the_refusals_this_batch_earns(
            operations,
            layers_the_project_holds=the_layers_a_project_holds_among(project_id, addressed),
        )
    )


def _project_what_this_flush_applied(applied: Sequence[ClientHalf]) -> None:
    """Leave the current state beside the log this flush appends, in the same transaction (M15).

    The applied operations alone and never the whole batch, or a refusal would leave exactly the
    state it exists to withhold (ADR-0012 decision 3 as narrowed 2026-09-17).

    Immediately before the cursor write, which is where ADR-0012 decision 3 puts it in the order
    ADR-0004 decision 2 owns. A flush that applied none of them projects nothing.
    """
    if not applied:
        return

    project_the_current_state(the_current_state_this_batch_leaves(applied))


def _advance_the_cursor_of(stream: OneUnbrokenStream, last_decided: int) -> None:
    """Raise this installation's cursor to what this flush decided, never lowering it (M4)."""
    with connection.cursor() as cursor:
        cursor.execute(
            ADVANCE_THIS_INSTALLATIONS_CURSOR,
            [stream.tenant_id, stream.client_id, stream.project_id, last_decided],
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


def _as_a_log_entry(
    operation: ClientHalf, refusal: TheRefusalOfAnOperation | None
) -> OperationLogEntry:
    """One entry with everything the insert needs except its place in the project's order.

    The client half is verbatim whatever the verdict, because a refused operation is retained
    exactly as an applied one is and M8 forbids the server rewriting what the client sent
    (ADR-0014 decision 3).
    """
    address = the_address_of(operation)
    return OperationLogEntry(
        tenant_id=address.tenant_id,
        operation_id=operation.root.operation_id,
        client_half=operation.model_dump(mode="json"),
        project_id=address.project_id,
        verdict=Verdict.applied if refusal is None else Verdict.refused,
        refusal_reason=None if refusal is None else refusal.reason,
    )
