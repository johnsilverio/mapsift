# ADR-0001: Architecture baseline for the scaffold

- **Status:** accepted (2026-07-30)
- **Deciders:** the owner, with the planning window
- **Authority:** derives from `specs/mapsift-foundation.md` v0.11.1 (sections 9.5, 9.6, 10, 14) and `specs/PRD.md` v0.8. Where this ADR and the foundation disagree, the foundation wins and this ADR is the one that is wrong.
- **Supersedes:** nothing. **Superseded by:** nothing.

---

## ADR conventions (stated here because this is the first one)

ADRs live in `specs/adr/`, numbered `NNNN-kebab-title.md` starting at 0001, in Context / Decision / Consequences form. **The set reads as the current truth: when a decision changes or grows, its ADR is edited in place, and every such change carries a short dated note saying what changed and why**, so a reader who opens one document gets the live decision with its history beside it, while git carries the full prior text. A new numbered ADR is opened for a new decision area, never for revising an existing one, and a change is never quiet: an edit without its dated note is the drift the fan-out exists to prevent. An ADR records **code shape**; the *what* and the *why* live in the foundation, the *how* one layer above code lives in the PRD.

> **Changed (2026-08-05, owner decision, the MAP-27 round).** The original convention was supersede-not-edit, for the reasoning chain's sake. Reversed because a reader who opens a superseded ADR first and not its successor walks away with a wrong architecture: the chain served the writer where the set must serve the reader, and git history carries the chain either way.

---

## Context

The PRD's prose is complete (four layers, the non-functional block, the design system), and the next phase is architecture. Two risk spikes are open and deliberately not waited on: **OQ-10** (Postgres-ordered sync) and **OQ-1** (shared topology). The scaffold cannot wait for them, and it does not need to: everything the scaffold requires is already settled in the foundation, and nothing in this ADR depends on either spike's outcome. That is the point of writing this one first.

This ADR exists to answer one question with no ambiguity: **what does a developer create on disk, and what must never be created yet.** The foundation already forbids scaffolding a future that is not decided (the premature `apps/sync` and `apps/desktop` folders that were created once and removed), so the absence list below is as binding as the presence list.

Concrete versions are not asserted here. The external-dependency rule requires the current documentation to be read before a version is chosen, and the canonical place for pinned versions and per-dependency particularities is `specs/dependencies.md`, which was written after this ADR and is now the place to check (a correction under this ADR's own patch rule: it does not alter the decision). This ADR names the technologies the foundation ratified and stops there.

---

## Decision

### 1. Repository layout, organised by unit of deploy

```
apps/          deployables, one folder per shipped service
  api/         the single Django backend
  web/         the Angular web client
libs/          shared code, never deployed alone
  core/        the Rust client logic core (WASM for web and desktop, FFI for mobile)
  ui/          the Angular component library, published internally as @mapsift/ui
infra/         third-party services as compose units, plus deploy configuration
specs/         the foundation, the PRD, the ADRs, and the reference documents
justfile       top-level orchestration across the ecosystems
```

`apps/` is code we write. `infra/` is what we only configure. The load-bearing rule: **nothing in `apps/` imports from another `apps/`; everything shared crosses through `libs/`.** A service is extracted to its own repository by cutting one folder, never by untangling cross-service imports.

### 2. Language roles, one per place, no overlap

Rust in `libs/core` (the client logic core: operation queue, optimistic apply, optimistic conflict detection, client geometry). Python in `apps/api` (the one backend: CRUD, auth, tenant, background jobs, ordering, and the authoritative conflict rule). TypeScript in `apps/web` and `libs/ui` (the web and desktop UI). Dart in `apps/mobile` when it exists (the Flutter UI). Each ecosystem uses its own native tooling: Cargo for Rust; a Python packaging and lock tool with mypy `--strict`, django-stubs, ruff, and pytest; the Angular workspace with ng-packagr for the library; the Flutter SDK later. **No single monorepo tool spans them**; the `justfile` plus compose orchestrate across.

**No Rust runs on the server.** The conflict rule is one specification implemented twice (the Rust core and the Python server) and kept identical by golden tests in CI (foundation 9.6.6, PRD T4.1, M12). A generator must never be pointed at that duplication to "fix" it.

### 3. Containerised from the first commit

**Every service runs in a container from day one, in development as well as in deployment**, and the whole system comes up with one command. Third-party services (PostgreSQL with PostGIS, Redis, object storage, the tile servers when they arrive) are compose services under `infra/` and are never `apps/`. The application services (`api`, `web`, and the `core` build) are containerised too, so a fresh machine, a teammate's machine, a VM, and CI all run the same thing.

- **Development** uses a compose file with source bind-mounted for hot reload, and **named volumes for dependency and build artifacts** (Python virtualenv or site-packages, `node_modules`, the Cargo registry and `target`), so a container rebuild does not re-download the world and a host directory does not fight the container's file layout.
- **`libs/core` builds in its own stage or container**, producing the WASM artifact that `apps/web` consumes, so building the web client never requires a Rust toolchain on the host.
- **Deployment** uses a separate compose file, and the difference between it and development is configuration and build target, never a different architecture.
- Compose files stay to the OCI-standard surface so a Podman-based host can run them without a rewrite.
- The native toolchains are still installed on the developer machine for editor tooling (language servers, formatters, type checking in the editor). The container is the source of truth for **running**; the host toolchain exists for **authoring**.

*Rationale (the owner's, recorded as such):* reproduction across environments is the point. A dockerised project moves to a VM, to a new machine, or to a new developer without an environment archaeology session, and the parity between development and deployment removes the class of bug that only appears in one of them.

### 4. Configuration and secrets

Configuration comes from the environment, never from a checked-in file with real values. Every environment has its own configuration, and **no production credential or production data exists in any non-production environment** (foundation I7, PRD N3), which is checked rather than promised. Secrets never enter the repository and never enter a client bundle. This is set up at scaffold time, not retrofitted, because a repository that starts with a committed secret carries it in its history forever.

### 5. Contracts are generated, and the wiring exists at scaffold

Two generation directions are wired from the start, even while their outputs are nearly empty: the API's OpenAPI schema generates the TypeScript types the web client consumes, and the Rust core's types generate the TypeScript (later Dart) types the clients consume across the boundary (PRD M12). Generated output is committed or built reproducibly, and **CI regenerates and fails on any difference**, so a stale contract is a red build rather than a silent drift. No hand-written duplicate of a generated type is allowed.

### 6. The CI gates, present from the first commit

A change is blocked on: `mypy --strict` with django-stubs and `ruff` on Python; `tsc` strict and the linter on TypeScript; the Rust toolchain's own check, clippy, and formatting; the test suites of each ecosystem; and the generated-contract freshness check of section 5. Pre-commit runs the fast subset locally. The gates exist before there is meaningful code in them, because a gate added later is a gate that arrives after the violations.

### 7. Test-first, with tests beside their ecosystem

Each ecosystem holds its own tests in its own idiom (pytest under `apps/api`, the Angular workspace's runner under `apps/web` and `libs/ui`, Cargo tests under `libs/core`), and the cross-runtime golden vectors for the conflict rule live in a shared fixture location consumed by both the Rust and the Python suites (PRD M13). The canonical method document is `specs/testing.md`, which is written before real code exists.

### 8. What is deliberately NOT created, and the gate that unlocks each

- **`apps/sync`**: the collaboration server. Gated on the OQ-10 spike and on the section 4 sync model being specced. The scaffold's Channels usage is transport and presence only; authoritative document state never lives there.
- **`apps/desktop`**: the Tauri shell. Gated on the web client existing and on the separate offline design (OQ-9).
- **`apps/mobile`**: the Flutter UI. Gated on the web client and on the core being real.
- **The sync engine's internals**: gated on the OQ-10 spike, which may still change the version-axis design (the resync cursor is not yet a named axis in PRD M10).
- **The tile server choice, the client store choice, the identifier variant, the geometry encoding, and the editing library**: each is its own ADR and each is gated on `specs/dependencies.md` existing, because the external-dependency rule forbids choosing any of them from memory.

Creating any of these early is not neutral. It invites code to be written against a guess, and the guess then defends itself.

---

## Consequences

**What this buys.** The scaffold can be created today, in parallel with both spikes, with zero risk that a spike outcome invalidates it, because everything above derives from decisions the foundation already closed. Containerisation from the first commit gives reproduction across machines and environments and kills the dev-versus-deploy divergence class of bug. The gates and the generated contracts exist before the code they govern, which is the only ordering in which they are cheap.

**What this costs.** A containerised polyglot development loop has real friction: file watching across bind mounts, dependency volumes that must be rebuilt when a lockfile changes, and a WASM build step between the Rust core and the web client. On Linux the bind-mount cost is low, which is the environment this team develops on, and the named-volume layout above is the mitigation for the rest. The developer also installs the native toolchains for editor tooling, so the machine is not as clean as "only Docker" implies.

**What this forecloses.** Nothing that the foundation left open. This ADR takes no position on sync internals, storage engines, tile serving, identifier format, or wire encodings, all of which are named above as separate ADRs behind the dependency survey.

**What must be revisited, and when.** If the OQ-10 spike changes the shape of the flush endpoint or introduces an ephemeral store (a Client View Record in Redis is one of the three candidate strategies), that is an addition to `infra/` and to `apps/api`, not a change to this baseline. If it ever demanded a separate sync runtime, `apps/sync` appears then, under the rule in section 8, and this ADR is amended with a dated note.
