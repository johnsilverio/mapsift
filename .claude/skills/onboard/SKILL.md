---
name: onboard
description: Onboard to a new task by reading the canon, exploring the codebase, and building the context needed to implement. Use when starting a new task, feature, or bug fix that requires understanding the project first. Triggers on requests like "onboard me", "get ready for this task", "explore and prepare", "/onboard".
---

# Onboard

The user has given the task as an argument. Use it to aim the exploration.

> "AI models are geniuses who start from scratch on every task." (Noam Brown)

**This is task-scoped and it is not the orchestrator boot.** Run it when there is a task and you need the
context for **it**. the `orchestrate` skill is the other thing: it opens an orchestrator session when there is no
task yet, and its job is to establish where the project stands and what happens next. That file carries the
role and the boot checklist; this skill carries the reading, and it is the one either of them uses.

## 1. Read the canon first, not the code

**Half of this tree is intent rather than code**, so the code is the smallest part of the answer and the
decisions live in the specs. Read in this order, from disk rather than from a summary:

1. `CLAUDE.md`, the operational digest: the authority chain, the invariants in condensed form, the closed
   decisions that bind implementation, the non-goals, the build order, the naming rules.
2. `specs/session-handoff.md` **section 0**, the live state: what exists, what the last round produced, what
   must happen next, and which open questions are gating. Its own rule is worth inheriting: **a state claim
   is written only with the command that verified it**, so verify rather than trust.
3. **`specs/tasks/MAP-<n>-*.md` if the task has one**, which it does once the issue is picked up. That is
   the assembled contract and it names everything below, so reading it first turns the rest of this list
   into targeted lookups instead of a survey.
4. `specs/constraints.md`, **the section for the area the task touches**: the invariants with their
   acceptance criteria and the closed decisions that bind implementation. This is where the digest lives
   since the 2026-08-05 reduction moved it out of `CLAUDE.md`.
5. `specs/PRD.md` for the requirement that governs the task, its acceptance criterion and its status.
6. `specs/mapsift-foundation.md` for the sections the requirement cites, and for the **scar** behind an
   invariant when you are about to build against one. **Do not read all of it for a narrow task**; read
   section 0.5, which is the plain-language soul the rest is the engineering consequence of, and then the
   cited sections.
7. `specs/adr/` for the code-shape decision that governs where things go. **Follow the reading order in
   `adr/README.md`**, and check `0001`'s header for which later ADR amends which of its sections, because
   several are amended.
8. `specs/testing.md` before writing any test or any code.

## 2. Trace the task to its authority

Name the invariant `I1` to `I23`, the foundation section, or the ADR section the task derives from. **If it
traces to nothing, that is the finding**: surface it rather than inventing a spec or building against a
guess. The same holds if it depends on an open question that is still open, and several are hard blocks
(foundation section 13).

## 3. Explore the codebase

- **Which stack:** `apps/api` (Django with DRF, **verify with `ls -A apps/api`**, it may still be empty)
  or `apps/web` (Angular 21, scaffolded, no feature modules yet). **ADR-0001 section 1 decided one repository and the
  move has not run**, so they are still two git repositories today; two deployables either way, and
  neither
  imports the other.
- **Which package**, in the api: ADR-0002 section 2 has the fourteen packages and the tier order, and section
  3 explains why a module is not a package. A package imports downward only, and CI enforces it.
- **Which patterns** the existing code follows. In the web, read `apps/web/CLAUDE.md` and `apps/web/docs/`
  first: they are more current than any memory of Angular. Its `.claude/` is bespoke and correct, and its
  `docs/ecosystem-context.md` is the **June** version, superseded by the specs tree.

## 4. Ask before assuming

Ask about anything genuinely ambiguous. A question costs a minute; a wrong assumption costs the
implementation. And **never assert a library's behaviour from memory**: confirm against the version pinned in
the lockfile, or say you could not and give a confidence level.

## 5. Where the output goes

Do **not** create a private notes file. This project keeps exactly two homes for work context, deliberately:
**git owns the contract** (the foundation, the ADRs, the specs an agent reads to implement) and **Linear owns
execution state** (status, assignee, discussion), bridged only by the identifier, which never carries state.
A third home inside `.claude/` is drift by construction and nobody would review it.

So: report the onboarding summary in the conversation. If it deserves to persist, it is either a change to
the canon in git or a comment on the Linear issue, per the `linear-workflow` skill. If the session itself
needs to be resumable, that is `/session-handoff`, which updates section 0 of the canonical handoff.
