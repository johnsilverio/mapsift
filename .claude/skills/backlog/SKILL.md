---
allowed-tools: Bash(grep *), Bash(sed *)
name: backlog
description: Turn a problem, a module or a closed decision into a real backlog: requirement analysis against the canon, decomposition into issues that are outcomes rather than task lists, sizing against the tracer-bullet rule, dependency edges, sequencing into a vertical slice, priority with meanings, and the Linear project, milestones and issues that carry it. Acts as product owner and scrum master over what already exists, not just as an issue creator. Use this whenever the user wants to plan work, break something down, create issues, fill or groom the backlog, or asks "what are the tasks for X". Use it even when the request sounds like "just create an issue for this", because an issue that is not sequenced and traced is noise. Triggers on "/backlog", "break this into tasks", "create the issues", "plan this module", "groom the backlog", "what should we build first".
---

# Build the backlog

Turn a problem into a set of issues somebody can actually work, in an order that makes sense, each traced
to something that was already decided. **The output is a plan, not a pile.**

Two jobs at once, and they pull in different directions on purpose. The **product owner** half asks what
outcome is being bought and in what order it delivers value. The **scrum master** half asks whether these
issues can actually flow: are they the right size, do they block each other, is anything already covered,
is anything secretly two things.

**Never create anything in Linear before the analysis is on the table and the owner has seen it.** An issue
created and then reworked is worse than one that took a minute longer, because the identifier is already in
circulation.

## What the canon offers you, injected

**The PRD's own map**, so you know which section holds the requirements you are decomposing:

!`grep -n '^## ' specs/PRD.md`

**The open questions**, one line each, because an issue may not be created for one and several gate whole
PRD families (read the full entry in foundation section 13 before leaning on one):

!`grep '^- \*\*OQ-' specs/mapsift-foundation.md`

---

## 1. Establish the problem, and refuse to guess it

State in one paragraph what is being asked for, in **outcome** terms: what will be true when this is done
that is not true now. If the request is a solution ("add a `status` column"), work backwards to the outcome
it serves and confirm that with the owner, because a backlog built from a proposed solution locks in the
solution.

**Interview before decomposing when the problem is fuzzy.** Ask about the parts a plan would get wrong:
who the actor is, what the states are, what happens in the unhappy path, what already exists that this
touches, what is explicitly not wanted. A question costs a minute and a wrong decomposition costs the
whole slice. Stop asking when the remaining questions no longer change the shape of the work.

## 2. Trace to the canon, and stop if it does not trace

**An issue exists only when it traces to something already decided, and the trace is cited.** Walk the
chain and name what governs this work:

- **`specs/PRD.md`**: which requirement items are in scope (a T, M, S, N or U identifier), and whether each
  is firm or gated: a requirement whose Open/ADR field is unresolved has a gap, and a gap is a question for
  the owner rather than work.
- **The invariants and constraints** it carries (`CLAUDE.md` C1 to C14 for the criteria, foundation
  section 11 for the scars). These decide what the acceptance has to prove.
- **The ADR sections** that fix the shape, so the decomposition does not invent a layout.
- **The open questions** it depends on. Several are hard blocks; **an open question is not an issue**, it is
  a question with an owner and an exit criterion.

Three outcomes, and only one of them continues:

| What you find | What you do |
| --- | --- |
| It traces cleanly | Continue |
| It traces to a requirement that is **soft**, so the acceptance would have to be invented here | **Stop.** Sharpen the requirement in `PRD.md` first. Acceptance invented at issue-writing time is acceptance nobody agreed to |
| It traces to **nothing** | **Stop.** This is a decision that has not been taken. Take it to the owner, close it in the canon, fan it out, then come back |

## 3. Decompose into outcomes

**The rules below restate ADR-0008 section 2 and `specs/tasks/README.md`; neither is decided here.**
Where this skill and the ADR disagree, the ADR wins.

**One issue is one behaviour, one requirement, one pull request.** If the title needs an "and", it is two
issues, which is the same rule the commit convention uses.

**Write the issue as an outcome, never as a task list.** "A feature created offline syncs without an
identifier collision" is an issue. "Work on sync" is a project. "Add a column" is a step inside one, and
steps do not get issues.

**Every issue carries its trace and its acceptance, copied rather than invented.** The requirement
identifier (a T, M, S, N or U item, a C-test, an invariant) and the pass or fail criterion that requirement
already states. If you are writing new acceptance prose, you are in the second row of the table above.

**Sub-issues are for a genuine parent and child**, not for phases. Phases are milestones.

## 4. Size each one against the tracer-bullet rule

This is the half people skip, and it is what decides whether the two-window protocol survives contact.

**An issue is the right size when all of Window A's tests for it are one tracer bullet**: one behaviour
cluster, one seam, one requirement or a tight group that shares a seam (`specs/testing.md` section 1.2).

Four tells that it is too big, checkable before anything runs:

- the outcome sentence needs an "and";
- the behaviours it names do not share a seam;
- it touches more than one bounded context in a way that is not just a read;
- you cannot say what its first failing test would assert.

Two tells that it is too small: it has no observable behaviour of its own, or it would produce a pull
request nobody could review meaningfully without the next one. **Fold those into their neighbour**, because
the protocol's overhead should not exceed the work it protects.

## 5. Find the edges, and sequence into a vertical slice

Now stop looking at issues one at a time and look at the set, which is the scrum master's job.

**Draw the dependency edges.** For each issue, what must exist first? A blocking edge is real when the
second issue's tests cannot be written without the first one's shape. **A shared file is not a dependency**;
a shared contract is.

**Sequence vertically, not by layer.** The first issues must produce something that works end to end, even
if narrow. A backlog ordered as "all the models, then all the services, then all the endpoints" delivers
nothing until the last one lands and hides every integration mistake until then. This project's build order
already says foundations before features and registries before modules; within that, the slice is vertical.

**Respect what the canon already sequenced, and what it deliberately did not.** Delivery order and roadmap
are out of the foundation's scope (`CLAUDE.md`: closed-scope, non-MVP, so "ship it sooner" is never an
argument), which means the sequence comes from the dependency edges and the project's exit criterion, not
from a roadmap. The one hard order is technical: the core and the library build before the web
(`CLAUDE.md` Commands), so a slice that crosses them is one issue with that order inside it.

**Check the set against what already exists.** Read the open issues before adding to them. Three findings
worth reporting: an issue that duplicates one already there, two issues that are secretly one behaviour,
and an issue nobody consumes, which usually means it was derived from a layer rather than from an outcome.

## 6. Prioritise with meanings, not vibes

Linear offers five and this project uses them with stated meanings (ADR-0008 section 2):

- **Urgent**: it blocks other issues in the same project, or it is a decision a later artifact is expensive
  to take back. A first migration is the canonical case.
- **High**: on the critical path to the project's exit criterion.
- **Medium**: in the project's scope and not on its critical path. Real work, no urgency.
- **Low**: worth doing and safe to never reach. If a Low sits for two projects running, it was noise.
- **No priority**: the default, and it carries no shame. Most issues sit here, and an issue that has not
  been triaged is honestly represented by leaving it here rather than by a guess.

**Priority orders the work and never promises a date.** No estimates and no story points: scope control
here comes from a closed canon and small issues, and a point ritual on a two-person team measures nothing
the issue size does not already show.

## 7. Present, then create

**Present first**: the project with its exit criterion in pass or fail terms, the milestones as its
execution phases, the issues in sequence with their traces, the edges, and anything you found that blocks
or that the canon has to absorb first. **Wait for the owner.**

Then create in Linear, through `linear-workflow`, which owns the structure, the labels, the status flow and
the MCP rules. A **spike is its own project** with its gate as the exit criterion, never a normal issue,
because its output is a decision and throwaway code rather than a feature.

**The task spec is not written here.** `specs/tasks/` explains why: it is written at pickup, by the
orchestrator, because twenty written upfront go stale before they are read.

## 8. What this skill refuses to do

**Invent a requirement.** If the work needs something nobody decided, that is a decision for the owner and
a fan-out, not a line in an issue description.

**Copy the contract into Linear.** Cite the identifier and quote the criterion. The reasoning stays in git,
because a copy in an issue description is a copy that drifts and nobody diffs a tracker.

**Create an issue for an open question.** It goes on the question's own log with its owner and its exit
criterion, and becomes an issue the day it is answered.

**Produce a backlog longer than the canon supports.** If decomposing produces thirty issues and the canon
covers twelve, the honest output is twelve issues and a list of eighteen questions.
