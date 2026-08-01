"""The API surface, and the source of the Python-to-TypeScript contract (PRD M12)."""

from django.http import HttpRequest
from ninja import NinjaAPI, Schema

api = NinjaAPI(
    title="Mapsift API",
    version="0.1.0",
    description=(
        "The one Mapsift backend: truth, auth, tenant isolation, ordering, and the "
        "authoritative conflict resolution."
    ),
)


class ServiceStatus(Schema):
    status: str


@api.get("/health", response=ServiceStatus, tags=["operations"])
def health(request: HttpRequest) -> ServiceStatus:
    """Liveness only. It touches no dependency, because a probe that fails on a slow query
    restarts a healthy service and turns a hiccup into an outage."""
    return ServiceStatus(status="ok")
