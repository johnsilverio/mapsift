---
name: django-models
description: Django model and QuerySet design for the Mapsift backend, emphasizing pure decisions outside the ORM, chainable QuerySets, query optimization, and PostGIS geometry. Use when designing models, optimizing queries, writing migrations, or working with the ORM in apps/api.
---

# Django model patterns (Mapsift)

## Core philosophy: the ORM is a persistence detail

This project rejects both of the usual extremes, and the reasoning matters because each looks reasonable on
its own.

- **No repository pattern over the ORM.** `CLAUDE.md` is explicit: do not wrap it without a concrete,
  measured reason. Django's QuerySet already is the query abstraction, and a second one buys ceremony.
- **No fat models either.** Domain rules welded to a `models.Model` subclass can only be exercised with a
  live database, and `CLAUDE.md` states the consequence directly: if a piece of logic can only be tested with
  the network, a large raster, or a live PostGIS, it was factored wrong. The test-first method (foundation
  section 14) puts the bulk of the tests on pure decisions, so those decisions must be reachable without a
  database.

What replaces both: **decisions are pure functions over plain data, effects sit behind narrow interfaces, and
use cases and services live outside the views.**

- **Pure decision**: conflict resolution, tenant and permission resolution, geometry math, spectral indices,
  config merge, geometric validation, the choice of metric frame (PRD M5). Plain input, plain output, no ORM
  import, tested with no database.
- **Service or use case**: loads what the decision needs, calls it, persists the result, emits the effect. It
  is thin and mostly orchestration.
- **Model**: fields, constraints, indexes, `__str__`, `Meta`, and persistence-shaped helpers. Not the home of
  a state machine, a permission rule, or a legal-weight verdict.

```
BAD   feature.resolve_conflict(other)         # a legal-weight decision that needs a DB to test
GOOD  verdict = resolve_conflict(incoming, current, classification)   # pure, golden-testable
      FeatureService.apply(verdict)                                   # the effect
```

## Model design

- Use `TextChoices` / `IntegerChoices` for status fields and enums.
- Include `__str__()` for readable representations; set `ordering` in `Meta` where a default order is real.
- Add database indexes for the fields actually filtered and sorted, and remember the tenant identifier is on
  every tenant-owned row and is in nearly every query's `WHERE`.
- Use abstract base models for shared fields (timestamps, tenant identifier, soft delete where it applies).
- Optional text: `blank=True, default=""`, avoid `null` on text. Optional foreign key: `null=True,
  blank=True`. Unique optional field: `null=True` to dodge collisions.
- `JSONField` for genuinely flexible metadata, not as an escape from modelling.
- Geometry columns are PostGIS types and are stored in SIRGAS 2000 (EPSG:4674) with the source CRS recorded
  (PRD M5). No metric is ever computed in degrees, and no projection is hard-coded: the frame is chosen by the
  metric's purpose.
- Every tenant-owned table carries the tenant identifier and a row-level security policy, **enabled and
  forced**. PRD N2 makes that a test that enumerates the tables, so a new model without the policy fails CI.

## QuerySets: composition is the whole point

Custom QuerySet classes make queries reusable, chainable and testable.

- Define a QuerySet subclass with domain-specific filters and attach it with
  `objects = FeatureQuerySet.as_manager()`.
- Chain for expressive reads: `Feature.objects.in_project(p).legal_weight().recent()`.
- Use a Manager only for model-level operations that do not return a QuerySet (factory methods). Most of the
  time you want a QuerySet.

## Query optimization

1. `select_related()` for ForeignKey and OneToOne (a JOIN).
2. `prefetch_related()` for many-to-many and reverse relations, with `Prefetch()` when it needs its own
   filter or `select_related`.
3. `only()` / `defer()` to keep a geometry or a JSON blob out of a list query.
4. `.exists()` instead of truthiness; `.count()` instead of `len()`.
5. `annotate()` and `aggregate()` for computed values, `F()` for database-level updates.

An N+1 inside a loop over features is a review blocker, not a nitpick: layers hold a lot of features.

```python
# BAD, one query per feature
for feature in Feature.objects.all():
    print(feature.layer.name)

# GOOD, one query
for feature in Feature.objects.select_related("layer"):
    print(feature.layer.name)
```

Let PostGIS own authoritative geometry. `ST_Area`, `ST_Buffer` and `ST_Intersects` are GEOS in C inside the
database that is already the source of truth; do not reimplement them in Python.

## Signals: use sparingly

Signals create implicit coupling. Prefer an explicit call.

- Reasonable: audit logging, cache invalidation, reacting to a third-party app's models.
- Not reasonable: business logic that belongs in a service, or anything where you control both the trigger
  and the reaction.

The append-only operation log (PRD M15) is written explicitly by the flush path, never by a signal, because
its ordering and its authorship stamp are the point.

## Migrations

- Generate with `python manage.py makemigrations`, never hand-write one. `--empty` for a data migration.
- Review the generated file before applying it; this database holds legal-weight geometry.
- In a data migration use `apps.get_model()`, not a direct import, and write the reverse operation.
- A migration that adds a tenant-owned table also adds its row-level security policy, or PRD N2's test fails.

## Anti-patterns

- Business rules, state transitions or permission decisions implemented as model methods.
- A repository or unit-of-work layer wrapping the ORM without a measured reason.
- Iterating over related objects without `select_related` / `prefetch_related`.
- `if queryset:` instead of `.exists()`, `len()` instead of `.count()`.
- A model without its index on the fields it is actually filtered by.
- Django Forms. There are none in this stack: validation lives at the API boundary in django-ninja plus
  Pydantic schemas.

## Integration

- **pytest-django-patterns**: factories and the test-first cycle.
- **celery-patterns**: background work over models (pass identifiers, never instances).
- `.claude/rules/python-django.md` carries the enforceable per-path version of these rules.
