---
allowed-tools: Bash(sed *), Bash(wc *)
name: writing-for-agents
description: Write or revise any document an agent reads in this ecosystem, so it is cheap to load and reliable to reach: a skill, a rule, CLAUDE.md, a spec, an ADR, a window prompt. Covers the loading tiers, pointer wording, the no-op test, and pruning duplication and sprawl. Use when creating or editing anything under .claude/ or specs/, when a document feels long, or when an agent ignored a rule that is written down. Triggers on "/writing-for-agents", "write a skill", "edit CLAUDE.md", "this doc is too long", "the agent is ignoring the rule".
---

# Writing for agents

The reader has already read everything. **Explanation is waste and precision is the whole job.**

This skill governs the **form** of a document: what it costs to load, whether the agent reaches it, whether
it says anything twice. It does not check whether the document is **true**; that is `docs-sync`, which
walks the authority chain and compares claims against disk. Run this one when writing, that one when
auditing.

The **model** for where a document lives is ADR-0002 section 5, which fixes the three-level split. This skill is the craft of writing the
line once the tier is chosen.

## The loading model, injected because it is what this skill executes against

This is the Decision of `specs/adr/0019-the-context-loading-model.md`, loaded from disk. Where this skill
and the text below disagree, **the ADR wins**.

!`sed -n '/^## Decision/,/^## Consequences/p' specs/adr/0019-the-context-loading-model.md`

## What tier 0 costs right now

!`wc -l CLAUDE.md`

---

## 1. Two budgets, and every choice spends one

**Context load** is the cost on the model's window: an always-loaded line is paid on every turn whether or
not it fires. **Cognitive load** is the cost on the human: which documents exist and when to reach for
each. The second is not a cost to minimize away, because the human staying the index is the point.

Most authoring decisions (split or not, inline or point, state or cite) are the same trade made in
different places. **Ask which budget you are spending before you write.**

## 2. Ladder down, do not pile up

Three rungs, and material belongs on the lowest one where it still fires:

1. **In-file step**: needed every time this document runs.
2. **In-file reference**: needed most times, so it stays but sits below the steps.
3. **Behind a pointer**: needed on one branch out of several, so it lives in its own file and the parent
   names it.

A document that carries every branch inline pays for all of them on every run. Moving a branch behind a
pointer is **progressive disclosure**, and it is the only reason a long reference can exist at all.

## 3. A pointer carries where AND when

> The pointer's wording, not its target, decides whether the agent reaches through it.

Every pointer states **where to read** and **the condition that sends you there**. A skill's `description`
carries the words a user would actually say. A line in `CLAUDE.md` naming a document says what question
that document answers. A window prompt names the file, the section, and what the window is looking for.

**A pointer is not a summary.** The moment you write the gist beside the citation you have made a second
copy, and it is the copy that goes stale, because nothing propagates into it. This is the same rule
`CLAUDE.md` states about code comments, applied to documents.

**An unreached pointer is worse than an absent one**, because the material is then both unread and believed
to be covered. If an agent keeps missing a rule that is written down, the pointer is the defect, not the
agent.

### How to write the reference, which depends on the document

**Verified 2026-08-05 against Claude Code's own documentation, because `@` means three different things
depending on where it sits, and one of them is expensive.**

**The question to ask first is not which syntax. It is whether the document can do its job without the
target.** A **hard dependency** is loaded, really loaded. An **optional lookup** is pointed at. Getting
that backwards in either direction is a defect: a pointer where a dependency belongs produces an agent
that works without the context it needed, and a load where a lookup belongs pays for material nobody used.

| Where you are writing | For a hard dependency | For an optional lookup |
| --- | --- | --- |
| **a `SKILL.md`** | **`` !`sed -n '/^## 8/,/^## 9/p' specs/testing.md` ``**. The shell runs **before** the content reaches the model and its output replaces the placeholder, so the material is simply there and cannot be skipped. Declare the commands in `allowed-tools` or it prompts | **backticks plus the firing condition**, or a **markdown link** for a file inside the skill's own directory |
| **`CLAUDE.md`** or a `rules/` file | **`@path`**, which is a real import: expanded into context **at launch**, recursively up to four hops | **backticks**. The docs say plainly that wrapping a path in backticks is how you name it **without** importing |
| **a spec, an ADR, a task spec** | there is no mechanism. These are plain markdown, so state the dependency as a reading instruction | **backticks** |
| **the chat, when the owner types it** | **`@specs/testing.md`**, which attaches the file to that message | just say it |

**Two traps, opposite in direction, and both have bitten this tree.**

**In a skill, backticks look sufficient and are not.** A skill that says "read `specs/testing.md` sections
1 to 9" is a request, and a window that skips it writes a plausible test against a method it never read.
**Every skill that cannot function without a spec injects it**, which is why `test` and `implement` carry
the whole method, `fan-out` carries the document map, and `backlog` carries the open questions.

**In `CLAUDE.md`, `@` looks tidier and is expensive.** `@specs/PRD.md` there would silently load more than
twelve hundred lines into every session, undoing the separation ADR-0002 section 5 exists for. **The
correct form looks like the lazy one**, so anyone "improving" the citations in a tier 0 file reads this
table before touching it.

The rule underneath both: **the tier decides when the document loads, and within it, a hard dependency is
injected rather than requested.** Injection is not a second copy, because it is read from disk at fire
time; there is still exactly one copy and nothing to drift.

## 4. The no-op test

**Delete the line and ask whether the agent's behaviour changes.** If it does not, the line was paying
context and buying nothing.

Applied honestly this deletes a lot: anything the model already knows, anything stated elsewhere in the
same document, anything that reads as encouragement. **When a sentence fails, delete the whole sentence
rather than shortening it.**

The test is behavioural, not aesthetic. A document told to be "streamlined" gets shorter and loses
function, because length is the thing a model can see. Settle a disagreement about a line by running the
document and watching what the agent does, not by arguing about it.

## 5. Three failure modes, named so a review can call them

- **Duplication**: the same fact in two places. The most reliable sign a document was never tested. One of
  the copies is already wrong.
- **Sediment**: a line that was true two revisions ago and now only looks true. In this tree it shows up as
  a stale version number, a document that no longer exists, a layout that describes the destination as
  though it were the tree.
- **Sprawl**: the document grew past where anyone reads to the end, so the rules at the bottom are
  decorative.

## 6. Leading words

A compact concept the model already has (**red**, **seam**, **tracer bullet**, **fan-out**, **the gate**,
**stop and report**) does more work than a paragraph explaining the same thing, and it anchors twice: once
in the body while the document runs, once in the pointer when the agent decides whether to reach for it.

This ecosystem has its own, and using them consistently is what makes the tree read as one system: **the
canon**, **the fan-out**, **the two windows**, **the gate**, **an invariant**, **a scar**, **stop and
report**, **a criterion that can fail**. Use the existing word rather than inventing a synonym.

## 7. The rules that are specific to this tree

- **English, always, with exactly two carve-outs.** The acronym rule in `CLAUDE.md`, and **`docs/` at the
  repository root, which is human-facing and written in Portuguese** because the conversation is. Nothing
  under `specs/`, `.claude/` or `apps/` carves.
- **No em dash and no double hyphen in prose**, anywhere, including under `.claude/`. A CLI flag is a flag
  and an arrow in a fenced diagram is not prose.
- **Cite by identifier**: `I4`, `C7`, `M9`, `OQ-8`, `ADR-0005 section 3`. A citation
  that resolves is worth more than a paraphrase that reads well.
- **A lower layer never decides.** A rule restates an ADR, a skill executes a method, `CLAUDE.md` digests
  the foundation. **A constraint that exists only in a derived document is a constraint nobody ratified**,
  and finding one is a defect to report, not a convention to keep.
- **A closed decision fans out in one pass.** Writing it in one place and planning to propagate later is
  how a contradiction is born. The targets are in `specs/session-handoff.md` section 7.
- **State claims carry the command that verified them.** "The tree has no remote" is worth nothing;
  `git remote -v` returning empty is worth something.

## 8. Writing a skill specifically

- The **`description` is the trigger** and it is the only part loaded until the skill fires, so it carries
  the words a user would actually say plus the situations that should reach it. A skill nobody reaches is
  a skill that does not exist.
- **One skill, one job.** Split when the file grows unwieldy or when two halves are never needed together.
- **Do not restate a spec, which is different from injecting one.** Injecting is loading the authority
  from disk at fire time and it is right for a hard dependency (section 3); restating is typing a second
  copy of what it says, and it is always wrong. Point at `specs/testing.md` for the method, at the ADR for the shape, at
  `PRD.md` for the requirement. A skill that carries its own copy of the method is the second copy that
  drifts, and it is the most dangerous kind here because the agent obeys it and cannot tell which authority
  is stale.
- **Practice what it preaches.** A skill about keeping documents lean that runs to four hundred lines has
  refuted itself.

## 9. Done when

- Every line survives the no-op test.
- Nothing is stated twice, in any form, at any tier.
- Every pointer says where and when, and every citation resolves.
- The document got **shorter** as it got better, and you are mildly surprised how little is left.
- A branch only one path needs sits behind a pointer rather than in the main file.
- No em dash, no double hyphen, English throughout.
