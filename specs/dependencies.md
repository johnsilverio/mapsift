# Mapsift dependency survey

> **Purpose.** The canonical home for external-dependency versions and for the particularity of each one that actually bites. It exists to serve the foundation's external-dependency rule: Mapsift leans on fast-moving libraries where stale knowledge is a defect, so a choice is made against current documentation and against the version actually installed, never from memory.
>
> **How to read an entry.** Each carries a **status**, what was **verified and when and against which source**, and the **particularity** that changes how it is used. Two words are not interchangeable here. **Ratified** means the foundation closed the *choice* (Django is the backend). **Pinned** means a *version* is fixed, which only a lockfile can do, and no lockfile exists yet because the scaffold does not exist. Everything below is therefore a survey finding, not a pin.
>
> **The rule when this document and reality disagree.** The installed version wins on behaviour and this document is the one to correct. A claim here with no verification date is a claim to distrust.
>
> **What is deliberately elsewhere.** Data sources, the fixture corpus, the CRS matrix, and the per-tool expected behaviour live in `specs/data-and-tooling-references.md` and are referenced rather than duplicated. Cost and quota reality for imagery lives there too (section 1.5).

---

## 1. Backend, `apps/api`

> **Survey round of 2026-08-01.** The four rows this section carried as "ratified choice, no surveyed version"
> were surveyed, and the round found three more questions the scaffold forces and nobody had decided: the Django
> major inside the ratified 5 line, the Python packaging and lock tool, and the interpreter. All three are settled
> below. Two things the round did **not** do: it did not pin anything, because only a lockfile pins, and it did not
> change a ratified decision, because the answers all land inside what the foundation already ratified.

| Dependency | Status | Notes |
|---|---|---|
| **Python 3.13** | ratified as a 3.12+ floor (foundation section 10); the interpreter is chosen here, surveyed 2026-08-01 | current patch 3.13.14 (2026-06-10), line supported to **2029-10-31**. **3.14 is the newest stable** (3.14.6, supported to 2030-10-31) and is deliberately not taken; Celery is the binding constraint and the reasoning is below. *Verified against the Python developer guide and the release index.* |
| **Django 5.2 LTS** | ratified as "Django 5" (foundation section 10); the release inside that line is chosen here, surveyed 2026-08-01 | current patch 5.2.16 (2026-07-07). Mainstream support ended 2025-12-03; **security and data-loss support runs to 2028-04-30**. For contrast: 6.0.7 is the current release and its whole line ends 2027-04-30, 6.1 is at rc1 and lands this month, and **6.2 LTS is due April 2027 with support to April 2030**. **This stays inside the foundation's ratified "Django 5", so it is a pin and not a foundation round.** Reasoning and the migration plan below. *Verified against the Django download page and the release cycle index.* |
| django-ninja | ratified; surveyed 2026-08-01 | **1.6.2**, declaring `Django >=3.1,<6.1` and `pydantic >=2.0,<3.0`. The OpenAPI schema it emits is the source of the Python-to-TypeScript contract (PRD M12). **The `<6.1` cap is live rather than theoretical:** Django 6.1 releases this month and django-ninja does not accept it, so the 6 line was not a place to be standing anyway |
| Pydantic v2 | ratified; surveyed 2026-08-01 | **2.13.4** (2026-05-06), Python 3.9 to 3.14, on pydantic-core >=2.33.0. Validation at every boundary (API input, WebSocket messages, config) |
| Django Channels | ratified; surveyed 2026-08-01 | **4.3.2**, classifiers covering Django 4.2, 5.1, 5.2 and 6.0. **Transport and presence only.** `group_send` is at-most-once and silently drops over capacity, which is the scar behind I2; sync correctness never relies on delivery |
| Celery | ratified (foundation v0.6); surveyed 2026-08-01 | **5.6.3** (2026-03-26), on billiard, kombu, vine and click. Background jobs and heavy analysis. **Its own documentation lists supported CPython as 3.9 through 3.13 and does not list 3.14**, while the 5.6 release notes claim initial 3.14 support. That gap is what chooses the interpreter, below |
| psycopg 3 | **added to this survey 2026-08-01**, previously absent from it | **3.3.4** (2026-05-01), Python >=3.10, with `binary`, `c` and `pool` extras. This is **the same version SP-1 measured on** (ADR-0004), worth holding aligned so the spike's numbers stay comparable to the first real implementation |
| **uv** | **decided 2026-08-01**; previously undecided, with ADR-0001 saying only "a Python packaging and lock tool" and `CLAUDE.md` saying "uv or poetry" | **0.12.1**. One tool for the interpreter, the virtual environment, the universal lockfile, the workspace, and the runner. Reasoning and its one real cost below |
| mypy `--strict` | ratified; surveyed 2026-08-01 | **2.3**, Python >=3.10. **The 2.0 line is a real break rather than a renumber:** `--local-partial-types` and `--strict-bytes` became defaults, `--allow-redefinition` took the newer semantics, Python 3.9 was dropped, and `--num-workers` added parallel checking reported at up to five times faster, which the CI gate wants. **The version usable here is decided by django-stubs, not by mypy**, see the pairing below |
| django-stubs | ratified; surveyed 2026-08-01 | **6.0.7** targets Django 6.0 with **partial** support for 5.2, 5.1 and 5.0, on mypy 1.13 to 2.3 and Python 3.10 to 3.14. The **5.2 line** (5.2.9) targets Django 5.2 fully and caps mypy at 1.19. This pairing is the one real cost of the LTS choice and is settled empirically at scaffold, below |
| ruff | ratified; surveyed 2026-08-01 | **0.16.1**, and still **0.x**, so a minor can carry a breaking change. Pin it exactly and move it deliberately, the same discipline uv gets |
| pytest | ratified; surveyed 2026-08-01 | **9.1.1**, Python >=3.10 |
| pytest-django | ratified; surveyed 2026-08-01 | **4.12.0** (2026-02-14), Python >=3.10, pytest >=7.0, classifiers covering Django 4.2, 5.1, 5.2 and 6.0 |
| pytest-asyncio | ratified; surveyed 2026-08-01 **with a caveat** | **0.26.0**, declaring `pytest >=8.4,<10`, so it accepts the pytest 9.1.1 above. **Its release date could not be confirmed from the package index** (the index's own release listing came back internally inconsistent), so this row is re-verified when the lockfile resolves it. Recorded as unconfirmed rather than asserted |
| PostgreSQL 18 + PostGIS | ratified (foundation v0.14, superseding the 16 of v0.6) | **the major is ratified and the minor always runs current**, per upstream policy. Chosen by remaining support runway: PostgreSQL supports each major for five years from its initial release and **designates no LTS at all**, so the pick is the newest stable major the ecosystem supports, not a nonexistent long-term line. *Verified 2026-07-31 against the upstream versioning policy and release list: 14 through 18 supported, 14 expiring 2026-11-12, current minor 18.4, next major in beta and therefore excluded.* PostGIS 3.6 covers PostgreSQL 12 through 18 (3.6.2 released 2026-02-06), and Django's floor is PostgreSQL 14, so neither constrains the choice. See the particularities below |
| Redis | ratified | Channels layer and Celery broker. **The Client View Record possibility is closed and this row no longer carries it:** SP-1 eliminated the row-version strategy on read cost, and ADR-0004 ratified the per-project version, whose cursor is an ordinary integer column in PostgreSQL. Redis is therefore off the sync correctness path entirely, which is a better place for it to be |

**Nothing in this section is unsurveyed as of 2026-08-01, and as of the same day it is PINNED.** The `apps/api`
scaffold landed with `apps/api/uv.lock`, so from here the lockfile is the authority on behaviour and this section
records the reasoning and the particularity rather than a second copy of it. Every version the survey predicted is
what actually resolved, which is the useful part of the result:

| Pinned | Resolved 2026-08-01 | Note |
|---|---|---|
| Python | **3.13.13** | Fetched by uv itself; the host runs 3.14.6 and carries no 3.13, so the pin is enforced by the resolver rather than by what happens to be installed. `requires-python = ">=3.13,<3.14"` carries the ceiling with its reason in a comment |
| Django | **5.2.16** | The LTS line, exactly as chosen above |
| django-ninja | **1.6.2** | |
| Pydantic | **2.13.4** | with pydantic-core 2.46.4 |
| pydantic-settings | **2.14.2** | **New, and not in the survey that preceded it.** It is how config becomes a Pydantic boundary (I5, C5) rather than a pile of `os.environ` reads |
| psycopg | **3.3.4** (`[binary]`) | The same version SP-1 measured on. **The `binary` extra is a development convenience and is revisited at the container step**, since upstream advises against it for production in favour of the C or pure implementation against a system libpq |
| mypy | **2.3.0** | with librt 0.13.0 and ast-serialize 0.6.0, which are the mypyc runtime pieces the 2.x line brought |
| django-stubs | **6.0.7** | with django-stubs-ext 6.0.7 |
| ruff | **0.16.1** | |
| pytest | **9.1.1** | with pytest-django 4.12.0 |

**Deliberately not installed yet, and the reason is a rule rather than an oversight:** Celery and Channels are
ratified and have no consumer in the scaffold, so they arrive with the code that imports them. A dependency in a
lockfile that nothing imports is a ghost that still has to be upgraded, audited and explained.

### The django-stubs and mypy pairing: ANSWERED, and the preferred branch won

The survey left this as the one empirical question and set the order: try django-stubs 6.0.7 with mypy 2.x against
Django 5.2 first, fall back to the 5.2 stub line with mypy 1.19 if partial support produces false positives.

**It was tried and `mypy --strict` reports `Success: no issues found in 9 source files`.** So the fallback is not
needed: the codebase gets Django 5.2 LTS **and** the current mypy, with its stricter defaults and its parallel
checking. The cost the survey feared did not materialise, and this row stops being a pending decision.

Two mypy plugins are configured together and they do different jobs, which is not obvious from either project's
documentation: `mypy_django_plugin.main` teaches mypy the ORM and the settings, and `pydantic.mypy` teaches it that
a model validates and coerces its input. Without the second one, every correct `Environment(secret_key="...")` call
is an error because the field is declared as a `SecretStr`, and a settings object populated from the environment
reads as a constructor missing every required argument. `init_typed = false` is what states that in the config.

### The type checker loads Django settings, so the toolchain needs an environment too

This one cost real time and is worth reading before it costs it again. The settings module validates the
environment with no fallback for `SECRET_KEY` or `DATABASE_URL`, which is what ADR-0001 section 4 asks for. The
consequence nobody expects is that **django-stubs constructs its mypy plugin by importing those settings**, so a
missing variable does not arrive as a settings error. It arrives as:

```
error: INTERNAL ERROR -- Please try using mypy master on GitHub
Error constructing plugin instance of NewSemanalDjangoPlugin
```

which reads exactly like a broken type checker and is nothing of the sort. The same class of surprise sits in the
test suite: **pytest-django sets Django up inside `pytest_load_initial_conftests`, which runs before any
`conftest.py` is imported**, so a conftest cannot supply those variables in time. Two things follow and both are
on disk. `config/settings.py` wraps the failure in `ImproperlyConfigured` with a message naming `.env.example`, so
the toolchain fails legibly instead of cryptically. And `DJANGO_SETTINGS_MODULE` is deliberately absent from the
pytest configuration while every test is a pure decision that needs neither Django nor a database; the window that
writes the first ORM test turns it on and supplies the environment the way the suite is actually run.

### Two smaller traps found while wiring the boundary

- **`PostgresDsn` rejects `postgis://`.** The ratified database is always spoken of as PostgreSQL plus PostGIS, so
  that scheme reads as the obvious one and is not valid. PostGIS is selected by Django's database ENGINE
  (`django.contrib.gis.db.backends.postgis`); the URL scheme stays `postgresql://`. There is a test for it.
- **`PostgresDsn` is a multi-host URL**, so there is no `.username`, `.password`, `.host` or `.port` on the object.
  They live per host in `hosts()[0]`, and reading them off the URL raises `AttributeError` at runtime rather than
  failing a type check.
- **A list field needs `NoDecode`.** pydantic-settings JSON-decodes a raw environment value before any validator
  runs, so the comma-separated form an operator actually writes fails before a splitting validator sees it. The
  trap only appears on the real environment-variable path, which is why the test exercises that path and not only
  the constructor.

### `django.contrib.gis` is not in INSTALLED_APPS yet, and that is a decision

The database ENGINE is the PostGIS backend from the first line, because the ratified database is PostgreSQL 18
with PostGIS and pointing the scaffold at SQLite would be a lie the `.gitignore` already anticipates. But
`django.contrib.gis` in INSTALLED_APPS loads GDAL and GEOS at import, the developer host is not required to carry
them (ADR-0001 section 3 puts running in the container and authoring on the host), and this machine has no
`gdal-config` at all. Verified: with the ENGINE set and the app absent, `manage.py check` passes on a host with no
GDAL. It goes in with the first geometry model, inside the container.

### Why the pin is Django 5.2 LTS rather than the 6 line

The instinct that produced the PostgreSQL round of foundation v0.14 was to take the major with the most remaining
runway. That instinct is right and its arithmetic does not transfer, because the two projects have opposite release
shapes and **a Django upgrade is not the dump-and-reload event a PostgreSQL major upgrade is**. Django ships a
feature release roughly every eight months and an LTS every two years with three years of support, so there is no
four-year option to pick the way there was on the database. What there is instead is an LTS line, and following it
is the documented strategy for exactly this project's posture: closed scope, built to completion, then run for
years.

Measured from today, the runway is **21 months on 5.2 LTS** (to 2028-04-30) against **9 months on 6.0** (to
2027-04-30). Both paths converge on the same destination, **6.2 LTS in April 2027, supported to April 2030**. The
difference is entirely in how forced the hop is. From 5.2 the hop is optional for a further twelve months after 6.2
ships, which is slack to do it deliberately and under green tests. From 6.0 the hop is mandatory by April 2027 with
no slack at all, and the path to it runs through 6.1, which **django-ninja does not currently accept**.

So the plan of record is one planned LTS-to-LTS migration rather than a release train: build on 5.2 LTS, move to
6.2 LTS after it ships in April 2027, inside the twelve-month overlap.

**The cost, stated rather than hidden.** 5.2's mainstream window closed on 2025-12-03, so it receives security and
data-loss fixes and no ordinary bug fixes. A non-security bug found in Django during the build is not going to be
fixed on that branch, and the answer when it happens is to carry a local workaround or to bring the 6.2 migration
forward, not to wait. That is a real and accepted cost, and it is the reason this reasoning is written down instead
of the version being asserted.

### Why the interpreter is Python 3.13 and not 3.14

Everything else in the backend accepts 3.14: Django 5.2 added it in 5.2.8, Pydantic covers 3.9 to 3.14, django-stubs
covers 3.10 to 3.14, and mypy, pytest and pytest-django all floor at 3.10. **Celery is the single constraint.** Its
own documentation lists supported CPython as 3.9 through 3.13 and does not name 3.14, while its 5.6 release notes
claim initial 3.14 support. Initial support that the supported-versions list has not caught up with is not a thing to
put a background job queue on when the queue runs the heavy analysis path.

3.13 is supported to 2029-10-31, which is well past the 6.2 LTS migration above, so nothing is being bought cheaply
here. **The re-check trigger is written so it is not forgotten:** when Celery's own supported-versions list names
3.14, the interpreter is revisited, most naturally in the same round as the Django 6.2 move.

### uv is the packaging and lock tool

The choice had never been made. ADR-0001 section 2 says only "a Python packaging and lock tool", `CLAUDE.md` said
"uv or poetry", and this survey had no row for it, while `.claude/commands/quality-gate.md` had already started
writing `uv run` in its fallback commands. That is tooling deciding what its authority left open, so the decision is
taken here and the tooling becomes correct rather than presumptuous.

**uv, for four reasons that are this project's rather than general enthusiasm.** It **manages the interpreter
itself**, so the 3.13 pin above is enforced by the same tool that resolves the dependencies instead of by a
convention about what is installed on a machine. Its resolution and installation are roughly an order of magnitude
faster than the alternative, which lands directly on **the containerised loop ADR-0001 chose and named as carrying
real friction**: a dependency layer that rebuilds in seconds instead of a minute and a half is the difference
between a gate people run and a gate people skip, and the performance rule of foundation section 10 counts that as
structural rather than as an optimisation. Its lockfile is **universal across platforms**, which matters in a
repository whose developers, containers and CI are not the same environment. And it is Astral's, like **ruff, which
is already ratified**, so the Python side of the toolchain is one vendor and one release cadence to track rather
than two.

**The cost, and it is the same shape as ruff's.** uv is at **0.12.1 and still pre-1.0**, so a minor release can
break something. It is pinned exactly, in the lockfile and in the container image, and moved deliberately. The other
honest note: poetry remains the stronger tool for publishing a library to a package index, which Mapsift's backend
never does, so that advantage is not one this project can spend.

### The type-checking pairing is the real cost of the LTS, and it is settled at scaffold rather than guessed

django-stubs versions track the Django release they target, which turns the Django choice into a mypy choice.
Pairing Django 5.2 with **django-stubs 5.2.x** gives full stub fidelity for that Django and **caps mypy at 1.19**,
leaving the project a whole major behind on its own type gate from day one, without mypy 2.0's stricter defaults
(which a `--strict` codebase wants) and without `--num-workers` (which the CI gate wants). Pairing it with
**django-stubs 6.0.7** allows **mypy up to 2.3** but supports Django 5.2 only **partially**, which its maintainers
document as a deliberate mode rather than an accident.

**This is an empirical question and it is answered with the real code, not here.** At scaffold the order is:
django-stubs 6.0.7 with mypy 2.3 against Django 5.2 first, and the fallback to django-stubs 5.2.x with mypy 1.19 if
partial support produces false positives on 5.2 APIs. Whichever wins is recorded here with the date and the evidence.
The tension disappears on its own at the 6.2 LTS migration, when the stub line and the Django line meet again.

### PostGIS particularities that already shape decisions

- **`ST_TransformPipeline` requires PostGIS 3.4.0 or later** and, when given a PROJ pipeline string, **does not apply automatic axis normalisation**, so the caller adds or removes an `axisswap` step. This is the path under consideration for computing the Sistema Geodesico Local frame (PRD M5), where PROJ's `+proj=topocentric` is the EPSG:9836 conversion. *Verified 2026-07-30 against the PostGIS documentation and the PROJ operations reference.*
- **Row-level security must be ENABLED and FORCED.** A role that owns the table bypasses a policy that is not forced, and a role holding the bypass privilege defeats it outright, which is why PRD N2 makes both explicit test cases rather than review notes. The direct-to-PostGIS tile role must connect non-privileged and set the tenant on its session or it defeats I4.
- **Sequences do not give a safe change-feed cursor.** A sequence value is taken before commit, so a transaction that started later can commit first with a higher number, and a consumer polling `WHERE position > last` skips the rows that commit late. That is silent data loss, which is the one thing this product refuses. Documented alternatives: transaction ids (`xid8` with `pg_snapshot_xmin(pg_current_snapshot())`, ordering by transaction id then position), a serialized counter in a singleton row (correct, serializes all writes), or logical replication. **This is the crux of the OQ-10 spike and the reason the resync cursor is not yet a named version axis in PRD M10.** *Verified 2026-07-30.*

---

## 2. Client core, `libs/core`

| Dependency | Status | Notes |
|---|---|---|
| Rust with Cargo | ratified (foundation 9.6.2) | the client logic core: operation queue, optimistic apply, optimistic conflict detection, client geometry |
| PyO3 | **rejected** (foundation v0.6) | the core does not run on the server; the conflict rule is one specification implemented twice and golden-tested |
| wasm-bindgen with wasm-pack | surveyed 2026-07-30, the standard path | see below |
| The type generator to TypeScript and Dart | **surveyed, and the Dart half has no tool** | see below |
| flutter_rust_bridge | surveyed 2026-07-30 | v2 is still a development release (`2.0.0-dev.32`) though actively maintained; only relevant when `apps/mobile` exists, which ADR-0001 forbids scaffolding now |
| The geometry engine | surveyed 2026-07-30 | see below |

### The WASM build path

**wasm-bindgen is actively maintained** (a release on 2026-06-24) and **wasm-pack is the orchestration on top of it**: it invokes Cargo against the `wasm32-unknown-unknown` target, runs the output through wasm-bindgen to produce the JavaScript glue **and the TypeScript definitions**, runs `wasm-opt` for size, and writes a `pkg/` directory shaped like an npm package. That `pkg/` is generated output and belongs in `.gitignore`, not in version control.

**The consequence for PRD M12 is good news on one side.** wasm-bindgen generates the TypeScript definitions itself, so the TypeScript half of the core contract largely comes out of the build rather than needing a separate generator. What remains is the Dart half.

### Angular's WASM integration is the constraint that shapes the scaffold

*Verified 2026-07-30 against the Angular CLI's WASM/ES-module integration work and the wasm-bindgen deployment guide.*

- The application builder supports **direct import of WASM files**, following the WebAssembly/ES module integration proposal.
- It **requires native async/await and top-level await**.
- **The application must be zoneless.** A Zone.js application is incompatible and the build errors out. Mapsift is zoneless by construction (the Angular default since v21), so this is satisfied, and it converts zoneless from a modern-default into a **hard requirement**: turning Zone.js back on would break the core's integration path.
- **A type definition file is needed per WASM file**, either hand-written or supplied by the library author. wasm-bindgen supplies one, which is a concrete reason to go through wasm-pack rather than raw Cargo output.
- Source phase imports are currently supported only in esbuild and Node 24, and wasm-bindgen's default output assumes the module is natively an ES module, so a bundler is in the path either way.
- **The feature rides an active standards proposal that may still change**, so behaviour can differ between versions.

**Design instruction that follows from that last point:** the WASM load is isolated behind one thin adapter in `apps/web`, so a change in the proposal touches one file instead of every consumer of the core. This is cheap now and expensive to retrofit.

### Type generation to Dart is an open hole, and it must not be assumed solved

The foundation (9.6.2) and PRD M12 require the core's types to be generated to **TypeScript and Dart**. The survey found no single tool that does both:

- **Specta** is actively maintained and exports TypeScript (stable), Swift, Go, Kotlin, Python, C#, Java, JSON Schema, Zod, and OpenAPI. **Dart is not among them.**
- **ts-rs** generates TypeScript only.
- **Typeshare** statically analyses Rust source, which loses information and does not see types from other crates.

So the realistic shape is an intermediate schema (JSON Schema is the obvious candidate, and Specta emits it) plus a Dart generator on the other side, or a purpose-built emitter. **This is not decided, it does not block the scaffold** (mobile is not scaffolded and the TypeScript side comes from wasm-bindgen), and it is recorded here so nobody plans as if the Dart half were solved.

### The geometry engine, and why PRD M13's tolerance is structural

The client core uses the pure-Rust **`geo`** crate (GeoRust): planar geometries, topological predicates, boolean operations (intersection, difference, union, clip, xor), affine operations, 64-bit floats by default. Buffering lives in the separate **`geo-buffer`** crate, which implements it via a straight skeleton and handles non-convex polygons and polygons with holes.

**The `geos` crate (Rust bindings to GEOS) is not an option for the client core**, because it links dynamically against a system-installed GEOS, and there is no system GEOS inside a browser. The client therefore runs a genuinely different implementation from the server's GEOS-via-PostGIS, which means **the divergence PRD M13 absorbs with a metre-denominated tolerance is structural rather than incidental**. That is the reason the golden test is written to tolerate it instead of demanding bit-equality, and the reason a legal-weight verdict inside the tolerance band falls to the preserving side.

---

## 3. Web, `apps/web` and `libs/ui`

### Angular

**Verified 2026-07-30 against the official documentation and against the toolchain installed in the editor prototype.** The stable line is **v22** (since 2026-06-03), and Angular moved to an annual major cycle with it.

- **Zoneless is the default since v21.**
- **Signal Forms, `resource()` and `httpResource()` are stable since v22.0**, so none of the three is experimental any more.
- **`ChangeDetectionStrategy.Default` is deprecated in favour of `Eager`**, and neither belongs in this codebase because the schematic already emits `OnPush`.
- **The component schematic emits** a folder holding the class, the template, the stylesheet, and the spec, standalone implied and with **no type suffix**; `--type` has no default and is not passed. Guards and interceptors are functional by default.
- **OnPush is the default and the schematic does not write it.** Verified in the installed template: both the `changeDetection` property and the `ChangeDetectionStrategy` import are emitted **only when the strategy is not OnPush**. So a generated component is OnPush while containing no mention of it, exactly as it contains no `standalone: true`. **Writing the property by hand therefore breaks the ADR-0002 verification rule**, whose test is that a new artifact matches what the generator prints with `--dry-run`. The only prohibited deviation is writing `Eager` explicitly.
- **The application builder is `@angular/build:application`.**
- **`ng test` runs the `@angular/build:unit-test` builder**, whose default runner is **Vitest** (Karma is still selectable). Tests execute in Node with jsdom by default; `--browsers ChromeHeadless` opts into a real browser; `--watch=false` is what a gate wants. Always go through `ng test` rather than the Vitest CLI directly, because only the builder wires the Angular pieces.
- **Consequence carried by ADR-0002:** never pass `--inline-template` or `--inline-style`; the CLI default is the layout.

### The rest of the web stack

| Dependency | Status | Notes |
|---|---|---|
| TypeScript, strict | ratified | CI blocks on any `tsc` violation |
| Zoneless change detection | ratified, and now **load-bearing** | the Angular default since v21, and the WASM integration path in section 2 **requires** it: a Zone.js application cannot import the core's WASM module at all |
| MapLibre GL JS v5 | ratified as the renderer (foundation section 8) | **requires WebGL2**: v5 removed WebGL1 support, and the library targets ES2019, which puts browsers and tooling older than roughly 2022 outside the floor. This is what sets the PRD N11 support floor. *Verified 2026-07-30 against the v5.0.0 release notes.* |
| The editing library (Terra Draw or Geoman) | **not decided**, gated ADR (foundation section 8) | the prototype ran Terra Draw with snapping (`toCoordinate`, `toLine`) through a MapLibre adapter, which is **evidence that the combination works and is not a decision** |
| Tailwind CSS v4 | **ratified by the artifact, not a candidate** | the foundation-ratified component library depends on it structurally: `class-variance-authority` in 45 files, `clsx` in 65, and `twMerge` as the composition primitive of every component. Replacing it is not a choice between options, it is rewriting the library. The open work is not the choice but the **mandatory reconciliation** between U1's closed scales and Tailwind v4's `@theme`, which must resolve to one source of truth rather than two that drift |
| `@mapsift/ui` | ratified (foundation, handoff section 10) | a vendorized ZardUI fork at `libs/ui`, built with ng-packagr, consumed by package name only (PRD U10) |
| The component catalog tool (Storybook or equivalent) | not decided, ADR (foundation 9.6.5, PRD U12) | its scope includes the platform-neutral token export |

### PINNED 2026-08-01 by the workspace scaffold

The Angular workspace exists and `package-lock.json` is the authority from here. Generated with the **current**
CLI (22.1.2) rather than the 22.0.0 installed globally, because generating with an older CLI reproduces an older
schematic shape, which is the whole reason ADR-0002 makes generation CLI-first.

| Pinned | Resolved | Note |
|---|---|---|
| @angular/core | **22.1.0** | with CLI and `@angular/build` at 22.1.2 |
| TypeScript | **6.0.2** | see the strict finding below |
| ng-packagr | **22.1.0** | the `@angular/build:ng-packagr` builder |
| @angular/cdk | **22.1.0** | the library uses it in 42 files |
| Vitest | **4.0.8** | the `@angular/build:unit-test` default runner, with jsdom |
| angular-eslint | **22.1.0** | added with `ng add`, because `ng new` ships no linter and ADR-0001 section 6 requires one |
| @ng-icons/core and /lucide | **34.0.0** | replaces lucide-angular, see below |
| clsx, class-variance-authority, tailwind-merge | current | what the library actually imports, in 65, 45 and 2 files, which is the structural Tailwind dependency this document already recorded |

### TypeScript 6 turns `strict` on by default, and the hazard is the inverse of the obvious one

The generated `tsconfig.json` contains **no `"strict": true`**, which reads like a missing gate against C5 and is
not one. Verified empirically rather than assumed: compiling with the generated config rejects an implicit `any`
and a null assignment exactly as `--strict` forced does. TypeScript 6 made it the default, which is why the
schematic stopped writing it.

**So the thing to watch is the opposite of what it looks like.** Adding the line back is harmless noise;
**pinning TypeScript below 6 would silently turn strict off across the whole front end**, with nothing in the
configuration showing it. Anyone considering a downgrade owns that consequence.

### lucide-angular is incompatible with Angular 22 in every published version

Its peer is pinned at `13.x - 21.x` including in its 1.0.0, so this is blocked upstream rather than a version to
pick. The icon module moved to **@ng-icons/core and @ng-icons/lucide**, which declare peer `>=21.0.0` and which
**the ratified editor prototype already runs on Angular 22**, so the combination is proven inside this repository
rather than assumed. Same Lucide artwork, same public API on `ui-icon`. All 89 icon names were verified against
the installed package's real exports instead of translated by naming convention, and the one custom icon was
rewritten as an SVG string. `uiAbsoluteStrokeWidth` was dropped: ng-icons has no equivalent and no consumer used it.

### The library's own debt, recorded rather than silently carried

Found while making the workspace green, and deliberately **not** fixed here because it is design-system work under
PRD section 9: **69 components use an inline template**, against ADR-0002 section 2 and its bounded exception;
**four directives remain on a camelCase selector** while the library's majority convention is kebab-case, and they
are enumerated by file in `libs/ui/eslint.config.js` so the debt stays countable; and the library had **no tests at
all** until the three added with this scaffold.

### Versions observed in the prototype (evidence, not pins)

The editor prototype ran this combination successfully, which is useful as a starting point for the scaffold's own resolution and is **not a decision and not a pin**: Angular 22.0.0 with CDK 22.0.2, TypeScript 6.0.2, MapLibre GL JS 5.24.0, Terra Draw 1.31.2 with its MapLibre adapter 1.4.1, Turf 7.3.5, PMTiles 4.4.1, Protomaps basemaps 5.7.2, Tailwind CSS 4.1.12, ng-icons 33.3.0. The scaffold resolves its own versions and pins them in lockfiles; this row exists so nobody has to excavate the prototype to know what was known to work.

---

## 4. Infrastructure and services, `infra/`

| Dependency | Status | Notes |
|---|---|---|
| The MVT tile server (Martin, pg_tileserv, or Tegola) | **not decided**, ADR; Martin is the leading candidate (foundation section 10) | whichever wins must connect under a non-privileged role that sets the tenant on its session (PRD N2, T6.1) |
| TiTiler | ratified as a leading choice, not an invariant (foundation v0.7) | dynamic raster tiling is compute-on-read, so its cost scales with request volume |
| Tippecanoe and PMTiles | **gated**, not default | the pre-generated path is introduced only when the measured I6 per-tile budget is crossed (foundation section 6, PRD N1) |
| S3 or MinIO | ratified at the same level (foundation v0.7) | object storage for uploads, exports, and imagery |
| Docker and compose | ratified by ADR-0001 | containerised from the first commit, development and deployment alike; compose kept to the OCI-standard surface so a Podman host runs it unchanged |
| Copernicus Data Space and openEO | ratified as the imagery source | the free tier is metered and the cost model is **OQ-3**; the quota figures and the serving-cost reasoning live in `data-and-tooling-references.md` section 1.5 and are not duplicated here |

### 4.1 Observability, surveyed 2026-08-03

The foundation closed the *properties* in v0.16 and left the *tools* to an ADR whose trigger is the first real
users, which is the same split section 9.6.5 uses for the component catalog. This subsection is the survey that
ADR walks through. Nothing here is installed.

| Dependency | Status | Notes |
|---|---|---|
| OpenTelemetry Python, traces and metrics | **candidate**, and it is what the vendor-neutrality property means concretely | the traces and metrics SDKs are **stable**; the Django and Celery instrumentations were both released 2026-06-24, so they are current rather than abandoned. *Verified 2026-08-03.* |
| OpenTelemetry Python, **logs** | **not usable as the log path yet, and this is the load-bearing row** | as of **May 2026** the language-status table lists Python logs as **Development**, while Java, .NET, C++ and PHP are stable and Go and Rust are beta. The logs signal itself is stable in the specification, so this is an SDK gap rather than a design gap. The log path therefore runs through the standard library with trace identifiers injected, and this row carries the **re-check trigger**: when Python logs reach stable, revisit the mechanism, never the property. *Verified 2026-08-03.* |
| A structured-logging library (`structlog` with `django-structlog`, against the standard library plus a JSON formatter) | **not decided**, part of the same ADR | Django's own components all log through the standard library and its `LOGGING` dict maps to `dictConfig`, which is the argument for staying there; `django-structlog` binds a request identifier and a user per request and **supports django-ninja and Celery by name**, which is exactly the two surfaces PRD N9 requires the correlation keys on, which is the argument against hand-rolling it. Decide with the first code that logs. *Verified 2026-08-03.* |
| **Grafana** as the backend, with Alloy as the collector | **the owner's stated preference (2026-08-03), recorded here rather than in the foundation**, because a tool is an ADR and not a constitutional decision (the 9.6.5 precedent) | it composes with the neutrality property rather than fighting it: Alloy speaks OTLP, so the application emits the same telemetry whether Grafana or anything else consumes it. Two deployment shapes to weigh in the ADR: **Grafana Cloud free** (10,000 active series, 50 GB logs, 50 GB traces, 14-day retention, three users, no card) which costs no operational time, against a **self-hosted LGTM** stack, whose own documentation presents the `docker-otel-lgtm` image as development and demo rather than production. *Verified 2026-08-03.* |
| **Grafana Faro** (browser SDK) | **candidate, and it is the piece that answers the owner's actual question** | it collects Core Web Vitals, errors, exceptions, logs and user events from the browser and integrates with OpenTelemetry-JS. Two payoffs rather than one: it is what catches a first user's bug on a device nobody owns, and its web-vitals output is the same class of number PRD N1 defines its budgets in, which makes it a real-device source for the 10.5 measurements. **The caveat is the privacy one:** browser telemetry leaks identifiers through URLs and user events unless the path strips them, and PRD N9's redaction rule applies to it in full. *Verified 2026-08-03.* |
| A dedicated error tracker (GlitchTip, self-hosted Sentry) | **candidate, deliberately second** | GlitchTip speaks the Sentry SDK protocol, so it is a DSN change rather than a code change, and it fits in 1 to 2 GB of RAM, while self-hosted Sentry wants Postgres, Redis and Kafka. Do not run two observability systems on day one: reach for this only if the Grafana error view proves insufficient. *Verified 2026-08-03.* |
| PostgreSQL backup tooling (pgBackRest, Barman, WAL-G, or `pg_dump` alone) | **not decided**, ADR gated on a deployment target | PRD N12 fixes the shape as continuous archiving with point-in-time recovery rather than a periodic dump alone, and fixes that a rehearsed restore is what makes it a backup. `pg_dump` stays useful for object-level recovery and migration and is not the disaster-recovery plan. *Verified 2026-08-03.* |

---

## 5. External standards and norms the code depends on

These are not libraries, and they move, so they carry the same verification discipline.

- **WCAG 2.2, level AA** is the declared accessibility target (PRD N7). Current W3C Recommendation, published October 2023, editorially updated December 2024, adopted as ISO/IEC 40500 in 2025. *Verified 2026-07-30.*
- **Interaction thresholds** used by the PRD N1 budgets: a main-thread task over **50 ms** is a long task and blocks input; an interaction over about **200 ms at the 75th percentile** reads as lag (the Interaction to Next Paint threshold, which replaced First Input Delay in March 2024). *Verified 2026-07-30.*
- **MTGIR 2nd edition (INCRA, approved by Portaria 2.502 of 22/12/2022, published 23/12/2022)**, item 1.4.6 with item 3.8.1 (a certified parcel's area is computed from coordinates referenced to the Sistema Geodesico Local, whose origin for that purpose is the mean of the parcel's coordinates), item 3.8.3 (Gauss formula, in hectares) and item 1.4.4 (vertex positional precision: 0,50 m artificial, 3,00 m natural, 7,50 m inaccessible, with a tolerance of at most three times that between credentialed surveyors). These drive PRD M5 and S5. **This entry replaced a revoked one and is the reason the re-verification discipline exists:** through 2026-07-30 the canon cited the NTGIR 3rd edition (2013), revoked by Portaria INCRA 629 of 05/04/2022 along with the Manual Tecnico de Posicionamento that PRD M5 named as required reading, so a legal-area requirement rested on a dead standard for a full round. *Verified 2026-07-31 against the primary source; the citations live in `data-and-tooling-references.md` section 1.2 and the verification record in `domain-questions.md` section V.1.*
- **EPSG codes in use:** 4674 (SIRGAS 2000 geographic) for storage and interchange; 9836 (topocentric conversion) for the SGL frame; 4326 and CRS84 at the render and interchange edge. The South America Albers definition for the CAR frame is **not pinned** and is part of the same ADR as the SGL computation path.

---

## 6. Not chosen yet: the dependency-gated ADR agenda

Each of these is a decision that this survey must feed before it can be made without guessing. They are listed so the agenda is visible in one place.

1. Tenant isolation mechanism: row-level security against per-tenant views, plus the tile role's session-tenant wiring.
2. The identifier variant (a random against a time-ordered 128-bit identifier), weighing index locality against embedding a device clock the model distrusts.
3. The web client store: IndexedDB against OPFS, behind the storage interface.
4. The geometry encoding across the serializable boundary, with MapLibre needing GeoJSON only at the very edge.
5. The SGL computation path and the equal-area conic definition.
6. The MVT tile server.
7. The type-generation toolchain. The survey narrowed this one: the OpenAPI-to-TypeScript direction and the Rust-to-TypeScript direction are largely solved (the second falls out of wasm-bindgen), so what is actually open is **the Rust-to-Dart path**, which has no single tool.
8. The editing library.
9. The operation-log projection strategy.
10. The object-storage reference shape for images and its offline behaviour.
11. The component catalog tool and the token export format.
12. External GNSS integration for field capture.
13. Field-trip preparation semantics (what a prepared trip downloads and how it is bounded).
14. The docking model beyond a single rail.
15. **The observability toolchain** (added 2026-08-03, foundation v0.16). One ADR covering four choices that
    belong together: the structured-logging library, the client telemetry SDK, the backend and its collector,
    and the sampling and alerting policy. **Its trigger is the first real users**, not a date and not a
    deployment for its own sake. The survey it walks through is section 4.1 above, and the constraint it may
    not relax is the vendor neutrality the foundation closed, so whatever wins stays swappable.
16. **PostgreSQL backup and recovery** (added 2026-08-03, foundation v0.16, PRD N12). The tool, the schedule,
    the recovery-point and recovery-time targets, and where the archive lives. Gated on a deployment target
    existing. The shape is already fixed by N12 and is not this ADR's to reopen: continuous archiving with
    point-in-time recovery, and a rehearsed restore recorded with its date and its numbers.
17. **How the geospatial fixture corpus is stored** (added 2026-08-01, surfaced by writing the `.gitignore`).
    The corpus in `data-and-tooling-references.md` Part 1 includes rasters, git handles large binaries badly,
    and the three options (tracked directly, carried by an LFS-class mechanism, or fetched by a script from a
    recorded source) differ in whether a fresh clone can run the suite offline. Nothing in `.gitignore` excludes
    fixture data, deliberately, because a silently ignored fixture is a suite that passes on one machine and
    fails on another.

**And one that was not an ADR but a spike, now closed:** the sync ordering strategy (a per-project version counter, a transaction-id watermark, or row versioning with a Client View Record) was decided by the SP-1 spike against measurements rather than by reading, and **ADR-0004 ratifies the per-project version**. The documented design space is Replicache's three backend strategies, whose stated ceiling for the serialized shape is about fifty pushes per second per space, comfortably above a project edited by a handful of people. *Verified 2026-07-30.*

---

## 7. How this document is maintained

An entry is re-verified when its version moves, when a decision starts leaning on it, or when it is about to be pinned in a lockfile. The verification date is what makes staleness visible, so it is never omitted. When the scaffold creates lockfiles, the pinned versions become the authority for behaviour and this document records the particularity, the reasoning, and the date, not a second copy of the lockfile.
