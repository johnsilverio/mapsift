"""The request half of the logging path (ADR-0011 sections 2, 5 and 6)."""

from collections.abc import Callable
from uuid import uuid4

from django.http import HttpRequest, HttpResponse
from django.urls import reverse

from config import probes
from config.api import api
from mapsift.common.decision_trail import correlated_by, remembering_on

# Emptying this tuple leaves the whole suite green, measured: a probe answers 200 whether bound or
# not, so the exemption reads as dead weight and this line is the only thing guarding it
# (ADR-0011 section 6, whose reason was rewritten 2026-08-17).
THE_PROBES_EXEMPT_FROM_THE_BINDING = (probes.health, probes.ready)


class CorrelateEveryRequestButAProbe:
    """Binds the request identifier once, so nothing below this reaches for one to pass along."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self._get_response = get_response
        self._exempt = _the_paths_the_probes_answer_on()

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if request.path in self._exempt:
            return self._get_response(request)
        with remembering_on(request), correlated_by(request_id=uuid4()):
            return self._get_response(request)


def _the_paths_the_probes_answer_on() -> frozenset[str]:
    """Where the exempt operations are mounted, asked of the URL configuration.

    Their route belongs to `config/probes.py` and their prefix to `config/urls.py`, so a set
    holding a copy of either would exempt nothing the day one of them moved.
    """
    return frozenset(
        reverse(f"{api.urls_namespace}:{probe.__name__}")
        for probe in THE_PROBES_EXEMPT_FROM_THE_BINDING
    )
