"""The API surface, and the source of the cross-language contract.

ADR-0001 section 5 requires the generation wiring to exist from the first commit even while
its output is nearly empty, because this schema is the single source of truth for the
Python-to-TypeScript contract (PRD M12). Types on the other side are generated from what this
emits; they are never hand-written twice.

Routers for real capabilities arrive with the slices that need them, each in its own app, and
register against this one instance. Keeping them thin is the rule: a router parses, calls a use
case, and returns a schema, while the decisions live in pure functions that need no database.
"""

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
    """What the service says about itself when asked whether it is up."""

    status: str


@api.get("/health", response=ServiceStatus, tags=["operations"])
def health(request: HttpRequest) -> ServiceStatus:
    """Liveness only, and deliberately nothing more.

    This answers "is the process serving requests", which is what a container healthcheck and
    a load balancer need. It does not touch the database, because a liveness probe that fails
    on a slow query restarts a healthy service and turns a hiccup into an outage. Readiness,
    which does check dependencies, is a separate concern and arrives with the container step.
    """
    return ServiceStatus(status="ok")
