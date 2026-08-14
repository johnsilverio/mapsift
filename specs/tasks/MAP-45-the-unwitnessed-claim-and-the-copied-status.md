# MAP-45 with MAP-44: the suite claims only what it can witness, and the pure module names no wire status

> Two corrections over one package, both residue of MAP-13's post-merge review of 2026-08-13. They run as
> **one pass** by the owner's call of 2026-08-14, whose record is MAP-45's pickup comment.

## Trace

**MAP-45.** `specs/testing.md` sections 2, 6 and 9. PRD **M10**'s acceptance as narrowed 2026-08-13, and
**C12**. `mapsift/sync/api.py` carries its own account of why its `catch` sits outside the binding, and that
account is one of the two things this task weighs.

**MAP-44.** **ADR-0007 section 3** for what `rules.py` may contain. **ADR-0010 decision 6's addition of
2026-08-13** for the status and the closed refusal object. `CLAUDE.md`'s comment discipline for why a value
sitting beside a correct citation is the defect rather than the citation.

Both Linear issues carry the full trace and the acceptance, pasted from the requirements at creation.

## What this task owns

`test_a_flush_starting_above_the_cursor_applies_nothing_at_all` claims only what it can witness, the
guarantee it was written to protect is under a test that can fail or its untestability is recorded with the
reason, and `mapsift/sync/rules.py` names no HTTP status.

**Three outcomes are all acceptable for the first half and the choice belongs to whoever does the work:** a
case that can fail against a violating implementation, a corrected docstring over a case kept for a narrower
reason, or the case retired with the guarantee moved somewhere that can hold it. What is not acceptable is a
docstring that keeps a claim the seam makes unobservable.

## Out of scope

- **The behaviour of the flush.** No status, no response body and no refusal changes. What the route answers
  is a wire contract and it moves through ADR-0010 decision 6, never through a correction pass.
- **M10's acceptance itself.** If the narrowed clause turns out to be unwitnessable from the route, that is a
  finding to record, never a licence to widen it back. Reopening it is a fan-out through the PRD.
- **The rest of MAP-13's post-merge review.** Per `session-handoff.md` section 0 it returned eight advisory
  items and named two as worth acting on. This pass is those two, and it does not revisit the judgement on
  the other six.
- **MAP-14**, the next task in the milestone. It shares this package and starts after this pass merges.

## Boundary decisions the owner closed

All three closed 2026-08-14 and registered before this file was written. **MAP-45's pickup comment is the
record and this is the pointer.**

1. MAP-44 and MAP-45 run as one pass and one pull request closing both, bending
   `linear-workflow`'s one-issue-one-pull-request rule knowingly, under the batching allowance of
   `specs/testing.md` section 1.2.
2. This task runs in the **manual dispatch mode** of ADR-0008 section 4, on the condition that section names.
3. A wrong `specs/log.md` entry is corrected in place with a dated note, never deleted and never appended
   over. Registered in that file's own header the same day.

## Evidence handed over

Two facts. **The conclusion they suggest is deliberately not handed over**, which is the correction MAP-13's
own spec earned at its review.

**From MAP-13's post-merge review, 2026-08-13.** An axis built an implementation that answers the refusal
correctly and appends the batch anyway, and `test_a_flush_starting_above_the_cursor_applies_nothing_at_all`
stayed **green**.

**Read from disk by the orchestrator, 2026-08-14, and it is a reading rather than a run.** `tenant_scope`
opens `transaction.atomic()` itself at `mapsift/common/binding.py:51`, nested inside the one `user_scope`
opens at line 84, and `flush_operations` catches `ThisStreamCannotBeContinued` outside the tenant binding.
Whether that fully accounts for the observation above is precisely what this task settles, and the source is
named so it can be refuted rather than believed.

**What is not handed over, each because it is a conclusion this task exists to reach:** that the case is
worthless, that it should be deleted, or that `specs/log.md`'s entry of 2026-08-13 is wrong.

## Acceptance

Pasted from the two issues, which pasted from the requirements. No clause here is new.

**MAP-45.**

* the docstring of that case describes only what the case can witness, with no claim about an implementation
  the seam makes unobservable
* the guarantee behind M10's "applies nothing at all" is pinned by a test that fails against an
  implementation violating it, or its untestability is recorded with the reason
* `specs/log.md`'s 2026-08-13 entry agrees with what the suite actually does, since it is the record a later
  reader will cite

**MAP-44.**

* `rules.py` names no HTTP status, in code or in prose
* the docstring still cites ADR-0010 decision 6's addition of 2026-08-13, so a reader reaches the decision
  rather than a paraphrase of it
* nothing about the responses the route answers changes, asserted by the existing suite staying green
