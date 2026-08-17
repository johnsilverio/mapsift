---
allowed-tools: Bash(cat *), Bash(ls *), Bash(tail *)
name: fan-out
description: Propagate a closed decision to every document it touches, in one pass, so the canon cannot contradict itself. Use this whenever a decision is taken, changed, reopened or refused, whenever a requirement or an invariant moves, and whenever a session is about to end with something decided in chat that is not yet written down. Use it even when the change feels small, because a decision recorded in one document and not the others is exactly how a contradiction is born. Triggers on "/fan-out", "propagate this decision", "update the docs for this", "we decided X", "record this in the canon".
---

# Fan out a decision

**A closed decision is not closed until it has been propagated.** Recording it in one document and
planning to update the rest later is how this canon acquires a contradiction, and every contradiction
found here so far was born exactly that way.

Run this in the main session, not in a subagent: the output is edits to the tree that the owner reviews as
a diff, and there is nothing to isolate.

## The document map, injected because you cannot propagate to files you do not know exist

This is `specs/index.md`, loaded from disk. It is the catalog of every document and every identifier
namespace, and it is what makes the target table below resolvable.

!`cat specs/index.md`

## The tail of the log, so your entry matches the format and the order

!`tail -3 specs/log.md`

---

## 1. Establish what actually changed

State it in one sentence before touching a file. **A decision, an amendment and a correction are three
different things and they propagate differently.**

| Kind | What it is | What it triggers |
| --- | --- | --- |
| **Decision** | something that was open is now closed, or something closed has been reopened and re-decided | the full fan-out below, and a version bump on the owning document |
| **Amendment** | a higher document changed and a lower one must follow | the targets the change reaches, plus a revision entry in each ADR touched |
| **Correction** | a document says something untrue and no decision moved | fix it, log one line, **do not** bump a version. A correction dressed as a round produces a revision nobody reviews |

If it is a **refusal**, it still propagates. A refusal written nowhere is proposed again in six months by
somebody acting in good faith, which is why a refusal gets its log line and its place in the owning
document exactly like a decision (foundation section 15).

## 2. Find every target, by grep rather than by memory

**Never fan out from memory.** Grep for the identifiers and the distinctive phrases the decision touches
and let the tree tell you where it lives:

```bash
grep -rn "C7\|M9\|OQ-8" specs/ CLAUDE.md .claude/
grep -rln "the distinctive phrase the old decision used" specs/ CLAUDE.md .claude/
```

The second grep is the one people skip and it is the one that finds the stale copy, because a document
that paraphrased the decision does not cite its identifier.

## 3. The targets, and what each one gets

Work down the authority chain. **A lower document never decides**, so if the decision is not in the
foundation or an ADR first, stop and put it there before touching anything below.

| Target | What it gets | Skip when |
| --- | --- | --- |
| `specs/mapsift-foundation.md` | the decision as **law**, plus its scar or its evidence, plus an entry in section 15 and a version bump | the decision is code shape only, which is an ADR |
| `specs/PRD.md` | the requirement and its acceptance criterion in its family (a T, M, S, N or U item) taking the next free number. A retired one is struck through **in place**, never renumbered | nothing in the product's behaviour moved |
| `specs/adr/` | an amendment inside the owning ADR with its date and reason; a new numbered file only for a new decision area. **An ADR is never quietly rewritten: every change carries its dated note (ADR-0001, revised 2026-08-05)** | no code shape moved |
| `CLAUDE.md` | **only if the constraint is true for every task.** Otherwise it belongs one tier down (ADR-0002 section 5) | almost always: the file is the digest, not the archive |
| `.claude/rules/` | the enforceable per-path restatement (`angular.md`, `design-system.md`, `python-django.md`, `rust-core.md`), because that is what fires while a file is being edited | there is no path-scoped consequence, which is most of the time |
| `.claude/skills/` | the procedure, if the decision changes how work is done | it changes what is true rather than how work runs |
| `specs/dependencies.md` | **any measurement pinned to a version**: what the installed source does, a particularity that bites, a probe against the lockfile. A dated subsection, naming the version read and the ADR it fed | the decision touched no external dependency. **Added 2026-08-14, after this file had no row for it at all** and two django-ninja 1.6.2 measurements were made in one round, cited in an ADR, and never reached the survey the external-dependency rule calls their home. The next window opens this file first, by its path rule, and finds nothing |
| `specs/session-handoff.md` **section 0** | the live state, and section 6 if a settled objection was reversed | never. Section 0 always moves |
| `specs/log.md` | **one grep-able line**, oldest first, in the format the file's header states | never |

### Before you write into a target, grep that target for what you are about to say

**The anchor is not the check** (added 2026-08-17, from the measurement below). This is mechanical: one
trigger, one command. It is deliberately not "read the file carefully".

**It fires when you are adding text** to a document: a new bullet, a new paragraph, a new dated note, a new
table row, a new section. **It does not fire when you are replacing text you have read in this window** and
are editing in place.

**What you run, against the target file alone, before the edit:**

```bash
grep -n "<a distinctive phrase from what you are adding>" <the target file>
```

The phrase comes from the **content you are adding**, never from the anchor you are editing next to: the
identifier the note is about, the field name, the issue key, the decision's own wording.

**A hit means the target already speaks to this, and what you are adding is a second copy until you have
read the hit and decided otherwise.** Then do exactly one of two things: amend the place that already
exists, or write your addition with a dated note saying how it differs from it. **A hit is never permission
to skip the target.** It changes the shape of the edit from an insertion into an amendment, and nothing
else.

**Why the anchor cannot stand in for this.** `Edit` proves that its `old_string` occurs exactly once. It
proves nothing about whether the text you are **adding** occurs at all. *Measured 2026-08-17 under MAP-14:*
two edits each matched a unique, valid anchor and each inserted a block that already existed further down
the same file in a **corrected** form, so both insertions were superseded content and both had to be
reverted.

**The case this exists for is your own earlier work in the same session.** This canon already forbids
answering from memory about the canon, and already requires verifying against disk rather than against
another agent's report. **Neither covers what you yourself wrote an hour ago**, which is where confidence is
highest and the check feels most redundant. In a long session your own output is a source to re-read, not a
memory to cite.

## 4. Two rules that decide the hard cases

**A settled objection that changes is moved, never deleted.** `session-handoff.md` section 6 lists what
must not be reopened. When one is genuinely reversed, it stays in the list with its reversal recorded and
the reason, because a settled objection that vanishes without a record is how a team stops trusting its
own log.

**Work in flight is a target, and the committed tree is not the whole tree** (added 2026-08-14). A decision
closed in the middle of a task invalidates artifacts that already exist against the version it replaced, and
those artifacts are often **uncommitted**: a window's tests in the working tree, a prompt already dispatched,
a spec a window has read. Run `git status` as part of the sweep and read what is uncommitted, because the
grep over `specs/` will not see it. The worked case is the one that produced this paragraph: an ADR gained a
name at midday, a test module written that morning carried a docstring saying that name did not exist, and
each was correct when written. **The failure is invisible to step 5**, which stops you when a target
contradicts the decision, because the invalidated artifact was never in the target list at all.

**Provenance citations do not move.** "Closed in v0.3" is history. Only pointers that claim currency move,
and an ADR's `Authority` line is a claim that it has been **read** against that version and does not
contradict it. **Moving that pointer without doing the reading is worse than leaving it stale**, because
it converts an obvious gap into a false assurance.

## 5. Verify, then report

```bash
grep -rn "<the old wording>" specs/ CLAUDE.md .claude/ docs/    # must return nothing
grep -rn "—\|–" specs/ CLAUDE.md .claude/ docs/                  # must return nothing
```

Report: which kind of change it was, every file touched and what each got, every target you **skipped**
with the reason, and anything you found stale while grepping that this decision did not cause. That last
one is where the real defects surface.

**Paste the greps you ran and what each returned. Never report that you swept** (added 2026-08-14, ADR-0008
section 9). This project's oldest rule is that a state claim is written with the command that verified it,
and it had never been applied to this skill's own completeness claim, which is the one claim here that
nothing else checks. Three of the seven blocking findings recorded against an orchestrator-owned document
were a sweep that reported itself complete and was not, and in the sharpest of them **this file already
prescribed both greps and already named the second as the one people skip**, and it was skipped three times
in the session that quoted it. A pasted command with a hit count is a fact a reader can re-run; "propagated
to every target" is a memory. **The reverse grep of step 2 is the one whose output has to appear**, because
the forward grep can only find the wording you just wrote.

**If a target contradicts the decision rather than merely lagging it, stop and report.** Two documents
disagreeing is not a propagation problem; it is a decision somebody needs to take.
