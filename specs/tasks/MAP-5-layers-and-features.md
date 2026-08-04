# MAP-5: layers and features, and the class that decides the path

> **What this is.** The spec-per-task the authority chain ends at (`CLAUDE.md`, Process and tracking): what an
> implementing window reads, assembled from the documents that already decided it. It **cites and never
> restates**; where this file and a cited document disagree, the cited document wins and this one is the
> defect. Read `specs/testing.md` before writing a line of either window.
>
> **Trace.** PRD **M2** (elements and layers as persisted shapes, and the class that decides the path),
> **M3** (identity of every created object), **M5 rule 1** (the storage frame), **T6.1**, **N2**; foundation
> **section 3** (the elements and layers frontier), **I3**, **I4**; **C1**, **C3**, **C4**; **ADR-0005**
> sections 5 and 7, **ADR-0006** section 3.
>
> **The pattern to copy is on disk.** `specs/tasks/MAP-3-account-tree.md` and the code it produced
> (`apps/api/accounts/`) are how this repository writes a tenant-owned model and puts it inside the wall.
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
  this slice. The enforceable half of M5 rule 1 today is that the stored geometry column declares
  **EPSG:4674**; there is no source CRS to record until something is imported.

That scoping is read off the slice boundary in OQ-4 and off the issue's own note, not decided here. A
reviewer who disagrees argues it in the issue, never by widening the model.

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
  `accounts/migrations/0001_initial.py` already uses. **`mapsift_tile` gets nothing yet**, deliberately: it is
  the direct-to-PostGIS reader and the tile path is an open ADR, so granting it now would scaffold a decision
  nobody has taken (ADR-0001 section 8).
- **Composite references over `(tenant_id, key)`** (ADR-0005 section 5): feature to layer, and layer to
  project. As in MAP-3, the Django field carries `db_constraint=False` and the real constraint is added in a
  `RunSQL` operation, because a single-column reference crosses tenants.
- **Identifiers as the native `uuid` type with no server-side default** on either table (ADR-0006 section 3,
  M3): a feature is minted by the client that draws it, offline, and a database default would quietly make
  the server the allocator the first time a code path forgot to send one.
- **Indexes lead with `tenant_id`** (ADR-0005 section 5): `(tenant_id, layer_id)` on feature, and
  `(tenant_id, project_id)` on layer.

---

## 4. Two things this task hits that MAP-3 did not

Both were found by reading the code on disk, and both are stated here so a window does not lose an hour to
them.

**`Project` carries no `UNIQUE (tenant_id, id)` while `Workspace` does.** A composite reference from `layer`
to `project` has nothing to point at until it exists, so this task adds it, by exactly the rule and for
exactly the reason that put the matching constraint on `Workspace`
(`workspace_identity_within_its_tenant`, ADR-0005 section 5). It is redundant against the primary key and it
is not removable.

**`django.contrib.gis` is not in `INSTALLED_APPS`, while the database engine is already
`django.contrib.gis.db.backends.postgis`.** This is the first task that declares a geometry column, so it is
the first moment that gap can matter. **Verify what the installed Django's own GeoDjango installation
documentation requires, against the version in `apps/api/uv.lock`, and do not assert it from memory**: that
is the external-dependency rule, and it is the whole reason this line says "verify" instead of naming an
answer.

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
   data and it is tested as one.

**The invariant acceptance tests, against a real database, because the wall is the database's.** These are
C4 and N2 tests and they may never be weakened:

4. the existing catalogue enumeration now returns the two new tables with row-level security **enabled and
   forced**, and it passes **unchanged**;
5. a read or write bound to one tenant cannot reach another tenant's layer or feature **by any path**,
   including through the composite reference and including a unique-key collision that would reveal the row
   exists (N2, ADR-0005 section 5);
6. neither new table carries a **server-side default** for its identifier, asserted from the catalogue rather
   than reviewed (ADR-0006 section 3);
7. the geometry column declares **SRID 4674**, asserted from the catalogue (M5 rule 1).

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
reasoning. **Do not edit `accounts/migrations/0001_initial.py`**, which is applied; the new migration puts its
own tables inside the wall in its own module.

**One choice this file does not make for you, with a recommendation and its reason.** Where these two models
live is a Django app-layout call that no document in the canon decides. The recommendation is a **new app**
rather than growing `accounts`, because `accounts` holds the account tree and these are its contents, and
because M2 makes the layer the thing that decides while the feature is subordinate to it. Name it for what it
holds. Make the call, note it in the pull request, and move on; it is not worth a round trip.

**One structural-performance question to settle rather than skip** (foundation section 10: structural
performance is free at design time and is therefore not optional). ADR-0005 section 5 requires every index
serving a tenant-scoped query to lead with `tenant_id`, because the policy adds that predicate to every query
on the table. A spatial index does not naturally lead with anything. Decide deliberately whether the geometry
index is a plain spatial one that the planner combines with the tenant index, or a composite that leads with
the tenant, **against the current PostGIS and PostgreSQL 18 documentation rather than from memory**, and
record what you chose and why in the pull request. If it needs a number to settle, it is a measurement and
not a hunch.

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
