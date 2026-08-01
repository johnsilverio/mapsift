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

**Version note.** Nothing is pinned yet (no lockfile exists until the scaffold), and `specs/dependencies.md` now exists as the survey to check first. Do not assert a library
version from memory, and do not introduce a dependency the foundation has not ratified without walking that
gate.

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

## Tenant isolation (C4, I4, PRD T6.1 and N2)

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

## Queries

- DO use `select_related()` for ForeignKey and OneToOne, `prefetch_related()` for many-to-many and reverse
  relations. An N+1 in a loop over features is a review blocker, not a nitpick.
- DO use `.only()` / `.defer()` on heavy rows, `.exists()` instead of truthiness, `.count()` instead of
  `len()`, and `F()` expressions for database-level updates.
- DO define chainable custom QuerySets for reusable query logic (`Feature.objects.in_layer(x).legal_weight()`)
  and attach them with `as_manager()`.
- DO let PostGIS own authoritative geometry (GEOS). Don't reimplement in Python what `ST_Area`, `ST_Buffer`
  or `ST_Intersects` already computes, and never compute a metric in degrees (M5).

## Operations, sync and the moral line

- Every operation is append-only (M15), addresses exactly one target path (M9), carries its per-client
  mutation number (C12) and its proven author (C13).
- A conflict on legal-weight geometry is detected and both versions retained. No code path silently
  overwrites, drops, or resurrects a legal-weight feature (C7).
- Ordering is the database's, through the transactional flush. Channels carries transport and presence only;
  authoritative state never lives there (C9).

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
