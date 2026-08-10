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

**Deliberately left to the implementing window**, and a review that asks for a different one needs a reason
that is not preference: whether the version row is created with its project or lazily on first flush, and
which single statement does both. The acceptance says *one statement*, never *this statement*.

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

## Acceptance

From ADR-0004 decisions 2, 3 and 4, PRD M10, and the T2.2 requirement sentence that the flush is a
transactional call. **Nothing here is invented in this file.**

- a batch whose operations disagree on their project is refused at the boundary, before anything is bound
- a batch takes the project lock exactly once, asserted by a test rather than by reading the code
- the version table is separate from project metadata and carries its autovacuum settings in the migration
- batch size is a declared knob, starting at 500
- a failure in the version allocation rolls back the append that preceded it, so the flush is one
  transaction

**One note on the last clause, because this repository has already been burned by it.** MAP-10's spec put an
atomicity clause into **T2.2's acceptance**, where T2.2 does not carry one, and it was struck on 2026-08-10
as a spec inventing an acceptance criterion. The clause is legitimate here and its upstream is named
precisely: **T2.2's requirement sentence** that the op-queue flush is a transactional API call the database
orders, plus **ADR-0004's LATE rule**, which is what puts a second statement after the append and therefore
creates the failure the clause describes. It is not a bullet added to T2.2's acceptance list.
