# MAP-14: A flush's decisions are reconstructible from one operation identifier, and no record carries geometry or personal data

## Trace

PRD **N9** (the requirement, its mechanism half, and its acceptance), **N5** (what personal data means here),
**N12** (the probes this path must not drown). Foundation **section 10**, the observability decision closed in
v0.16 with its dated OpenTelemetry caveat. **ADR-0011** is the code shape, in full: section 1 the library,
2 the binding, 3 the redaction, **4 the record granularity and the closed wire vocabulary**, 5 the placement
under **ADR-0007** sections 1, 2 and 4, 6 the probe exemption, 7 the refusals that never reach a handler
**with every one of its dated notes, which are named rather than counted: the provenance correction, the
resolution, the sharpening that followed hours later, the settlement of the `DEBUG` branch, and the
departure from the vendor's `logger.exception`**; the third supersedes the second on what the `Exception`
entry does, and at DEBUG false that entry is a pass-through rather than a logging seam. *(This sentence
carried a number three times and the number was wrong three times, each correction outlived by the next note
added to that section in the same session. **Naming is the repair rather than recounting**: an enumeration
missing an item is visible to a reader, a wrong total is not.)*
**ADR-0005** is cited for the tenant binding the flush runs inside, which is a **different** mechanism at a
different scope from ADR-0011 section 2's per-context key binding and must not be read as nesting one in the
other. **ADR-0010** decision 6 for the route and its refusal shapes.

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
- **The credential refusals on this route, the `401` and the CSRF `403`.** Owner: **MAP-48**. *(It named
  "ADR-0010's seam" until 2026-08-14, which is where they are taken and not something that can be closed, so
  nothing tracked them ever reaching N9's clause.)* **Counted rather than asserted, 2026-08-14:** this block
  holds six deferrals and **two** now name an issue, this one and the deferred decision categories. The
  other three that need an owner name a trigger instead, the observability ADR twice and "the issue that
  installs Celery" with no identifier, which is a weaker form and is left as it is deliberately rather than
  overlooked. *(This sentence read "every other deferral in this block names an issue" until it was counted,
  which made it the fourth set-claim of the day that its own set did not support, written inside the fix for
  the third.)* Declared here rather than left silent (added 2026-08-14, at the
  Window A review, where the Spec axis found them neither covered nor named): they are user-visible refusals
  on the same path, so N9's every-refusal clause does reach them eventually, and the ground for deferring is
  that **neither is lost work**. A rejected credential leaves the client's queue intact and retryable. The
  `404` of a claim the principal cannot back is the one that is not, which is why it has a case here.
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
7. The seam for the refusals that answer before any handler is entered. **Section 7 and every one of its
   dated notes, named in the Trace above**: the conditional does not fire and the split-and-say-so
   fallback is spent, because
   `ValidationError` is a real handler with a real body and both pre-handler refusals arrive there. **The
   third note corrects the second**, and only about `Exception`, which is a pass-through at DEBUG false, so
   the *failure with no user-visible signal* clause is reached through Django's own `log_response` and
   registering our own handler is a choice about the record's shape rather than a necessity.

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
  JSON containing geometry.** *Read from the code rather than measured, and labelled so on purpose:*
  `OperationLogEntry.client_half` is a `JSONField` and the envelope's geometry payload reaches it. This is the
  fact that forces the allowlist onto the root handler rather than onto our own loggers, and it is why a test
  that only exercises our own call sites proves less than it looks. **A window that depends on it should
  witness it rather than trust this bullet**, which is what the label is for.
- **Two refusals answer 422 before any handler is entered**, and their provenance differs, which the first
  version of this bullet flattened into one label (corrected 2026-08-14, see ADR-0011 section 7's note). The
  **catalog** half is *probed 2026-08-07 and recorded in `dependencies.md`*: an operation type outside the
  catalog is refused by the generated discriminated union itself. The **composition rules** are *decided, not
  probed*: they run in a Pydantic `model_validator` on `OperationBatch` under ADR-0010 decision 6, whose fifth
  rule is dated 2026-08-13. Both hold in the code today.
- **The seam for both of them exists**, so ADR-0011 section 7's conditional does not fire and the acceptance
  is not split on that ground. *Verified 2026-08-14 in the installed source at the pinned django-ninja
  1.6.2:* `set_default_exc_handlers` registers `Exception`, `Http404`, `HttpError` and `ValidationError`.
  **The trap that rides with it:** registering your own `ValidationError` handler **replaces** that default,
  and ADR-0010 decision 6 makes the malformed refusals tell each other apart **by their bodies**, which
  existing cases assert.
- **A test that reads state after a refusal is blind to whatever that refusal's transaction unwound.**
  *Measured at MAP-45, 2026-08-14, in this same package.* The flush's catch sits outside the `atomic()` block
  `tenant_scope` opens, so a case asserting on rows after a refusal cannot see what the rollback took with it;
  **three** docstrings in `test_the_typed_resend_on_a_gap.py` claimed a discriminating power that seam makes
  impossible, two were corrected and one was struck, becoming MAP-46. *(Counted from commit `5ffcb78`, which
  is the only commit that ever touched that file for MAP-45 and whose hunks reach exactly three test
  functions. This bullet said four until 2026-08-14, taking the number from a handoff sentence that had
  borrowed it from a different set, the four state-reading siblings that stayed **green** under the mutant.
  `specs/log.md` was right and the summary of it was not.)* **Handed over because this task is a refusal path too**
  and the same shape is available to it.
- **A record emitted inside a transaction that later rolls back survives it, so logging is not
  transactional.** *Measured at this task's Window B, 2026-08-17, and the ADR is the authority:* **ADR-0011
  section 4's extension of that date** carries it as law, and the consequence it draws is what a window
  needs, that a record asserting a decision took effect is emitted only after the commit. *(Until 2026-08-17
  this bullet ended by refusing to hand over the conclusion, on the ground that nobody had measured it. That
  was correct when written and false the moment the window measured it, and the ADR was swept while this
  document was not. Found by the Spec axis at the Window A correction round, which is the third time in one
  session that a fan-out reached the decision and missed a **fact the decision changed in passing**.)*

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
- **Narrowed by the Out of scope block, and here is where that block meets this one** (written 2026-08-14,
  replacing a sentence that said "nothing else is narrowed" while the block below deferred two things that
  are exactly narrowings; each half was defensible alone and the conjunction was false, which is the shape
  MAP-45 recorded and the `fan-out` skill still has no step for). N9's clause *every user-visible refusal has
  a matching record and the reverse* **is narrowed twice**: the `401` and the CSRF `403` are deferred to
  **MAP-48**, and the conflict, authorship and force-upgrade decisions are deferred to the issues that
  create them. *(This line said "ADR-0010's seam" until 2026-08-14, hours after the Out of scope block below
  had already been corrected to name the issue; one block was swept and its twin was not.)* **Out of scope is authoritative for both**, so read it as part of this block rather than after
  it.
- **Not narrowed, and named because narrowing it would have been the easy move:** *a failure with no
  user-visible signal and no record fails review* is in scope **as written**. It is the moral line of the
  whole requirement, and the record it needs is reachable. **By which route is Window B's to pick**, and the
  measurement is in `specs/dependencies.md` under django-ninja's four default handlers: `_default_exception`
  re-raises at `DEBUG` false, so Django's own `log_response` writes the record and it crosses the root
  handler like any other. *(This bullet said "the seam it needs exists, django-ninja registering a default
  handler for `Exception`" until 2026-08-14. Registration is not a body, the ADR had already retired that
  reading in section 7's second note, and this sentence had not been swept with it.)*

From **ADR-0011 section 6**, which is this task's own and is what the suite pins: an availability probe
manufactures no record whose correlation keys are empty. **N12's own clause, that the liveness probe keeps
passing while a dependency is down, is already carried by `tests/test_probes.py` and is not this task's to
re-prove** (corrected 2026-08-14, where this line named the N12 clause over a suite that asserts the section
6 one; each sentence was true and they were not about the same thing).
