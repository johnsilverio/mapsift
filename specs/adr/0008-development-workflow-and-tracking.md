# ADR-0008: Development workflow and tracking

> **Status:** accepted 2026-08-05, ratified by the owner.
> **Authority:** derives from foundation v0.17 section 14 (the development method) and section 15 (decision
> log and revisions), from `specs/testing.md` section 1 (the two-window protocol, its prompt contract in 1.1
> and task sizing in 1.2), and from the `CLAUDE.md` "Process & tracking" digest. Where this ADR and the
> foundation disagree, the foundation wins.

## Context

The method was ported from a sibling project on 2026-08-05 and adapted to this repository. Its skills were
built to inject the Decision section of a workflow ADR at dispatch, and Mapsift had no such ADR: ADR-0004
here is the sync ordering strategy, so the decision this document holds lived only in the `CLAUDE.md` digest
and in two skills, with nothing in `specs/adr/` owning it. A skill citing an authority that does not exist
injects nothing and reads as if it had, which is the exact silent-empty failure ADR-0005 section 4 teaches
the tests to distinguish.

The Linear side was already decided and recorded (`specs/log.md`, 2026-08-03): the move to a dedicated team
in the owner's personal workspace, the MAP prefix, the eight team labels, the first project created from
foundation OQ-4. This ADR ratifies those records and the working loop as one decision.

## Decision

### 1. The boundary

**git owns the contract; Linear owns execution state; the task identifier bridges them.** The contract is
the foundation, the PRD, the ADRs and the spec per task (`specs/tasks/README.md`); it changes only through a
reviewed commit. Execution state is project, milestone, issue, status, assignee and discussion; it changes
constantly and never lives in a markdown file. `MAP-<n>` is the only field in both and never carries state.
A decision is never made in a Linear comment: it goes into the foundation or an ADR before code follows it.

### 2. Issues

An issue exists only when it traces to the canon (an invariant, a foundation decision, an ADR, a PRD
requirement, or an answered open question), and the trace is cited in the issue. One issue is **one
behaviour, one requirement, one pull request**, written as an outcome; acceptance is copied from the
requirement, never invented at creation time. No estimates and no story points; priority orders and never
promises a date. A spike is its own project with its gate as the exit criterion. The assembled task lives in
git at `specs/tasks/MAP-<n>-<slug>.md`, written at pickup rather than at backlog creation.

### 3. The structure in Linear

The owner's **personal workspace**, one team **Mapsift** with prefix **MAP**; the isolation wall is the API
key scoped to that team, verified by `list_teams` returning only it. Projects are delivery areas with a
start and an end; milestones are their execution phases; the eight team labels (`domain`, `api`, `sync`,
`core`, `frontend`, `geo`, `infra`, `adr`) recover the cross-cutting view; cycles are off. The Linear MCP is
a **local-scope** server keyed by this working tree, never an account-level connector.

### 4. The working loop

Work runs in the **two-window protocol under an orchestrator**: `specs/testing.md` section 1 is the method,
1.1 the prompt contract, 1.2 the sizing rule, and this ADR does not restate them. The orchestrator does not
implement and dispatches sequentially; the branch is created from the Linear issue so the identifier rides
in its name; the gate runs before every commit; commits are atomic Conventional Commits in English with no
AI attribution trailer (the `dev-workflow` skill); the change reaches `main` only through a pull request
with green required checks. Status moves **from git to Linear, one direction**: a pushed branch to In
Progress, an opened pull request to In Review, a merge to Done.

> **Changed (2026-08-06, closing the divergence the MAP-7 round recorded).** The pushed-branch wire is
> deliberately not built. Moving an issue to In Progress is a **human act**, performed through the MCP at
> pickup on the owner's OK, because starting work is a decision rather than a side effect of a push. The
> letter above is corrected to: an opened pull request moves In Review, a merge moves Done, and nothing
> moves an issue into In Progress automatically. The GitHub automation stays deliberately narrow.

> **Added (2026-08-10, MAP-41): a window may be opened by the orchestrator or by the owner, and the protocol
> does not change either way.** The method has always specified the three roles, the sequence and the review,
> and never **who opens the window**. Both modes are named now because leaving it unwritten meant the manual
> one was the method rather than a mode of it.
>
> **Automatic is the default.** The orchestrator asks, and on the owner's go dispatches the window as an
> isolated subagent carrying **the identical prompt the manual mode would have produced, from the same
> source**. It reviews what comes back **by running**, and Window B is not dispatched until that review has
> happened. What isolation buys is exactly what `specs/testing.md` section 1 wants and cannot get from an
> intention: a context that returns a result rather than its reasoning.
>
> **Manual stays a named mode and is not a legacy path**, in the `orchestrate-manual` skill. What the
> automatic mode gives up is not isolation, which it gains, but **the chance to interrupt**: to watch a
> window take a wrong turn in its second minute and stop it. That is worth little once the contract is
> written and the boundaries are closed, and a great deal while the task is still being understood, which is
> the condition rather than the preference that selects it.
>
> **Three conditions, each a fact on disk rather than a judgement of the day.** A **task spec exists** with
> its boundary decisions registered, which is what makes a prompt a pointer instead of a briefing. The
> **gate runs from the orchestrator**, never from the window, which was already true and is now load-bearing.
> And the **enforcement layer exists** (MAP-40), because unattended dispatch is the first mode with no human
> between an instruction and a file, and until 2026-08-10 this repository had none.
>
> **Two harness facts a dispatch must carry, measured rather than assumed.** A subagent's injected
> `gitStatus` block was **stale**, reporting a commit one task behind the live tree, so a prompt tells the
> window to measure the tree rather than trust its own context block. And **path-scoped rules arrive on
> demand**, delivered with the `Read` that matches their glob rather than at launch, so a window that owes a
> stack rule meets it only after it opens a file in that stack. The root `CLAUDE.md` **is** inherited, so
> tier 0 survives isolation and a prompt saying it loads on its own is telling the truth.

### 5. Skills inject their dependencies

A skill that depends on a spec's content to function **loads it from disk at dispatch** with a `!` command
injection, never as a paraphrase and never as a bare citation the window may skip: `test` and `implement`
inject `specs/testing.md`, `code-review` injects its section 8, `linear-workflow` injects this ADR's
Decision, `orchestrate` injects the measured tree and the handoff's section 0. A copy of a spec inside a
skill is a second copy outside the fan-out, and a citation without injection is a contract the window can
fail to read. Heavy canon (the foundation, the PRD) stays by reference, opened per cited section.

### 6. A crossing change is one pull request

A change spanning the api and the web (a serializer, the regenerated schema, the regenerated types, the
consumer) is one commit, one pull request, one CI run, in the one repository ADR-0001 section 1 defines.
Drift between the sides is prevented by generation plus the freshness gate, not detected by a schedule.

### 7. What is deliberately not adopted

**No webhook bridge that turns an issue assignment into an autonomous run opening a pull request.** It
collapses the two windows into one pass, which is the failure the protocol exists to prevent. The gate for
reconsidering: a mechanical, fully specified backlog whose tests already exist, and a quality gate with a
track record. Until both hold, agents read issues, comment and move state through the MCP, and nothing else.

> **Scoped (2026-08-10, MAP-41), because the closing sentence was read as forbidding something this refusal
> never argued against.** What is refused is the **bridge**: an assignment becoming a run that opens a pull
> request with nobody in the loop, and the stated reason is that it **collapses the two windows into one
> pass**. **Orchestrated dispatch does not collapse them, it isolates them**, which is the property the
> protocol exists to buy, and the orchestrator's review still sits between Window A and Window B. So the
> refusal stands exactly as written for the bridge, and section 4's addition of the same date covers
> dispatch. The distinction to hold: this section refuses **an issue reaching a pull request unattended**;
> it does not refuse **a window running in a context of its own**.

### 8. Parallel work

Independent issues run in independent git worktrees, so two lines of work never share a checkout or a
branch. The `worktree-commit-merge` skill is the exit path; `main` is never merged locally.

### 9. The orchestrator's artifacts have no gate, so four things replace the missing one

**Added 2026-08-14, at MAP-14, from a count rather than from an impression.** Every round since MAP-10 has
produced at least one **blocking** review finding in a document the orchestrator owned, and two rounds
produced nothing else: `specs/log.md` records "every blocking finding of that task's four review rounds was
the orchestrator's" at MAP-12 and "both in documents the orchestrator owned" at MAP-13. Seven instances in
seven rounds is a process defect and not a run of bad luck.

**The diagnosis, and it is structural.** Sorted by artifact rather than by lesson, the seven collapse into
two surfaces. **Four sit in the two blocks of a task spec that transcribe instead of pointing**, its
Acceptance (a copy of the requirement) and its Evidence (a transcription of a measurement); `tasks/README.md`
opens with "it cites and never restates" and then designates exactly those two as exceptions, so the defects
live in the only part of the file where they are possible. **Three sit in a fan-out**, where the artifact is
a claim that a sweep covered its targets.

**Why this role and not the windows.** Every artifact a window produces is falsifiable by a machine: `ruff`,
`mypy --strict`, `pytest`, `lint-imports`, the freshness gates and the three hooks all read code. **Nothing
reads a task spec, an ADR or a fan-out sweep**, so the orchestrator is the only role in the loop operating
with no red-or-green signal, and it is the role producing the findings. The role is also the only one that
**compresses**: a window produces, an orchestrator reduces five documents to one, and every lossy operation
is a claim about what it dropped that nothing in the loop compares against the source.

**Why no further prose rule was written, which is the load-bearing half.** "A sentence about a set has to be
re-read against the set" was already written down after MAP-12 and was violated again at MAP-14 by the
orchestrator that had read it. The `fan-out` skill already prescribes both greps and already names the
second as the one people skip, and it was skipped three times in the session that quoted it. **The prose
layer is saturated on both surfaces**, and `.claude/skills/README.md` already carries the law that decides
this: a prompt instruction is a request, a hook or a gate is enforcement.

So, six changes, each removing a surface or moving a discovery rather than asking for more care. The fourth,
fifth and sixth were all added on 2026-08-17 by the surfaces they name, none of which had been counted when
the first three were written; the sixth is about the cost of the machinery rather than about a defect.

1. **A task spec's Acceptance block is a delta, never a copy.** It cites the requirement by identifier and
   lists **only what this task does differently**: what is split, what has no runtime here, what is deferred,
   each with its reason. The window reads the criteria from the PRD, where they are law. Under a copy the
   orchestrator must reproduce N clauses and any omission is invisible; under a delta **there is nothing to
   omit**, because the full set is never transcribed. It is also shorter, and it restores that file's own
   first rule. **This does not change the Linear issue**, whose acceptance stays copied from the requirement
   (section 2): an issue is read standalone in a tracker by a human, a task spec is read beside the canon.
2. **The task spec is adversarially reviewed before Window A, not after.** The Spec axis already reads it,
   but only once a window has consumed it, and `specs/testing.md` section 1.1 tells that window handed-over
   evidence is not its to question, so **a spec defect rides through by construction** and surfaces a full
   window later. That late discovery is the correction round this section exists to stop. One pass over the
   spec alone, with the requirement open, before the dispatch.
3. **A fan-out reports the commands it ran, never that it swept.** This project's oldest rule is that a
   state claim is written with the command that verified it, and it had never been applied to the fan-out's
   own completeness claim. The sweep pastes its greps and their hit counts.
4. **Before writing into a target, grep that target for the content, never only for the anchor** (added
   2026-08-17; the mechanical form is in the `fan-out` skill). **A third surface, found by the first three
   catching it.** The pre-dispatch read of change 2 fired for the first time and its blocking findings were
   caused by the orchestrator that had just written the step: two edits matched a unique, valid `Edit`
   anchor and each inserted a block that already existed further down the same file **in a corrected form**,
   so both were superseded content and both were reverted. **The false assurance is specific and worth
   naming: `Edit` proves its `old_string` is unique and proves nothing about the text being added.** The
   case it guards is **your own earlier work in the same session**, which no existing rule covered: the
   canon rule forbids answering from memory about the canon, and the verification rule targets another
   agent's report, while a long session makes the orchestrator's own output a source to re-read rather than
   a memory to cite.
5. **A fan-out sweeps `apps/` and `libs/`, and a count is re-read against its set every time the set is
   touched** (added 2026-08-17; the mechanical form is in the `fan-out` skill). **Two holes, one round.**
   The skill's target table and both its verification greps covered the canon documents and `docs/`, a
   directory that does not exist in this repository, and never covered code. **Code is a fan-out target by
   this canon's own requirement rather than by tolerance:** `CLAUDE.md` tells a comment to cite the decision
   and let the document hold the reasoning, and `specs/testing.md` section 6 requires a test to name its
   requirement, so a docstring is a citation that goes stale exactly like a document and nothing was
   looking. And the same round produced the second hole in its own fix: a count corrected to three was made
   false an hour later **by the same session adding a fourth note to the section it counted**, which is
   MAP-13's recorded lesson that a verdict refined later needs its own sweep, met again because a completed
   sweep leaves the memory of having swept. **The sharper statement the three misses of that session share:
   a fan-out reaches the decision being closed and misses the facts the decision changed in passing**, which
   is why the trigger is now the set being touched rather than the decision being closed.
6. **A correction round that touches no production file closes with the Spec axis alone** (added
   2026-08-17). The three axes stay the rule for any round that changes production code, and nothing about
   their independence is reconsidered. **What changed is a measurement, not an opinion.** Across MAP-14 the
   axes over implementation found two blocking defects in ordinary traffic, a binding that never reached the
   record Django writes about a response and a carrier the dedup loop overwrote, both of which would have
   shipped. The axes over **test-only** correction rounds found stale docstring counts and a missing
   idempotent create, at three full runs each, and **the Spec axis is the one that found both blocking
   defects of the task**. A correction round also creates prose defects at close to the rate it repairs
   them, measured: the round that existed to remove four stale counts left a new false one behind in the
   same file. **The cap that comes with it, so this does not become a licence to stop caring:** after a
   round's second pass, an advisory that is prose only is recorded in `specs/log.md` and does not gate the
   merge. A requirement met with green gates is not held hostage to docstring accuracy, and the accuracy is
   still written down where the next reader meets it.

**What this costs:** one subagent pass per task before Window A, and a fan-out report that is longer than a
sentence. **What it does not buy:** anything on the two surfaces a machine could have checked instead, and
the residual is named rather than hidden. A gate comparing an Acceptance block against the PRD was
considered and refused: the PRD's acceptance lines are semicolon-separated prose rather than structure, so
the parser would be brittle, and a brittle gate is one people switch off (section 5's rule about a guard
wider than its rule, in `.claude/skills/README.md`).

## Consequences

The `linear-workflow` and `dev-workflow` skills are the enforceable restatements of this decision and inject
or cite it rather than deciding; where a skill and this ADR disagree, the ADR wins, and where this ADR and
the foundation disagree, the foundation wins. The port's residue rule is recorded with this ADR's creation:
a fan-out after adapting borrowed material sweeps for **state claims** (repository layout, stack names,
invariant ranges, version numbers), not only for the donor's name, because a false state claim executes
while a wrong name merely offends.
