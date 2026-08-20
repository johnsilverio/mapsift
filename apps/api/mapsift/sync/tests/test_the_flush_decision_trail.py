"""A user quotes one operation identifier and the server's decision about it comes back.

Trace: PRD N9's Requirement (every flush records its batches and its dedup decisions, keyed by
operation identifier and clientID, so a user report maps to a reconstructible decision trail; every
refusal presented to a user is also recorded, and every recorded refusal was presented) and the
three acceptance clauses that follow, *given an operation identifier from a user report, the flush
decision path is reconstructible end to end*, *every user-visible refusal has a matching record and
the reverse*, and *a failure with no user-visible signal and no record fails review*; ADR-0011
section 4 for the record granularity and the closed wire vocabulary **as its addition of 2026-08-14
closes it, `request.failed` joining the three names that section carried before it**, section 2
with its **sharpening of 2026-08-17**, whose third point is what the deduplicate-then-fail case
below is about, and section 7 for the refusals that answer before any handler of ours is entered,
**whose dated notes are the provenance correction, the resolution, the sharpening that followed it
hours later, the settlement of the `DEBUG` branch and the departure from the vendor's
`logger.exception`**, the one the failure cases read being the sharpening, which corrects the
resolution before it about what the `Exception` entry does; ADR-0010 decision 6 with
its additions of
2026-08-07, 2026-08-11 and 2026-08-13 for the refusals themselves and the bodies they carry; T2.3
and M4 for the dedup; I9, I10; C12, C13.

**Only the decisions the flush takes today are here, and that is why this task runs before the three
that add the rest.** N9 also names conflict verdicts, authorship normalizations and force-upgrade
rejections; none exists in this repository, so a case for one would be a test of an imagined shape.
Their owners are MAP-38 and the conflict slice, MAP-37, and the versioning mechanism of OQ-15, and
each inherits this path rather than building its own.

**The join is over a field and never over a message.** ADR-0011 section 4 states the rule this
module is the enforcement of: an identifier interpolated into a message string is not a join key, a
key is a field, and `operation_ids` is a list rather than a delimited string. Every case below looks
the operation up through `_the_records_naming`, which reads that field through
`_the_operations_a_record_names` as the list the section closes, so neither a beautifully readable
sentence naming the operation nor a comma-joined string of identifiers is a trail.

**Two of N9's four keys are the flush's to carry and nothing else here would have noticed them
missing**, which is why the two cases after the first are about the clientID and the tenant rather
than about a decision. The requirement keys the trail by operation identifier *and clientID*, and
its mechanism half names the tenant beside them; a suite that joins on the operation alone is
satisfied by a path carrying one key of the four. The request identifier is the fourth and is
`tests/test_the_logging_path.py`'s, because it is bound before this route is reached.

**Everything goes through the route and never through the writer**, on the ground the two sibling
modules already state: `tenant_scope` opens `transaction.atomic()` itself, so a case whose only
transaction is one it opened is green against an implementation that has none, and three of the
refusals below have no seam but the route in any case.

**A record emitted inside a transaction that later rolls back does survive it, measured 2026-08-17
and now written into ADR-0011 section 4.** The cases arranging an answer raised inside a binding and
taken outside it are the gap, the unbacked tenant claim, the unbacked project claim, the failure
nobody planned for, the operation that failure is reached from, the flush that deduplicated before
it failed, and the commit that never went through, which is the shape that cost MAP-45 three
docstrings on 2026-08-14, two corrected and one struck. Every one of them but the last decides what
the path emitted without reading a durable store at all: the capture takes each line **as the
handler is asked to write it**, which is the same
witness-it-as-it-runs instrument MAP-45 landed on. The commit that never went through does read the
store, as a **control** rather than as a trail, because the whole of what it asserts is that a
record claimed a state the store does not hold.
"""

from collections.abc import Iterator, Sequence
from contextlib import AbstractContextManager, contextmanager
from http import HTTPStatus
from uuid import UUID, uuid4

import pytest
from django.db import connection
from django.test import Client

from conftest import (
    CLIENT_ID,
    EVENT,
    OPERATION_IDS,
    REASON,
    STATUS,
    TENANT_ID,
    Execute,
    JsonObject,
    Params,
    Party,
    a_browser,
    a_feature_create_claiming,
    the_documents_of,
    the_lines_the_logging_path_emits,
)
from mapsift.common.binding import tenant_scope
from mapsift.sync.models import OperationLogEntry

pytestmark = pytest.mark.django_db(transaction=True)

OPERATIONS_PATH = "/api/operations"
JSON = "application/json"

# The refusal body this route answers with (ADR-0010 decision 6, addition of 2026-08-13), read here
# only to arrange which of that status's two refusals a case is about. Spelled apart from conftest's
# `REASON` on purpose: that one is the record's field under ADR-0011 section 4, this one is the wire
# object's key, and the two contracts agreeing on a spelling is not the same as being one contract.
THE_REASON_IN_THE_BODY = "reason"
A_GAP_ABOVE_THE_CURSOR = "gap_above_cursor"

# The four event names ADR-0011 section 4 closes, as a record spells them. The first two are the
# flush's own decisions and the last two are separate names on purpose (that section's addition of
# 2026-08-14): a refusal is a decision the server took and carries a reason from a closed set, a
# failure is a decision nobody took. Reading a record's status without its event is what lets those
# two fold into one, which is why every case below that reads a status names an event first.
FLUSH_APPLIED = "flush.applied"
FLUSH_DEDUPLICATED = "flush.deduplicated"
REQUEST_REFUSED = "request.refused"
REQUEST_FAILED = "request.failed"


def _a_contiguous_queue_of(
    *operation_ids: UUID,
    by: Party,
    from_installation: UUID,
    starting_at: int,
) -> JsonObject:
    """One installation's queue in one project of one tenant, ascending one at a time from a
    given mutation number (M4, M10, ADR-0010 decision 6).

    The name and the signature are `test_the_typed_resend_on_a_gap.py`'s exactly, and `starting_at`
    carries no default for that reason alone: a single name over two signatures disagreeing on
    arity is a grep that misleads whoever runs it, which is the defect that module's own docstring
    records avoiding.

    **Local rather than hoisted into `conftest.py`, which is the opposite of what that file argues
    for its connection instruments, and the difference is the count of spellings.** This package
    holds four queue arrangers under three names and three signatures, each documented as named
    apart on purpose, and every other module holding one is outside this task's scope. A shared
    home would therefore gain a fifth spelling rather than lose one, which is the failure the rule
    exists against; `conftest.py` holds the per-operation arrangers this builds on for the reason
    that does apply, which is that every module needs those and they have one shape.
    """
    return {
        "operations": [
            a_feature_create_claiming(
                by.tenant_id,
                operation_id=operation_id,
                client_id=from_installation,
                mutation_number=mutation_number,
                project_id=by.project_id,
            )
            for mutation_number, operation_id in enumerate(operation_ids, start=starting_at)
        ]
    }


def _the_server_took(browser: Client, batch: JsonObject) -> None:
    """Post a batch whose landing is arranged rather than asserted, and witness that it landed.

    The reason the two sibling modules give: this route collects a typed refusal with nearly every
    task in this milestone, so an arrange step that quietly starts being refused leaves the
    assertions standing and the module vacuous rather than red.
    """
    assert browser.post(OPERATIONS_PATH, batch, JSON).status_code == HTTPStatus.OK


@contextmanager
def the_write_failing_when_it_reaches(table: str) -> Iterator[None]:
    """Break the flush at a statement, the way a database does without asking.

    Injected at the connection rather than at anything this repository wrote, because the clause it
    serves is about the failures nobody planned for: a fault arranged by replacing our own writer
    proves the path handles the failures somebody imagined, which is the set that was never the
    problem.
    """

    def fail(
        execute: Execute, sql: str, params: Params, many: bool, context: dict[str, object]
    ) -> object:
        if table in sql:
            raise RuntimeError("the database went away mid-flush")
        return execute(sql, params, many, context)

    with connection.execute_wrapper(fail):
        yield


# The DROP reads as redundant beside CREATE OR REPLACE and is not: a constraint trigger has no
# replacing form, so without it a run killed between here and the undo below leaves the next run
# erroring in its arrangement rather than failing on its assertion.
REFUSE_THE_COMMIT = f"""
DROP TRIGGER IF EXISTS refuse_the_commit_of_this_flush ON {OperationLogEntry._meta.db_table};

CREATE OR REPLACE FUNCTION the_commit_this_case_refuses() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'the commit did not go through';
END;
$$ LANGUAGE plpgsql;

CREATE CONSTRAINT TRIGGER refuse_the_commit_of_this_flush
AFTER INSERT ON {OperationLogEntry._meta.db_table}
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION the_commit_this_case_refuses();
"""

LET_THE_COMMIT_THROUGH_AGAIN = f"""
DROP TRIGGER IF EXISTS refuse_the_commit_of_this_flush ON {OperationLogEntry._meta.db_table};
DROP FUNCTION IF EXISTS the_commit_this_case_refuses();
"""


@contextmanager
def the_commit_refused_after_everything_was_written() -> Iterator[None]:
    """Let the whole flush run and take the commit away from it at the end.

    **Not `the_write_failing_when_it_reaches` with a later table, and the difference is the whole
    case.** An execute wrapper is offered statements, and the commit is not one of them, so every
    fault it can inject lands while the transaction is still open; a path that emits its record one
    line after the last statement instead of after the commit stays green under it. A deferred
    constraint fires inside COMMIT itself, which leaves nothing between the record and durability
    for a wrong implementation to sit in.
    """
    with connection.cursor() as cursor:
        cursor.execute(REFUSE_THE_COMMIT)
    try:
        yield
    finally:
        with connection.cursor() as cursor:
            cursor.execute(LET_THE_COMMIT_THROUGH_AGAIN)


def _a_flush_meeting(
    fault: AbstractContextManager[None],
    *operation_ids: UUID,
    by: Party,
    from_installation: UUID,
    starting_at: int,
) -> tuple[int, list[JsonObject]]:
    """Post one queue into a fault, answering with what the client was told and what the path
    emitted while it was told it.

    Shared rather than written out per case, unlike the arrangers above it: the fault cases carry
    this one byte for byte, and ADR-0011 section 4's extension of 2026-08-17 binds MAP-37, MAP-38
    and MAP-39 to the same shape. What a case actually differs on stays at its call site, which is
    the fault it arranges and the operations it names.

    The client reads a failure as a response rather than re-raising it, for the measured reason
    `a_browser` carries; a case asking what the user was shown cannot be written without it.
    """
    browser = a_browser(authenticated_as=by.user_id, reading_a_failure_as_a_response=True)

    with fault, the_lines_the_logging_path_emits() as emitted:
        answered = browser.post(
            OPERATIONS_PATH,
            _a_contiguous_queue_of(
                *operation_ids,
                by=by,
                from_installation=from_installation,
                starting_at=starting_at,
            ),
            JSON,
        )

    return answered.status_code, the_documents_of(emitted)


def _the_operations_a_record_names(document: JsonObject) -> list[str]:
    """The join key as ADR-0011 section 4 closes it: a list of identifiers, never a delimited
    string.

    Reading the field as a list rather than searching inside it is the whole difference, and that
    section says why in one line: `in` answers the same for `["a", "b"]` and for `"a,b"`, so the
    shape stops being enforced the moment an obvious reader is written over it.
    """
    named = document.get(OPERATION_IDS, [])

    assert isinstance(named, list), f"{OPERATION_IDS} is a list, never a delimited string"

    return [str(identifier) for identifier in named]


def _the_records_naming(operation_id: UUID, documents: Sequence[JsonObject]) -> list[JsonObject]:
    """Every record whose join key covers one operation, in the order the path emitted them.

    The one lookup in this module, so the rule above holds for every case that reads a record about
    an operation rather than for the cases that happen to remember it.
    """
    return [
        document
        for document in documents
        if str(operation_id) in _the_operations_a_record_names(document)
    ]


def _the_decisions_recorded_about(operation_id: UUID, documents: Sequence[JsonObject]) -> list[str]:
    """What the server decided about one operation, in the order it decided it.

    N9's reconstruction spelled out as the question a support desk actually asks: a user quotes one
    identifier and this is everything the path has to say about it.
    """
    return [str(document[EVENT]) for document in _the_records_naming(operation_id, documents)]


def _the_records_of(event: str, documents: Sequence[JsonObject]) -> list[JsonObject]:
    """Every record naming one decision, which is how a case says which trail it is reading.

    Parameterised by the event rather than written once per kind, because the four names are a
    contract in ADR-0011 section 4 and a call site that spells one is a call site that can be
    grepped when a fifth decision is added; a reader that filtered on nothing would let a refusal
    and a failure answer for each other.
    """
    return [document for document in documents if document.get(EVENT) == event]


def _the_field_each_record_carries(field: str, documents: Sequence[JsonObject]) -> list[object]:
    """One field as each record spells it, an absent one read as None rather than raised on.

    A subscript would raise before the assertion reading it could show anything, and a case whose
    own control errors reports the wrong defect: the question every caller of this is asking is
    whether the record carries the field, never whether the reader survived it.
    """
    return [document.get(field) for document in documents]


def _the_reasons_recorded(documents: Sequence[JsonObject]) -> list[str]:
    """The reason each record gives, with an absent or null one read as the empty string.

    The normalisation is the whole point and it closes a trap that was live in this file:
    `str(None)` is `"None"`, which compares unequal to the empty string, so a check for emptiness
    written over a raw read passes a record whose reason is null.
    """
    return [str(document.get(REASON) or "") for document in documents]


def test_an_operation_identifier_from_a_report_leads_to_the_decision_the_flush_took_on_it(
    alice: Party,
) -> None:
    """N9's first acceptance clause, in the shape the requirement describes it: a user quotes one
    identifier out of a batch and the trail says what happened to it.

    **The operation travels beside another one on purpose, and the quoted one is the second.**
    ADR-0011 section 4 emits one record per decision carrying the operations it covers as a
    structured list, so a batch of one never asks whether that list covers the whole batch: a path
    that names only the operation it happened to look at first answers this report with silence and
    is caught here. What keeps that list from being a comma-joined string is the reader, not the
    batch length, which is what `_the_operations_a_record_names` exists for."""
    reported, alongside = uuid4(), uuid4()
    browser = a_browser(authenticated_as=alice.user_id)

    with the_lines_the_logging_path_emits() as emitted:
        response = browser.post(
            OPERATIONS_PATH,
            _a_contiguous_queue_of(
                alongside, reported, by=alice, from_installation=uuid4(), starting_at=0
            ),
            JSON,
        )

    assert response.status_code == HTTPStatus.OK
    assert _the_decisions_recorded_about(reported, the_documents_of(emitted)) == [FLUSH_APPLIED]


def test_a_flush_record_names_the_installation_whose_queue_it_covers(alice: Party) -> None:
    """N9's Requirement keys a flush's records by operation identifier **and clientID**, and this is
    the second of those two, which nothing else in either module asks for.

    **Every other case here joins on the operation alone**, so a path that lists the operations and
    binds the request identifier answers all of them while recording nothing about which
    installation sent the queue. That is not a hypothetical gap: C12 makes the clientID the axis the
    dedup cursor is kept on and makes one user's two devices two streams, so the report that arrives
    as *this device has been resending for a week* has no join at all without it and the trail
    cannot tell the two apart.

    The identifier is minted by the arrangement rather than read back from the response, so a record
    carrying some clientID rather than this queue's is red."""
    applied = uuid4()
    installation = uuid4()
    browser = a_browser(authenticated_as=alice.user_id)

    with the_lines_the_logging_path_emits() as emitted:
        response = browser.post(
            OPERATIONS_PATH,
            _a_contiguous_queue_of(
                applied, by=alice, from_installation=installation, starting_at=0
            ),
            JSON,
        )

    keyed = _the_records_naming(applied, the_documents_of(emitted))

    assert response.status_code == HTTPStatus.OK
    assert _the_field_each_record_carries(CLIENT_ID, keyed) == [str(installation)]


def test_a_flush_record_names_the_tenant_the_decision_was_taken_in(alice: Party) -> None:
    """N9's mechanism half names four correlation keys and the tenant is one of them: without this
    case the whole suite passes over records that never say whose data the decision was about.

    **The reason it is a key rather than a convenience is C4.** Every row this flush touched lives
    behind the tenant wall and every question asked of the trail afterwards is asked by or about one
    account, so a decision trail that cannot be scoped to a tenant is one a support desk has to read
    across all of them. It is also the key an implementation reasoning from this suite alone is
    likeliest to leave out, which is why it is asserted rather than assumed.

    Separate from the case above it because the two keys reach the record by different routes: the
    clientID is the client's own claim travelling in the envelope, while the tenant is the one the
    server bound the transaction to (ADR-0005 section 3), so a path could carry either and not the
    other."""
    applied = uuid4()
    browser = a_browser(authenticated_as=alice.user_id)

    with the_lines_the_logging_path_emits() as emitted:
        response = browser.post(
            OPERATIONS_PATH,
            _a_contiguous_queue_of(applied, by=alice, from_installation=uuid4(), starting_at=0),
            JSON,
        )

    keyed = _the_records_naming(applied, the_documents_of(emitted))

    assert response.status_code == HTTPStatus.OK
    assert _the_field_each_record_carries(TENANT_ID, keyed) == [str(alice.tenant_id)]


def test_an_operation_the_cursor_had_already_seen_is_recorded_as_dropped_and_not_as_applied(
    alice: Party,
) -> None:
    """N9's Requirement naming the dedup decision by name, and ADR-0011 section 4's one exception to
    the per-decision record: the dedup drop is genuinely per operation, so it gets one each.

    **This is the report the trail exists for.** A user whose flush answered `200` and whose edit is
    not on the server has exactly one question, and the difference between *applied* and *dropped as
    already applied* is the whole answer. A path recording only what it wrote leaves that user with
    silence, which is the failure N9's moral line refuses.

    The single operation is the boundary this axis turns on: the cursor after the first flush is
    zero, which is also the first mutation number, so an implementation reading an absent cursor as
    a stored zero is caught here rather than reported as a drop that never happened (M4's Shape)."""
    resent = uuid4()
    installation = uuid4()
    browser = a_browser(authenticated_as=alice.user_id)

    _the_server_took(
        browser,
        _a_contiguous_queue_of(resent, by=alice, from_installation=installation, starting_at=0),
    )
    with the_lines_the_logging_path_emits() as emitted:
        again = browser.post(
            OPERATIONS_PATH,
            _a_contiguous_queue_of(resent, by=alice, from_installation=installation, starting_at=0),
            JSON,
        )

    assert again.status_code == HTTPStatus.OK
    assert _the_decisions_recorded_about(resent, the_documents_of(emitted)) == [FLUSH_DEDUPLICATED]


def test_a_stream_the_server_could_not_continue_is_recorded_with_the_reason_the_client_was_shown(
    alice: Party,
) -> None:
    """N9's clause that every user-visible refusal has a matching record, asserted as a match rather
    than as an existence: the record names the reason this client was refused for, so a path
    recording *some* refusal for a request that was refused for a different one is red.

    Why that matters here specifically: this route answers one status for two reasons whose remedies
    differ (ADR-0010 decision 6's addition of 2026-08-13), and a support desk reading the trail is
    deciding between telling a client to resend from a number and telling it to rehandshake. A
    record that collapses them is a record that answers the wrong one.

    **Which of the two this case arranged is witnessed rather than assumed**, the instrument
    `test_the_typed_resend_on_a_gap.py` built for its own cases on the same measured ground: a
    server that never advances a cursor refuses this very batch with `no_cursor_in_this_domain`, so
    a case comparing the record against whatever the body happened to say would call that a gap and
    stay green.

    This refusal is raised inside the binding and taken outside it, so it is the gap the module
    docstring's rollback paragraph names first."""
    installation = uuid4()
    browser = a_browser(authenticated_as=alice.user_id)

    _the_server_took(
        browser,
        _a_contiguous_queue_of(
            uuid4(), uuid4(), by=alice, from_installation=installation, starting_at=0
        ),
    )
    with the_lines_the_logging_path_emits() as emitted:
        refused = browser.post(
            OPERATIONS_PATH,
            _a_contiguous_queue_of(
                uuid4(), by=alice, from_installation=installation, starting_at=3
            ),
            JSON,
        )

    recorded = _the_records_of(REQUEST_REFUSED, the_documents_of(emitted))

    assert refused.status_code == HTTPStatus.CONFLICT
    assert refused.json()[THE_REASON_IN_THE_BODY] == A_GAP_ABOVE_THE_CURSOR
    assert _the_reasons_recorded(recorded) == [A_GAP_ABOVE_THE_CURSOR]


def test_a_batch_refused_before_any_handler_is_entered_still_leaves_a_record(alice: Party) -> None:
    """ADR-0011 section 7 with N9's every-refusal clause. The five composition rules run in a
    Pydantic `model_validator` on the request body, so this refusal is answered with **no frame of
    ours on the stack at all** and a path built only where this codebase handles something records
    nothing for it.

    That is not an edge: it is four of this route's seven refusals, and a client that flushed a
    malformed queue and was told `422` is precisely the report nobody can answer without a record.

    The status is the positive control and it is doing real work, since a request refused by the
    credential or by the CSRF check also produces no flush record and would satisfy an existence
    assertion on its own."""
    browser = a_browser(authenticated_as=alice.user_id)
    two_tenants = {
        "operations": [
            a_feature_create_claiming(alice.tenant_id),
            a_feature_create_claiming(uuid4()),
        ]
    }

    with the_lines_the_logging_path_emits() as emitted:
        refused = browser.post(OPERATIONS_PATH, two_tenants, JSON)

    recorded = _the_records_of(REQUEST_REFUSED, the_documents_of(emitted))

    assert refused.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert _the_field_each_record_carries(STATUS, recorded) == [HTTPStatus.UNPROCESSABLE_ENTITY]


def test_an_operation_type_the_generated_union_refuses_still_leaves_a_record(
    alice: Party,
) -> None:
    """The sibling of the case above on the other pre-handler shape, and not a duplicate of it. That
    refusal is taken by a validator this repository wrote, decided in ADR-0010 decision 6 whose
    fifth rule is dated 2026-08-13; this one is taken by the **generated** discriminated union of
    M8's closed catalog, probed 2026-08-07 and recorded in `dependencies.md`, which is code nobody
    here may edit and which raises before the validator is ever reached. ADR-0011 section 7 names
    both, and a seam that caught one and not the other would leave the whole catalog boundary
    silent.

    Both surface as `ninja.errors.ValidationError`, which the pinned django-ninja registers by
    default, so the seam ADR-0011 section 7 made conditional exists and the acceptance needs no
    split on that ground. The measurement behind that sentence is cited rather than repeated here:
    it is `specs/dependencies.md`'s subsection on the four default handlers, which is where a
    version-pinned particularity belongs and where this one was moved after being found living in a
    test docstring, the one place no grep looks and no fan-out reaches."""
    browser = a_browser(authenticated_as=alice.user_id)
    outside_the_catalog = a_feature_create_claiming(alice.tenant_id)
    outside_the_catalog["operation_type"] = "feature.invented"

    with the_lines_the_logging_path_emits() as emitted:
        refused = browser.post(OPERATIONS_PATH, {"operations": [outside_the_catalog]}, JSON)

    recorded = _the_records_of(REQUEST_REFUSED, the_documents_of(emitted))

    assert refused.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert _the_field_each_record_carries(STATUS, recorded) == [HTTPStatus.UNPROCESSABLE_ENTITY]


def test_a_claim_the_principal_cannot_back_is_recorded_though_the_client_is_told_nothing(
    alice: Party, bob: Party
) -> None:
    """N9's every-refusal clause on the one refusal whose **response says nothing on purpose**.
    T6.5 requires this answer to be indistinguishable from a resource that never existed, so the
    body may not say which tenant, which membership or which reason (ADR-0010 decision 6), and the
    record is therefore the only place that reason exists at all. A path that skipped it would leave
    a client whose queue can never flush facing a support desk with nothing to read.

    **So the reason is asserted and not only the status**, which is what that argument obliges: a
    record carrying the status alone reproduces in the trail exactly the silence the body is
    required to keep, and satisfies the clause on paper while answering nobody. What the reason
    *says* is not pinned to a literal here, because ADR-0011 section 4 closes the field names and
    the event names and no document names this refusal's reason value.

    **What the reason is read through is load-bearing** (corrected 2026-08-14). Read raw, an absent
    field raises before the status assertion below has run, so the case reports a missing key while
    saying nothing about whether the refusal even happened, and a null one reads as the string
    `"None"` and passes a check for emptiness. `_the_reasons_recorded` normalises both to the empty
    string, and the status assertion above it is what makes an empty list fail rather than pass.

    The status is the positive control and it separates this from the refusal beside it: a batch
    that is malformed answers 422 and never reaches the verification, so a record with the wrong
    status would be a record about a different refusal entirely."""
    browser = a_browser(authenticated_as=bob.user_id)

    with the_lines_the_logging_path_emits() as emitted:
        refused = browser.post(
            OPERATIONS_PATH,
            _a_contiguous_queue_of(uuid4(), by=alice, from_installation=uuid4(), starting_at=0),
            JSON,
        )

    recorded = _the_records_of(REQUEST_REFUSED, the_documents_of(emitted))

    assert refused.status_code == HTTPStatus.NOT_FOUND
    assert _the_field_each_record_carries(STATUS, recorded) == [HTTPStatus.NOT_FOUND]
    assert "" not in _the_reasons_recorded(recorded)


def test_a_project_claim_the_verified_tenant_cannot_back_is_recorded_though_it_too_says_nothing(
    alice: Party, bob: Party
) -> None:
    """N9's every-refusal clause on the second answer this route keeps silent on purpose, and the
    mirror of the case above rather than a repetition of it. That one refuses a **tenant** claim
    before anything binds; this one refuses a **project** claim from a principal whose tenant claim
    was good, after the binding and before the cursor is read (ADR-0010 decision 6's addition of
    2026-08-20). Two mechanisms, one status, one empty body, so the record is the only thing that
    can ever tell a support desk which of them answered.

    **The reason is therefore asserted present rather than only the status**, for the reason its
    sibling gives: a record carrying the status alone reproduces in the trail exactly the silence
    the body is required to keep. What the reason *says* is not pinned to a literal, because
    ADR-0011 section 4 closes the field names and the event names and leaves the 404's reason value
    to the window that emits it, and it is read through `_the_reasons_recorded` because an absent
    field raises before the status assertion could show anything and a null one reads as `"None"`.

    The status is the positive control and it separates this refusal from the two it stands beside:
    a malformed batch answers 422 and never reaches the verification at all."""
    browser = a_browser(authenticated_as=alice.user_id)
    on_a_project_of_bobs = {
        "operations": [a_feature_create_claiming(alice.tenant_id, project_id=bob.project_id)]
    }

    with the_lines_the_logging_path_emits() as emitted:
        refused = browser.post(OPERATIONS_PATH, on_a_project_of_bobs, JSON)

    recorded = _the_records_of(REQUEST_REFUSED, the_documents_of(emitted))

    assert refused.status_code == HTTPStatus.NOT_FOUND
    assert _the_field_each_record_carries(STATUS, recorded) == [HTTPStatus.NOT_FOUND]
    assert "" not in _the_reasons_recorded(recorded)


def test_a_failure_nobody_planned_for_is_silent_neither_to_the_client_nor_to_the_trail(
    alice: Party,
) -> None:
    """N9's acceptance that *a failure with no user-visible signal and no record fails review*, in
    scope as written rather than narrowed: it is the moral line of the whole requirement, and the
    two ways to break it are answering nothing and recording nothing.

    **The failure is a real one and not a refusal in disguise.** Every other case in this module
    arranges an answer the route was written to give; this one breaks the write underneath it, so
    the flush meets something no rule of ours anticipated, which is the only arrangement that tests
    what happens when the plan runs out.

    **The record is reachable and its shape is not this case's to pick**, which is ADR-0011 section
    7's second note of 2026-08-14 correcting its first. django-ninja's default `Exception` entry is
    a pass-through at DEBUG false, `if not settings.DEBUG: raise exc`, so the failure travels on,
    Django's own `log_response` writes the record, and it crosses the root handler like any other
    and acquires the bound keys there. Registering a handler of ours buys control over the record's
    shape rather than its existence, so nothing here reads a handler. The same measurement is the
    trap recorded on `a_browser`: the 500 the user receives is Django's, and a client left on its
    default settings re-raises it instead of reporting it.

    **The event is pinned and the fold it refuses is named in the ADR.** `request.failed` is a
    separate name from `request.refused` because a refusal is a decision the server took and carries
    a reason from a closed set, while a failure is a decision nobody took and has no reason to give
    (ADR-0011 section 4, addition of 2026-08-14). A trail that called this one a refusal would
    answer the support desk's first question, whether anything decided anything at all, with the
    wrong word; reading the status without the event admitted exactly that and no longer does.

    The status of the recorded answer is compared as a set rather than a count, because a path that
    records this failure once and one that records it at two frames are the same answer to the
    clause, while a path that records a different status or nothing at all is not."""
    what_the_client_was_told, documents = _a_flush_meeting(
        the_write_failing_when_it_reaches(OperationLogEntry._meta.db_table),
        uuid4(),
        by=alice,
        from_installation=uuid4(),
        starting_at=0,
    )

    recorded = _the_records_of(REQUEST_FAILED, documents)

    assert what_the_client_was_told == HTTPStatus.INTERNAL_SERVER_ERROR
    assert set(_the_field_each_record_carries(STATUS, recorded)) == {
        HTTPStatus.INTERNAL_SERVER_ERROR
    }


def test_a_flush_that_failed_is_reached_from_the_operation_it_was_about(alice: Party) -> None:
    """N9's reconstruction is a join **from one operation identifier a user quotes**, and the case
    above it asks only whether the failure was recorded at all. A record that exists and carries no
    join key answers the clause and answers nobody: the report that arrives is *my edit is gone*
    with an identifier attached, and a trail that leads from that identifier to `flush.applied` and
    `flush.deduplicated` and never to the failure tells that user their work landed.

    **What makes it red:** the failure leaves the frames that knew which operations it was about,
    so the record that names it is written where only the request is still known. Nothing that
    names the quoted operation says the flush failed, and the reconstruction stops one step short
    of the only interesting answer.

    **What would pass it dishonestly:** recording a failure against every operation of every
    request, which the first case in this module refuses by asserting an accepted flush's trail is
    exactly `flush.applied`. Interpolating the identifiers into the message is the other, and
    `_the_records_naming` refuses it by reading the field as the list ADR-0011 section 4 closes.

    The `500` is the control, the same one its sibling above carries: every other end this route
    has is a refusal with a status of its own, so any other answer means the case never met a
    failure at all."""
    attempted = uuid4()

    what_the_client_was_told, documents = _a_flush_meeting(
        the_write_failing_when_it_reaches(OperationLogEntry._meta.db_table),
        attempted,
        by=alice,
        from_installation=uuid4(),
        starting_at=0,
    )

    reached = _the_records_of(REQUEST_FAILED, _the_records_naming(attempted, documents))

    assert what_the_client_was_told == HTTPStatus.INTERNAL_SERVER_ERROR
    assert reached != []


def test_a_flush_that_deduplicated_before_it_failed_leads_back_to_the_operations_that_failed(
    alice: Party,
) -> None:
    """N9's reconstruction clause meeting the ordinary partial resend C12 makes routine: a client
    resends its whole queue, the server drops what it had already applied and then fails on what
    was left, and the report that arrives quotes an operation from the half that failed.

    **Why the drop is on the path at all when the flush it rode in never committed**, which is the
    same discriminator the commit case below reads from the other end (ADR-0011 section 4's
    correction of 2026-08-17): ask what the record would be false about if the transaction
    vanished. A drop asserts that an *earlier* flush already applied the operation, which is true
    whether or not this one commits, so it is emitted where it is taken, and deferring it to a
    commit that never comes would lose the one record a resent-and-then-failed flush has to offer.
    This case is where that loss would show.

    **The case above it cannot see this, and one deduplicated operation is the whole difference.**
    It arranges a flush with nothing to drop, so the only correlation ever bound for that request
    is the batch itself and any record of the failure names the quoted operation anyway. A resend
    after a partial flush is the ordinary shape rather than an exotic one (C12, T2.3), and it is
    where a narrower binding, opened per dropped operation because the dedup is the one decision
    that is genuinely per operation (ADR-0011 section 4), meets the record written from what the
    request still remembers.

    **What makes it red:** the failure is recorded after every frame that knew which operations it
    covered has unwound, so the trail leads from the operation the flush *dropped* and not from the
    one it lost, and the user who quotes the second is told nothing about it. ADR-0011 section 2's
    sharpening of 2026-08-17 fixes the merge as widest-first for exactly this, so a narrow binding
    stays narrow on its own record without narrowing what the request remembers.

    **What would pass it dishonestly:** recording a failure against every operation of every
    request, which the first case in this module refuses by asserting an accepted flush's trail is
    exactly `flush.applied`; and holding one correlation open past the request that opened it,
    which ADR-0011 section 2 refuses with its own reason and which no case here witnesses. **What
    it does not refuse is a drop that names too much**: a path that stopped narrowing per dropped
    operation satisfies every assertion below while answering a report about one dropped operation
    with every other operation's drop, and nothing in this module can see that.

    The deduplication is witnessed rather than assumed, the control `_the_server_took` exists for:
    a resend that quietly stopped being dropped would leave this case a copy of its sibling and
    green for a reason it is not about. The `500` is the other control, every other end this route
    has being a refusal carrying a status of its own.

    **Both trails are read through `_the_records_of` and not through
    `_the_decisions_recorded_about`, which is the obvious-looking reader and raises here.** A
    failing flush puts a record on the path that names an operation and carries no event of ours,
    Django's own answer to the 500 acquiring the keys from the request, so a reader that subscripts
    the event reports a missing key while saying nothing about the decision it was asked for."""
    dropped, failed = uuid4(), uuid4()
    installation = uuid4()

    _the_server_took(
        a_browser(authenticated_as=alice.user_id),
        _a_contiguous_queue_of(dropped, by=alice, from_installation=installation, starting_at=0),
    )
    what_the_client_was_told, documents = _a_flush_meeting(
        the_write_failing_when_it_reaches(OperationLogEntry._meta.db_table),
        dropped,
        failed,
        by=alice,
        from_installation=installation,
        starting_at=0,
    )

    assert what_the_client_was_told == HTTPStatus.INTERNAL_SERVER_ERROR
    assert _the_records_of(FLUSH_DEDUPLICATED, _the_records_naming(dropped, documents)) != []
    assert _the_records_of(REQUEST_FAILED, _the_records_naming(failed, documents)) != []


def test_no_flush_is_recorded_as_applied_over_a_transaction_that_never_committed(
    alice: Party,
) -> None:
    """ADR-0011 section 4's extension of 2026-08-17, which that note calls the direction no case
    covers: a record asserting a decision took effect is emitted only once the transaction that
    effected it has committed.

    **Why this record waits while the drop its sibling reads does not**, which is the correction
    that section took hours later and the reason neither docstring could give before: ask what the
    record would be false about if the transaction vanished. An application would be false about
    the write, so it waits for the commit; a refusal and a drop would still be true, so they stay
    where they are taken.

    **What makes it red:** logging is not transactional, so a record written inside a transaction
    outlives that transaction's rollback, and the trail then reads *applied* over a database
    holding nothing. That database is the second assertion, measured rather than argued, and it is
    the mirror of N9's requirement that every recorded refusal was one a user was actually shown.

    **What would pass it dishonestly:** never recording `flush.applied` at all, which **four**
    cases in this module refuse between them, two naming the event and two reading a field off the
    record that names the operation (counted rather than gestured at); and emitting it after the
    last statement but still inside the transaction, which is why the fault is a deferred constraint
    rather than the execute wrapper its sibling above uses, for the reason
    `the_commit_refused_after_everything_was_written` gives.

    The `500` is the first control and it says the flush got as far as its commit: every other way
    this route ends is a refusal carrying a status of its own, so a `409`, a `404` or a `422` here
    would mean the arrangement never reached the direction this case is about."""
    attempted = uuid4()

    what_the_client_was_told, documents = _a_flush_meeting(
        the_commit_refused_after_everything_was_written(),
        attempted,
        by=alice,
        from_installation=uuid4(),
        starting_at=0,
    )

    with tenant_scope(alice.tenant_id):
        what_the_log_holds = OperationLogEntry.objects.filter(operation_id=attempted).count()

    assert what_the_client_was_told == HTTPStatus.INTERNAL_SERVER_ERROR
    assert what_the_log_holds == 0
    assert _the_records_of(FLUSH_APPLIED, documents) == []


def test_a_flush_the_server_accepted_records_no_refusal(alice: Party) -> None:
    """N9's *and the reverse*: every recorded refusal was presented. The quiet side of the rule, and
    it is here for the reason the dedup suite gives for its own quiet cases: a rule witnessed only
    where it fires is satisfied by an implementation that always fires, and a trail that logs a
    refusal for every flush is a trail that sends a support desk hunting a failure the user never
    saw.

    The applied record is asserted beside the empty one so this cannot pass by emitting nothing at
    all, which is what an accepted flush and a path that does not exist have in common."""
    applied = uuid4()
    browser = a_browser(authenticated_as=alice.user_id)

    with the_lines_the_logging_path_emits() as emitted:
        response = browser.post(
            OPERATIONS_PATH,
            _a_contiguous_queue_of(applied, by=alice, from_installation=uuid4(), starting_at=0),
            JSON,
        )

    documents = the_documents_of(emitted)

    assert response.status_code == HTTPStatus.OK
    assert _the_decisions_recorded_about(applied, documents) == [FLUSH_APPLIED]
    assert _the_records_of(REQUEST_REFUSED, documents) == []
