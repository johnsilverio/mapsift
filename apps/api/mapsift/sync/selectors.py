"""The reads `sync` publishes (ADR-0007 section 3)."""

from uuid import UUID

from mapsift.sync.models import ClientCursor


def the_cursor_of(client_id: UUID, project_id: UUID) -> int | None:
    """How far this installation's stream has been decided here, or None if the server holds no
    cursor for it in this flush domain (M4).

    Decided rather than applied: a refused operation is passed by the cursor exactly as an applied
    one is (ADR-0014 decision 5).

    The tenant is the third of the three keys and comes from the binding in force (ADR-0005 3).
    """
    held = ClientCursor.objects.filter(client_id=client_id, project_id=project_id).first()
    return None if held is None else held.last_decided_mutation_number
