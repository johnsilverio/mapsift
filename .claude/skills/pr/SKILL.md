---
name: pr
description: Push the current branch and open a pull request against the base, then point at the required CI checks. Use when the user asks to open a pull request, push the branch, or ship the work for review. Triggers on "/pr".
argument-hint: "[base-branch, default main]"
disable-model-invocation: true
---

Open a pull request for the current branch. Follow `CLAUDE.md`, the `dev-workflow` skill and the
`linear-workflow` skill. Base branch: $ARGUMENTS (default `main` when empty).

**ADR-0001 section 1 decided one repository and the move has not run**, so `apps/web` and the tree root are still
separate repositories, and only `apps/web` has a remote. Run `git rev-parse --show-toplevel`, say which
repository the pull request belongs to and which stacks it touches, before doing anything
else, because opening it against the wrong remote is a mistake nobody notices until review.

Resolve the base to `$ARGUMENTS` or `main`, and the current branch with `git rev-parse --abbrev-ref HEAD`.

## 1. Validate preconditions (stop on any failure)

Run `git fetch origin` first so the comparisons are accurate, then check all of:

- **A remote exists.** `git remote -v` must not be empty. The tree root has no remote yet and must not gain
  one until its history is recreated, because the first commit carries a production dump (session-handoff
  section 0). If there is no remote, stop and say so.
- Current branch is not the base. If on `main`, stop: branch from `main` first. **Main never receives a
  direct push.**
- There are commits ahead of the base: `git log origin/<base>..HEAD --oneline` lists at least one.
- No pull request exists for this branch: `gh pr list --head <branch>` returns nothing. If one exists, show
  its URL rather than opening a duplicate.
- **The gate is green.** Run `/quality-gate` if it has not run since the last commit. A pull request opened
  on red wastes a review.

## 2. Push the branch

```bash
git push -u origin <branch>
```

Never force-push, and never push to `main`.

## 3. Open the pull request

```bash
gh pr create --base <base> --fill
```

`--fill` derives the title and body from the commits; `/pr-summary` writes a better body when the change
deserves one.

**Two rules that are not optional.** **No AI or assistant attribution trailer** anywhere in the body
(ADR-0001 section 20). And if the work traces to a Linear issue, **reference `MAP-123` in the body** so the
native GitHub and Linear automation links them: a pushed branch moves the issue to In Progress, an opened
pull request to In Review, and a merge to `main` to Done, **git to Linear, one direction** (the `linear-workflow` skill
sections 4 and 9).

Use a **closing magic word** plus the identifier only when this pull request finishes the issue, and the bare
identifier when it merely touches it.

## 4. The crossing case: one pull request, not two

**Revised 2026-08-04 (ADR-0001 section 1, the one-pull-request rule).** A change spanning both stacks is **one
pull request** carrying the serializer, the regenerated OpenAPI schema, the regenerated TypeScript types and
the component that consumes them, verified in one CI run. Drift is prevented rather than detected, so the
snapshot, the fixed ordering and the scheduled drift check are retired.

**What the old rule said, so a stale memory recognises itself:** two pull requests in a fixed sequence, the
api first because it owned the schema, then the web bumping the snapshot it consumed and regenerating its
types, both citing the same identifier with only the second closing it. **That is retired.** It bought the
property that the web is never broken by a merge in the api, which was deferral rather than protection: the
breakage existed either way and the shape moved it from the pull request that caused it to whichever week
somebody bumped the snapshot.

**What survives unchanged:** the api owns the schema and CI fails when regenerating it produces a
difference; the web's types are generated from that same file and CI fails on a difference there too; and
neither deployable imports code from the other.

## 5. Point at the required checks

```bash
gh pr checks --watch
```

Merge only when the required checks are green. A red build is not merged and is not overridden.
