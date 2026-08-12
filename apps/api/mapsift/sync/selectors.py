"""The reads `sync` publishes (ADR-0007 section 3)."""

from uuid import UUID

from mapsift.sync.models import ClientCursor


def the_cursor_of(client_id: UUID, project_id: UUID) -> int | None:
    """How far this installation's stream has been applied here, or None if the server holds no
    cursor for it in this flush domain (M4).

    The tenant is the third of the three keys and comes from the binding in force (ADR-0005 3).
    """
    held = ClientCursor.objects.filter(client_id=client_id, project_id=project_id).first()
    return None if held is None else held.last_applied_mutation_number
