---
paths:
  - "apps/api/**/*.py"
---

# Python and Django checklist (Mapsift backend)

Actionable per-path rules for `apps/api`, the one Django backend. Grounded in `CLAUDE.md`, the foundation
(sections 9, 10, 14) and ADR-0001.

**What this backend is.** Django 5 with Channels, django-ninja and Pydantic, Celery for background jobs, on
PostgreSQL 18 with PostGIS. It is a JSON API. There are **no server-rendered templates, no Django Forms and
no HTMX**, and it is not Django REST Framework. Input validation lives at the API boundary in Pydantic
schemas. No Rust runs here (foundation 9.6.6): the authoritative conflict rule is the Python implementation,
kept identical to the client core by golden tests.

**Version note.** `apps/api/uv.lock` exists and is what pins a version; `specs/dependencies.md` is the survey
that says why a choice was made and which particularity of it bites. Check the survey first and the lockfile
for the number. Do not assert a library version from memory, and do not introduce a dependency the foundation
has not ratified without walking that gate.

## Generate with the CLI, then edit (non-negotiable)

Every framework-owned file is created by Django's own generator and then edited.

```bash
python manage.py startapp <name>          # a new app
python manage.py makemigrations <app>     # never hand-write a migration file
python manage.py makemigrations --empty <app>   # data migration skeleton
```

Same reason as everywhere else in this repo: the generator writes what the installed version produces, a
model writes what it remembers. A hand-written migration that diverges from the autodetector is a silent
schema drift, and this database holds legal-weight geometry.

## Where a file goes (ADR-0007, and this section decides nothing it does not say)

- The application package is **`mapsift/`**, one subpackage per **domain** and never per layer. There is no
  top-level `models/`, `schemas/` or `services/`. A package past roughly ten models is hiding two domains.
- **`config/` is the Django project and never holds domain code.** It holds the settings, the validated
  environment, `urls.py`, the server entrypoints, and the `NinjaAPI` instance with its `add_router` calls.
- **`mapsift/common/` is tier 0** and holds what every package needs and no package owns: the tenant binding
  and its guard, the tenant-owned manager, the shared model primitives. It depends on nothing above it. A
  helper that grows a domain opinion has left `common/`.
- Inside a package: `models.py`, `rules.py`, `selectors.py`, `services.py`, `capabilities.py`, `api.py`,
  `migrations/`, `tests/`.
  - `rules.py` is **pure**: no ORM, no I/O, no framework import beyond types. The test density lives here.
  - `selectors.py` reads, `services.py` writes and is the only writer.
  - `capabilities.py` holds the named capabilities this package publishes (foundation 9.5, PRD T7), which are
    serializable, carry a machine-readable description, and return composable output. A capability is not a
    service: a service is internal, a capability is the published surface the SDK and the agent consume.
  - `api.py` holds one thin django-ninja `Router`. A route carrying a business decision has taken work that
    belongs in `rules.py`.
- **Reach another package through its `selectors` or `services`, never through its `models`**, enforced by an
  `import-linter` `protected` contract rather than by review. A cross-package relation needs **no import at
  all**, because the foreign key is declared with the string form: `models.ForeignKey("accounts.Tenant", ...)`.
- **Importing upward across tiers fails the build** (`import-linter` `layers` contract, root package
  `mapsift`). If a contract has to be relaxed to make a feature land, the feature is in the wrong package.
- Per-package tests live under the package. **`apps/api/tests/` holds only what crosses packages** (the wall's
  own catalogue suite) plus the shared fixtures.

## Decisions are pure, effects sit behind interfaces

This is the architecture rule that makes the test-first method possible (foundation section 14), and it
decides where domain logic goes.

- DO put a decision in a pure function over plain data: conflict resolution, tenant and permission
  resolution, geometry math, spectral indices, config merge, geometric validation, the metric frame choice
  (M5). These carry the bulk of the tests and need no database.
- DO keep use cases and services outside the views, calling those pure functions and then persisting.
- DON'T put domain rules on a `models.Model` subclass. A rule that lives on an ORM class can only be tested
  with a live PostGIS, and `CLAUDE.md` is explicit: if a piece of logic can only be tested with the network,
  a large raster, or a live PostGIS, it was factored wrong. Model methods stay for persistence-shaped
  behaviour.
- DON'T wrap the ORM in a repository pattern. It is a persistence detail, and the canon rejects the wrapper
  without a concrete measured reason. Only genuine external integrations (PostGIS beyond the ORM, S3/MinIO,
  Copernicus/openEO, the tile servers, the sync transport) sit behind narrow interfaces with a real adapter
  and a test fake.

Both halves of that are one rule: no ceremony around the ORM, and no domain logic welded to it either.

## Types and boundaries

- DO type every signature completely. mypy `--strict` with django-stubs must pass; CI blocks on it (C5).
- DON'T use `Any` without a comment justifying it.
- DO validate at every boundary with Pydantic: API input, WebSocket messages, config.
- DO keep django-ninja routers thin. A router parses, calls a use case, and returns a schema.
- DO generate the frontend contract from the OpenAPI schema; never hand-write the other side (M12).

## Tenant isolation (C4, I4, PRD T6.1 and N2; the mechanism is **ADR-0005**)

- The **tenant** is the top container of an account (a personal user account or an organization) and it is
  the only isolation boundary. It rides as a tenant identifier on every tenant-owned row.
- The **workspace** and the **project** below it are organization and permission, never a second SQL wall.
  Confidentiality between a tenant's own clients or projects is the permission model's job.
- DO enforce isolation in the database (row-level security, enabled **and forced**), not only in the ORM, so
  direct-to-PostGIS readers such as the tile server are covered.
- DON'T let the tile role connect privileged or skip setting the tenant on its session, and watch the defeat
  conditions: a role that owns the table without `FORCE ROW LEVEL SECURITY`, or any role holding
  `BYPASSRLS`, silently removes the wall.
- DON'T write raw SQL that reaches a tenant-owned table outside the policy.
- DO bind the tenant **transaction-scoped and parameterised**, as the first statement of the transaction
  serving the request or the task: `SELECT set_config('mapsift.tenant_id', %s, true)`. Bind it once, where
  the N9 correlation keys are bound, never per caller.
- DON'T use a session-scoped binding (`SET`, or `set_config` with `is_local` false). It survives into the
  next request on a pooled or persistent connection, which may belong to another tenant (ADR-0005, measured).
- DON'T interpolate the tenant into that statement. The parameter is settable by the same unprivileged role,
  so an injection on the binding path re-binds the tenant and the wall does not stop it (ADR-0005, measured).
- DO read the parameter in a policy through the guarded cast,
  `nullif(current_setting('mapsift.tenant_id', true), '')::uuid`. The bare cast throws
  `invalid input syntax for type uuid: ""` on every transaction after the first on a reused connection,
  because the setting reverts to the empty string rather than to unset (ADR-0005, measured).
- DO make every foreign key between tenant-owned tables composite over `(tenant_id, key)`, with the matching
  `UNIQUE (tenant_id, id)`, and every **natural** unique key unique per tenant rather than globally.
  Referential integrity checks always bypass row security, so this is the only thing that closes that channel.
- DO lead every index serving a tenant-scoped query with `tenant_id`, because the policy adds that predicate
  to every query on the table (structural performance, foundation section 10).
- DO let the application raise when a tenant-scoped query runs with no binding in force. The policy denies
  silently by construction, and a silent empty result is indistinguishable from an empty tenant (N9, N12).
- The wall's one deliberate exception is the login question (ADR-0005 section 8): `membership` carries a
  second permissive policy, **`FOR SELECT` only**, keyed on `mapsift.user_id`, which obeys the same binding
  rules as the tenant parameter. DON'T widen it to `FOR ALL`, and DON'T answer the login question with
  `BYPASSRLS` or through the owning role.

## Queries

- DO use `select_related()` for ForeignKey and OneToOne, `prefetch_related()` for many-to-many and reverse
  relations. An N+1 in a loop over features is a review blocker, not a nitpick.
- DO use `.only()` / `.defer()` on heavy rows, `.exists()` instead of truthiness, `.count()` instead of
  `len()`, and `F()` expressions for database-level updates.
- DO define chainable custom QuerySets for reusable query logic (`Feature.objects.in_layer(x).legal_weight()`)
  and attach them with `as_manager()`. **This does not contradict the styleguide rule that bans business logic
  in managers and querysets (ADR-0007 section 3): query composition is not a business rule.** A queryset method
  that narrows rows is a selector's building block; one that decides whether an edit is allowed is a rule in
  the wrong file.
- DO let PostGIS own authoritative geometry (GEOS). Don't reimplement in Python what `ST_Area`, `ST_Buffer`
  or `ST_Intersects` already computes, and never compute a metric in degrees (M5).

## Operations, sync and the moral line

- Every operation is append-only (M15), addresses exactly one target path (M9), carries its per-client
  mutation number (C12) and its proven author (C13).
- A conflict on legal-weight geometry is detected and both versions retained. No code path silently
  overwrites, drops, or resurrects a legal-weight feature (C7).
- Ordering is the database's, through the transactional flush. Channels carries transport and presence only;
  authoritative state never lives there (C9).

## Logging (the mechanism is **ADR-0011**; this section restates it and decides nothing)

- DON'T pass a correlation key as a function argument. The four keys of N9 (operation identifier, clientID,
  tenant, request or task) are bound **once per context** and reach the record from there. A signature that
  takes one is the design the requirement replaced.
- DON'T add a field to what a record emits without adding it to the **allowlist** deliberately. The gate is a
  closed set on the root handler and it **drops** what is not named rather than trimming it, which is what
  makes it hold for Django's own records too, `django.db.backends` and its SQL parameters included.
- DON'T put an identifier inside a message string and call it traceable. A key is a field; an interpolated
  identifier is not a join.
- DO emit one record per **decision**, carrying the operations it covers as a structured list, and one per
  operation only where the decision is genuinely per operation.

## Celery

- DO make every task idempotent, pass primary keys and never model instances, and validate that the
  referenced object still exists at task start.
- DO use exponential backoff with jitter for external services, and no retry at all for validation or
  business-rule failures.
- DO log task start, success and failure with the operation identifiers a user report can be traced by (N9),
  and never log geometry payloads or personal data (N5).
- DON'T swallow an exception. Log with context and re-raise.

## Tests

- Tests live under `apps/api` in pytest idiom (ADR-0001 section 7), never in a repository-root `tests/`
  folder, which holds the throwaway prototype.
- The conflict rule's golden vectors are shared fixtures consumed by both the Python suite and the Rust
  suite; a divergence fails the build (C10, M13).
- Test behaviour, not implementation. Don't test Django itself.
