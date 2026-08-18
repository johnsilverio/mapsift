"""The cursor's backwards guard, witnessed under two flushes contending for the same row.

Trace: PRD T2.3 (the server tracks the per-client last-applied number and echoes it) and M4 (the
cursor keyed by clientID, tenant and project, **holding** the last-applied mutation number, which
is the word this module is about); I9, whose Scar is the interrupted-then-resent flush; C12.
ADR-0004 decision 2's extension of 2026-08-11 for the shape under test, the cursor read early and
written late in one statement carrying a guard that refuses to move it backwards; ADR-0010
decision 6 for what makes the contention one installation against its own resend and nothing else,
since a flush addresses one tenant, one project and one clientID; ADR-0005 sections 3 and 4 for
what a connection binds before it reads a tenant-owned row.

**This module is where this suite opens its second database connection**, and everything unusual
below follows from that rather than from a preference. The readings that shaped it, each dated and
sourced, none of them a decision this module took:

- **A Python signal handler runs only in the main thread**, so nothing on this side can interrupt a
  worker blocked inside `cursor.execute` on a lock wait; only the server can, through `lock_timeout`
  and SQLSTATE `55P03` (`specs/dependencies.md` section 1, 2026-08-18). Every wait here is therefore
  bounded twice, once in Python and once in PostgreSQL.
- **A psycopg 3 connection is thread-safe and every cursor on it shares one transaction**, so a race
  needs a second connection and a second cursor stages none (same source and date). Django's
  `connection` is thread-local by construction, which is what makes a thread the way to get one.
- **Django's own precedent for two connections in one test** is `tests/select_for_update/tests.py`,
  whose contender runs in a thread that closes its connection in `finally` and joins with a bound,
  and `tests/get_or_create/tests.py::test_creation_in_transaction`, whose sleeps were replaced by
  `threading.Event` in PR #19048 because a sleep let the wrong thread win the race (read
  2026-08-18). A connection a thread leaves open makes the `TRUNCATE` of teardown wait rather than
  fail, which `specs/log.md` records SP-1's harness doing to itself on 2026-08-05.
- **Nothing here sleeps to sequence anything.** Of the twenty flaky-test fixes that added or
  lengthened a sleep, none removed the flakiness, while all eight that made the ordering
  deterministic did (Luo et al., FSE 2014, table 4).
- **An `INSERT ... ON CONFLICT DO UPDATE` whose conflict originates in a transaction whose effects
  are not yet visible waits for it, and its `UPDATE` then affects the committed version of that
  row** (PostgreSQL 18, transaction isolation 13.2.1, read 2026-08-18). That is the whole mechanism
  the case rests on: the loser reads its guard's left-hand side from what the winner committed.
- **That a waiter of exactly that kind is visible in `pg_blocking_pids` was measured here rather
  than read**, 2026-08-18, in this project's own `postgis/postgis:18-3.6`, because the row-level
  lock itself lives on disk and normally does not appear in `pg_locks`. Polling that predicate is
  how PostgreSQL's own isolation harness decides a step is blocked, every 10 ms and never by
  waiting out a duration (`src/test/isolation/isolationtester.c`, read 2026-08-18).

**Why the route and never the writer**, which is `test_project_version_allocation.py`'s reason
unchanged: `tenant_scope` opens `transaction.atomic()` itself, so a test whose only transaction is
the one its own context manager opened is green against an implementation that has none, and two
flushes that never held a transaction apiece cannot contend for anything.

What is deliberately not here, each with the issue that owns it: convergence, which needs two
clients rather than two flushes of one installation (MAP-23, T2.1, C2); the resync a second axis in
the response opens (MAP-22); and the cursor a refused flush must not have advanced, which is a
rollback rather than a race (MAP-46). The harness below is shaped by the one case it carries and
stays in this module: the root `conftest.py` is where what more than one suite reads belongs
(ADR-0007 section 6), and a second reader is what would move it there.
"""

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from http import HTTPStatus
from uuid import UUID, uuid4

import pytest
from django.db import connection
from django.test import Client

from conftest import Execute, JsonObject, Params, Party, a_browser, a_feature_create_claiming
from mapsift.common.binding import tenant_scope
from mapsift.sync.models import ClientCursor
from mapsift.sync.selectors import the_cursor_of

pytestmark = pytest.mark.django_db(transaction=True)

OPERATIONS_PATH = "/api/operations"
JSON = "application/json"

CURSOR_TABLE = ClientCursor._meta.db_table

# The other half of Django's execute-wrapper contract, which `conftest` publishes only the inner
# half of. Local rather than shared for the reason `test_project_version_allocation.py` keeps its
# own: one module consumes it, and it moves to `conftest` when a second one does.
_Wrapper = Callable[[Execute, str, Params, bool, dict[str, object]], object]

# Every wait in this module carries one of these two, and the pair is the point rather than the
# values: the first bounds what this side can interrupt, the second bounds what only the server
# can (`specs/dependencies.md` section 1, 2026-08-18).
THE_LONGEST_ANY_WAIT_MAY_LAST = 5.0
THE_LONGEST_A_LOCK_MAY_BE_WAITED_FOR = "5s"

# Strictly shorter than the pair above, and it is the ordering rather than the values that is
# load-bearing. The winner holds its row inside a bound of its own while this question is being
# asked, so an observation allowed to run as long lets the winner's bound expire in the same
# instant and replaces the case's own witness with the harness's refusal. Measured 2026-08-18
# against the arm where the block is never reported: at equal bounds the assertion below is
# unreachable, which makes a positive control decoration.
THE_LONGEST_A_BLOCK_MAY_TAKE_TO_APPEAR = 2.0

# The interval between two questions to the database, never a duration anything is assumed to take.
# It is isolationtester's own (read 2026-08-18); what ends the loop is the answer, or the bound.
BETWEEN_TWO_QUESTIONS = 0.01


class TheRaceWasNotStaged(Exception):
    """Raised where the harness could not put the two flushes in the order it promises.

    Its message names the invariant that broke rather than the step that timed out, because a
    concurrency harness reporting only "waited too long" leaves the reader to guess which of the
    steps it sequences did not happen.
    """


@dataclass
class ASessionInTheRace:
    """One flush on a connection of its own: which backend ran it, and how it ended.

    The backend identifier is taken from inside the flush's own transaction rather than before the
    request, because Django closes and reopens a connection around a request at `CONN_MAX_AGE=0`
    and a pid read outside would name a session that no longer exists.
    """

    name: str
    backend_pid: int | None = None
    answered: int | None = None
    failure: Exception | None = None


@dataclass
class TheRaceAsTheDatabaseSawIt:
    """Whether the two flushes actually contended, asked of the database rather than inferred.

    This is the positive control the case cannot do without. Serialised either way round the
    assertion about the cursor passes with the guard collapsed: run loser-then-winner and the
    winner reads a cursor of zero and raises it to two on its own; run winner-then-loser and the
    loser's batch is deduplicated away entirely and it never writes the cursor at all. So a harness
    that serialises by accident leaves the case green and vacuous, and this is what refuses that.
    """

    the_loser_was_blocked_by_the_winner: bool = False


def _writes_the_cursor(sql: str) -> bool:
    """Whether a statement is the one that raises this installation's cursor.

    Matched on the table and the verb, the way `test_project_version_allocation.py` matches the
    append and for the same reason: the read that precedes the write names the same table, and an
    instrument stopping there would hold a flush that has nothing to contend about yet. What the
    write spells as its guard, its conflict target or its arithmetic stays the implementation's.
    """
    return CURSOR_TABLE in sql and "INSERT" in sql.upper()


def _bound_the_wait_and_name_the_backend(session: ASessionInTheRace) -> None:
    """Cap how long this backend may wait on a lock, and record which backend it is.

    The cap is the server's because it has to be, and the reason is in the module docstring. It is
    transaction-local, so it covers exactly the flush that races and dies with it; a session-scoped
    one would not survive Django reopening the connection anyway. Both facts travel in one round
    trip because the flush is holding nothing yet and there is no reason to take two.
    """
    with connection.cursor() as probe:
        probe.execute(
            "SELECT set_config('lock_timeout', %s, true), pg_backend_pid()",
            [THE_LONGEST_A_LOCK_MAY_BE_WAITED_FOR],
        )
        _, session.backend_pid = probe.fetchone()


def _wait_for(reached: threading.Event, otherwise: str) -> None:
    """Wait for one step of the race, refusing to wait for it forever."""
    if not reached.wait(THE_LONGEST_ANY_WAIT_MAY_LAST):
        raise TheRaceWasNotStaged(otherwise)


def _the_winner_blocks_the_loser(loser: ASessionInTheRace, winner: ASessionInTheRace) -> bool:
    """Whether the database reports the losing backend waiting on the winning one.

    Answers False rather than raising, because "the two flushes did not contend" is the case's own
    assertion and not the harness's to take: a harness that refused it would leave the reader with
    an exception where the module promises a witness. Its bound is the short one for the same
    reason, stated where that constant is.
    """
    deadline = time.monotonic() + THE_LONGEST_A_BLOCK_MAY_TAKE_TO_APPEAR

    while time.monotonic() < deadline:
        with connection.cursor() as probe:
            probe.execute("SELECT pg_blocking_pids(%s)", [loser.backend_pid])
            if winner.backend_pid in probe.fetchone()[0]:
                return True
        time.sleep(BETWEEN_TWO_QUESTIONS)

    return False


def _flush_on_a_connection_of_its_own(
    browser: Client, batch: JsonObject, holding: _Wrapper, session: ASessionInTheRace
) -> None:
    """Post one flush from this thread, and leave nothing of its connection behind.

    The wrapper is installed here rather than by the caller because Django installs one on the
    **thread-local** connection, so a wrapper installed by the test thread sees nothing this one
    executes (Django instrumentation documentation, read 2026-08-18).
    """
    try:
        with connection.execute_wrapper(holding):
            session.answered = browser.post(OPERATIONS_PATH, batch, JSON).status_code
    except Exception as met:
        session.failure = met
    finally:
        connection.close()


def _refuse_a_race_that_did_not_run(*sessions: ASessionInTheRace) -> None:
    """Refuse anything that leaves the cursor assertion measuring something else."""
    for session in sessions:
        if session.failure is not None:
            raise TheRaceWasNotStaged(
                f"the {session.name} flush did not survive its own request"
            ) from session.failure
        if session.answered != HTTPStatus.OK:
            raise TheRaceWasNotStaged(
                f"the {session.name} flush was answered {session.answered} rather than "
                f"{HTTPStatus.OK}, so nothing it did to the cursor is this case's subject"
            )


def _the_race_for_the_cursor(
    party: Party, *, the_winner_flushes: JsonObject, the_loser_flushes: JsonObject
) -> TheRaceAsTheDatabaseSawIt:
    """Hold the loser at the cursor statement, let the winner take that row and commit under it,
    and release the loser into the wait the guard exists for.

    Both flushes read an absent cursor before either writes one, which is what makes the loser's
    write a stale one and the whole thing a race rather than a sequence. The winner is released
    only once the database reports the loser queued behind it, so the order is decided by an answer
    and never by an elapsed duration.

    The browsers are built here rather than inside each thread, because `a_browser` does database
    work of its own (`User.objects.get`, then `force_login`), and a thread doing it after its
    wrapper is installed puts those statements in front of the race, where the instrument would
    have to learn to ignore them. Each thread still gets one of its own, because a client's cookie
    jar is mutable and two threads sharing a client would share it.
    """
    winner, loser = ASessionInTheRace("winning"), ASessionInTheRace("losing")
    the_loser_is_at_the_cursor = threading.Event()
    the_winner_holds_the_row = threading.Event()
    the_winner_may_commit = threading.Event()

    def hold_the_loser_at_the_cursor(
        execute: Execute, sql: str, params: Params, many: bool, context: dict[str, object]
    ) -> object:
        if not _writes_the_cursor(sql):
            return execute(sql, params, many, context)

        _bound_the_wait_and_name_the_backend(loser)
        the_loser_is_at_the_cursor.set()
        _wait_for(the_winner_holds_the_row, "the winning flush never took the cursor row")
        return execute(sql, params, many, context)

    def hold_the_winner_before_it_commits(
        execute: Execute, sql: str, params: Params, many: bool, context: dict[str, object]
    ) -> object:
        if not _writes_the_cursor(sql):
            return execute(sql, params, many, context)

        _bound_the_wait_and_name_the_backend(winner)
        taken = execute(sql, params, many, context)
        the_winner_holds_the_row.set()
        _wait_for(the_winner_may_commit, "the losing flush never reached the cursor row")
        return taken

    losing = threading.Thread(
        target=_flush_on_a_connection_of_its_own,
        args=(
            a_browser(authenticated_as=party.user_id),
            the_loser_flushes,
            hold_the_loser_at_the_cursor,
            loser,
        ),
        name="the losing flush",
    )
    winning = threading.Thread(
        target=_flush_on_a_connection_of_its_own,
        args=(
            a_browser(authenticated_as=party.user_id),
            the_winner_flushes,
            hold_the_winner_before_it_commits,
            winner,
        ),
        name="the winning flush",
    )

    seen = TheRaceAsTheDatabaseSawIt()
    # Only what was actually started, and joined in reverse: joining a thread that never ran raises
    # a `RuntimeError` of its own and buries the diagnosis this harness exists to give (measured
    # 2026-08-18 against the arm where the instrument never recognises the cursor statement), and
    # the loser cannot finish until the winner has committed under it.
    running: list[threading.Thread] = []
    try:
        losing.start()
        running.append(losing)
        _wait_for(
            the_loser_is_at_the_cursor,
            "the losing flush never reached the cursor statement, so it had none to lower",
        )

        winning.start()
        running.append(winning)
        _wait_for(the_winner_holds_the_row, "the winning flush never reached the cursor statement")

        seen.the_loser_was_blocked_by_the_winner = _the_winner_blocks_the_loser(loser, winner)
    finally:
        # Released whatever happened above, and before anything is joined: a wrapper still waiting
        # holds an open transaction, and a transaction still open makes teardown's TRUNCATE wait
        # rather than fail (`specs/log.md`, 2026-08-05).
        the_winner_holds_the_row.set()
        the_winner_may_commit.set()
        for thread in reversed(running):
            thread.join(THE_LONGEST_ANY_WAIT_MAY_LAST)

    outlived = [flush.name for flush in (winning, losing) if flush.is_alive()]
    if outlived:
        raise TheRaceWasNotStaged(
            f"{' and '.join(outlived)} outlived every bound this harness sets for it"
        )
    _refuse_a_race_that_did_not_run(winner, loser)

    return seen


def _a_queue_of(operation_ids: list[UUID], *, by: Party, from_installation: UUID) -> JsonObject:
    """One installation's queue, in one project of one tenant, from the first mutation number.

    From zero always, because both queues here are what a client sends before it has ever been
    acknowledged (M10's Shape), and that is what makes both flushes read an absent cursor.
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
            for mutation_number, operation_id in enumerate(operation_ids)
        ]
    }


def _the_cursor_left_for(party: Party, installation: UUID) -> int | None:
    """How far the server holds this installation's stream applied, read where the flush reads it.

    Bound to the tenant before the read, because the wall answers an unbound one with nothing and a
    case can pass on that silence (ADR-0005 sections 3 and 4).
    """
    with tenant_scope(party.tenant_id):
        return the_cursor_of(installation, party.project_id)


def test_a_flush_that_lost_the_race_does_not_lower_the_cursor_the_winner_already_raised(
    alice: Party,
) -> None:
    """M4's "holding the last-applied", under the guard ADR-0004 decision 2's extension of
    2026-08-11 puts on the cursor write. The story is I9's own scar: a client flushes what it has,
    the acknowledgement does not arrive, and it resends a queue that grew while it waited, so two
    flushes of one installation are in flight and both read a cursor that is not there yet. The
    resend wins the row and raises the cursor to two; the first flush arrives behind it and would
    write zero.

    **Two is the winner's number independently of anything the server computes**: its client
    authored three operations at mutation numbers zero, one and two, and the winner applied all
    three. Zero is the loser's for the same reason, its queue being one operation long.

    A cursor lowered here is silent loss with an acknowledgement on top: under C12 the client
    advances from the echo alone, so it would be told two and the server would be holding zero, and
    the next flush from that installation would re-apply operations one and two against a log that
    already holds them. The dedup filter cannot catch it, because the operations are above the
    cursor the server now believes in.

    The block is asserted before the cursor is, and the record's own docstring carries why: without
    it this case is green against the collapsed guard in either serialised order."""
    installation = uuid4()
    first_drawn = uuid4()

    race = _the_race_for_the_cursor(
        alice,
        the_winner_flushes=_a_queue_of(
            [first_drawn, uuid4(), uuid4()], by=alice, from_installation=installation
        ),
        the_loser_flushes=_a_queue_of([first_drawn], by=alice, from_installation=installation),
    )

    assert race.the_loser_was_blocked_by_the_winner
    assert _the_cursor_left_for(alice, installation) == 2
