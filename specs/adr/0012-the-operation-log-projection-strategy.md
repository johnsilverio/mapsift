# ADR-0012: The operation-log projection strategy, and where the applied server half is stored

- **Status:** accepted (2026-08-21)
- **Deciders:** the owner, on the MAP-50 pickup (two research rounds, a reproduction probe, and two adversarial reads, 2026-08-21)
- **Authority:** derives from `specs/mapsift-foundation.md` v0.18.1 (section 10's performance rule, I10) and `specs/PRD.md` v0.16 (M15, M10, M9, M2). Where this ADR and the foundation disagree, the foundation wins and this ADR is the one that is wrong.
- **Supersedes:** nothing. **Superseded by:** nothing. **Amends:** ADR-0004 decision 4's addition of 2026-08-10, which decision 5 below makes stale in two places.
- **Delivers:** the **materialization half** of PRD M15's `Open / ADR` line (its retention half is OQ-20 and stays open) and item 9 of the `specs/dependencies.md` ADR agenda; unblocks MAP-38 and fixes what MAP-23 asserts against.

---

## Context

PRD M15 settles that the current state the application reads **is** a projection of the append-only log, and
delegates only the materialization strategy, bounded by its reproducibility acceptance. Measured at pickup
against `add8d8e`, **no projection exists**: nothing writes `layers_feature`, `mapsift/layers/` carries no
`services.py` and no `selectors.py`, and the only occurrence of `Feature` outside tests is its model
definition.

MAP-50 as created already put "where the authoritative per-feature version lives" among what this decision
has to settle. **The owner widened it further at pickup on 2026-08-21**, to the storage of the whole applied
server half, because the generated `ServerHalf` declares six fields and the log persists exactly one of them
as a column, so choosing a home for one field alone would pre-decide the other five in silence. That
widening is what authorises decision 5 and its deferrals; decision 4's storage half was in scope from the
issue's creation, and **decision 4's mechanism half stays MAP-38's**.

Foundation section 10 puts the burden of proof on one side of this and names it: "a materialised projection"
is listed with the cache, the denormalisation and the second store, each of which "waits for a number showing
it is needed". This ADR does not get to argue that a maintained table is structural. It has to produce the
number.

## What was measured

On PostgreSQL 18.4 and PostGIS 3.6.4 in the project container, 2026-08-21, **with the tenant-isolation policy
in force**, against a fixture carrying the real DDL of `layers_feature` and `sync_operationlogentry`. Every
timing is a **median of five runs** after a warmup. The experiment is in
`specs/spikes/map-50-projection-strategy/` and can be re-run; its README carries the two conditions that make
a number from it worthless if skipped.

**The negative control ran first and its result is the reason the rest is trusted.** The known-wrong variant,
which filters the log spatially before reducing to the latest row per target path, returned **1,201**
features it must not have, against the
**1,200 movers the fixture creates by construction**. It did not land exactly on the predicted count: the one
extra is a feature whose home sits on the box boundary and whose per-version jitter took an earlier version
inside, which is a fixture artifact rather than an instrument failure. **The control passes**, and it passes
by catching a defect at the order of magnitude the fixture guarantees rather than by matching it exactly.

**Fixture A: 20,000 features, 21 operations each, 420,000 log rows, 380,000 carrying superseded geometry.**

| read of current geometry in a bounding box | policy in force |
|---|---|
| maintained current-state table | **42.5 ms** |
| latest-row-per-target-path from the log, best correct form, covering index | **4,088 ms** |
| the same, written naively | **32,131 ms** |
| the same, spatially filtered first | 17,014 ms, and **the wrong answer** |

**96x in the best correct form and 756x written the obvious way.** The number section 10 asks for exists, and
it is not close.

**Fixture B, a separate sweep, is what isolates the cause**, and its rows are not interchangeable with
Fixture A's. Holding the feature count at 20,000 and varying operations per feature: at two each (zero
superseded rows) the log read costs 1,798 ms and the projection 49.6 ms; at twenty-one (380,000 superseded
rows) the log read costs 4,143 ms and the projection 42.8 ms. **Supersession makes the log read 2.3 times
worse and leaves the projection alone.** What makes it expensive in the first place is decoding geometry out
of `client_half`: the same read against a log carrying a typed geometry column, on Fixture A, costs 292 ms.

**What owns that last question, stated narrowly because a wider claim was made here and was wrong.** MAP-33
covers the encoding of the geometry inside the envelope: its Trace names PRD M8's `Open / ADR` and its
Acceptance requires it to say what happens to the MAP-8 interim payload shape, which is what a log row holds
today. **What nobody owns is whether the server additionally denormalises geometry into a typed column beside
the jsonb**, which is a storage question rather than a wire-encoding one. This ADR records the measurement
and does not take it.

**The append is the more expensive write, not the cheaper one.** Per operation on the same 1 KB geometry:
`UPDATE` on a projection 2,684 bytes of WAL, `INSERT` into the log 3,395. Keeping both costs roughly 6 KB per
edit. Nobody should choose the log expecting to save on writes.

## Decision

### 1. A maintained current-state table, written at the flush

Replay on read is rejected on the numbers above. M15's reproducibility acceptance does **not** discriminate
between the two, and the reason is structural: PRD M9 forbids a vertex delta and requires a geometry
operation to carry the whole geometry, so replaying a feature's geometry is a latest-row-per-target-path
query rather than a fold, and both shapes reproduce it exactly. What separates them is drift, and drift
exists on only one side. Decision 3 is what keeps it at zero.

Marten, the closest prior art on PostgreSQL, names three lifecycles rather than the pair M15 frames: inline,
live and async (martendb.io/events/projections, read 2026-08-21). **Async is refused rather than merely
unchosen**: an eventually-consistent projection means the log says applied while the state a user reads does
not. Foundation section 9.6.7 calls state misread as correct "the preserve-not-discard sin in the read
direction", and although its subject is temporal skew between an old client and a new server rather than a
stale projection, **the harm it names is the same harm** and no other section names it better.

### 2. The projection is `layers_feature`, written through a `layers` service

The direction is already enforced by CI rather than open. `apps/api/pyproject.toml` sets the tier order
`["sync", "layers", "accounts", "common"]` with `exhaustive = true`, and a `protected` contract confines
`mapsift.layers.models` to `mapsift.layers`. So `sync` may call `layers` and never the reverse, and
`sync/services.py` may not import `Feature` at all. The write lands in `layers/services.py` under ADR-0007
section 3 and the flush calls it.

**ADR-0007 section 4's snippet still shows the two-tier form** it had before `sync` and `layers` existed.
Correcting it belongs to that ADR and is named in Consequences.

### 3. The projection write is inside the flush transaction, before the range allocation, over a sorted set of rows

Inside, because a projection written outside the transaction that appends the log is the drift this decision
exists to prevent. The Rails Event Store guidance for synchronous handlers, to swallow the exception and send
it to a tracker (railseventstore.org, read 2026-08-21), is **poison in this codebase for exactly that reason**
and is named here because somebody will find it.

Before the allocation, because ADR-0004 decision 2's LATE rule is a claim about the critical section and the
projection write is per-operation work. **The flush order is ADR-0004 decision 2's, with one step inserted:
the projection write goes immediately before the cursor write.** That ADR owns the rest of the sequence and
is not restated here.

**And this decision creates an N-row lock exposure that is its own, not MAP-38's.** A per-operation
projection write inside one transaction takes **one row of `layers_feature` per distinct feature among the
batch's target paths**, and holds each to commit, whatever MAP-38 later decides about the version. The row is
per feature and the target path is finer (M9 makes it `tenant, project, layer, feature, property`), so a
batch of a hundred operations across forty features is a forty-row exposure rather than a hundred-row one. **So the rows are taken in a deterministic order,
sorted by feature identifier, and that ordering is part of this decision.** Measured: four workers, twelve
transactions each, per-row statements in random order produced **14 deadlocks in 48**; one batched statement
over a randomly ordered array produced **4**; over a **sorted** array, **zero**. A batched upsert plans as a
Function Scan and processes rows in array order rather than key order, which is why the ordering has to be
the application's rather than the planner's.

**This reorders code that exists.** `append_to_the_operation_log` today builds its entries inside itself,
after the cursor write. Building them earlier is the shape ADR-0004's correction of 2026-08-11 called better
and "not required here", so adopting it is sanctioned, but it is a refactor rather than a description of what
is already there.

### 4. The per-feature version is a column on `layers_feature`, and the mechanism is MAP-38's

**Where it lives is this ADR's**, and was from MAP-50's creation. It is a column on the projection row, not a
table of its own. Three reasons. The projection write already takes that row under decision 3, so the version
costs no second lock and no second table. A version derived instead from the log would be the
`max(project_version)` escape ADR-0004 decision 2 names as the sequence trap in a new costume, reached
through a different door. And a column on the projection is rebuilt by whatever rebuilds the projection,
rather than needing a second reconstruction path of its own.

It is **nullable, with its reason**: PRD M2 puts the storage class on the layer, and a served layer's features
never enter the operation queue, so a served feature has no per-feature version and the column says so rather
than inventing a zero.

**How it is allocated is MAP-38's**, and this ADR stops here. One thing is handed over as measured evidence
rather than as a decision, because it cost a probe: **`ON CONFLICT DO UPDATE` raises a cardinality violation
when one statement affects a row twice**, so a batch meets it whenever two operations touch **the same
feature**, whatever their target paths, because the projection row is per feature. Geometry set plus
attribute set on one feature is an ordinary flush and hits this; **folding the batch by target path is not
enough and folding by feature is what the statement needs.** PG18's `RETURNING WITH (OLD, NEW)` distinguishes an update from an insert in one statement, measured on
this server; PG17 needed a prior `SELECT … FOR UPDATE` for the same distinction, which is documentation
rather than something measured here.

The deadlock measurement is **not** handed to MAP-38, because decision 3 above already spends it.

One further measurement, with its condition stated because the condition is not the shipped schema: on a
table with an added **unindexed** column, an update touching only that column cost 168 bytes of WAL as a HOT
update, and indexing that column took the same update to 1,978 bytes and non-HOT, because changing one
indexed column requires a new index tuple in every index including the GiST. `layers_feature` as shipped has
five columns and none is an attribute, so this is a property of indexing a hot column on a GiST-bearing table
rather than a measurement of this table today. It is the reason **not to index the per-feature version unless
a query needs it**, which is a constraint on MAP-38 rather than a mechanism for it.

### 5. `applied_at` gains a column now; three fields keep ADR-0004's rule

ADR-0004 decision 4's addition of 2026-08-10 says the server half assembles at the read boundary "once its
remaining fields have owners", and lists four fields as undecided work: the per-feature version, the applied
rule version, M7's legal weight in force, and a verdict set with one member. **`applied_at` is not among them
and is not undecided.** T5.3 fixes it as the authoritative stamp explicitly distinguished from the client's
untrusted `created_at`, and M15 requires each chain entry to carry it. Measured at pickup, the log holds **no
timestamp column of any kind**, so under T5.3 and M15 an applied operation's authoritative applied-at is not
reconstructible from anything stored today. That is a defect this ADR closes rather than inherits, and
**MAP-53 lands it**.

**This amends ADR-0004 decision 4's addition in two places**, and that ADR needs the dated note: the set of
columns it names a log entry as carrying gains a third, and its list of four undecided fields becomes three,
decision 4 above having given the per-feature version an owner. The conditions the remaining three wait on
are ADR-0004's and are not restated here.

### 6. The grant on `layers_feature` states its own set, and `DELETE` stays with its reason

ADR-0005 section 2's addition of 2026-08-10 fixes that a grant is decided per table by what that table
guarantees. `layers_feature` keeps `SELECT, INSERT, UPDATE, DELETE` for `mapsift_app`, because **it is not
purely a projection of the log**. M2 puts the storage class on the layer rather than on the feature, and a
served layer's features never enter the operation queue; with one `Feature` model today, that one table
therefore holds log-derived element features beside import-derived served features. **That single-table
consequence is a reading of the current model rather than a sentence M2 states.** Narrowing `DELETE` would
constrain the served path, which is not this decision's subject.

`TRUNCATE` stays ungranted. Rebuilding the projection is an owner-profile operation, not a runtime one.

### 7. What this decision does not take

**It does not fix the spatial read.** The 42.5 ms above is the projection under the isolation policy and it is
a sequential scan: no spatial index is used, because row-level security refuses a non-`leakproof` qual as an
index condition and `st_intersects` is not leakproof. At 60,000 features that read is 109 ms **on a third
fixture of the same shape, recorded in MAP-51 and in ADR-0005's correction of 2026-08-21 rather than here**,
which eats more than half of PRD N1's 200 millisecond interaction ceiling before serialization, network, or
anything the client does. **N1's 50 millisecond long-task line does not grade a server query**: it is a
browser main-thread rule on a named reference device, and it is one of N1's two interaction rules rather than
one of the three budgets whose conflation N1 separately forbids. The comparison above is also a median
against a ceiling N1 states at the 75th percentile, so it is indicative rather than a verdict.

The projection is necessary and insufficient, and the rest is **MAP-51**, which is an ADR of its own because
the candidate remedy is a security assertion.

It does not take retention, archival or physical deletion (OQ-20, which is the other half of M15's
`Open / ADR` line), the conflict rule or preserve-not-discard (the next slice, gated on OQ-8), whether the
server denormalises geometry into a typed column beside the jsonb (unowned, see above), or snapshotting,
which is an optimisation with no number yet and therefore waits under the same section 10 rule this decision
was held to.

## Consequences

- **Every element write now touches two tables in one transaction**, so the flush's failure surface grows by
  one write, and the atomicity T2.2's requirement sentence already asks for is what keeps them consistent.
- **No counter table is added.** Putting the version on the projection row is what avoids a second grant, a
  second policy, a second composite key and a lock ordering *between* tables. The ordering *within*
  `layers_feature` is decision 3's and is not avoided by this.
- **The projection is rebuildable from the log only for what the log produced.** `layers_feature` also holds
  served features that no operation created (decision 6), so a rebuild path that empties the table and
  replays destroys them. Whatever rebuild exists is scoped to log-derived rows, and **M15's acceptance is not
  the test of it**: that acceptance is per-feature, geometry-only and legal-weight-only, so it tests one
  feature's chain reproducing one geometry and says nothing about a table-wide rebuild or about the
  per-feature version.
- **ADR-0004 decision 4 and ADR-0007 section 4 both need a dated note**, the first because decision 5 amends
  its column set and its list of four, the second because its tier snippet predates two packages.
- **The measured numbers are on PostgreSQL 18.4 while the sanctioned minor is 18.6**, because the image was
  deliberately not pulled mid-round. Ratios transfer; absolute milliseconds do not. Re-measure from
  `specs/spikes/map-50-projection-strategy/` before any of these figures becomes a baseline.
- **This ADR's reproduction round refuted the figures its own first research round produced**, which had been
  measured with the policy bypassed and against a log carrying a typed geometry column. Both were true of
  their configuration and neither was true of this one. **Two adversarial reads then found thirteen defects
  in this document, and three of the second read's four blocking ones had been introduced by the correction
  of the first.** That is the argument for the reads, and also the argument for keeping the experiment where
  somebody can re-run it instead of trusting the prose around it.
