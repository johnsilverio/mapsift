# MAP-14: A flush's decisions are reconstructible from one operation identifier, and no record carries geometry or personal data

## Trace

PRD **N9** (the requirement, its mechanism half, and its acceptance), **N5** (what personal data means here),
**N12** (the probes this path must not drown). Foundation **section 10**, the observability decision closed in
v0.16 with its dated OpenTelemetry caveat. **ADR-0011** is the code shape, in full: section 1 the library,
2 the binding, 3 the redaction, 4 the record granularity, 5 the placement under **ADR-0007** sections 2 and 3,
6 the probe exemption, 7 the refusals that never reach a handler. **ADR-0010** decision 6 for the route and its
refusal shapes; **ADR-0005** for what the binding runs inside.

Invariants: **I9** and **I10**, whose decisions are what N9 requires recorded. Constraints: **C6** and the
privacy posture (a record is a place production data leaks to), **C12** and **C13** (the dedup decision and the
authorship normalization are two of the five things N9 names by name).

## What this task owns

The logging path exists, and the flush's decisions are on it: a report quoting one operation identifier leads
to what the server decided about that operation and why, while nothing the path emits carries a coordinate or
a person.

## Out of scope

- **The telemetry backend, the collector, the sampling, the dashboards and the alerting.** Owner: the
  observability ADR, trigger unchanged at the first real users (foundation section 10; `dependencies.md`
  agenda item 15, narrowed 2026-08-14).
- **The client telemetry SDK and the browser half of N9.** Same owner, same trigger.
- **The per-background-task binding.** N9 asks for it and **Celery is deliberately not installed**
  (`dependencies.md`), so there is no runtime for that half here. It is **declared and not built**, and the
  acceptance below is split accordingly rather than shortened: the clause is named, its half is marked as
  having no runtime, and the issue that installs Celery inherits it. This is the MAP-12 rule about a clause
  with no runtime, applied deliberately.
- **The decisions that do not exist yet.** N9 lists conflict verdicts, authorship normalizations and
  force-upgrade rejections. Owners: **MAP-38** and the conflict slice, **MAP-37**, and the versioning
  mechanism (OQ-15). This task builds the path and puts on it **only the decisions the flush takes today**,
  which is why it runs before those three rather than after.
- **The Rust and TypeScript sides.** Nothing in `libs/core` or `apps/web` changes.

## Boundary decisions the owner closed

All closed at the 2026-08-14 pickup and **registered before this file was written**. The record is ADR-0011,
which is where to read them; this is the pointer.

1. The library, and it went **against** `dependencies.md`'s own leaning. **ADR-0011 section 1.**
2. Where and how the keys are bound. **Section 2.**
3. Redaction as a closed allowlist rather than a denylist. **Section 3.**
4. One record per decision rather than per operation. **Section 4.**
5. Where each piece lives under ADR-0007. **Section 5.**
6. The availability probes are exempt from the binding. **Section 6.**
7. The seam for the refusals that answer before any handler is entered, **with the split-and-say-so fallback
   if that seam does not exist at the pinned version**. **Section 7.**

The fan-out that closed them: `specs/dependencies.md` (the row and agenda item 15), `specs/PRD.md` N9's
Open/ADR line, `CLAUDE.md`, `specs/index.md`, `specs/log.md` (one decision entry and one trap entry), and
`.claude/rules/python-django.md`.

## Evidence handed over

- **`apps/api` has no logging at all.** *Measured 2026-08-14 at this pickup:* no `LOGGING` in
  `config/settings.py`, no `import logging` and no `getLogger` anywhere in the package. This task creates the
  path rather than adding to one, and nothing existing needs migrating onto it.
- **`structlog` 26.1.0 and `django-structlog` 10.1.0 both fit the pinned Django 5.2.16 and Python 3.13.13.**
  *Verified 2026-08-14 against the package index.* Handed over so nobody re-runs it: the refusal in ADR-0011
  section 1 is **not** a compatibility refusal, and reopening it on compatibility grounds is reopening
  something already measured.
- **`django.db.backends` logs SQL with its parameters, and the operation-log insert carries `client_half` as
  JSON containing geometry.** This is the fact that forces the allowlist onto the root handler rather than
  onto our own loggers, and it is why a test that only exercises our own call sites proves less than it looks.
- **Two refusals answer 422 before any handler is entered.** *Probed 2026-08-07, recorded in
  `dependencies.md`:* the five composition rules run in a Pydantic `model_validator` on `OperationBatch`, and
  an operation type outside the catalog is refused by the generated discriminated union itself.
- **A test that reads state after a refusal is blind to whatever that refusal's transaction unwound.**
  *Measured at MAP-45, 2026-08-14, in this same package.* The flush's catch sits outside the `atomic()` block
  `tenant_scope` opens, so a case asserting on rows after a refusal cannot see what the rollback took with it;
  four docstrings in `test_the_typed_resend_on_a_gap.py` claimed a discriminating power that seam makes
  impossible, three were corrected and one was struck. **Handed over because this task is a refusal path too**
  and the same shape is available to it. **What is not handed over is the conclusion:** whether a record
  emitted inside a rolled-back transaction survives is a property of the logging path this task is about to
  build, and it has **not** been measured. Deciding it is the window's, and it is exactly the kind of claim
  that must be witnessed rather than reasoned.

## Acceptance

**The criteria are PRD N9's and are read there.** This block carries only what this task does differently.

> **Rewritten 2026-08-14, and this file is the worked example of why the rule changed.** It previously
> announced itself as "Copied from PRD N9" and carried five of that requirement's six clauses plus one
> promoted from its mechanism half. The Spec axis caught it **after** Window A had already run against it.
> The Acceptance block is now the delta rather than the copy (ADR-0008 section 9), which is what makes the
> omission that produced this note impossible rather than merely discouraged.

- **Split, and said so.** N9's mechanism half binds the keys "once per request and per background task". The
  **per-request** half is in scope. The **per-background-task** half has **no runtime in this repository**,
  Celery being deliberately not installed, so it is declared and not built, and the issue that installs
  Celery inherits it.
- **Deferred, with its owner.** N9's clause that the emitted telemetry is readable by a second backend
  without changing application code cannot be asserted without a second backend. It stays with the
  observability ADR whose trigger is the first real users, beside the client telemetry SDK.
- **Nothing else is narrowed**, and one clause is named here only because narrowing it would have been the
  easy move: *a failure with no user-visible signal and no record fails review* is in scope **as written**.
  It is the moral line of the whole requirement, and the seam it needs exists, django-ninja registering a
  default handler for `Exception` (verified 2026-08-14 in the installed source at the pinned 1.6.2).

From N12, because this path can break it: the liveness probe keeps passing while a dependency is down, and
nothing this task adds makes a probe touch one.
