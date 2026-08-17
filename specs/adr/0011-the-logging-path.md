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

> **Extended 2026-08-17, at MAP-14's Window B review, where the Canon and Spec axes measured the same defect
> independently. A middleware alone does not satisfy the sentence above.** Django logs every 4xx and 5xx
> itself, in `BaseHandler.get_response`, **after the whole middleware chain has returned**, so a context a
> middleware opened has already closed and that record crosses the handler carrying **none** of the four
> keys. Measured on this route: a 422, a 404 and a 409 each emit one correct record and one orphan, and a
> **405 emits only the orphan**, no view of ours having run at all. The 500 is the contrast that proves the
> diagnosis rather than an exception to it, since `response_for_exception` fires **inside** the chain and its
> record does carry the key.
>
> **The mechanism, and it rests on a property of the emitter rather than on a trick:**
> `django.utils.log.log_response` emits with `extra={"status_code": ..., "request": request}`, so the record
> holds the request even where no context is in force. The binding writes its keys onto the request as well
> as into the context, and the filter falls back to the request when the context is empty.
>
> **The alternative is refused with its reason.** A context opened at request start and never closed leaks
> into whatever that thread or task serves next, which under ASGI is another request. A scope that never
> exits is not a scope, and a correlation key bleeding across requests is worse than an absent one because
> it joins a report to the wrong work.
>
> **What this covers is wider than the refusals this task set out to record:** every status Django answers on
> this route, the ones no view of ours produces included.

> **Sharpened 2026-08-17, at the second Window B review, on three points where the paragraph above was
> narrower than what actually satisfies the requirement. The implementation was right and the wording was
> not.**
>
> **The fill is per key, not "when the context is empty".** At the failure handler's frame the context still
> holds the request identifier while the operations have already unwound, so a wholesale fallback would
> refuse to fill the keys that are missing. Per key is the superset, and it is what lets one handler stay
> the single recorder of a failure.
>
> **What the request remembers deliberately outlives the block that wrote it**, and that is load-bearing
> rather than an oversight: the handler that records a failure runs **after** the view's context has already
> reset, so a symmetric restore on exit would empty the carrier exactly where it is needed. Restoring it is
> the obvious-looking fix and it breaks the case this mechanism exists for.
>
> **The merge is widest-first, never last-writer-wins**, and this is the one the first implementation got
> wrong. A narrower binding opened inside a wider one, one per deduplicated operation, overwrote the whole
> batch on the carrier, so a flush that deduplicated and then failed named **one** operation in its failure
> record and left the operations that actually failed in no record at all. Measured at that review against
> the ordinary partial resend C12 makes routine. The carrier therefore takes the keys it does not already
> hold and keeps the ones it does, while the context still wins wherever it holds a key, so a per-operation
> record stays narrow.
>
> **One consequence for whoever reads the trail, settled 2026-08-17 and armed for MAP-37, MAP-38 and
> MAP-39: a record naming an operation is not necessarily ours.** Django's own record about a response
> carries the keys this section grants it and carries **no event of ours**, so a reader that takes the event
> off every record naming an operation raises rather than answers. **A reader skips what carries no event of
> ours and carries on**, which is the only reading consistent with this section admitting those records to
> the path in the first place; asserting they cannot exist would contradict the paragraph above it.

### 3. Redaction is an allowlist, never a denylist

N9 requires that no geometry payload and no personal data reaches a log **regardless of what a caller
passes**. A denylist scrubs the fields somebody thought of and passes everything nobody did, which fails on
the first new field and fails silently. So the handler emits the correlation keys, the event name, and the
fields of a **closed named set**, and drops everything else rather than trimming it.

Two consequences follow and both are the point. Adding a field to that set is a deliberate act, and adding
one that carries geometry or personal data is a defect in the same class as a raw colour in a component
(PRD U1). And Django's own records pass through the same gate, which is what section 1 argued the whole
choice on.

> **Clarified 2026-08-17, at MAP-14's Window A review, where a review axis read the sentence above both
> ways.** What the gate drops is a **field**, never the record. A record that carries no allowlisted field
> beyond its keys is still emitted, carrying its keys and its event and nothing else. **Dropping the whole
> record is the reading this ADR refuses**, and the reason is N9's own acceptance rather than taste: a
> requirement that every user-visible refusal has a matching record cannot be satisfied by a gate that
> silently deletes records it does not recognise, and a path that answers "no record" and a path that
> answers "a record with nothing in it" are the difference between silence and evidence. It is also what
> makes the sync-path clause testable, since a record that is never emitted cannot be a line with no
> correlation key.

> **Extended 2026-08-17, same review, closing the hole the clarification above left open.** The guarantee
> holds **even when an allowlisted field will not serialize**. An encoder that raises inside the formatter
> loses the **whole record**, which is exactly the outcome the clarification refuses, arriving through the
> encoder instead of through the gate. The encoder therefore degrades an unexpected value to its string form
> rather than failing on it. **The shape worth naming: a guarantee stated about one mechanism is not a
> guarantee about the path**, and the second way to lose a record is the one nobody writes a rule against.

> **Extended 2026-08-17, same review, and this one is about a record escaping the gate rather than being
> lost inside it. The `LOGGING` configuration redefines `loggers`, so no handler survives outside the
> allowlist.** Django applies its `DEFAULT_LOGGING` before ours, and a configuration that adds a root
> handler without redefining `loggers` leaves the `django` logger still carrying `console` and
> `mail_admins`, **neither of which passes the gate**. Measured at this review: it leaks nothing today,
> because `console` is `require_debug_true` at INFO while the SQL records section 1 argued the whole choice
> on are DEBUG, and `mail_admins` is inert while `ADMINS` is unset. **That is exactly the shape this ADR
> refused when it refused `django-structlog`**: a path that is safe because two settings happen to be right
> is caller diligence wearing a configuration file, and the guarantee this section states is unconditional.
> One day somebody sets `ADMINS` and redaction stops holding on that path with nothing turning red.

### 4. One record per decision, with the operations it covers as a structured list

N9's reconstruction is a join from **one** operation identifier, and a flush carries a batch of operations
under one clientID. A record per decision, carrying the identifiers that decision covers as a structured
list field, answers that join. A record per operation multiplies the volume by the batch size and answers
nothing extra.

Where a decision is genuinely per operation it gets a record per operation, and the dedup drop is that shape
today, the conflict verdict later.

**The rule that keeps this honest: an identifier interpolated into a message string is not a join key.** A
key is a field.

> **Added 2026-08-14, at MAP-14's Window A review, because the names were being fixed by a test suite and by
> no document.** A record's field names and its event names are a **contract**, not a suite convention:
> MAP-37, MAP-38 and MAP-39 each add a decision to this path and will read these names to do it, and a
> vocabulary that lives only in `conftest.py` is one the next window reinvents. The closed set is
> **`operation_ids`** (a list on **every** record, so the join has one name whether the decision covers one
> operation or fifty), **`client_id`**, **`tenant_id`**, **`request_id`**, **`event`**, **`status`** and
> **`reason`**. The events this path names today are **`flush.applied`**, **`flush.deduplicated`** and
> **`request.refused`** and, added 2026-08-14, **`request.failed`**; a new decision adds a name here first and
> emits it second.
>
> **`request.failed` is separate from `request.refused` rather than folded into it**, and the correction
> round that asked for it was right to refuse to choose alone. A **refusal is a decision the server took**
> and carries a reason from a closed set; a **failure is a decision nobody took**, and a 500 has no reason to
> give. Stretching one name over both would make the trail answer the support desk's first question wrongly,
> which is whether anything decided anything at all, and that question is the whole of N9's moral half.
>
> **Which field rides on which event, added 2026-08-14 because closing the names left the mapping open and a
> test suite was fixing it by assertion.** The four correlation keys ride on **every** record, as far as the
> context holds them, which is the "none of the four" clause above and not "all four". `event` is on every
> record. **`status` is on the two records that answered a client**, `request.refused` and `request.failed`.
> **`reason` is on `request.refused` alone**, which is the same distinction one paragraph up read from the
> other end: a failure has no reason to give, so emitting an empty one would be a field pretending a decision
> happened.
>
> **The identifier keys emit as the canonical hyphenated lowercase string**, not as an integer, a compact
> hex form or a nested object. This is a value contract rather than a field contract, and it is here because
> a join across two records is a string comparison in whatever backend eventually reads them; a producer that
> spells the same identifier two ways has broken the join without breaking any test that checks one producer.
> **`status` emits as the integer**, for the mirror reason: `"422"` and `422` do not compare equal and a
> dashboard filtering on one silently loses the other.
>
> **What "closed" does and does not close, added 2026-08-14 because the first reading of it was a trap.** The
> set above closes **the names this path chooses**. It does **not** close a record's envelope: a timestamp
> and a severity are what makes a structured record a record at all, they are the formatter's rather than a
> decision's, and section 3's allowlist is not to be read as forbidding them. A reviewer applying the closed
> set to a timestamp would refuse the only shape a log can have, which is what happens when a rule written
> about one layer is enforced against another.
>
> **Reason *values* are deliberately open and this is the sentence that says so.** The names are closed;
> what a `reason` may contain is not. The `409`'s values come from `WhyAStreamCannotBeContinued`, a closed
> set that already exists in `mapsift/sync/rules.py` and is owned there; the `404`'s has no upstream and is
> the implementing window's to choose, because inventing one here would be this ADR deciding a wire value it
> has no requirement for. What is **not** open is that the field be present on a `request.refused` record.
>
> **`operation_ids` is a list and never a delimited string**, which reads as pedantry and is not: `in`
> answers the same for `["a", "b"]` and for `"a,b"`, so the distinction is invisible to the obvious reader
> and the shape stops being enforced the moment one is written.
>
> **What "carries no correlation key" means, since the two readings differ where it matters:** a record fails
> the N9 clause when it carries **none of the four**, not when it is missing one. A refusal taken before a
> batch is parsed has a request and no tenant, no clientID and no operation, and demanding all four would
> fail precisely the records this requirement exists to guarantee.

> **Extended 2026-08-17, at MAP-14's Window B review, on when a record is emitted rather than on what it
> carries. A record asserting that a decision took effect is emitted only once the transaction that effected
> it has committed.** Logging is not transactional, measured at this task: a record written inside a
> transaction survives that transaction's rollback. So a record written before the commit is a claim about a
> state that may never exist, and the trail then reads *applied* over a database holding nothing, which is
> the mirror of N9's requirement that every recorded refusal was presented. **It is the direction no case
> covers**, because reaching it needs a commit to fail. **A refusal record is unaffected and stays where it
> is taken**, a refusal being true whether or not anything committed. This binds MAP-37, MAP-38 and MAP-39
> as much as this task, each of them adding a decision that takes effect.
>
> **Corrected 2026-08-17, hours later, because the rule above named two categories over a set of three and a
> window would have had to choose between two approved cases in the dark.** The third is **a record about
> what a flush declined to write**, `flush.deduplicated` today, and it is emitted **where it is taken**,
> like a refusal and unlike an application. A drop asserts that an earlier flush already applied the
> operation, which is true whether or not this one commits, so deferring it to a commit that never comes
> would lose the one record a resent-and-then-failed flush has to offer. **The test that sorts the three:
> ask what the record would be false about if the transaction vanished.** An application would be false
> about the write, so it waits; a refusal and a drop would still be true, so they stay. *(Found by the Craft
> axis, which noticed that two cases approved in the same round pin opposite timings and that neither the
> rule nor either docstring said why.)*

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

Two refusals answer 422 **before any handler is entered**, so there is no frame of ours to log from. The
five batch composition rules run inside a Pydantic `model_validator` on `OperationBatch`, and an operation
type outside the catalog is refused by the generated discriminated union itself.

> **Provenance corrected 2026-08-14, hours after this section was written, by the pre-dispatch read of
> MAP-14's spec.** The sentence above carried one label, "measured, `specs/dependencies.md`, probed
> 2026-08-07", over **two** facts of different origin, and only one of them is that probe's. The
> **discriminated union** half is: it is the MAP-10 pickup entry in `dependencies.md` section 1. The
> **composition rules** are ADR-0010 decision 6, and its **fifth** rule was decided **2026-08-13**, so it
> could not have been probed six days earlier. Both are true of the code today, at
> `mapsift/sync/api.py` and `mapsift/sync/rules.py`; it was the citation that was wrong, not the fact.
> **The shape is this canon's most-recorded defect wearing a new costume:** one label stretched across a set
> whose members do not share it, which is the same operation as a count taken from a different set.

N9 accepts that every user-visible refusal has a matching record and that every record was presented, so
those two must be reachable from the logging path. The seam is a **django-ninja exception handler**, which is
the one place both shapes pass through.

**If that seam turns out not to exist at the pinned django-ninja 1.6.2, the acceptance is split and said
so**, the way MAP-12's was, and never quietly shortened to what the code happened to reach.

> **Resolved (2026-08-14, the same day, at MAP-14's Window A review). The conditional does not fire and the
> acceptance needs no split.** Measured in the installed source rather than read from a report:
> `ninja.errors.set_default_exc_handlers`, called from `ninja/main.py` at `NinjaAPI` construction, registers
> **four** handlers by default, `Exception`, `Http404`, `HttpError` and **`ValidationError`**, and both
> pre-handler refusals surface as the last of those. So the seam exists, and the `Http404` entry is what the
> membership refusal travels through. **Two consequences that are not the same sentence.** Registering a
> handler for `ValidationError` **replaces** django-ninja's default one, and ADR-0010 decision 6 makes the
> malformed refusals "told apart by their bodies", with cases in `test_authenticated_request.py` and the
> batch-agreement suite asserting exactly those bodies, so a seam that logs without re-emitting the identical
> body breaks a wire contract that is law. And the `Exception` entry is what N9's *failure with no
> user-visible signal* clause reaches, which is why that clause is in scope as written rather than split.
>
> **Sharpened 2026-08-14, later the same day, by MAP-14's correction round measuring what that entry
> *does* rather than that it exists.** django-ninja's `_default_exception` reads `if not settings.DEBUG:
> raise exc  # let django deal with it`, so **at DEBUG false it is a pass-through and not a logging seam**.
> The clause is still reachable, and by two routes rather than none: Django's own
> `core/handlers/exception.py` calls `log_response` on the re-raised failure, and **that record passes the
> root handler like any other**, so it acquires the bound keys and the allowlist by construction. Registering
> our own handler is therefore **a choice about the record's shape, not a necessity for its existence**.
> Window B picks one and says which. *Recorded here because the first version of this note said the entry was
> the seam, which was an inference from its registration rather than from its body.*
>
> *Recorded here because it was found living only in a test docstring, which is the one place no grep looks
> and no fan-out reaches. A version-pinned measurement belongs to the pin.*

> **Settled 2026-08-17, at MAP-14's Window B review: a handler registered here keeps the vendor's `DEBUG`
> branch.** Registering our own for `Exception` **replaces** django-ninja's, whose body returns a plain-text
> traceback at DEBUG true and re-raises at DEBUG false. Re-raising unconditionally is simpler and changes
> what a developer sees for no gain. **A silent divergence in developer experience is a cost with no
> benefit**, and it is the kind that is discovered months later by someone who assumes their tooling is
> broken. Record the decision, then behave as the vendor does on both sides of the flag.
>
> **One deliberate departure from "as the vendor does", added the same day at the second Window B review:
> the vendor's own `logger.exception` is not reproduced.** Its record would reach the allowlist carrying no
> allowlisted field, so it would emit keys with no event and no content, and `request.failed` already
> carries what that record was for. **The departure is recorded here because the code cannot say it:** a
> reader diffing against the vendor sees a missing line, and a comment claiming both arms are the vendor's
> invites restoring it.

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
