---
name: docs-sync
description: Check whether the specs are still true, both against each other along the authority chain and against the code. Use when the user wants to verify the documentation matches reality, find a derived document that drifted from the foundation, or audit doc accuracy. Triggers on requests like "check docs", "sync documentation", "are the specs up to date", "/docs-sync".
---

# Docs sync

Mapsift's documentation is not a folder of guides beside the code, it is the **authority chain**, and "out of
sync" here has a precise meaning: a derived document asserting something the authority did not say, or a
document asserting something that is not true on disk.

The chain: `specs/mapsift-foundation.md` (constitution) → `specs/PRD.md` and `CLAUDE.md` (derived) → the ADRs
in `specs/adr/` (code shape) → the per-task spec in git → `.claude/rules/` (the enforceable restatement).
**Where a derived document and the foundation disagree, the foundation wins and the derived one is wrong.**

## 1. Check the chain, downward

This is the drift that actually hurts, because the agent obeys the derived document and cannot tell which
authority is stale. For each derived document, check that:

- It does not **contradict** the foundation. The recurring shape is a derived document deciding something the
  authority left open (the historical examples are the Celery and PostgreSQL-16 drift and the TiTiler and
  S3/MinIO drift, both fixed by raising the decision into the foundation rather than by letting the derived
  file quietly decide).
- Its **version pointers** are current. A decision-provenance citation ("closed in v0.9") is history and does
  not move; a current-version pointer does.
- It does not reference a **section, requirement or document that does not exist** (`specs/testing.md` and
  `specs/dependencies.md` are the live examples: cited in several places, not yet written).
- A decision that closed recently completed its **fan-out** (handoff section 7): foundation as law, PRD
  requirement and acceptance, `CLAUDE.md` constraint or version pointer, session-handoff section 0,
  `.claude/rules/` where a rule enforces it, and one grep-able line in `specs/log.md`.

## 2. Check the documents against disk

```bash
git log --since="30 days ago" --name-only --pretty=format: -- "*.py" "*.ts" "*.rs" | sort -u
```

If there is no `.git` (the repository is being recreated), skip that and read the files directly: verification
here is reading the file on disk.

Then confirm the documents that make factual claims still hold: the repository layout in `CLAUDE.md` and
ADR-0001, the commands in `CLAUDE.md`, the state bullets in session-handoff section 0, the document catalog
in `specs/index.md`, and the versions and behaviours in `specs/dependencies.md` once it exists.

## 3. Report only what is wrong

- Flag what is **false or contradictory**, not what is missing. A gap the PRD already lists in its section 10
  is tracked, not drift.
- For each finding: the file, the exact excerpt, which authority it contradicts, and the correction.
- Say which side to fix. Almost always the derived document, except when the authority genuinely never
  decided, in which case the fix is to raise the decision to the authority, not to let the derived file keep
  deciding.

## 4. Output

A checklist of documents to update, ordered by severity: contradicts the foundation, contradicts another
derived document, false against disk, stale pointer.
