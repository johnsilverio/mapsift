---
name: plan
description: Plan a feature for Mapsift before writing any code, grounded in the canon and the codebase, then wait for confirmation. Use when the user asks to plan a feature before code, wants an implementation approach, or says plan this. Triggers on "/plan".
argument-hint: "[feature description | path/to/spec.md]"
---

Plan the work described by: $ARGUMENTS

Run this INLINE. Do not call a subagent by default; do the analysis in this conversation. If `$ARGUMENTS`
points to a file, read it first; otherwise treat it as the feature description. **Produce a plan only, write
no code.**

## 1. Restate the requirement and trace it to its authority

Restate the goal and scope in clear English. Call out anything ambiguous and ask before assuming, because
**ambiguity in a spec is a defect and not a style issue**: a sentence that admits two readings is where two
sessions decide differently.

Trace the work through the chain: `specs/mapsift-foundation.md` (the constitution, currently v0.15) →
`specs/PRD.md` (requirements with acceptance criteria) → `specs/adr/` (code shape) →
`CLAUDE.md` and the per-repo docs. **Where a derived document and the foundation disagree, the foundation
wins and the derived one is wrong.**

**Cite the specific thing**, not the document: an invariant `I1` to `I23`, a numbered foundation section, an
ADR section. If the work does not trace to any of them, that is the finding: surface it rather than planning
around a guess. **Do not invent a document or a section that does not exist**, and do not build ahead of the
canon.

## 2. Check the open questions before planning around them

Sixteen open questions are live (foundation section 13) and several are hard blocks. The ones that most often
catch a plan: **OQ-1** blocks any `PaymentPlan` behaviour, **OQ-3** blocks shipping a module to real users,
**OQ-5** blocks any legal area computed anywhere, **OQ-7** blocks the first deploy, **OQ-8** blocks
publishing a retention promise, **OQ-10** blocks the embedded editor, **OQ-13** blocks the metered
notification channel. If the work depends on one, say which, and stop rather than inventing the answer.

## 3. Ground it in the codebase

- **Which stack:** `apps/api` (Django 5.2 with DRF, currently an empty folder) or `apps/web` (Angular
  21, scaffolded with no feature modules yet). ADR-0001 section 1 decided one repository and the move has not run, so
  they are still two git repositories today, and **neither imports code from
  the other**; the boundary is the generated OpenAPI contract.
- **Which package**, in the api: ADR-0002 section 2 has the fourteen packages, what each owns, and the tier
  order. **A package may import downward and never upward**, and CI enforces it with `import-linter`. Reach
  another package through its `selectors` and `services`, never its `models`; foreign keys use the string
  form so no import is needed.
- **Which module**, which is a different axis: a `Module` is the unit of activation (I19) and a package is
  the unit of dependency, mapped in ADR-0002 section 3.
- **Where the decision goes:** pure decisions in `rules.py`, reads in `selectors.py`, writes in
  `services.py`, which is the only writer and therefore the only outbox producer.

## 4. Check the constraints the change actually crosses

Name the ones that bind this work, not all of them:

- **Is this configuration or code?** The instinct to hand-build a screen for a specific service is almost
  always wrong: extend a piece. A form is a `FieldLayout`, a workflow is a pipeline, a document type is
  catalog data. **But an administrator never invents behaviour**: field types, computations, transition
  effects, guards, stage kinds, capability actions and validity kinds are closed catalogs in code (I17).
- **Does it write?** Then it carries the version contract (I5), an actor (I13), an idempotency key if it
  commits (I23), and an outbox row if the fact crosses a process (I12).
- **Does it select a party?** Then it declares a **role scope**, and creating from a relationship picker
  grants no role (foundation 4.9).
- **Does it touch a deadline?** Decide first whether it is a **legal term** (code, its norm cited, not bound
  by I16) or an **operational reminder** (pipeline configuration). They are never the same mechanism
  (foundation 5.12.2).
- **Does it delete?** It does not. Deactivation is the default, referential actions are restrictive, and
  there is no destroy action on the base viewset (ADR-0010 section 3).
- **Does it compute a legal area?** Then it is blocked by OQ-5.

## 5. Break into ordered phases, test-first

Ordered phases with specific steps, in the **two-window protocol**: one pass writes the failing tests as
behaviour, another implements the minimum to green using those tests as a contract it may not edit.
`specs/testing.md` is the canonical method; read section 7 for what not to test and section 6.1 for the
invariant-coverage rule.

**Name the `REQ-` identifiers each phase carries and stop there.** Section 1.1 is the contract for the
prompt that dispatches a window, and its rule reaches a plan too: the acceptance criterion in `PRD.md` is
already the behaviour, so a plan that transcribes it has made a second copy that drifts. A behaviour no
requirement covers is a **PRD change**, which is a commit, never a line invented in a plan.

**Framework files are generated, never hand-written**: `ng g c|s|d|p|guard|interceptor` on the web,
`manage.py startapp` and `makemigrations` on the api. Lead each phase with those commands, and sequence so
each phase leaves the build and the suite green.

## 6. Flag risks and dependencies

Risks, unknowns, ordering constraints, and any new dependency, which walks the gate in
`specs/dependencies.md` and is recorded with its rejected alternatives. **Never assert a library's behaviour
from memory**: this ecosystem leans on fast-moving pieces, and a design built on a misremembered API is a
defect. If you cannot verify, say so and give a confidence level.

If the change spans both stacks, say so and say that it is **one pull request** (`CLAUDE.md` "Process & tracking"
section 5).

## 7. Present and wait

Present the plan and STOP. Wait for explicit confirmation before writing any code.
