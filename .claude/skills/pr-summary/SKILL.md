---
name: pr-summary
description: Write a pull request body for the current branch. Use when the user wants a PR description, a summary of the branch changes, or a body prepared before opening the PR. Triggers on requests like "summarize my changes", "write a PR description", "what changed in this branch", "/pr-summary".
---

# PR summary

Write the body for the current branch's pull request. **Produce the text; do not open the pull request.**
That is `/pr`.

## 1. Read what actually changed

```bash
git rev-parse --show-toplevel          # which repository is this
git rev-parse --abbrev-ref HEAD
git log origin/main..HEAD --oneline
git diff origin/main...HEAD --stat
git diff origin/main...HEAD
```

Read the diff, not just the commit subjects. A body derived from commit subjects repeats what the reviewer
can already see in the commit list and adds nothing.

## 2. The body

English, no em dashes, no double hyphens, **no AI or Co-Authored-By attribution trailer** anywhere.

Structure it as four parts, and drop any that would be empty rather than padding it:

**What this changes, and why.** One short paragraph in plain language. Lead with the behaviour that is
different now, not with the files.

**The trace.** Which invariant, foundation section, ADR section or requirement this implements, cited by
identifier. **This is the part reviewers actually need**, because `CLAUDE.md` "Process & tracking" makes the trace the
condition for the work existing at all. If the branch traces to a Linear issue, reference `MAP-123` here,
with a closing magic word only when this pull request finishes it.

**What a reviewer should look at hardest.** Name the risky part rather than making them find it: a decision
that moved, a migration, a new package boundary, a place where the change was arguable. **A pull request that
claims everything is straightforward gets a shallow review.**

**What is deliberately not here.** Scope you left out on purpose, a follow-up, an open question you hit. This
is what stops a reviewer asking for something that was decided against.

## 3. Two things worth checking before you hand it over

**If the change spans both stacks**, say so: it is **one pull request** carrying the serializer, the
regenerated schema, the regenerated types and the component that consumes them (ADR-0008 section 6), and the
body names the crossing so the reviewer reads both sides together instead of finding half a contract.

**If the change touches a decision**, the fan-out is part of the work and belongs in the body: the
foundation, the ADR, `CLAUDE.md`, `specs/PRD.md`, the handoff's section 0, and one line in
`specs/log.md`. A pull request that changes a decision in one place only is incomplete, and saying which
documents moved is how the reviewer checks it.
