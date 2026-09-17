# MAP-72: a refused operation is decided alone, kept, and passed by the cursor

## Trace

**Requirements:** PRD **T5.2** (its Acceptance carries the addition of 2026-09-17), **M9**'s final Acceptance
clause, **M10** (the contiguity rule and the dedup clause), **M4** and **T2.3** (the cursor and its echo),
**M15** (what the log holds and what the projection is), **M8** (the envelope's verdict field), **M13** (whose
three verdict members are not this task's), **N9** (the record).

**Invariants and constraints:** **I2**, **I9**, **I10**; **C7**, **C12**, **C13**.

**ADR sections:** **ADR-0014** in full, which is this task's mechanism; **ADR-0010 decision 6**, addition of
2026-09-17 for the wire, and the additions of 2026-08-13 and 2026-09-08 for what it changes; **ADR-0004**
decision 2 and decision 4 with its amendment of 2026-09-17; **ADR-0011 section 4** with its addition of
2026-09-17; **ADR-0012 decision 3** with its narrowing of 2026-09-17 and decision 5 with its amendment of the
same day; **ADR-0005 sections 3 and 4** for why a read happens inside the binding.

**Foundation:** section 4's v0.7 and v0.8 decisions with the revision of 2026-09-17 (v0.19).

## What this task owns

The flush decides each operation of a batch rather than the batch: it applies what it can, records what it
refuses, and answers with one cursor plus the refusals, so a stream is never stalled behind an operation the
server will refuse every time.

The one refusal with a runtime today is the unknown layer, which is why it is the one this task converts.

## Out of scope

- **The two layer-declaration refusals.** **MAP-66**, parked on its own branch; ADR-0014 decision 2 names
  both as operation verdicts for when that task resumes, and ADR-0014's Consequences name its cases that
  assert a refused batch applies nothing at all as that task's rework. **Their pure predicates are on this branch with no production
  caller** (`layers/rules.py`, exercised by their own unit tests and by nothing on the flush path), and they
  stay that way here: wiring either is MAP-66's work, not a loose end.
- **The author who lost authorization.** **MAP-37**. T5.2's other half has no runtime here: nothing in
  `apps/api` validates a per-project write permission, because the permission model PRD 10.6 defers is not
  built.
- **The client's side of all of it**: the local queue, the optimistic preview a refusal must not leave
  standing, and the resolution surface. **MAP-15**, **MAP-16** and T5.2's open `Open / ADR`.
- **The resync read that must filter on the verdict.** **MAP-22**, per ADR-0004 decision 4's amendment.
- **The per-feature version, the applied rule version and the legal weight in force.** MAP-38 owns the first
  and OQ-8 the third; **the applied rule version has no owner in the canon**, which ADR-0004 decision 4's
  addition of 2026-08-10 states as work nobody has decided. ADR-0014 decision 3 says explicitly that it
  decides nothing about any of the three.
- **The log's `applied_at` column, and therefore the nullability paired to the verdict.** **MAP-53**, still in
  Backlog: measured on this branch, `OperationLogEntry` carries no timestamp field and no migration adds one,
  so there is nothing here to make nullable. ADR-0012 decision 5's amendment binds MAP-53 when it lands the
  column; this task neither creates it nor works around its absence.
- **What a wire-legal geometry payload is**, and **what a create addressing an existing feature means**.
  **MAP-70** and **MAP-68**.
- **The two cursor reasons' `409` behaviour**, which keeps its shape, its status and its restart point.
  Taking the third reason out of that set is boundary decision 5 and **is** this task's work; what is out of
  scope is changing anything about a gap or an absent cursor.

## Boundary decisions the owner closed

All on **2026-09-17**, each written into the document that owns it before this file existed, with one
exception recorded rather than smoothed: decision 7's **timing** half reached ADR-0011 section 4 after this
file was first committed, at the pre-dispatch read. The decision itself is ADR-0014 decision 8 and predates
it.

1. The cursor counts what the server **decided** and the echoed key is renamed with it: foundation v0.19,
   ADR-0014 decision 5.
2. The criterion separating a whole-batch refusal from an operation verdict: ADR-0014 decision 1.
3. The verdict is a `refused` member of the envelope's closed set, spelled apart from M13's
   `flag and preserve both`: ADR-0014 decision 4, and PRD M8's Shape and M13's Requirement carry the note.
4. The refused operation is retained on the append-only log with its verdict and reason: ADR-0014 decision 3.
   Its `applied_at` half binds **the column MAP-53 has not landed yet** and therefore has no runtime in this
   task (see Out of scope): ADR-0012 decision 5's amendment.
5. `no_layer_in_this_project` leaves the `409` set, which returns to two members: ADR-0010 decision 6's
   addition of 2026-09-17.
6. The response stays `200` and grows the refusal list: the same addition.
7. `flush.refused`, one record per operation, emitted after the commit, and a refused operation appearing in
   no other record of that flush: ADR-0011 section 4's addition and ADR-0014 decision 8.

## Evidence handed over

**The surface the fan-out sweep found, measured 2026-09-17** with
`grep -rn "last_applied\|last-applied" specs/ CLAUDE.md README.md .claude/ apps/ libs/`. The old cursor
spelling reaches `mapsift/sync/` in `models.py`, `api.py`, `services.py`, `rules.py`, `selectors.py` and the
migration that created the cursor table, and it is fixed as a **constant** in two test modules,
`test_dedup_and_the_echoed_cursor.py` and `test_the_typed_resend_on_a_gap.py`, plus three occurrences across two
docstrings in `test_the_cursor_under_a_lost_race.py`, the module's and one case's. **This is a measurement of where the word
appears and not a conclusion about which of those the task must change**, which is the window's to decide
against ADR-0014.

**The rustdoc on `Verdict` in `libs/core/src/envelope.rs` names M13 as the sole declarant of the set**
(read 2026-09-17). PRD M8's Shape and ADR-0014 decision 4 now give it two. The correction is authorised and
is implementation rather than canon.

**A reading, labelled as one.** `ServerHalf` declares `applied_at`, `feature_version`,
`applied_rule_version`, `project_version`, `legal_weight_in_force` and `verdict`, **all six non-optional**;
`AppliedOperation` is the separate struct holding a client half beside a server half.
ADR-0012 decision 5's amendment is about the **log column** and not about either struct, and ADR-0014
decision 3 answers the struct question directly. **This paragraph hands over what is on disk and settles
nothing**, which is deliberate: the envelope is touched in this task for the verdict member of boundary
decision 3, and what else it needs is read from ADR-0014 rather than inferred from here.

**The trap that has cost three runs.** `pytest -q` in this repository is effectively `-qq` and suppresses the
final count, because `apps/api/pyproject.toml`'s `addopts` already carries `-q`. Run `pytest` bare or with
`--tb=short`.

**A gate run with the stack down reports roughly 240 errors that read as a broken suite**, every one of them
`failed to resolve host 'db'`, because `just check` passes `--no-deps`. The remedy is `just up` and a re-run
(2026-09-14, `specs/log.md`).

**What an absence assertion costs here, measured across MAP-45 and MAP-46 and repeated because it decides test
design.** State read **after** a refusal is blind to anything the refusal unwinds: the cursor write and the
log append both sit inside the `atomic()` block `tenant_scope` opens, and the refusal is caught outside it, so
a later read sees nothing either way. What separates the two is recording the statements as they run, and
the lesson is what MAP-45 and MAP-46 established; **the instrument predates them**, `statements_reaching`
having reached `conftest.py` at MAP-12 (`63e9522`), with MAP-46 adding the write filter beside it.

## Acceptance

**The delta only.** The criteria are law in the PRD and in the ADR sections the Trace names, ADR-0011 section 4 included, and the window reads them there.

- **T5.2's Acceptance is split, and only its second half has a runtime here.** The authorization half needs a
  permission model that does not exist (see Out of scope), so this task delivers the clause added on
  2026-09-17, that the operations after a flagged one still reach the server, and delivers it against the
  refusal that does exist. The first half is MAP-37's and is not weakened, deferred or restated.
- **M9's final Acceptance clause has no runtime on this branch at all**, the predicate that would decide it
  being present and uncalled (see Out of scope). Its refusal lives on MAP-66's parked
  branch. This task must not implement it in order to test it.
- **M10's Acceptance is read with ADR-0014 decision 5, not against it.** Its applies-nothing-at-all clause is
  about a **gap**, which stays a whole-batch `409`; the per-operation verdict does not touch it, and a case
  proving the gap still refuses the whole batch is what keeps the two apart.
- **The projection clause is a narrowing of an existing green behaviour, not a new one.** ADR-0012 decision 3's
  fold is already tested; what changes is which operations it walks.
- **Six cases on this branch pin the retired whole-batch refusal and are this task's rework** (found at
  Window A's review, 2026-09-17, and named here because the first form of this file named only MAP-66's
  parked cases). Five of them are in `apps/api/tests/test_the_projection_at_the_flush.py` and one in
  `mapsift/sync/tests/test_the_flush_decision_trail.py`; each was green when this task started and each
  becomes false under ADR-0014. The rule that decides each is **`specs/testing.md` section 2**, where it was
  written on 2026-09-17 rather than here, because it is general. Reworking them is the test author's, which is
  why they are named here and not in Window B's brief: Window B may not edit a test.
