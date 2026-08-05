---
name: plan
description: Plan a feature for Mapsift before writing any code, grounded in the foundation and the codebase, then wait for confirmation. Use when the user asks to plan, design an approach, or think through a change before implementing. Triggers on "/plan".
argument-hint: "[feature description | path/to/spec.md]"
---

Plan the work described by: $ARGUMENTS

Run this INLINE. Do NOT call a subagent by default; do the analysis yourself in this conversation. If
`$ARGUMENTS` points to a file, read it first; otherwise treat it as the feature description. Produce a plan
only, write no code in this skill. Planning a task that will be dispatched as windows is the `orchestrate`
skill's job; this is the inline pass for work outside that loop, or the thinking that precedes it.

## 1. Restate the requirements

Restate the goal and scope in clear English. Call out anything ambiguous or underspecified and ask before
assuming. Trace the work to its authority: `specs/mapsift-foundation.md` (the constitution, the what and the
why) → `specs/PRD.md` and `CLAUDE.md` (both derived) → the ADRs in `specs/adr/` (code shape) → the per-task
spec in git (`specs/tasks/README.md`). Where a derived document and the foundation disagree, the foundation
wins and the derived one is wrong. Cite the specific requirement (a T, M, S, N or U item in the PRD, a
C-test in `CLAUDE.md`, an invariant I1 to I11) rather than gesturing at the document. Do NOT invent spec
documents or sections that do not exist, and do NOT build ahead of specs. If the work does not trace to the
foundation or the PRD, surface that instead of planning around a guess.

## 2. Ground it in the codebase

- Identify which deployable/library the work touches: `apps/api` (Django + django-ninja backend), `apps/web`
  (Angular), `libs/core` (the Rust client logic core), `libs/ui` (`@mapsift/ui`). Remember the layout rule:
  nothing in `apps/` imports from another `apps/`; everything shared crosses through `libs/`.
- Find the existing files and patterns this work touches or should follow.
- Place client logic correctly: the offline op queue, optimistic apply, conflict detection, and client-side
  geometry belong in `libs/core` (Rust), not in Angular. The UI is per-platform; the core is shared (C11).
- Respect the constraints relevant to the change: tenant isolation at the SQL layer, keyed on the **tenant**
  (the top container of an account) and never on the workspace (C4); type safety end to end (C5);
  preserve-not-discard for legal-weight geometry (C7); conflict-rule equivalence and server authority (C10);
  the serializable boundary (C11); idempotency (C12); authored and authorized writes (C13); mediated and
  gated agent writes (C14). Note any boundary the change crosses (PostGIS beyond the ORM, S3/MinIO,
  Copernicus/openEO, the tile servers, the sync transport) since those sit behind narrow interfaces.
- Do NOT plan anything into a folder ADR-0001 section 8 forbids for now: `apps/sync`, `apps/desktop`,
  `apps/mobile`, the sync engine internals, and the dependency-gated ADRs. Each has a named gate; if the
  work needs one, say which gate must open first.

## 3. Break into ordered phases

Lay out ordered phases, each with specific actionable steps, test-first in the two-window protocol under
the orchestrator: `specs/testing.md` section 1 is the method, 1.1 the prompt contract, 1.2 the sizing rule
(ADR-0008 section 4). A phase that does not fit one tracer bullet is two phases.

Every framework-owned file is created by its own generator and then edited, never hand-written (ADR-0002):
`ng g c|s|d|p|guard|interceptor` for Angular, `manage.py startapp` and `manage.py makemigrations` for
Django, `cargo new` and `cargo add` for Rust. Lead each phase with those commands. Sequence so each phase
leaves the relevant build and tests green.

## 4. Flag risks and dependencies

Call out risks, unknowns, ordering constraints, cross-cutting coupling, and any new dependency (which must
walk the gate in `specs/dependencies.md`, never a blanket approval, because Mapsift leans on fast-moving
libraries where stale knowledge is a defect). Flag anything that touches an open question (an OQ-N in the
foundation) or conflicts with the inviolable constraints in `CLAUDE.md`.

## 5. Present and wait

Present the plan and STOP. Wait for explicit user confirmation before writing any code. Once confirmed,
implementation follows the gate in the `dev-workflow` skill: the relevant lint, strict type check, and
tests must be green before any commit.
