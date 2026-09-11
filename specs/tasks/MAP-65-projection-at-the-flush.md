# MAP-65: The flush materializes the current state, so the log stops being the only thing a write produces

## Trace

**PRD M15** (the append-only log and its projections: the current state the application reads **is** a
projection of the log, and the reproducibility clause that makes the chain evidence). **PRD T2.2**, its
**requirement sentence** rather than its acceptance list, for the transactionality that keeps the append and
the projection consistent; the acceptance list under T2.2 is about dropped notifications and resync and is
not this task's, which is the distinction MAP-10's review earned and MAP-11's spec recorded. **PRD M9** for
the target path and the whole-geometry rule that decides what a replay is. **PRD M2** for the storage class
sitting on the layer. **PRD T2.3**, whose first acceptance clause is **already witnessed over the log** by
MAP-12 (`test_a_queue_resent_whole_after_a_partial_flush_lands_only_what_was_missing`, which names that clause
in its own docstring); what this task adds is the **feature-state** reading of the same clause, no duplicated
feature meaning no second row in the projection. **PRD N9** for the record every refusal owes, which is what
the new refusal reaches. *Added 2026-09-09 at the Window A review and corrected the same day at the re-read:
the first form claimed T2.3 had no runtime, which is false of the clause and true only of its feature-state
half, and it named N9 nowhere while a case in the diff already cited it.*

Invariants **I2** and **I10**. Constraints **C9**, **C4** and **C12**. **ADR-0011 section 4** for the record
shape that refusal takes.

**ADR-0012 decisions 1, 2, 3 and 6** (the whole of the strategy: the maintained table, the table it is, the
placement and the ordering, the grant). **ADR-0004 decision 2** for where this write sits in the flush order.
**ADR-0007 section 3** for which file each piece goes in. **ADR-0010 decision 6, addition of 2026-09-08**,
for the refusal this write creates. **ADR-0005 sections 3 and 4** for the binding every one of these reads
and writes happens inside.

## What this task owns

A flush that leaves `layers_feature` holding the current state its batch produces, in the same transaction
that appends the log, and that refuses in a typed way rather than crashing when an operation addresses a
layer that does not exist.

## Out of scope

- **The per-feature version** and its column: **MAP-38**, which this blocks.
- **`applied_at`**: **MAP-53**. Its absence is why the reproducibility clause is split below.
- **The two refusals a layer's own declarations make**, its storage class and its geometry family, whose
  rules already sit unwired in `layers/rules.py`: **MAP-66**, which this blocks.
- **The rebuild path** for the projection. ADR-0012's Consequences says why M15's acceptance is not the test
  of it and names no owner; this task does not open one.
- **The frame a wire geometry declares for itself**: **MAP-69**. The write stamps the storage frame on the
  parsed payload, which is a relabel and not a transformation, and a payload carrying its own `crs` member has
  that declaration overwritten rather than refused. *Added 2026-09-11 at the final review, where the Spec axis
  found this deferral recorded in no document on the branch while `specs/log.md` lists the defect beside two
  this task did close, so a reader would conclude all three were fixed.*
- **A geometry payload the parser or the column cannot take**: **MAP-70**. The projection makes a
  client-supplied payload reach GEOS and PostGIS for the first time, and four wire-legal shapes answer `500`.
- **Any read of the projection.** The container-scoped selectors have existed since MAP-51 and gain **no
  caller here**. The one read this task does perform is inside a test, and the evidence block below is about
  exactly that read.
- **Legal weight** (OQ-8, the engineer's) and **authorship normalization** (**MAP-37**). Both are qualifiers
  on M15's reproducibility clause and both are why it is split.

## Boundary decisions the owner closed

Each went into the document that owns it before this file was written. These are pointers.

**1. The unknown-layer refusal is typed, answers `409`, and joins the closed reason set** (2026-09-08).
Registered in **ADR-0010 decision 6, addition of 2026-09-08**, which also records why the shape is reused
rather than given a sibling body, why the type's cursor-shaped name survives a container-shaped member, and
what the null restart point now means. Read it there.

**One thing inside that decision was the software side's rather than the owner's and is flagged as such:**
the member's **spelling**. The ADR fixes it, because ADR-0010's own history twice records a public wire value
living as a constant in a test module as the defect, so leaving it to a window would repeat that. If the
owner wants a different spelling it changes in the ADR first and this file follows.

**2. M15's grant clause is not this task's acceptance** (2026-09-08). It is already witnessed, in full,
including its negative control and its `TRUNCATE` arm. See the Acceptance block.

**3. M15's reproducibility clause is split rather than shortened** (2026-09-08). See the Acceptance block.

## Evidence handed over

**A lazy `QuerySet` built inside a binding and evaluated outside it answers zero rows and raises nothing.**
*Measured 2026-08-28, by two parties independently: 0 rows outside the binding, 2 inside.* `TenantOwnedManager`
raises `TenantNotBound` when a selector is **called** with no binding in force, so the loud failure is
covered; what is not covered is a queryset **built** inside `tenant_scope` and **evaluated** after the
`atomic()` block closes, which has lost `SET LOCAL mapsift.tenant_id` and is answered by the policy with
silence. Nothing in the suite covers this direction.

**Why it is handed to this task specifically, and the conclusion is deliberately not handed over with it.**
The reproducibility case below has to read both the log and the projection. If that read is written lazily
and evaluated outside the binding, it returns nothing, and nothing is indistinguishable from *this feature
has no chain*, so the case passes for the wrong reason. **Whether the remedy is to force evaluation inside
the binding, to read inside a single scope, or something else, is the window's to decide**, and so is
whether this deserves a case of its own. The measurement is handed over; the design is not.

**`pytest -q` in this repository is effectively `-qq` and prints no count line**, because `apps/api/pyproject.toml`'s
`addopts` already carries `-q`. Run `pytest` bare or with `--tb=short`. This is in `specs/log.md` and is
repeated here only because it has cost three runs at a previous Window B.

**What is measured and lives in a document, so it is cited rather than transcribed:** the `ON CONFLICT DO UPDATE`
cardinality violation when one statement affects a row twice, and why folding by target path is not enough
(**ADR-0012 decision 4**); the deadlock counts behind the sorted ordering (**ADR-0012 decision 3**, which
sweeps **two** variables rather than one, the per-row against the batched statement and the random against
the sorted array, so the three figures are read there and not paired here); the 96x and 756x that chose the
strategy at all (**ADR-0012**, What was measured). Read them there. None of the three is this task's to
re-derive.

**No existing flush test arranges a layer, so the suite already authors batches this task's refusal will
start refusing.** *Measured 2026-09-09 across the whole suite:* **thirteen modules reach the flush route and
exactly one arranges a layer**, which is this task's own new module. `grep -rn "Layer\b"` over `conftest.py`,
`mapsift/sync/tests/` and `tests/test_authenticated_request.py` returns nothing at all, and both shared
arrangers default `layer_id` to a fresh `uuid4()`. This was inert while nothing consulted the layer. *Measured
by implementing the refusal in a read-only scratch copy at the ADR-0012 decision 3 position:* the suite goes
to **52 failed, 248 passed** against a 12/288 baseline, **44 green cases across nine modules going red**.

**What that means for this window, with the conclusion deliberately refused.** One of the cases that turns red
is MAP-12's `test_a_queue_resent_whole_after_a_partial_flush_lands_only_what_was_missing`, the existing witness
of the T2.3 clause the Trace above names, so a window meeting it red has to be able to tell an expected
consequence from a defect, and that is why this is handed over rather than discovered. **Which shape closes it
is the window's:** the shared fixture carrying a layer, the arrangers creating the one they address, or
something neither of those. What is not the window's is editing an existing case to accommodate it
(`specs/testing.md` section 1), so the remedy lives in the arrangement rather than in any `def test`.

**One thing that is already true on disk and shortens the work:** `layers_feature` already carries the grant
ADR-0012 decision 6 requires, from `layers/migrations/0001_initial.py`, and no column of this task's is new.
Whether that leaves this task with no migration at all is the window's finding to report, not this file's
claim.

## Acceptance

**The delta against the requirements, which the window reads from the PRD where they are law.**

**M15's reproducibility clause is split, and the split is a runtime fact rather than a preference.** The
clause reads *replaying a **legal-weight** feature's **attributed** chain in server order reproduces its
current authoritative geometry exactly*, and two of its qualifiers have no runtime here. **Legal weight** has
no marker on `Feature` and its classification rule is OQ-8, the engineer's. **Attributed** needs the
authoritative applied-at (**MAP-53**) and the normalized author (**MAP-37**), and the log carries neither
today. **The marker's home is the layer rather than the feature** (M7), and neither model carries one, which
is written out because the shorter sentence this replaces read as though the feature were where it belonged. What this task proves is the clause's **mechanism**: replaying one feature's ordered chain from the
log in the order the server recorded reproduces the geometry the projection holds. The two qualifiers are
named here so the clause is visibly incomplete rather than quietly reinterpreted, and they arrive with their
owners.

**M15's grant clause is not in this task's acceptance and no case here restates it.** It is already
witnessed, in `apps/api/mapsift/sync/tests/test_append_only_log.py`, by five cases covering the whole
grant, the negative control that stops the three refusals passing vacuously, and the `UPDATE`, `DELETE` and
`TRUNCATE` arms each distinguished from a statement that matched no rows. It is a clause about the **log**,
and this task writes the **projection**. Writing it again here would be a second copy of a green guarantee.

**T2.2 is cited at its requirement sentence and not at its acceptance list.** Its acceptance is about a
dropped notification recovered by gap detection, which is MAP-22's. What this task carries from T2.2 is the
transactionality of the flush, which is what makes the append and the projection consistent or neither, and
that lives in the requirement sentence. This is the correction MAP-10's review produced and MAP-11's spec
recorded; it is repeated as a pointer because the same mis-citation is available here.

**The typed refusal's *shape* has no upstream PRD criterion, and its *record* does.** No PRD requirement names
an unknown-layer refusal, its `409` or its reason code: that is created by ADR-0010 decision 6's addition of
2026-09-08 and is cited there, and a window will not find it upstream and should not invent one. **But N9's
acceptance carries the record half** ("every user-visible refusal has a matching record and the reverse; a
failure with no user-visible signal and no record fails review"), which is why this refusal owes a
`request.refused` in the shape of ADR-0011 section 4 exactly as the two existing reasons do. *Corrected
2026-09-09 at the re-read: the first form said "nothing in the PRD carries it" without qualification, which
told a window not to look for the one upstream that does exist and would have lost the record N9 requires.*
