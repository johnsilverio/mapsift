# MAP-5: layers and features, and the class that decides the path

> **What this is.** The spec-per-task the authority chain ends at (`CLAUDE.md`, Process and tracking): what an
> implementing window reads, assembled from the documents that already decided it. It **cites and never
> restates**; where this file and a cited document disagree, the cited document wins and this one is the
> defect. Read `specs/testing.md` before writing a line of either window.
>
> **Trace.** PRD **M2** (elements and layers as persisted shapes, and the class that decides the path),
> **M3** (identity of every created object), **M5 rule 1** (the storage frame), **T6.1**, **N2**; foundation
> **section 3** (the elements and layers frontier), **I3**, **I4**; **C1**, **C3**, **C4**; **ADR-0005**
> sections 5 and 7, **ADR-0006** section 3, and **ADR-0007** for where every file in this task goes.
>
> **The pattern to copy is on disk.** `specs/tasks/MAP-3-account-tree.md` and the code it produced
> (`apps/api/mapsift/accounts/`) are how this repository writes a tenant-owned model and puts it inside the wall.
> Read both before starting; almost every mechanical question below is already answered there.

---

## 1. What this task delivers

Two persisted shapes, **layer** and **feature**, both inside the isolation wall, with the **storage class on
the layer**, and geometry stored in the one frame M5 rule 1 declares. That single field is what makes the
foundation's frontier implementable instead of aspirational, and it is the reason this issue precedes
milestones 2 and 3: every operation, version and flush in them addresses a shape that does not exist yet.

---

## 2. The shape, and what this slice deliberately leaves out

M2 fixes the full shape and this file does not re-derive it. What it does fix is the **scope**, because the
first vertical slice (foundation **OQ-4**) takes the tree only as deep as the slice needs and its operation
catalog is create a feature and set its geometry.

**Carried here:** on the layer, its identifier, its tenant, its project, its name, its geometry kind, and its
**storage class** (element or served). On the feature, its identifier, its tenant, its project, its layer,
and its geometry.

**Deferred, each with the owner that holds it, so neither window invents one:**

- **the attribute schema and attribute values (M6).** Nothing in this slice reads or writes an attribute, and
  M6 fixes rules that would be modelled blind here: the stable key that is the field's identity and is never
  reused, the three types that carry a reference rather than a value, and the date field that declares whether
  it carries an offset.
- **the legal-weight marker (M7)**, which waits on **OQ-8**, exactly as MAP-3 named it.
- **style (F1 to F4)** and **source, attribution and licence (B4)**, both outside the slice by name.
- **the source-CRS provenance of M5's Shape**, because it is an import-time fact and import (B2) is not in
  this slice.
  > **Correction (2026-08-04), and the sentence it replaces is the most expensive kind of wrong, because
  > the next window would have read it as true.** This bullet used to end: "the enforceable half of M5 rule
  > 1 today is that the stored geometry column declares EPSG:4674; there is no source CRS to record until
  > something is imported." Measured on this branch against PostgreSQL 18.4 and PostGIS 3.6 on 2026-08-04,
  > that column declaration is two different guarantees on two different paths and only one of them was
  > real.
  > **The writer that never passes through the ORM was already closed**, by the column's own type modifier
  > rather than by a constraint anybody added: a raw insert of a parcel in EPSG:31983 is refused with
  > SQLSTATE 22023, `Geometry SRID (31983) does not match column SRID (4674)`. That is I4's reasoning
  > applied to the frame, and the direct-to-PostGIS tile reader is exactly the writer it covers.
  > **The ORM path was wide open.** GeoDjango wraps a value whose SRID differs in `ST_Transform`, so the
  > same parcel was accepted, converted to degrees, and its source frame discarded with nothing raised.
  > M5 rule 1 requires the source CRS recorded and never discarded, and rule 3 requires a datum
  > transformation to be an explicit recorded decision, so that path broke both. It is closed here rather
  > than deferred, in `mapsift/common/geometry.py`, at the point where the conversion happened: a geometry
  > declaring another frame is refused instead of converted, so what is stored is coordinate for
  > coordinate what was sent.
  > **What stays open, each with the path that owes it.** A geometry arriving with **no frame declared at
  > all** is taken to be in the storage frame already, which is an assumption rather than a recorded fact;
  > the boundary that has to turn it into one is the flush's, where the envelope declares what it carries
  > (M8, M11, M12, MAP-7 onwards). And the **legitimate conversion**, the one that records the source CRS
  > and transforms once authoritatively, belongs to import (B2), which section 7 puts out of this slice by
  > name.

- **the layer's `kind`, vector or raster, from M2's Shape**, and this line exists because an adversarial
  review found the omission silent rather than deferred, which is the one thing this section may not do.
  A raster layer reaches the product only through import (B2), it has no features, and nothing in this
  slice can create one or read one, so the owner is the served path whose tile server is still its own ADR
  (ADR-0001 section 8). **The consequence is stated rather than implied:** with `kind` absent and
  `geometry_kind` NOT NULL, a raster layer is **unrepresentable today**, and the served storage class
  exists partly for it. What makes the deferral cheap rather than a debt is that both halves are additive
  and backfillable: every layer that can exist before a raster path exists is a vector layer, so `kind`
  arrives later with `DEFAULT 'vector'` correct for every row already written, and `geometry_kind` drops
  its NOT NULL in the same migration. Neither is a data migration that has to decide anything.

That scoping is read off the slice boundary in OQ-4 and off the issue's own note, not decided here. A
reviewer who disagrees argues it in the issue, never by widening the model.

### 2.1 One rule this task invented, and the half of it that is the owner's

**The rule.** A feature's geometry must belong to the family its layer declares, and a disagreeing one is
refused. **M2 does not say that.** It gives a layer a geometry kind and stops; nothing in the PRD turns
that declaration into a constraint on the layer's features. The rule was invented in section 5 of this
file, which makes its test a test with no requirement, and `specs/testing.md` section 6 calls that a
candidate for deletion. Raising it into the PRD is an owner decision and is **not** taken here.

**What was closed on 2026-08-04 without taking that decision.** The rule as first implemented compared the
declared kind against a concrete type by identity, and that half is not open: **D3 makes multipart geometry
and a ring with an enclave a domain requirement rather than a nicety**, because a legal reserve is
frequently one or the other, so an identity rule would refuse one. The declared kind is therefore a
**family**, with `Polygon` and `MultiPolygon` both inside it. That half traces to a requirement and is
closed; the rule's existence does not and is not.

**Road A, raise it into the PRD.** M2 grows one acceptance: a feature's geometry belongs to the family its
layer declares, multipart and enclaves inside that family, and a disagreeing geometry is refused rather
than stored. **Costs** a PRD round with its fan-out, and then a caller, because the rule closes nothing
until the write path calls it (the flush, MAP-10 to MAP-14). **Buys** a layer that cannot come to hold a
geometry it cannot render, style, or measure.

**Road B, delete it.** `geometry_is_admissible` and its test module go, under `specs/testing.md` section 6.
The layer's declared kind stays what M2 makes it, a declaration, until something needs it to be more.
**Costs** nothing today and closes no door, because road A stays available the day the requirement is
written. **Buys** a suite where every test still names a requirement that exists.

**A recommendation, which is not the decision.** Road A: a declaration a feature may contradict is worth
little, and the write path that would call the rule is the next milestone rather than a distant one. Until
the owner takes it, the rule stays pure and callerless and its test module says in its first paragraph that
it has no requirement above it.

---

## 3. What the migration carries, beyond the tables

Each item names the decision it comes from, so a reviewer checks it against that document rather than against
this list.

- **Both tables are tenant-owned** and go inside the wall: `ENABLE` **and** `FORCE ROW LEVEL SECURITY`, one
  policy each, using the guarded expression `nullif(current_setting('mapsift.tenant_id', true), '')::uuid`
  (ADR-0005 sections 3 and 7, which names `layer` and `feature` among the tables inside the wall). The
  existing N2 catalogue test then covers them **without being edited**, because it enumerates from the
  catalogue rather than from a list. **If that test has to be edited to pass, the model is wrong, not the
  test.**
- **Grants for `mapsift_app`** on the two new tables, following the shape
  `mapsift/accounts/migrations/0001_initial.py` already uses. **`mapsift_tile` gets nothing yet**, deliberately: it is
  the direct-to-PostGIS reader and the tile path is an open ADR, so granting it now would scaffold a decision
  nobody has taken (ADR-0001 section 8).
- **Composite references over `(tenant_id, key)`** (ADR-0005 section 5): feature to layer, and layer to
  project. As in MAP-3, the Django field carries `db_constraint=False` and the real constraint is added in a
  `RunSQL` operation, because a single-column reference crosses tenants.
- **The feature's reference to its layer is three columns wide, not two, and this is a hole window A found in
  an earlier version of this list.** A feature carries both a project and a layer (M2), and the two composite
  references above close the tenant channel while closing nothing between them: a feature can be filed under
  project X while its layer lives in project Y, and the row then resolves to two projects, which contradicts
  M2's own acceptance that a feature resolves to exactly one. So the layer additionally carries
  `UNIQUE (tenant_id, project_id, id)` and the feature references **`(tenant_id, project_id, layer_id)`**
  against it, which subsumes the two-column reference rather than sitting beside it. It is the same ADR-0005
  section 5 rule one column wider, and it is settled here rather than later because the alternative is a
  constraint added to a live table.
- **Identifiers as the native `uuid` type with no server-side default** on either table (ADR-0006 section 3,
  M3): a feature is minted by the client that draws it, offline, and a database default would quietly make
  the server the allocator the first time a code path forgot to send one.
- **Indexes lead with `tenant_id`** (ADR-0005 section 5): `(tenant_id, layer_id)` on feature, and
  `(tenant_id, project_id)` on layer.
  > **Correction (2026-08-04), and the implementing window was right to refuse half of this line.**
  > ADR-0005 section 5 fixes that an index serving a tenant-scoped query **leads** with the tenant;
  > it does not enumerate which indexes exist, and this list overstepped it. The composite unique
  > key the reference above already requires, `(tenant_id, project_id, id)` on layer, is a btree
  > that answers both `WHERE tenant_id = x` and `WHERE tenant_id = x AND project_id = y` from its
  > leading columns, so a separate `(tenant_id, project_id)` index is a **strict prefix duplicate**:
  > it serves no read and costs every write. The same reasoning removes Django's default
  > single-column index from the tenant foreign keys. On the highest-volume table in the product,
  > whose write path is a flush of queued operations and whose keys are random by ADR-0006, paying
  > for an index nobody reads runs against the performance rule rather than serving it.

- **The spatial index is a plain GiST, and the condition that flips it is named**, because a deferral with
  no trigger is a decision nobody ever revisits. The shape is foundation section 6's: the tiling gate
  defers pre-generated tiles to a **measured** per-tile budget rather than to a feeling. ADR-0005 section 5
  requires an index serving a tenant-scoped query to lead with `tenant_id` and a GiST index leads with
  nothing, so the alternative is a composite `(tenant_id, geometry)` under `btree_gist`.
  > **Correction (2026-08-04): the decision is right and the reason first recorded beside it was wrong in
  > the clause that matters.** The field's comment said the composite would serve "a query nobody has
  > written". That query is written, in **ADR-0005 section 6** and **foundation section 6**: tiles are
  > served straight out of PostGIS with the isolation policy adding `tenant_id = ...` to every query, so
  > the tenant-scoped bounding-box query is the tile path's ordinary shape rather than a hypothetical.
  >
  > **Measured** on PostgreSQL 18.4 with PostGIS 3.6, 1.000.000 features across 100 tenants, 2026-08-04.
  > With tenants **sharing an extent**, the composite answers a tenant-scoped bounding-box query in
  > **0,12 ms against 2,14 ms** and scans **18 index entries against 12.492**. With tenants
  > **geographically separate** it loses, **4,02 ms against 2,40 ms**. And it costs **86 MB against
  > 40 MB**. So the plain GiST is right while tenants are separated on the map, which is the anchor
  > domain's ordinary case, and wrong by an order of magnitude the day two consultancies work the same
  > municipality.
  >
  > **The trigger, named rather than left to judgement:** the composite plus `btree_gist` is introduced
  > when a measured tenant-scoped spatial query on real data crosses the I6 per-tile budget **and** its
  > plan shows the index scanning entries belonging to tenants the query cannot see. That is a
  > measurement under the N1 protocol, recorded with its device, versions, fixture and date, and it is
  > deliberately two conditions rather than one, because the first alone can be met by a query that is
  > slow for a reason this index cannot fix.

- **The feature table deliberately carries no `UNIQUE (tenant_id, id)`**, and this is an answer rather than
  the silence a review found. That composite is what ADR-0005 section 5 requires of a table something else
  references, and the argument for adding it preventively is real: the alternative is a constraint on the
  highest-volume table in the product, which is exactly why `Project` got its equivalent in this same
  change. It is refused here on the **direction of derivation**. M15 makes the operation log the source and
  the current state its **projection**, so a referential constraint from the log to the feature would make
  the source depend on its own derivative; and the log has to **outlive the feature it describes**, because
  a legal-weight feature that is deleted keeps its chain (C7, M15) and whether such a project can be
  physically deleted at all is OQ-20. That is why M9 carries the target path as an **address in data**
  rather than as a foreign key. So the table whose write path is a flush of queued operations does not pay
  for an index nobody reads, which is the same rule that removed the prefix duplicate above (foundation
  section 10).
  **The trigger:** the first tenant-owned table that must reference a feature by a **referential
  constraint**, which the operation log is not. **And the live-table objection is answered rather than
  waved away:** adding it later is `CREATE UNIQUE INDEX CONCURRENTLY` followed by
  `ADD CONSTRAINT ... USING INDEX`, which builds without holding writes out, so it is not the migration
  the preventive argument imagines. `Project`'s key is a different case: it is pointed at by a constraint
  that exists in this very migration.

- **A note rather than a change, so nobody reads it as a regression later.** The composite references above
  are `NOT DEFERRABLE`, which is PostgreSQL's default, while Django's own single-column tenant foreign key
  on the same tables is `DEFERRABLE INITIALLY DEFERRED`, which is Django's. The mixture is inherited from
  MAP-3 rather than introduced here, and it is therefore a **permanent property of every tenant-owned
  table** until something changes it deliberately. It matters only where a transaction would create two
  rows that reference each other, which nothing in this slice does.

---

## 4. Two things this task hits that MAP-3 did not

**`Project` carries no `UNIQUE (tenant_id, id)` while `Workspace` does**, which is a real gap rather than a
deliberate omission. A composite reference from `layer` to `project` has nothing to point at until it exists,
so this task adds it, by exactly the rule and for exactly the reason that put the matching constraint on
`Workspace` (`workspace_identity_within_its_tenant`, ADR-0005 section 5). It is redundant against the primary
key and it is not removable.

**`django.contrib.gis` enters `INSTALLED_APPS` here, and that was already decided rather than discovered.**
`specs/dependencies.md` section 1 records the reasoning and the verification: the engine is the PostGIS
backend from the first line, but the app loads GDAL and GEOS at import while the developer host is not
required to carry them (ADR-0001 section 3 puts running in the container and authoring on the host), and it
was verified that `manage.py check` passes with the engine set and the app absent. That entry names its own
trigger, **"it goes in with the first geometry model, inside the container"**, and this task is that model.
So add it, and confirm the container is where it runs; there is no open question to research here, only a
dated decision to execute.

---

## 5. Window A, the tests

Write these as **failing** tests and nothing else. Do not write, sketch, or look at an implementation
(`testing.md` section 1). Each test **names its requirement ID** (section 6 of the same document), and each
asserts a behaviour rather than a shape.

**The pure decisions, which carry the bulk of the suite, and which exist because the queue does not.** M2's
acceptance is written in terms of an operation queue that MAP-7 to MAP-14 have not built yet. The queue is an
effect; what this task owns is the **decision** underneath it, and pulling it out is `testing.md` section 3
applied rather than quoted.

1. **Which path a feature takes is a function of its layer's storage class alone.** Element enters the
   operation queue, served does not. This is the function the flush issues consume later rather than
   re-derive, so it is worth naming well.
2. **The class is the layer's and never the feature's**, which is the testable form of M2's second acceptance
   ("a feature does not change path without its layer changing class"): there is no per-feature class to
   change, so the path cannot drift per feature. Whether a feature may move between layers at all is
   promotion, and promotion is **OQ-6**; do not decide it here.
3. **A feature's geometry kind agrees with the kind its layer declares**, and a mismatch is refused rather
   than stored. PostgreSQL cannot express this as a check across two tables, so it is a decision over plain
   data and it is tested as one. **This item is the one thing in this file with no requirement above it,
   and half of it is the owner's; read section 2.1 before touching it.**

**The invariant acceptance tests, against a real database, because the wall is the database's.** These are
C4 and N2 tests and they may never be weakened:

4. the existing catalogue enumeration now returns the two new tables with row-level security **enabled and
   forced**, and it passes **unchanged**;
5. a read or write bound to one tenant cannot reach another tenant's layer or feature **by any path**,
   including through the composite reference and including a unique-key collision that would reveal the row
   exists (N2, ADR-0005 section 5);
6. neither new table carries a **server-side default** for its identifier, asserted from the catalogue rather
   than reviewed (ADR-0006 section 3);
7. the geometry column declares **SRID 4674**, asserted from the catalogue (M5 rule 1), and, per the
   correction in section 2, that declaration is a **shape** assertion that neither write path is entitled
   to be read off: each is asserted as behaviour, the writer outside the ORM refused by the column's own
   type modifier and the writer through it refused instead of silently converted.

**The shape's own invariants** (M2, M3): a feature resolves to exactly one layer, one project and one tenant,
and a layer to exactly one project and one tenant; an ordinary update cannot move either across tenants.

**What window A must not test** (`testing.md` section 7): that Django saves a row, that a foreign key
constrains, that GeoDjango round-trips a polygon, or any generated type. Those test Django, PostGIS and the
generator. The subject here is the class that decides the path, the wall, and the frame.

---

## 6. Window B, the implementation

Read the tests as a contract authored by someone else and write the **minimum** to green. **A test may not be
edited to make it pass**; a test that looks wrong is a finding reported back, never a licence to rewrite the
contract (`testing.md` sections 1 and 9). Design happens in the refactor step under green.

Generate rather than hand-write: `python manage.py startapp`, `python manage.py makemigrations`, never a
hand-written migration file (ADR-0002 section 1, `dev-workflow` section 3). What the autodetector cannot
produce (the policies, the grants, the composite constraints) goes in `RunSQL` operations inside the
generated migration, and that migration **cites ADR-0005 and ADR-0006 by number** rather than restating their
reasoning. **Do not edit `mapsift/accounts/migrations/0001_initial.py`**, which is applied; the new migration puts its
own tables inside the wall in its own module.

**Two mechanical things, probed rather than assumed, so the first command of this window does not fail.**
`python manage.py startapp layers mapsift/layers` **does not refuse** a directory that already holds window
A's `tests/` package; measured in the container on 2026-08-04, it exits 0 and writes its template beside it.
What it writes that this project does not use, and that the MAP-3 round already deleted from `accounts/`, is
`admin.py`, `views.py` and **`tests.py`**, and the last one is the one that bites: a `tests.py` module sitting
next to a `tests/` package in the same directory is a name collision nobody enjoys diagnosing. Delete all
three. And **`mapsift.layers` must be added to the `layers` list of the `import-linter` tiers contract**
above `mapsift.accounts`, or the new package sits outside the gate entirely; note while doing it that the
contract is **not** `exhaustive`, so today a package added later is silently unguarded, which is the opposite
of the by-construction property N2 has and ADR-0007 section 4 claims.

> **Correction (2026-08-04), both halves of that last sentence now closed and the second was missed the
> first time.** The **tiers** contract is `exhaustive`, corrected inside ADR-0007 section 4. Its sibling
> could not be: `import-linter` offers no `exhaustive` option for a **`protected`** contract, so its module
> list stayed the one part of the gate a new package is silently absent from, and this task's own package
> was absent from it. `apps/api/tests/test_dependency_direction.py` closes it the way N2 closes the wall,
> by enumerating the packages that hold models from disk and asserting the gate covers exactly them. It
> also catches the mistake that looks like the obvious fix: a `protected` contract applies **every** allowed
> importer to **every** protected module, so folding two packages into one contract reads as coverage while
> granting each one access to the other's models.

**Where the code goes is decided and is no longer this file's to recommend.** **ADR-0007** fixes the layout:
one subpackage per **domain** under `mapsift/`, so these two models are a **new package** rather than growth
inside `accounts`, with the per-package file roles of its section 3 (`models.py`, `rules.py` pure,
`selectors.py`, `services.py`, `capabilities.py`, one thin `api.py`) and its tests under the package. The
tenant binding and the tenant-owned manager come from **`mapsift.common`** and are not re-implemented or
imported out of `accounts`. Only the package's **name** is left to the implementing window; name it for what
it holds, note it in the pull request, and move on.

**One structural-performance question to settle rather than skip** (foundation section 10: structural
performance is free at design time and is therefore not optional). ADR-0005 section 5 requires every index
serving a tenant-scoped query to lead with `tenant_id`, because the policy adds that predicate to every query
on the table. A spatial index does not naturally lead with anything. Decide deliberately whether the geometry
index is a plain spatial one that the planner combines with the tenant index, or a composite that leads with
the tenant, **against the current PostGIS and PostgreSQL 18 documentation rather than from memory**, and
record what you chose and why in the pull request. If it needs a number to settle, it is a measurement and
not a hunch.

> **Settled 2026-08-04, and it did need a number.** It is a plain GiST, and the measurement, the condition
> under which the answer inverts, and the named trigger that flips it are in **section 3** rather than in a
> pull-request body, because a pull request is not a place a later window reads.

---

## 7. Out of scope, named so neither window drifts in

The operation envelope and the catalog (MAP-7 to MAP-9), the flush and the version axes (MAP-10 to MAP-14),
the per-project version table and its autovacuum settings (MAP-11, ADR-0004), anything in the client core or
the web client, import and the element budget that classifies at import (B2, M2, and an unmeasured number in
PRD 10.5), the permission model above the wall (T6.2 to T6.5), the legal-weight marker (M7, which waits on
OQ-8), the attribute schema (M6), styling, any metric at all (this slice stores geometry and does not measure
it, G1 and D8), and the login path's cross-tenant question, which is MAP-27 and not this one.

---

## 8. Done

The five points of the `linear-workflow` definition of done, with one of them doing real work here as it did
in MAP-3: the behaviour is proven by tests **written first**, which is checkable, because window A's commits
land before window B's and the tests are red in between.
