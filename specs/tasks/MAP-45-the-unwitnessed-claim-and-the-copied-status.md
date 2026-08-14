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
guarantee PRD M10 states is witnessed on purpose rather than through a side effect, and
`mapsift/sync/rules.py` names no HTTP status.

**The shape was open at pickup and the probe of 2026-08-14 closed it**, so what follows is the owner's call
rather than the window's: the case is **repointed**, not retired and not left as corrected prose. Retiring it
would be the wrong correction, because it is not a case without a requirement, it is a case without a
witness, and those are different things.

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

Three more closed **2026-08-14, after the probe reported**, which is what retired the manual mode this task
was opened in.

4. The case is **repointed** at what M10's clause is actually about, rather than retired or left as prose.
   The reason is in the section above.
5. **One window and no Window B.** No production behaviour changes in this pass, so there is nothing for an
   implementing window to make green, and the separation the two windows buy has nothing to protect here.
   That the repointed case discriminates is proven by a run **the orchestrator** performs against a violating
   implementation, never by a case committed to CI, which is the shape `specs/testing.md` section 4 gives a
   measurement.
6. The round earns a `finding` entry in `specs/log.md`, written 2026-08-14 before this dispatch.

## Evidence handed over

**Rewritten 2026-08-14 after the probe, and the rewrite is the point.** What this block first handed over was
a reading, labelled as one so it could be refuted, and it was refuted: it named the right facts and attributed
them to the wrong layer. What follows is what was measured.

**From MAP-13's post-merge review, 2026-08-13.** An axis built an implementation that answers the refusal
correctly and appends the batch anyway, and `test_a_flush_starting_above_the_cursor_applies_nothing_at_all`
stayed **green**.

**Reproduced by the probe, 2026-08-14, against a `services.py` that appends the batch and then re-raises the
refusal untouched.** The case stays green, and so do its four state-reading siblings. The single case that
goes red is `test_a_refused_flush_takes_no_per_project_version`, whose statement recorder sees the allocation
the append needed even though nothing survived, which is itself the proof that the append ran and was undone.

**The account is one level simpler than the reading this block first carried.** It is not the tenant and user
bindings nesting: the append sits inside an `atomic()` block that the refusal exits by exception, with the
catch outside that block, so the write is discarded whatever the nesting does. Isolated by moving only the
catch inside the binding, which turns one failure into four against the same violating service, while the
identical move against the committed service changes nothing at all.

**No implementation below the route alone can make the case fail.** The one that does is a pair, a route
catching inside the binding plus a writer appending before it refuses, and each half is invisible on its own.
That pair is what the comment at `mapsift/sync/api.py:81` exists to prevent.

**The surviving witness is one by accident.** `OperationLogEntry.project_version` is a plain non-null integer
field, so the counter case catches the append only through the version allocation the append happened to
need, and an implementation sourcing that number elsewhere walks past it.

**What the canon already said, and what it means for this task.** PRD **M10's Shape** records that the
contrast the narrowing draws has no witness and that the clause must not be read as pinned by a case telling
the two forms apart, and `specs/log.md`'s entry of 2026-08-13 says the same in different words. **So the canon
is consistent and only the test docstring is wrong**, which is the opposite of what this task was opened
suspecting. Verified independently by the orchestrator against both documents on 2026-08-14.

**What is still open and belongs to the window:** where exactly the repointed assertion reads, and what it
costs the module to assert over statement text rather than over rows.

## Acceptance

Pasted from the two issues, which pasted from the requirements. No clause here is new.

**MAP-45.**

* the docstring of that case describes only what the case can witness, with no claim about an implementation
  the seam makes unobservable
* the guarantee behind M10's "applies nothing at all" is pinned by a test that fails against an
  implementation violating it, or its untestability is recorded with the reason
* ~~`specs/log.md`'s 2026-08-13 entry agrees with what the suite actually does, since it is the record a
  later reader will cite~~ **Struck 2026-08-14: it does agree.** Verified at the probe and independently by
  the orchestrator against PRD M10's Shape and that entry. Nothing in the canon needed correcting, and the
  round earned a new `finding` entry instead.

**MAP-44.**

* `rules.py` names no HTTP status, in code or in prose
* the docstring still cites ADR-0010 decision 6's addition of 2026-08-13, so a reader reaches the decision
  rather than a paraphrase of it
* nothing about the responses the route answers changes, asserted by the existing suite staying green
