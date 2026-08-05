---
name: systematic-debugging
description: Four-phase debugging methodology with root cause analysis for the Mapsift ecosystem (Django API with DRF, Angular client, PostgreSQL with PostGIS). Use when investigating bugs, fixing test failures, or troubleshooting unexpected behavior. Emphasizes NO FIXES WITHOUT ROOT CAUSE FIRST.
---

# Systematic debugging (Mapsift)

## Core principle

**NO FIXES WITHOUT ROOT CAUSE FIRST.**

Never apply a patch that masks the underlying problem. Understand why something fails before changing
anything. In this product the stakes make it concrete: a wrong projection is a liability with a matrícula
number on it, a lost outbox event is two systems disagreeing with no record that they do, and a one-day
error on a validity date is a process advancing at a registry office on a document the system should have
refused.

## Four-phase framework

### Phase 1: reproduce and investigate

Before touching any code:

1. **Write a failing test** that captures the wrong behaviour. It is the regression test afterwards.
2. **Read the error message in full.** Every word, including the frames you are tempted to skip.
3. **Look at what changed.** `git diff`, `git log`. If the behaviour was specified, the spec says what it
   was supposed to be: an invariant, a foundation section, an ADR section.
4. **Trace the data flow** to where the bad value is born, not where it surfaces.

### Phase 2: isolate

Narrow it down. Log at the decision points, not everywhere. And **log the party UUID, never the name or the
tax id** (foundation 9.3): a debug line with personal data in it survives into production logs.

### Phase 3: state the root cause as a violated assumption

Not "the date was wrong" but "the code assumed the installation timezone applies to a legal date, and I20
says a legal date is a date and is never converted". A root cause stated as an assumption tells you whether
the fix is local or whether the same assumption is made in four other places.

### Phase 4: fix and prove

1. The fix addresses the cause, not the symptom.
2. The reproduction test passes and would have failed before.
3. `/quality-gate` is green for the stack touched.

## The failure modes this system actually has

Generic Django advice does not fit: `apps/api` is a **DRF** JSON API with no server-rendered templates and no
Django Forms, the queue is **Procrastinate on PostgreSQL with no broker**, and half the guarantees live in the
database rather than in the application. The recurring bugs are these.

**Identity duplication.** A second party where a role should have been attached, which is almost always a
create path that inserted before searching the normalized identifier (foundation 7.5). Its mirror: a picker
offering the wrong people, which is a party selector called with no **role scope**, so a spouse or a
neighbouring-lot owner appears in a client field.

**The catalog and the resolver.** A value that vanished after a promotion, which is a caller reading
`custom_fields` directly instead of through the resolver (ADR-0006 section 4). A write validated against the
wrong rules, which is a stale **layout version** that should have been rejected explicitly. A field required
where it should not be, which is `is_required` having drifted onto the definition instead of the placement.
And after v0.11: **a service layout that changed when its nature layout changed**, which means somebody
turned the copy into a link (ADR-0012 section 2).

**Dates, and this is the one that costs a day.** The installation runs at **UTC minus four**. A legal date
converted by a timezone moves a certificate's expiry by a day (I20). A completeness figure with no
**reference date** is not wrong, it is meaningless (I15). And the annual-exercise kind is valid through the
end of its exercise year **plus a grace declared on the type**, so a document that looks expired may not be.

**The outbox.** An event written outside the state change's transaction, which reintroduces the dual-write
problem the whole design exists to prevent (I12). A consumer that is not idempotent. A dead-letter row with
no alarm. If the state changed and no event exists, the write did not go through `services.py`, which is the
only writer and therefore the only producer.

**Attribution and connection state.** A write with a null author, which is a context that was not set. And
the silent one: **context set as a session property instead of transaction-scoped** (foundation 3.1), which
works until a connection pooler in transaction mode is put in front of the cluster and then fails with no
error at all, objects resolving in the wrong schema and audit rows authored by nobody.

**Concurrency, and the two mechanisms that are not the same.** Two people editing from one read state is
**I5**, the version contract and a 409 carrying enough state to merge. One person sending twice, a double
click or a mobile retry, is **I23**, the idempotency key. Approving a proposal twice produces two sets of
executions and two sets of charges, so a bug here is financial. **A 409 does not fix a double click and an
idempotency key does not fix a conflict.**

**Money and numbering.** A `FloatField` on a monetary column. A rounding rule applied at a different step
than the one declared, which makes a total irreproducible against a frozen snapshot (I21). A number
allocated at draft creation instead of when it becomes public, which burns the series on abandoned drafts
(I22).

**Legal terms.** A stored counter or a frozen limit date, which is the measured 1.0 defect: a term extended
by a later law must reach every execution at once, and **I16 explicitly does not bind a legal term**
(foundation 5.12.1). A branch on a stage's **name** rather than its kind (I17). And a deadline that turned
out to be an operational reminder wearing a legal term's clothes.

**Geometry and CRS.** A metric computed in degrees. UTM treated as authoritative for a legal area. A frame
chosen by habit instead of by the metric's purpose. A browser preview presented as the authoritative value
(I11, foundation section 8).

**A query that never returns.** The ownership traversal for the foreign condition runs over a graph that can
contain cycles, so it uses PostgreSQL's `CYCLE` clause. A hang here is a missing cycle clause, not a slow
database (ADR-0011 section 6).

## Tooling

```bash
# api, from inside apps/api
pytest --pdb -x                    # drop into the debugger on the first failure
pytest -k "<name>" -vv             # one behaviour, verbose

# web, from inside apps/web
pnpm exec ng test --watch=false
```

ADR-0003 makes the container the source of truth for **running**, so a bug that only reproduces on the host
is itself a finding. And the checks that live in the database (triggers, row-level security, GRANTs, PostGIS,
the JSONB index path) **cannot be reproduced against anything lighter**: run them against the containerized
PostgreSQL, which is the same image production runs.

Query-count assertions catch an N+1 before it reaches production:

```python
from django.test.utils import CaptureQueriesContext
from django.db import connection

with CaptureQueriesContext(connection) as ctx:
    list(Property.objects.select_related("owner"))
assert len(ctx) <= 2
```

For a background job, run the task **synchronously** while debugging so the traceback is yours and not the
worker's. The queue is Procrastinate on the same PostgreSQL, so there is no broker to inspect and the job
table is a normal table you can query.

## Checklist before claiming it is fixed

- Root cause identified and **stated as the violated assumption**.
- The reproduction test passes and would have failed before.
- The gate is green for the stack touched.
- Nothing was silenced: no bare `except`, no suppressed lint, **no test weakened to make it pass**.
- If the bug violated an invariant, the test **names that invariant** (`specs/testing.md` section 6.1).
- If the root cause was a wrong assumption written down somewhere, the document is fixed too.

## Red flags

Stop if you are thinking "quick fix now, investigate later", "one more attempt" after three failures, or
"this should work" without knowing why. **Three consecutive failed fixes means the problem is
architectural.** Stop and discuss.

## Integration

- `specs/testing.md` for the reproduction test and what not to test.
- `solid` for the refactor, which happens under green and never while the test is red.
- `specs/mapsift-foundation.md` section 11 for the invariant the bug violated, and its **scar**, which is
  usually a description of the same bug happening somewhere before.
