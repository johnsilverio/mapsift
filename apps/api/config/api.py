"""The API surface, and the source of the Python-to-TypeScript contract (PRD M12)."""

from ninja import NinjaAPI

from config import probes

api = NinjaAPI(
    title="Mapsift API",
    version="0.1.0",
    description=(
        "The one Mapsift backend: truth, auth, tenant isolation, ordering, and the "
        "authoritative conflict resolution."
    ),
)

api.add_router("", probes.router)
