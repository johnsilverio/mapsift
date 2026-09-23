# MAP-66: an operation its layer's declarations reject is refused on its own, kept, and passed

> **Second pickup, 2026-09-23, on `main` at `935f12d`, after MAP-72 merged.** The first pickup (2026-09-14
> to 2026-09-17) built both refusals as whole-batch `409`s on `js/MAP-66-layer-declaration-refusals`, and its
> final review blocked them for stalling an append-only stream against I2. That branch never merged and is
> kept as evidence until this task merges. This file replaces its spec rather than amending it, because the
> shape it assembled no longer exists.

## Trace

**Requirement:** PRD **M2** for the storage-class clause and the geometry-family clause of its Acceptance;
PRD **M9** for the final clause of its Acceptance, which is where a geometry outside its layer's family is
refused, flagged and retained, on that operation alone.

**Invariants and constraints:** **I1**, **I2**, **I9**; **C1**, **C7**, **C12**.

**Code shape:** **ADR-0014** decisions 1, 2, 3, 5, 6, 7 and 8, which are the mechanism these two reasons join
and are not restated here; **ADR-0010 decision 6**, its addition of 2026-09-17 for the success body and the
refusal set's home, and its addition of **2026-09-23** for the two names, the order that picks one reason,
and the scope of the family check; **ADR-0005 sections 3 and 4** for why the declarations are read inside the
binding; **ADR-0007 section 3** for where a pure rule, a read and a write each live; **ADR-0012 decision 3**
for the projection the refusals stand in front of; **ADR-0011 section 4** with ADR-0014 decision 8 for the
record. `specs/testing.md` sections 2, 3, 6 and 9.

**Named as the reason this is reachable at all and not as this task's requirement:** MAP-65, which made the
projection write; MAP-64, which published `create_layer`; MAP-72, which made a refusal a verdict on one
operation.

## What this task owns

The two decisions a layer's declarations make about its features get a caller on the flush path, so an
operation naming a served layer, or carrying a geometry outside the family its layer declares, receives its
own refusal and never becomes current state, while the operations around it apply.

## Out of scope

- **The client's queue.** PRD T1.2 makes the operation queue local and `libs/core` has none, so what a client
  does with a refused entry and its optimistic preview is **MAP-15** and **MAP-16**'s; ADR-0014's
  Consequences name the preview, not the entry, as an I2 obligation.
- **The element budget and the import classification**, M2's other Acceptance clauses. Nothing imports, and
  the budget is a PRD 10.5 measurement downstream of running code.
- **A feature changing path.** Its promotion half is **OQ-6**, which M2's Open/ADR scopes to where a promoted
  analysis result lives. Its layer-changing-class half is **M2 Acceptance clause 4**, a requirement rather
  than an open question, out of scope because nothing changes a layer's class today.
- **What a valid geometry payload is on the wire.** **MAP-70** owns the six shapes that answer `500`, four
  in its first table and two added 2026-09-17,
  **MAP-69** the relabelled frame, and **MAP-33** the encoding both feed, including the recorded difference
  between how the family check and the writer read `type`. The payloads this check does not read are fixed
  by ADR-0010 decision 6's addition of 2026-09-23.
- **A create addressing a feature that already exists.** **MAP-68**. It re-files the feature under the layer
  it names and keeps the stored geometry, so a geometry of one family can end up under a layer that declares
  another with no single operation carrying the pair.
- **The per-feature version** (**MAP-38**), **the applied-at column** (**MAP-53**, born nullable under
  ADR-0014 decision 3), **the resync read's verdict filter** (**MAP-22**), and **an author who lost
  authorization** (**MAP-37**, T5.2).
- **Who may create or classify a layer.** The permission model, deferred by the Open/ADR of **T6.3 and
  T6.4**, and the licence tiers **T6.2** rests on, which are foundation **OQ-7**.

## Boundary decisions the owner closed

Closed 2026-09-23 at the second pickup, on the owner's go over the orchestrator's recommendations.
Decisions 1, 3 and 4 are recorded in the documents that own them (`specs/log.md` under 2026-09-23 and
ADR-0010 decision 6's addition of that date) and this is the pointer. **Decisions 2 and 5 are this task's
alone and this file is their home**, because neither binds anything past this task.

1. **A fresh branch from `main`**, `js/MAP-66-layer-declaration-verdicts`. The first branch is not rebased:
   its production code implements the retired shape, and six of its files conflict with `main` (measured
   below). It is deleted when this task merges.
2. **The first round's test module is evidence for Window A and its implementation is not handed to Window
   B.** The cases were written by a previous Window A and killed all thirteen mutants at review, so their
   arrangements are worth reading; which of them survive, and under what name, is Window A's under
   `specs/testing.md` section 2's rule on a case whose contract moved. The implementation carries the retired
   shape and would be a contract Window B could copy instead of satisfy.
3. **The names, the order that picks one reason, and the scope of the family check** are ADR-0010 decision
   6's addition of 2026-09-23.
4. **The first round's `refused_operation_id` key is not adopted.** Same addition, last paragraph but one.
5. **`no_layer_in_this_project` and the cases that witness it stay as they are.** Those cases sit in three
   modules, not one: the MAP-72 module named under Evidence, `mapsift/sync/tests/test_the_flush_decision_trail.py`
   for the `flush.refused` record, and `tests/test_the_projection_at_the_flush.py`, which asserts the reason
   at lines 780, 828, 894 and 1207 (grep). How the declarations are
   read is the window's, under ADR-0007 section 3, which fixes that a read lives in `selectors.py` and fixes
   nothing about how many reads there are.

## Evidence handed over

**Measured 2026-09-23 on `main` at `935f12d`, in the container unless marked as a grep or a reading.**

**The suite is green at 327 Python cases**: `pytest --tb=short` in the `api` service, `327 passed`, exit 0,
working tree clean afterwards.

**Two arrangers declare a layer outside `mapsift/layers/`, and both declare `GeometryKind.POINT` and
`StorageClass.ELEMENT`** (grep): the shared one in `conftest.py` (lines 106 and 107), and the module-local
`_an_element_layer_of` in `apps/api/tests/test_the_projection_at_the_flush.py` (defined line 136, declaring at
150 and 151), which takes `layer_id` and an optional `project_id`. **No test outside `mapsift/layers/`
arranges a served layer or any family other than point**, and that grep is whole.

**A `feature.geometry.set` whose payload's geometry is null reaches the route and is green, as a run:**
`test_the_projection_a_geometry_set_carrying_none_leaves_is_what_that_chain_replays_to` (line 1089 of the
projection module), `1 passed`. Its payload is built by `_a_geometry_set_stating_there_is_none` (line 211,
`{"geometry": None}` at line 236).

**The payload that dominates the route is a point** (grep): `a_geometry_set_claiming` in `conftest.py` (line
531, `{"type": "Point", ...}` at 579) addresses the shared point layer by default. So the family check will
run on many green cases and pass. **The only other geometry payloads outside `mapsift/layers/` are two
`"type": "Polygon"` literals**, in `mapsift/sync/tests/test_generated_catalog.py` (line 40) and
`test_generated_envelope.py` (line 43); neither module declares `django_db`, posts, opens `tenant_scope` or
calls `create_layer` (grep), so neither reaches the route.

**MAP-72's module is where the verdict is witnessed today**, `apps/api/tests/test_the_per_operation_verdict.py`,
thirteen cases (grep), twelve of which arrange their refusal through a layer the project lacks and one of
which refuses nothing. **Which module the new cases
belong in is not decided here.**

**The refusal set needs no migration to grow**, as a reading of `mapsift/sync/models.py`: `refusal_reason`
is a `CharField(max_length=64, null=True)` with no choices, and its one check constraint,
`a_reason_exactly_where_the_verdict_refuses`, pairs the reason's presence with the verdict and reads no value.
**Nothing outside `mapsift/sync/rules.py` enumerates `WhyAnOperationWasRefused`**, no test and no migration
(grep).

**The first branch, `js/MAP-66-layer-declaration-refusals` at `622774d`**, forks from `85ed416`, carries
thirteen commits, and conflicts with `main` in six files (`git merge-tree`): `sync/rules.py`,
`sync/services.py`, `tests/test_the_projection_at_the_flush.py`, ADR-0010, `index.md` and `log.md`. Its test
module is `apps/api/tests/test_the_layer_declaration_refusals.py`, 877 lines, eleven cases, read with
`git show js/MAP-66-layer-declaration-refusals:<path>`. **The retired shape reaches most of it**, by grep
at `622774d`: `HTTPStatus.CONFLICT` is asserted in nine of the eleven cases, every one but the multipart case
(line 775) and the enclave case (line 826); `refused_operation_id` is a constant at line 81, asserted at lines
270, 457 and 543, and named by no case; and one case is named for a refused batch applying nothing at all
(line 601). That is a grep of assertions and not a verdict on each case.

**What that branch's final review found and recorded in MAP-66's Linear issue, handed over because three of
them are about this exact wiring:** the served-layer check walked every layer in the mapping it was handed
rather than the layers the batch names, correct only because its one caller passed exactly those (measured
then); the three payload shapes the family check skips were skipped and pinned by no case; and the refusal's read
and the projection's write each decided separately what geometry an operation carries, in two `match`
blocks, which two review rounds disagreed on as one decision or two.

**None of the three skipped payload shapes can be shown applied through the route today**, as MAP-70's
measurements rather than this pickup's (Linear MAP-70, 2026-09-11 and 2026-09-17, not re-measured here):
`{}`, a non-string `type` and a geometry that is not a mapping each answer `500` where the writer parses
them. **Two shapes inside the point family by their declared `type` answer `500` as well**, a
three-dimensional point and a `Point` with no coordinates. So the route cannot carry a case on a skipped
shape, nor a stored-inside-the-family case built on either of those two; where such a case lives instead is
the window's.

**One trap from MAP-65, still live under this task:** a guard fed from the folded current state rather than
from the operations inherits every loss of the fold, and the pre-correction shape left the whole suite
green. `the_layers_this_batch_addresses` in `sync/rules.py` says why it reads the operations. A batch can name
a served layer and an element layer for one feature, and carry two geometries for one feature; the fold keeps
one of each. **What to do with it is not decided here.**

**Three harness facts, each paid for once:** `pytest -q` here is effectively `-qq` and hides the count line,
so run it bare or with `--tb=short`; a command piped into `tail` reports `tail`'s status; and a mutant runs
only through a read-only mount over the container path (`-v <scratch>/<file>:/app/<path>:ro`), never by
editing the working tree.

## Acceptance

**M2**, two clauses of its Acceptance list, **both split**:

- **The served-versus-element clause.** Its subject is the operation queue, which PRD T1.2 makes the client's
  local queue, so its client half has no runtime until MAP-15 and MAP-19. **This task's half:** on the
  server, an operation naming a served layer is refused as its own verdict and never becomes current state.
  **The first round's reading is retired and why:** it made this half "the server's log never holds an
  operation naming a served layer", and ADR-0014 decision 3 now keeps every refused operation on that log
  with its verdict, which M15's Shape (added 2026-09-17) states for any refused operation.
- **The geometry-family clause.** **This task's half:** a geometry an operation carries is stored when it is
  inside the family of the layer that operation addresses, multipart and enclave cases included, and refused
  as that operation's verdict when it is outside it. **Not this task's half:** the stored row can pair a layer
  and a geometry no single operation carried, across flushes and within one batch, through a create
  addressing a feature that already exists (MAP-68).

**M9**, its final clause, **whole**. The *flagged* of that clause is the verdict `refused`, reconciled by
ADR-0014 decision 4, and not a second marker. This task adds a reason to a mechanism MAP-72 built; it does
not rebuild the mechanism.

**Nothing here is an acceptance criterion that does not appear upstream.** The names, the order and the
scope are wire contract, decided in ADR-0010 decision 6 and not invented here.
