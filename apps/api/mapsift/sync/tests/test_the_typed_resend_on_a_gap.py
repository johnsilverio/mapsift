"""The second answer this route carries: a stream the server cannot continue is asked for back.

Trace: PRD M10's Requirement (the server applies a client's operations only in contiguous
mutation-number order, and a gap above the cursor is a typed error that asks the client to resend
from the cursor, never a silent skip) with its acceptance as narrowed 2026-08-13 (the flush applies
nothing at all, rather than merely nothing from the gap onward); PRD M4's Requirement and acceptance
(a flush from a clientID the server holds no cursor for in this flush domain is a new client only
when it starts at the first mutation number, and one starting above it is a typed reconciliation,
never applied optimistically); ADR-0010 decision 6's addition of 2026-08-13 for the status, the
closed object, the two reasons and the restart point; ADR-0004 decision 2 for why a refused batch
never reaches the allocation; I9 and I2; C12, C2, C4.

**Everything goes through the route and never through the writer.** `tenant_scope` opens
`transaction.atomic()` itself (`mapsift/common/binding.py`, measured 2026-08-10 at MAP-11), so a
test whose only transaction is the one its own context manager opened is green against an
implementation that has none, and every claim below about what a refused flush left behind depends
on the real one. The two responses have no other seam in any case, being response bodies.

**Every queue here is contiguous within itself**, because a batch that is not is refused one step
earlier, at the Pydantic boundary and before anything is bound
(`test_batch_mutation_contiguity.py`, ADR-0010 decision 6's addition of 2026-08-13). What is left
for this module is the one comparison that boundary cannot take: where the batch starts against the
cursor that installation left behind, which needs the tenant bound and a read.

**Why the status is not 200 with a reason in the body**, since that shape reads as the friendlier
one: a client that reads the status and not the body would take a refusal for an acknowledgement,
and under C12 it advances its cursor from the echo alone, so its own dedup would then drop exactly
the operations the refusal was reporting. That is the silent loss this answer exists to prevent,
reintroduced one layer above it.

What is deliberately not here, each with the issue that owns it: the cursor's expiry and collection
and how a client rehandshakes after being told the server holds none (MAP-42), so nothing below
collects a cursor and the absent one is simply an installation the server has never met; the
two-connection harness (MAP-43), so no case here needs two concurrent flushes; the per-project
version in the response (MAP-22); the check that a batch's project belongs to the verified tenant,
which landed at MAP-39 and is `test_the_project_claim_on_the_flush_path.py`'s, including the case
pinning that it is taken before the cursor this module is about is ever read; and every client half
of this axis, which is minting the clientID, persisting the queue, advancing from the echo and
reacting to either refusal (MAP-15, MAP-17, MAP-19).
"""

from http import HTTPStatus
from uuid import UUID, uuid4

import pytest
from django.test import Client

from conftest import (
    JsonObject,
    Party,
    a_browser,
    a_feature_create_claiming,
    statements_reaching,
    the_writes_among,
)
from mapsift.common.binding import tenant_scope
from mapsift.sync.models import ClientCursor, OperationLogEntry, ProjectVersionCounter

pytestmark = pytest.mark.django_db(transaction=True)

OPERATIONS_PATH = "/api/operations"
JSON = "application/json"

# The one key an accepted flush answers with (ADR-0010 decision 6, addition of 2026-08-11), read
# here only as the control that says a refusal did not quietly move what it refused to apply.
THE_ECHO = "last_applied_mutation_number"

# The closed object a refusal answers with, and the closed set of two its reason comes from
# (ADR-0010 decision 6, addition of 2026-08-13). The restart point names its axis because M10
# carries five and forbids any code path reading one as another.
THE_REASON = "reason"
THE_RESTART_POINT = "resend_from_mutation_number"
A_GAP_ABOVE_THE_CURSOR = "gap_above_cursor"
NO_CURSOR_IN_THIS_DOMAIN = "no_cursor_in_this_domain"


def _a_contiguous_queue_of(
    *operation_ids: UUID,
    by: Party,
    from_installation: UUID,
    starting_at: int,
) -> JsonObject:
    """One installation's queue in one project of one tenant, ascending one at a time from a
    given mutation number (M4, M10, ADR-0010 decision 6).

    **`starting_at` carries no default, unlike the sibling in
    `test_dedup_and_the_echoed_cursor.py`.** Every case in this module is about where a queue begins
    against the cursor behind it, so a default would hide the one field each test is about. Named
    apart from that sibling for the reason its own docstring gives: a single name over two
    signatures disagreeing on arity is a grep that misleads whoever runs it.
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

    This route collects a typed refusal with nearly every task in this milestone and gains two more
    with this one, so an arrange step that quietly starts being refused would leave most of the
    assertions below true and the module vacuous rather than red.
    """
    assert browser.post(OPERATIONS_PATH, batch, JSON).status_code == HTTPStatus.OK


def _the_server_refused_the_gap(browser: Client, batch: JsonObject) -> None:
    """Post a batch whose refusal is arranged rather than asserted, and witness which one it was.

    The sibling of `_the_server_took` on the other answer, and it pins the reason as well as the
    status because this task alone gives one status two reasons: a batch answered
    `no_cursor_in_this_domain`, or refused at the boundary for its own composition, arranges
    something other than what the case that calls this is about while leaving its assertions
    standing.
    """
    refusal = browser.post(OPERATIONS_PATH, batch, JSON)

    assert refusal.status_code == HTTPStatus.CONFLICT
    assert refusal.json()[THE_REASON] == A_GAP_ABOVE_THE_CURSOR


def _the_operations_in_the_log(party: Party) -> list[UUID]:
    """Every operation the log holds for a tenant, in the order its project's version puts them."""
    with tenant_scope(party.tenant_id):
        return list(
            OperationLogEntry.objects.order_by("project_version").values_list(
                "operation_id", flat=True
            )
        )


def test_a_flush_starting_above_the_cursor_is_answered_with_the_number_the_server_needs_next(
    alice: Party,
) -> None:
    """M10's Requirement with ADR-0010 decision 6's addition of 2026-08-13. The client's queue is
    persistent and append-only, so a number the server never saw means an operation was lost rather
    than never created, and the answer has to be one the client can act on: the reason it is being
    refused, and the point to start again from. The whole body is compared rather than one key of
    it, because the addition closes the object exactly as it closed the acknowledgement's, and an
    unexpected key is a contract change that goes through that ADR.

    **409 rather than 200 is the load-bearing half**, and I9's scar is why the distinction has to be
    visible at all: a client recovers from a lost acknowledgement by resending the same batch and
    from a gap by resending from the cursor, so an answer it cannot tell apart from a transport
    failure sends it to the wrong recovery.

    The restart point is the first number the server has not applied, which is the one thing an
    answer naming a restart point can mean: everything from there is what it is missing."""
    installation = uuid4()
    browser = a_browser(authenticated_as=alice.user_id)

    _the_server_took(
        browser,
        _a_contiguous_queue_of(
            uuid4(), uuid4(), by=alice, from_installation=installation, starting_at=0
        ),
    )
    refused = browser.post(
        OPERATIONS_PATH,
        _a_contiguous_queue_of(
            uuid4(), uuid4(), by=alice, from_installation=installation, starting_at=3
        ),
        JSON,
    )

    assert refused.status_code == HTTPStatus.CONFLICT
    assert refused.json() == {THE_REASON: A_GAP_ABOVE_THE_CURSOR, THE_RESTART_POINT: 2}


def test_a_flush_starting_above_the_cursor_applies_nothing_at_all(alice: Party) -> None:
    """M10's acceptance as narrowed 2026-08-13, whose teeth are against an implementation that
    answers the refusal correctly and appends the batch anyway. It does not tell the narrowed form
    from the wider one, because M10's Shape records that no case can while the composition rule
    stands.

    **The append is witnessed as it runs and never as the rows it left**, measured at the MAP-45
    probe of 2026-08-14: it sits inside a transaction the refusal exits by exception, so nothing
    survives for a later read to find and a case reading the log afterwards stays green against a
    writer that appended. What that instrument sees, and what it leaves to the implementation, is
    `statements_reaching`'s own docstring.

    **The refusal is arranged through the helper that pins its reason, and the status alone would
    not do.** This route answers one status for two reasons and the other one reaches this table
    zero times as well: measured 2026-08-14, a server that never advances a cursor refuses this
    batch with `no_cursor_in_this_domain`, and a case reading the status would have called that a
    gap and stayed green."""
    installation = uuid4()
    browser = a_browser(authenticated_as=alice.user_id)

    _the_server_took(
        browser,
        _a_contiguous_queue_of(
            uuid4(), uuid4(), by=alice, from_installation=installation, starting_at=0
        ),
    )
    with statements_reaching(OperationLogEntry._meta.db_table) as the_append:
        _the_server_refused_the_gap(
            browser,
            _a_contiguous_queue_of(
                uuid4(), uuid4(), by=alice, from_installation=installation, starting_at=3
            ),
        )

    assert the_append == []


def test_a_refused_flush_leaves_this_installations_cursor_where_it_was(alice: Party) -> None:
    """M10's acceptance as narrowed 2026-08-13, on the second of the two writes a broken server
    could make before refusing; the first is the append
    `test_a_flush_starting_above_the_cursor_applies_nothing_at_all` witnesses. The cursor is the one
    thing C12 has a client advance from, so a server that raises it and then refuses has told this
    installation the refusal never happened, and the installation's own dedup then drops exactly the
    operations it was being asked to resend (M4; ADR-0004 decision 2's extension of 2026-08-11 for
    where that write sits and why it is one statement of its own).

    **The advance is witnessed as it runs and never as the value it left**, which is the measurement
    of 2026-08-14 that struck the residue
    `test_the_resend_a_refusal_asked_for_lands_whole_rather_than_being_deduplicated_away` had
    claimed: the write sits inside the transaction the refusal exits by exception, so a correct
    server and a broken one leave the same value behind and every case reading state afterwards is
    blind to the difference.

    **The writes are separated from the reads rather than the recording being asserted empty, and
    that is this case's difficulty rather than a nicety.** The flush *reads* this table on this
    path, because reading the cursor is how the gap is detected, so against a correct server the
    recording carries one SELECT (measured 2026-08-20) and the shape that worked for the append does
    not transfer. Asserting the recording whole would pin how many times the flush reads, and
    spelling the write inside this case would put here the knowledge `statements_reaching` exists to
    keep out of it; what counts as a write is `the_writes_among`'s, and what stops that filter
    answering empty to everything is `test_an_applied_flush_writes_this_installations_cursor`
    (`test_dedup_and_the_echoed_cursor.py`), which reads it for the write an accepted flush makes.

    **The refusal is arranged through the helper that pins its reason**, for the reason that
    helper's other caller gives and one this case sharpens: `gap_above_cursor` is raised only
    against a cursor that already exists, so pinning it is what proves the arrange step's flush
    wrote one, and what makes an empty recording here a write withheld rather than a table nothing
    has ever touched."""
    installation = uuid4()
    browser = a_browser(authenticated_as=alice.user_id)

    _the_server_took(
        browser,
        _a_contiguous_queue_of(
            uuid4(), uuid4(), by=alice, from_installation=installation, starting_at=0
        ),
    )
    with statements_reaching(ClientCursor._meta.db_table) as reaching_the_cursors_table:
        _the_server_refused_the_gap(
            browser,
            _a_contiguous_queue_of(
                uuid4(), uuid4(), by=alice, from_installation=installation, starting_at=3
            ),
        )

    assert the_writes_among(reaching_the_cursors_table) == []


def test_a_flush_above_the_first_mutation_number_from_an_installation_with_no_cursor_says_so(
    alice: Party,
) -> None:
    """M4's Requirement and acceptance with ADR-0010 decision 6's addition of 2026-08-13. The
    absence of the cursor row is the only representation of an absent cursor, never a stored zero,
    so an installation the server has never met is exactly the state a collected cursor leaves
    behind, and a flush that does not start at the first mutation number cannot be treated as a new
    client's.

    **The two refusals are one comparison and two remedies, which is why the reason is a field
    rather than an inference.** A client meeting a gap holds the missing operations in its
    persistent queue and can resend them; a client the server holds no cursor for may not hold them
    at all, because the cursor may have been collected under a policy MAP-42 has not written yet.
    The restart point is null for the same reason: naming the first mutation number here would ask
    for what this client no longer has, and the null is what makes the reason actionable instead of
    decorative."""
    browser = a_browser(authenticated_as=alice.user_id)

    refused = browser.post(
        OPERATIONS_PATH,
        _a_contiguous_queue_of(
            uuid4(), uuid4(), by=alice, from_installation=uuid4(), starting_at=2
        ),
        JSON,
    )

    assert refused.status_code == HTTPStatus.CONFLICT
    assert refused.json() == {THE_REASON: NO_CURSOR_IN_THIS_DOMAIN, THE_RESTART_POINT: None}


def test_a_flush_from_an_installation_with_no_cursor_is_never_applied_optimistically(
    alice: Party,
) -> None:
    """M4's Requirement, whose whole reason for refusing rather than applying is that applying it
    blindly would risk re-applying operations the server already holds.

    **The append is witnessed as it runs and never as the rows it left**, the same instrument and
    the same measurement of 2026-08-14 as
    `test_a_flush_starting_above_the_cursor_applies_nothing_at_all`: the refusal exits the
    transaction the append sat in, so nothing survives for a later read to find and a case reading
    the log afterwards stays green against a writer that appended. The log is read as well and
    asserted empty rather than unchanged, which is what an installation the server has never met is
    entitled to: this tenant has flushed nothing at all.

    The status rules out the 401, the 404 and the five malformed-batch refusals, each of which
    reaches this table zero times too. It does not tell the two reasons this one status carries
    apart, and here it does not have to: the answer to this arrangement is the closed object the
    case above pins."""
    browser = a_browser(authenticated_as=alice.user_id)

    with statements_reaching(OperationLogEntry._meta.db_table) as the_append:
        refused = browser.post(
            OPERATIONS_PATH,
            _a_contiguous_queue_of(
                uuid4(), uuid4(), by=alice, from_installation=uuid4(), starting_at=2
            ),
            JSON,
        )

    assert refused.status_code == HTTPStatus.CONFLICT
    assert the_append == []
    assert _the_operations_in_the_log(alice) == []


def test_the_resend_a_refusal_asked_for_lands_whole_rather_than_being_deduplicated_away(
    alice: Party,
) -> None:
    """M10's Requirement and C12 together: the answer asks the client to resend from a point, so
    the server has to still be at that point when the resend arrives. What is witnessed is the
    resend landing whole and in the order the log puts it, rather than being deduplicated away in
    part or entirely.

    The log is what says so rather than the echo, because the echo names a number while what a
    resend has to leave behind is the rows under it: a server answering four having applied none of
    them satisfies the echo on its own.

    **The residue this case was written against is struck rather than claimed**, 2026-08-14 and
    measured: an implementation that advances the cursor and then refuses leaves this case green,
    and every case this module then held with it, because the advance sits inside the transaction
    the refusal exits, exactly as the append does. That property landed at MAP-46 and is
    `test_a_refused_flush_leaves_this_installations_cursor_where_it_was`'s, above, which is not
    blind to that implementation because it witnesses the advance as it runs rather than as the
    value it left."""
    applied = [uuid4(), uuid4()]
    the_missing_one = uuid4()
    # Shared with the refused batch on purpose: this is the resend that refusal asked for, not a
    # second queue. Mint fresh ones and a server deduplicating on operation_id rather than on the
    # per-client cursor (C12) passes this case too.
    above_the_gap = [uuid4(), uuid4()]
    installation = uuid4()
    browser = a_browser(authenticated_as=alice.user_id)

    _the_server_took(
        browser,
        _a_contiguous_queue_of(*applied, by=alice, from_installation=installation, starting_at=0),
    )
    _the_server_refused_the_gap(
        browser,
        _a_contiguous_queue_of(
            *above_the_gap, by=alice, from_installation=installation, starting_at=3
        ),
    )
    filling_the_gap = browser.post(
        OPERATIONS_PATH,
        _a_contiguous_queue_of(
            the_missing_one,
            *above_the_gap,
            by=alice,
            from_installation=installation,
            starting_at=2,
        ),
        JSON,
    )

    assert filling_the_gap.json() == {THE_ECHO: 4}
    assert _the_operations_in_the_log(alice) == [*applied, the_missing_one, *above_the_gap]


def test_a_refused_flush_takes_no_per_project_version(alice: Party) -> None:
    """ADR-0004 decision 2 with M10's narrowed acceptance: a flush left with nothing to apply takes
    no range at all, and a flush that applies nothing at all is that case at its limit. The
    allocating statement creates the counter row on first use and holds it to the commit, so
    reaching it for a batch that is being refused mints or burns a number out of a flush that
    changed nothing, and the resync cursor a client presents then points into a range with no rows
    under it.

    Asserted as statements reaching the counter rather than as a version that did not move, on the
    argument `test_project_version_allocation.py` and `test_dedup_and_the_echoed_cursor.py` both
    already make for this instrument: allocating a range of zero leaves the number untouched while
    still taking the one hot row per project this strategy's Consequences accept as its whole cost.
    The status is the positive control, since a batch refused at the boundary touches the row zero
    times too and would satisfy the count on its own."""
    installation = uuid4()
    browser = a_browser(authenticated_as=alice.user_id)

    _the_server_took(
        browser,
        _a_contiguous_queue_of(
            uuid4(), uuid4(), by=alice, from_installation=installation, starting_at=0
        ),
    )
    with statements_reaching(ProjectVersionCounter._meta.db_table) as allocation:
        refused = browser.post(
            OPERATIONS_PATH,
            _a_contiguous_queue_of(
                uuid4(), uuid4(), by=alice, from_installation=installation, starting_at=3
            ),
            JSON,
        )

    assert refused.status_code == HTTPStatus.CONFLICT
    assert allocation == []
