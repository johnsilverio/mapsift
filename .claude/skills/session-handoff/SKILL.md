---
name: session-handoff
description: Update Section 0 (the live state) of specs/session-handoff.md so a fresh context window can resume from that file plus CLAUDE.md. Use when the user asks to write the handoff, close the session, or record the live state for the next window. Triggers on "/session-handoff".
argument-hint: "[optional note]"
disable-model-invocation: true
---

# Session handoff

Update the live state in `specs/session-handoff.md` so a fresh clean-context session, reading that file plus
the root `CLAUDE.md`, can pick up exactly where this one stopped.

Optional note from the user for this handoff: $ARGUMENTS

## The rule that governs this command

`specs/session-handoff.md` is a canonical document catalogued in `specs/index.md`. It has a fixed shape:

- **Section 0, Current state**, is the live part. It is what this command updates, every clean-context
  window.
- **Sections 1 to 10** (the canon and authority chain, the working method, the empirical base, the
  determinism philosophy, positioning, settled objections, governance discipline, environment and flow, the
  Linear workflow, the `.claude` inheritance discipline) are **permanent and change rarely**.

**Never overwrite the whole file, and never replace its structure with a different one.** Sections 1 to 10
carry context that exists nowhere else in the repository; regenerating the file destroys it. If something in
sections 1 to 10 is genuinely wrong or outdated, edit that specific paragraph in place and say so in the
report, do not rewrite the document around it.

## Phase 1: gather the live state

Read the working-tree state rather than guessing it. A state claim is written only with the command that
verified it:

```bash
git status -sb                     # branch, tracking, changed and untracked files
git worktree list                  # parallel lines of work (ADR-0008 section 8)
git diff --stat                    # size of pending change
git log --oneline -5               # recent commits for context
```

`specs/session-handoff.md` itself is deliberately kept out of version control and lives in the main
checkout, so the handoff never rides in a pull request and a worktree does not carry it.

## Phase 2: read the current Section 0

Read `specs/session-handoff.md` first. Section 0 is a list of bullets covering, at minimum: the repository
layout, the documents on disk with their versions, the team, the repository/version-control state, the
current phase, what the last round produced, what must happen next and in what order, and the gating open
questions. Keep that shape and update the facts.

## Phase 3: edit Section 0 in place

Edit only the bullets whose facts changed, and add a bullet when this session produced something Section 0
does not yet mention. Every bullet must be checkable against disk. In particular update, when they moved:

- **Document versions** (foundation, PRD, CLAUDE.md sync, ADRs on disk) and what each round produced.
- **The current phase** and the ordered list of what must happen before the next architecture step.
- **Decisions closed this session**, with a one-line note on why, so the next window does not relitigate
  them. If a decision closed, remember the fan-out rule (handoff section 7): the foundation carries it as
  law, the ADR that owns its code shape is amended or created, `CLAUDE.md` updates the constraint or version
  pointer, `specs/PRD.md` takes it when it is a requirement, `specs/index.md` reflects a new document,
  Section 0 records the state, and `specs/log.md` gets one grep-able line. **Closing a decision is not
  finished until its fan-out is**, which is how `CLAUDE.md` still said "uv or poetry" while the tooling was
  already writing `uv run`, until the survey of 2026-08-01 closed it.
- **Blockers and gating open questions** (the OQ-N the work touches), and anything that must pass before a
  commit.
- **The branch and worktree state**, so the next window knows which line of work it is resuming.

Weave in the user's note if one was given.

## Phase 4: confirm and report

Re-read the file and confirm three things: sections 1 to 10 are byte-for-byte intact, Section 0 stands alone
for a reader who did not see this conversation, and no bullet asserts something that is not on disk.

Report what you changed in Section 0, the recorded repository state, and the top next step. If you found a
contradiction between Section 0 and the foundation or the PRD, report it rather than silently choosing one:
the foundation wins, and the derived document is the one that is wrong.
