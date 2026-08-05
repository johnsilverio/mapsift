---
name: commit
description: Run the pre-commit gate and create atomic Conventional Commits (does not push). Use when the user asks to commit, save the work, or create commits. Runs the gate first and never pushes. Triggers on "/commit".
argument-hint: "[optional scope or message hint]"
disable-model-invocation: true
---

Create one or more commits for the staged work. Follow `CLAUDE.md`, `specs/mapsift-foundation.md`
section 14 and the `dev-workflow` skill. Optional hint for scope or wording: $ARGUMENTS

**ADR-0001 section 1 decided one repository and the move has not run**, so today `apps/web` and the tree root are
still separate repositories and a commit belongs to one of them. After the migration a commit may
legitimately carry `specs/`, `apps/api` and `apps/web` together when they are one change. Run
`git rev-parse --show-toplevel` and say
which one you are committing to.

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

**Two things that stop a commit outright in this tree**, both from foundation 9.1 and ADR-0003 section 2: a
credential, and production data. If the staged diff carries a database dump, a fixture derived from the 1.0
database, or a secret, stop. A repository that starts with a committed secret carries it in its history
forever, which this tree has already learned once.

## 3. Compose an atomic Conventional Commit message, in English

One purpose per commit. Format `type(scope): short description`, with type from `feat`, `fix`, `refactor`,
`test`, `docs`, `style`, `chore`, `perf`. Subject in English, imperative, lower case, no trailing period.

**Everything written in this ecosystem is in English**, commit messages included, and there are no em dashes
or double hyphens in prose.

If the subject needs an "and" to describe what is staged, that is two commits: split by purpose and plan one
message per purpose.

If the work traces to a Linear issue, reference `MAP-123`. **An issue exists only when the work traces to the
canon and the trace is cited** (`CLAUDE.md` "Process & tracking"), so a commit referencing an identifier that traces to
nothing is a signal that the issue should not have existed.

**Do NOT add any AI or Co-Authored-By attribution trailer.** The committer of record is the developer.

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
incomplete is a contradiction waiting to be found by the next adversarial pass**, which is exactly how the
`PARTNER` and `SPOUSE` role kinds survived in `CLAUDE.md` long after the foundation made them relationships.
