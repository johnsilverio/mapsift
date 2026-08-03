---
name: linear-workflow
description: "Use when creating, structuring, or updating Mapsift work tracking in Linear, or when deciding whether a piece of work belongs in Linear at all. Covers the git-versus-Linear boundary (contract vs execution state), the Workspace/Team/Project/Milestone/Issue structure for Mapsift, when an issue may be created (only when it traces to the foundation/PRD/spec), the GitHub status automation, and the local-scope MCP isolation rule. Trigger before touching any Linear issue, project, milestone, or cycle."
---

# Linear workflow (Mapsift)

## The boundary (read this first)

git owns the contract; Linear owns execution state; the task ID bridges them.

- git (foundation, ADRs, spec-per-task): the what and the technical how. The agent reads this to implement. Changes via reviewed commit.
- Linear (Project, Milestone, Issue, status, assignee, cycle, discussion): the state of execution. Changes constantly.
- The task ID (MAP-...) is the only field in both. It never carries state, so it never diverges.
- Never edit in Linear something that is a git truth (a spec, an acceptance criterion). Never put status in git. There is no two-way sync, by design.

## When an issue may be created

- Only when it traces to `specs/mapsift-foundation.md`, the PRD, or a spec. An issue that does not trace to the contract is noise. Do not create it.
- While the foundation does not exist, create nothing. No improvised backlog.
- A spike (an open question with a feasibility gate, e.g. CRDT on shared geometry) is its own Project, not a normal issue; the gate is written in the project description as the exit criterion.
- The trace is cited, not assumed. When creating an issue, name the requirement it comes from (a PRD item, a C-test, an invariant, an ADR). If you cannot name one, the issue is noise and the answer is to close the decision first, in git.

## Current state of the workspace

**Verified 2026-08-03, and the workspace moved that day.** Mapsift now lives in the owner's **personal
workspace**, in a dedicated team **Mapsift (prefix MAP)**, rather than in a workspace of its own. The reason is
practical: he runs several personal projects and switching workspaces was the bottleneck. The isolation that
the separate workspace used to provide is now provided better, by an **API key scoped to the Mapsift team**,
because a key scope is a wall and remembering which workspace you are in is discipline.

On disk in Linear: one team, **one project** (`First vertical slice: the sync spine`) with six milestones and
**MAP-1 to MAP-24**, all in Backlog. That project was created from foundation **OQ-4**, closed in v0.17, and
not the reverse: git owns the contract, Linear owns execution state.

The four onboarding issues that the old workspace carried are gone with it and were never real work. The
numbering restarted, so MAP-1 is the first real issue rather than the tutorial's.

## What one issue is

- **One behaviour, one requirement, one pull request.** If the title needs an "and", it is two issues, the same rule the commit convention uses.
- **An issue is written as an outcome, never as a task list.** "Deduplicate by mutation number and echo the cursor" is an issue; "work on sync" is a project and "add a field" is a step inside one.
- **Every issue carries its trace and its acceptance**, copied from the requirement rather than invented: the identifier (a C-test, a PRD item, an ADR) and the pass/fail criteria that requirement already states. If the acceptance has to be invented at issue-writing time, the requirement is soft and the answer is to sharpen it in git first.
- **Sub-issues are for a genuine parent-child split**, not for phases. Phases are milestones.
- **No estimates, deliberately.** Scope control here comes from the closed canon and from small issues, and a story-point ritual on a three-person team measures nothing that the issue size does not already show. Revisit only if forecasting ever becomes a real need rather than a habit.

## The issue lifecycle, and where the two-window protocol lands

Status lives only in Linear. The flow is deliberately short, and the interesting part is that **red and green are both "In Progress"**, because the two-window protocol is one unit of work rather than two.

| Status | What it means |
|---|---|
| **Backlog** | Traced and accepted, not started. Everything begins here. |
| **Todo** | Picked up next. Only meaningful when more than one person is choosing work. |
| **In Progress** | Window A is writing the failing tests, or window B is implementing to green. Both. |
| **In Review** | The PR is open and CI is running (`dev-workflow` owns everything from the branch onward). |
| **Done** | Merged to `main` with the gates green. |
| **Canceled** | The requirement moved or the issue turned out to be noise. Say which in a comment, because a cancelled issue that traced to something is a signal that the canon changed. |

**Prefer git-driven status.** The Linear ID rides in the branch name, so the GitHub integration moves the issue on open, merge and close. Direction is git to Linear, unidirectional, with no loop to maintain. Moving a status by hand is for the cases the integration cannot see.

**The automation is configured to this mapping, which is not Linear's default.** Under the team's pull-request automations, a PR opened moves the issue to **In Review** and a PR merged moves it to **Done**. Linear ships with "opened moves to In Progress", and that is wrong here: In Progress means the two windows are working, and a PR is open only after they finished. Nothing moves an issue **into** In Progress automatically, because starting work is a human act.

**The GitHub side is configured to have one tracker, not two (2026-08-03).** The repository has **Issues, Projects and Wiki turned off**, and each for a reason worth keeping. Issues would be a second inbox that nobody triages, on a public repository, colliding with the rule that an issue exists only when it traces to the canon. Projects would be a second board, and status in two places diverges every time. The Wiki is the worst of the three, because documentation duplicated there does not fail loudly, it simply ages against the foundation in silence, which is the exact drift the fan-out rule exists to prevent. **The revisit trigger for Issues is the first real users**, the same trigger the observability backend carries: today that channel has nobody on the other end, and a support surface with no support behind it is worse than none.

**GitHub Issues Sync stays off, and it is a different feature from the one above.** It is a two-way sync that creates and mirrors issues, titles, descriptions, statuses and comments between GitHub and Linear. Turning it on would put the contract and the execution state on both sides of a loop, which is exactly what the boundary at the top of this document forbids. The PR linking is unidirectional and is all this project wants.

## Definition of done

An issue is Done when **all** of these hold. Anything less is In Review at best.

1. The behaviour the acceptance criteria describe is proven by tests written **before** the implementation.
2. `just check` is green, which is the same gate set CI runs (`dev-workflow` section 2).
3. The PR is merged to `main` through the normal flow, never a local merge.
4. If the issue was an **ADR**, the document exists in `specs/adr/` and the code that follows it cites it.
5. If the work **closed a decision**, its fan-out is finished: the foundation, the requirements, `CLAUDE.md`, the path-scoped rules and one line in `log.md`. A decision closed in code and not in the canon is drift with a green build on top of it.

## Priority, with meanings rather than vibes

- **Urgent** blocks other issues in the same project, or it is a decision that a later artifact is expensive to take back (an ADR before its migration).
- **High** is on the critical path of the project's exit criterion.
- **No priority** is the default and carries no shame. Most issues sit here.

Priority is not a schedule. Release ordering deliberately lives outside the specs, so priority orders the work and never promises a date.

## Working with more than one person

- **Assign an issue only when work starts on it.** An assignee on an untouched issue is a reservation, and reservations rot.
- **One issue In Progress per person.** With the two-window protocol, one person already holds two contexts; a second issue on top of that is how a half-finished branch is born.
- **Parallel work runs in git worktrees**, one per issue, so two features progress without stepping on each other. The tight specs and the generated contracts are what let that not diverge.
- **Collective ownership holds**: anybody may touch any part, and the canon plus the gates are what keep that safe. Nobody owns a folder.
- **Review is on the PR, never in Linear.** A comment in Linear that reviews code is a review nobody will find again.

## Bugs and unplanned work

A bug is an issue like any other and it still needs a trace, which for a bug is the **invariant or requirement it violates**. A defect that violates nothing identifiable is a signal that a requirement is missing, and the honest move is to write the requirement first.

Label it `Bug`, put it in the project whose surface it broke, and give it a failing test before a fix. No fix without a root cause, which is what the `systematic-debugging` skill exists for.

## Projects and milestones

- **A project exists because a decision in the canon created it**, never the reverse. The first one exists because foundation OQ-4 closed and named the slice.
- **A project carries its exit criterion in the description**, in pass/fail terms, so "done" is a checked state rather than a feeling.
- **Milestones are the execution phases of that project**, and their descriptions carry which requirements they discharge.
- **A spike is its own project**, with the gate written as the exit criterion, because a spike's output is a decision and throwaway code rather than a feature.
- **Perennial work is a label**, never a dated project.
- A **status update** on the project is where the honest state goes when it moves, including "this is blocked on a question that belongs to a person".

## XP, adapted rather than performed

The method is XP-shaped and three of its practices are deliberately replaced, which is worth stating so nobody re-adds the ceremony.

**Kept as-is.** Test-first, continuous integration on every push, collective ownership, small and frequent integration, refactoring under green, and a sustainable pace.

**Replaced.** The **planning game** is replaced by the closed canon: scope is decided in the foundation and the requirements before it reaches a tracker, so there is no card negotiation and no velocity to bargain with. **Pair programming** is replaced by the **two-window protocol**, where one pass writes the failing test as behaviour and a different pass implements it, which buys the same independent-check property without two people on one keyboard. **The on-site customer** is the embedded domain engineer, and the questions that belong to him are marked as open in the canon rather than guessed at in a planning session.

**Dropped on purpose.** Story points, velocity, iteration commitments, and burndown. All four are forecasting instruments for a scope that is still being negotiated, and this scope is closed.

## Cycles

**Off, deliberately.** The backlog is continuous, and a cycle boundary on a three-person team with a closed scope adds a ritual without adding information.

Turn a light one-week or two-week cycle on only when a **specific** symptom appears: work in progress piling up with nothing finishing, or a third and fourth person needing a shared rhythm to coordinate. Turning it on is a decision with a reason, and the reason goes in a comment on the project.

## What never enters Linear

- The contract. A requirement, an acceptance criterion or an architecture decision lives in git, and a copy in an issue description is a copy that drifts. **Cite the identifier, quote the criterion, and let git hold the reasoning.**
- Status in git. The reverse of the same rule.
- Secrets, and anything a public repository would not carry.
- An issue that traces to nothing, however sensible it sounds. Close the decision first.

## Structure

- Workspace: the owner's **personal** workspace (changed 2026-08-03 from a dedicated Mapsift workspace). What keeps the work Linear out is the **team-scoped API key**, not the workspace boundary.
- Team: one, "Mapsift", prefix MAP. Do not split into frontend/backend teams at this size.
- Projects: areas of delivery with a clear start and end (sync engine, rendering and layers, vector editing, environmental analysis, auth and multi-tenant, tile pipeline). Perennial work (infra, observability) is a label or a Maintenance-status project, not a dated project.
- Milestones (within a project): the execution phases of that project.
- Issues: the unit of work. ID MAP-..., matching the spec in git. Label by layer (domain, adapter, api, frontend, sync, geo, infra) to recover the per-layer view.
- Cycles: optional. Start without them (continuous backlog); enable a light 1-2 week cycle only if cadence is missing.
- Initiative: optional. "Mapsift v1" grouping the delivery Projects, when a roadmap view is wanted.

## Status flow

- Status lives only in Linear, never in the spec.
- Prefer git-driven status: reference the issue ID in the PR or commit so the GitHub integration moves the issue automatically on open/merge/close. Direction is git → Linear, unidirectional, no loop to maintain.

## MCP isolation (how Linear is connected)

- The Linear MCP is a Claude Code local-scope server configured in the Mapsift project directory, never a Claude.ai account connector. It authenticates with a **personal API key scoped to the Mapsift team**, sent as `Authorization: Bearer`, which the Linear MCP accepts in place of the interactive OAuth flow. The key lives in `~/.claude.json` on this machine only, under the `/home/johnsilverio/Documents/projects/mapsift` project entry.
- **Two Linears coexist on this machine and they are isolated by living in different files**, which is worth knowing before touching either. Mapsift is **local scope**, in `~/.claude.json`, keyed by the project directory. The work Linear (Vale Verde, in the Ecobalance repository) is **project scope**, in a `.mcp.json` inside that repository. There is deliberately **no user-scope MCP server**, since that is the only scope that would apply everywhere at once.
- **The runbook, because the rule without the commands is a rule somebody executes wrong in a hurry.** Always `cd` into the Mapsift directory first, and always pass `-s local` explicitly: without it, `remove` deletes from whichever scope it finds, which from the wrong directory means eating another repository's `.mcp.json`.

```bash
cd ~/Documents/projects/mapsift
claude mcp remove linear -s local
claude mcp add --transport http linear https://mcp.linear.app/mcp \
  --header "Authorization: Bearer <key>" -s local
history delete --contains lin_api   # fish, because the command above is now in the history
```

- **Two traps that cost time on 2026-08-03.** The header value must carry the `Bearer ` scheme; without it the server answers 401 with `invalid_token`, which reads like a bad key and is not. And `claude mcp get <name>` **prints the header value in clear**, so it leaks the key into whatever transcript is running; use `claude mcp list`, which shows the status and not the secret.
- Tool permissions live in `.claude/settings.local.json`, which is gitignored because the local layer is per machine and is bound to this machine's OAuth session. Reads and the writes this workflow needs (`save_issue`, `save_project`, `save_milestone`, `save_comment`, `save_document`, `create_issue_label`) are allowed; everything destructive (`delete_*`, `merge_diff`, `submit_diff_review`) still prompts, deliberately, because an issue that does not trace to the canon is noise and a deletion is not recoverable from git.
- Consequence: it does not appear in Claude.ai web, and does not appear on another machine logged into the same account. This is deliberate isolation, do not move it to account scope.
