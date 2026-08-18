# MAP-43: a second database connection in the suite, and the cursor guard witnessed under a real race

## Trace

**Requirement:** PRD **T2.3** (the server tracks the per-client last-applied number and echoes it) and PRD
**M4** (the server cursor, keyed by clientID, tenant and project, holding the last-applied mutation number).
Under a race, "holding the last-applied" is the property this task witnesses.

**Invariant and constraint:** foundation **I9** (its Scar is the interrupted-then-resent flush), **C12**.

**Code shape:** **ADR-0004 decision 2**, the extension of 2026-08-11 (the cursor is read early and written late
in one statement carrying a guard that refuses to move it backwards, and the shape that must not be taken),
including its correction of the same day on **which row is contended** and its rule that the cursor is
written before the append. **ADR-0010 decision 6** for the composition of a flush (one tenant, one project,
one clientID), which is what makes the race one installation against its own resend and nothing else.
**ADR-0005 sections 3 and 4** for what any connection this suite opens must carry before it reads a
tenant-owned row, and for why the wall's silence is the trap. **ADR-0007 section 6** for where a fixture
more than one suite reads lives. `specs/testing.md` sections 2, 3, 4 (the paragraph on integration tests
with real adapters, and the one on a suite people learn to ignore), 6 and 9.

**Named as a future consumer and not as this task's requirement:** PRD **T2.1** and **C2**, through
**MAP-23**, and **MAP-22**; the tracker carries the relations.

## What this task owns

The suite can open a second database connection and hold two flush transactions in a chosen order, and one
case proves that a flush which lost the race on the cursor row does not lower a cursor the winner already
raised.

## Out of scope

- **Any convergence or gap case.** MAP-23 and MAP-22 extend the harness when they arrive; a case written
  now for either would be an unbuilt future (`specs/testing.md` section 7).
- **The cursor a refused flush must not have advanced.** MAP-46, a different seam (a refusal's rollback,
  not a race), explicitly not blocked on this task, not batched with it.
- **Any change to the flush's behaviour, response, or statements.** What the route answers and what the
  service writes move through ADR-0010 decision 6 and ADR-0004 decision 2, never through a task that
  witnesses them. If a case cannot be written without such a change, that is a finding to report.
- **A suite-wide timeout dependency.** `pytest-timeout` is refused in `specs/dependencies.md` section 1
  (2026-08-18); the backstop is pytest's own faulthandler pair, configured by this task and by nothing
  else it adds.
- **The Rust core, the client queue, and everything client-side.** The race this task stages is two
  server-side flushes; the client half of the axis belongs to MAP-15, MAP-17 and MAP-19.

## Boundary decisions the owner closed

All closed 2026-08-18, after a research round, and registered before this file was written. **The pickup
comment on MAP-43 is the record and this is the pointer**; `specs/log.md` carries the two lines of that
date. In one sentence each:

1. One window and no Window B; red is defined against a mutant, the exit is proven by the orchestrator's
   mutant run, and the review runs on all three axes.
2. The window may strike the one production sentence this task makes false, in `mapsift/sync/services.py`
   beside the cursor upsert, and nothing else in production; the stale sentence in the dedup module's
   docstring is test code and is the window's own. **Extended 2026-08-18 at the review, because the count
   was wrong:** the round falsified **two** sentences, and the second, "No case in this suite catches the
   swap" above the cursor write in `apply_the_flush`, was measured false by the order-swap mutant at all
   three axes. The correction round may strike that one too, and still nothing else in production; the
   nuance (tripped over, not witnessed) is ADR-0004 decision 2's sharpening of 2026-08-18 and no comment
   restates it.
3. Failing loudly costs no new dependency: the harness owns bounded waits and a server-side lock timeout
   on the session that races, and the backstop armed per test item is `faulthandler_timeout` with
   `faulthandler_exit_on_timeout` (`specs/dependencies.md` section 1, 2026-08-18).
4. The harness is shaped by the one case it carries today.
5. The trace is the one above; T2.1 is a consumer, not the requirement.
6. Acceptance is the delta below.
7. **The pre-dispatch spec read did not run for this task, by the owner's waiver of 2026-08-18** (ADR-0008
   section 9 change 2), after four attempts were stopped; the Spec axis then found the counting defect in
   decision 2 above, which is the kind of finding that read exists to catch before a window. Recorded here
   and in `specs/log.md` rather than left to look like an oversight.

## Evidence handed over

Everything below is a **reading**, dated, with its source, and none of it was measured in this repository
unless it says so. A reading can be wrong; that is what the label is for.

**Measured in this repository, 2026-08-18.** The lockfile pins Django 5.2.16, psycopg 3.3.4, pytest 9.1.1
and pytest-django 4.12.0; the installed pytest registers both `faulthandler_timeout` and
`faulthandler_exit_on_timeout` (`_pytest/faulthandler.py`). The suite connects as `mapsift_owner`
(`apps/api/.env.example`), and it is subject to the wall because of FORCE (ADR-0005 section 2).

**Two properties the case relies on, from the PostgreSQL 18 documentation, read 2026-08-18.** Under READ
COMMITTED, an `INSERT ... ON CONFLICT DO UPDATE` whose conflict "originates in another transaction whose
effects are not yet visible" waits for it and its `UPDATE` then "will affect that row", the committed
version (transaction isolation, 13.2.1), and the target alias in `DO UPDATE` names that existing row while
`EXCLUDED` names the proposed one (the `INSERT` reference page). Waiting processes "will be granted the lock
in arrival order" (`src/backend/storage/lmgr/README`, REL_18_STABLE), with two named departures: a lock
upgrade queues ahead of conflicting waiters, and the deadlock detector may reorder the queue.

**How a session's wait is observed, and what it must not be observed with, same source and date.**
Row-level locks live on disk and "normally do not appear" in `pg_locks`; a waiter shows as waiting on the
holder's transaction id. `pg_blocking_pids(pid)` answers which sessions block a given one, understands a
waiter that is merely ahead in the queue, and carries a documented cost note about frequent calls
(functions-info). PostgreSQL's own concurrency harness, isolationtester, decides a step is blocked by
polling such a predicate every 10 ms and never by sleeping (`src/test/isolation/isolationtester.c`), and it
requires the permutations that can block to be written by hand (`src/test/isolation/README`).
`pg_isolation_test_session_is_blocked` is a test-support function whose presence in the image this project
runs was **not verified**.

**What ends a wait, same source and date.** `lock_timeout` aborts a statement waiting on a lock, per
acquisition attempt, SQLSTATE `55P03`, settable per session; `statement_timeout` set lower fires first with
`57014`; `deadlock_timeout` is not a knob this role can set. Deadlock detection resolves a cycle and never a
wait on a transaction that simply does not commit.

**Why a Python-side timeout cannot reach the wait that matters, read 2026-08-18.** A Python signal handler
runs only in the main thread (`signal` module documentation), and psycopg's wait loop yields to a signal
only there (its `waiting.py` and `waiting.pyx`), so a worker thread blocked in `cursor.execute` is
interrupted by the server or by nothing. A psycopg 3 connection is thread-safe, and every cursor on it
shares one transaction (psycopg "concurrent operations"), so a race needs a second connection and a second
cursor stages no race at all.

**Django's own precedent for two connections in one test, read 2026-08-18 on `stable/5.2.x`.**
`connection.copy()`, documented in its docstring as being for tests that require two connections to the
same database, and `django.db.connection` being thread-local by construction (`ConnectionHandler` with
`thread_critical = True`), so a thread that touches the ORM opens its own session. `tests/select_for_update/tests.py`
runs the contender in a thread that closes its connection in `finally` and joins with a bound;
`tests/get_or_create/tests.py::test_creation_in_transaction` sequences two threads with `threading.Event`
and a `wait_or_fail` helper, and Django PR #19048 replaced its earlier `time.sleep` because the sleep let
the wrong thread win the race. A comment in `tests/transactions/tests.py` names the limit of that
technique: a thread already blocked on a lock cannot reach its own `event.set()`, so the last hop into a
lock wait is not Event-synchronisable. `connection.execute_wrapper` is installed on the **thread-local**
connection (Django instrumentation docs), so a wrapper installed by the test thread sees nothing a worker
thread executes.

**Two teardown facts, same reading.** `TransactionTestCase` flushes with `TRUNCATE` and the test database
is dropped with a bare `DROP DATABASE`; a connection left open by a thread makes both wait rather than
fail (pytest-django issue #429 carries the workaround people reach for). `specs/log.md`, 2026-08-05,
records the SP-1 harness deadlocking itself the same way, a connection idle in transaction blocking the next
test's DDL.

**Why `sleep` is refused as a sequencer, read 2026-08-18.** Luo et al., "An Empirical Analysis of Flaky
Tests" (FSE 2014), table 4: of twenty fixes that added or lengthened a sleep, none removed the flakiness,
while all eight fixes that made the ordering deterministic did.

**What is still open and belongs to the window:** the mechanism that holds one flush at a chosen point
while the other commits, whether the flushes are driven through the route or the service, the shape of the
fixture within ADR-0007 section 6, the timeout values, and the assertion that shows the race actually
happened rather than that both flushes ran.

## Acceptance

The requirement's criteria are PRD T2.3's and M4's and the window reads them there. What this task does
differently:

- **The case is green against `main` from its first run**, because the guard it witnesses already exists.
  Red is defined against a mutant of the cursor upsert with its guard collapsed, and that red is proven by
  a run **the orchestrator** performs and records in `specs/log.md`, never by a case committed to CI (the
  MAP-45 decision 5 shape). The `test` skill's "tests that fail" therefore holds against the mutant, and the
  window reports the case's status against `main` as what it is.
- **The exit of the issue is met by that mutant run**: with the guard removed the case fails, with the
  guard present it passes.
- **The case witnesses that a race happened**, not only that two flushes ran, so a harness that serialises
  them by accident turns the case red rather than vacuous. This is the `test` skill's unwitnessed-happy-path
  rule applied, not a new criterion.
- **No hang is left possible without a loud failure**: the racing session's wait is bounded on the server
  side, every Python-side wait is bounded and checked, and the per-item backstop is configured, all
  without a new dependency (boundary decision 3).
