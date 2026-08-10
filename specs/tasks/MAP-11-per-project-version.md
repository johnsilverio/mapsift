# MAP-11: a flush allocates its ordering key once, last, and leaves nothing behind if it fails

## Trace

PRD **M10** (the five axes, and the per-project version as the resync cursor) and **T2.2** (the flush is a
transactional API call the database orders). Invariants **I2** and **I9**; constraints **C9** and **C4**.
**ADR-0004** decisions 2, 3 and 4 with the addition of 2026-08-10, which are the RANGE and LATE rules, the
batch bound, the narrow dedicated table with its own autovacuum settings, and where the allocated version
reaches disk. **ADR-0005** sections 2 and 3 for the wall, the role grants and the transaction-scoped
binding. **ADR-0007** sections 1 and 3 for where a file goes and what it may import. **ADR-0010** decision 6
with both additions, for the request body, the typed refusals and the boundary they are taken at.
Foundation section 10 for why the two allocation rules are structural rather than an optimisation.

## What this task owns

The server-owned key that orders the rows MAP-10 appends. A flush allocates the whole range of per-project
versions it needs in one statement, takes that allocation last, distributes the range across the operations
of the batch, and persists each operation's version beside its log entry. The flush becomes one transaction
in a way a failure can actually reach.

**The route, the request body and the append already exist** (`mapsift/sync/api.py` and
`mapsift/sync/services.py`, delivered by MAP-34 and MAP-10). This task adds what runs after the append and
what the log entry needs in order to carry the result.

**The counter is a tenant-owned table and is therefore inside the wall** (C4, PRD N2, ADR-0005 sections 1
and 3). That is not a new criterion, it is C4 reaching a new table, and the evidence block below carries the
reason it needs saying out loud rather than being left to the existing sweep.

## Out of scope

Named with the owner of each, because a vague boundary is the measured root cause of a window doing work
nobody asked for, and because a line missing from MAP-10's block is what cost that task a round.

- **The per-feature version, including the never-decreases clause.** **MAP-38**, in this milestone. It was
  inherited here from MAP-9 and left on 2026-08-10; the reasoning is that issue's and `specs/log.md` under
  the same date. Nothing in this task assigns, reads or stores it.
- **The dedup by per-client mutation number and the echoed cursor.** MAP-12. **The flush still answers with
  no body**, unchanged from MAP-10.
- **The contiguity check and the typed resend on a gap.** MAP-13.
- **The correlation keys on the flush path.** MAP-14.
- **Any read of the log.** No projection, no resync endpoint, no query by version. The column and its index
  exist so MAP-22 can read them; this task writes and never reads back except to assert what it wrote.
- **The author normalization.** MAP-37.
- **Tuning the batch bound.** ADR-0004 decision 3 fixes the starting value and says it is tuned against
  measurement; measuring it is not this task.

## Boundary decisions the owner closed

All four were ruled 2026-08-10 and **registered in the documents that own them before this file was
written**. This block is the pointer, not the record; a window reads the cited section.

1. **One flush addresses exactly one project**, a third typed `MalformedBatch` at the same boundary as the
   two that exist. **ADR-0010 decision 6**, addition of 2026-08-10, which also states what it deliberately
   does not answer.
2. **The allocated version reaches disk as a column beside the log entry**, never as a stored server half.
   **ADR-0004 decision 4**, addition of 2026-08-10.
3. **The version table holds `SELECT, INSERT, UPDATE`.** **ADR-0005 section 2**, addition of 2026-08-10,
   which also states the rule the pair with the append-only log establishes.
4. **The per-feature version leaves for MAP-38**, as in Out of scope above.

Two more were ruled at the **Window A review**, both because the review found them already decided by
something nobody had looked at.

5. **The counter row is created on first use and does not reference the project table.** **ADR-0004
   decision 4**, second addition of 2026-08-10. Recorded here as closed because this file previously
   recorded it as open, which it was not.
6. **The batch-bound clause left this task for MAP-22**, so the acceptance below is four clauses rather than
   five. PRD N10 puts the bounding on the client and nothing on the server consumes the value, so the
   symbol would have had no caller. Its record is in MAP-11's issue and in `specs/log.md`.

**Deliberately left to the implementing window**, and a review that asks for a different one needs a reason
that is not preference: which single statement creates-or-increments the counter row. The acceptance says
*one statement*, never *this statement*.

## Evidence handed over

Transcribed rather than cited, because it exists nowhere else yet.

- **`tenant_scope` opens `transaction.atomic()` itself** (`mapsift/common/binding.py`, read 2026-08-10).
  A test whose only transaction is the one its own context manager opened is **green against an
  implementation that has none**, so the atomicity assertion has to go through the route. This is the trap
  that made the clause untestable in MAP-10 and testable here.
- **The append-only grant does not reach the owner profile**, and migrations, tests and CI all connect as
  the owner (ADR-0005 section 2, correction of 2026-08-07). Anything asserting a privilege on the new table
  inherits that limit, and a grant assertion written against the owner proves nothing.
- **What was not measured, said plainly so nobody treats it as handed over:** how to make the allocation
  fail after the append has run. No probe was taken. Choosing the instrument is Window A's, and a mock of an
  internal that bypasses the route would fail the trap above rather than satisfy it.

Three more were measured at the **Window A review** and are handed over because they change what the next
pass has to do.

- **The wall's suite cannot see a table that does not carry the tenant column** (read 2026-08-10).
  `apps/api/conftest.py`'s `tenant_owned_tables` enumerates from the catalogue **by that column**, and every
  case in `tests/test_tenant_isolation.py` consumes that set. So a counter built without it does not fail
  those cases, it **disappears from them**, which is the silence this system's heaviest trap is made of. The
  width assertion does not close it: a two-column table passes the width and stays outside the wall.
- **A raise inside a `connection.execute_wrapper` reaches `pytest.raises` through the route, and a flush
  that fails midway already rolls its append back today** (probed 2026-08-10 by the orchestrator, on the log
  table, and the probe deleted). `DEBUG` is false under the test settings, so django-ninja re-raises. The
  consequence for the next pass: the atomicity clause is a **regression guard rather than a driver**, and it
  should not be expected to force new production code.
- **The flush suites that predate this task address projects that do not exist** (grepped 2026-08-10).
  `mapsift/sync/tests/test_flush.py` posts batches whose `project_id` is a random value with no row in
  `accounts_project`, and those tests may not be edited. That is half of what closed boundary decision 5.

## Acceptance

From ADR-0004 decisions 2 and 4, PRD M10, and the T2.2 requirement sentence that the flush is a
transactional call. **Nothing here is invented in this file.**

- a batch whose operations disagree on their project is refused at the boundary, before anything is bound
- a batch takes the project lock exactly once, asserted by a test rather than by reading the code
- the version table is separate from project metadata and carries its autovacuum settings in the migration
- a failure in the version allocation rolls back the append that preceded it, so the flush is one
  transaction

**A fifth clause was struck on 2026-08-10** at the Window A review: "batch size is a declared knob, starting
at 500" reached this file from ADR-0004 decision 3 by way of the issue, and it has no consumer on the
server. It is MAP-22's now. It is recorded here rather than removed silently, because a task spec that
quietly loses a clause is indistinguishable from one that never carried it.

**One note on the last clause, because this repository has already been burned by it.** MAP-10's spec put an
atomicity clause into **T2.2's acceptance**, where T2.2 does not carry one, and it was struck on 2026-08-10
as a spec inventing an acceptance criterion. The clause is legitimate here and its upstream is named
precisely: **T2.2's requirement sentence** that the op-queue flush is a transactional API call the database
orders, plus **ADR-0004's LATE rule**, which is what puts a second statement after the append and therefore
creates the failure the clause describes. It is not a bullet added to T2.2's acceptance list.
