---
name: github-workflow
description: Take approved work all the way out: the gate, the commits, the push and the pull request, in one invocation instead of three. Use when the user says ship it, take this to a PR, commit and open the pull request, or otherwise wants the whole chain rather than one step of it. Triggers on "/github-workflow", "ship it", "commit and open a PR", "take this out". For one step on its own, use `/quality-gate`, `/commit` or `/pr` directly.
disable-model-invocation: true
---

# Ship the work

**This is a pointer, not a procedure.** The three steps are already written and this file does not carry a
second copy of any of them:

1. **`.claude/skills/quality-gate/SKILL.md`**, the checks CI will run for the stack you touched.
2. **`.claude/skills/commit/SKILL.md`**, the gate plus atomic Conventional Commits. It does not push.
3. **`.claude/skills/pr/SKILL.md`**, the push, the pull request, and the required checks.

Read each one when you reach it. What follows is only what none of the three says, because each of them is
written to also work alone.

## Why this is a skill and not a subagent

Two reasons, and the second is measured rather than preferred.

**The output belongs in the main session.** A subagent returns a summary, and the whole point of this chain
is that the owner reads the diff and the commit messages before anything leaves the machine. Isolation
would hide exactly what needs looking at.

**And a subagent could not carry it anyway.** Verified 2026-08-05 against Claude Code's documentation: a
subagent preloads skills through its `skills:` field, and **a skill that sets
`disable-model-invocation: true` cannot be preloaded**, because preloading draws from the same set the
model is allowed to invoke. `commit` and `pr` both set it, deliberately, since they write history and
push. So the subagent shape is not available for this chain, and the pointer shape is.

## What the three do not say

**When the whole chain is appropriate at all.** Only when the work is finished and reviewed: the gate is
green, `code-review` returned no blocking finding, and you are on a branch created from the Linear issue.
**Never on `main`.** If any of those is false, run the step that is missing instead of the chain.

**Where to stop when a step fails, which is the part that costs time.** The three steps are not one
transaction and they fail differently:

| Fails at | State you are left in | What to do |
| --- | --- | --- |
| gate | nothing happened | fix, do not commit on red |
| commit | some commits may exist | finish the commits, do not push a half-told story |
| push | commits are local | this is recoverable and normal; retry or fix the remote |
| pull request | the branch is pushed | the branch is public and the issue has not moved. Open the pull request by hand rather than leaving it |

**Whether the fan-out ran.** If this work closed a decision, the canon change is **part of this commit**,
not a follow-up. **Run the `fan-out` skill, which owns the target list**; naming a subset here would be the
seventh copy of it. A decision that lands in code and not in the canon is
the contradiction the next adversarial pass finds, and it is cheapest to fix before the commit exists.

**Which worktree and branch you are on.** Run `git status -sb` and `git worktree list` and say so before
anything else. This is one repository organised by unit of deploy (ADR-0001 section 1), with one remote and
a protected `main`; parallel lines of work live in worktrees (ADR-0008 section 8), and shipping from the
wrong one is a mistake nobody notices until review.

**That a crossing change is one pull request.** `pr` section 4 has the mechanics; what it does not say is
when to look: if the diff touches a serializer, the regenerated schema, the regenerated types or a
component that consumes them, it is crossing, and splitting it means shipping half a contract.
