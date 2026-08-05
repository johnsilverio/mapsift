---
name: onboard
description: Onboard to a new task by reading the canon, exploring the codebase, and building the context needed to implement. Use when starting a new task, feature, or bug fix that requires understanding the project first. Triggers on requests like "onboard me", "get ready for this task", "explore and prepare", "/onboard".
allowed-tools: Bash(sed *), Bash(ls *)
---

# Onboard

The user has given the task as an argument. Use it to aim the exploration.

> "AI models are geniuses who start from scratch on every task." (Noam Brown)

**This is task-scoped and it is not the orchestrator boot.** Run it when there is a task and you need the
context for **it**; the `orchestrate` skill is the other thing, opening a session when no task is picked up
yet, and it points here the moment one exists.

## The live state, injected

This is section 0 of `specs/session-handoff.md`, loaded from disk. Its own rule is worth inheriting: **a
state claim is written only with the command that verified it**, so where this block and the tree disagree,
the tree wins and the document is what is stale.

!`sed -n '/^## 0\. Current state/,/^## 1\. The canon/p' specs/session-handoff.md 2>/dev/null || echo "ABSENT. specs/session-handoff.md is deliberately untracked, so it exists in the main checkout and never in a worktree. Read it from there before claiming any live state, and say that you started without it."`

## The task specs on disk

!`ls specs/tasks/MAP-*.md 2>/dev/null || echo "(none picked up yet)"`

## 1. Read the canon first, not the code

The code is the smallest part of this project right now, and the decisions live in the specs. Read in this
order, and read from disk rather than trusting a summary:

1. `CLAUDE.md`, the operational floor: constraints C1 to C14, the architecture, the stack.
2. **`specs/tasks/MAP-<n>-<slug>.md` if the task has one**, which it does once the issue is picked up
   (ADR-0008 section 2). It is the assembled contract and it cites everything below, so reading it first
   turns the rest of this list into targeted lookups instead of a survey.
3. `specs/mapsift-foundation.md`, the constitution, for the sections the task touches. Do not read all of it
   for a narrow task; read the sections the requirement cites.
4. `specs/PRD.md` for the specific requirement and its acceptance criterion, which is the test to be written.
5. `specs/adr/` for the code-shape decision that governs where things go, and ADR-0001 section 8 for what
   must not be created yet.
6. `specs/testing.md` before writing any test or any code; the `test` and `implement` skills inject it at
   dispatch, so open it here only when you are onboarding outside a dispatched window.

## 2. Trace the task to its authority

Name the invariant, the C-test, or the PRD requirement the task derives from. If the task does not trace to
the foundation, the PRD or a spec, that is the finding: surface it rather than inventing a spec or building
against a guess. The same holds if it depends on an open question (an OQ-N) that is still open.

## 3. Explore the codebase

Find the code the task touches and the patterns it should follow. Note which deployable or library it lands
in (`apps/api`, `apps/web`, `libs/core`, `libs/ui`) and remember that nothing in `apps/` imports from another
`apps/`. Check the path-scoped rules in `.claude/rules/` for the languages involved.

## 4. Ask before assuming

Ask the user about anything genuinely ambiguous. A question now costs a minute; a wrong assumption costs the
implementation. And **never assert a library's behaviour from memory**: confirm against the version pinned
in the lockfile (`specs/dependencies.md` is the survey), or say you could not and give a confidence level.

## 5. Where the output goes

Do **not** create a private notes file. This project keeps exactly two homes for work context, deliberately:
**git owns the contract** (the foundation, the ADRs, the per-task spec the agent reads to implement) and
**Linear owns execution state** (status, assignee, discussion), bridged only by the task ID (ADR-0008
section 1). A third home inside `.claude/` is drift by construction and would not be reviewed by anyone.

So: report the onboarding summary in the conversation, and if it deserves to persist, write it as the
**per-task spec in git** (the contract), or as a comment on the Linear issue (execution state), per the
`linear-workflow` skill. If the session itself needs to be resumable, that is `/session-handoff`, which
updates section 0 of the canonical handoff.
