# ADR-0011: The logging path: structured records, the correlation keys, and redaction by allowlist

- **Status:** accepted (2026-08-14)
- **Deciders:** the owner, on the MAP-14 pickup (verification round against the package index, 2026-08-14)
- **Authority:** derives from `specs/mapsift-foundation.md` v0.18 (section 10, the observability decision closed in v0.16) and `specs/PRD.md` v0.16 (N9, N5, N12). Where this ADR and the foundation disagree, the foundation wins and this ADR is the one that is wrong.
- **Supersedes:** nothing. **Superseded by:** nothing.
- **Delivers:** the logging-library half that PRD N9's Open/ADR line had folded into the observability ADR, and the `specs/dependencies.md` row that says to decide it with the first code that logs; unblocks MAP-14.

---

## Context

PRD N9 asks for four things and only the last of them is a tool. The flush decision path must be
reconstructible end to end from an operation identifier a user quotes in a report. Logs must be structured
and carry their correlation keys **bound once per request and per background task** rather than passed by
hand, because the reconstruction is a join and a join cannot be added to free text later without editing
every call site. **Redaction must be a property of the path** rather than of each caller's diligence, since a
discipline that depends on every author is a leak with a date on it. And telemetry must be emitted
vendor-neutral so the backend stays swappable.

Foundation section 10 already constrained the mechanism with a dated caveat: as of May 2026 the
OpenTelemetry Python traces and metrics SDKs are stable while its **logs** SDK is still in development, so
the log path runs through the standard library with the trace identifiers injected into it. That caveat is
an input here rather than a question.

**Measured at this pickup, 2026-08-14: `apps/api` has no logging at all.** There is no `LOGGING` in
`config/settings.py`, no `import logging` and no `getLogger` anywhere in the package; ruff already runs with
`T20` so not even a stray `print` survives. This ADR therefore creates the path rather than adding to one,
which is the only moment it is cheap and the reason MAP-14 runs before MAP-37, MAP-38 and MAP-39, each of
which adds a decision N9 requires recorded.

What was genuinely open: which library carries the structured records, where the keys are bound, and what
shape redaction takes.

---

## Decision

### 1. The standard library carries the records, with a JSON formatter

Not `structlog` with `django-structlog`. The survey's leaning in `specs/dependencies.md` was the opposite and
is reversed here with its reasons on the record, because a reversed recommendation with no reasons is how the
next round reverses it back.

**This is not a compatibility refusal, verified 2026-08-14 against the package index.** `structlog` 26.1.0
(released 2026-06-06) requires Python 3.10 or later and carries no runtime dependency at all on 3.13.
`django-structlog` 10.1.0 (released 2026-05-30) declares Django 4.2 through 5.2 and Python 3.10 through 3.14
in its classifiers, so it fits the pinned Django 5.2.16 and Python 3.13.13 exactly. Both are current and
maintained. Four things decide against them anyway.

**It collects personal data by default, through a dependency it cannot drop.** `django-structlog` binds
`request_id`, `correlation_id`, `user_id` and **`ip`** per request, with `user_agent` on the request events.
The address comes from `django-ipware`, a **mandatory** requirement whose only purpose is extracting the
client IP from request headers. A setting turns it off (`DJANGO_STRUCTLOG_IP_LOGGING_ENABLED`), added for
exactly this concern. But N9 and foundation section 10 put redaction **on the path** and not on diligence,
and a library that is safe because three settings are right is diligence wearing a configuration file.

**The key it binds for free is not the set N9 asks for.** N9 names the operation identifier, the clientID,
the tenant, and the request or task. `django-structlog` supplies the request identifier. The other three are
ours to bind under either choice, so its principal advantage covers one key of four.

**Half its case has no consumer.** The survey's second argument was that it supports Celery by name, and
Celery is deliberately not installed (`specs/dependencies.md`): it is ratified and arrives with the code that
imports it, so nothing in the repository can exercise that integration today.

**And the one that decides it: `django.db.backends` logs SQL with its parameters.** The operation-log insert
carries `client_half` as a JSON payload containing geometry, so the redaction cannot sit only on our own
loggers, it has to sit on the **root handler** and cover Django's own. Through the standard library that is
one handler and one filter. Through `structlog` it is additionally the `ProcessorFormatter` bridge, because
records emitted by Django do not enter a `structlog` pipeline on their own. In fairness to the alternative,
`structlog`'s processor chain **is** a redaction-on-the-path mechanism and a nicer one than a filter; it is
the bridge that makes the total larger rather than smaller.

**The exit path, recorded now rather than when it is needed.** `structlog` consumes standard-library records
through `ProcessorFormatter`, so if the eventual backend or the client telemetry SDK makes a processor chain
the cheaper shape, the change lands at one wiring point and not at every call site. That reversibility is
what the vendor-neutrality rule was written to buy, and it is the reason this decision may be taken now
instead of waiting.

### 2. The keys are bound once per context, and the emitter reads them

The four keys of N9 are carried in a **context variable** bound once per request, and every record emitted
inside that context carries them **without the caller passing anything**. A caller that has to remember a
key is the design N9 rejects, in the same sentence and for the same reason it rejects a caller that has to
remember redaction.

The injection mechanism, a log-record factory against a filter, is the implementing window's to choose. The
property this ADR fixes is the one above: the keys reach the record from the context, never from the
signature.

### 3. Redaction is an allowlist, never a denylist

N9 requires that no geometry payload and no personal data reaches a log **regardless of what a caller
passes**. A denylist scrubs the fields somebody thought of and passes everything nobody did, which fails on
the first new field and fails silently. So the handler emits the correlation keys, the event name, and the
fields of a **closed named set**, and drops everything else rather than trimming it.

Two consequences follow and both are the point. Adding a field to that set is a deliberate act, and adding
one that carries geometry or personal data is a defect in the same class as a raw colour in a component
(PRD U1). And Django's own records pass through the same gate, which is what section 1 argued the whole
choice on.

### 4. One record per decision, with the operations it covers as a structured list

N9's reconstruction is a join from **one** operation identifier, and a flush carries a batch of operations
under one clientID. A record per decision, carrying the identifiers that decision covers as a structured
list field, answers that join. A record per operation multiplies the volume by the batch size and answers
nothing extra.

Where a decision is genuinely per operation it gets a record per operation, and the dedup drop is that shape
today, the conflict verdict later.

**The rule that keeps this honest: an identifier interpolated into a message string is not a join key.** A
key is a field.

### 5. Where each piece lives, under ADR-0007

The context carrier and the redaction filter live in **`mapsift/common/`**, because they are platform rather
than domain and every package may import them: the `import-linter` layers contract puts `common` at the
bottom with `exhaustive = true`, so this is the tier that already means what is needed.

The `LOGGING` configuration and the middleware registration live in **`config/`**, because that is Django
project wiring and ADR-0007 section 2 keeps domain code out of it.

The module names are the implementing window's, with one caution worth handing over rather than
rediscovering: `common/logging.py` does **not** shadow the standard library under absolute imports, and it
still reads badly at every call site.

### 6. The availability probes are exempt from the binding

`config/probes.py` answers liveness and readiness, and ADR-0010 decision 6 already exempts both from
authentication. A probe request carries no principal and no tenant, so binding on it emits records whose
correlation keys are empty, at whatever frequency the orchestrator polls. N9's acceptance calls a sync-path
record with no correlation key a review failure, and manufacturing a stream of them is the wrong way to
satisfy a probe. The middleware skips those paths: the same exemption as ADR-0010's, recorded twice because
the two reasons are different.

### 7. The refusals that never reach a handler

**Measured (`specs/dependencies.md`, probed 2026-08-07):** the five batch composition rules run inside a
Pydantic `model_validator` on `OperationBatch`, and an operation type outside the catalog is refused by the
generated discriminated union itself. Both answer 422 **before any handler is entered**, so there is no frame
of ours to log from.

N9 accepts that every user-visible refusal has a matching record and that every record was presented, so
those two must be reachable from the logging path. The seam is a **django-ninja exception handler**, which is
the one place both shapes pass through.

**If that seam turns out not to exist at the pinned django-ninja 1.6.2, the acceptance is split and said
so**, the way MAP-12's was, and never quietly shortened to what the code happened to reach.

### 8. What this decision does not take

The telemetry **backend**, the sampling policy, the dashboards and the alerting stay deferred with the
trigger foundation section 10 gave them: the first real users. The client telemetry SDK stays with them.
What moves out of that deferred ADR is the logging library alone plus the path shape above, on the plain
ground that the first code that logs arrived before the first user did.

---

## Consequences

**What this buys.** N9's reconstruction requirement becomes a join over fields that exist from the first
record rather than a retrofit across every call site, which is the only order in which it is cheap. Redaction
holds for code nobody on this team wrote, Django's own included, because the gate is on the root handler and
it drops rather than trims. And the dependency count does not move: the record path is the standard library,
which Django's own components already log through.

**What this costs, accepted with eyes open.**

- **The per-request binding is ours to write**, roughly the middleware plus a filter, where
  `django-structlog` would have supplied a request identifier. That is the price of not also supplying an IP
  address.
- **An allowlist is friction by design.** A field that should be logged and is not appears as a missing
  field rather than as an error, and the remedy is a deliberate addition to a named set. That is the
  intended failure direction: the alternative fails by emitting.
- **One more seam for the pre-handler refusals** (section 7), which exists only because the composition
  rules are validated where they belong rather than where logging is convenient.

**What this forecloses.** Nothing the foundation left open. The backend, the sampling and the client SDK keep
their trigger; section 1's exit path keeps `structlog` available at one wiring point; and the vendor
neutrality of foundation section 10 is what both of those rest on.
