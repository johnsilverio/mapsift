---
name: onboard
description: Onboard to a new task by reading the canon, exploring the codebase, and building the context needed to implement. Use when starting a new task, feature, or bug fix that requires understanding the project first. Triggers on requests like "onboard me", "get ready for this task", "explore and prepare", "/onboard".
---

# Onboard

The user has given the task as an argument. Use it to aim the exploration.

> "AI models are geniuses who start from scratch on every task." (Noam Brown)

## 1. Read the canon first, not the code

The code is the smallest part of this project right now, and the decisions live in the specs. Read in this
order, and read from disk rather than trusting a summary:

1. `CLAUDE.md`, the operational floor: constraints C1 to C14, the architecture, the stack.
2. `specs/session-handoff.md` section 0, the live state: what exists, what the last round produced, what must
   happen next, and which open questions are gating.
3. `specs/mapsift-foundation.md`, the constitution, for the sections the task touches. Do not read all of it
   for a narrow task; read the sections the requirement cites.
4. `specs/PRD.md` for the specific requirement and its acceptance criterion, which is the test to be written.
5. `specs/adr/` for the code-shape decision that governs where things go, and its section 8 for what must not
   be created yet.

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
implementation.

## 5. Where the output goes

Do **not** create a private notes file. This project keeps exactly two homes for work context, deliberately:
**git owns the contract** (the foundation, the ADRs, the per-task spec the agent reads to implement) and
**Linear owns execution state** (status, assignee, discussion), bridged only by the task ID. A third home
inside `.claude/` is drift by construction and would not be reviewed by anyone.

So: report the onboarding summary in the conversation, and if it deserves to persist, write it as the
**per-task spec in git** (the contract), or as a comment on the Linear issue (execution state), per the
`linear-workflow` skill. If the session itself needs to be resumable, that is `/session-handoff`, which
updates section 0 of the canonical handoff.
