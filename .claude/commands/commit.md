---
description: Run the pre-commit gate and create atomic Conventional Commits (does not push).
argument-hint: "[optional scope or message hint]"
---

Create one or more commits for the staged work in the Mapsift monorepo. Follow the project rules in `CLAUDE.md`, the foundation in `specs/mapsift-foundation.md`, and the `dev-workflow` skill. Optional hint for scope or wording: $ARGUMENTS

## 1. Pre-commit gate (never commit on red)

Run `/quality-gate`, which is the single definition of the per-language checks and mirrors the CI gates of
ADR-0001 section 6. Do not duplicate a partial list here: a gate that drifts from the one CI runs is worse
than no local gate, because it reports green on a change CI will reject.

The gate runs through the `justfile` recipes (`just lint`, `just typecheck`, `just test`, `just contracts`),
because ADR-0001 section 3 makes the container the source of truth for running. It covers, per language
touched: ruff plus mypy `--strict` plus pytest on `apps/api`; clippy plus fmt plus tests on `libs/core`;
`ng lint` plus `ng build` plus `ng test` on `apps/web` and `libs/ui`; and the generated-contract freshness
check in both directions.

If any check fails, STOP: report what failed and do not commit. Never commit on red.

## 2. Inspect what is staged

```bash
git status
git diff --staged
```

Read the staged changes to understand their purpose. If nothing is staged, stop and say so. Note: only staged changes are committed here; this command does not stage files for you.

## 3. Compose an atomic Conventional Commit message (English)

One purpose per commit. Format: `type(scope): short description`, where type is one of `feat`, `fix`, `refactor`, `test`, `docs`, `style`, `chore`, `perf`; scope is optional. Subject in English, imperative mood, lower case, no trailing period. If the work traces to a Linear ticket, you may reference its ID (e.g. `MAP-123`).

If the subject would need an "and" to describe everything staged, that is two (or more) commits: split the staged changes by purpose and plan one message per purpose.

**Do NOT add any AI/Co-Authored-By attribution trailer.**

## 4. Create the commit(s)

Create each commit with `git commit -m "type(scope): short description"`. When splitting, stage each purpose separately (for example `git restore --staged <paths>` then `git add <paths>`) so every commit contains only its own changes. Do NOT push; opening a PR is the `/pr` command.
