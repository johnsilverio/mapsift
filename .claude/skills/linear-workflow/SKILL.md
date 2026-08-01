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

Verified 2026-07-30: the MCP is connected, there is **one team, "Mapsift"**, and there are **zero projects**.
The backlog has not been created yet. The first Linear work is therefore structural (the delivery Projects and
the two spike Projects, then their Milestones), and it can only start once the work it would track traces to
the canon: the PRD's own gap list (section 10) and the pre-architecture order in session-handoff section 0 are
where that comes from, not from a brainstorm.

## Structure

- Workspace: the dedicated Mapsift workspace, separate from any work or personal workspace.
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

- The Linear MCP is a Claude Code local-scope server configured in the Mapsift project directory, never a Claude.ai account connector. The OAuth token lives in ~/.claude.json on this machine only.
- Tool permissions live in `.claude/settings.local.json`, which is gitignored because the local layer is per machine and is bound to this machine's OAuth session. Reads and the writes this workflow needs (`save_issue`, `save_project`, `save_milestone`, `save_comment`, `save_document`, `create_issue_label`) are allowed; everything destructive (`delete_*`, `merge_diff`, `submit_diff_review`) still prompts, deliberately, because an issue that does not trace to the canon is noise and a deletion is not recoverable from git.
- Consequence: it does not appear in Claude.ai web, and does not appear on another machine logged into the same account. This is deliberate isolation, do not move it to account scope.
