# MAP-68 and MAP-74: an operation is judged against the feature it names, and one the log already holds is not decided again

> **Picked up 2026-09-24 on `main` at `db42856`, branch `js/MAP-68-address-verdicts`.** Two issues, one window
> pair, under the batching allowance of `specs/testing.md` section 1.2: both are decided at the same point of the
> flush, before anything is written, against what the server already holds, and MAP-74 is what keeps MAP-68's
> refusals from being walked around (Evidence, P10).

## Trace

**Requirement:** PRD **M9**, the clause its Acceptance gained on 2026-09-24 and the Provenance sentence that
carries its reason and its one accepted exception; PRD **T2.3**, its addition of 2026-08-11 as sharpened on
2026-09-24; PRD **M2**'s geometry-family clause, for the half MAP-66's spec left to this issue; PRD **M15**'s
reproducibility clause, on the split `specs/tasks/MAP-65-projection-at-the-flush.md` records; PRD **N9**'s
Acceptance for the records these decisions leave, except its second-backend clause, which
`specs/tasks/MAP-14-correlation-keys-on-the-flush-path.md` records as deferred with its owner; PRD **T6.5**'s Provenance note of 2026-09-24.

**Invariants and constraints:** **I2**, **I3**, **I9**; **C3**, **C7**, **C12**.

**Code shape:** **ADR-0010 decision 6**, its addition of **2026-09-24** (the two names, the order that picks
one reason, what the batch contributes to what is held, and how a held operation is answered), with its
additions of 2026-09-17 and 2026-09-23 for the body and the refusal set they join; **ADR-0014** decisions 1, 3,
6 and 7, and decision 7's addition of 2026-09-24; **ADR-0012 decision 3**, its additions of 2026-09-09 and
2026-09-11 and its **note of 2026-09-24**; **ADR-0011 section 4** and its note of 2026-09-24 for the record a
held operation leaves; **ADR-0005 sections 3 and 4** for why every read is taken inside the binding;
**ADR-0007 section 3** for where a rule, a read and a write live; **ADR-0004 decision 2** for what runs outside
the critical section. `specs/testing.md` sections 2, 3, 6 and 9.

## What this task owns

The flush judges each operation it has not decided before against the feature that operation names, so no
operation re-files, re-creates or conjures a feature, and an operation the log has already decided is answered
with that decision and is neither judged, projected nor appended again. **Not decided before** is narrower than
the code's `fresh`, which is everything above the cursor and includes a held resend.

## Out of scope

- **The accepted T6.5 exception** (the cross-tenant identifier collision case in PRD M9's Provenance). It is
  accepted, not witnessed: **MAP-75** owns the case that retires it. A case pinning it as correct would be a
  test of a known leak.
- **Two flushes of one installation in flight at once**, where the loser decides before the winner's log holds
  anything (**MAP-76**, a reading nobody has run). The held rule of this task cannot see that case, and no new
  case of this task stages it. **One existing case does**,
  `mapsift/sync/tests/test_the_cursor_under_a_lost_race.py::test_a_flush_that_lost_the_race_does_not_lower_the_cursor_the_winner_already_raised`:
  by reading, its loser decides before the winner commits, so its append meets the winner's entry and survives
  only because the append tolerates the identity conflict. **A held operation not being appended does not
  retire that tolerance**, which is what the race still needs.
- **One operation identifier twice inside one batch** (**MAP-73**), and whether a resend reusing a held
  identifier with **different** content is a violation to be recorded (a reading, on MAP-73 as a comment).
- **What a wire-legal geometry payload is**: **MAP-70**, **MAP-69**, and **MAP-33** for the encoding.
- **Deletion.** The catalog carries `FeatureCreate` and `FeatureGeometrySet` only (`libs/core/src/catalog.rs`),
  so M3's never-reused-after-deletion clause has no runtime, and neither does C7's never-resurrects.
- **Moving a feature as a capability.** No catalog member does it; whether the product needs one is not this
  task's.
- **The per-feature version** (**MAP-38**), **`applied_at`** (**MAP-53**), **the resync read's verdict filter**
  (**MAP-22**), **the author who lost authorization** (**MAP-37**), **the client queue and its optimistic
  preview** (**MAP-15**, **MAP-16**).
- **Where the guard rule lives** (`specs/log.md`, 2026-09-23), which is the owner's.

## Boundary decisions the owner closed

Closed 2026-09-24 at the pickup, on the owner's go over the orchestrator's recommendations, including one
re-ruling the same hour recorded in `specs/log.md` under that date. Each is in the document that owns it and
this is the pointer. **Three sharpenings of the same day came from the pre-dispatch read and are the
orchestrator's, reported to the owner rather than ruled by them:** a second create after a refused one is
admitted; held is keyed by the identifier; a held operation is not appended and takes no per-project version.
All three are in ADR-0010 decision 6's addition.

1. **The two refusals, their names, the order and the batch's contribution**: PRD M9, ADR-0010 decision 6's
   addition of 2026-09-24.
2. **What the tenant holds is read from its current state inside the wall, with one accepted exception**: PRD
   M9's Provenance, T6.5's Provenance, ADR-0012 decision 3's note of 2026-09-24. MAP-75 owns the exception.
3. **A held operation, keyed by its identifier, is answered with the verdict the log holds and is neither
   judged, projected nor appended again**: PRD T2.3, ADR-0010 decision 6's addition, ADR-0014 decision 7's
   addition, ADR-0011 section 4's note.
4. **One window pair for both issues.** This file's alone, under `specs/testing.md` section 1.2.

## Evidence handed over

**Measured 2026-09-24 on `main` at `db42856`, in the container on databases of the orchestrator's own, unless
marked as a reading or a grep.**

**Probes through the route** (`POST /api/operations`), the last flush of each answering `200` with `refused: []` (P11's first flush is the one refusal arranged):

| Probe | Shape | What the projection held afterwards |
|---|---|---|
| P1 | create F on L1 and set, then a set naming F on a second point layer L2 of the same project | F under **L2**, new geometry |
| P2 | create F in project A and set, then a create naming F in project B of the same tenant | F under **B**'s layer, geometry kept, **gone from A** |
| P2b | as P2, the second operation a set | F under B, new geometry, gone from A |
| P5 | one batch: create F on L1, set naming F on L2 | F under **L2** |
| P7 | create F and set, then a second create of F, same layer | F unchanged, the create logged applied |
| P8 | a set naming a feature nothing created | a **new row** for F |
| P6 | Bob creates F in his tenant; Alice, in hers, creates F under Bob's identifier | Alice's create logged **applied**, **no row** for her, Bob's row untouched |
| P9 | create F, set G1 (op B), set G2 (op C), then B resent under a new mutation number | geometry **G1**; the log's chain ends on **G2** |
| P10 | create F on L1 (op A) and set, then A resent under a new number naming L2 | F under **L2**; the log's only entry for A names **L1** |
| P11 | a create refused `no_layer_in_this_project`, that layer created, then the create resent under a new number | a **row** for F; the log's only entry for it says `refused` |

**What the suite already authors against these rules, measured by a non-behavioural instrument over
`sync/services.py`** (read-only mount, own reads hidden from `statements_reaching`, full suite **351 passed**
under it):

- **Two cases arrange a create naming a feature the projection holds**, both in
  `apps/api/tests/test_the_projection_at_the_flush.py`. What each will do under the new rules is a **reading of
  its assertions, not a run**: `test_a_create_for_a_feature_that_already_exists_files_it_under_the_layer_it_names`
  (line 635) asserts the re-filing and inverts; `test_a_create_for_a_feature_that_already_exists_leaves_the_stored_geometry_it_says_nothing_of`
  (line 583) asserts only that the stored geometry is unchanged, and since its second create carries a freshly
  minted operation identifier it will be refused rather than reach the write, so it **stays green while no
  longer exercising the write's rule, which is its subject**. *(Corrected at the pre-dispatch read: the first
  form said both pin the retired behaviour.)*
- **Five cases post a geometry set naming a feature nothing created**:
  `mapsift/sync/tests/test_flush.py::test_a_logged_entry_replays_the_catalogs_other_operation_with_its_payload`
  (line 104), and in `tests/test_the_logging_path.py` lines 207, 260, 378 and 445. The instrument records that
  each authors the shape; **which of them goes red, and on what assertion, was not measured.** The reason they
  exist is a reading: `a_geometry_set_claiming` in `conftest.py` defaults its feature to a fresh identifier.
- **Two cases resend a held operation and must stay green**, both in
  `mapsift/sync/tests/test_dedup_and_the_echoed_cursor.py` (lines 345 and 375). Read: they assert the answer,
  the echo and the log, and assert nothing about records; and **they resend the held identifier carrying a
  freshly minted feature**, because the arranger mints one per call, which is the shape ADR-0010 decision 6's
  keying by identifier answers. The docstring at line 345 names the log's unique key as what meets the resend,
  a mechanism this task moves in front of.
- **Two cases post a refused create and then a create of the same feature, and assert only the first is
  refused** (read): `tests/test_the_projection_at_the_flush.py` line 836 and
  `tests/test_the_layer_declaration_refusals.py` line 370. ADR-0010 decision 6's addition admits the second
  create.

**Readings of the code, not measurements:**

- The projection write sets `project_id` and `layer_id` from the batch unconditionally and filters its update
  on the tenant alone (`mapsift/layers/services.py`, `PROJECT_THE_CURRENT_STATE`).
- `apply_the_flush` projects every operation no refusal names, a held resend included, and the duplicate is
  dropped later, only on the log, by `bulk_create(ignore_conflicts=True)` over the `(tenant, operation_id)`
  constraint (`mapsift/sync/services.py`). The held resend's record is `flush.applied` today.
- `the_reason_an_operation_is_refused_for` judges each operation alone (`mapsift/sync/rules.py`): these two
  reasons are the first that need what the earlier operations of the batch leave (ADR-0014 decision 7).
  `the_current_state_this_batch_leaves` keeps the last address it sees per feature. **What to do with either
  is not decided here.**
- With both rulings in force, **sequential flushes no longer reach the projection's unspoken-column arm**
  (ADR-0012 decision 3's note of 2026-09-24; by reading, the MAP-76 race still could), so the case at line 583 has no route arrangement left for its subject, a
  rule the canon still holds. How it is re-subjected is the window's, under `specs/testing.md` section 2.
- **Docstrings describing as open what this task decides** (grep): four cite MAP-68,
  `tests/test_the_projection_at_the_flush.py` lines 64 and 598, `tests/test_the_per_operation_verdict.py`
  line 56, `tests/test_the_layer_declaration_refusals.py` line 28; and seven more describe an operation on a
  feature no applied operation created as undecided, six of them citing ADR-0014 decision 7 (line 68 of the
  projection module does not):
  `tests/test_the_per_operation_verdict.py` line 534, `mapsift/sync/tests/test_the_reason_an_operation_is_refused_for.py`
  lines 12 and 112, `tests/test_the_projection_at_the_flush.py` lines 68 and 855,
  `tests/test_the_layer_declaration_refusals.py` lines 31 and 383. Line numbers are from `db42856`.

**Harness facts, each paid for once:** `pytest -q` here hides the count line, so run it bare or with
`--tb=short`; a command piped into `tail` reports `tail`'s status; a mutant runs only through a read-only mount
over an existing container path, never by editing the working tree, and a run that needs a database of its own
uses ADR-0002 section 5's literal command; **write everything you create under a scratchpad subdirectory named
for your window**, because the scratchpad is shared by every window this session dispatches (`specs/log.md`,
2026-09-23).

## Acceptance

**PRD M9**, the clause added 2026-09-24, **whole**, with the collision exception its Provenance accepts left
unwitnessed (Out of scope). **ADR-0010 decision 6's addition of 2026-09-24** is contract for the names, the
order and the batch's contribution, and is not a second criterion.

**PRD T2.3**, the addition of 2026-08-11 **as sharpened 2026-09-24, whole**: for a held applied operation and
for a held refused one.

**PRD M2**, the geometry-family clause: **this task closes the half MAP-66 left**, the stored row pairing a
layer and a geometry no single operation carried, across flushes and within one batch, through a create naming
an existing feature.

**PRD M15**, the reproducibility clause, **split as MAP-65 split it**: its legal-weight and attributed
qualifiers have no runtime; **this task's half** is that a resend of a held operation leaves the current state
equal to what the applied log replays to.

**PRD N9**, **for the records these decisions leave**, with every deferral MAP-14's spec records left standing
(the second-backend clause, and the refusals it handed to MAP-48 and to the issues that create them); ADR-0011
section 4's note of 2026-09-24 is what reaches the held operation, including the matching record of a held refusal
listed under `refused`.

**Nothing here is an acceptance criterion that does not appear upstream.**
