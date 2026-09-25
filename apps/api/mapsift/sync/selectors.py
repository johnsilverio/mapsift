"""The reads `sync` publishes (ADR-0007 section 3)."""

from collections.abc import Collection
from uuid import UUID

from mapsift.sync.models import ClientCursor, OperationLogEntry
from mapsift.sync.rules import WhyAnOperationWasRefused


def the_cursor_of(client_id: UUID, project_id: UUID) -> int | None:
    """How far this installation's stream has been decided here, or None if the server holds no
    cursor for it in this flush domain (M4).

    Decided rather than applied: a refused operation is passed by the cursor exactly as an applied
    one is (ADR-0014 decision 5).

    The tenant is the third of the three keys and comes from the binding in force (ADR-0005 3).
    """
    held = ClientCursor.objects.filter(client_id=client_id, project_id=project_id).first()
    return None if held is None else held.last_decided_mutation_number


def the_refusals_the_log_holds_among(
    operation_ids: Collection[UUID],
) -> dict[UUID, WhyAnOperationWasRefused | None]:
    """Each of the given operations the tenant's log already holds, mapped to the reason the log
    refused it for, or to None where the log holds no refusal of it (T2.3, ADR-0014 decision 3).

    A given operation the log does not hold is absent from the mapping. Held is keyed by the
    identifier alone, whatever project or stream the entry was appended from (M3; ADR-0010
    decision 6's addition of 2026-09-24).

    Requires a tenant binding and opens none (ADR-0005 sections 3 and 4). It answers a mapping
    rather than a queryset, so its rows are read inside the binding that authorised them.
    """
    held = OperationLogEntry.objects.filter(operation_id__in=operation_ids)
    return {
        operation_id: None if reason is None else WhyAnOperationWasRefused(reason)
        for operation_id, reason in held.values_list("operation_id", "refusal_reason")
    }
