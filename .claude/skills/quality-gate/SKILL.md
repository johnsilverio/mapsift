---
name: quality-gate
description: Validate an implementation locally before commit or PR, running the same checks CI will run for the stack you touched. Stops you committing on red. Use before any commit or pull request, and whenever the user asks whether the work is ready or if the checks pass. Triggers on "/quality-gate".
argument-hint: "[optional scope note]"
---

# Quality gate

Local mirror of the checks CI runs (`specs/testing.md` section 9, ADR-0001 section 6). A green run here
means those gates should pass on the pull request. It **complements, does not replace** CI: only the
remote checks are authoritative for merging. Treat green here as "safe to push", not "merge approved".

Run only the phases for the stack actually touched. Optional focus: $ARGUMENTS

## Where things live: one repository, two toolchains, no orchestrator

**ADR-0001 section 1 decided one repository organised by unit of deploy and the move has NOT run** (it is sequenced
after `PRD.md`). There is **no monorepo tool** in either layout: each stack keeps its native toolchain, and
what will span them is a `justfile` plus compose, created with the api scaffold.

What decides where you type, today:

- **`apps/web` is still its own repository with its own Angular workspace**, so **every web command runs
  from `apps/web`**. After the migration the workspace hoists and they run from the repository root.
- **The api does not hoist in either layout**, because uv is per project. Its commands run from `apps/api`,
  which is still empty.

ADR-0003 makes the container the source of truth for **running**, with the host toolchain there for
**authoring**. Where a compose service exists, prefer it over the host command.

## Phase 1: the web (`apps/web`)

```bash
cd apps/web                       # until the ADR-0001 section 1 migration runs
pnpm build
pnpm exec ng test --watch=false
```

`pnpm build` runs the strict `tsc`, so it is also the type check. **Never invoke the Vitest CLI directly**:
the `@angular/build:unit-test` builder is what wires the tsconfig path aliases, `@mapsift/ui` included, so
a direct Vitest run fails to resolve the library. `--watch=false` is explicit because watch defaults to true
in a TTY.

`pnpm e2e` runs Playwright and boots its own dev server. Run it when the change touches a journey, not on
every gate: end-to-end is where integration risk is proven, not where behaviour is specified
(`specs/testing.md` section 4).

**ESLint is registered debt** (ADR-0001 section 17): it is not set up yet, so there is no lint step here to
run. Do not invent one, and do not report a lint pass that did not happen.

## Phase 2: the api (`apps/api`)

**`apps/api` is an empty folder.** Verify with `ls -A apps/api` before claiming anything about it. Until the
scaffold lands there is nothing to run here, and saying so plainly is the correct output rather than
inventing a green result.

When it exists, the gate is the one `specs/testing.md` section 9 and ADR-0001 section 6 define:

| Check | Fails when |
| --- | --- |
| lint and type check | **the tool is not chosen yet.** ADR-0001 section 19 requires the gate and deliberately does not name the linter or the type checker. It is decided at scaffold and recorded in `apps/api/docs/dependencies.md`. Do not assume a tool here |
| `pytest` | a test is red. Runs against the **containerized PostgreSQL with PostGIS** from ADR-0003, the same image production runs, because triggers, row-level security, GRANTs and PostGIS cannot be faked |
| `lint-imports` | a package imports upward through the tier order, or `engines/` imports a domain package (ADR-0002 section 5) |
| missing-migration check | a model changed with no migration. In a model-heavy system this is the cheapest real bug the gate catches |
| schema freshness | regenerating the OpenAPI schema differs from what is committed |
| capability-registry freshness | the code registry and the permission rows disagree (ADR-0007 section 3) |

## Phase 3: the generated contract, when both sides moved

The api owns the schema; the web commits both the snapshot it consumes and the types generated from it
(the one-pull-request rule). Regenerating either must produce no diff:

```bash
git diff --exit-code
```

A stale contract is a red build and never a silent drift.

## Phase 4: invariant coverage

`specs/testing.md` section 6.1: a test implementing an invariant **names its identifier**, and CI fails when
an invariant I1 to I23 has no test naming it and no allow-list entry. Locally this is a grep, and it is worth
running when the change implements or touches an invariant.

## Phase 5: report and block on red

Report each phase you ran on its own line, unambiguously, as PASS or FAIL. **Say explicitly which phases you
skipped and why** ("api not scaffolded", "no journey touched"), because a report that silently omits a phase
reads as a pass.

If anything is FAIL, state that the change is **not ready to commit or push**, show the failing output, and
stop. Do not commit, do not open a pull request, and do not paper over it by skipping or deleting a test.
Committing on red is forbidden by the project workflow, and **weakening a test to make it pass is forbidden
outright** (`specs/testing.md` section 10): if a test blocks you and you believe it is wrong, that is a
conversation about the requirement, in the requirement's document.

## Phase 6: diff summary

Only when the gate passes, summarize the pending change so the scope can be sanity-checked.

```bash
git status --short
git diff --stat
```

Flag anything unexpected: files outside the intended scope, a generated artifact that should not be
committed, a lockfile from a package manager other than pnpm or uv, or **anything under `apps/api` that
ADR-0002 section 12 says must not exist yet** (`PaymentPlan` behaviour, a legacy import package, the GIS
surfaces, the embedded editor).

**And one check specific to this tree:** no production data, ever. If the diff contains a dump, a fixture
derived from the 1.0 database, or a credential, stop and say so. Foundation 9.1 and ADR-0003 section 2 forbid
production data outside production, version control included.
