---
name: angular-tooling
description: Use the Angular CLI effectively in Angular v22 projects. Covers generating code with the schematics that produce the project's naming and file layout, building, testing with the unit-test builder, workspace and library commands, and configuration. Triggers on generating components/services/guards/interceptors, configuring builds, running tests, or setting up the workspace and the @mapsift/ui library.
---

# Angular tooling

Angular CLI for Mapsift's web client (`apps/web`) and component library (`libs/ui`, published internally as
`@mapsift/ui`).

**Version note.** Verified against Angular v22 (the stable line since 2026-06-03) and the toolchain installed
in `tests/prototypes/editor` (`@angular/core` 22.0.3, `@angular/cli` 22). Nothing is pinned yet: `apps/web`
does not exist and `specs/dependencies.md`, the canonical home for versions, is still to be written. When it
exists it wins over this file, and the flags below should be re-confirmed with `ng g <schematic> --help`
against the version actually installed.

## The rule that governs this skill

**Generate, then edit. Never hand-write a framework file.** A model writes from a training snapshot that may
be two majors stale; the schematic writes what the installed version produces. The v22 defaults are the proof:
`OnPush` is now the schematic default, `ChangeDetectionStrategy.Default` is deprecated in favour of `Eager`,
guards and interceptors are functional, standalone is implicit, and the type suffix is gone. Anything typed
from memory reproduces the v19 shape.

## What the schematics actually produce in v22

Read from the installed `@schematics/angular` schemas, not from memory:

| Schematic | Relevant defaults |
| --- | --- |
| component | `type` **unset**, `addTypeToClassName` true, `changeDetection` **`OnPush`**, `inlineTemplate` false, `inlineStyle` false, `skipTests` false, `standalone` true, `style` `css` |
| service | `type` unset, `addTypeToClassName` true, `skipTests` false |
| directive | `type` unset, `addTypeToClassName` true, `skipTests` false, `standalone` true |
| guard, interceptor, resolver | `functional` **true**, `skipTests` false |
| pipe | `standalone` true, `skipTests` false |

So `ng g c features/layers/layer-panel` creates a folder with four files:

```
layer-panel/
  layer-panel.ts        class LayerPanel, standalone, OnPush
  layer-panel.html
  layer-panel.css
  layer-panel.spec.ts
```

Two flags decide naming and are the ones to understand:

- **`--type`** appends a custom type to the file name (`--type=page` gives `layer-panel.page.ts`). It has
  **no default**, which is why the type suffix is gone by default. Mapsift does not pass it.
- **`--add-type-to-class-name`** (default true) appends that same type to the class name, so
  `--type=page` also gives class `LayerPanelPage`. With no `--type`, it changes nothing.

Confirm any generation before running it:

```bash
ng g c features/layers/layer-panel --dry-run
```

## Generating

```bash
ng g c features/<feature>/<name>          # component
ng g s core/<area>/<name>                 # service, providedIn root
ng g d shared/<name>                      # directive
ng g pipe shared/<name>                   # pipe
ng g guard core/auth/<name>               # functional
ng g interceptor core/http/<name>         # functional
ng g resolver features/<feature>/<name>   # functional
ng g interface models/<name>
ng g class models/<name>
```

Never pass `--inline-template` or `--inline-style`: Mapsift keeps the template and stylesheet in their own
files, with a narrow exception for tiny shared primitives spelled out in `.claude/rules/angular.md`.
`--change-detection=OnPush` is redundant in v22 (it is the default) and harmless if passed.
`--skip-tests` exists but the project wants the spec file; if a whole project should skip them, that belongs in
`angular.json` under `schematics`, not in a habit of passing the flag.

## Workspace and library

`apps/web` and `libs/ui` live in one Angular workspace, with the library built by ng-packagr and consumed by
package name (`@mapsift/ui`), never by a relative path into its source.

```bash
ng g library <name>            # a new ng-packagr library under the workspace
ng build <library>             # build the library
ng build web                   # build the app
```

## Serving and building

```bash
ng serve                       # dev server
ng serve --port 4201 --open
ng build                       # development build
ng build --configuration production
ng build -c production --stats-json    # then analyse the bundle
```

The v22 application builder is `@angular/build:application`. **Zoneless is the default since v21**, so a new
project carries no `zone.js` polyfill; do not add one back.

Remember ADR-0001 section 3: the container is the source of truth for running, the host toolchain is for
authoring. Prefer the `justfile` recipes once they exist.

## Testing

```bash
ng test                          # watch in a TTY
ng test --watch=false            # single run, what a gate wants
ng test --watch=false --include=**/layer-panel.spec.ts
ng test --coverage
```

`ng test` runs the `@angular/build:unit-test` builder, whose default runner is **Vitest** (Karma is still
selectable via `runner`). Tests execute in Node with jsdom by default; `--browsers ChromeHeadless` opts into a
real browser. Always go through `ng test`, never the Vitest CLI directly, because only the builder wires the
tsconfig path aliases such as `@mapsift/ui`.

## Linting

```bash
ng lint
ng lint --fix
```

The linter is its own CI gate (ADR-0001 section 6), so a green `ng build` does not cover it.

## Updating

```bash
ng update                                  # what is available
ng update @angular/core @angular/cli       # the framework and the CLI together
```

Angular moved to an annual major cycle with v22. An update is a dependency decision: it walks the
external-dependency rule and lands in `specs/dependencies.md`, never a blind `--force`.

## Adding libraries

```bash
ng add <package>       # when the package ships schematics
npm install <package>  # otherwise
```

A new dependency is never added on the agent's initiative. Surface the need; adoption walks the gate in
`specs/dependencies.md`.

## Caching

The persistent build cache is on by default under `.angular/cache`. Clear it with `rm -rf .angular/cache` when
a build behaves impossibly.

For patterns and deeper configuration, see [references/tooling-patterns.md](references/tooling-patterns.md).
