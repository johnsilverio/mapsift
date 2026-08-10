# MAP-10: a batch of client operations reaches the database, once, and can never be rewritten

## Trace

PRD **T2.2** (ordering authority and transport separation) and **M15** (the append-only log), with the
unknown-type clause of **M9**'s acceptance. Invariants **I2** and **I9**; constraints **C9**, **C4**, **C5**.
**ADR-0004** decision 2 for the shape of the transaction, **ADR-0005** sections 2 and 3 for the wall and the
role grants, **ADR-0007** sections 1 and 3 for where each file goes and what it may import, **ADR-0009**
section 4 for why the envelope types are never hand-written, and **ADR-0010** decision 6 with its addition
for the route this task fills, the request body it is handed, and the client a write test is allowed to use.

## What this task owns

The body of the django-ninja call the authenticated-request seam already publishes: it accepts a batch of
client-authored operations and persists them as rows in an append-only log inside the tenant wall. It creates
the `sync` package as a Django app and its first migrations. **The router already exists** (`mapsift/sync/api.py`,
delivered by MAP-34) and this task fills the handler that today binds the tenant and returns nothing.

**Order is deliberately not claimed here** (corrected 2026-08-07): the server-owned key that orders these
rows is the per-project version and it is MAP-11's, so this slice asserts that every operation of a batch
lands and none is lost, and asserts nothing about the sequence they land in.

**Atomicity is not claimed here either** (corrected 2026-08-10, boundary decision 7 below): this slice
asserts that a batch lands, not that it lands or fails as one.

## Out of scope

Named explicitly, each with the owner it goes to.

- **The projection.** Nothing in this task updates a feature, a layer, or any current-state row. Owner:
  the operation-log projection-strategy ADR, which M15 leaves open and which has no issue yet.
- **The per-project version and the two ADR-0004 lock rules.** Owner: **MAP-11**. This task fixes only the
  *place* the allocation will go, per the boundary decision below.
- **The assertion that the flush is one transaction.** Owner: **MAP-11**, by boundary decision 7 of
  2026-08-10. There is no failure reachable through the route in this slice that a non-transactional
  implementation would survive, so any test written here would pass for the wrong reason, which is the
  defect the first Window A review already found in another costume.
- **Dedup by mutation number and the echoed last-applied cursor.** Owner: **MAP-12**, including the clause
  MAP-10's own tracker acceptance points at.
- **Contiguity and the typed resend-from-cursor on a gap.** Owner: **MAP-13**.
- **The correlation keys and the redaction on the logging path.** Owner: **MAP-14**.
- **Normalizing the author an operation claims against the session that can prove it.** Owner: **MAP-37**,
  filed at this task's implementation review on 2026-08-10. The envelope carries
  `author_session_material` and M15's Shape requires it stored as authored, so this slice writes the claim
  and verifies none of it, which is C13's authorship half left open. **This line was missing while the
  implementation was written**, which is the same absence that blocked this task's first Window A, and it
  is written here rather than only in the tracker for that reason. The mechanism's offline half is OQ-18
  and stays open.
- **Conflict resolution, the per-feature version, and preserve-not-discard.** Owner: the next slice, whose
  input is OQ-8. A green build here proves ordering, not the moral line.
- **Anything on the WebSocket tier.** T2.2 is carried here as the negative half: no authoritative state is
  read from it, and this task does not build it.
- **Where the request's authenticated principal comes from, and the binding built on it.** Owner: the
  authenticated-request seam, which is a prerequisite of this task rather than a parallel one. **This line
  was missing from the first version of this file and its absence is what the MAP-10 Window A review
  found** (2026-08-07): with nothing saying where the tenant comes from, the only shape available to a
  window was to bind it from the value the client sent, which is C13's "free client field" and OWASP
  API1:2023 in one move. This task **consumes** that seam and does not build it.

## Boundary decisions the owner closed

The first six on **2026-08-07** and three more at the resumption on **2026-08-10**, each registered in the
document that owns it before this file was written; the reasoning is one grep away in `specs/log.md` under
those dates.

1. **This task owns the M15 log table**, because no issue in milestone 3 did.
2. **The flush appends and does not write the projection.**
3. **The echoed cursor is MAP-12's**, not this task's.
4. **MAP-10 dispatches alone, with ADR-0004's LATE ordering fixed as a constraint on shape:** validation and
   the log write happen before any version allocation, and the allocation is the last thing before commit.
   MAP-11 adds the allocation into that slot. This is the performance rule of foundation section 10 applied
   at design time, where it is free.
5. **Both armed re-checks return negative** as a consequence of decision 2, and re-arm at the first slice
   that reads a target path server-side.
6. **Append-only is enforced by privilege, not watched by a test:** ADR-0005 section 2, addition of
   2026-08-07, and M15's sharpened acceptance.
7. **The atomicity assertion moves to MAP-11, and the reason is that MAP-34 closed the last failure that
   reached it.** ADR-0010 decision 6 refuses a batch disagreeing on its tenant at the Pydantic boundary,
   before any binding, so no cross-tenant operation reaches the wall through the route any more. Nothing runs
   after the append in this slice, the log holds no foreign key to a layer or a feature, and a duplicate
   `operation_id` fails a single `INSERT` whole, which a non-transactional implementation survives
   identically. MAP-11 puts the version allocation after the append, which is the second statement a failure
   can roll the first one back from, and the assertion is written there. **PRD T2.2's acceptance never
   carried an atomicity clause** (gap detection and resync, and no authoritative state from the WebSocket
   tier, are its two clauses), so nothing in the canon is weakened; the clause was this file's own invention
   and is struck.
8. **The same operation never lands twice, refused by the database rather than by a check the writer
   remembers.** Structural integrity rather than a feature: M8 makes `operation_id` the operation's
   identity and a log admitting the same operation twice cannot support the idempotency MAP-12 will claim
   over it. Distinct from MAP-12's dedup key, which is `(client_id, mutation_number)` across batches.
   **The constraint that carries it is `UNIQUE (tenant_id, operation_id)`, and that spelling is a shape
   instruction for the implementing window, not a property a test pins** (corrected 2026-08-10 at the
   Window A review, which is where the over-specification was caught). The reason it is not a test's
   business: a test that named the constraint would be asserting implementation against
   `specs/testing.md` section 2, and the tenant half is already held by construction, since
   `tests/test_tenant_isolation.py` drives every tenant-owned table through a catalogue case refusing any
   non-primary unique index whose leading column is not `tenant_id`. What a test here may assert is the
   SQLSTATE, which separates a database refusal from a Python guard ahead of the insert.
9. **The flush answers with no body in this slice.** ADR-0010 decision 6's addition leaves the response
   shape to this task and constrains nothing; the only thing a client needs in order to advance its cursor
   is MAP-12's echoed last-applied, so inventing a shape now is the wire break the named request key exists
   to avoid. The handler keeps returning nothing.

## Evidence handed over

Transcribed rather than cited, because it exists nowhere else and was bought with a probe.

**django-ninja consumes the generated envelope types directly** (probed 2026-08-07 against the pinned
django-ninja 1.6.2, pydantic 2.13.4, Django 5.2.16; full record in `specs/dependencies.md` section 1).
`list[ClientHalf]` binds as a request body, discriminates on `operation_type`, and emits a `$ref` into
`components` so the M12 chain survives. **No adapter and no hand-written `ninja.Schema` is needed, and
writing one would violate ADR-0009 section 4.**

**An unknown `operation_type` is already refused at the boundary** by the generated discriminated union, as
a typed pydantic `union_tag_invalid`, before a handler is entered. M9's clause is therefore **asserted**
here, never implemented.

**Measured on disk at the resumption, 2026-08-10, and it replaces the pickup's own measurement, which MAP-34
overtook.** `mapsift/sync/` is still not a Django app: it has no `apps.py`, no `models.py` and no
`migrations/`, and `mapsift.sync` is absent from `INSTALLED_APPS`. It now holds `api.py`, `rules.py` and a
`tests/` package as well as the generated `envelope.py`. `import-linter` already names `sync` as the top tier
of the layers contract, so the package is anticipated by the gate and adding it must not break
`exhaustive = true`.

**Inherited from MAP-5 and still true:** `django.contrib.gis` is in `INSTALLED_APPS` and the engine is the
PostGIS backend.

**What went stale in the first Window A while this task was blocked, which is state rather than canon and is
why it is written here.** Those tests were authored on 2026-08-07 before ADR-0010 existed, so three contract
facts they encode are now wrong and the documents that hold the right ones are already in the reading
protocol: the route and the request body (ADR-0010 decision 6's addition), the client a write test is
allowed to use (the same addition, and `specs/dependencies.md` section 1 for the measurement under it), and
the envelope builders, which MAP-34 landed in `apps/api/conftest.py` and which
`mapsift/sync/tests/envelopes.py` now duplicates. The correction round owns all three.

## Acceptance

From the requirements, with the clause of each that this slice carries.

- **T2.2:** no authoritative state is read from the WebSocket tier, which is the clause of T2.2's acceptance
  this slice carries. The other, gap detection and resync from the database, is MAP-22's. **This bullet has
  no test and is satisfied by construction**, written down 2026-08-10 rather than left for a reader to count
  as covered: it is a negative about a tier this task does not build, and the honest form of the guarantee is
  that no module here imports Channels. When the tier exists, the assertion becomes MAP-21's.
- **M15:** the runtime role holds `SELECT, INSERT` and no `UPDATE, DELETE, TRUNCATE` on the log, so an
  in-place rewrite is refused by the database on the runtime path, and the test asserts that refusal
  **while distinguishing it from a statement that matched no rows**. The owner profile is outside that
  guarantee and ADR-0005 section 2 says why. The reproducible-projection and user-deletion clauses need the
  projection and are not this slice's. **What the row must carry is M15's Shape**, the M8 envelope as
  applied: these rows are the only record this slice produces, so a log of bare identifiers satisfies
  nothing downstream and starves MAP-12, whose dedup reads the clientID and the mutation number off them.
- **M9:** an unknown operation type is rejected with a typed error rather than ignored.
- **C4 and C13:** the new table is inside the wall on the same terms as every other tenant-owned table, and
  the cross-tenant case is impossible by construction rather than by a guard. The tenant a flush binds is
  the one the seam above resolved and verified against the authenticated principal, never the one the
  request asserted about itself. **ADR-0005 section 4's silence is the trap here twice over:** the wall
  denies by returning nothing and the grant denies by raising, so a test that asserts an empty result must
  say which of the two it caught.
- **M8:** the same operation never lands twice, and the refusal is the database's rather than a check the
  writer remembers, per boundary decision 8.

## Ratified at the Window A review, 2026-08-10

The names the suite chose and the implementing window is held to, so the shape is not guessed and then
defended. **`OperationLogEntry`** is the model and **`entry.client_half`** is where the stored envelope is
read from, chosen over `operation` or `envelope` because this slice persists only the client half and MAP-11
puts the server half beside it, so the accessor does not have to be renamed when that lands.
**`append_to_the_operation_log(list[ClientHalf])`** in `services.py` is the writer, and it is the only one.
Two additions to `apps/api/conftest.py` are ratified with it: the `UNIQUE_VIOLATION` SQLSTATE constant, and
three optional keyword arguments on `a_feature_create_claiming` (`operation_id`, `client_id`,
`mutation_number`), all defaulted so no existing call site changed.

## Ruled at the Window B review, 2026-08-10

**`editable=False` stays on the primary key and comes off `operation_id` and `client_half`.** On the key it
is the idiom Django's own generator writes for a defaulted UUID primary key. On the other two it has no
runtime effect in a project with no forms and no admin, and it sits three lines under a docstring saying
that what makes this table append-only is the grant in the migration and never a model option. A field
option that reads like the enforcement, directly beneath a sentence denying model-level enforcement, is a
signal pointed at the wrong mechanism, and the next reader is who pays for it. The cost of the correction
is regenerating the migration, which is one command while nothing outside a development volume has applied
it and a data migration afterwards, which is why it is taken now rather than carried.

**The trap that killed the first Window A's transactional tests, kept because it still governs anything
written near the wall:** `tenant_scope` opens `transaction.atomic()` itself
(`mapsift/common/binding.py`), so a test whose only transaction is the one its own context manager opened is
green against an implementation that has no transaction at all. That is why boundary decision 7 moves the
assertion rather than strengthening it.
