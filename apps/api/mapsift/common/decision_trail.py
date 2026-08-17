"""The logging path of ADR-0011: correlation bound per context, and an allowlist on the way out.

Three guarantees live here rather than in the code that logs. Every record leaving the root handler
carries the correlation keys PRD N9 names, as far as the context in force holds them, without any
caller having passed one. Every record still leaves, whatever it carries, so a refusal is never
answered by silence. And a record emits the closed set of fields ADR-0011 section 4 names and
nothing else, so no geometry payload and no personal datum can reach a log whatever a caller,
Django's own components included, hands to a logger.
"""

import json
import logging
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from http import HTTPStatus
from typing import Self
from uuid import UUID

from django.http import HttpRequest

OPERATION_IDS = "operation_ids"
CLIENT_ID = "client_id"
TENANT_ID = "tenant_id"
REQUEST_ID = "request_id"
EVENT = "event"
STATUS = "status"
REASON = "reason"

# The closed set of ADR-0011 section 4. Everything a record carries beyond these is dropped rather
# than trimmed, so adding a name here is the deliberate act that section asks it to be.
THE_FIELDS_A_RECORD_MAY_CARRY = (
    OPERATION_IDS,
    CLIENT_ID,
    TENANT_ID,
    REQUEST_ID,
    EVENT,
    STATUS,
    REASON,
)

# Django's own spelling, not ours: `django.utils.log.log_response` emits with
# `extra={"request": request}`, so a record made after the middleware chain returned still holds
# the request its keys were remembered on (ADR-0011 section 2's extension of 2026-08-17).
_THE_CARRIER_A_RECORD_HOLDS = "request"

_THE_KEYS_A_CARRIER_REMEMBERS = "mapsift_correlation_keys"

# Every way `json.dumps` refuses a value: an unnameable type, a structure it cannot walk, and one
# deeper than the interpreter will follow.
_THE_WAYS_AN_ENCODER_FAILS = (TypeError, ValueError, RecursionError)


class TheDecisionARecordNames(StrEnum):
    """The event names ADR-0011 section 4 closes, each carrying the severity it is emitted at.

    A new decision joins this enum before it emits, and it cannot join without saying how loud it
    is: a severity kept in a table beside the enum is one a later decision forgets, and the entry
    it forgets is looked up inside the logging path, by the handler that was recording a failure.
    """

    severity: int

    def __new__(cls, wire_name: str, severity: int) -> Self:
        member = str.__new__(cls, wire_name)
        member._value_ = wire_name
        member.severity = severity
        return member

    FLUSH_APPLIED = ("flush.applied", logging.INFO)
    FLUSH_DEDUPLICATED = ("flush.deduplicated", logging.INFO)
    REQUEST_REFUSED = ("request.refused", logging.WARNING)
    REQUEST_FAILED = ("request.failed", logging.ERROR)


_the_trail = logging.getLogger("mapsift.trail")


@dataclass(frozen=True, slots=True)
class CorrelationKeys:
    """PRD N9's four keys, each held only as far as the context that bound it knew it."""

    request_id: UUID | None = None
    tenant_id: UUID | None = None
    client_id: UUID | None = None
    operation_ids: tuple[UUID, ...] = ()

    def filled_in_from(self, wider: "CorrelationKeys") -> "CorrelationKeys":
        """These keys, with every one they do not hold taken from a wider set."""
        return CorrelationKeys(
            request_id=self.request_id or wider.request_id,
            tenant_id=self.tenant_id or wider.tenant_id,
            client_id=self.client_id or wider.client_id,
            operation_ids=self.operation_ids or wider.operation_ids,
        )

    def as_fields(self) -> dict[str, str | list[str]]:
        """The keys as a record spells them, an unheld one left out rather than emitted empty.

        Every identifier is its canonical hyphenated lowercase string, because a join across two
        records is a string comparison in whatever backend reads them (ADR-0011 section 4).
        """
        scalars = {
            REQUEST_ID: self.request_id,
            TENANT_ID: self.tenant_id,
            CLIENT_ID: self.client_id,
        }
        fields: dict[str, str | list[str]] = {
            name: str(held) for name, held in scalars.items() if held is not None
        }
        if self.operation_ids:
            fields[OPERATION_IDS] = [str(one) for one in self.operation_ids]
        return fields


_NOTHING_BOUND = CorrelationKeys()

_the_keys_in_force: ContextVar[CorrelationKeys] = ContextVar(
    "mapsift_keys_in_force", default=_NOTHING_BOUND
)
_the_request_being_served: ContextVar[HttpRequest | None] = ContextVar(
    "mapsift_request_being_served", default=None
)


@contextmanager
def remembering_on(request: HttpRequest) -> Iterator[None]:
    """Name the request that every key bound inside is written onto as well as put in force.

    Django answers a 4xx or a 5xx by logging it in `BaseHandler.get_response`, after the whole
    middleware chain has returned, and a failure is answered after the frame that knew which
    operations it was about has unwound. Neither has a context left to read, and both still hold
    the request (ADR-0011 section 2's extension of 2026-08-17).
    """
    token = _the_request_being_served.set(request)
    try:
        yield
    finally:
        # The scope exits and what the request remembers deliberately does not: a symmetric
        # restore here empties the carrier exactly where the records above are written from
        # (that section, as sharpened 2026-08-17).
        _the_request_being_served.reset(token)


@contextmanager
def correlated_by(
    *,
    request_id: UUID | None = None,
    tenant_id: UUID | None = None,
    client_id: UUID | None = None,
    operation_ids: Sequence[UUID] = (),
) -> Iterator[None]:
    """Put correlation keys in force for a block, inheriting whatever a wider block already bound.

    Every record emitted inside carries them without being handed anything, which is the mechanism
    PRD N9 asks for and ADR-0011 section 2 fixes.
    """
    in_force = CorrelationKeys(
        request_id=request_id,
        tenant_id=tenant_id,
        client_id=client_id,
        operation_ids=tuple(operation_ids),
    ).filled_in_from(_the_keys_in_force.get())

    _widen_what_the_request_remembers(in_force)
    token = _the_keys_in_force.set(in_force)
    try:
        yield
    finally:
        _the_keys_in_force.reset(token)


def record_the_decision(
    event: TheDecisionARecordNames,
    *,
    status: HTTPStatus | None = None,
    reason: str | None = None,
) -> None:
    """Emit one record naming one decision, keyed by whatever correlation is in force.

    It takes no correlation key, because a signature that took one would be the design PRD N9
    replaced.
    """
    fields: dict[str, object] = {EVENT: str(event)}
    if status is not None:
        fields[STATUS] = int(status)
    if reason is not None:
        fields[REASON] = str(reason)

    _the_trail.log(event.severity, str(event), extra=fields)


class TheCorrelationKeysInForce(logging.Filter):
    """Stamps the keys bound for this context onto every record, and refuses none of them.

    It belongs on the root handler, which is what makes a record this codebase did not author
    carry the keys too (ADR-0011 sections 2 and 3). The context wins **per key** rather than
    wholesale: at a failure handler's frame it still holds the request identifier while the
    operations have unwound, so a fallback taken only on an empty context would refuse to fill
    exactly the keys that are missing (that section, as sharpened 2026-08-17).
    """

    def filter(self, record: logging.LogRecord) -> bool:
        keys = _the_keys_in_force.get().filled_in_from(
            _the_keys_remembered_on(_the_carrier_reachable_from(record))
        )
        for name, value in keys.as_fields().items():
            setattr(record, name, value)
        return True


class OnlyTheAllowedFields(logging.Formatter):
    """Writes a record's allowlisted fields as one JSON object and drops every other field.

    It never reads the message, the arguments or the traceback, which is what makes the guarantee
    hold for a record this codebase did not author. The timestamp and the severity are the
    record's envelope rather than a decision's field, so the closed set does not reach them
    (ADR-0011 sections 3 and 4).
    """

    def format(self, record: logging.LogRecord) -> str:
        emitted: dict[str, object] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
        }
        for name in THE_FIELDS_A_RECORD_MAY_CARRY:
            carried = getattr(record, name, None)
            if carried is not None:
                emitted[name] = carried
        return _json_that_cannot_fail(emitted)


def _json_that_cannot_fail(fields: dict[str, object]) -> str:
    """One line for a record, whatever its values are, the unencodable degraded to its text."""
    # `default=str` reads as making the repair below unreachable and does not: the encoder
    # consults it for a value whose type it cannot name, never for one it cannot walk, so a
    # container holding itself raises here and would take the whole record (ADR-0011 section 3).
    try:
        return json.dumps(fields, default=str)
    except _THE_WAYS_AN_ENCODER_FAILS:
        return json.dumps(
            {name: _degraded_where_the_encoder_refuses(value) for name, value in fields.items()},
            default=str,
        )


def _degraded_where_the_encoder_refuses(value: object) -> object:
    try:
        json.dumps(value, default=str)
    except _THE_WAYS_AN_ENCODER_FAILS:
        return str(value)
    return value


def _widen_what_the_request_remembers(keys: CorrelationKeys) -> None:
    request = _the_request_being_served.get()
    if request is None:
        return

    # Widest-first, and a plain assignment of `keys` is the obvious-looking form that broke it: a
    # binding opened per deduplicated operation then left a failure naming one of the batch
    # (ADR-0011 section 2, as sharpened 2026-08-17).
    setattr(
        request,
        _THE_KEYS_A_CARRIER_REMEMBERS,
        _the_keys_remembered_on(request).filled_in_from(keys),
    )


def _the_carrier_reachable_from(record: logging.LogRecord) -> HttpRequest | None:
    carried = getattr(record, _THE_CARRIER_A_RECORD_HOLDS, None)
    if isinstance(carried, HttpRequest):
        return carried
    return _the_request_being_served.get()


def _the_keys_remembered_on(request: HttpRequest | None) -> CorrelationKeys:
    remembered = getattr(request, _THE_KEYS_A_CARRIER_REMEMBERS, None)
    return remembered if isinstance(remembered, CorrelationKeys) else _NOTHING_BOUND
