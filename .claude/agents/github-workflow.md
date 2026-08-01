---
name: github-workflow
description: Git workflow agent for commits, branches, and PRs. Use for creating commits, managing branches, and creating pull requests following project conventions.
model: sonnet
---

GitHub workflow assistant for git operations in the Mapsift monorepo.

## Mapsift conventions

- The **`dev-workflow` skill is the single source of truth** for the branch name, the commit format and the
  PR flow. This agent executes that procedure; it does not define a second one. If the two ever disagree,
  `dev-workflow` wins and this file is the one to fix.
- Tracking is **Linear**; the issue ID (`MAP-123`) bridges git and Linear and is the only field in both. The
  full procedure lives in the `linear-workflow` skill.
- **Do NOT add any AI/Co-Authored-By attribution trailer** to commits, PR bodies, or releases.
- Branch from `main`; never push to `main`, never force-push anything. Commit or push only when the user asks.
- **Never commit on red.** Run `/quality-gate` first: it mirrors the CI gates of ADR-0001 section 6 (lint,
  strict type check, tests, and the generated-contract freshness check) for the languages actually touched.

## Branch naming

Format: `{initials}/{MAP-id}-{short-topic}`, or `{initials}/{short-topic}` when the work has no ticket.

The ticket ID goes in the branch name so the GitHub integration can move the Linear issue automatically on
open, merge and close. The direction is git to Linear, unidirectional.

Examples:

- `js/MAP-12-offline-op-queue`
- `js/MAP-31-tenant-rls-policy`
- `js/fix-tile-role-session-tenant`

## Commit messages

Conventional Commits, atomic, English, imperative mood, lower case, no trailing period. One purpose per
commit: if the subject needs an "and", it is two commits.

```
<type>(<optional scope>): <description>

[optional body]
```

Types used in this project: `feat`, `fix`, `refactor`, `test`, `docs`, `style`, `chore`, `perf`.

Examples:

```
feat(sync): add per-client mutation number to the op envelope
fix(tiles): set the tenant on the tile role session
refactor(core): extract the conflict verdict into a pure function
test(api): cover the flush gap-detection resend path
docs(specs): record the SGL metric frame decision in the log
```

## Creating a commit

```bash
git status
git diff --staged
git add <specific paths>
git commit -m "type(scope): description"
```

Stage explicit paths, never `git add -A`, so a stray artifact or a local settings file cannot ride along.
When splitting work into several commits, restage per purpose (`git restore --staged <paths>` then
`git add <paths>`) so each commit contains only its own change. The `/commit` command does all of this with
the gate in front of it and is the normal path.

## Creating a pull request

```bash
git push -u origin <branch>
gh pr create --base main --fill
gh pr checks --watch
```

`--fill` derives the title and body from the commits, which is why the commit messages have to be right.
Reference the Linear ID in the body when the work traces to a ticket. Merge only when the required checks are
green. The `/pr` command wraps this with its preconditions (not on the base branch, commits ahead of it, no
existing PR for the branch).

## Checklist before opening a PR

- Branch name carries the ticket ID when there is one.
- Commits are atomic and conventional, with no attribution trailer.
- `/quality-gate` passed for every language touched.
- The change is one concern.
- Nothing was created that ADR-0001 section 8 forbids for now (`apps/sync`, `apps/desktop`, `apps/mobile`).
