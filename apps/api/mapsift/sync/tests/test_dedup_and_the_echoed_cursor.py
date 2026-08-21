"""The server's memory of how far each installation got, and the answer that hands it back.

Trace: PRD T2.3 (the per-client mutation number, the dedup by the server's cursor, and the echo,
with the clause added 2026-08-11), M4 (the clientID and its server cursor, Shape sharpened the same
day and **corrected the same day at this suite's review**), M10's Requirement and Shape (the
contiguity domain, and the first mutation number is zero); I9; C12, C4; foundation section 4, whose
v0.8 Decision block was sharpened to this key in v0.18. ADR-0004 decision 2's extension of
2026-08-11 for where the cursor's read and its write sit around the critical section, and ADR-0010
decision 6 for the request body and for the response key.

**The cursor is keyed by clientID, tenant and project together**, which is the correction that
reached this module: the first form keyed it on tenant and clientID, and a suite that never sends
two projects is green against both. Two of the cases below are the axis witnesses that tell them
apart, one per axis, and neither is a variation on the other. The tenant axis has no case here on
purpose, because it is not this suite's to buy: carrying the tenant column is what puts the table
inside the wall, and the wall's own catalogue suite is then what holds every unique key led by the
tenant (`test_client_cursor_table.py`, C4, ADR-0005 section 3).

**Everything here goes through the route and never through the writer.** `tenant_scope` opens
`transaction.atomic()` itself (`mapsift/common/binding.py`, read 2026-08-10), so a test whose only
transaction is the one its own context manager opened is green against an implementation that has
none. The echo has no other seam in any case, being a response body.

**Every queue here starts at mutation number zero**, which is M10's Shape rather than a convention
this module picked, and it is the value that cannot double as a sentinel for an absent cursor. An
implementation reading a missing cursor as a stored zero drops the first operation of every
installation, and the cases that catch that name it in their own docstrings rather than being given
a case of their own.

**What a batch may be composed of is not here, and the precondition it carries is why it is not.**
The dedup is keyed by the clientID, so a flush has to read one off its batch; that rule is ADR-0010
decision 6's addition of 2026-08-11 and it is proved in `test_batch_client_agreement.py`, beside
the tenant's and the project's own agreement modules rather than inside the module that consumes
it. Every queue below therefore names one installation, and a batch that did not would be refused
before it arrived.

**No post in this module goes unwitnessed**, which is the general form of a gap found in one case at
the second review: this route gains a typed refusal with nearly every task in this milestone, a
fourth of them at this task's own review, so an arrange step that quietly starts being refused
leaves most of the assertions below true and the module goes vacuous rather than red. Every post
whose response is not the subject of an assertion therefore goes through `_the_server_took`.

What is deliberately not here, each with the issue that owns it: the contiguity check, the typed
resend on a gap and M4's missing-cursor reconciliation (MAP-13), which no queue below meets, since
each of them either opens at the first mutation number or continues from the cursor it flushes
against; the cursor's expiry and the last-seen time (MAP-42); the per-project version
in the response (MAP-22); the check that a batch's project belongs to the verified tenant (MAP-39);
and every client half of this axis (MAP-15, MAP-17, MAP-19). **And the guard that stops a cursor
moving backwards under a lost race is next door**, in `test_the_cursor_under_a_lost_race.py`, which
is where this suite's second database connection lives (MAP-43): it needs two concurrent
transactions and every case here runs on one. Convergence (MAP-23, C2) and the resync (MAP-22) each
extend that harness rather than this module.
"""

from collections.abc import Sequence
from http import HTTPStatus
from uuid import UUID, uuid4

import pytest
from django.test import Client

from conftest import (
    JsonObject,
    Party,
    a_browser,
    a_feature_create_claiming,
    second_project_of,
    statements_reaching,
    the_writes_among,
)
from mapsift.common.binding import tenant_scope
from mapsift.sync.models import ClientCursor, OperationLogEntry, ProjectVersionCounter

pytestmark = pytest.mark.django_db(transaction=True)

OPERATIONS_PATH = "/api/operations"
JSON = "application/json"

# The one key this slice's response body carries (ADR-0010 decision 6, addition of 2026-08-11).
THE_ECHO = "last_applied_mutation_number"


def _a_queue_of(
    operation_ids: Sequence[UUID],
    *,
    by: Party,
    from_installation: UUID,
    starting_at: int = 0,
    in_project: UUID | None = None,
) -> JsonObject:
    """One installation's queue, in one project of one tenant, from a given mutation number.

    Zero is the default because that is where a client's first queue starts (M10's Shape); the knob
    exists for the batch that resends an operation the server already holds under a later number.
    The project is settable for the same reason on the axis the corrected cursor key added: it is
    part of the domain the contiguity is measured in (M10's Requirement), so a suite that cannot
    say which project is one that cannot see the key it is about.

    **Named apart from `test_project_version_allocation.py`'s `_a_flush_of` deliberately.** That one
    takes varargs and mints its installation internally; this one takes a sequence and is told its
    installation, because every case here needs two flushes of the *same* one. A single name over
    two signatures disagreeing on arity is a grep that misleads whoever runs it.
    """
    return {
        "operations": [
            a_feature_create_claiming(
                by.tenant_id,
                operation_id=operation_id,
                client_id=from_installation,
                mutation_number=mutation_number,
                project_id=in_project or by.project_id,
            )
            for mutation_number, operation_id in enumerate(operation_ids, start=starting_at)
        ]
    }


def _the_server_took(browser: Client, batch: JsonObject) -> None:
    """Post a batch whose landing is arranged rather than asserted, and witness that it landed.

    The module docstring carries why every such post comes through here: a route that collects a
    new typed refusal each task turns a silent arrange failure into a suite that agrees with
    itself about nothing.
    """
    assert browser.post(OPERATIONS_PATH, batch, JSON).status_code == HTTPStatus.OK


def _the_operations_in_the_log(party: Party) -> list[UUID]:
    """Every operation the log holds for a tenant, in the order its project's version puts them."""
    with tenant_scope(party.tenant_id):
        return list(
            OperationLogEntry.objects.order_by("project_version").values_list(
                "operation_id", flat=True
            )
        )


def test_a_queue_resent_whole_after_a_partial_flush_lands_only_what_was_missing(
    alice: Party,
) -> None:
    """C12 and T2.3's first acceptance clause. A flush is transactional, so a queue is never half
    applied inside one call (MAP-11 pins that rollback); what "the server applies part of the queue"
    reaches on this path is the bounded batch of ADR-0004 decision 3 landing and its answer never
    arriving, after which the client resends everything it still holds. Each of the four operations
    has to come back exactly once: a server that deduplicates nothing is refused by the log's unique
    key and loses the two new ones with it, and a server that deduplicates past the cursor loses
    them silently, which is worse. The queue starts at mutation number zero, so an implementation
    reading an absent cursor as a stored zero fails here on the first operation (M4, M10)."""
    installation = uuid4()
    queued = [uuid4(), uuid4(), uuid4(), uuid4()]
    browser = a_browser(authenticated_as=alice.user_id)

    _the_server_took(browser, _a_queue_of(queued[:2], by=alice, from_installation=installation))
    resent = browser.post(
        OPERATIONS_PATH,
        _a_queue_of(queued, by=alice, from_installation=installation),
        JSON,
    )

    assert resent.status_code == HTTPStatus.OK
    assert _the_operations_in_the_log(alice) == queued


def test_two_installations_of_one_user_hold_streams_that_never_dedup_against_each_other(
    alice: Party,
) -> None:
    """C12 and T2.3's third acceptance clause, with M4: a client is a persistent installation rather
    than the user, so one person on a laptop and on a field tablet is two streams. Both start at
    mutation number zero, which is what makes a cursor keyed on anything coarser than the
    installation deduplicate the second queue away in its entirety. This case is quiet by nature and
    passes before any dedup exists, and it is here for exactly that reason: a rule witnessed only
    where it fires is satisfied by an implementation that always fires."""
    on_the_laptop = [uuid4(), uuid4()]
    on_the_tablet = [uuid4(), uuid4()]
    browser = a_browser(authenticated_as=alice.user_id)

    _the_server_took(browser, _a_queue_of(on_the_laptop, by=alice, from_installation=uuid4()))
    _the_server_took(browser, _a_queue_of(on_the_tablet, by=alice, from_installation=uuid4()))

    assert _the_operations_in_the_log(alice) == [*on_the_laptop, *on_the_tablet]


def test_two_projects_of_one_tenant_hold_cursors_that_never_dedup_against_each_other(
    alice: Party,
) -> None:
    """M4's Shape as corrected 2026-08-11, with M10's Requirement, foundation v0.18's sharpening of
    the v0.8 Decision block, and ADR-0010 decision 6; the sibling of the case above on the axis that
    correction added. A flush addresses exactly one project, so the stream is contiguous per
    clientID within one tenant and one project and the cursor is keyed the same way. One
    installation working in two projects opens each at mutation number zero, and a cursor keyed on
    tenant and clientID alone reads the second of them as a queue it has already applied: that
    project's work is deduplicated away entirely and lost in silence, which is the failure the
    corrected key exists against. One operation each rather than a queue, because zero is where the
    two keys disagree. The assertion is over a set, since two projects carry two independent version
    sequences and the order between them is nobody's.

    Green before any dedup exists, like the sibling above and for the same reason: both are the
    quiet side of a conditional rule, and a rule witnessed only where it fires is satisfied by an
    implementation that always fires. What this one adds is that it also stays green against a
    cursor keyed too coarsely **until that cursor exists**, so it is the case the review's Canon
    finding would have had no witness without."""
    on_this_project, on_the_other = uuid4(), uuid4()
    installation = uuid4()
    elsewhere = second_project_of(alice)
    browser = a_browser(authenticated_as=alice.user_id)

    _the_server_took(
        browser, _a_queue_of([on_this_project], by=alice, from_installation=installation)
    )
    _the_server_took(
        browser,
        _a_queue_of([on_the_other], by=alice, from_installation=installation, in_project=elsewhere),
    )

    assert set(_the_operations_in_the_log(alice)) == {on_this_project, on_the_other}


def test_a_flush_answers_with_the_last_mutation_number_it_applied(alice: Party) -> None:
    """T2.3 and C12: the client advances its cursor only from this echo and never by assumption, so
    the flush has to say how far it got. The whole body is compared rather than one key of it,
    because ADR-0010 decision 6's addition of 2026-08-11 closes the object: an unexpected key is a
    contract change and goes through that ADR, and MAP-22 is what takes it there."""
    browser = a_browser(authenticated_as=alice.user_id)

    response = browser.post(
        OPERATIONS_PATH,
        _a_queue_of([uuid4(), uuid4(), uuid4()], by=alice, from_installation=uuid4()),
        JSON,
    )

    assert response.json() == {THE_ECHO: 2}


def test_an_applied_flush_writes_this_installations_cursor(alice: Party) -> None:
    """T2.3 and C12 with M4, the storage side of the case above: the echo is the only thing a
    client advances from, and the server can only echo on the next flush what it kept on this one,
    so an applied flush has to leave that row written. **Already true and already covered
    indirectly**, by the dedup this module witnesses throughout, which a server keeping no cursor
    cannot deliver at all; this case introduces no criterion and pins no product guarantee this
    module did not already carry.

    **It is here to arm `the_writes_among`, and the false green it closes was reproduced twice
    before it could reach `main`.** Measured 2026-08-20, before this case existed, with that
    helper's body replaced by `return []` through a scratch `conftest.py` mounted over the
    container path: the whole suite stayed green at 247 passed, and against a server advancing the
    cursor **before** refusing a gap the module reading it stayed green at 7 passed as well. That
    is the exact defect `test_a_refused_flush_leaves_this_installations_cursor_where_it_was`
    (`test_the_typed_resend_on_a_gap.py`) exists to close, reproduced one layer down in the
    instrument that case reads, and a witness nothing can make fail is not one.

    **The assertion is that a write happened and deliberately not that exactly one did.** The
    cursor being raised in a single statement of its own is ADR-0004 decision 2's extension of
    2026-08-11, with reasons of its own about which row is contended and for how long, so counting
    here would fold a second behaviour into a case about something else.

    **Here rather than beside the case it arms**, on the precedent the sibling instrument already
    set: `statements_reaching` is kept honest by `test_project_version_allocation.py`'s lock count,
    in the module whose subject is the write, while the two cases reading it for an *absence* sit
    in this module and in the gap module and ride on that one. The subject here is the server's
    memory of how far this installation got, which is this module's first line."""
    browser = a_browser(authenticated_as=alice.user_id)

    with statements_reaching(ClientCursor._meta.db_table) as reaching_the_cursors_table:
        _the_server_took(browser, _a_queue_of([uuid4()], by=alice, from_installation=uuid4()))

    assert the_writes_among(reaching_the_cursors_table) != []


def test_a_batch_the_cursor_has_already_seen_appends_nothing_to_the_log(alice: Party) -> None:
    """T2.3 and M10: an operation at or below the cursor is ignored. One operation at mutation
    number zero rather than a longer queue, because that is the boundary this axis turns on: the
    cursor's value after the first flush is zero, and an implementation representing an absent
    cursor as a stored zero cannot tell an installation that has applied through zero from one it
    has never met, and applies the resend (M4's Shape, M10's Shape)."""
    already_flushed = [uuid4()]
    installation = uuid4()
    browser = a_browser(authenticated_as=alice.user_id)

    _the_server_took(
        browser, _a_queue_of(already_flushed, by=alice, from_installation=installation)
    )
    _the_server_took(
        browser, _a_queue_of(already_flushed, by=alice, from_installation=installation)
    )

    assert _the_operations_in_the_log(alice) == already_flushed


def test_a_batch_the_cursor_has_already_seen_takes_no_per_project_version(alice: Party) -> None:
    """Boundary decision 6 of 2026-08-11 with ADR-0004 decision 2: a batch deduplicated away
    entirely applies nothing and allocates nothing. Asserted as statements reaching the counter
    rather than as a version that did not move, because allocating a range of zero leaves the number
    untouched and still takes the one hot row per project that this strategy's Consequences accept
    as its whole cost. The status is the positive control, on the same argument
    `test_project_version_allocation.py` already makes for the same instrument: a batch refused
    before it ever reached the allocation touches the row zero times too, so the count alone is
    satisfied by a flush that failed for a reason this case is not about."""
    already_flushed = [uuid4()]
    installation = uuid4()
    browser = a_browser(authenticated_as=alice.user_id)

    _the_server_took(
        browser, _a_queue_of(already_flushed, by=alice, from_installation=installation)
    )
    with statements_reaching(ProjectVersionCounter._meta.db_table) as allocation:
        resent = browser.post(
            OPERATIONS_PATH,
            _a_queue_of(already_flushed, by=alice, from_installation=installation),
            JSON,
        )

    assert resent.status_code == HTTPStatus.OK
    assert allocation == []


def test_a_batch_the_cursor_has_already_seen_answers_with_the_cursor_it_did_not_move(
    alice: Party,
) -> None:
    """Boundary decision 6 of 2026-08-11: the flush still answers, and it answers with the cursor
    that was already there. An answer of nothing, or one that started counting again, would have a
    client advance onto a number the server never applied, which is the assumption C12 forbids it to
    make."""
    already_flushed = [uuid4(), uuid4()]
    installation = uuid4()
    browser = a_browser(authenticated_as=alice.user_id)

    _the_server_took(
        browser, _a_queue_of(already_flushed, by=alice, from_installation=installation)
    )
    resent = browser.post(
        OPERATIONS_PATH,
        _a_queue_of(already_flushed, by=alice, from_installation=installation),
        JSON,
    )

    assert resent.json() == {THE_ECHO: 1}


def test_an_operation_the_server_already_holds_is_answered_as_applied_rather_than_refused(
    alice: Party,
) -> None:
    """T2.3's acceptance as added 2026-08-11, whole: answered as applied rather than refused, **so
    the flush succeeds and echoes**. The dedup filter lets this one through because it arrived
    under a mutation number above the cursor, so what meets it is the log's unique key, which is
    ADR-0004 decision 2's extension exactly: the cursor is the cheap path and the constraint is the
    correctness backstop. A refusal here is indistinguishable to a client from a real failure, so
    the retry path C12 exists to make safe becomes the path that breaks.

    **The echo is the load-bearing half and the first form of this case dropped it**, which is the
    Spec finding this suite was blocked on. This is the one path where *applied* and *inserted*
    come apart: nothing was written, so an implementation that advances its cursor from what it
    inserted answers 0 here, passes a status-only assertion, and leaves the client at 0 under C12,
    resending this operation for as long as it holds it."""
    already_held = uuid4()
    installation = uuid4()
    browser = a_browser(authenticated_as=alice.user_id)

    _the_server_took(browser, _a_queue_of([already_held], by=alice, from_installation=installation))
    resent = browser.post(
        OPERATIONS_PATH,
        _a_queue_of([already_held], by=alice, from_installation=installation, starting_at=1),
        JSON,
    )

    assert resent.status_code == HTTPStatus.OK
    assert resent.json() == {THE_ECHO: 1}


def test_a_batch_carrying_an_operation_the_server_already_holds_still_lands_the_rest_of_it(
    alice: Party,
) -> None:
    """C12's no-lost-edit clause on the path the case above opens. The narrow reading of that clause
    is satisfied by a flush that answers OK and discards the whole batch, which is silent loss
    wearing an acknowledgement, and the operation travelling beside the resent one is what refuses
    that reading."""
    already_held, drawn_since = uuid4(), uuid4()
    installation = uuid4()
    browser = a_browser(authenticated_as=alice.user_id)

    _the_server_took(browser, _a_queue_of([already_held], by=alice, from_installation=installation))
    _the_server_took(
        browser,
        _a_queue_of(
            [already_held, drawn_since], by=alice, from_installation=installation, starting_at=1
        ),
    )

    assert _the_operations_in_the_log(alice) == [already_held, drawn_since]
