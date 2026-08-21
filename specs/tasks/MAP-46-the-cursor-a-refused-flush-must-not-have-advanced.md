# MAP-46: the cursor a refused flush must not have advanced, witnessed rather than assumed

## Trace

PRD **M10**'s Acceptance as narrowed 2026-08-13, the clause that a flush with a gap above the cursor
"applies nothing at all". PRD **M4** for the per-installation cursor and what its absence means.
**C12** and foundation **I9**. **ADR-0004** decision 2 with its extension of 2026-08-11, which places
the cursor write and carries the backwards guard. **ADR-0010** decision 6 with its addition of
2026-08-13 for the refusal's status, its closed object and its two reasons. **ADR-0007** section 6 for
where a shared fixture lives. `specs/testing.md` section 2 for what a case may assert.

## What this task owns

A refused flush is witnessed to have left this installation's cursor where it was, **by a witness that can
itself be shown to fail**.

**Two rounds have landed and both stand.** In the working tree, uncommitted: `the_writes_among` and
`THE_VERB_THAT_READS` in `apps/api/conftest.py`,
`test_a_refused_flush_leaves_this_installations_cursor_where_it_was` in `test_the_typed_resend_on_a_gap.py`,
and `test_an_applied_flush_writes_this_installations_cursor` in `test_dedup_and_the_echoed_cursor.py`. Six
axis reports drove them, the suite is 248 green, and each of the three mutants produces exactly one red.
**The third round changes no name, no assertion, no arrange and no body: it is boundary decision 5 and
nothing else.** **Every imperative in decisions 2, 3 and 4 below is spent and addressed to a window that has
already run**, "measure before building it", "whether it is needed at all", "where that case lands is this
window's" and "decide it and say why" among them. They are recorded so the round can be audited, and none of
them is an instruction to this one.

## Out of scope

- **The implementation.** The guard exists on `main` and this task adds no production behaviour. If a
  case here is red against unmutated `main`, that is a finding reported back, never a licence to edit
  `mapsift/sync/services.py`.
- **The mutant run that defines red.** It is the orchestrator's, on the MAP-43 shape, and never a case
  committed to CI.
- **The cursor's expiry, collection and rehandshake** (MAP-42).
- **The backwards guard under a concurrent race**, which MAP-43 already witnesses and which is a
  different question from this one.
- **Every client half of this axis**: minting the clientID, persisting the queue, advancing from the
  echo, reacting to either refusal (MAP-15, MAP-17, MAP-19).
- **The per-project version a refused flush must not take**, already witnessed in this module.

## Boundary decisions the owner closed

All five on 2026-08-20 and this block is the pointer rather than the record. The first three are on the
MAP-46 pickup comment and in the `decision` entry of `specs/log.md` under that date; **the fourth is in that
day's `finding` entry only**, because it was closed after the first review round rather than at pickup, and
the round it authorized is a correction round.

1. **One window and no Window B**, on the precedent MAP-43's spec states, because the guard already
   exists and the case is born green.
2. **A case of its own** rather than an added assertion on
   `test_the_resend_a_refusal_asked_for_lands_whole_rather_than_being_deduplicated_away`, under
   `specs/testing.md` section 2. **Read the docstring of
   `test_a_flush_starting_above_the_cursor_applies_nothing_at_all` before arranging this one**: it records,
   measured, why the refusal is arranged through the helper that pins its reason and why the status alone
   would not do.
3. **`apps/api/conftest.py` is permitted to gain a sibling instrument, and is not required to.** What the
   owner sanctioned is that one **may** exist; whether it is needed at all, and its spelling and its shape,
   are this window's, in that order. Measure before building it. It needs no ADR, because ADR-0007 section 6
   already decides where a shared fixture lives.
4. **A new instrument carries a positive control, as a case of its own, and the assertion is `!= []`
   rather than `== 1`.** A witness nothing can make fail is not one, and the Evidence below carries the
   measurement that this one could not. The write being a single statement is ADR-0004 decision 2's property
   and therefore a second behaviour, which decision 2 above already refused to fold into one case. **Where
   that case lands is this window's and is a real question rather than a default:** its subject is an
   accepted flush, while its purpose is arming an instrument a refusal case reads, and those two pull toward
   different modules. Decide it and say why.

5. **A docstring accuracy pass closes the round, and it touches nothing executable.** Closed 2026-08-20
   after the re-review, recorded in that day's last `finding` entry in `specs/log.md`. In scope: the three
   claims that are false as written, the shared filter's docstring carrying one caller's path measurement,
   the one-way pointer between the two cases, and **the one false reference to this issue**, which is
   `test_the_typed_resend_on_a_gap.py`'s "Putting that property back under test is MAP-46"; `grep -rn
   "MAP-46" apps/ libs/` returns four, and the other three are scope pointers naming the owning issue that
   are still true, which the house style updates to name where the thing landed. Out of scope by name: the ordering of `specs/index.md`'s task block, deferred with its reason
   in the same entry, and any rename, assertion, arrange or body anywhere.

## Evidence handed over

**A measurement, 2026-08-14 at the MAP-45 review, by the Canon axis and independently by the
orchestrator.** Against a `mapsift/sync/services.py` whose `apply_the_flush` advances the cursor
**before** the refusal, **all six cases in `test_the_typed_resend_on_a_gap.py` stay green.** The
mechanism is the one MAP-45's probe established for the append: the write sits inside the `atomic()`
block `tenant_scope` opens and the refusal exits that block by exception, so nothing survives for a
later read to find. **State after the fact is blind to any mutation a refusal unwinds.**

**A reading taken at pickup 2026-08-20 and measured the same day**, by Window A and independently by all
three review axes, which drove the real route and reached the same pair: a refused flush leaves one SELECT
naming the cursor's table, an accepted one leaves that SELECT and the upsert. `statements_reaching` matches
every statement whose text names the table, reads included. `the_cursor_of`
(`mapsift/sync/selectors.py`) issues an ORM read of `ClientCursor`, and `apply_the_flush` calls it
before the refusal, because reading the cursor is how the gap is detected. The log's table carries no
such read on that path.

**The conclusion was refused in writing and the first round reached it**, which is recorded here because
the refusal is why the instrument was measured into existence rather than assumed: MAP-45's
`assert seen == []` cannot be repointed at the cursor's table, and what replaced it was chosen after the
measurement above, not before. Nothing in this paragraph asks this round to redo that.

**A measurement, 2026-08-20, taken at the first review round by the Craft axis and reproduced by the
orchestrator.** With the sibling instrument's body replaced by `return []` through a scratch `conftest.py`
mounted read-only over the container path, **the whole suite stayed green at 247 passed against a correct
server, and against the cursor-advance mutant the module stayed green too at 7 passed.** The witness added
by the first round could therefore be silenced without anything noticing, which is the defect this issue
exists to close, reproduced one layer down. This is what boundary decision 4 answers.

**A trap, 2026-08-20, that cost three runs at MAP-39's Window B.** `pytest -q` in this repository is
effectively `-qq`, because `apps/api/pyproject.toml`'s `addopts` already carries `-q`. `pytest --tb=no
-q` reports failures and never says how many passed, which reads as a truncated run. Run `pytest` bare,
or with `--tb=short`, to get the count line.

## Acceptance

**The delta against M10, whose Acceptance is law and is read there.**

- The clause this task serves is M10's **"applies nothing at all"**, already witnessed for one of the two
  writes a broken server could make before refusing (the append, by
  `test_a_flush_starting_above_the_cursor_applies_nothing_at_all`). This task witnesses the **second**, the
  cursor. No new criterion is introduced and none is needed.
- **Against a correct server nothing is written and nothing is rolled back**, and that is the difficulty
  rather than a detail: the rollback is what a broken server hides behind, which is why a case reading state
  after the fact sees neither write.
- **The flush path writes three tables from two hoistable sites**, which is why the count above and the Out
  of scope block do not disagree. `apply_the_flush` calls the cursor advance and then the append, and the
  version allocation lives **inside** `append_to_the_operation_log` rather than beside it, so a broken server
  hoisting the append hoists both and the version counter is not a third site of its own. It carries a case
  of its own regardless, and a refused batch never reaches the allocation at all (ADR-0004 decision 2, and the header of
  `test_the_typed_resend_on_a_gap.py` states it).
- **The positive control asserts a behaviour that is already true and already covered indirectly**, by the
  dedup this suite witnesses elsewhere, so it introduces no criterion and pins no new product guarantee. Its
  purpose is to arm the instrument the refusal case reads, and it is listed here so it is not mistaken for
  one.
- **The issue's Acceptance carries two bullets and only the narrowed one is this task's.** The first is copied
  from C12's test clause, two of its three cases, and its interrupt-and-resend half is witnessed elsewhere
  in this suite (ADR-0008 section 9, Acceptance is the delta).
- **The issue's own narrowed bullet is a statement about the suite, not a product criterion**, and is
  read as the exit condition rather than as the requirement. The requirement is M10's clause above.
- **The exit is a mutant run the orchestrator performs**: with the advance moved ahead of the refusal
  the new case fails, and against unmutated `main` the whole module passes. A case that cannot be made
  to fail that way has not met this issue, whatever it asserts.

## What a review fails this file for

Everything the block of that name in `specs/tasks/README.md` fails a spec for, and one specific to this
task: **a case** that pins how many times the flush reads the cursor, or that carries in its own body the
knowledge of how a write is spelled, in place of asserting the behaviour. A shared instrument in
`apps/api/conftest.py` is the sanctioned home for that knowledge and is not what this line refuses.
