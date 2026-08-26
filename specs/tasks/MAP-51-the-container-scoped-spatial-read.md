# MAP-51: A spatial read in this product names a container, and cannot be written without one

> **Rewritten 2026-08-25, after a research round corrected the requirement this file assembles.** The first
> version sized the migration from an index shape ADR-0013 has since retracted, and its Acceptance ratified
> two cases that were then measured passing on a schema violating the property they exist to prove. Both
> corrections are in ADR-0013, dated; this file points at them rather than carrying them.

## Trace

Foundation **I4** (the wall) and **I6** (the per-tile budget); **C4**. PRD **M2** (the storage class that
decides the path) and **M15**'s `Open / ADR` bullet, whose spatial-index claim this round's ADR narrowed.
**ADR-0005** decisions 3, 5, 6 and 7 (the binding, the tenant-leading index, the tile path, and the shape a
catalogue case takes). **ADR-0013**, whose **decision 5, cases 7 and 8** is this task's requirement, read
against decisions 1 to 4 and against **condition 2**, which the two cases are sized from. Decision 4 names
**ADR-0007** as where the published selector lives and **ADR-0002 section 5** as the rules a gate lives by;
its **third** mechanism is out of scope below.

## What this task owns

A spatial read cannot be written without a container by the ordinary route, and that it cannot is proven from
the catalogue and from the plan rather than asserted.

**What that does not reach is stated here rather than left to be inferred**, because decision 4 spends a
paragraph on ADR-0002 section 5's third rule and a task spec claiming a wider guarantee than its requirement
would be breaking the rule it cites. The seam stops the **ordinary caller**; the residual decision 4 names is
not closed by this round, and its third mechanism is out of scope below.

## Out of scope

- **The merged unique-key gate carrying the same catalogue defect. MAP-59**, which also owns the **shared
  helper** both gates read an index's key columns through. This task consumes that helper; it does not own it.
- **The tile server's function source naming the container.** ADR-0013 decision 2 called that clause owed;
  this round's fan-out already **paid** it, and ADR-0005 decision 6 carries it dated 2026-08-25. What is out
  of scope is satisfying it, which is **MAP-55**'s.
- **Dropping `btree_gist`**, which the refusal left with nothing needing it. **MAP-52**. Note that case 7's
  enumeration now **covers** its 212 functions, so the two touch and do not conflict.
- **The ordering path.** ADR-0013's Consequences record a nearest-neighbour ordering visiting entries a
  reader cannot see, and say plainly that whether it wants an answer of its own is a later round's question.
  It has **no owner** and this task does not give it one; it only refuses to let that path arrive disguised
  as a clean plan.
- **The source gate**, the third of decision 4's three mechanisms. **MAP-58**.
- **PostGIS statistics functions answering across tenants. MAP-56.**
- **`prosecdef`**, a wider hole in the same wall than `proleakproof` and empty today. It belongs to ADR-0005
  decision 7, not to this ADR, and nobody has opened it.
- **Widening what the gates enumerate** past this task's need: `relkind = 'p'` for a partitioned parent,
  `geography` and domain-typed geometry columns. Each is real and each is about **what** is enumerated rather
  than **how** an index is read, which is this task's correction.
- **Any caller of the selector.** It is published and unconsumed until a read path exists; that is the cost
  the owner accepted on 2026-08-25.

## Boundary decisions the owner closed

Closed 2026-08-25 at the pickup, then **re-opened and re-closed the same day** after the research round.

1. **One window pair, not two.** The migration, the catalogue case and the plan case rest on one object.
2. **The published selector is built in this round.** Registered where it already lived: ADR-0013 decision 4.
3. **The plan case forces the index path rather than growing the fixture.** Registered as a dated note on
   ADR-0013 decision 5, whose stated reason was then **retracted and replaced** in the same note when three
   parties measured the planner already taking an index path unforced. Forcing stays; the mechanism is
   Window A's.
4. **The fan-out commits before dispatch.**
5. **Two containers are modelled and one is not.** ADR-0013 decision 2's note.
6. **The index is two btrees and the migration is additive**, not one three-column btree replacing what the
   table carries. ADR-0013 **condition 2**, corrected 2026-08-25, holds the measurement and the reasoning.
7. **Both cases witness something they did not.** ADR-0013 decision 5's correction of 2026-08-25 holds what
   each must assert and why the first design passed on a violating schema.

## Evidence handed over

**Measured 2026-08-25, two versions, and it is why condition 2 changed.** The sweep at
`specs/spikes/map-51-spatial-read-under-the-policy/version-and-order/` runs the project's own fixture against
PostgreSQL **17.11** and **18.6**. The 1,000-row layer read costs **965 buffers on 17 and 50 on 18** with the
container key buried third, and **38 on both** with it second. The conclusion is in condition 2; what is
handed over here is that **a number measured on one major version is not a number about this product** unless
the other one was run too.

**Measured 2026-08-25, and it is the trap this round exists to not repeat.** Two tables identical but for the
index, one of them carrying an index that does **not** lead on the tenant: `Index Cond` byte-identical,
`Actual Rows` and `Rows Removed by Filter` identical, 553 buffers against 7. Every assertion of the first
design passed on both. **The conclusion is refused rather than handed over:** which field discriminates them
is ADR-0013 decision 5's to say, and it says `Index Name`.

**Measured 2026-08-25, on the instrument rather than on the subject.** `Actual Rows + Rows Removed by Filter`
returned **180 on a bitmap path and 90 on an index-scan path for the same read at the same instant**. It is
also a per-loop average once `loops` exceeds one, and PostgreSQL 18 renders `Actual Rows` with decimals, which
`int()` floors.

**Measured 2026-08-25.** A negative assertion over an EXPLAIN field that defaults to empty passes on a
sequential scan.

**Read, with its source.** PostgreSQL's own regression suite runs `EXPLAIN (COSTS OFF)` without ANALYZE 2,235
times against 107 with it and masks every number through `explain_filter()`; `memoize.sql` keeps **zero
distinguishable from non-zero** and destroys magnitude. pgTAP has **no plan assertion at all** and reads no
index validity flag. This is context for the shape of an assertion, not an instruction.

**Measured 2026-08-25, and it closes a design option.** `ALTER FUNCTION ... LEAKPROOF` is superuser-only in
both directions, including on a function the migration role just created, so an in-suite positive control that
marks and rolls back is impossible. The mutant for that arm is a statement against a database of the run's
own, under `--reuse-db`; `--create-db` rebuilds from migrations and takes it with it. ADR-0002 section 5,
amended 2026-08-25, carries the rule.

**Operational, cost three runs at MAP-39's Window B (2026-08-20).** `apps/api/pyproject.toml`'s `addopts`
already carries `-q`, so `pytest -q` is effectively `-qq` and swallows the final count line. Run `pytest`
bare or with `--tb=short`.

## Acceptance

The requirement is **ADR-0013 decision 5, cases 7 and 8, as corrected 2026-08-25**, read there. The delta:

- **MAP-51's acceptance clause 1 as originally written is retired** and the issue body says so; clause 2 was
  delivered by ADR-0013. Neither is this round's.
- **The migration is additive.** `layers_feature` already carries the btree for one of the two containers, so
  what is red is the other one. Size it from **condition 2**, never from case 7's sentence, which an index
  already present can be read as satisfying.
- **Case 7's leakproof arm is green on a clean install**, so its red is defined against a database mutant and
  the exit is a run the orchestrator performs, in the shape MAP-43 established. Its **positive** arm and its
  index arm are red.
- **Case 7 reads key columns through the MAP-59 helper.** If that helper does not exist when this window runs,
  that is a finding reported back, not a licence to hand-roll the join the correction exists to remove.
- **Case 8 carries the limitation registered in ADR-0013 decision 5**: it witnesses the shape of the index
  path when taken, and neither that the planner takes it nor any timing. The node type is not part of the
  assertion, and `Index Name` is.
