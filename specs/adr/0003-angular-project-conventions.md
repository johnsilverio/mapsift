# ADR-0003: Angular project conventions beyond layout and generation

- **Status:** accepted (2026-07-30)
- **Deciders:** the owner, with the planning window
- **Authority:** derives from `specs/mapsift-foundation.md` v0.12 (9.6.4, the portability principle) and `specs/PRD.md` v0.9 (U10, N7, N8). The official Angular style guide is cited as an external authority, not restated as a decision.
- **Supersedes:** nothing. **Superseded by:** nothing.

---

## Context

ADR-0002 fixed code layout and generation and stated, as a rule with teeth, that **a rules file may not decide anything its ADR does not say**. An audit then found that `.claude/rules/angular.md` decides considerably more than ADR-0002 covers, and that ADR-0002's own Consequences section named only the Python and Rust rules as unratified. That was wrong: the unratified surface in the Angular rule was larger than either.

The material in that rule splits cleanly in two, and the split is what this ADR exists to draw.

**Restatement of an external authority, which needs no ADR.** Signal inputs and outputs, `inject()` over constructor injection, the `host` object over the decorators, the built-in control flow, standalone by default, `computed()` for derived state, thin lifecycle hooks, member ordering, `protected` for template-only members, handler naming by action. These are the official Angular style guide. Their authority is external and citable; copying them into an ADR would create a second copy that can drift from the source, which is the failure this canon avoids everywhere else. The rule cites the style guide and that is enough.

**Project decisions, which do need an ADR.** A smaller set is Mapsift choosing among things the style guide leaves open, or choosing against a defensible alternative. Those are below.

---

## Decision

### 1. Every feature route is lazy loaded

Feature routes load with `loadComponent` or `loadChildren`; no feature is eagerly bundled into the initial payload. The reason is specific to this product rather than general hygiene: the initial payload already carries a map renderer and a WASM core, and the client is expected to run on a field tablet on a bad connection (PRD S4). An eagerly bundled feature is paid for by the surface with the least budget.

### 2. Signal-based data access is the default, `HttpClient` is the exception

Prefer `httpResource()` and `resource()`; reach for `HttpClient` only for an imperative flow that genuinely needs the observable pipeline. Both are stable since v22.0 (`specs/dependencies.md` section 3). The reason is coherence rather than novelty: the client's state is signals end to end, and mixing two reactive models in one component is how a codebase acquires two mental models for the same thing.

Interceptors are functional. Class-based interceptors are not used.

### 3. One forms API per surface, and the interim rule is explicit

Signal Forms is the default for new work, stable since v22.0. **A single component never mixes Signal Forms and Reactive Forms.** Where an existing surface uses one, it stays on that one until it is migrated whole. This is an interim rule with an expiry: it exists while both APIs are current, and it is superseded when the codebase is uniform.

### 4. UI is imported from the library barrel only

Components come from `@mapsift/ui` by package name, from its public entry point, never by a deep import into its internals and never by a relative path into its source. No second UI library enters the dependency set. This is the enforceable half of PRD U10, restated here because it is a project decision rather than framework guidance.

### 5. The boundary rule that outranks all of the above

None of these conventions may be read as permission to put client logic in the Angular layer. The operation queue, optimistic apply, conflict detection, and client-side geometry live in `libs/core` (C11, foundation 9.6.4). A service in `apps/web` that starts to look like a sync engine is a defect regardless of how idiomatic its Angular is.

---

## Consequences

**What this buys.** The Angular rules file now has an authority behind every line that is not a style-guide restatement, which is what ADR-0002 section 5 requires. The split also documents *why* most of the file needs no ADR, so a future reader does not mistake citation for decision.

**What this costs.** One more artifact to keep aligned with its rules file, and an interim rule (section 3) that must actually be retired rather than becoming permanent by neglect.

**What this forecloses.** Nothing the foundation left open. The Python and Rust rules files remain unratified and are still candidates for their own ADR when they stop restating the canon and start deciding, which is the same sentence ADR-0002 used and it is still true of them.
