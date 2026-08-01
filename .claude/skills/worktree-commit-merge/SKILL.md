---
name: worktree-commit-merge
description: Commit the work in a git worktree and take it to main through a pull request, then sync the worktree branch with main. Trigger when the user says things like "commit and merge to main", "we're done with this worktree, commit and merge", or any similar phrasing. Don't wait for the user to spell out "worktree" — if there are changes and they mention merging to main, use this skill.
---

# Finishing a worktree

You are in a git worktree on a feature branch with uncommitted changes. Mapsift runs several backlog items in
parallel worktrees, so this is the normal way a feature ends.

**What this skill does not do: it never merges into `main` locally.** `main` is protected, the change reaches
it through a pull request, and the required CI checks decide (`dev-workflow` section 5, ADR-0001 section 6). A
local `git merge` into `main` skips lint, strict type checks, the test suites and the generated-contract
freshness check, which is the whole reason those gates exist. If a merge really must happen locally for a
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

Run `/quality-gate` for the languages the change touched. **Never commit on red.** If anything fails, stop,
report it, and do not commit.

## Step 3: Commit

Stage explicit paths rather than `git add -A`, which can pull in `.env`, build artifacts, or a local settings
file:

```bash
git add <specific relevant files>
git commit -m "type(scope): short description"
```

Conventional Commits, English, imperative mood, one purpose per commit. **Do NOT add any AI/Co-Authored-By
attribution trailer.** If the work traces to a Linear ticket, reference its ID (`MAP-123`).

## Step 4: Push and open the pull request

```bash
git push -u origin <current-branch>
gh pr create --base main --fill
gh pr checks --watch
```

`/pr` wraps this with its preconditions (not on the base branch, at least one commit ahead, no existing PR for
the branch). Merge only when the required checks are green, with the team's chosen strategy, for example
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
