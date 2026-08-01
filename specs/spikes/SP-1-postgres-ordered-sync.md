# SP-1: Postgres-ordered sync

- **Status:** **CLOSED 2026-07-31** (planned 2026-07-30). Both stages ran. The outcome is ratified in **ADR-0004**, which is the authority on the decision; what stays here is the plan, so a reader can check that what ran is what was planned. Headline results: the negative control caught the documented trap (53.6 percent of committed rows lost at ten concurrent writers, the cursor finishing convinced it had seen everything); all three candidates passed Stage A correctness; candidate C was eliminated on read cost; A and B both passed 7/7 in Stage B; and the choice fell on failure mode, with the per-project version ratified.
- **Answers:** foundation **OQ-10**, and the version-axis hole it exposed in PRD M10
- **Owner of the exit decision:** the owner, on the numbers the spike produces
- **Authority:** the plan derives from `specs/mapsift-foundation.md` v0.12 (section 10, OQ-10), `specs/PRD.md` v0.9 (T2, T4, M8, M10, N10) and `specs/dependencies.md` section 1
- **Output:** an ADR plus recorded measurements. **The code is thrown away.**

---

## 1. Why this runs now

The foundation's instruction on OQ-10 is explicit: putting the ordering authority in PostgreSQL with Channels as transport and presence only is sound in principle but had **no documented production precedent found**, so it is validated in a spike **before spec is written on top of it**. Spec has now been written on top of it, in quantity: T2 (convergence, transport separation, idempotency), M8 (the operation envelope), M10 (the version axes and the contiguous-order rule) and N10 (batching and backpressure). The spike is therefore overdue rather than optional, and until it closes, **no further specification is built on the sync path**.

The survey in `dependencies.md` sharpened what it has to resolve.

**The trap.** A sequence value in PostgreSQL is taken **before commit**, so a transaction that started later can commit first with a higher number. A consumer polling `WHERE position > last_processed` then advances past rows that commit late, and those rows are lost silently. This product's entire moral line is that data is never lost silently, so a design that carries this trap is disqualified, not merely slow.

**The hole it exposes.** PRD M10 names four version axes (per-feature version, per-client mutation number, operation-schema version, conflict-rule version). None of them is the **resync cursor**, the thing a client uses to ask for everything that changed since it last looked, and the cursor is exactly where the trap lives. This spike decides whether the cursor is an existing axis (the project version doubling as it) or a fifth axis with its own mechanism.

**The documented design space.** Replicache publishes three backend strategies with stated tradeoffs, and they map onto Mapsift directly, with the **project** as the space:

| Candidate | Shape | Known cost |
|---|---|---|
| **A. Per-project version** | a version integer per project, incremented inside the flush transaction | serialises writes per project; the published ceiling for this shape is around fifty pushes per second per space; requires soft deletes; partial sync and read authorisation are harder |
| **B. Transaction-id watermark** | rows carry `xid8`, the reader filters on `pg_snapshot_xmin(pg_current_snapshot())` and orders by transaction id then position | no write serialisation; a more complex read; gapless by construction because transaction ids are |
| **C. Row version with a Client View Record** | per-row version (Postgres `xmin` can serve), plus a CVR in ephemeral storage that the pull diffs against | no global lock, hard deletes work, arbitrary queries with filters and authorisation; pays in implementation complexity and read cost, and adds Redis to the correctness path |

Fifty pushes per second per project is comfortably above a project edited by a handful of people, which is why A is not dismissed on throughput. It is dismissed or kept on the other columns.

---

## 2. What this spike is not

It is **not** `apps/api`, it is not product code, and it does not live in the repository's application folders. It is a throwaway harness in a scratch location, deleted when the ADR is written. Nothing it produces is promoted into the product: what survives is the ADR, the numbers, and the test cases, which are re-derived as real tests inside the product later.

This is the Hort SP-1 and SP-2 discipline: a spike is a shot at the unknown, and its value is the answer, not the code.

---

## 3. Stage A: the database ordering strategy

No web layer, no Django, no WebSocket. Concurrent writer processes against a real PostgreSQL, because the risk being tested is the database's ordering semantics and nothing else. Building the web tier three times to test three strategies would be waste.

### A.0 The negative control, which runs first

**Implement the naive design first: a `BIGSERIAL` cursor, readers polling `WHERE position > last`.** Then prove the harness **detects the loss** under concurrent writers with overlapping transaction lifetimes.

This is not a formality. If the harness cannot catch the bug that is already documented and understood, it cannot be trusted to validate a fix, and every green result afterwards is decoration. The control passes when the harness reports lost rows and names them.

### A.1 The three candidates

Each of A, B and C is implemented against the same schema and the same workload, and each faces the same checks.

### A.2 Workload

- Writers: 1, 2, 5 and 10 concurrent processes writing operations to **one project**, with deliberately overlapping transaction windows (a randomised pause inside the transaction, so commit order and start order disagree).
- A reader polling with a cursor throughout, recording every row it observes.
- A second project written concurrently, to check that per-project serialisation in candidate A does not serialise across projects.
- Queue sizes: a normal flush, then 1,000 and 5,000 queued operations from a single client, which is the field-trip case behind N10.

### A.3 Exit criteria, all pass or fail

1. **No lost row.** The set of rows the reader observed equals the set committed, at every concurrency level. The naive control fails this; a candidate that fails it is eliminated.
2. **No duplicate.** No row is delivered twice by cursor advancement.
3. **Monotonic cursor.** The cursor never moves backwards and never skips a committed row.
4. **Per-project isolation of contention.** Writes to project B are not blocked by contention on project A beyond what the strategy declares.
5. **Deletes are representable.** The strategy expresses a delete in a way a pulling client can apply. Candidate A needs soft deletes; that cost is recorded, not hidden.

### A.4 Numbers to record

Latency at p50 and p95 per concurrency level, throughput ceiling per project, and the read cost of a pull at a realistic backlog. Recorded with the machine, the PostgreSQL version, the PostGIS version, and the date, per the measurement protocol PRD N1 sets. A number without its conditions is not a result.

---

## 4. Stage B: the protocol loop

Only the winner of Stage A, or the top two if Stage A does not separate them, goes to Stage B. Here the minimal transactional flush endpoint, a WebSocket poke carrying "project X changed to version N" and nothing authoritative, and **headless script clients**, no browser and no UI.

### B.1 Chaos, applied deliberately

- Kill a client mid-flush, after the server has applied part of the queue and before the client sees the acknowledgement, then resend the whole queue.
- Drop the poke entirely and let the client discover the change by its own gap detection.
- Skew a client's clock, to confirm nothing depends on it (created-at is a claim, applied-at is authoritative, per T5.3).
- Flush from two clients of the same user with distinct clientIDs.
- Flush a queue with a deliberate gap in the mutation numbers.

### B.2 Exit criteria, all pass or fail

1. **Convergence (I2, C2).** Concurrent edits from two clients, replayed in server order, leave both clients in one identical state.
2. **Idempotent resend (I9, C12).** The interrupted-then-resent flush ends in a state identical to an uninterrupted one, with no duplicated feature and no lost edit, and the client advances its cursor **only from the server's echoed last-applied**.
3. **Gap detection and resync (C9).** A dropped poke is recovered by the client detecting a version gap and resyncing from the database, not lost.
4. **Contiguity enforcement (M10).** A flush with a gap above the cursor is rejected with a typed resend-from-cursor response and applies nothing from the gap onward. It is never silently skipped.
5. **No false dedup across devices (I9 case 3).** Two clientIDs of the same user do not collide and neither loses an operation.
6. **Batching preserves order (N10).** A 5,000-operation queue flushes in bounded batches with per-batch acknowledgement, contiguity intact, resumable from the echoed cursor after an interruption, with visible progress and no timeout.
7. **Nothing authoritative comes from the transport.** Disabling the WebSocket entirely leaves correctness intact and only presence degraded.

---

## 5. What the spike delivers

1. **An ADR** choosing the strategy, with the measurements and the eliminated candidates and why.
2. **The fifth version axis settled in PRD M10**: either the resync cursor is named as its own axis with its mechanism, or M10 states explicitly that the project version is the cursor and why that is safe.
3. **A recorded number for the per-project write ceiling**, which is the input to any future capacity claim.
4. **The list of test cases**, which become real tests in the product rather than being re-invented.
5. If a candidate fails a criterion, **the failure is the result**, recorded with the same weight as a success. A spike that only reports success was not a spike.

---

## 6. What this spike does not answer

The conflict rule itself (T4 and M13, its own golden-test surface), the shape of the offline store (an ADR behind `dependencies.md`), tile serving, and anything about topology, which belongs to OQ-1 and to a second spike **that is named and not yet planned** (no `SP-2-*.md` exists on disk; naming a spike is not planning it). Scope creep here is how a spike becomes a project.

---

## 7. The rule while it runs

This rule is **lifted**, because the spike closed on 2026-07-31. While it ran, no further specification was written on the sync path, which is the foundation's own instruction on OQ-10 and the reason this document exists. Specification on that path now proceeds against ADR-0004.
