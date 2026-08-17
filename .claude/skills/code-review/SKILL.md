---
allowed-tools: Bash(git *), Bash(sed *), Bash(ls *)
name: code-review
description: Review your own diff against the canon with explicit quality gates: the machine gates first, then three isolated judgement axes (Canon, Spec, Craft) with blocking and advisory findings. Built for the orchestrator closing a window it dispatched, where the requirement, the task spec and the canon are all known. Use when reviewing what a window delivered, your working branch, or anything before you commit it. Triggers on "/code-review", "review this diff", "review the branch", "is this ready to commit", "review since <ref>". For a pull request written by someone else, use `pr-review`, which reconstructs intent instead of assuming it.
---

# Review your own diff

Review the diff between `HEAD` and a fixed point, in **two stages that are not interchangeable**: the
**machine gates**, which are pass or fail and decided by a script, and the **judgement axes**, which are
decided by reading and which never run before the machine gates are green.

**This is the review of work you commissioned**, normally run by the orchestrator closing a window it
dispatched. That is what makes it stricter than reviewing a stranger's contribution rather than gentler:
the requirement is known, the task spec exists, the canon was in the window's reading protocol, and the
window was told to stop and report on a contradiction rather than reconcile it. **So a canon violation here
is not a gap in the author's knowledge, it is a defect in the delivery**, and "they could not have known"
is never available as an explanation. For code written outside this loop, `pr-review` is the skill, and it
starts by reconstructing an intent this one already has.

**This skill reports. It does not fix.** The agent investigates, the human decides. Handing a review the
authority to also apply its own findings collapses the independence the review exists for.

**It never claims completeness.** A model that says "here are all the bugs" found *some* bugs. Say what was
examined and under what criteria, and never that the diff is clean.

## Stage 0: pin the diff, and fail early

1. **The fixed point** is whatever the user named: a SHA, `main`, `HEAD~5`, a branch, a tag. If they named
   none, ask. Do not guess.
2. `git rev-parse <ref>` resolves, and `git diff <ref>...HEAD` is non-empty. **Three dots**, so the
   comparison is against the merge base. A bad ref or an empty diff fails here rather than inside three
   parallel reviews.
3. `git log <ref>..HEAD --oneline` for the commit list.
4. **Find the spec, and here it should already exist.** In order: the **task spec** at
   `specs/tasks/MAP-<n>-*.md`, which is the assembled contract and names the requirement, the invariants
   and what was explicitly out of scope; then the `MAP-` identifier in the branch name or the commit
   messages; then the issue itself through the Linear MCP. **If no task spec exists for a dispatched window,
   that is a process finding worth reporting**, because the window was briefed from something that is no
   longer on disk. If there is genuinely no requirement, the Spec axis reports so, and work that traces to
   nothing should not exist (`CLAUDE.md` "Process & tracking").

## The gate, injected because it is what stage 1 runs

This is section 8 of `specs/testing.md`, loaded from disk. It is the authority for what must be green.

!`sed -n '/^## 8\. The gate/,/^## 9\./p' specs/testing.md`

## The diff you are reviewing

- Commits since `main`: !`git log main..HEAD --oneline 2>/dev/null | head -20 | grep . || echo "(none: you are on main, or the branch has no commits yet)"`
- Working tree: !`git status --short 2>&1 | head -20`
- Task specs on disk: !`ls specs/tasks/MAP-*.md 2>/dev/null || echo "(none)"`

---

## Stage 1: the machine gates, and they run first

**Never spend a model's attention on what a script already decides.** The gate list is the table injected
above from `specs/testing.md` section 8, and **this skill does not restate it**. A local copy that drifts
from the one CI runs is worse than none, which is the rule `commit` already states.

**Run them through `/quality-gate`**, which knows which checks exist for the ecosystem the diff touches and
which do not exist yet. That matters more than it sounds here: four ecosystems share one gate, the build
order between the core, the library and the web client is a requirement rather than a convention, and the
generated-contract half has exactly one live direction today. A review that reports failing gates for a
stack the diff never touched is reporting that it does not know what it is looking at.

**If a machine gate is red the review stops here and reports that.** A judgement review over a red build
is a report about code that does not run.

**Prose is caught by `.claude/hooks/check-prose.sh` since 2026-08-10, and the axis still reads it.** The
hook is `PostToolUse`: the write **lands** and the violation is handed back to the model to fix, which is
not the same as refusing it. Two things it cannot see, and they are why nothing here was narrowed on the
strength of it: a markdown file written through `Bash` rather than `Write` or `Edit` is never checked at
all, and a turn that ends before the model acts leaves the violation on disk.

**Run them yourself.** Do not read the window's claim that they passed. Coding-agent benchmarks record
models that build a reasonable thing and then hallucinate their own inspection, and this project's own
rule predates that evidence: verify against disk, never against a report.

## Stage 2: three axes, in isolated contexts, never merged

Run the three as **three parallel subagents**, each seeing the diff, the commit list and its own criteria,
and **not** the reasoning that produced the change. A fresh reader evaluates the result on its own terms; a
shared context lets one axis mask another, which is the whole reason they are separate.

**One narrow exception: a correction round that touches no production file closes with the Spec axis alone**
(ADR-0008 section 9, change 6, added 2026-08-17). **Decide it from the diff, never from the round's
description:** if one file outside the test tree changed, all three run. **The comparison is against the
tree as it stood when the round was dispatched, not against `HEAD`**, because an uncommitted implementation
from an earlier round makes `git status` show production files this round never touched; measure the
production paths before dispatching and compare the numbers after. The measurement is in the ADR and
the short form is that Spec found both blocking defects of the task that produced this rule, while the other
two axes on test-only rounds found docstring counts and a missing idempotent create.

**Do not merge or rerank the three reports.** Present them under their own headings. A change can pass one
axis and fail another, and a single ranked list is where that gets lost.

### How they are dispatched, measured 2026-08-10 rather than assumed

**The three prompts are in [`references/axis-prompts.md`](references/axis-prompts.md), copied verbatim
rather than composed each time.** Only three values vary: the range, one clause naming the change, and the
task spec path. The criteria are identical on every review, so writing them fresh per run pays for them per
run and lets the copies drift, which is the argument that moved the window protocol's standing discipline
into `test` and `implement`.

**Three `Agent` calls in one message** so they run concurrently, `subagent_type: general-purpose`, and
**`model: opus`** on each, because the axes are the judgement half of this loop. Every prompt **ends with
two instrumentation lines** asking whether the root `CLAUDE.md` was already in context and whether any tool
call was intercepted. They cost nothing and they are what turns a claim about the harness into a
measurement.

**What a subagent inherits is in ADR-0008 section 4**, with the decision that rests on it. One consequence
belongs here rather than there: **a path-scoped rule arrives on demand**, so an axis that never opens a file
in a stack never meets that stack's rule.

**One caution the prompts carry because it was found rather than expected:** a subagent's injected
`gitStatus` block can be **stale**. Every axis is told to run the range command itself rather than read its
own context block for the state of the branch.

**The orchestrator still runs the machine gates itself** (stage 1) and still reads the diff. The axes judge;
they never replace the run. **If the axes are run inline instead**, which is a deliberate departure and not
a default, say so in the verdict: a reader has to know whether one axis could have masked another.

### Axis 1: Canon. Blocking.

Does the diff violate something the ecosystem decided? This axis reads **law**, and law is not a judgement
call: a finding here blocks.

**Read [`references/canon-checks.md`](references/canon-checks.md)** and work through it. It carries what a
violation of each invariant `I1` to `I11` and each constraint `C1` to `C14` looks like in code, the
code-shape rules of ADR-0002, ADR-0003 and ADR-0007, and the names that must not exist. The reasoning behind
each is in the authority it cites, not in the checklist.

The four this axis catches most often, worth holding in mind while reading a diff even before you open the
reference: **a metric computed in degrees, or in UTM as an authoritative legal frame** (M5); **a tenant-owned
table, index or foreign key that does not carry the tenant identifier the way ADR-0005 requires** (I4, C4);
**client logic settling into the Angular or Python layer instead of the shared core** (C11); and **a path
that discards, overwrites or silently drops a legal-weight edit, including a validation that refuses without
retaining** (C7).

Cite the rule by identifier and quote the hunk. **An invariant finding is never softened.** If the
invariant is genuinely wrong, that is a foundation revision decided by the owner, not a compromise reached
inside a review.

### Axis 2: Spec. Blocking for the first and third, advisory for the second.

Against the requirement's acceptance criterion, quoting the criterion line for every finding:

1. **Missing or partial**: the criterion asks for something the diff does not do. **Blocking.**
2. **Scope creep**: behaviour in the diff that no requirement asked for. **Advisory**, and reported with
   the question of whether it should become a requirement or be removed, because unrequested behaviour is
   untested by construction and nobody agreed to maintain it.
3. **Implemented but wrong**: the criterion looks satisfied and the implementation would not survive its
   own test. **Blocking.**

Five disqualifiers sit on this axis and each one blocks on its own:

- a schema change with no migration;
- a change to public behaviour with no test covering the compatibility;
- **a commit message or PR description that does not match the diff**;
- a bulk addition nobody reviewed;
- a regression, meaning an existing test weakened, renamed or deleted.

### Axis 3: Craft. Advisory by default.

Judgement calls, and they are labelled as such. **A documented decision in this repository always wins over
this axis**, and anything the tooling already enforces is skipped.

**Test quality first**, because this is a test-first project and a bad test is worse than none: a test
coupled to implementation (mocks an internal, reaches a private, asserts through a side channel), a
**tautological** test whose expected value is recomputed the way the code computes it, a test with logic in
it, a name that needs "and", an assertion with no requirement behind it.

**The smell baseline** (Fowler, *Refactoring* chapter 3), each a labelled heuristic and never a hard
violation: mysterious name, duplicated code, feature envy, data clumps, primitive obsession, repeated
switches, shotgun surgery, divergent change, speculative generality, message chains, middle man, refused
bequest.

**Agent navigability**, because the next reader of this code is a model: a file that no longer fits in one
read, a generic name (`data`, `handler`, `Service`, `Manager`) whose grep returns fifty hits, nesting past
two levels where a guard clause would do, a boundary with no explicit type, an error message that says
`invalid input` instead of carrying the value and the expectation.

**Comments**, against `CLAUDE.md`: an inline comment that explains what the code does is a naming failure;
one that restates a decision the canon documents is a second copy that will drift; one that protects a
line where the correct code looks wrong has earned its place.

**The replacement is judged on the next reader, never on the line count.** A shorter form that hides a
tradeoff names the tradeoff or is not raised, and a construct the canon made deliberately verbose is not a
finding at all: the five single-variant target enums (M9's structural pairing), the hand-spelled
`#[tsify(type = ...)]` (ADR-0009 section 3), a closed set carrying one variant today (M13) and an empty
payload struct each look like something to collapse, and each is law. **A review that always recommends the
shorter form has stopped exercising the judgement this axis exists for.**

## Stage 3: the finding format, and the bar a finding has to clear

Every finding carries, without exception:

- **file and line**, and the quoted hunk;
- **the rule**, cited by identifier (`I4`, `C7`, `M9`, `ADR-0005 section 3`, a smell name) or, on the Craft
  axis, named as a judgement call with no identifier;
- **the failure**: concrete inputs or state, and the wrong output, refusal or corruption that results.
  "This could be a problem" is not a finding.

**On the Craft axis the third element is the replacement, not the failure.** A smell produces no wrong
output, so demanding one either kills the finding or invites the hedge that fills its place, which is how a
complexity review degenerates into "have you considered whether this is more complex than necessary". Name
what replaces it, concretely enough to apply: *twenty-seven-line validator, the standard library ships this*,
*abstraction with one implementation, inline it until a second exists*, *manual loop building a dict,
`dict(zip(...))`*. **A Craft finding with no replacement is an opinion, and an opinion goes unstated.**

**Report only what you are confident of.** A reviewer asked to find gaps will produce some even when the
work is sound, because that is what it was asked to do, and chasing every one of them buys defensive code,
extra abstraction and tests for cases that cannot happen. **Flag what affects correctness or the stated
requirement; everything else is advisory and says so.** When you are unsure whether something is real, say
that you are unsure rather than dropping it or dressing it up.

## Stage 4: the verdict

One of three, stated plainly:

| Verdict | Meaning |
| --- | --- |
| **BLOCKED** | at least one machine gate is red, or at least one blocking finding stands. Not committed |
| **PASS WITH FINDINGS** | gates green, no blocking finding, advisory findings listed. The owner decides which to take |
| **PASS** | gates green, nothing blocking, nothing advisory worth the owner's time |

Close with per-axis counts and the worst finding **within each axis**. Do not pick a single winner across
axes; that is exactly the reranking the separation exists to prevent.

Then the two things the review owes the owner beyond the findings:

- **What the canon has to absorb.** A decision taken during the work, a spelling to ratify, a requirement
  that turned out to be wrong. Under the fan-out rule that lands in the owning document **before** the
  commit, never as a follow-up.
- **What was not examined**, and why. Coverage the diff has no test for, a path only the containerized
  database exercises, an integration nobody ran.
