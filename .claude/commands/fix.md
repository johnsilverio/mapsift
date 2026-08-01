---
description: Lint, format-check, and type-check the modified files, then fix what they report.
---

Run the checks for the languages of the files that were modified, then fix every error or warning reported.
Do not suppress with `# noqa`, `# type: ignore`, `@ts-ignore`, or `#[allow(...)]` unless absolutely necessary
(and justify it in a comment if you must).

Prefer the `justfile` recipes (`just lint`, `just typecheck`), since ADR-0001 section 3 makes the container
the source of truth for running. The raw commands below are what those recipes wrap, and the fallback while
the scaffold does not exist yet. Scope every command to the modified paths, never to the whole repository.

- **Python** (`apps/api`): `uv run ruff check`, `uv run ruff format --check`, `uv run mypy --strict` on the
  modified paths. The type checker is mypy `--strict` with django-stubs, never pyright, never `ty`.
- **TypeScript / Angular** (`apps/web`, `libs/ui`): `ng lint` and `ng build` (the strict `tsc` runs there).
  Fix lint, type and template errors. The linter is a CI gate in its own right (ADR-0001 section 6), so a
  green `ng build` alone is not enough.
- **Rust** (`libs/core`): `cargo clippy`, `cargo fmt --check`.

Only run the checks for languages actually present in the modified files.

If a generated contract is among the modified files (the OpenAPI-derived types or the Rust-derived core
types), do not hand-edit it: regenerate it (`just contracts`) and fix the source of truth instead (PRD M12).
