# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Market references use codes.** This file and the specs cite other tools in the market by code
(MC-01, MC-02, and so on) rather than by name. The codes are defined in the internal market-research
document `specs/market-reserarch.md`, which is kept out of version control because market research is
internal by nature.

## Project status

Mapsift is **early**: a scaffold exists and runs (four ecosystems building, type checking and testing green,
containerised, with the task runner and the CI gates in place) and **no product capability is built yet**.
`specs/mapsift-foundation.md` is at **v0.17.1** and is the **live source of truth** (the
constitution: the what and the why). `specs/PRD.md` is a living document at **v0.16**, and its **prose is complete**
(Layer 1 the native capability floor with the anti-requirements and the extension catalog, Layer 2 the transversal
system behaviors T1 to T9, Layer 3 the data model and contracts M1 to M16, Layer 4 the surfaces and platform
S1 to S10, section 8 the non-functional requirements N1 to N12, and section 9 the design system U1 to U12; PRD
section 10 is the gap list of what is left, which is decisions, artifacts, and measurements rather than text):
it is the *how* (one layer above code), derives from the
foundation, and must not contradict it. Nine PRD rules that bind implementation and that an agent gets wrong on
its own: geometry is stored and interchanged in SIRGAS 2000 (EPSG:4674) with the source CRS recorded, and a metric
is never computed in degrees and never in one hard-coded frame, because **the metric frame is chosen by the
metric's purpose** (geodesic on the ellipsoid for generic and preview figures, the Sistema Geodesico Local for a
certified rural parcel per MTGIR 2nd edition items 1.4.6 and 3.8.3, an equal-area conic for the CAR and environmental chain,
and UTM never as the authoritative frame for a legal area) (PRD M5); a layer's storage class (element or served)
decides whether its features enter the operation queue at all (PRD M2); **every operation addresses exactly one
target path**, and a geometry operation carries the whole geometry rather than a vertex delta, because the conflict
unit is the target path and preserve-not-discard needs both whole versions (PRD M9); the operation log is
append-only, with a legal-weight feature's current geometry reproducible by replaying its attributed chain
(PRD M15); a captured vertex carries its capture method and precision estimate, so geometry captured by a
device's built-in positioning is never presentable as meeting the certification-grade accuracy the norm requires
(PRD S5); and the **three performance budgets are distinct and must never be conflated** (the I6 per-tile render
budget on the served path, the editable working-set budget on the element path, the element budget at
classification), each recorded with its device, versions, fixture, and date (PRD N1); and **the design system is a
token system**, so no component carries a raw colour, radius, or size, there is one glass material used by every
translucent surface (differing only in alpha), and the chrome is built from `@mapsift/ui` by package name with no
bespoke re-implementation of a library primitive (PRD U1, U2, U10); **every rule that comes from a regime is data
in a versioned, dated jurisdiction package and never a literal in a function** (which feature types carry legal
weight, a width or threshold fixed in law, what a deliverable must contain and how it is attested, and the
retention policy), so a regulatory value hard-coded in an engine is a defect the same way a raw colour in a
component is (foundation section 9, PRD M16); and **legal weight follows the nature of the feature, never the
state of an external registry**, so a registry status is recorded and displayed as provenance and never raises or
lowers the protection, and protection is never removed retroactively (PRD M7). For interface work the editor prototype in
`tests/prototypes/` is a **permitted visual reference and nothing else**: open it to see what the result must look
like, then **recreate by refactoring under the PRD section 9 rules, never copy a file, a class, or a structure**,
and never inherit its architecture, state handling, persistence, or identity shortcuts. The non-negotiable constraints below are derived from the foundation;
the PRD and the ADRs (code shape) derive from it too. When this file or the PRD disagrees with the
foundation, the foundation wins. Do not
invent constraints, do not scaffold against guessed decisions, and do not create tracking issues that do not
trace to the foundation. When building starts, it is test-first via the two-window protocol, toward the
interface the foundation and PRD describe.

Mapsift is a **closed-scope, non-MVP product** built point by point to completion. Release versioning,
delivery order, and roadmap are out of scope for the foundation (and for this file); do not use "ship it
sooner" as an architectural argument.

Mapsift is a **multi-platform platform** (web, desktop via Tauri, mobile via Flutter and tablet-first for the
field), not a single web app. Stack (ratified by the foundation): a **monorepo** with a **Django 5** backend
(Channels, django-ninja, Pydantic, a background job queue), an **Angular** web and desktop UI (TypeScript
strict, MapLibre GL JS), a **Flutter** mobile UI (Dart), and a **shared Rust logic core** (`libs/core`)
compiled to WASM (web, desktop) and to a native FFI library (mobile) and running on the clients only, on
**PostgreSQL 18 + PostGIS** and **Redis**, with **Celery** as the background job queue. The collaboration model
is **server-authoritative with offline support** (Figma shape), not local-first with CRDTs.

## What Mapsift is

A **collaborative, multi-platform GIS for environmental analysis**: a web app, a desktop app (Tauri), and a
mobile app (Flutter, tablet-first for field work), with the UI rewritten per platform on top of one shared
Rust logic core (`libs/core`). The collaboration model is **server-authoritative with offline support**: the
server (PostgreSQL) is the source of truth and defines the order of operations; each client keeps a working
copy and a persistent local operation queue so work continues when the network drops, and syncs on reconnect.
Offline is a fully usable degraded mode, not the resting state. The technical depth is general-purpose, at the level of desktop GIS like MC-02 in what it covers; the
environmental-analysis workflow (vegetation cover, change detection, preservation areas) is the anchor domain
that guides packaging and the first users, not a ceiling on capability (foundation sections 1.3 and 12). The product philosophy, the plain-language soul that the rest of the foundation is the
engineering consequence of, lives in foundation section 0.5; read it before the constraints.

## The architecture in one diagram

```
clients (UI per platform, each embedding libs/core, the Rust CLIENT core)
  web: Angular UI + core (WASM)                      server (Django, Python; no Rust core)
  desktop: Tauri + Angular UI + core (WASM)            api tier (django-ninja): CRUD, auth, tenant,
  mobile: Flutter UI + core (FFI)                        ordered op-flush, AUTHORITATIVE conflict
    core: op queue, optimistic apply,                     resolution (Python rule, golden-tested
      OPTIMISTIC conflict-detect, geometry                equal to the client core, rule versioned)
        │ flush on reconnect: transactional API ─►    PostgreSQL 18 + PostGIS (truth, ordering,
        └─ WebSocket: presence + change notify ──►      authoritative geometry via GEOS)
  layers: consume MVT tiles ◄────────────────────    sync tier (Channels/WebSocket): transport + presence
                                                      background jobs (Celery): heavy analysis
                                                      tile server (MVT via ST_AsMVT; Martin), TiTiler raster
                                                      object storage (S3 / MinIO)
```

## Repository layout

Monorepo organized by unit of deploy, not by layer.

- `apps/`: deployables, one folder per service shipped. At scaffold: `apps/api`
  (the single Django backend: CRUD, auth, multi-tenant, Celery, ordering, and the
  authoritative conflict resolution in Python, golden-tested against the client core)
  and `apps/web` (Angular, consuming `@mapsift/ui` and `libs/core` via WASM). Later,
  only when the foundation reaches them:
  `apps/mobile` (Flutter, consuming `libs/core` via FFI), `apps/sync` (collaboration
  server, after the section 4 sync model is specced and the geometry spike OQ-1),
  `apps/desktop` (Tauri shell of web, after the web client exists and the separate
  offline design OQ-9).
- `libs/`: shared code, never deployed alone. At scaffold: `libs/core` (the Rust client
  logic core, compiled to WASM for web/desktop and to a native FFI library for mobile;
  the textbook shared lib, used by the web, desktop, and mobile clients, not the server)
  and `libs/ui` (the Angular
  component library, built with ng-packagr to `@mapsift/ui`, for web and desktop). Later:
  `libs/contracts` (types generated from `apps/api`'s OpenAPI schema and from the
  `libs/core` Rust types, the single source of truth for the cross-language contracts).
- `infra/`: docker-compose (dev/prod), nginx, deploy. Third-party services
  (PostgreSQL+PostGIS, Redis, MinIO, Martin, TiTiler) live here as compose services,
  NOT as `apps/`. `apps/` is code we write; `infra/` is what we only configure.
- `specs/`: foundation, PRD, ADRs, dependencies, testing, session-handoff, and
  data-and-tooling-references (the canonical reference for data sources and per-tool
  expected behavior, referenced by the PRD rather than duplicated into it), plus index (the document
  catalog) and log (the grep-able derived version-and-decision index, not a source of truth).
- `justfile`: top-level orchestration (`just dev`, `just test`, `just lint`).

**The rule that keeps a future split cheap: nothing in `apps/` imports from another
`apps/`. Everything shared crosses through `libs/`.** A service is moved to its own
repo by cutting one folder, never by untangling cross-service imports.

Polyglot by design, four languages in clean non-overlapping roles: Rust (`libs/core`,
the shared logic core), Python (`apps/api`, the one backend), TypeScript (`apps/web`,
`libs/ui`, later `apps/desktop`, the Angular UI), Dart (`apps/mobile`, the Flutter UI).
Each ecosystem uses its own native tooling (Cargo for Rust; **uv** for packaging, locking
and the interpreter itself, plus mypy `--strict`, ruff, pytest for Python; the Angular
workspace for TypeScript; the Flutter SDK for Dart); `justfile` plus docker-compose
orchestrate across them. No single monorepo
tool spans them. This is roles in different places, not duplicated backends: one backend
(Django), plus a client-internal core. The conflict-resolution rule is one specification
implemented on both sides (the client's Rust core and the Python server), kept identical
by golden tests; the server holds resolution authority and runs authoritative geometry in
PostGIS, so no Rust runs on the server.

## The one idea everything derives from: server-authoritative with offline

This is the architectural core. Get it wrong and nothing else makes sense.

- **The server is the source of truth.** PostgreSQL holds the canonical state and defines the order of
  operations. The client is not the ultimate truth, so true peer-to-peer or server-less operation is off
  the table.
- **Offline is a fully usable degraded mode.** A user operation on an **element** (draw a polygon, edit an
  attribute, move a vertex) is applied locally and appended to a persistent local operation queue
  (IndexedDB or OPFS, behind a storage interface) so it survives an app restart, and the user sees the
  result immediately. On reconnect the client flushes the queue and the server orders and applies it.
- **Conflicts resolve by granularity, not by session** (foundation section 4): different features or
  different properties never conflict; trivial collisions resolve last-writer-wins; a collision on
  **legal-weight** geometry is detected and both versions are preserved for human resolution, never silently
  discarded.
- "Local-first" is a **sensation Mapsift delivers** (your work continues offline), not an architecture that
  forces the client to be the truth. CRDTs (Yjs) are demoted from the default to a gated candidate
  (foundation OQ-2); shared-topology CRDT remains a research-grade spike (OQ-1).

## Non-negotiable constraints

Derived from the foundation (v0.17.1). Each is load-bearing and pairs with a pass/fail acceptance test (the
Hort C-equivalents). Breaking one is a regression, not a tradeoff. CI and review enforce them.

- **C1, offline write path (foundation I1).** An element edit commits locally (op queue, IndexedDB/OPFS)
  before any network round-trip; within the offline domain limits the app stays functional offline.
  *Test:* with the network disabled, drawing or editing an element persists across an app restart and is
  flushed on reconnect.
- **C2, convergence (I2).** After reconnect, all clients reach the same state; no client diverges
  permanently; the server defines order. *Test:* concurrent edits from two clients, replayed in server
  order, converge to one identical state on both.
- **C3, ID safety (I3).** Client-generated feature IDs never collide; an offline-created feature syncs
  without server pre-allocation. *Test:* features created offline on two clients sync without ID collision.
- **C4, tenant isolation at the SQL layer (I4).** The tenant is the **top container of an account** (a personal
  user account or an organization; foundation v0.11), carried as a tenant identifier on every row; the
  **workspace** and **project** below it are permission and organization, not isolation, and confidentiality
  within a tenant (between its clients or projects) is the permission model's job, not a second SQL wall.
  Isolation is enforced in the database (PostgreSQL row-level security, chosen over per-tenant views in ADR-0005,
  which also fixes the roles, the transaction-scoped binding and the tile path's contract), not only in the ORM,
  so direct-to-PostGIS readers such as the tile server are covered (the tile role must set the tenant on its
  session, never run with RLS bypassed). The single deliberate exception: a user's own `membership` rows are
  readable across tenants for the login question, `FOR SELECT` only (I4 as revised v0.17.1; ADR-0005
  section 8). *Test:* a cross-tenant read or write, including a tile request, is impossible by construction.
- **C5, type safety end to end (I5).** mypy `--strict` with django-stubs on the backend, TypeScript strict
  on the frontend, Pydantic at every boundary; frontend types generated from the OpenAPI schema. *Test:* CI
  blocks on any mypy, ruff, or tsc violation.
- **C6, no production data outside production (I7).** No production credentials or production data in any
  non-production environment, ever. *Test:* environments are checked; none carry production secrets or data.
- **C7, preserve-not-discard for legal-weight geometry (foundation section 4).** A conflict on the geometry
  of a legal-weight feature is detected and both versions are retained for human resolution; silent discard
  is prohibited, and a legal-weight feature never vanishes or resurrects without a record. *Test:* two
  offline geometry edits to the same legal-weight feature produce a flagged conflict with both versions
  retained, never a silent overwrite.
- **C8, additive restore (section 4).** Restoring a version snapshot creates a new current version with that
  content; it never deletes work that came after. *Test:* restoring an older snapshot leaves all later
  versions still retrievable.
- **C9, PostgreSQL is the ordering authority (section 10).** Ordering lives in the database via a
  transactional op-flush with a monotonic per-feature version; Channels carries transport and presence only;
  the sync protocol does not trust at-most-once delivery (it uses versioning, gap detection, resync).
  *Test:* a dropped notification is recovered by gap detection and resync, not lost.
- **C10, conflict-rule equivalence and server authority (foundation I8, section 9.6.6).** The
  conflict-resolution rule has one specification, implemented per runtime (the client Rust core and the Python
  server) and verified identical by golden tests in CI (canonical vectors run against both, divergence fails
  the build, with a defined tolerance where the rule consults a geometric predicate). Resolution authority is
  the server's alone; the client's resolution is an optimistic preview. The rule is versioned in the sync
  protocol so an old client meeting a new server is reconciled, not silently trusted. No Rust runs on the
  server; authoritative geometry is PostGIS. *Test:* the golden vectors resolve identically (within tolerance)
  on both runtimes, and an old-client/new-server case is detected by rule version and reconciled, not lost.
- **C11, portability and serializable boundary (foundation section 9.6.4).** Client logic lives in the shared
  core, isolated from UI and platform behind a boundary that passes only serializable data, never live
  references; the UI is rewritten per platform, the core is not. Client logic must not fuse into the Angular
  or Flutter code, because that closes both the portability and the extensibility doors. *Test:* the core
  compiles to both WASM and a native FFI library from one source, and no UI object or live handle crosses the
  boundary.
- **C12, idempotency and partial-failure recovery (foundation I9, section 4).** Every operation carries a
  per-client monotonic mutation number; the server tracks the per-client last-applied number and ignores any
  operation at or below it (dedup), so a resent flush is idempotent. The server echoes the per-client
  last-applied number in the flush response and the client advances its cursor only from that echo, never by
  assumption. A client here is a persistent instance (a clientID generated and persisted per installation, using
  the I3 client-side identifier mechanism), not the user, so the same user on two devices is two clients with
  non-colliding streams. This is distinct from the per-feature version (which orders and detects conflict).
  *Test:* interrupt a flush after the server applies part of the queue, resend the full queue, and the final
  state is identical with no duplicated feature and no lost edit; the client advances its cursor from the
  echoed last-applied; and two clients of the same user (distinct clientIDs) do not collide and neither loses an
  operation to false dedup.
- **C13, authored and authorized writes (foundation I10, section 9).** Every operation is attributed to an
  author whose authoritative identity is the authenticated session that created it, proved by verifiable
  session material and normalized by the server at flush (not a free client field, and not the flush session's
  identity); the server validates that author's authorization at flush; an unauthorized offline operation is
  flagged, never silently applied or discarded; a divergence between claimed and provable author is normalized
  to the proven identity or rejected and retained for inspection. The authorship of a legal-weight feature is
  the preserved ordered chain of attributed operations (each with its authoritative applied-at), never
  collapsed to a single stamp. *Test:* (1) an author who lost write permission offline is flagged at flush, not
  applied and not dropped; (2) a claimed author diverging from the session-material identity is normalized or
  rejected, never accepted as claimed; (3) a legal-weight feature edited by two authors in distinct sessions
  preserves both chains, inspectable and in order.
- **C14, mediated and gated agent writes (foundation I11, section 9.5.1).** An agent-originated write is the
  user's write through the agent: it carries mediation provenance (user through the identified agent), distinct
  from a direct human write and preserved in the trail; and agent action on a legal-weight feature or on a bulk
  write requires human confirmation before it is applied; all under C13 (I10) and preserve-not-discard. *Test:*
  (1) an agent-originated operation is recorded as user-through-agent, distinguishable from a direct human write
  by the same user; (2) an agent attempting to delete or edit a legal-weight feature triggers human confirmation
  and is never applied directly.

Gated or open, NOT yet firm constraints (do not enforce as settled): **the rule classifying which features carry legal weight (OQ-8), which is the input C7 depends on, so C7 is enforceable as a mechanism while what it applies to is still the environmental engineer's to decide**; extension governance, sandboxing, and capability permissions (OQ-14), under which no third-party code executes at all; the exact per-tile performance budget
(foundation I6, set in the PRD), shared-topology editing (OQ-1, reframed as snapping plus validation plus
PostGIS Topology, propagation online-only), CRDT reconsideration (OQ-2), desktop project-scoped offline
(OQ-9), the Postgres-ordered-sync spike (OQ-10), operation/schema versioning mechanism (OQ-15; its principle is settled in foundation v0.11), the LGPD compliance
posture, now framed multi-regime with the strictest regime served as the design ceiling (OQ-16), offline-store
protection on the device (OQ-17), the offline authorship-proof mechanism
(OQ-18), agent-write governance (OQ-19), legal-weight retention and project deletion, whose retention half is
per-jurisdiction policy rather than one global period (OQ-20), and whether the shipped desktop and mobile builds
carry product obligations the web tier does not, the clock starting on distribution and nothing distributed today
(OQ-21), and the three operational questions opened in v0.16 and deliberately not scheduled: edge caching with a content delivery network and tile invalidation (OQ-22), rate limiting and quota (OQ-23), and horizontal scale-out with what balances in front of it (OQ-24).

**Security and privacy posture (foundation section 9):** data is encrypted in transit (TLS) and at rest for
production data; collection is minimized to what environmental analysis needs; production data never leaves
production (C6); provenance of who edited what is retained. LGPD compliance (legal basis, retention,
data-subject rights, whether a DPO is required) is a legal and product decision opened as foundation OQ-16, not
asserted here. The offline device (the field tablet above all) is a distinct exposure vector from the server,
with its own per-platform protection tradeoff, opened as foundation OQ-17 and not solved here.

## Key behaviors to implement correctly

These come from the foundation; product-specific behavior (supported formats, the exact tool list, sharing
rules) is deferred to the PRD and is NOT pre-decided here.

- **Elements vs layers is the frontier.** Elements (hand-drawn or edited points, lines, polygons,
  annotations, attributes, styling) are the light, live, offline-capable, collaborative surface and live
  behind the op queue. Layers (rasters, imagery, large imported vector, analysis outputs) are heavy,
  server-authoritative, and served as tiles, never loaded whole into the client.
- **Server-authoritative sync, ordered by Postgres, on the per-project version (ADR-0004).** The op-queue flush
  is a transactional django-ninja call ordered by the database. The **resync cursor is the per-project version**,
  the fifth version axis (PRD M10), allocated inside the flush transaction so version order is commit order by
  construction; the per-feature version orders and detects conflict on one feature and is a different axis. Two
  rules are part of that decision and are not optimisations to add later: a flush allocates its **whole range in
  one statement** rather than one per operation, and the allocation is the **last thing before commit**, so
  validation, dedup, contiguity, feature versions and the conflict rule all run outside the critical section.
  Measured, those two cut the worst interactive save fifty-six fold and made the flush four times faster. Channels carries WebSocket transport
  and presence only; the sync protocol uses versioning, gap detection, and resync, and never relies on
  at-most-once delivery. Do NOT put authoritative document state in the Channels tier.
- **Operations are idempotent and authored.** Every queued operation carries a per-client monotonic mutation
  number (the server dedups by per-client last-applied, making resends idempotent, distinct from the
  per-feature version that orders and detects conflict) and an author stamped at creation (authorization is
  validated server-side at flush; an unauthorized offline op is flagged, not silently applied or dropped).
- **Large data: dynamic MVT now, pre-generated tiles gated.** Large vector is served as dynamic MVT from
  PostGIS (ST_AsMVT) via the tile server (Martin), with edits writing straight to PostGIS and HTTP tile
  caching. Pre-generated base tiles plus merge-on-demand (the Lightning shape) are introduced only when a
  measured per-tile bottleneck is crossed, not up front.
- **MapLibre is the renderer, with an editing restriction.** Render volume as MVT tiles on the GPU; keep
  only the small set of elements under live edit in a client-side GeoJSON source (Terra Draw or Geoman). The
  editable working set is capped; a whole layer is never promoted to live editing. Snapping gives shared-edge
  coincidence at draw time; a shared topological structure with edge-move propagation is online-only (PostGIS
  Topology), reframed in OQ-1.
- **One client persistence layer behind a storage interface.** Web uses a single store (IndexedDB or OPFS).
  The sync engine is platform-agnostic (pure functions over the op log); a desktop SQLite adapter, if built,
  sits behind the same interface. One sync engine, never two sync surfaces.
- **Everything is a named capability (foundation section 9.5).** Data operations are expressed as named,
  asynchronous, serializable, invariant-respecting capabilities; the app is the first consumer of its own
  public capability layer. No capability bypasses tenant isolation (C4) or the conflict-resolution model
  (C7), and no live references cross the layer (no live map object or DB connection handed across), so later
  sandboxing stays possible. The app, extensions, the SDK, and the AI agent are all consumers of this one
  layer. For autonomous consumers, every capability carries a **machine-readable structured description** (what
  it does, parameters, preconditions, effects, when to use it, the MCP tool-description-plus-input-schema
  pattern) and returns **composable output** (structured data a next capability can consume, so an agent can
  chain). The AI agent is **online-only** (server-orchestrated; foundation sections 9.5.1 and 5), and its
  writes are mediated and gated (C14).
- **Technical depth comes from the capability layer, not a bloated core (foundation section 9.5, v0.9).**
  Mapsift's general-purpose technical depth (MC-02-level capability in what it covers) is delivered by a
  **closed, finite native kit plus extensibility**, both on the one capability layer, the same way MC-02 gets
  its depth from plugins and toolboxes and MC-04 from a sidecar, not from a fat core. Native-kit membership
  is decided by **frequency and centrality in the real workflow**, never by parity with another tool: a
  capability the professional uses daily is native (buffer, intersect/difference, NDVI, zonal stats); an
  occasional or specialized one is an extension (e.g. Voronoi, kriging). The native kit must be self-sufficient
  for the daily work, never a download for a basic capability (that is MC-03) and never every tool pulled into
  the kit (that is MC-02, and the scope bursts). Because both consume the same layer, the native-versus-extension
  boundary is a movable packaging label, not a rewrite. The PRD owns the closed native-kit list (each analysis
  capability tagged native|extensible with its frequency justification); implementation order is backlog, not
  PRD. Do NOT pre-decide the native-kit list here.
- **Shared Rust logic core, UI per platform (foundation section 9.6).** The client logic core (offline op
  queue, optimistic apply, conflict detection by granularity, client-side geometry) is one Rust library
  (`libs/core`), compiled to WASM for the Angular web and Tauri desktop and to a native FFI library for the
  Flutter mobile UI. It is a client-internal layer, not a backend and not an orchestrator. The UI is rewritten
  per platform; the core is shared. The boundary passes only serializable data, never live references (the
  same boundary as the capability layer), and types are generated from the Rust types (Typeshare-class), the
  way backend types are generated from OpenAPI. Share the logic core, never the UI.
- **One conflict-rule specification, two golden-tested runtimes, server authority.** The conflict-resolution
  rule has a single specification. The clients run it in the Rust core (`libs/core`); the Django server
  implements the same rule in Python. The two are kept identical by golden tests in CI (canonical vectors,
  divergence fails the build, with a defined tolerance where the rule consults a geometric predicate, because
  the client's Rust geometry engine and the server's GEOS-via-PostGIS diverge in floating point on edge cases).
  Resolution authority is the server's alone; the client's resolution is an optimistic preview reconciled on
  sync. The rule is versioned in the protocol so an old client meeting a new server is reconciled, not silently
  trusted. Do NOT run the Rust core on the server (no PyO3) and do NOT decide legal-weight data on the client.
- **Observability and availability are structural where they are free, and deferred where they are a hunch
  (foundation section 10, v0.16; PRD N9 and N12).** Three things bind from the first line of code, because
  none of them can be retrofitted cheaply. **Logs are structured and carry their correlation keys** (operation
  identifier, clientID, tenant, request or task), bound once per request and per background task rather than
  passed by hand, because PRD N9 requires a user's report to be reconstructible end to end and a join cannot
  be added to free text later. **Redaction lives on the logging path**, never in each caller's diligence: no
  geometry payload and no personal data reaches a log. And **liveness and readiness are different probes**,
  liveness touching no dependency (a probe that fails on a slow query restarts a healthy service and turns a
  hiccup into an outage), readiness checking what it needs. Telemetry is emitted vendor-neutral so the backend
  stays swappable; the backend itself, the sampling, the dashboards and the alerting are an ADR whose trigger
  is the first real users, and the **OpenTelemetry Python logs SDK was still in development as of May 2026**,
  so the log path runs through the standard library with trace identifiers injected. Do NOT pick a telemetry
  vendor in application code, and do NOT let a capability fail without both a user-visible signal and a record.
- **Type-safe end to end.** mypy `--strict` with django-stubs on the backend; TypeScript strict on the
  frontend; Pydantic at every boundary (API input, WebSocket messages, config). No function without a
  complete signature. No `Any` without a justifying comment. CI blocks a PR if mypy or ruff fail.
- **Contracts are generated, not hand-written twice.** Frontend TS types are generated from the django-ninja
  OpenAPI schema, the single source of truth for the Python↔TS contract, so the two sides never drift.
- **The ORM is a persistence detail.** Do NOT wrap it in a repository pattern without a concrete, measured
  reason. Use cases and services live outside the views; only genuine external integrations (PostGIS beyond
  the ORM, S3/MinIO, Copernicus/openEO, the tile servers, the sync transport) sit behind narrow interfaces.

## Testing & TDD (the development method)

Mapsift is built **test-first**. A canonical testing spec (`specs/testing.md`, to be created) governs it;
read it before writing any code or test. The essentials:

- **Red, Green, Refactor, always**, in **two clean-context windows**: window A writes the failing tests as
  behavior; window B implements the minimum to green, using those tests as a contract written by another
  pass; design happens in the refactor step, never while a test is red.
- **Test behavior, not implementation.** Assert what Mapsift guarantees (return values, emitted errors,
  persisted state, observable effects), never private shape or internal call order. A test changes only when
  a requirement changes.
- **Testability drives the architecture.** Separate decisions (pure) from effects (I/O). Pure decisions
  carry the bulk of the tests: geometry math, spectral indices, permission/tenant resolution, sync-conflict
  resolution, config merge, geometric validation. Effects sit behind narrow interfaces with a real adapter
  and a test fake. **If a piece of logic can only be tested with the network, a large raster, or a live
  PostGIS, it was factored wrong**, so pull the decision out of the effect.
- **Lean, no bloat.** One behavior per test, one test per behavior. Do not test trivial or generated code,
  third-party libraries, or unbuilt futures.

## Explicit non-goals

The non-goals are about purpose and breadth of domain, not technical depth: within what Mapsift covers, the
depth is general-purpose, at the level of desktop GIS like MC-02. Not a marketing-map or story-map builder
(purpose); does not aim to cover every domain of GIS, such as mining geology or whole-basin hydrological
modeling (breadth), which is the only sense of "not a full desktop-GIS replacement for every workflow";
explicitly not peer-to-peer or server-less (the model is server-authoritative); no promise of offline for heavy
raster or large-vector data on the web tier. The environmental and land domain is the anchor, not a ceiling on
capability, and Mapsift does not target a single national market as its defining constraint. The exact feature
list (roughly near-parity with MC-03 plus what the engineers bring from MC-02 and MC-01) is a PRD concern, not
decided here.

## Stack & toolchain

Monorepo: `apps/api` (the one Django backend), `apps/web` (Angular), `apps/mobile` (Flutter, later), shared
code in `libs/` including `libs/core` (the Rust logic core). Polyglot, four languages in non-overlapping
roles: Rust (shared CLIENT core: op queue, optimistic apply, optimistic conflict detection, client geometry;
compiled to WASM for web/desktop and FFI for mobile; does NOT run on the server), Python (the one backend,
including the authoritative conflict rule, golden-tested equal to the client core), TypeScript (Angular
web/desktop UI), Dart (Flutter mobile UI). Backend: **Python 3.13** (the foundation ratifies a 3.12+ floor and the
survey of 2026-08-01 chose the interpreter inside it, capped by Celery's own supported list), **Django 5.2 LTS**
(inside the ratified Django 5 line, security-supported to 2028-04-30, with one planned migration to 6.2 LTS after it
ships in April 2027) +
Channels (WebSocket transport and presence; PostgreSQL is the ordering authority), django-ninja, Pydantic,
Celery, psycopg 3; **uv** as the packaging and lock tool; mypy `--strict` + django-stubs, ruff (lint + format),
pytest (pytest-django, pytest-asyncio);
pre-commit runs ruff + mypy; CI blocks on either. Versions and the reasoning behind each choice live in
`specs/dependencies.md`, never in memory. Web/desktop UI: Angular, TypeScript strict, MapLibre GL JS,
with a client-side editing library (Terra Draw or Geoman) for geometry editing, RxJS, signals; Tauri for
desktop. Mobile UI: Flutter (Dart) with the official MapLibre binding, consuming `libs/core` via FFI. Core:
Rust (Cargo), with types generated to TypeScript and Dart by a Typeshare-class tool. Data: PostgreSQL 18 +
PostGIS, Redis (the ratified major; the minor always runs current, foundation section 10). Tiles: Martin (MVT via ST_AsMVT), TiTiler (raster), Tippecanoe/PMTiles (gated
pre-generation). Imagery: Copernicus Data Space / openEO. CRDTs (Yjs) are demoted to a gated candidate
(foundation OQ-2), not part of the default stack.

> ### Performance rule (non-negotiable, foundation section 10)
>
> Performance is engineered rather than hoped for, and **the established technique is researched before an
> implementation is settled for**, on the same discipline as the external-dependency rule below. Two classes,
> treated differently. **Structural performance is free at design time and is not optional:** the index the query
> needs, the batch that replaces a loop of round trips, the critical section held for one statement instead of one
> transaction, the payload that crosses a boundary once instead of per item, the query that does not multiply per
> row. Skipping one of those is a defect with a performance symptom, never an exercise of simplicity.
> **Optimisation that adds complexity is bought with a measurement, never a hunch:** a cache, a denormalisation, a
> materialised projection, a second store, each waits for a number. A budget in PRD N1 is a **floor**, the bar below
> which the product is defective, and never a target to stop at. The commercial reason is on the record in the
> foundation: the reference tools in this market are not fast, a professional pays for every wait across a whole
> working day, and an advantage made of hundreds of small decisions is one a competitor cannot answer in one release.

> ### External-dependency rule (non-negotiable)
>
> When in doubt about any external dependency, **research before deciding, never guess from memory**.
> Mapsift leans on fast-moving, particular libraries where stale knowledge is a defect, not a shortcut:
> MapLibre GL JS and its editing libraries (Terra Draw, Geoman), the MapLibre Flutter binding, the Rust client
> core boundary tooling (wasm-bindgen, a Typeshare-class type generator, the Rust FFI bridge for Flutter; note
> the core does not run on the server, so no PyO3), PostGIS Topology, django-ninja, Pydantic v2, Django
> Channels, PostGIS spatial functions, GDAL, Martin, TiTiler,
> Tippecanoe/PMTiles, and the Copernicus/openEO APIs (which also carry a monetary cost in processing units
> that must be modeled before any feature is offered as unlimited). If the CRDT spike (OQ-2) is ever run, Yjs
> and its providers join this list. Before choosing how
> to use one, load its current docs or source into context, confirm the behavior against the version actually
> pinned in the lockfile, prefer the newest stable resolution over an old workaround. If you cannot verify
> it, say so. A dependency survey doc (`specs/dependencies.md`, like Hort's) is the canonical place for
> versions and particularities.

> ### Canon rule (non-negotiable)
>
> The rule above applies to this product's own decisions too, and for the same reason: a canon of this size
> is not recallable, so **on any doubt, open the document and read it, never answer from memory**. Three
> obligations follow, and each closes a failure this project has actually met.
>
> **Never assert about a section you did not open in this window.** Not the foundation's, not the PRD's, not
> an ADR's. `specs/index.md` resolves a citation to the file and the section without reading the document,
> which is what makes opening it cheap; the heavy canon is always opened **by reference, never wholesale**,
> because a window filled with four thousand lines it does not need recalls the ten it does need worse.
> Reading everything and absorbing nothing is worse than reading the obligatory set and citing the rest,
> because it looks like coverage.
>
> **A contradiction between two documents is a defect, not a matter of style.** Stop and report it rather
> than choosing one in silence or reconciling it in code. The **foundation wins**, the derived document is
> the one that is wrong, and the correction is a dated revision whose fan-out is finished before the
> decision counts as closed. This is how every contradiction this canon has carried was found, and more than
> once it was found in a document written the same day.
>
> **State what you read and what you did not.** A window that lists the documents it opened makes its own
> blind spots reviewable, so a reader can judge whether a decision rested on something nobody opened. An
> answer that does not say which of the two it is invites being trusted for the wrong reason.

## Comments: a trap earns one, an explanation does not

Code is self-explanatory through naming, and this repository has a stronger reason than usual to keep
comments scarce: it carries a full authority chain (foundation, PRD, ADRs, `dependencies.md`, `log.md`) with
a fan-out rule whose whole purpose is to stop a decision existing as two copies that drift. **Reasoning
copied into a comment is exactly that second copy, and it is outside the fan-out**, so it ages against the
foundation with nobody noticing.

- **An inline comment earns its place only as a trap:** the correct code looks wrong, or the wrong code looks
  right, and without the note someone "fixes" it and reintroduces the defect. The worked example is
  `geodesic_area_unsigned`, whose obvious-looking name returns the rest of the planet for a reversed ring.
  Anchor it to the line it protects, three lines at most.
- **Documentation is a different thing and is wanted:** a docstring, rustdoc or TSDoc on a public API, one to
  three lines, saying what the thing guarantees. The product may be opened one day and the public surface has
  to read on its own.
- **Never restate the canon.** Cite the decision by its identifier (M5, C11, ADR-0004) and let the document
  hold the reasoning, the same way `specs/testing.md` section 6 already has a test name its requirement ID.
- **An explanation of what the code does is a naming failure**, so fix the name instead.

## Process & tracking

Authority chain: `specs/mapsift-foundation.md` (constitution, v0.17.1, the what and the why) → `specs/PRD.md`
(the how, one layer above code) and this file (the constraints-and-behaviors digest), both derived from the
foundation → ADRs (code-shape) → spec-per-task in git (what the agent reads to implement, shaped by
`specs/tasks/README.md`). **The loop from a decision in the canon to a merged pull request is ratified in
ADR-0008**, and the two skills below are its enforceable restatement rather than a second decision.

**git owns the contract; Linear owns execution state; the task ID bridges them.** The procedure for working
with Linear (the git↔Linear boundary, when an issue may be created and what one issue is, the status
lifecycle with the two-window protocol inside it, the definition of done, priority meanings, how more than
one person works in parallel, the project and milestone lifecycle, and the local-scope MCP isolation) lives
in the **`linear-workflow` skill**, not here. Everything from the branch onward (branch name, the pre-commit
gate, commit format, the PR flow) is the **`dev-workflow` skill**, and the two do not restate each other.

**The two-window protocol has a third window over it, and the protocol is `specs/testing.md` section 1.**
Window A writes the failing tests as behaviour (the `test` skill), Window B implements the minimum to green
without editing them (the `implement` skill), and an **orchestrator** opens the task, sizes the slice, closes
the boundary decisions with the owner before dispatching, writes each brief **only after reviewing what the
previous window returned**, and reviews by **running** the gates rather than by reading a report (the
`orchestrate` and `code-review` skills). The orchestrator does not implement and does not touch code: the
moment it edits what a window produced, it stops being the independent check the protocol exists to buy.
Section 1.1 is the contract every window brief satisfies and 1.2 is why sizing the slice is a step rather
than an afterthought.

**The method is XP-shaped with three practices deliberately replaced, and the replacements are not
shortcuts.** The **planning game** is replaced by the closed canon, since scope is decided in the foundation
and the PRD before it reaches a tracker. **Pair programming** is replaced by the **two-window protocol**,
which buys the same independent-check property. **The on-site customer** is the embedded domain engineer,
whose open questions are marked in the canon rather than guessed at. Story points, velocity, iteration
commitments and burndown are dropped, because all four forecast a scope that is still being negotiated and
this one is closed. An issue is **Done** only when the behaviour is proven by tests written first, `just
check` is green, the PR is merged through the normal flow, any ADR it owed exists, and any decision it closed
has finished its fan-out.

## Commands

Everything runs in a container (ADR-0001 section 3): the container is the source of truth for **running**,
the host toolchain is for **authoring**. The `justfile` at the root is the entry point, and it is not
optional ceremony, because each recipe passes `--env-file infra/.env`, which compose does not find on its
own from the repository root. `just` is a host requirement (`dnf install just` on Fedora).

| Recipe | What it does |
|---|---|
| `just setup` | create `infra/.env` and `apps/api/.env` from their tracked templates |
| `just dev` | build the wasm core and the component library, then bring the whole stack up |
| `just check` | the full gate set: `lint`, `typecheck`, `test`, `contracts` |
| `just manage <cmd>` | a Django management command; `just migrate` and `just psql` are shortcuts |
| `just build` / `just reset` | rebuild the images / drop the volumes, the database included |

The raw commands the recipes wrap, which is what CI runs inside the same images: `ruff check .`,
`ruff format --check .`, `mypy --strict .` and `pytest` in `apps/api`; `cargo fmt --check`,
`cargo clippy --locked --all-targets -- -D warnings`, `cargo test --locked` and
`wasm-pack build --target web --out-dir pkg` in `libs/core`; `ng lint`, `ng build ui`, `ng build web` and
`ng test --watch=false` in the Angular workspace. **The build order is a requirement rather than a
convention:** `apps/web` resolves `@mapsift/core` to `libs/core/pkg` and `@mapsift/ui` to `dist/libs/ui`, so
neither a web build nor a web test starts before wasm-pack and ng-packagr have run.
