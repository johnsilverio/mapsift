# MAP-66: an operation the layer's own declarations reject is refused with a typed error, not stored

## Trace

**Requirement:** PRD **M2** for the storage-class clause and the geometry-family clause of its Acceptance;
PRD **M9** for the shape of the refusal, which is where "flagged and retained for inspection" is law.

**Invariants and constraints:** **I1**, **I9**; **C1**, **C7**.

**Code shape:** **ADR-0010 decision 6**, whose addition of 2026-09-15 fixes both reason values, the new
`refused_operation_id` key and the rule for when it is populated, and whose addition of 2026-09-08 fixes the
member this one follows; **ADR-0005 sections 3 and 4** for why the read happens inside the binding;
**ADR-0007 section 3** for where a pure rule, a read and a write each live; **ADR-0012 decision 3** for the
write these refusals stand in front of. `specs/testing.md` sections 2, 3, 6 and 9.

**Named as the reason this is reachable at all and not as this task's requirement:** MAP-65, which made the
projection write, and MAP-64, which published `create_layer` and deferred both refusals here by name.

## What this task owns

The two decisions a layer's declarations already make about its features get a caller on the flush path, so
an operation naming a served layer, or carrying a geometry outside the family its layer declares, is refused
before it becomes current state.

## Out of scope

- **The element budget and the import classification.** M2's other Acceptance clauses. Nothing imports, and
  the budget is a PRD 10.5 measurement downstream of running code.
- **A feature changing path.** Its promotion half is **OQ-6**, which M2's Open/ADR scopes to where a
  promoted analysis result lives. Its layer-changing-class half is **M2 Acceptance clause 4**, a requirement
  rather than an open question, and it is out of scope here because nothing changes a layer's class today.
- **A flag on the refused operation, and a refusal that does not stall the stream.** That is T5.2's shape
  and it is **MAP-72**, which MAP-37 depends on. ADR-0010 decision 6's correction of 2026-09-16 records that
  the whole-batch refusal this task ships does not yet meet the foundation's retryable-refusal requirement,
  and why it is accepted until MAP-72 lands.
- **What a valid geometry payload is on the wire.** **MAP-70** owns the four shapes that answer `500` and
  **MAP-69** the relabelled frame; **MAP-33** owns the encoding both feed. A payload whose `type` is absent
  or is not a string is theirs, not this task's refusal.
- **A create addressing a feature that already exists**, and its mirror. **MAP-68**. That create is not the
  no-op its issue once described: it moves the feature to the layer it names and keeps the stored geometry,
  so a geometry of one family can end up under a layer that declares another. Measured 2026-09-16, below.
- **The per-feature version.** **MAP-38**, whose column ADR-0012 decision 4 already placed.
- **Who may create or classify a layer.** The permission model, deferred by the Open/ADR of **T6.3, T6.4
  and T6.5**, which PRD **10.6** records as pointing at themselves and as a decision the PRD still owes; and
  the licence tiers **T6.2** rests on, which are foundation **OQ-7**. OQ-7 is market, pricing and licensing
  and does not itself own who may create a layer.

## Boundary decisions the owner closed

Closed 2026-09-14 and 2026-09-15. Each is recorded in the document that owns it; this is the pointer.

1. **The family is read from the payload's own `type`, without parsing the geometry**, and the check
   applies **only where the payload carries a geometry at all**. This keeps the task independent of MAP-70,
   three of whose four shapes die inside GEOS or GDAL construction while the fourth, the three-dimensional
   point, reaches PostGIS and dies on insert; its own issue carries the measured table. A `feature.geometry.set` carrying null is not a family
   violation and is not refused: it is a statement that clears the stored geometry, which ADR-0012 decision
   3's addition of 2026-09-09 makes a different thing from saying nothing, and the Evidence block below
   names the green case that posts one. That scoping sentence is in ADR-0010 decision 6's addition of
   2026-09-15, not invented here. Where the boundary against MAP-70 lies is the Out of scope block above.
2. **Both refusals refuse the whole batch**, so retention is by construction. ADR-0010 decision 6's
   addition of 2026-09-15, last paragraph. Every refusal on this route already has that property, at the
   Pydantic boundary and after the binding alike; nothing here is new about it.
3. **The existing `no_layer_in_this_project` refusal and the case that witnesses it stay.** That member is
   ADR-0010 decision 6's addition of 2026-09-08 and this task does not touch it, which is the whole of what
   was closed. **How the declarations are read is the window's**, under ADR-0007 section 3, which fixes that
   a read lives in `selectors.py` and fixes nothing about how many reads there are.
4. **The geometry refusal names its operation and the storage-class refusal does not.** The rule, and the M9
   clause that forces it, are ADR-0010 decision 6's addition of 2026-09-15.

## Evidence handed over

**Measured 2026-09-15 on `main` at `85ed416`, by grep over all of `apps/api` outside `mapsift/layers/`.**
Every claim below is a grep result. Where a claim is about a suite passing rather than about a file's
contents, it says so.
*(Corrected 2026-09-15 at the pre-dispatch read, which re-ran both greps and found this block claiming a
wider scope than the greps behind it had covered. The first version searched `mapsift/sync/tests/` and
`conftest.py` and reported its result as though it had searched everything outside `mapsift/layers/`.
That difference is the first correction below. **Corrected a second time the same day, at the second
pre-dispatch read**, which found the rewrite had dropped the route-reaching point payload the first version
had cited and replaced it with a closed set of three that was wrong in both its membership and its count.)*

**Two arrangers declare a layer, not one**, and both declare `GeometryKind.POINT` and
`StorageClass.ELEMENT`: the shared one in `conftest.py` (lines 106 and 107), and a module-local
`_an_element_layer_of` in `apps/api/tests/test_the_projection_at_the_flush.py` (defined line 118, declaring
at 132 and 133), whose own docstring names both of this task's refusals as the reason it declares what it
does. **The second one already takes `layer_id` and an optional `project_id`**, which is a per-case arranger
in the very suite this task extends.

**No test outside `mapsift/layers/` arranges a served layer or any family other than point.** That grep is
whole and the served-layer conclusion rests on it.

**A `feature.geometry.set` carrying a null payload reaches the route today and is green.**
`_a_geometry_set_stating_there_is_none` (line 193) builds `{"geometry": None}` (line 218) and
`test_the_projection_a_geometry_set_carrying_none_leaves_is_what_that_chain_replays_to` (line 998) posts it
to `OPERATIONS_PATH` at line 1032. It is deliberate: ADR-0012 decision 3's addition of 2026-09-09 makes
saying null and saying nothing different statements, and `TheCurrentStateOfAFeature` carries
`the_batch_spoke_of_its_geometry` to hold the difference.

**The payload that dominates the route is a point, and it is the fact the geometry half actually rests
on.** `a_geometry_set_claiming` in `conftest.py` (defined line 531) carries
`{"type": "Point", "coordinates": [...]}` at line 579, and its `layer_id` defaults to the shared arranger's
point layer. It reaches `OPERATIONS_PATH` from three modules: `mapsift/sync/tests/test_flush.py` (line 111),
`apps/api/tests/test_the_logging_path.py` (line 204), and `apps/api/tests/test_the_projection_at_the_flush.py`
through `_a_geometry_set` (line 181). **So the family check will run on many currently-green cases and pass**,
a point payload against a point layer.

**Two further geometry payloads exist and neither reaches a route:**
`mapsift/sync/tests/test_generated_catalog.py` lines 38 to 40 and `test_generated_envelope.py` lines 41 to
43, **both** carrying `"type": "Polygon"`. Neither module declares `django_db`, calls `.post(`, opens
`tenant_scope` or calls `create_layer`, so both are Pydantic-only and cannot go red from this wiring.
`test_generated_catalog.py` line 107 is `{"payload": {}}` inside a `pytest.raises(ValidationError)`, which
carries no geometry key at all and is not a geometry payload in the sense used here.

**The conclusion this supports, stated per half because the two halves do not rest on the same thing:**

- **Storage class:** nothing outside `mapsift/layers/` arranges a served layer, which is the measurement.
  That no existing case can therefore reach this refusal is the inference drawn from it, not a second
  measurement.
- **Geometry family:** the many route-reaching point payloads pass the check against the point layer they
  address, which is what the green rests on. The **one** case that would not survive a naive reading is the
  null payload above, and it would fail by crashing rather than by refusing, which is why boundary decision
  1 scopes the check to a payload that carries a geometry.

**The conclusion none of it supports, refused in writing:** that the arrangements this task needs are cheap.
Nothing arranges a served layer or a mismatched family today, so both have to be built. Whether the
per-case arranger named above is extended, whether the shared one grows a parameter, or whether each case
creates its own, is **not measured and not decided here**. **Nor is which module the new cases belong in**: the
composition refusals have dedicated modules under `mapsift/sync/tests/` while three of them **also** have
cases in `apps/api/tests/test_authenticated_request.py`, and only the unknown-layer sibling sits in the
projection module. Naming any of them above is description rather than direction. **One constraint on that
file is not description:** ADR-0010 decision 6's additions of 2026-08-11 and 2026-08-13 name two of its
cases and say an implementing window may not edit them.

**One trap handed over, because it cost a review round of MAP-65 and sits directly under this task.** That
task's unknown-layer refusal read its layer set from the **folded** current state rather than from the
operations, and the fold is one row per feature and lawfully lossy, so a batch naming an absent layer on its
first operation and a held layer on its second had the absent one folded away before the check and was
accepted. **The pre-correction shape left the whole suite green**, which is the part that matters here.
`specs/log.md` under 2026-09-09 carries the account, and 2026-09-10 and 2026-09-11 carry the
generalisation. *(Who found it is recorded two ways: `log.md` says the Craft axis, confirmed by the
orchestrator through the route; `session-handoff.md` section 0 says two axes independently. Neither is a
source of truth and the difference does not bear on this task, so it is named rather than resolved here.)*
**The storage-class refusal has that same shape**, since a batch can name a served layer and an element
layer for one feature. **What to do with it is not decided here**, and nothing about where a check reads
from is handed over as an instruction.

**Why this block exists at all:** MAP-65's pre-dispatch read cleared a spec whose every citation was true
while the blocking defect was that no existing flush test arranged a layer. The same class of absence was
looked for here before dispatch, and the read still found this block reporting a grep it had not run.

## Acceptance

**M2**, two clauses of its Acceptance list:

- the served-versus-element clause is taken **whole**. It has no import half: M2's import clauses are
  separate members of the same list and are deferred above, so there is no delta on this one.
- the geometry-family clause is **split**. *(Corrected 2026-09-16 at the MAP-66 review, where this line said
  whole. Two review axes reproduced a polygon stored under a point layer through the route, answering `200`,
  and the orchestrator re-ran it.)* **This task's half:** a geometry an operation carries is refused when it
  is outside the family of the layer that operation addresses, including the multipart and enclave cases the
  clause names. **Not this task's half:** a `feature.create` addressing a feature that already exists moves
  it under another layer while keeping its stored geometry, and no operation in that path carries a geometry,
  so the refusal is never consulted. That path is **MAP-68**'s, whose create semantics decide it.

**M9**, its final Acceptance clause, **split**:

- the typed-refusal half is **whole** and is this task's.
- the **flagged-and-retained** half has no runtime for the word *flagged* in T5.2's sense, since nothing
  marks an operation today. What is provable here is that nothing is discarded, the batch being refused
  whole and rolled back, and that the refused operation is **locatable** by the key ADR-0010 decision 6's
  addition of 2026-09-15 adds. **What is not true here, and is recorded rather than implied:** retention by
  refusing the whole batch stalls every later operation of that installation, so it meets *never discarded*
  and misses I2. The flag and the non-stalling refusal are **MAP-72's**. *(Corrected 2026-09-16: this named
  MAP-37, which carries the flag only for an author who lost authorization.)*

**Nothing here is an acceptance criterion that does not appear upstream.** The `refused_operation_id` key is
a wire contract, decided in ADR-0010 and not invented here.
