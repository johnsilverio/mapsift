---
paths:
  - "libs/core/**/*.rs"
  - "libs/core/**/Cargo.toml"
---

# Rust core checklist (`libs/core`)

Actionable per-path rules for the shared client logic core. Grounded in the foundation section 9.6 and
PRD M8 to M15. This is the layer with the least code and the most canon, so read the rule before writing.

**What this crate is.** One Rust library compiled to two targets from one source: WASM for the Angular web
client and the Tauri desktop shell, and a native FFI library for the Flutter mobile UI. It holds the offline
operation queue, optimistic apply, optimistic conflict detection, and client-side geometry.

**What this crate is not.** It is not a backend, not an orchestrator between the UI and the API, and it
**never runs on the server**. There is no PyO3 (foundation 9.6.6, revised v0.6). Authoritative geometry runs
in PostGIS; authoritative conflict resolution runs in the Python server. What happens here is a preview.

**Version note.** Nothing is pinned. The boundary tooling (wasm-bindgen, the Typeshare-class generator, the
Flutter FFI bridge) is fast-moving and each choice walks the external-dependency gate into
`specs/dependencies.md`, the dependency survey, which now exists and is the place to check. Do not pick one from memory.

## Generate with the toolchain, then edit

`cargo new`, `cargo add`, `cargo generate` where a template applies. Never hand-write a `Cargo.toml` stanza
from memory; `cargo add` writes what the registry actually resolves.

## The boundary (C11, M11)

- DO pass **serializable data only** across the boundary, in both directions. No live reference ever crosses:
  no map object, no database handle, no callback into a live object.
- DO use **one declared geometry encoding**, the same for WASM and for FFI, so no platform gets its own
  dialect.
- DO pass **identifiers and deltas by default**. Whole geometry crosses only where the consumer must render
  or edit it, because the crossing is this architecture's known bottleneck (foundation 9.6.2). A continuous
  vertex drag must not cross once per vertex.
- DON'T let bytes cross. An image or a raster is a reference plus metadata (M6); the platform layer fetches
  the payload.
- DON'T hand-write a type that also exists on the other side. Types cross by generation from the Rust types,
  the same discipline the backend uses with OpenAPI (M12).
- MapLibre consumes GeoJSON at the very edge, so that conversion belongs to the UI adapter, never to the core
  contract. Do not let the renderer's format leak into the portable layer.

## The conflict rule (C10, M13)

- The rule is a **pure function over a declared contract**: input is the target path, the authoritative state
  with its per-feature version, the incoming operation, the concurrent state or operation, and the
  legal-weight classification in force; output is a verdict from a closed set (apply, last-writer-wins with a
  named winner, flag and preserve both).
- Keep it small and deterministic. It exists twice on purpose, here and in Python, and golden vectors in CI
  prove they agree. That duplication is deliberate and is never "fixed" by generating it.
- Where the rule consults a geometric predicate, the tolerance is declared **in metres, never in degrees**,
  and inside the tolerance band a legal-weight verdict falls to **flag and preserve**. A doubt resolves
  toward keeping both versions.
- This core's resolution is an **optimistic preview**. Never finalize a legal-weight decision here.

## The operation queue (C1, C3, C12, M8, M9, M10)

- Every operation addresses **exactly one target path** (tenant, project, layer, feature, property). The
  conflict unit is the target path, and the granularity ladder is undecidable without it.
- A geometry operation carries the **whole geometry**, never a vertex delta, because preserve-not-discard
  needs both whole versions presentable.
- Identifiers are client-generated, globally unique with no coordination, opaque, stable, and never reused.
  No code path derives meaning, order or authority from an identifier's content.
- Every operation carries a per-client monotonic and **contiguous** mutation number. The cursor advances only
  from the server's echoed last-applied, never by assumption.
- The queue is append-only and persistent; the sync engine is pure functions over the operation log, with the
  store behind one narrow storage interface. One sync engine, never two sync surfaces.

## Rust hygiene

- DO model errors with `Result`. No `unwrap()` or `panic!` on a recoverable path, and no silent failure: this
  product's moral line is that nothing fails without a record.
- DON'T use `unsafe` without a documented, reviewed reason (the FFI edge is the only expected place).
- DO keep `cargo clippy` and `cargo fmt --check` clean; CI blocks on both (ADR-0001 section 6).
- DO keep the crate free of platform assumptions. If something needs the browser or the OS, it belongs in the
  UI adapter, not here.

## Tests

- Cargo tests live under `libs/core` (ADR-0001 section 7).
- The conflict rule's golden vectors are shared fixtures consumed by both this suite and the Python suite; a
  divergence fails the build.
- Pure decisions carry the bulk of the tests. If a piece of logic here needs the network or a live database
  to test, it was factored wrong.
