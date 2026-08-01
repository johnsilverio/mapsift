---
description: Validate an implementation locally before commit or PR, running the same lint/type/test/contract checks CI will run for the languages you touched. Stops you committing on red.
argument-hint: "[optional scope note]"
---

# Quality gate

Local mirror of the per-language checks CI runs (ADR-0001 section 6). A green run here means those gates
should pass on the PR. It **complements, does not replace** CI: only the PR checks are authoritative for
merging. Treat a green local run as "safe to push", not "merge approved".

Run only the phases for the languages actually present in the pending change. Optional focus: $ARGUMENTS

## How these checks are run

ADR-0001 section 3 makes the container the source of truth for **running**, in development as well as in
deployment, with the host toolchain there for **authoring** (editor, language servers, formatters). The
`justfile` is the top-level orchestration across the ecosystems, so prefer the recipe over the raw command:

```bash
just lint        # per-language linters
just typecheck   # mypy --strict, tsc strict, cargo check
just test        # the suites of each ecosystem
just contracts   # regenerate the cross-language contracts and fail on any diff
```

**Pre-scaffold note.** `apps/`, `libs/` and the `justfile` do not exist yet. Until the scaffold lands, this
command has nothing to run: say so plainly instead of inventing a green result, and fill the real recipe
names into `CLAUDE.md` (the Commands section) when they exist. The raw commands below are the fallback and
the reference for what each recipe must wrap; they are what runs on the host when a recipe is missing.

## Phase 1: Python backend (`apps/api`)

```bash
uv run ruff check apps/api
uv run ruff format --check apps/api
uv run mypy --strict apps/api
uv run pytest
```

Lint, format check, strict type check (mypy `--strict` with django-stubs), and the test suite.

## Phase 2: Rust core (`libs/core`)

```bash
cargo clippy -- -D warnings
cargo fmt --check
cargo test
```

## Phase 3: Angular web and UI (`apps/web`, `libs/ui`)

```bash
ng lint
ng build
ng test --watch=false
```

`ng build` runs the strict `tsc`, so it is also the type check, but it is **not** the linter: ADR-0001
section 6 blocks a change on `tsc` strict **and** the linter, so `ng lint` is not optional. Run unit tests
through `ng test` (the `@angular/build:unit-test` builder, whose default runner is Vitest), never the Vitest
CLI directly, so the `@mapsift/ui` tsconfig path alias resolves. `--watch=false` is explicit because watch
defaults to true in a TTY.

## Phase 4: generated contracts (any language touched)

ADR-0001 section 5 and PRD M12 require the generated contracts to be regenerated in CI, with any difference
failing the build. Two directions: the API's OpenAPI schema generates the TypeScript (later Dart) types, and
the Rust core's types generate the TypeScript (later Dart) types across the boundary.

```bash
just contracts        # regenerate both directions
git diff --exit-code  # any diff here means a stale contract was committed
```

A stale contract must be a red build, never a silent drift. The one deliberate duplication in this repository
is the conflict rule (Rust core and Python server, guarded by golden tests, foundation 9.6.6): no generator
ever emits it, and nobody "fixes" it by generating it.

## Phase 5: report and block on red

Report each phase you ran on its own line, unambiguously (Backend lint/format/types/tests, Rust
clippy/fmt/tests, Web lint/build/tests, Contracts): PASS or FAIL.

If anything is FAIL, state clearly that the change is **not ready to commit or push**, show the failing
output, and stop. Do not commit, do not open a PR, and do not paper over it by skipping or deleting tests.
Fix the cause, then re-run. Committing on red is forbidden by the project workflow.

## Phase 6: diff summary

Only when the gate passes, summarize the pending change so the user can sanity-check the scope. Skip this
phase if there is no `.git` yet, and list the touched paths from your own record instead.

```bash
git status --short
git diff --stat
```

Flag anything unexpected: files outside the intended scope, a generated artifact that should not be
committed, a lockfile from the wrong package manager, or a folder ADR-0001 section 8 says must not exist yet
(`apps/sync`, `apps/desktop`, `apps/mobile`).

## Phase 7: offer a deeper review

Offer, do not auto-run, a review subagent for a deeper pass: `code-reviewer` for the full polyglot review, or
`angular-reviewer` for the Angular conventions and security. Ask first; if the user declines, end here.

Reminder: this gate runs locally what CI runs, but only the remote PR checks are authoritative for merging.
