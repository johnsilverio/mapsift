---
name: pr
description: Push the current branch and open a pull request against the base, then point at the required CI checks. Use when the user asks to open a pull request, push the branch, or ship the work for review. Triggers on "/pr".
argument-hint: "[base-branch, default main]"
disable-model-invocation: true
---

Open a pull request for the current branch. Follow `CLAUDE.md`, the `dev-workflow` skill and the
`linear-workflow` skill. Base branch: $ARGUMENTS (default `main` when empty).

**This is one repository with one remote and a protected `main`** (ADR-0001 section 1). Say which branch
you are on and which stacks the diff touches before doing anything else, because a pull request whose title
promises one stack and whose diff carries two gets a review that misses half of it.

Resolve the base to `$ARGUMENTS` or `main`, and the current branch with `git rev-parse --abbrev-ref HEAD`.

## 1. Validate preconditions (stop on any failure)

Run `git fetch origin` first so the comparisons are accurate, then check all of:

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

**Two rules that are not optional.** **No AI or assistant attribution trailer** anywhere in the body (the
`dev-workflow` skill section 4). And if the work traces to a Linear issue, **reference `MAP-123` in the
body** so the native GitHub and Linear automation links them: a pushed branch moves the issue to In
Progress, an opened pull request to In Review, and a merge to `main` to Done, **git to Linear, one
direction** (ADR-0008 section 4).

Use a **closing magic word** plus the identifier only when this pull request finishes the issue, and the bare
identifier when it merely touches it.

## 4. The crossing case: one pull request, not two

A change spanning both stacks is **one pull request** carrying the serializer, the regenerated OpenAPI
schema, the regenerated TypeScript types and the component that consumes them, verified in one CI run
(ADR-0008 section 6). Drift between the sides is prevented by generation plus the freshness gate
(`just contracts`, PRD M12), never detected by a schedule. The api owns the schema, the web's types are
generated from it, and neither deployable imports code from the other (ADR-0001 section 1).

## 5. Point at the required checks

```bash
gh pr checks --watch
```

Merge only when the required checks are green. A red build is not merged and is not overridden.
