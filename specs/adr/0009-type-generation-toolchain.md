# ADR-0009: The type-generation toolchain for the envelope contract

- **Status:** accepted (2026-08-05)
- **Deciders:** the owner, on the MAP-31 research round (three verification passes against primary sources, 2026-08-05)
- **Authority:** derives from `specs/mapsift-foundation.md` v0.17.1 (sections 9.6.2, 9.6.6, 10) and `specs/PRD.md` v0.16 (M8, M11, M12). Where this ADR and the foundation disagree, the foundation wins and this ADR is the one that is wrong.
- **Supersedes:** nothing. **Superseded by:** nothing.
- **Delivers:** the Rust-to-Python and Rust-to-TypeScript halves of `specs/dependencies.md` agenda item 7; unblocks MAP-7 (the operation envelope, PRD M8).

---

## Context

M8 requires the envelope to have exactly one definition in the repository, with every language reading a generated form of it, and M12 fixes the core contract's source of truth as the Rust types. The flush path makes Python a reader of that contract, a direction agenda item 7 never named: the survey had narrowed the open half to Rust-to-Dart on the assumption that the TypeScript side falls out of wasm-bindgen. The MAP-31 research round (2026-08-05, primary sources, versions and particularities registered in `specs/dependencies.md` section 2) refuted that assumption and one more: a serde-serialized value crosses wasm-bindgen as `any`, and Specta's Python and JSON Schema exporters are 0.0.x stubs rather than tools.

The alternative space is empty rather than close. A hand-written Pydantic mirror fails M8's one-definition acceptance by construction; serde-generate emits plain dataclasses aimed at binary formats and struggles with the opaque `serde_json::Value` field the envelope carries; Specta fails on its own README. What was genuinely open was which tools carry each direction and where the freshness gates live.

---

## Decision

### 1. The source of truth is the Rust definition in `libs/core`

Per M12. The envelope types are plain serde structs and enums with no wasm-specific types, so every generator below consumes the same source.

### 2. Rust to Python: schemars to JSON Schema 2020-12, then datamodel-code-generator to Pydantic v2

The Rust side emits the schema with **schemars**, pinned explicitly to the 2020-12 dialect (`SchemaSettings::draft2020_12()`), because schemars documents that its default dialect is liable to change. The schema artifact is committed. The Python side generates the Pydantic v2 model in `apps/api` with **datamodel-code-generator** (`--output-model-type pydantic_v2.BaseModel`, `--disable-timestamp`, `--use-annotated`, `--use-union-operator`, `--target-python-version 3.13`, formatters passed explicitly), and **the CI freshness gate is the tool's native `--check`**, which exits non-zero with a diff when the committed model is stale (ADR-0001 section 5's gate, concretized). The generator version, the formatter set and the target Python version are pinned together and bumped deliberately; the diff gate absorbs any output change as a reviewed commit rather than silent drift.

> **Changed (2026-08-06, closing the MAP-7 implementation review).** `--use-title-as-name` joins the enumerated flag set, paired with a `title` per `TargetPath` variant on the Rust side, so the generated union members carry readable names (`TenantTarget` through `PropertyTarget`) instead of `TargetPath1..5`, which would otherwise leak into the conflict-rule code that discriminates on them.

### 3. Rust to TypeScript: tsify into the wasm-pack pkg, with a recorded exit path

**tsify** (the original crate; the tsify-next fork was retired back into it) with its `js` feature emits the named interfaces and discriminated unions into the `.d.ts` of the wasm-pack pkg that `apps/web` already resolves as `@mapsift/core`, and types the crossing signatures. Freshness is by construction: every `wasm-pack build` regenerates the `.d.ts`, and the build order already gates web builds behind wasm-pack (ADR-0001 section 3), so this direction costs no new CI job.

**The exit path is recorded now rather than when needed:** if tsify goes dormant or its tagged-union output fails the empirical check in section 5, the fallback is **ts-rs** emitting into `libs/contracts` with a regenerate-and-diff gate, accepting hand-annotated `unchecked_return_type` and `unchecked_param_type` overrides on the crossing signatures as the cost.

### 4. The single-TypeScript-shape rule

The envelope's TypeScript type is the core-generated one. The OpenAPI-to-TypeScript direction (M12's other generator) references that type wherever the API surface carries an envelope and never redeclares it. A second TypeScript declaration of a core-contract type, generated or hand-written, is a defect under M12's no-hand-written-duplicate rule.

### 5. Two guard rules the implementing windows own

- **A unique literal tag per union variant on the Rust side, witnessed downstream.** datamodel-code-generator degrades silently to a plain union when a discriminator is duplicated or unresolvable, so a test asserts the discriminator actually survived into the generated Pydantic model.
- **The opaque payload's schema is confirmed against the generator.** `serde_json::Value` emits the boolean schema `true`, valid 2020-12 but a known interop risk for schema-to-code tools; if the generator mishandles it, the Rust side forces an object-form schema with `#[schemars(schema_with = ...)]` without touching serde behaviour.

### 6. Rust to Dart stays open, with its trigger

The Dart half of agenda item 7 remains open and is decided when `apps/mobile` exists. The leading candidate on 2026-08-05 is flutter_rust_bridge, and it is a boundary-architecture commitment (it owns the FFI layer and the generated Dart surface), not a drop-in type emitter, which is exactly why it is not decided here.

### 7. What no generator may be pointed at

The conflict rule stays two implementations under golden tests (M12's deliberate duplication, foundation 9.6.6). This ADR adds tooling for data contracts and changes nothing about that.

---

## Consequences

**What this buys.** M8's acceptance becomes mechanical: one definition, every reader generated, and staleness is a red build on either path (the `--check` gate for Python, the build order for TypeScript). The pins turn a Beta-classified generator's output shifts into reviewed commits.

**What this costs.** Three pinned tools whose versions and particularities live in `specs/dependencies.md` section 2: schemars, datamodel-code-generator (a 0.x tool whose output changes across minors and whose default formatters are becoming opt-in), and tsify, whose maintenance cadence is thin, mitigated by the recorded ts-rs exit path.

**What this forecloses.** Nothing the foundation left open. The Dart half stays open by name.

**What must be revisited, and when.** tsify dormancy or a failed tagged-union check triggers the section 3 exit path, recorded here as a dated note. The Dart half closes on the `apps/mobile` trigger, in its own round. A schemars default-dialect change is neutralized by the explicit pin and needs nothing.
