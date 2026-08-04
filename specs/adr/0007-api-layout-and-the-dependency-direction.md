# ADR-0007: The `apps/api` layout, the dependency direction, and where a capability lives

- **Status:** accepted (2026-08-04)
- **Deciders:** the owner, on the survey recorded below
- **Authority:** derives from `specs/mapsift-foundation.md` v0.17 (sections 9.5 and 9.5.1 the capability layer, section 10 the stack and the performance rule, section 14 the method) and `specs/PRD.md` v0.14 (T7.1 to T7.3, M1, M2, M12, N2, N9), and from **ADR-0002 section 5**, whose named trigger fired. Where this ADR and the foundation disagree, the foundation wins and this ADR is the one that is wrong.
- **Supersedes:** nothing. **Superseded by:** nothing.
- **Delivers:** MAP-28, and it unblocks MAP-5.

---

## Context

`apps/api` holds **one** Django app, `accounts`, and **one** migration. Everything about this stack is
settled except the thing a developer needs before typing: **where does a file go, and what may it import.**

ADR-0002 fixed generation and Angular's file layout, deliberately left Python's out, and named the trigger
for its own ADR: when `.claude/rules/python-django.md` "stops being a restatement of the canon and starts
being a decision". A folder layout is a decision, so the trigger has fired.

**What forces it now rather than later is already on disk.** `accounts/binding.py` holds `tenant_scope` and
`TenantOwnedManager`, which are the mechanics of the ADR-0005 wall and are needed by **every** tenant-owned
table. MAP-5 creates the second app. Under today's layout that app writes
`from accounts.binding import TenantOwnedManager`, and from that moment a platform primitive is something
imported out of a domain package, which is how a dependency graph rots. This is also the cheapest moment the
move will ever be: one app, one migration, five test modules, no deployment.

And there is a reason this decision carries more weight here than in an ordinary Django project: **most of
this code is written by agents reading these documents cold.** An agent that has to infer a convention
invents one, and invents a different one next session. The layout is a specification rather than something to
be discovered from the existing tree.

---

## What the survey found

Researched 2026-08-04 against current sources rather than from memory, under the external-dependency rule.

| Source | What it establishes | Read on |
|---|---|---|
| **cookiecutter-django** 2026.31.2 | The community default is the two-tier "Two Scoops" layout: repository root holds `manage.py`, `config/` holds the settings (split per tier), the URL conf and the server entrypoints, and the apps live in a package of their own. A new app is created with `startapp` and **moved** into it. | 2026-08-04 |
| **HackSoft Django Styleguide** | The `services.py` (writes) and `selectors.py` (reads) split, and, more usefully, the explicit list of where business logic may **not** live: views, serializers, forms, `save()`, custom managers or querysets, and signals. A `services.py` that grows becomes a package by subdomain. Tests mirror the module structure. | 2026-08-04 |
| **django-ninja**, official guide | The framework's own recommendation is **an `api.py` per app holding a `Router`**, plus one `api.py` beside the project's `urls.py` holding the `NinjaAPI` instance and its `add_router` calls. There are no serializers; the schemas are Pydantic. | 2026-08-04 |
| **import-linter 2.13** (released 2026-07-03, BSD-2, Python 3.10 to 3.14) | Five contract types: `layers`, `forbidden`, `independence`, `protected`, `acyclic_siblings`. In a layers contract `|` makes siblings independent and `:` lets them import each other. **`protected` restricts who may import a module directly, from an allow-list**, which is the piece that matters below. | 2026-08-04 |
| The domain-versus-layer question | The consensus for anything past a toy is one app per cohesive domain, not top-level `models/`, `views/`, `services/`. The concrete argument, rather than "separation of concerns": in a layer-organised project adding one field edits five directories and produces five diffs a reviewer has to hold at once. | 2026-08-04 |

**The reference that was read in full is the Ecobalance ADR-0002**, a sibling project's answer to this same
question. Its reasoning transfers almost entirely and three of its parts do not, each for a stated reason.
Its `engines/` package exists because that backend is one writer among three in a shared cluster, and Mapsift
owns its database outright. Its `Module`-versus-package distinction exists because that product activates
modules per installation, which this one does not have. And its `api/` subpackage carries the four files a
DRF project needs, while this stack is django-ninja and the framework recommends a single `api.py`.

**What neither that ADR nor any surveyed source has to answer is the one thing this product cannot omit.**
Foundation 9.5 and 9.5.1 make every data operation a **named capability**: asynchronous, serializable,
carrying a machine-readable structured description, returning composable output, respecting the invariants by
construction, with the app as the first consumer of its own public layer (PRD T7.1 to T7.3). That is not a
`services.py`. A service is an internal function; a capability is a published, described, permissioned,
chainable unit that the app, the extensions, the SDK and the AI agent all consume through one surface. **A
layout with no home for the capability registry is wrong for this product**, whatever else it gets right.

---

## Decision

### 1. One application package, `mapsift/`, with one subpackage per domain

```
apps/api/
├── pyproject.toml          the stack's dependencies and its gate configuration
├── uv.lock
├── manage.py
├── config/                 the Django project. NEVER domain code
│   ├── settings.py
│   ├── env.py              the validated environment
│   ├── api.py              the NinjaAPI instance and its add_router calls
│   ├── urls.py  asgi.py  wsgi.py
├── mapsift/                the application package
│   ├── common/             tier 0: the wall's mechanics and the shared primitives
│   └── accounts/           tier 1: user, tenant, membership, workspace, project
└── tests/                  cross-package tests, shared fixtures and factories
```

Every import then reads `from mapsift.accounts.services import ...`. Three reasons, in weight order. It gives
`import-linter` the single `root_package` its contracts want, which section 4 depends on. It stops a bare
`accounts` from colliding with any third-party distribution of the same name on the path. And the path names
the system in a working tree that holds four ecosystems.

**A package is named after a domain, never after a layer.** There is no top-level `models/`, `schemas/` or
`services/`. The heuristic that comes with it: **a package past roughly ten models is hiding two domains**
and splits, which is a normal refactor rather than a new ADR.

### 2. `config/` holds the Django project and never holds domain code

The settings stay **one file** until a second real environment exists. The rule that matters is not the
number of files, it is that environments differ **in size, secrets and data, never in shape**, because an
environment that swaps out the component holding the invariants tests a system nobody ships. The trigger for
splitting into a per-tier package is the same one that already holds back `infra/compose.prod.yaml`: a
deployment target existing. Splitting earlier produces three files that differ in nothing.

### 3. What each file in a package holds

```
accounts/
├── __init__.py  apps.py
├── models.py            or models/ when it stops fitting on one screen
├── rules.py             pure decisions: no ORM, no I/O, no framework import
├── selectors.py         reads: queryset composition, the public read surface
├── services.py          writes: use cases, transactions, effects
├── capabilities.py      the named capabilities this package publishes (section 5)
├── api.py               the django-ninja Router, per the framework's own guide
├── migrations/
└── tests/
```

| File | Holds | The rule that keeps it honest |
|---|---|---|
| `rules.py` | **pure decisions over plain data**: tenant and permission resolution, the conflict rule, the metric frame choice, geometric validation, the version and upcasting rules | It imports nothing from Django beyond types. **This is where the test density lives** (`testing.md` section 3), and a decision that can only be tested with a live PostGIS was written in the wrong file |
| `selectors.py` | reads, and the read surface another package calls | A property that spans relations, or that would produce an N+1 when serialised, is a selector rather than a model property |
| `services.py` | writes: use cases, transactions, effects | The only writer, therefore the only place an operation reaches the log (M15) |
| `capabilities.py` | the capabilities this package publishes, with their descriptions | Collected by walking packages rather than from a central list somebody forgets to update |
| `api.py` | one `Router`, thin | A route holding a business decision has taken work that belongs in `rules.py` and made it untestable without HTTP |

**One clarification the survey forced, because two authorities read as contradicting each other.** The
styleguide forbids business logic in custom managers and querysets;
`.claude/rules/python-django.md` requires chainable custom QuerySets for reusable query logic. They agree:
**query composition is not a business rule.** A queryset method that narrows rows is a selector's building
block; a queryset method that decides whether an edit is allowed is a rule in the wrong file.

**The ORM stays a persistence detail and is not wrapped in a repository pattern.** Only genuine external
integrations sit behind narrow interfaces with a real adapter and a test fake (object storage, the tile
servers, the imagery APIs, the sync transport), which is the canon's rule and not this ADR's.

### 4. The dependency direction is a checked contract, not a review item

Every other load-bearing rule in this repository is enforced by topology or by CI, and this one has no reason
to be the exception, least of all in a codebase written largely by agents. **`import-linter` runs as a gate**,
with `mapsift` as the root package, under a **layers** contract that fails the build when a lower tier
imports a higher one.

```toml
[tool.importlinter]
root_package = "mapsift"

[[tool.importlinter.contracts]]
name = "Mapsift package tiers"
type = "layers"
containers = ["mapsift"]
layers = ["accounts", "common"]
exhaustive = true

[[tool.importlinter.contracts]]
name = "A package is reached through its selectors and services, never its models"
type = "protected"
protected_modules = ["mapsift.accounts.models"]
allowed_importers = ["mapsift.accounts"]
```

Two things about this being thin today, stated rather than glossed. **Two layers assert almost nothing**, and
that is fine: ADR-0001 section 6 already established that a gate exists before the code it governs, and the
first violation this prevents is the concrete one in the Context. **The `protected` contract is the part that
is not thin**: it enforces mechanically what the reference ADR could only leave as a convention a reviewer
must remember, and it is why the tool is adopted at its current version rather than an older one.

> **Correction (2026-08-04), and it is the difference between a gate and a gate that means something.** The
> first version of this contract listed fully-qualified module names and was **not exhaustive**, which left a
> package added later silently **outside** the tier order, the exact opposite of the by-construction property
> N2 has and this section claims. `exhaustive = true` closes it, and the form above is the one the tool
> actually accepts: `exhaustive` **requires `containers`**, so the layers are named relative to the container
> rather than fully qualified, and the fully-qualified form is rejected as a misconfiguration rather than
> quietly ignored. Both halves were **probed rather than read**: with the corrected form the contracts are
> kept, and creating an unlisted package under `mapsift/` turns the tiers contract **BROKEN** on the next run,
> which is the property being bought.

**Reaching another package costs no import at all**, because a relation is declared with the string form,
`models.ForeignKey("accounts.Tenant", ...)`. So breaking the rule requires typing an import somebody sees in
review and the contract fails.

### 5. Where a capability lives, and why it is not `services.py`

A capability (foundation 9.5, PRD T7) is declared in the `capabilities.py` of the package that owns its
domain, so it sits beside the rules and services it composes and is greppable per domain. **The registry
collects by walking the packages**, never from a central list, for the same reason the N2 isolation test
enumerates tenant-owned tables from the catalogue: a list somebody maintains is a list that goes stale
silently, and a capability missing from the registry is invisible to the SDK and to the agent rather than
loudly broken.

Three properties bind wherever a capability is declared, and they are the foundation's rather than this
ADR's: it exchanges **serializable data and never a live reference**, it carries its **machine-readable
description**, and it returns **composable output**. A `services.py` function that is not a capability is an
internal detail; the moment it becomes part of the public surface it moves, and the move is a rename rather
than a rewrite precisely because both live in the same package.

### 6. Tests live with their subject

Per-package tests under the package, in the `tests/` folder beside the code they test. **Cross-package tests
stay in `apps/api/tests/`**, which is where the wall's own suite belongs, because the N2 catalogue test
enumerates every tenant-owned table across every package by construction and is not any single package's.

> **Correction (2026-08-04), found while executing this ADR and recorded rather than silently worked around.**
> The sentence above originally also put the **shared fixtures** in `apps/api/tests/`, which cannot work:
> pytest resolves a `conftest.py` by directory, so a fixture declared there is invisible to a test under
> `mapsift/accounts/tests/`. It is not a hypothetical, it is the actual shape of this suite, where `alice` and
> `bob` are used both by the account-tree tests, which belong to a package, and by the wall's own suite, which
> does not. **Shared fixtures therefore live in the stack's root `conftest.py`** (`apps/api/conftest.py`),
> which is pytest's own convention for project-wide fixtures, and `apps/api/tests/` holds cross-package
> **tests**. This is a correction to an instruction that could not be executed rather than a change of
> decision, so it is recorded here in the ADR-0005 section 7 form rather than in a superseding ADR.

This is `testing.md` section 5 applied rather than changed: tests stay inside `apps/api`, in pytest idiom,
and there is still no repository-root `tests/` folder for application tests.

### 7. What is deliberately not created yet

No package is created before the code that lives in it. Named here so nobody scaffolds them: `sync/` (the
envelope, the catalog, the flush and the version axes) arrives with MAP-7; the served-tile path arrives with
its own ADR; and the capability registry itself is created when the second capability exists, since one
capability is a function and two are a registry.

---

## Consequences

**What this buys.** A developer, human or agent, knows where a file goes before writing it, and the one
boundary that is already load-bearing (platform below domain) is checked by CI instead of remembered. The
pure-decision module gives the test-first method somewhere to land, which is what stops a suite from becoming
database fixtures with assertions. And the capability layer has a home before the first capability exists,
which is the only order in which it is cheap.

**What this costs, accepted with eyes open.**

- **A move that touches every import in the stack**, paid once, at the only moment it is small.
- **One more dev dependency and one more CI step**, which is real and is the price of the rule not being a
  review item.
- **A `rules.py` that will look empty in the first package.** That is deliberate: the alternative is that the
  first decision lands in a model method and the second one follows it there.
- **Two layers that assert little today.** The contract grows with the packages; the gate does not wait for
  it to be interesting.

**What this forecloses.** A top-level `models/`, `views/` or `services/` split, and a package reaching into
another package's `models`. Nothing the foundation left open: the permission model, the tile server, the
operation-log projection strategy and the capability exposure protocol are all untouched here.

**What must be revisited, and when.** A package past roughly ten models splits, and that is a refactor rather
than an ADR. If two same-tier packages start importing each other, one of them is a lower-tier concern born
in the wrong place. The settings split when a deployment target exists. **And if the layers contract ever has
to be relaxed to make a feature land, the feature is in the wrong package and the contract is right.**
