---
name: fix
description: Run the checks for the stack of the modified files, then fix what they report. Use when checks are failing, when the user says the lint or the types are broken, or asks to fix what CI reports. Triggers on "/fix".
---

Run the checks for the repository the modified files belong to, then fix every error or warning reported.
Do not suppress with `# noqa`, `# type: ignore` or `@ts-ignore` unless there is no alternative, and justify
it in a comment when you must.

**Scope every command to the modified paths, never to the whole repository.** Two toolchains that do not
span each other, and **the ADR-0001 section 1 migration has not run**, so the Angular workspace is still inside
`apps/web` and web commands run from there, while `apps/api` keeps its own
(ADR-0001 section 16), and there is no root task runner.

## The web (`apps/web`)

```bash
cd apps/web                       # until the ADR-0001 section 1 migration runs
pnpm build                        # the strict tsc runs here, so this is the type check
pnpm exec ng test --watch=false   # never the Vitest CLI: the builder wires the path aliases
```

Fix type and template errors. **There is no linter to run yet**: ESLint is registered debt in ADR-0001
section 17. Do not invent a lint command and do not report a lint pass that did not happen.

## The api (`apps/api`)

**Check `ls -A apps/api` first.** It is an empty folder until the scaffold lands, and there is nothing to
run against nothing.

When it exists: the linter and the type checker are **not chosen yet**. ADR-0001 section 19 requires the
gate and deliberately does not name the tools, and ADR-0002 section 12 leaves the decision to the scaffold,
where it is recorded in `apps/api/docs/dependencies.md`. **Read that file for the real commands rather than
assuming a stack**, and if it does not name them, that is the finding: say so instead of guessing.

Two checks that are decided and are not lint: `lint-imports`, which enforces the package tier order of
ADR-0002 section 5, and the missing-migration check.

## Generated artifacts are never hand-edited

If a generated file is among the modified paths, **regenerate it and fix its source instead**: the OpenAPI
schema comes from the DRF layer, and the web's TypeScript types come from the committed schema snapshot
(ADR-0002 section 10). Hand-editing either produces a green local run and a red CI, which is the worst of
both.

The same rule covers migrations: they are generated with `makemigrations` and never hand-authored, except
for deliberate data migrations and trigger installations, which are reviewed like code (ADR-0002 section 9).
