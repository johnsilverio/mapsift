---
name: celery-patterns
description: Celery task patterns including task definition, retry strategies, periodic tasks, and best practices. Use when implementing background tasks, scheduled jobs, or async processing.
---

# Celery Patterns for Django

## Core Philosophy

- **Idempotent tasks**: Running a task twice must produce the same result
- **Pass IDs, not objects**: Arguments must be JSON-serializable
- **Always handle failures**: Log errors, never swallow exceptions silently
- **Proper retry strategies**: Use exponential backoff for external services

## Task Design

### Structure
- Celery runs in the **one backend**, `apps/api`. Tasks live in `apps/api/<django_app>/tasks.py`, never in a
  new top-level `apps/` folder: `apps/` holds deployables, and the background worker is a process of the same
  Django deployable, not a second one.
- Use `@shared_task` for reusable tasks across projects
- Use `bind=True` when needing access to task instance (retries, task ID, state updates)
- Add type hints to task signatures
- Log task start, completion, and failures

### Arguments
- Pass model primary keys, not model instances
- Keep arguments simple and serializable (str, int, dict, list)
- Validate that referenced objects exist at task start

## Retry Strategies

### When to Use Each Approach
- **Fixed delay**: Internal operations with predictable recovery (database locks)
- **Exponential backoff**: External APIs that may rate-limit or have variable recovery
- **No retry**: Validation errors, business logic failures, permanent errors

### Configuration
- Set `max_retries` based on acceptable total wait time
- Use `retry_jitter=True` to prevent thundering herd
- Set `retry_backoff_max` to cap maximum wait time
- Use `autoretry_for` tuple for automatic retry on specific exceptions

## Idempotency Patterns

### Check-Before-Process
Query current state before processing; skip if already complete

### Status Field Tracking
Use status transitions (pending → processing → complete/failed) with `select_for_update()` for race condition safety

### Unique Constraints
Use database constraints to prevent duplicate processing

## Periodic Tasks (Beat)

- Configure schedules in the Django project's Celery module using `beat_schedule`. The concrete settings
  layout is not fixed by any ADR yet, so follow the scaffold rather than assuming a path.
- Use `crontab()` for time-based schedules
- Use float values for interval-based schedules (seconds)
- Keep periodic tasks lightweight; spawn subtasks for heavy work

## What Celery carries in Mapsift

The heavy, server-side, online work (foundation section 5 and section 10): raster and imagery processing,
NDVI and change detection, analysis over large layers, import processing and tiling, and anything routed
through the imagery provider. None of it is on the offline element path, and none of it decides a conflict:
resolution authority is the server's synchronous flush path, not a background worker.

Two constraints follow from the canon and bind every task here:

- A task that touches tenant-owned data runs under a session with the tenant set. A worker connecting
  privileged defeats the isolation wall exactly as the tile role would (PRD N2).
- Copernicus and openEO work carries a real per-use cost in processing units (foundation OQ-3), so a task
  that pulls imagery is metered and never offered as unlimited.

## Anti-Patterns to Avoid

- Passing model instances instead of IDs
- Non-idempotent operations (incrementing without checks)
- Silent exception handling (bare `except: pass`)
- Missing logging for task lifecycle, or logging that carries geometry payloads or personal data (PRD N9, N5)
- Long-running tasks without progress updates
- Retry on permanent failures (validation, business logic errors)
- Deciding a conflict, or writing legal-weight geometry, from a background worker outside the flush path

## Commands

- Worker: `uv run celery -A config worker -l info`
- Beat: `uv run celery -A config beat -l info`
- Monitoring: `uv run celery -A config flower`
