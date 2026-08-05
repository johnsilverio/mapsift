---
name: worktree-commit-merge
description: Commit the work in a git worktree and take it to main through a pull request, then sync the worktree branch with main. Trigger when the user says things like "commit and merge to main", "we're done with this worktree, commit and merge", or any similar phrasing. Do not wait for the user to spell out "worktree": if there are changes and they mention merging to main, use this skill.
---

# Finishing a worktree

You are in a git worktree on a feature branch with uncommitted changes. Independent issues run in
independent worktrees (ADR-0008 section 8), so two lines of work (two people, or two agent sessions) do not
step on each other's checkout and branch, which is closer to a requirement for parallel agent sessions than
a convenience.

**This is one repository, organised by unit of deploy** (ADR-0001 section 1), so a worktree is a worktree of
the whole ecosystem and may legitimately carry `specs/`, `apps/api` and `apps/web` in one change when they
are one change. Confirm with `git worktree list` and say which worktree and branch you are on before doing
anything.

**What this skill does not do: it never merges into `main` locally.** `main` is protected, the change reaches
it through a pull request, and the required CI checks decide (the `dev-workflow` skill and ADR-0001 section 6). A local `git merge`
into `main` skips the suites, the strict type checks, `lint-imports` and the contract freshness check,
which is the whole reason those gates exist. If a merge really must happen locally for a
reason outside this workflow, that is the owner's explicit call, not this skill's default.

## Step 1: Gather context

```bash
git status
git diff HEAD
git branch --show-current
git worktree list
git log --oneline -10
```

That gives you what changed and what is staged, the worktree branch, the main worktree path and its branch,
and the recent commit style so your message fits the project.

## Step 2: Run the gate

Run `/quality-gate` for the stack the change touched. **Never commit on red.** If anything fails, stop,
report it, and do not commit.

## Step 3: Commit

Stage explicit paths rather than `git add -A`, which can pull in `.env`, build artifacts, or a local settings
file:

```bash
git add <specific relevant files>
git commit -m "type(scope): short description"
```

Conventional Commits, English, imperative mood, one purpose per commit. **Do NOT add any AI/Co-Authored-By
attribution trailer.** If the work traces to a Linear issue, reference `MAP-123`.

And the check specific to this tree: **no production data, no dump, no credential** in the staged diff
(foundation 9.1, ADR-0003 section 2).

## Step 4: Push and open the pull request

```bash
git push -u origin <current-branch>
gh pr create --base main --fill
gh pr checks --watch
```

`/pr` wraps this with its preconditions and is the normal path.

**A change spanning both stacks is ONE pull request** (the one-pull-request rule under ADR-0001 section 1): the
serializer, the regenerated OpenAPI schema, the regenerated TypeScript types and the component that consumes
them, verified in one CI run. The fixed api-first ordering, the schema snapshot the web controlled and the
scheduled drift check are **retired**, and if you remember them, that memory is stale.

Merge only when the required checks are green, with the team's chosen strategy, for example
`gh pr merge --delete-branch`.

## Step 5: Sync the worktree branch with main

Once the PR is merged, bring the worktree branch up to date so it carries whatever else landed on `main`
meanwhile:

```bash
git fetch origin
git merge origin/main
```

This runs in the worktree directory. If the worktree's purpose is finished, remove it instead:
`git worktree remove <path>`.

## Step 6: Confirm

Report what was committed (files and message), the PR URL and the state of its checks, and whether the
worktree branch is now in sync with `main` or the worktree was removed. If the PR is still waiting on checks,
say so plainly rather than implying the work has landed.
