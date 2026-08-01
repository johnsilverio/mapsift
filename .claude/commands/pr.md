---
description: Push the current branch and open a pull request against the base, then point at the required CI checks.
argument-hint: "[base-branch, default main]"
---

Open a pull request for the current branch in the Mapsift repository. Follow `CLAUDE.md` and the `dev-workflow` skill. Base branch: $ARGUMENTS (default `main` when empty).

Resolve the base to `$ARGUMENTS` or `main`, and the current branch with `git rev-parse --abbrev-ref HEAD`.

## 1. Validate preconditions (stop on any failure)

Run `git fetch origin` first so the comparisons below are accurate, then check all of:

- Current branch is not the base. If on `main` (or the resolved base), stop: branch from `main` first.
- There are commits ahead of the base: `git log origin/<base>..HEAD --oneline` must list at least one commit. If empty, stop: nothing to open a PR for.
- No PR already exists for this branch: `gh pr list --head <branch>` must return nothing. If a PR exists, stop and show its URL instead of opening a duplicate.

If any check fails, report the exact reason and do not continue.

## 2. Push the branch

```bash
git push -u origin <branch>
```

Never force-push, and never push to `main`.

## 3. Open the pull request

```bash
gh pr create --base <base> --fill
```

`<base>` is the base resolved at the top of this command: `$ARGUMENTS` when given, `main` otherwise. `main`
is the protected default and the normal target; an explicit base is for the rare stacked-branch case, and if
one is given, use it rather than silently retargeting `main`. `--fill` derives the title and body from the
commits. **Do NOT add any AI/Co-Authored-By attribution trailer** to the PR body. If the work traces to a Linear ticket, reference its ID (e.g. `MAP-123`) in the body so the GitHub↔Linear automation links them (see the `linear-workflow` skill).

## 4. Point at the required checks

Tell the user the PR must pass the repository's required CI checks before merging. Discover and watch them:

```bash
gh pr checks --watch
```

Merge only when the required checks are green (for example `gh pr merge --delete-branch` with the team's chosen strategy). Never force-push `main`.
