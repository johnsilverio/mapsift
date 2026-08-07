"""The two probes of PRD N12, which ask different questions and are never one another.

Liveness answers whether the process should be restarted; readiness answers whether this instance
should receive traffic, and names what is out rather than presenting an outage as a blank result.

Both are exempted from the credential by name (ADR-0010 decision 6's addition).
"""

from http import HTTPStatus

from django.db import Error, connection
from django.http import HttpRequest
from ninja import Router, Schema, Status

DATABASE = "database"

router = Router(tags=["operations"])


class ServiceStatus(Schema):
    status: str


class ReadinessReport(Schema):
    """The dependencies this instance needs and cannot reach, empty when it can serve."""

    unavailable: list[str]


@router.get("/health", response=ServiceStatus, auth=None)
def health(request: HttpRequest) -> ServiceStatus:
    """Liveness (N12): whether the process should be restarted. It touches no dependency."""
    return ServiceStatus(status="ok")


@router.get(
    "/ready",
    response={HTTPStatus.OK: ReadinessReport, HTTPStatus.SERVICE_UNAVAILABLE: ReadinessReport},
    auth=None,
)
def ready(request: HttpRequest) -> Status[ReadinessReport]:
    """Readiness (N12): whether this instance should receive traffic, naming whatever is out."""
    unavailable = [] if _database_answers() else [DATABASE]
    code = HTTPStatus.SERVICE_UNAVAILABLE if unavailable else HTTPStatus.OK
    return Status(code, ReadinessReport(unavailable=unavailable))


def _database_answers() -> bool:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Error:
        # Widening this catch reports an outage that never happened: a blocked or misconfigured
        # database raises something that is not a `django.db.Error`, and no test would catch it.
        return False
    return True
