"""What the logging path guarantees about every record that leaves it, whoever made that record.

Trace: PRD N9's mechanism half (logs structured and carrying their correlation keys bound once per
request rather than passed by hand, and redaction a property of the path rather than of each
caller's diligence) with the two acceptance clauses that follow from it, *no log line carries
coordinates or personal data, asserted by a test over the logging path rather than by review* and
*a log line on the sync path that carries no correlation key fails review*; PRD N5 for what personal
data is; PRD N12 and ADR-0011 section 6 for the probe exemption. ADR-0011 in full: section 1 the
standard library with a JSON formatter, 2 the keys bound once per context, 3 redaction as a closed
allowlist on the **root** handler **with its third extension of 2026-08-17, which is about a record
escaping that handler rather than being trimmed by it**, 5 where each piece lives. Foundation
section 10; C6, and the privacy posture of foundation section 9, a record being a place production
data leaks to.

Cross-package by nature, so it lives here (ADR-0007 section 6): the path is `config` and `common`,
the traffic that exercises it is `sync`, and the personal datum it must not emit is `accounts`.

**Why every case here forces Django's own SQL logger on.** ADR-0011 section 1 turns on one measured
fact: `django.db.backends` logs SQL with its parameters, and the operation-log insert carries
`client_half` as a JSON literal holding the geometry. So the gate cannot sit on our own loggers, and
**a case that exercised only our own call sites would prove less than it looks**. pytest-django runs
the suite with `DEBUG` false, so `connection.queries_logged` is false and Django logs nothing unless
a case asks it to; `the_sql_django_logs_for_itself` is that ask, and it witnesses what was made so
no assertion below rests on a leak that never happened.

**What is deliberately not here, with the owner of each.** The telemetry backend, the sampling, the
dashboards and the alerting, and the client telemetry SDK with the browser half of N9: the
observability ADR, trigger unchanged at the first real users (foundation section 10). The
per-background-task binding, which N9 asks for in the same sentence as the per-request one: Celery
is deliberately not installed, so **that half has no runtime in this repository**, it is declared
and not built, and the issue that installs Celery inherits it. The vendor-neutrality clause, which
needs a second backend to read the emission before it can be asserted at all.
"""

import logging
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from http import HTTPStatus

import pytest
from django.core import mail
from django.db import connection
from django.test import Client, override_settings

from conftest import (
    Execute,
    JsonObject,
    Params,
    Party,
    a_browser,
    a_feature_create_claiming,
    a_geometry_set_claiming,
    the_documents_of,
    the_lines_the_logging_path_emits,
    the_records_missing_the_request_key,
    the_records_with_no_correlation_key,
    the_request_keys_in,
)
from mapsift.accounts.services import create_personal_account
from mapsift.sync.models import OperationLogEntry

pytestmark = pytest.mark.django_db(transaction=True)

OPERATIONS_PATH = "/api/operations"
LIVENESS_PATH = "/api/health"
JSON = "application/json"

# Django's own loggers, named rather than reached, because what makes them the subject here is
# that **this codebase did not author them** (ADR-0011 sections 1 and 3). The first carries the SQL
# the redaction cases are about; the second is where `log_response` writes the record Django makes
# about a 4xx or a 5xx of its own accord, after the middleware chain has returned.
DJANGO_SQL_LOGGER = "django.db.backends"
DJANGO_RESPONSE_LOGGER = "django.request"

# One half of the point `a_geometry_set_claiming` carries. Measured 2026-08-14: it reaches
# `django.db.backends` inside the `client_half` JSON of the operation-log insert.
A_COORDINATE_FROM_THE_PAYLOAD = "-47.9"

# A person, and the one piece of personal data this backend holds today (N5). Measured 2026-08-14:
# creating an account puts it in the parameters of two inserts Django logs, the user's and the
# personal tenant's, whose name is the address.
AN_EMAIL_ADDRESS = "carla@example.com"

# Somewhere for a handler outside the gate to deliver to. Django's own `mail_admins` handler is
# inert while this setting is empty, which is one of the two reasons ADR-0011 section 3's third
# extension of 2026-08-17 gives for the path leaking nothing today, and the one it ends on: *one
# day somebody sets `ADMINS` and redaction stops holding on that path with nothing turning red*.
SOMEBODY_SET_ADMINS = [("The address a failure is mailed to", "ops@example.com")]


class _WitnessWhatWasMade(logging.Filter):
    """Records what a logger produced and lets it carry on to the handlers below it."""

    def __init__(self, made: list[str]) -> None:
        super().__init__()
        self._made = made

    def filter(self, record: logging.LogRecord) -> bool:
        self._made.append(record.getMessage())
        return True


@contextmanager
def the_sql_django_logs_for_itself() -> Iterator[list[str]]:
    """Make Django log its own SQL, and witness the messages it made rather than assume them.

    Three switches and one arrangement, none of them optional. `force_debug_cursor` is what makes
    Django log at all, since pytest-django runs with `DEBUG` false; the logger's own level is what
    lets a DEBUG record be made, the root level being irrelevant because propagation consults
    handler levels and never an ancestor logger's; and the filter returns True, so the record
    carries on to the handlers and a capture around this block still sees whatever the path emits.
    """
    made: list[str] = []
    witness = _WitnessWhatWasMade(made)
    logger = logging.getLogger(DJANGO_SQL_LOGGER)
    level = logger.level

    logger.setLevel(logging.DEBUG)
    logger.addFilter(witness)
    connection.force_debug_cursor = True
    try:
        yield made
    finally:
        connection.force_debug_cursor = False
        logger.removeFilter(witness)
        logger.setLevel(level)


@contextmanager
def the_records_django_makes_about_a_response() -> Iterator[list[str]]:
    """Witness the records Django writes about its own answers, the way the block above witnesses
    the SQL it writes about its own queries.

    Neither switch that one needs applies here: `log_response` emits at WARNING for a 4xx and at
    ERROR for a 5xx, which no default level filters out, and it consults no cursor. What is shared
    is the instrument and its reason, that a case turning on a record somebody else made is green
    against a run where nobody made one.
    """
    made: list[str] = []
    witness = _WitnessWhatWasMade(made)
    logger = logging.getLogger(DJANGO_RESPONSE_LOGGER)

    logger.addFilter(witness)
    try:
        yield made
    finally:
        logger.removeFilter(witness)


@contextmanager
def the_write_failing_when_it_reaches(table: str) -> Iterator[None]:
    """Break the flush at a statement, the way a database does without asking.

    The name and the signature are `mapsift/sync/tests/test_the_flush_decision_trail.py`'s exactly,
    and the duplication is deliberate for the reason that module gives about its own arrangers: a
    grep on this name has to find one shape, and a second home in `conftest.py` would gain a
    spelling rather than lose one while every other module holding a fault stays out of this task.
    """

    def fail(
        execute: Execute, sql: str, params: Params, many: bool, context: dict[str, object]
    ) -> object:
        if table in sql:
            raise RuntimeError("the database went away mid-flush")
        return execute(sql, params, many, context)

    with connection.execute_wrapper(fail):
        yield


def the_records_a_handler_outside_the_gate_delivered() -> list[str]:
    """What a handler the allowlist does not sit on actually put in front of a reader.

    **The capture this module already has cannot answer this, and its own docstring says why.**
    `the_lines_the_logging_path_emits` reads the handlers `settings.LOGGING` declares, on the root
    logger, which is the whole of what the application configured; `console` and `mail_admins` are
    neither, sitting on Django's `django` logger from a configuration applied before ours. Widening
    that capture to every handler is the direction its docstring already refuses, on a measurement
    of pytest's own unnamed root handlers that is cited here rather than counted again.

    **Formatting through the escaped handler is the reading that looks right and is worthless.**
    *Measured 2026-08-17:* `AdminEmailHandler.emit` builds its body from an `ExceptionReporter`
    rather than from `self.format(record)`, so the formatted line is `Internal Server Error:
    /api/operations` with a traceback and carries no person at all, while the body delivered beside
    it runs to fifteen thousand characters and names the signed-in user. A capture that formatted
    through this handler would therefore be green over a live leak, which is why the observation
    point here is what the handler **did** and not what it would write.

    Read at call time rather than held, because pytest-django clears the outbox in place before
    every test, so the list is this test's own and nothing needs arranging to make it so. The body
    is resolved to text because django-stubs types it as possibly lazy, which a search for a leak
    inside it cannot be.
    """
    return [str(message.body) for message in mail.outbox]


def _carrying(text: str, lines: Sequence[str]) -> list[str]:
    """Every line holding a piece of text, which is how a leak is looked for rather than argued."""
    return [line for line in lines if text in line]


def _a_flush_carrying_a_coordinate(party: Party) -> JsonObject:
    """One geometry operation from an installation the server has never met (M9, M10's Shape)."""
    return {"operations": [a_geometry_set_claiming(party.tenant_id, project_id=party.project_id)]}


def test_no_line_the_path_emits_carries_a_coordinate_though_django_logs_the_insert_holding_one(
    alice: Party,
) -> None:
    """N9's acceptance that no log line carries coordinates, asserted over the path and not over our
    own call sites. The record that carries the leak here is made by Django, so an implementation
    that redacts wherever this codebase logs and nowhere else fails exactly where ADR-0011 section 1
    said it would.

    **The witness is the load-bearing half.** Without it this case is green against a path that
    redacts nothing and a flush that never reached the insert, which is one refused batch away at
    any time; with it, the leak is proven to have been offered to the path before the path is
    required not to have emitted it. The emitted lines are asserted non-empty for the mirror
    reason: absence of a coordinate in an empty list is absence of a path."""
    browser = a_browser(authenticated_as=alice.user_id)

    with (
        the_sql_django_logs_for_itself() as django_made,
        the_lines_the_logging_path_emits() as emitted,
    ):
        browser.post(OPERATIONS_PATH, _a_flush_carrying_a_coordinate(alice), JSON)

    assert _carrying(A_COORDINATE_FROM_THE_PAYLOAD, django_made) != []
    assert emitted != []
    assert _carrying(A_COORDINATE_FROM_THE_PAYLOAD, emitted) == []


def test_no_line_the_path_emits_carries_an_email_though_django_logs_the_insert_holding_one() -> (
    None
):
    """N9's other half of the same clause, with N5: personal data is kept out by the path itself,
    since a discipline that depends on every author is a leak with a date on it.

    **Separate from the coordinate case rather than folded into it**, because the two leaks arrive
    by different routes and a path could plausibly stop one and not the other: a coordinate is a
    field of a payload this codebase serialises, while the address is a column value that reaches
    the statement as an ordinary parameter of an ordinary insert. The act is real application code
    writing a real person, not a record this case authored, which is what makes the arrangement
    evidence rather than a rehearsal.

    An allowlist satisfies both by construction, and that is the argument for an allowlist rather
    than a reason to test only one of them: a denylist passes whatever nobody thought of, and these
    two are what "nobody thought of" looked like on the day the list was written."""
    with (
        the_sql_django_logs_for_itself() as django_made,
        the_lines_the_logging_path_emits() as emitted,
    ):
        create_personal_account(email=AN_EMAIL_ADDRESS)

    assert _carrying(AN_EMAIL_ADDRESS, django_made) != []
    assert emitted != []
    assert _carrying(AN_EMAIL_ADDRESS, emitted) == []


def test_no_record_the_sync_path_emits_is_left_without_a_correlation_key(alice: Party) -> None:
    """N9's acceptance that a log line on the sync path carrying no correlation key fails review,
    as a test rather than as a review item.

    **Django's own records are on the path on purpose, and they are what makes this case mean
    "bound rather than passed".** `django.db.backends` is handed nothing by anybody here, so a key
    on one of its records can only have come from the context ADR-0011 section 2 binds once per
    request. An implementation that adds the keys wherever this codebase calls a logger leaves them
    bare and is caught here; one that drops them from the path altogether satisfies this case
    honestly, since a record that is never emitted cannot be a line with no key.

    **None of the four rather than all four**, which is N9's own wording: a refusal taken before a
    batch is parsed has a request and no tenant, clientID or operation, and demanding all four
    would fail the very records this requirement was written to guarantee. The non-empty assertion
    is the control, since an empty list has no record without a key either."""
    browser = a_browser(authenticated_as=alice.user_id)

    with the_sql_django_logs_for_itself(), the_lines_the_logging_path_emits() as emitted:
        browser.post(OPERATIONS_PATH, _a_flush_carrying_a_coordinate(alice), JSON)

    documents = the_documents_of(emitted)

    assert documents != []
    assert the_records_with_no_correlation_key(documents) == []


def test_a_refusal_on_the_sync_path_leaves_no_record_without_a_correlation_key(
    alice: Party, bob: Party
) -> None:
    """N9's same clause on the half the case above it cannot reach. That one posts a batch the
    server accepts, and Django writes no record of its own about a `200`, so the entire class of
    records this clause exists over sat outside its arrangement while it stayed green.

    **What makes it red:** Django logs every 4xx and 5xx itself, in `BaseHandler.get_response`,
    **after the whole middleware chain has returned** (ADR-0011 section 2's extension of
    2026-08-17). A context a middleware opened has already closed by then, so a refusal leaves two
    records rather than one: the decision the route took, carrying its keys, and Django's, carrying
    none of the four.

    **The orphan is witnessed rather than assumed**, the instrument the two redaction cases above
    already built and for the same reason: the whole of what this case adds is a record Django
    made on its own, so a run where Django made none leaves the assertion standing over the
    ordinary refusal record and green for a reason this case is not about. Our own record satisfies
    the non-empty check by itself, which is exactly why that check cannot serve as the witness here
    the way it does for the 405 below.

    **What would pass it dishonestly, and what refuses each.** Quieting `django.request`, by level
    or by `propagate`, deletes the keyless record and the evidence together; the witness is where
    that now shows, and the 405 case below is where it shows even without one, because there the
    orphan is the only record there is. Dropping a record the allowlist recognises nothing in is
    the other, and ADR-0011 section 3's clarification of 2026-08-17 refuses it in as many words,
    the gate dropping a **field** and never the record. The non-empty assertion is what stops a
    path that emits nothing at all passing by silence.

    The `404` rather than either 422: it is the refusal whose body is required to say nothing
    (T6.5), so the record is the only place its reason exists, and it is the refusal MAP-14's spec
    kept in scope on the ground that a client meeting it has no retry to make."""
    browser = a_browser(authenticated_as=bob.user_id)
    claiming_a_tenant_bob_is_not_in = {
        "operations": [a_feature_create_claiming(alice.tenant_id, project_id=alice.project_id)]
    }

    with (
        the_records_django_makes_about_a_response() as django_made,
        the_lines_the_logging_path_emits() as emitted,
    ):
        refused = browser.post(OPERATIONS_PATH, claiming_a_tenant_bob_is_not_in, JSON)

    documents = the_documents_of(emitted)

    assert refused.status_code == HTTPStatus.NOT_FOUND
    assert django_made != []
    assert documents != []
    assert the_records_with_no_correlation_key(documents) == []


def test_a_response_django_answers_with_no_view_of_ours_running_is_still_correlated(
    client: Client,
) -> None:
    """N9's acceptance that a log line on the sync path carrying no correlation key fails review,
    on the coverage ADR-0011 section 2's extension of 2026-08-17 says the binding owes: **every**
    status Django answers on this route, the ones no view of ours produces included. A method this
    route does not define is answered by django-ninja before any operation runs, so nothing of ours
    is ever entered and there is no second record to hide behind.

    **What makes it red, and why it is not the case above it.** There the refusal's own record
    carries the keys and Django's orphan sits beside it; here the orphan is the whole of what the
    path emits, so this is the case that a `django.request` silenced to make its sibling green
    turns red. The two are the same mechanism measured from opposite ends and neither closes the
    other's hole alone.

    **The key is asked for by name rather than through the any-of-four reader**, and here that is
    the difference between a real assertion and a formality. This request is refused before a body
    is parsed, so the tenant, the clientID and the operation are all legitimately absent and the
    request identifier is the only one of the four a record can carry; a reader satisfied by any of
    them is therefore satisfied by the one key that could possibly be there, and would go on being
    satisfied if the binding stopped reaching this record at all only for some other key to appear.
    The sibling above keeps the wider reader because a refusal past the body genuinely admits more
    than one of the four.

    **What would pass it dishonestly:** emitting nothing, which the non-empty assertion refuses,
    and holding a context open past the request that opened it, which ADR-0011 section 2 already
    refuses with its reason, a key that bleeds into the next request joining a report to the wrong
    work. **No case here witnesses that bleed**, one request being all this arrangement runs, and
    it is named rather than claimed for that reason.

    The status is the positive control: a route answering something else was never asked the
    question this case is about."""
    with the_lines_the_logging_path_emits() as emitted:
        answered = client.get(OPERATIONS_PATH)

    documents = the_documents_of(emitted)

    assert answered.status_code == HTTPStatus.METHOD_NOT_ALLOWED
    assert documents != []
    assert the_records_missing_the_request_key(documents) == []


def test_the_correlation_keys_are_bound_once_for_a_request_rather_than_by_each_caller(
    alice: Party,
) -> None:
    """N9's mechanism clause that the keys are bound once per request rather than passed by hand,
    in the only form a test can witness it: one request's records agree on their request identifier,
    a second request's carry a different one, and no record of either is left without it.

    **Django's own SQL is on the path here for the reason the case above it gives, and without it
    this case cannot tell a binding from an argument.** Every record it would otherwise see was
    written by one call site of ours, so an identifier handed to that call site as a parameter
    satisfies every assertion below and the mechanism N9 rejects passes. `django.db.backends` is
    handed nothing by anybody here, so the key on one of its records reached it from the context
    ADR-0011 section 2 binds and from nowhere else. The second request runs under the same switch
    for the same reason, since its count means nothing if only our own records are counted.

    The per-background-task half of that same sentence is **not** claimed by this case and has no
    runtime here, for the reason the module docstring gives.

    What the assertions refuse between them: a key minted per record fails the count, a key minted
    once for the process fails the comparison, and a key that reaches only the records this codebase
    authored fails the absence check. The witness is what stops that absence check passing because
    Django was logging nothing at all."""
    browser = a_browser(authenticated_as=alice.user_id)

    with (
        the_sql_django_logs_for_itself() as django_made,
        the_lines_the_logging_path_emits() as first,
    ):
        browser.post(OPERATIONS_PATH, _a_flush_carrying_a_coordinate(alice), JSON)
    with the_sql_django_logs_for_itself(), the_lines_the_logging_path_emits() as second:
        browser.post(OPERATIONS_PATH, _a_flush_carrying_a_coordinate(alice), JSON)

    made_serving_one_request = the_documents_of(first)
    made_serving_the_next = the_documents_of(second)
    one_request = the_request_keys_in(made_serving_one_request)
    the_next_request = the_request_keys_in(made_serving_the_next)

    assert django_made != []
    assert the_records_missing_the_request_key(made_serving_one_request) == []
    assert len(one_request) == 1
    assert len(the_next_request) == 1
    assert one_request != the_next_request


def test_an_availability_probe_manufactures_no_record_whose_correlation_keys_are_empty(
    client: Client,
) -> None:
    """ADR-0011 section 6 with N12. A probe carries no principal and no tenant, so binding on it
    emits records whose correlation keys are empty, at whatever rate the orchestrator polls; N9
    calls a keyless line on the sync path a review failure, and manufacturing a stream of them is
    the wrong way to satisfy a probe. Liveness rather than readiness because it touches no
    dependency at all, so any record emitted while it answers was manufactured by the request path
    itself and by nothing else.

    **Green on the day it was written, and not deletable for it**, the same standing as
    `test_probes.py`'s liveness case: today the path has no handlers and emits nothing, so what
    this pins is the middleware that does not yet exist skipping the two paths ADR-0010 decision 6
    already exempts from the credential. The status is the positive control, since a probe that
    stopped answering would emit nothing either."""
    with the_lines_the_logging_path_emits() as emitted:
        response = client.get(LIVENESS_PATH)

    assert response.status_code == HTTPStatus.OK
    assert the_records_with_no_correlation_key(the_documents_of(emitted)) == []


@override_settings(ADMINS=SOMEBODY_SET_ADMINS)
def test_no_person_leaves_the_path_through_a_handler_django_attached_before_our_configuration(
    alice: Party,
) -> None:
    """N9's acceptance that no log line carries personal data (N5), on the half every case above it
    is blind to: a record that never meets the gate at all. ADR-0011 section 3's third extension of
    2026-08-17 states the guarantee as unconditional, and the mechanism it names is that Django
    applies its own configuration first, leaving the `django` logger carrying `console` and
    `mail_admins`, neither of which the allowlist sits on.

    **What makes it red:** the failure is answered by Django's `log_response` at ERROR, which
    propagates to the `django` logger, where `mail_admins` renders the whole diagnostic report and
    mails it. That report names the signed-in user, so a person leaves this backend through a door
    the gate is not on, while every assertion in this module about what the path emits stays green.

    **The arrangement defeats one of the two reasons that extension gives for today's silence, and
    the other is named rather than claimed.** It sets `ADMINS`, which is the extension's own closing
    sentence and the reason it calls today's safety two settings happening to be right. It does
    **not** defeat the other, `console` being `require_debug_true` at INFO: that handler refuses
    this record under its own filter at the suite's `DEBUG` false, so nothing here exercises it, and
    a fix reaching only `mail_admins` would satisfy this case and not the section.

    **What would pass it dishonestly, and what refuses each.** Quieting `django.request`, by level
    or by `propagate`, takes the leak and the evidence together; the witness is where that shows,
    and it is the instrument
    `test_a_refusal_on_the_sync_path_leaves_no_record_without_a_correlation_key`
    already uses for the same reason. Scrubbing the person out of the report while leaving the
    handler where it is satisfies the letter here and not the guarantee, which is a field-by-field
    denylist under another name and is what section 3 refuses in its first sentence. **And one this
    case cannot refuse and does not pretend to:** an override that failed to take leaves the handler
    inert for exactly the reason the extension says it is inert today, and green for it. No witness
    closes that, because a witness that the escaped handler was live is precisely what a correct
    implementation removes; it is named here rather than covered.

    The status is the positive control and it says the failure was real rather than a refusal in
    disguise: `log_response` writes a refusal at WARNING, which is under the ERROR floor
    `mail_admins` sits at, so a case that collected a refusal never asked this question at all."""
    browser = a_browser(authenticated_as=alice.user_id, reading_a_failure_as_a_response=True)

    with (
        the_records_django_makes_about_a_response() as django_made,
        the_write_failing_when_it_reaches(OperationLogEntry._meta.db_table),
    ):
        answered = browser.post(OPERATIONS_PATH, _a_flush_carrying_a_coordinate(alice), JSON)

    delivered = the_records_a_handler_outside_the_gate_delivered()

    assert answered.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert django_made != []
    assert _carrying(alice.email, delivered) == []
