---
name: pr-summary
description: Write a pull request body for the current branch. Use when the user wants a PR description, a summary of the branch changes, or a body prepared before opening the PR. Triggers on requests like "summarize my changes", "write a PR description", "what changed in this branch", "/pr-summary".
---

# PR summary

Write the pull request body for the current branch.

Note that `/pr` opens PRs with `gh pr create --fill`, which derives the title and body from the commits. Use
this skill when the change needs more than the commits say: several commits under one purpose, a decision
worth recording, or a reviewer who needs the trace to the spec.

## 1. Analyze the branch

```bash
git log main..HEAD --oneline
git diff main...HEAD --stat
```

## 2. Write the body

```markdown
## Summary

One to three lines on what changed and why.

## Traces to

The requirement this implements: a PRD item (T, M, S, N, U), a C-test, an invariant, or the ADR that
fixed the shape. Reference the Linear ID (MAP-123) so the GitHub integration links the issue.

## Changes

The significant changes, grouped by deployable or library (`apps/api`, `apps/web`, `libs/core`, `libs/ui`).

## Test plan

- [ ] The behaviour is pinned by a test written before the code
- [ ] `/quality-gate` green for every language touched
- [ ] Generated contracts regenerated, no diff
```

Keep it factual. If something in the change is a known compromise or leaves an open question, say so
explicitly rather than letting a reviewer discover it.

**Do NOT add any AI/Co-Authored-By attribution trailer** to the PR body.
