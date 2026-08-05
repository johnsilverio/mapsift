---
name: ticket
description: Work on a Linear issue end-to-end: read the issue, trace it to the canon, explore the codebase, branch, implement test-first, run the quality gate, update the issue, open a PR. Use when the user provides an issue ID to implement. Triggers on requests like "/ticket MAP-123", "work on this ticket", "implement MAP-123".
---

# Issue workflow

End to end for an Mapsift issue, `MAP-123`. The loop is `CLAUDE.md` "Process & tracking" plus the `linear-workflow` and `dev-workflow` skills, and this skill executes it
rather than defining a second one.

## 1. Read the issue and check that it should exist

Read it through the Linear MCP (workspace `mapsift`, team `Mapsift`). Then apply the condition that
governs whether the work is legitimate at all:

**An issue exists only when it traces to the canon, and the trace is cited in the issue.** An invariant, a
foundation decision, an ADR, a requirement. **An open question is not an issue**: it is a question with an
owner and an exit criterion, and it becomes an issue when it is answered and there is work.

If the issue traces to nothing, stop and say so. Do not invent the trace, and do not build against a guess.
And if a discussion in Linear changed what the system should do, **that decision goes back into the
foundation or an ADR before code follows it**, because git owns the contract and the tracker owns only
execution state.

## 2. Onboard

Run `/onboard` with the issue's subject. Read the canon before the code: this tree is mostly intent, and the
decision you need is almost certainly written down already.

Check whether an open question blocks the work (foundation section 13). Several are hard blocks.

## 3. Branch from the issue, not from your head

**Create the branch from the Linear issue**, so the name carries the identifier and the automation links
itself. Status then moves on its own: pushed branch to In Progress, opened pull request to In Review, merge
to `main` to Done. **git to Linear, one direction**, so there is nothing to reconcile.

Never work on `main`.

## 4. Implement in the two-window protocol

This is the part that is easy to collapse and must not be. **Each half is a skill**: `test` writes the
failing tests as behaviour and implements nothing, `implement` turns them green without touching them, and
`code-review` closes each half by running the gates rather than reading a report. The brief each one
receives is specified in `specs/testing.md` section 1.1, and the `orchestrate` skill boots the window that writes
those briefs.

**Window A writes the failing tests as behaviour**, from the requirement, naming the invariant or the
requirement identifier in the test (`specs/testing.md` sections 1 and 6). It does not write the
implementation.

**Window B implements the minimum to green**, treating those tests as a contract authored by someone else,
and **may not edit a test to make it pass**. A test that looks wrong is a finding reported back, not a
licence to rewrite the contract it is supposed to satisfy.

**Design happens in the refactor step, under green.** That is where the `solid` skill is spent: a pattern
reached for while a test is red is a pattern chosen to make one test pass.

A single session doing both halves converges the test toward the implementation it already has in mind, and
the test stops being a specification. **That is the failure this protocol exists to prevent**, and it is also
why this project deliberately does not adopt an autonomous bridge that turns an issue assignment into a pull
request (`CLAUDE.md` "Process & tracking").

## 5. Gate

Run `/quality-gate`. Never commit on red, and never weaken a test to make it pass.

## 6. Commit and open the pull request

`/commit` then `/pr`. Conventional Commits in English, atomic, no attribution trailer. Reference `MAP-123`
in the body, with a closing magic word only when this finishes the issue.

If the change spans both stacks it is **one pull request** (ADR-0001 section 1, the one-pull-request rule),
carrying the serializer, the regenerated schema, the regenerated types and the component. The retired rule,
in case it is remembered: api first, web second, both citing the identifier, only the second
closing it.

## 7. Update the issue with what the automation cannot know

The status moves itself, so do not touch it. What is worth a comment is what a human would ask later: a
decision taken during the work, an assumption made, a thing found and deliberately left out, a follow-up.

**And if the work changed a decision, the canon change is part of the work**, not a follow-up. **Run the
`fan-out` skill, which owns the target list.** A decision that lands in code and not in the canon is a contradiction the next adversarial
pass will find.
