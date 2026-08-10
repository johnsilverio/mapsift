---
paths:
  - "apps/web/**/*.ts"
  - "apps/web/**/*.html"
  - "libs/ui/**/*.ts"
  - "libs/ui/**/*.html"
---

# Angular checklist (Mapsift web client)

Actionable per-path rules for `apps/web` (the Angular SPA) and `libs/ui` (`@mapsift/ui`). Grounded in the
official Angular style guide (angular.dev/style-guide), the design system in PRD section 9 (U1 to U12), and
this repo's `CLAUDE.md`.

**Version note.** Verified against Angular v22 (the stable line since 2026-06-03) and the toolchain installed
in `tests/prototypes/editor` (`@angular/core` 22.0.3, `@angular/cli` 22). **`apps/web` and
`specs/dependencies.md` both exist now, and both outrank this file:** the survey is the canonical home for a
version claim and `package-lock.json` is what pins one. This note records what the rule below was verified
against, never what is installed.

## Generate with the CLI, then edit (non-negotiable)

Every framework-owned file is created by the Angular CLI and then edited. Never hand-write a component,
service, directive, pipe, guard, interceptor, resolver, or library from memory.

```bash
ng g c features/<feature>/<name>      # component (folder + ts + html + css + spec)
ng g s core/<area>/<name>             # service
ng g d shared/<name>                  # directive
ng g guard core/auth/<name>           # functional by default
ng g interceptor core/http/<name>     # functional by default
ng g library <name>                   # ng-packagr library under libs/
```

The reason, so this is not read as ceremony: a model writes from a training snapshot that may be two majors
stale, while the schematic writes what the installed version actually produces. The v22 defaults prove it.
`changeDetection` is already `OnPush`, `ChangeDetectionStrategy.Default` is deprecated in favour of `Eager`,
guards and interceptors are functional, `standalone` is true, and the type suffix is gone. Anything written
from memory reproduces the v19 shape. This is the external-dependency rule of `CLAUDE.md` applied to the
framework itself: confirm the behaviour against the version actually installed, never against memory.

The only exception is a file no schematic produces (a pure function module, a fixture), and even there
`ng g interface` and `ng g class` exist. Verification: the diff of a new component matches what
`ng g c <same-name> --dry-run` prints.

## Component file layout

- DO keep the CLI default: one folder per component holding `<name>.ts`, `<name>.html`, `<name>.css`, and
  `<name>.spec.ts`. Never pass `--inline-template` or `--inline-style`, and never move a template into the
  decorator afterwards.
- The single exception is a shared primitive whose template is **at most 5 lines of markup AND has no control
  flow (`@if`, `@for`, `@switch`) AND no bindings beyond content projection and host bindings**. The typical
  case is a `libs/ui` primitive that renders `<ng-content />` and nothing else. If any of the three conditions
  fails, the template goes in its own file, whatever its length.
- DO keep one component per folder. A folder holding two components is two folders.

## Folder organization

- DO organize `apps/web/src/app` by feature: `core/` (singleton infra, no UI), `features/<feature>/` (lazy
  route with its own components inside), `shared/` (app UI built on top of the library). DON'T group by type
  (`components/`, `services/`).
- DO split a folder that exceeds **8 direct children** into subfolders by sub-feature. This is a countable
  trigger on purpose: "it feels big" is not a rule and it never fires.
- DO name files with hyphens, one concept per file. DON'T create `utils.ts` / `helpers.ts` / `common.ts`
  grab-bags.

## Components

- DON'T write `changeDetection` at all. OnPush is the v22 default and the schematic **omits both the property
  and the `ChangeDetectionStrategy` import** when the strategy is OnPush, exactly as it omits `standalone: true`.
  Adding either by hand makes the component diverge from `ng g c <same-name> --dry-run`, which is the
  verification rule of ADR-0002. The only prohibited deviation is writing `Eager` explicitly.
- DO rely on standalone by default. DON'T write `standalone: true`.
- DO use `input()` / `input.required()` / `output()`, marked `readonly`. DON'T use `@Input()` / `@Output()`.
- DO use the `host: {}` object. DON'T use `@HostBinding` / `@HostListener`.
- DO use `inject()`. DON'T use constructor injection.
- DO hold state in `signal()` / `computed()` / `linkedSignal()`; replace arrays/objects by reference
  (`[...arr, x]`). DON'T mutate in place (`arr.push`).
- DO put Angular properties (injected deps, inputs, outputs, queries) at the top, before methods.
- DO mark template-only members `protected`. DON'T expose them as `public` needlessly.
- DO name event handlers for the action (`saveLayer()`). DON'T name them for the trigger (`handleClick()`).
- DO keep lifecycle hooks thin and implement their interfaces. DON'T inline complex logic in them.

## Client logic belongs in the core, not the component

- DO keep the offline op queue, optimistic apply, conflict detection, and client-side geometry in `libs/core`
  (Rust to WASM). The Angular layer calls the core; it does not reimplement client logic (C11).
- DON'T fuse domain/sync/geometry logic into components or services, it closes the portability and
  extensibility doors.
- DO render volume as MVT tiles; keep only the capped live-edit set in a client-side GeoJSON source (T3.6,
  M14). DON'T load a whole layer into an editing source.
- DON'T let a live MapLibre handle cross a capability or core boundary (M11, U11); the map components own the
  instance internally and expose serializable state outward.

## Templates

- DO use `@if` / `@for` / `@switch`; every `@for` needs `track`. DON'T use `*ngIf` / `*ngFor` / `*ngSwitch`.
- DO use `[class.x]` / `[style.x]`. DON'T use `ngClass` / `ngStyle`.
- DO use self-closing tags for elementless components (`<app-foo />`).
- DO move non-trivial expressions into `computed()`. DON'T put complex logic in templates.
- DO use `NgOptimizedImage` (`ngSrc` + `width`/`height`) for static images.

## Naming and types

- DO drop the type suffix: file `layer-panel.ts`, class `LayerPanel`. This is what `ng g c` already produces,
  because the component schematic's `--type` has no default. DON'T write `*.component.ts` / `*.service.ts`,
  and DON'T pass `--type` to reintroduce a suffix. (`@mapsift/ui` may keep its own library naming convention.)
- DO keep `strict` types; use `unknown` when genuinely uncertain. DON'T use `any`, `@ts-ignore`, or
  `as unknown as T`.

## Imports, routing, data, styling

- DO import UI from the `@mapsift/ui` barrel only, by package name. DON'T deep-import into its source, DON'T
  re-implement a primitive the library already provides, and DON'T add another UI library (U10).
- DO lazy load every feature route via `loadComponent` / `loadChildren`.
- DO prefer `httpResource()` / `resource()` (both stable since v22.0); use `HttpClient` only for imperative
  RxJS flows. DON'T use class-based interceptors (functional only) or hardcode API URLs (read them from the
  environment config).
- DO generate API types from the backend OpenAPI schema and core types from the Rust types; consume the
  generated types. DON'T hand-write a request/response type that can drift from the contract (C5, M12).
- DO take every visual value from a design token (U1). DON'T write a raw colour, radius, size, or spacing
  literal in a component, and DON'T give an inset surface a backdrop filter (U2).
- DO name interactive states semantically (hover, active, selected, disabled, focus, danger). DON'T encode a
  colour value in a class or token name (U9).
- Forms: Signal Forms (`@angular/forms/signals`) are stable since v22.0, and Reactive Forms remain supported.
  Which one Mapsift standardizes on is an ADR gated on `specs/dependencies.md`; until it is decided, do not
  mix the two ad hoc in the same surface.

For depth and rationale see the root `CLAUDE.md`, the foundation `specs/mapsift-foundation.md`, PRD section 9,
and the `angular-component` and `angular-tooling` skills.
