---
allowed-tools: Bash(sed *)
name: linear-workflow
description: "Use when creating, structuring or updating Mapsift work tracking in Linear, or when deciding whether a piece of work belongs in Linear at all. Covers the git-versus-Linear boundary (contract versus execution state), the Workspace, Team, Project, Milestone and Issue structure for Mapsift, when an issue may be created, the GitHub status automation, and the local-scope MCP isolation rule. Trigger before touching any Linear issue, project, milestone or cycle."
---

# Linear workflow (Mapsift)

Ratified in `specs/adr/0008-development-workflow-and-tracking.md`. This file is the enforceable
restatement; the ADR is the decision, and where they disagree the ADR wins.

## The decision this skill restates, injected

This is the Decision of `specs/adr/0008-development-workflow-and-tracking.md`, loaded from disk. **This
skill restates it and never decides**; where the two disagree, the ADR wins.

!`sed -n '/^## Decision/,/^## Consequences/p' specs/adr/0008-development-workflow-and-tracking.md`

---

## The boundary (read this first)

**git owns the contract; Linear owns execution state; the identifier bridges them.**

- git (foundation, ADRs, the per-task spec) is the what and the technical how. Changed through a reviewed
  commit.
- Linear (project, milestone, issue, status, assignee, discussion) is the state of execution. Changes
  constantly.
- `MAP-123` is the **only field in both**, and it never carries state, so it never diverges.
- Never edit in Linear something that is a git truth (a decision, an acceptance criterion). Never put status
  in git. There is no two-way sync, by design.
- **A decision is never made in a Linear comment.** If a discussion there changes what the system does, it
  goes back into the foundation or an ADR before code follows it.

## When an issue may be created

- Only when it traces to the canon: an invariant, a foundation decision, an ADR, a PRD requirement when the
  PRD exists, or an open question that has been answered. **Cite the trace in the issue.** If you cannot name
  one, the issue is noise and the answer is to close the decision first, in git.
- **An open question is not an issue.** It lives in foundation section 13 with an owner and an exit
  criterion, and becomes an issue when it is answered and there is work to do.

## What one issue is (`specs/tasks/README.md`)

- **One behaviour, one requirement, one pull request.** If the title needs an "and", it is two issues.
- **Written as an outcome, never as a task list.** "A feature created offline syncs without an identifier
  collision" is an issue; "work on sync" is a project; "add a column" is a step, and steps do not get issues.
- **Trace and acceptance are copied from the requirement, never invented.** Acceptance written at
  issue-creation time is the tell that the requirement is soft: sharpen it in `PRD.md` first.
  **The issue and the task spec diverge here, and only here** (ADR-0008 section 9, 2026-08-14): an **issue**
  keeps the copy, because it is read standalone in a tracker by a human with no canon open. A **task spec**
  carries the **delta** instead, because it is read beside the canon and a copy there is the fourth of seven
  recorded orchestrator defects waiting to happen.
- **Sub-issues are for a genuine parent and child.** Phases are milestones.
- **No estimates and no story points.** Priority orders the work and never promises a date: **Urgent**
  blocks other issues or is a decision a later artifact is expensive to take back, **High** is on the
  critical path to the project's exit criterion, **no priority** is the default and carries no shame.
- **A spike is its own project** with its gate as the exit criterion, never a normal issue.
- **A project carries its exit criterion in its description**, in pass or fail terms, so done is a checked
  state rather than a feeling.
- **The assembled task lives in git** at `specs/tasks/MAP-<n>-<slug>.md`, written at pickup rather than at
  backlog creation. `specs/tasks/README.md` is its shape. **Building the backlog itself is the `backlog`
  skill**, which does the requirement analysis, the decomposition, the sizing and the sequencing before
  anything reaches Linear.

## Definition of done

An issue is Done when **all** of these hold. Anything less is In Review at best.

1. The behaviour its acceptance describes is proven by tests written **before** the implementation.
2. The gate is green, the same set CI runs (`specs/testing.md` section 8).
3. The pull request is merged to `main` through the normal flow, never a local merge.
4. If the work produced an **ADR**, the document exists and the code that follows it cites it.
5. If the work **closed a decision**, its fan-out is finished. A decision closed in code and not in the
   canon is drift with a green build on top of it. Use the `fan-out` skill.

## Bugs and unplanned work

A bug is an issue like any other and it still needs a trace, which for a bug is **the invariant or the
requirement it violates**. A defect that violates nothing identifiable is a signal that a requirement is
missing, and the honest move is to write the requirement first.

Label it, put it in the project whose surface it broke, and **give it a failing test before a fix**. No fix
without a root cause, which is what `systematic-debugging` exists for.

## Structure

- **Workspace:** the owner's **personal** workspace. It moved there deliberately, and the isolation is
  stronger rather than weaker for it: an **API key scoped to the Mapsift team** is a wall, while remembering
  which workspace you are in is discipline.
- **Team:** Mapsift, prefix **MAP**. Do not split into frontend and backend teams at this size.
- **Projects** are delivery areas with a start and an end. Perennial work is a label, never a dated project.
  A **spike is its own project** with its gate as the exit criterion, never a normal issue, because an issue
  whose definition of done is "we learned something" corrupts the definition of done for everything else.
- **Milestones** inside a project are its execution phases.
- **Labels:** `domain`, `api`, `sync`, `core`, `frontend`, `geo`, `infra`, `adr`, which recover the
  cross-cutting view the project structure loses.
- **Cycles:** off. Enable a light cadence only if the flow proves to need one.

## Status flow

Status lives only in Linear, and **git moves it**, never a human clicking:

- The branch is created **from the Linear issue**, so the identifier is in the name and the link is automatic.
- Moving an issue to In Progress is a **human act**, performed through the MCP at pickup on the owner's OK
  (ADR-0008 section 4, note of 2026-08-06); an opened pull request moves it to In Review; a merge to the
  default branch moves it to Done. Nothing moves an issue into In Progress automatically.
- Use a **closing magic word** plus the identifier when the pull request finishes the issue, and the bare
  identifier when it only touches it.
- A change spanning both stacks is **one** pull request citing `MAP-123`, and it carries the closing word
  when it finishes the issue (ADR-0008 section 6).

## MCP isolation

The Linear MCP is a Claude Code **local-scope** server configured inside the Mapsift working tree,
authenticated by a **personal API key scoped to the Mapsift team**, never an account-level connector and
never a Claude.ai account connector. Local scope is keyed by the **project directory**, which is what keeps
two Linear accounts on one machine from bleeding into each other: authenticate the personal one only in this
directory. **Do not use the user scope**, where a known bug ties it to project paths and a child project can
zero the parent.

Consequences worth knowing rather than rediscovering. It does not appear in Claude.ai web and does not
appear on another machine logged into the same account, which is the isolation wanted: a borrowed account
cannot touch the owner's Linear.

**Two traps, both paid for once.** The authorization header needs the `Bearer ` scheme or Linear answers
401 with a message that reads like a bad key. And `claude mcp get` **prints the key in clear** into the
transcript, while `claude mcp list` does not.

What `list_teams` returns from this working tree is the Mapsift team and nothing else, which is the check
that the scoping actually holds.

## What Claude Code does and does not do here

Reading the issue and its trace, writing progress comments and updating execution state through the MCP is
the whole of it. **Do not adopt a webhook bridge that turns an issue assignment into an autonomous run that
opens a pull request**: it collapses the two-window protocol into one pass, which is the exact failure the
protocol exists to prevent. The gate for reopening that is in `CLAUDE.md` "Process & tracking".
