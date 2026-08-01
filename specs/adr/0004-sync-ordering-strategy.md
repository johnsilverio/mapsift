# ADR-0004: The sync ordering strategy

- **Status:** accepted (2026-07-31)
- **Deciders:** the owner, on the numbers the SP-1 spike produced
- **Authority:** derives from `specs/mapsift-foundation.md` v0.15 (section 10, the ordering authority; OQ-10, closed by this ADR) and `specs/PRD.md` v0.11 (T2, T4, M8, M10, N10). Where this ADR and the foundation disagree, the foundation wins.
- **Supersedes:** nothing. **Superseded by:** nothing.
- **Delivers:** the exit of spike **SP-1** (`specs/spikes/SP-1-postgres-ordered-sync.md`), including the fifth version axis that PRD M10 declared missing.

---

## Context

The foundation put the ordering authority in PostgreSQL with the WebSocket tier carrying transport and presence only, and recorded that this was sound in principle with **no documented production precedent found**, so it had to be validated in a spike before specification was built on top of it. Specification was then built on top of it in quantity (T2, M8, M10, N10), which is why the spike ran now rather than earlier.

The trap the spike existed to catch is documented and is not subtle. A sequence value in PostgreSQL is taken at INSERT, before COMMIT, so a transaction that started later can commit first with a higher number. A consumer polling `WHERE position > last` advances past rows that commit late, and those rows are committed, durable, and invisible forever. That is silent loss, which this product refuses by construction.

Three candidate strategies were measured, mapped onto Mapsift with the **project** as the space:

- **A, per-project version.** A version integer per project, incremented inside the flush transaction under a row lock, so version order is commit order by construction.
- **B, transaction-id watermark.** Rows carry a 64-bit transaction id; the reader only reads below the current snapshot's xmin, so the cursor can never pass an in-flight write.
- **C, row version plus a Client View Record.** Per-row version, with a client-side record the pull diffs against.

---

## What was measured

All numbers were produced on one machine against PostgreSQL 18.4 in a container, with psycopg 3.3.4 and Python 3.14.6, on 2026-07-31, and are recorded with their conditions in the spike's result files. Absolute values are machine-specific. **The shape of the curves and the failure modes are what transfer.**

**The negative control ran first and passed.** The naive design lost **53.6%** of committed rows at ten concurrent writers (268 of 500), with the reader's cursor finishing at the highest position, convinced it had seen everything. With a single writer it lost nothing, which is what proves the harness detected that mechanism rather than noise. A harness that cannot catch the known bug cannot grade a fix.

**Stage A, correctness:** all three passed no-loss, no-duplicate, monotonic-cursor and delete-representable at 1, 2, 5 and 10 writers.

**Stage A, cost:**

| | write p50 at 10 writers | throughput at 10 writers | rows scanned per poll at 5,000 backlog |
|---|---|---|---|
| A | 9.3 ms | 508 ops/s | 6 |
| B | 2.0 ms | 1020 ops/s | 6 |
| C | 2.0 ms | 989 ops/s | **2,615** |

**Stage A, the long-transaction test, which is the finding that separated A from B.** An unrelated transaction that has written anything holds a real transaction id, which pins the watermark. Held for four seconds, candidate **B's feed stopped completely** and the row appeared 4001.7 ms after commit, at the instant of release. A read-only holder did nothing, which narrows the exposure but does not remove it. A and C were unaffected by either holder.

**Stage B, the protocol loop under deliberate chaos: 7/7 for both A and B.** Convergence; idempotent resend after a lost acknowledgement with the cursor advancing only from the server's echo; gap detection and resync with no notification delivered at all; contiguity enforced by a typed resend-from-cursor that applied nothing from the gap onward; two installations of one user with independent cursors and no false dedup; 5,000 operations in bounded batches, interrupted and resumed; and a client a month out on its clock still landing in server order.

**The addendum that decided how A is built** is in the Decision below.

---

## Decision

### 1. The ordering strategy is the per-project version (candidate A)

Each project carries a monotonic version integer, allocated inside the flush transaction. Version order is commit order by construction, which closes the sequence trap at the root rather than working around it.

**The decisive reason is not throughput, it is the shape of the failure.** A's cost is local, proportional and diagnosable: contention on one project, felt by the people on that project, in proportion to how hard they are hitting it. B's two costs are neither.

- **B couples liveness to unrelated subsystems.** Mapsift runs heavy analysis in background jobs that write their results (foundation section 10). Those are long transactions that have written, which is exactly what pins the watermark. Under B, a routine analysis stops the sync feed for every user of the installation, with no error and no signal, and the burst that arrives on release can turn a background job into human conflict work on legal-weight geometry.
- **B's cursor is bound to the physical identity of the database cluster.** Transaction ids are assigned from a counter global to one PostgreSQL installation. A logical restore into a new cluster produces unrelated ids, so every persisted cursor becomes meaningless, and it fails **silently in both directions**: a client either re-downloads everything or believes it is current when it is not. This is decisive here rather than merely awkward, because Mapsift's cursor lives on offline clients for as long as the supported offline window (PRD M4), so a migration or a disaster restore hits every tablet in the field at once. A physical streaming replica shares the id space and is unaffected; logical restore and logical replication are not.

Candidate A's cursor is an ordinary integer in an ordinary column. It survives dump and restore, logical replication and host migration, because it is data rather than an artifact of the installation.

### 2. Two engineering rules are part of this decision, not an optimisation to add later

Serialisation is not caused by the number of writers. It is caused by **how long each writer holds the lock, times how often it takes it**. Both rules attack exactly that, and they were measured.

- **RANGE.** A flush allocates its whole range in one statement (`version + N`) and distributes the N versions internally. A 500-operation batch takes the lock **once**, never 500 times. Ordering still holds because the allocation happens inside the transaction under the lock.
- **LATE.** The allocation is the **last** thing before commit. Dedup, contiguity, feature-version assignment, the conflict rule and every validation run before it. Under the lock there is one allocation and one bulk insert.

**Measured, ten people editing interactively while a field client flushes 3,000 operations:**

| | batch | interactive p95 | worst interactive save | flush |
|---|---|---|---|---|
| without the rules | 500 | 95.3 ms | **782 ms** | 817 ms |
| **with the rules** | **500** | **14.7 ms** | **40.1 ms** | **188 ms** |
| with the rules | 100 | 9.4 ms | 13.8 ms | 243 ms |

The worst interactive save drops **fifty-six fold** and the flush itself gets **four times faster**, because the lock stops being held across hundreds of round trips. Both sides win, so this is not a trade.

**LATE matters more over time than the numbers above show.** These inserts are bare; a real push carries validation, geometry and the conflict rule. Without LATE, a heavier push extends the lock directly. With LATE, the push can grow without the critical section growing at all.

Two supporting rules, from established practice and not measured here: the version row lives in a **narrow dedicated table** (identifier and version only, separate from project metadata) so updates stay HOT and the table stays cached; and that small, extremely hot table carries its **own aggressive autovacuum settings**, because a row updated thousands of times per second is where bloat starts.

**Ten people editing interactively, with nothing else running, measured 1.5 ms p50 and under 10 ms worst case even without the rules.** The concern that a small project with ten people would feel slow does not survive contact with the numbers: ten humans with think-time between saves leave that lock idle roughly 98% of the time. The regime that needed engineering was bulk flush concurrent with interactive editing, and that is what the rules above address.

### 3. Batch size is the declared knob, bounded on both sides

PRD N10 already requires bounded batches with per-batch acknowledgement. This ADR fixes what sets the bound: **larger batches make the flush faster and the worst interactive save slower.** The starting value is **500**, which measured a 40 ms worst-case interactive save against the PRD N1 interaction budget of 200 ms at the 75th percentile, leaving five times headroom. It is tuned against measurement, never guessed.

### 4. The resync cursor is the fifth version axis, and PRD M10 is completed by it

PRD M10 named four axes and recorded that none of them was the resync cursor, declaring itself incomplete until this spike closed. **The per-project version is a fifth axis with its own owner and its own mechanism:** server-assigned, monotonic per project, allocated under the project lock, and distinct from the per-feature version, which orders and detects conflict on one feature. A client presents the project version to ask for everything since it last looked.

### 5. Candidate C is eliminated, with the reason recorded

C is correct. It loses on read cost, which grows with the size of the project rather than with the number of changes: **2,615 rows scanned per poll** at a 5,000-operation backlog, which also **halved write throughput** (224 against 555 ops/s) because the reader competes with the writer for the same database. For an append-only log that only grows, that has no ceiling. Its remaining cost was deliberately not exercised by the harness and stands anyway: the real Client View Record lives in a separate store, which puts that store on the correctness path.

### 6. Candidate B is documented as the alternative, with the two conditions that return it to the table

B is faster and its read is as cheap. It comes back only if **both** of these hold: measured load on a single project approaches the ceiling of A as built under rule 2, and there is an answer for cursor durability across a logical restore. Neither is true today and neither is expected soon.

---

## Consequences

**What this buys.** The trap is closed at the root rather than mitigated. The cursor is ordinary data that survives the operational events a long-lived product actually meets. Sync liveness is decoupled from every other subsystem's transaction behaviour. And PRD M10 stops being incomplete.

**What this costs, accepted with eyes open.**

- **Writes serialise per project.** The published figure for this shape is around fifty pushes per second per space at a 20 ms push, and our bare-insert measurement of 508 ops/s at ten writers is the same mechanism with a cheaper push. Plan with **the published figure**, not with ours. Against a project edited by two or three people, which is what the domain round found, that is ample.
- **No atomicity across projects.** An operation that must be atomic while spanning two projects is **not expressible** under this strategy. Nothing in the current model asks for one, and PRD M1 already treats cross-tenant transfer of a project as a distinct recorded operation outside Layer 3's scope. If such an operation is ever specified, this ADR is what it must be reconciled against.
- **One hot row per project**, with the narrow-table and autovacuum consequences named in Decision 2.

**Two documented costs of this strategy do not apply to Mapsift, and the reason is recorded so nobody reopens it.** The published guidance says the strategy requires soft deletes; Mapsift's log is append-only (PRD M15), so a delete is an appended operation and never a removed row, which the spike confirmed by passing the delete criterion on all three candidates. The guidance also says partial sync and read authorisation get harder; Mapsift grants access per whole project (PRD T6.4, T6.5), so there is no partial view within a project to break.

**What this forecloses.** Nothing the foundation left open, beyond the cross-project atomicity named above.

**What must be revisited, and when.** If measured single-project load approaches the ceiling, or if a cross-project atomic operation is specified, this ADR is superseded rather than edited. The spike's harness is throwaway and is deleted; its test cases are re-derived as real tests inside `apps/api`, and the list of them is in Stage B of the spike document.
