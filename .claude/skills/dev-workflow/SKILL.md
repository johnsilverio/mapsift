---
name: dev-workflow
description: Use when creating branches, committing, opening pull requests, or otherwise contributing changes to the Mapsift project. Covers the branch convention, the pre-commit gate, commit conventions, code generation, and the CI and branch-protection flow.
---

# Contribution workflow

How a change lands in the Mapsift monorepo. **This skill is the single source of truth for the branch name,
the commit format and the PR flow**; the `github-workflow` agent, the `/commit` and `/pr` commands and the
`ticket` skill execute this procedure and must not define a second one. Concrete commands and examples are in
`reference.md`. The project rules this builds on live in the root `CLAUDE.md`, the foundation
`specs/mapsift-foundation.md` and `specs/adr/0001-architecture-baseline.md`.

## 1. Branch

Branch from `main`. Format: `{initials}/{MAP-id}-{short-topic}`, or `{initials}/{short-topic}` when the work
has no ticket. The ticket ID rides in the branch name so the GitHub integration moves the Linear issue
automatically on open, merge and close (git to Linear, unidirectional; see the `linear-workflow` skill).

```bash
git switch main && git pull
git switch -c js/MAP-12-offline-op-queue
```

## 2. Pre-commit gate (never commit on red)

Run `/quality-gate` before every commit. It is the one definition of the checks and mirrors the CI gates of
ADR-0001 section 6, so a partial list copied into another file is a gate that lies. It covers, per language
touched:

- **Python** (`apps/api`): ruff check, ruff format check, mypy `--strict` with django-stubs, pytest.
- **Rust** (`libs/core`): clippy, fmt check, cargo test.
- **Angular** (`apps/web`, `libs/ui`): `ng lint`, `ng build` (the strict tsc runs there), `ng test
  --watch=false`. The linter is its own CI gate, so a green build alone is not enough.
- **Generated contracts**: regenerate both directions (OpenAPI to TypeScript, Rust core types to TypeScript)
  and fail on any diff. A stale contract is a red build, never a silent drift.

Prefer the `justfile` recipes (`just lint`, `just typecheck`, `just test`, `just contracts`), because
ADR-0001 section 3 makes the container the source of truth for running and the host toolchain the one for
authoring. Always run Angular unit tests through `ng test`, never the `vitest` CLI directly: only the
`@angular/build:unit-test` builder resolves the `@mapsift/ui` tsconfig path alias.

## 3. Generate, never hand-write

Every framework-owned file is created by its own generator and then edited, because the generator writes what
the installed version produces and a model writes what it remembers.

```bash
ng g c features/<feature>/<name>     # Angular: standalone, OnPush, separate template and styles
ng g s core/<area>/<name>
python manage.py startapp <name>     # Django
python manage.py makemigrations <app>
cargo new / cargo add                # Rust
```

Never pass `--inline-template` or `--inline-style`, and never hand-write a migration.

## 4. Commits

Conventional Commits, atomic, message in English, imperative mood, one purpose per commit (if the subject
needs an "and", it is two commits). Types: `feat`, `fix`, `refactor`, `test`, `docs`, `style`, `chore`,
`perf`. Format: `type(scope): short description`, scope optional. Reference the Linear ID (`MAP-123`) when the
work traces to a ticket.

**Do NOT add any AI/Co-Authored-By attribution trailer**, to a commit, a PR body, or a release. This holds in
every skill, command and agent in this repository, with no exception.

Stage explicit paths, never `git add -A`.

## 5. Pull request flow

1. Push the branch and open a PR to `main` (`/pr` does this with its preconditions).
2. Wait for the repository's required CI checks (`gh pr checks --watch`).
3. Merge only when they are green. Never push to `main` directly, never force-push anything.

There is no path in this project where a branch reaches `main` without a PR and green checks. A local merge
into `main` bypasses the gates ADR-0001 section 6 exists to enforce.
