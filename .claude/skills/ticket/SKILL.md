---
name: ticket
description: Work on a Linear ticket end-to-end: read the ticket, trace it to the canon, explore the codebase, branch, implement test-first, run the quality gate, update the ticket, open a PR. Use when the user provides a ticket ID to implement. Triggers on requests like "/ticket MAP-123", "work on this ticket", "implement MAP-123".
---

# Ticket workflow

Work the ticket ID the user provided. The procedures this composes are owned elsewhere and are not restated
here: `linear-workflow` for anything touching Linear, `dev-workflow` for the branch, gate, commits and PR.

## 1. Read the ticket

Fetch it with the Linear MCP tools: title, description, acceptance criteria, linked issues, comments.
Summarize what has to be done, the acceptance criteria, and any blocker or dependency.

## 2. Trace it to the canon before writing anything

An issue is only legitimate work if it traces to `specs/mapsift-foundation.md`, `specs/PRD.md`, or a spec in
git (`linear-workflow`). Find that trace and cite it: the invariant (I1 to I11), the C-test, the PRD
requirement (a T, M, S, N or U item). git owns the contract, Linear owns execution state.

If the ticket does not trace, or asks for something the foundation left open (an OQ-N), or asks to create
something ADR-0001 section 8 forbids for now (`apps/sync`, `apps/desktop`, `apps/mobile`, the sync internals,
a dependency-gated ADR), stop and say so instead of implementing a guess.

## 3. Explore the codebase

Find the related code, understand the current implementation, and identify the files that change. Note which
deployable or library the work touches, and remember that nothing in `apps/` imports from another `apps/`.

## 4. Branch

Per `dev-workflow`:

```bash
git switch main && git pull
git switch -c {initials}/MAP-123-short-topic
```

## 5. Implement test-first, in two passes

`CLAUDE.md` and foundation section 14 require the two-window protocol: one pass writes the failing tests as
behaviour, another implements the minimum to green using those tests as a contract. Do not write the test and
its implementation in the same pass, and never weaken a test to reach green. The `tdd-implementer` agent is
the implementation window for Angular work.

Generate every framework file with its own generator and then edit it (`ng g ...`, `manage.py startapp`,
`manage.py makemigrations`, `cargo add`). Make incremental commits, one purpose each.

## 6. Run the quality gate

Run `/quality-gate`. It covers every language the change touched (Python, Rust, Angular) plus the
generated-contract freshness check, which a Python-only list would miss in a polyglot monorepo. Never commit
on red.

## 7. Update the ticket

Status lives only in Linear, never in the spec. Move the issue as the work moves, add a comment for a real
blocker or decision, and let the git integration move the status on PR open and merge where it can.

## 8. Open the PR

Use `/pr`. Reference the ticket ID in the body so the GitHub-to-Linear automation links them. **No
AI/Co-Authored-By attribution trailer**, in the commits or the PR body.

## 9. If you find an unrelated bug

Do not fold it into this ticket. Create a new issue only if it traces to the canon, link it, note it in the
PR description, and carry on with the original task.
