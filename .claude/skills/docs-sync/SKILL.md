---
name: docs-sync
description: Check whether the specs are still true, both against each other along the authority chain and against the code. Use when the user wants to verify the documentation matches reality, find a derived document that drifted from the foundation, or audit doc accuracy. Triggers on requests like "check docs", "sync documentation", "are the specs up to date", "/docs-sync".
---

# Docs sync

Mapsift's documentation is not a folder of guides beside the code, it is the **authority chain**, and "out
of sync" here has a precise meaning: a derived document asserting something the authority did not say, or a
document asserting something that is not true on disk.

The chain: `specs/mapsift-foundation.md` (constitution) → `specs/PRD.md` (requirements) →
`specs/adr/` (code shape) → `CLAUDE.md` and the per-repo docs. **Where a derived document and the foundation
disagree, the foundation wins and the derived one is wrong.**

**Search for the contradiction, do not read for confirmation.** This is the whole method, and it has a
measured justification: on 2026-08-01 the foundation declared itself closed and the handoff recorded that
only business content remained. Two days later an adversarial pass found three structural holes and two
accepted ADRs describing the same model incompatibly. **A document declaring itself complete is a hypothesis,
not a measurement.**

**Two axes, and they are different questions.** Is the document **true** (this skill), and is it at the
right tier and cheap to load (`writing-for-agents`, ADR-0002 section 5). A document can be perfectly true and still
be costing every session for a rule that fires once a month.

## 0. The orphan check, which is the one this tree currently fails

**A constraint that exists only in a derived document is a constraint nobody ratified.** `CLAUDE.md` and
`specs/constraints.md` both state that rule about themselves, and an audit on 2026-08-04 found several
constraints living only in `CLAUDE.md`. The 2026-08-05 reduction **moved** that content into
`specs/constraints.md` verbatim, which preserved the orphans rather than resolving them, and finding them
is open work this skill owns.

For each constraint in `specs/constraints.md`, grep the foundation, `PRD.md` and the ADR registry for the
thing it asserts. Three outcomes: it resolves upward and the digest is correct; it resolves upward but
says something **different**, which is drift and the authority wins; or **nothing upward says it**, which
is an orphan. An orphan is reported, never deleted and never promoted on your own: either the owner
ratifies it into the foundation or an ADR, or it was never a rule.

Check the **tier** in the same pass, since you are already reading the line: a constraint that is true for
every task belongs in `CLAUDE.md`, one that is true per stack belongs in a path-scoped rule, one that is
true per kind of task belongs in a skill, and the rest belongs where it is.

## 1. Check the chain, downward

This is the drift that hurts, because the agent obeys the derived document and cannot tell which authority is
stale. For each derived document, check that:

- It does not **contradict** the foundation. The worked example is the one that survived for months: the root
  `CLAUDE.md` listed `PARTNER` and `SPOUSE` as `PartyRole` kinds after foundation v0.3 made them
  relationships, in the file that loads first in every session.
- **Two accepted ADRs do not describe the same thing two ways.** ADR-0001 section 2 carried a two-column
  identifier model long after v0.9 replaced it with rows and ADR-0006 implemented rows, and the baseline's
  own amendment map did not list section 2 as amended. Check the amendment maps, not just the prose.
- Its **version pointers** are current. The convention is written in `adr/README.md`: the `Authority` line
  names **the current version the ADR has been checked against**, and the version it was written under is
  history. **Moving a pointer without doing the reading is worse than leaving it stale**, because it converts
  an obvious gap into a false assurance.
- It does not reference a **section, requirement or document that does not exist**.
- A decision that closed recently completed its **fan-out**: the foundation as law, the ADR that carries its
  code shape, `CLAUDE.md`, `specs/PRD.md` where it is a requirement, `specs/session-handoff.md` section 0,
  `specs/index.md`, and one grep-able line in `specs/log.md`. **Closing a decision is not finished until its
  fan-out is finished.**

## 2. Check the documents against disk

Verification here is reading the file and running the command, never trusting a summary. Useful sweeps:

```bash
grep -rn "—\|–" specs/ CLAUDE.md                      # em dashes are banned in prose
grep -h "Authority:\*\* derives from" specs/adr/*.md  # do all pointers agree?
ls -A apps/api                                        # is it still empty?
```

Then confirm the documents that make factual claims still hold: the repository layout of ADR-0001 section 1,
which the tree must actually match, the layout in `CLAUDE.md` and
ADR-0002, the commands in `CLAUDE.md`, the state bullets in session-handoff section 0, the document catalog
and the identifier ranges in `specs/index.md`, and the pinned versions, which are **confirmed against the
lockfile and never remembered**.

## 3. Check the naming, because v0.11 reversed a rule

Code carries **no Portuguese words**. An acronym naming a Brazilian registry or document stays, because it is
a proper noun; a common noun takes its English term of art. `Matricula` is `TitleRecord`, `Cartorio` is
`LandRegistryOffice`, `Comarca` is `JudicialDistrict`, `Congelado` is `is_dormant`. **Prose may still name
the Brazilian instrument in Portuguese**, because prose describes an institution while code declares a
symbol, so a hit is not automatically a finding: read it.

## 4. Report only what is wrong

- Flag what is **false or contradictory**, not what is missing. A gap that `PRD.md` section 20 already
  lists is tracked, not drift.
- For each finding: the file, the exact excerpt, which authority it contradicts, and the correction.
- Say which side to fix. Almost always the derived document, **except when the authority genuinely never
  decided**, in which case the fix is to raise the decision to the authority rather than let the derived file
  keep deciding. That distinction is the one that produced foundation v0.11 and v0.12.

## 5. Output

A checklist ordered by severity: contradicts the foundation, contradicts another accepted document, false
against disk, stale pointer. **And say plainly whether the tree is clean**, because a report that lists only
findings reads as incomplete when there are none.
