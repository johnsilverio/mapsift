---
name: systematic-debugging
description: Four-phase debugging methodology with root cause analysis for the Mapsift monorepo (Django API, Rust core, Angular client). Use when investigating bugs, fixing test failures, or troubleshooting unexpected behavior. Emphasizes NO FIXES WITHOUT ROOT CAUSE FIRST.
---

# Systematic debugging (Mapsift)

## Core principle

**NO FIXES WITHOUT ROOT CAUSE FIRST.**

Never apply a patch that masks the underlying problem. Understand why something fails before changing
anything. In this product the stakes make it concrete: a silently swallowed failure on the sync path is lost
work, and on a legal-weight feature it is a compliance event.

## Four-phase framework

### Phase 1: reproduce and investigate

Before touching any code:

1. **Write a failing test** that captures the wrong behaviour. It is the regression test afterwards.
2. **Read the error message in full.** Every word, including the frames you are tempted to skip.
3. **Look at what changed.** `git diff`, `git log`. If there is no `.git` yet, compare against the spec: the
   PRD acceptance criterion says what the behaviour was supposed to be.
4. **Trace the data flow** to where the bad value is born, not where it surfaces.

```python
@pytest.mark.django_db
def test_flush_gap_returns_typed_resend():
    """Reproduces MAP-xx: a gap above the cursor was silently skipped."""
    ...  # currently failing
```

### Phase 2: isolate

Narrow it down. Log at the decision points, not everywhere.

```python
logger.debug("flush client=%s cursor=%s first_mutation=%s", client_id, cursor, ops[0].mutation_number)
logger.debug("verdict=%s target=%s legal_weight=%s", verdict, target_path, classification)
```

Cross-runtime bugs need the boundary logged on both sides: what the client core sent, what the server
received after deserialization. A difference there is a contract bug, not a logic bug.

### Phase 3: identify the root cause

Read the full stack trace, inspect state at the failing frame, and name the violated assumption out loud. If
you cannot state the assumption, you have not found the cause yet.

### Phase 4: fix and verify

1. Fix at the root cause.
2. The reproduction test passes.
3. The full suite passes for every language touched (`/quality-gate`).
4. Where the bug was in the conflict rule, the golden vectors still resolve identically on both runtimes.

## The failure modes this system actually has

Generic Django advice does not fit here: `apps/api` is a django-ninja JSON API with **no server-rendered
templates, no Django Forms and no HTMX**. The recurring bugs are these.

**Sync and idempotency.** A resent flush duplicating or losing operations (check the per-client mutation
number and the last-applied cursor); a client advancing its cursor by assumption instead of from the server's
echo; a gap above the cursor silently skipped instead of returning a typed resend; two devices of one user
colliding because the clientID was treated as the user.

**Conflict resolution.** A verdict that differs between the Rust core and the Python server (run the golden
vectors first: it is usually the geometric predicate inside the tolerance band); a tolerance expressed in
degrees instead of metres, which behaves differently in the north and the south of the country; a
legal-weight case resolving to a discarding verdict when it should fall to flag-and-preserve.

**Tenant isolation.** A query returning zero rows when the data exists, which is usually the session tenant
not being set, and its mirror, a query returning rows it should not, which is usually a policy that is
enabled but not **forced**, a table owner bypassing it, or a role with `BYPASSRLS`. The tile path is the one
an ORM-level filter never covered.

**Geometry and CRS.** A metric computed in degrees on a geographic frame; a hard-coded projection; a
coordinate that changed on a render or edit round trip when it should have come back identical; an area that
disagrees with the registry because the frame was chosen by habit instead of by the metric's purpose (PRD M5).

**Boundary and encoding.** A live reference crossing the core boundary; bytes marshalled through the core
instead of a reference; a generated type edited by hand and now out of sync with its source.

**Background work.** A task that is not idempotent, a task passed a model instance instead of an identifier,
a worker connecting without the tenant on its session.

## Tooling

```bash
uv run pytest --pdb -x            # drop into the debugger on the first failure
uv run pytest -k "<name>" -vv     # one behaviour, verbose
cargo test -- --nocapture         # Rust core, with output
ng test --watch=false --include=**/<name>.spec.ts
```

Prefer `just` recipes where they exist: ADR-0001 section 3 makes the container the source of truth for
running, so a bug that only reproduces on the host is itself a finding.

Query-count assertions catch an N+1 before it reaches production:

```python
from django.test.utils import CaptureQueriesContext
from django.db import connection

with CaptureQueriesContext(connection) as ctx:
    list(Feature.objects.select_related("layer"))
assert len(ctx) <= 2
```

For Celery, run the task synchronously while debugging (call it directly, or set the eager flag in the test
settings) so the traceback is yours and not the worker's.

## Checklist before claiming it is fixed

- Root cause identified and stated as the violated assumption.
- The reproduction test passes and would have failed before.
- The full gate is green for every language touched.
- Nothing was silenced: no bare `except`, no `unwrap` on a recoverable path, no suppressed lint.
- If the bug reached a user, the failure is now both **presented and recorded** (PRD N9).

## Red flags

Stop if you are thinking "quick fix now, investigate later", "one more attempt" after three failures, or
"this should work" without knowing why. Three consecutive failed fixes means the problem is architectural.
Stop and discuss.

## Integration

- **pytest-django-patterns**: write the reproduction test.
- **django-models**: QuerySet and query-count issues.
- **celery-patterns**: task failures and idempotency.
- `.claude/rules/` carries the per-path rules the fix must still satisfy.
