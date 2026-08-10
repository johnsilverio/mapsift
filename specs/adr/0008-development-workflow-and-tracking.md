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

## Consequences

The `linear-workflow` and `dev-workflow` skills are the enforceable restatements of this decision and inject
or cite it rather than deciding; where a skill and this ADR disagree, the ADR wins, and where this ADR and
the foundation disagree, the foundation wins. The port's residue rule is recorded with this ADR's creation:
a fan-out after adapting borrowed material sweeps for **state claims** (repository layout, stack names,
invariant ranges, version numbers), not only for the donor's name, because a false state claim executes
while a wrong name merely offends.
