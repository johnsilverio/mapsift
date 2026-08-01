---
name: pytest-django-patterns
description: pytest-django testing patterns for the Mapsift backend, Factory Boy, fixtures, the two-window test-first cycle, and the cross-runtime golden vectors. Use when writing tests for apps/api, creating factories, or driving a change test-first.
---

# pytest-django testing patterns (Mapsift)

## The test-first cycle, in two windows

Mapsift is built test-first, and `CLAUDE.md` and foundation section 14 specify **how**: Red, Green, Refactor
in **two clean-context windows**. One pass writes the failing tests as behaviour; another implements the
minimum to green, using those tests as a contract written by another pass, so the implementation cannot be
shaped to fit a test it authored itself. Design happens in the refactor step, never while a test is red.

Never write production code without a failing test, and never weaken a test to reach green.

`specs/testing.md` is the canonical method document and does not exist yet. Until it does, this skill plus the
Testing and TDD section of `CLAUDE.md` are the method; do not invent the missing spec's content.

## Where tests live

Each ecosystem holds its own tests in its own idiom (ADR-0001 section 7): **pytest under `apps/api`**, the
Angular workspace runner under `apps/web` and `libs/ui`, Cargo tests under `libs/core`. The repository-root
`tests/` folder holds the throwaway prototype and is not the suite.

The conflict rule's **golden vectors** live in a shared fixture location consumed by both the Python suite and
the Rust suite (PRD M13). Canonical inputs run against both runtimes and a divergence fails the build; the
tolerance where the rule consults a geometric predicate is declared in metres, and inside that band a
legal-weight verdict falls to flag-and-preserve.

## What carries the bulk of the tests

Pure decisions, with no database at all: conflict resolution, tenant and permission resolution, geometry math,
spectral indices, config merge, geometric validation, the metric-frame choice. If a decision needs
`@pytest.mark.django_db` to be exercised, that is a factoring problem, not a testing problem.

Effects sit behind narrow interfaces with a real adapter and a test fake.

## Database access

- `@pytest.mark.django_db` on any test that genuinely touches the database, or
  `pytestmark = pytest.mark.django_db` for a module of them.
- Transactions roll back after each test.
- PostGIS-backed assertions belong to the integration layer, not to the pure-decision suite.

## Fixtures and factories

- **Factory Boy** for model instances: `factory.Sequence()` for unique fields, `factory.Faker()` for
  realistic data, `factory.SubFactory()` for foreign keys, `@factory.post_generation` for many-to-many.
- A factory for a tenant-owned model always sets the tenant, so a test cannot accidentally prove isolation by
  never having two tenants.
- **pytest fixtures** for setup: clients, authenticated sessions, shared resources. Define them in
  `conftest.py` for reuse.

## What to test

**API endpoints (django-ninja)**: status codes, authenticated versus anonymous behaviour, authorization
(including that a request cannot reach another tenant's rows by any path), the response body against its
Pydantic schema, and the side effects (rows written, tasks queued).

**Tenant isolation (PRD N2)**: a test enumerates every tenant-owned table and asserts row-level security is
enabled **and forced**, so a table added later without the policy fails CI. The defeat conditions are their
own cases: a role owning the table without `FORCE`, a role holding `BYPASSRLS`, and the tile role connecting
privileged or failing to set the tenant on its session. A cross-tenant read through the tile path is a test,
because that path is the one an ORM filter never covered.

**The sync path**: an interrupted flush resent converges with no duplicate and no loss; a gap above the
cursor returns a typed resend rather than a silent skip; a legal-weight geometry collision is flagged with
both versions retained; an operation whose author diverges from its session material is normalized or
rejected, never accepted as claimed.

**Models**: custom QuerySet filtering, constraints enforced at the database level, `__str__`.

**Celery tasks**: the logic with external calls mocked, and idempotency (running twice is safe). Do not test
that Celery itself dispatches.

There are **no Django Forms** in this stack, so there is nothing to test there. Input validation is Pydantic
at the API boundary and is covered through the endpoint.

## Patterns

- `@pytest.mark.parametrize` for several scenarios of one behaviour.
- `mocker.patch()` for external services (HTTP, object storage, the imagery provider), never for your own
  code.
- `refresh_from_db()` before asserting an update, `Model.objects.filter(...).exists()` after a creation.
- One behaviour per test, one test per behaviour. Test names describe the behaviour, not the method.

## Running

```bash
uv run pytest                      # all
uv run pytest -x                   # stop on first failure
uv run pytest --lf                 # last failed
uv run pytest -k "conflict"        # by name
uv run pytest apps/api/<app>       # a subtree
uv run pytest --cov=apps/api       # coverage
```

Prefer `just test` where the recipe exists: ADR-0001 section 3 makes the container the source of truth for
running.

## Common pitfalls

- Forgetting `@pytest.mark.django_db` on a test that does touch the database.
- Adding `@pytest.mark.django_db` to a test that should not need it, which hides a factoring problem.
- Testing implementation instead of behaviour (asserting a call happened rather than an outcome).
- Writing the test and its implementation in the same pass, which defeats the two-window protocol.
- Over-mocking: mock external dependencies, not your own decisions.
- Testing Django, Pydantic or PostGIS themselves.

## Integration

- **systematic-debugging**: a bug fix starts with the failing test that reproduces it.
- **django-models**: QuerySets, constraints and the pure-decision split.
- **celery-patterns**: task logic with mocked externals.
