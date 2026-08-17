"""The API surface, the source of the Python-to-TypeScript contract (PRD M12), and the two
handlers where a refusal taken before any route and a failure nobody planned for become records
(ADR-0011 section 7).
"""

import traceback
from http import HTTPStatus

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from ninja import NinjaAPI
from ninja.errors import ValidationError
from ninja.security import django_auth

from config import probes
from mapsift.common.decision_trail import TheDecisionARecordNames, record_the_decision
from mapsift.sync import api as sync

# The 422 a pre-handler refusal answers with is one wire shape told apart by its body (ADR-0010
# decision 6), so the record names the class of refusal and never what was refused: the validation
# errors carry the payload the allowlist exists to keep out.
A_REQUEST_BODY_THE_CONTRACT_REFUSES = "malformed_request_body"

api = NinjaAPI(
    title="Mapsift API",
    version="0.1.0",
    description=(
        "The one Mapsift backend: truth, auth, tenant isolation, ordering, and the "
        "authoritative conflict resolution."
    ),
    # On the instance and never on an add_router call (ADR-0010 decision 4).
    auth=django_auth,
)

api.add_router("", probes.router)
api.add_router("", sync.router)


@api.exception_handler(ValidationError)
def record_a_request_refused_before_any_handler(
    request: HttpRequest, exc: ValidationError
) -> HttpResponse:
    """Record the refusals answered with no frame of ours on the stack (ADR-0011 section 7)."""
    record_the_decision(
        TheDecisionARecordNames.REQUEST_REFUSED,
        status=HTTPStatus.UNPROCESSABLE_ENTITY,
        reason=A_REQUEST_BODY_THE_CONTRACT_REFUSES,
    )
    # Registering this handler replaces django-ninja's default, and this body is the one
    # ADR-0010 decision 6 tells the malformed refusals apart by, so it is re-emitted identically.
    return api.create_response(
        request, {"detail": exc.errors}, status=HTTPStatus.UNPROCESSABLE_ENTITY
    )


@api.exception_handler(Exception)
def record_a_failure_nobody_planned_for(request: HttpRequest, exc: Exception) -> HttpResponse:
    """Record the failure, then answer as the handler this one replaced answers it (N9)."""
    record_the_decision(
        TheDecisionARecordNames.REQUEST_FAILED, status=HTTPStatus.INTERNAL_SERVER_ERROR
    )
    if not settings.DEBUG:
        raise exc
    # What each arm answers is django-ninja's `_default_exception`, and the vendor's
    # `logger.exception` beside it is deliberately not reproduced, which is a departure a reader
    # diffing the two would otherwise restore (ADR-0011 section 7's notes of 2026-08-17).
    return HttpResponse(
        traceback.format_exc(),
        status=HTTPStatus.INTERNAL_SERVER_ERROR,
        content_type="text/plain",
    )
