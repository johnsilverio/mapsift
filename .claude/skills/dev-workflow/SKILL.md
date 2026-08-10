---
name: dev-workflow
description: Use when creating branches, committing, opening pull requests, or otherwise contributing changes to the Mapsift project. Covers the branch convention, the pre-commit gate, commit conventions, code generation, and the CI and branch-protection flow.
---

# Contribution workflow

How a change lands in the Mapsift monorepo. **This skill is the single source of truth for the branch name,
the commit format and the PR flow**; the `github-workflow`, `commit`, `pr` and `ticket` skills execute this
procedure and must not define a second one. Concrete commands and examples are in
`reference.md`. The project rules this builds on live in the root `CLAUDE.md`, the foundation
`specs/mapsift-foundation.md`, `specs/adr/0001-architecture-baseline.md` and
`specs/adr/0008-development-workflow-and-tracking.md`.

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

**One line. That is the whole message, and a body is the exception rather than the short version.** A subject
under about 72 characters, and nothing else unless the change genuinely cannot be understood without a note
that exists nowhere else, which is rare.

The reason is not brevity for its own sake. **A commit body almost always repeats what the Linear card and
the pull request already say**, and a fact stored in three places is a fact that drifts in two of them. The
issue carries the trace and the acceptance, the PR carries the reasoning, the measurements and the review
notes, and both of those can be edited when they turn out to be wrong. A commit message cannot, and it is
read in a one-line log far more often than in full. So the commit says **what changed**, and the other two
say why and how well.

**Do NOT add any AI/Co-Authored-By attribution trailer**, to a commit, a PR body, or a release. This holds in
every skill, command and agent in this repository, with no exception.

Stage explicit paths, never `git add -A`.

## 5. Pull request flow

1. Push the branch and open a PR to `main` (`/pr` does this with its preconditions).
2. Wait for the repository's required CI checks (`gh pr checks --watch`).
3. Merge only when they are green. Never push to `main` directly.

There is no path in this project where a branch reaches `main` without a PR and green checks. A local merge
into `main` bypasses the gates ADR-0001 section 6 exists to enforce.

**When `main` moves under an open pull request, and it always does** (added 2026-08-10). The ruleset
requires branches to be up to date before merging, so every merge puts every other open pull request
behind. **`reference.md` under "Repository protection" already answers the ordinary case and this section
does not restate it**: the branch is `BEHIND` and clean, and the fix is **Update with rebase**
(`gh pr update-branch --rebase`), never the plain update, which would put a merge commit inside the branch
and fight the required linear history.

**The case it does not answer is a branch that goes `CONFLICTING`**, where no server-side update can
resolve anything. There the branch is rebased locally and pushed with **`git push --force-with-lease`**.
The lease is the whole point: unlike `--force`, it **refuses the push if the remote moved since your last
fetch**, so it cannot overwrite somebody else's work. **Never force-push `main`, and never force-push a
branch somebody else has pulled.**

**This is legal as well as safe, and it was measured rather than assumed** (2026-08-10,
`gh api repos/johnsilverio/mapsift/rulesets/<id>`): the ruleset's conditions are
`include: ["~DEFAULT_BRANCH"]` with an empty exclude, so `non_fast_forward`, the rule that blocks force
pushes, **covers `main` and no feature branch**. This paragraph replaced a blanket "never force-push
anything" that had no answer for a moved base; the alternatives it left were worse rather than safer, since
merging `main` into the branch leaves the merge commit the `--rebase` merge then has to replay, and closing
the pull request to recreate the branch breaks the one-issue-one-pull-request rule of ADR-0008 section 6 to
avoid running one command.

**Merge with rebase, and the exception is named.** `gh pr merge --rebase --delete-branch` is the default,
because this project writes atomic commits with one purpose each and rebase replays every one of them onto
`main` intact, which is the whole point of writing them that way. **Squash** is for the branch that
accumulated noise (a typo fix, a review correction), where one clean commit is more honest than four; it
replaces the messages with the PR title and body, so it is the wrong tool for a branch whose commits were
written properly. **A merge commit is never used**, and the ruleset below blocks it. Note that rebasing
rewrites the commits, so the hash on `main` differs from the hash on the branch; the content and the message
do not.

**The flow above is enforced by a repository ruleset, not by discipline.** Its exact configuration, the two
places where it departs from the obvious setting, and the caveat that it stops being enforced if this
repository ever goes private on a free plan, are in `reference.md` under "Repository protection".
