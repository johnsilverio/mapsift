"""The authenticated request and the identity it carries (ADR-0010 decision 4)."""

from typing import Protocol
from uuid import UUID

from django.http import HttpRequest


class Principal(Protocol):
    """The durable identity a request acts as, carrying nothing about how it was proved."""

    @property
    def id(self) -> UUID: ...


class AuthenticatedRequest(HttpRequest):
    """A request that reached a protected route, with its principal already resolved.

    Every protected route annotates its request with this and reads `auth`; nothing below the
    mechanism reads the session, the cookie or the token that produced it (ADR-0010 decision 4).
    """

    auth: Principal
