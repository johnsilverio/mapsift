---
name: commit
description: Run the pre-commit gate and create atomic Conventional Commits (does not push). Use when the user asks to commit, save the work, or create commits. Runs the gate first and never pushes. Triggers on "/commit".
argument-hint: "[optional scope or message hint]"
disable-model-invocation: true
allowed-tools: Bash(git *), Bash(sed *)
---

Create one or more commits for the staged work. Follow `CLAUDE.md`, `specs/mapsift-foundation.md`
section 14 and the `dev-workflow` skill. Optional hint for scope or wording: $ARGUMENTS

**This is one repository, organised by unit of deploy** (ADR-0001 section 1), so a commit may legitimately
carry `specs/`, `apps/api` and `apps/web` together when they are one change; what it may not do is carry
two purposes because the paths happen to be staged together.

## The commit rules, injected from their single source

This is section 4 of the `dev-workflow` skill, loaded from disk. It is the authority for the message, and
this skill does not restate it.

!`sed -n '/^## 4\. Commits/,/^## 5\./p' .claude/skills/dev-workflow/SKILL.md`

## 1. Pre-commit gate, never commit on red

Run `/quality-gate`, which is the single definition of the checks and mirrors CI. Do not restate a partial
list here: a local gate that drifts from the one CI runs is worse than none, because it reports green on a
change CI will reject.

If any check fails, STOP: report what failed and do not commit.

## 2. Inspect what is staged

```bash
git status
git diff --staged
```

Read the staged changes to understand their purpose. If nothing is staged, stop and say so. Only staged
changes are committed here; this command does not stage files for you.

**Two things that stop a commit outright in this tree**, both C6 (foundation I7): a credential, and
production data. If the staged diff carries a database dump, a fixture derived from production data, or a
secret, stop. A committed secret stays in the history forever, which is why this check runs before the
commit exists rather than after.

## 3. Compose the message under the injected rules

The format, the types, the one-line rule, the language and the no-trailer rule are the injected section
above, not a list here. One thing it does not say: **an issue exists only when the work traces to the canon
and the trace is cited** (ADR-0008 section 2), so a commit referencing an identifier that traces to nothing
is a signal that the issue should not have existed.

## 4. Create the commits

```bash
git commit -m "type(scope): short description"
```

When splitting, stage each purpose separately (`git restore --staged <paths>` then `git add <paths>`) so
every commit contains only its own changes.

**Do not push.** Opening a pull request is `/pr`, and `main` never receives a direct push.

## 5. When the commit changes a decision, the fan-out is part of the change

A commit that closes or revises a decision is not finished when the code compiles. Foundation section 15 and
the fan-out rule require the decision to reach. **Run the `fan-out` skill, which owns that list.** Formerly enumerated here: the foundation as law, the ADR that
carries its code shape, `CLAUDE.md`, `specs/PRD.md` where it is a requirement, section 0 of
`specs/session-handoff.md`, and one grep-able line in `specs/log.md`. **A decision whose fan-out is
incomplete is a contradiction waiting to be found by the next adversarial pass**, which is exactly how
`CLAUDE.md` still said "uv or poetry" while the tooling had already started writing `uv run`, until the
survey of 2026-08-01 closed it (`specs/dependencies.md` section 1).
