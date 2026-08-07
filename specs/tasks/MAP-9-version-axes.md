# MAP-9: the five version axes are five types, and no axis can stand in for another

## Trace

PRD **M10** (the axes and the ordering rule), completed by **ADR-0004** (the per-project version as the
resync cursor, and the two allocation rules that come with it). The envelope this lands in is PRD **M8**,
whose Shape, Acceptance and Provenance were sharpened 2026-08-07 (see *Boundary decisions* below).
Generation toolchain: **ADR-0009** sections 2 and 3, with section 4 the reason one runtime is left
unprotected. Invariants **I2**, **I8**, **I9**; constraints **C10**, **C12**. The type-generation
particularities are `specs/dependencies.md` section 2.

## What this task owns

Every version axis is a distinct type in the contract, so the substitution M10's acceptance forbids is
refused by the compiler and the type checker rather than by a reviewer noticing a field name; and the fifth
axis, the per-project version, exists for the first time, on the envelope's server half.

## Out of scope

**The behaviour of any axis.** Nothing here increments, allocates, orders, deduplicates or compares. This
task fixes the contract; ADR-0004's allocation rules are **MAP-11**, dedup by mutation number is **MAP-12**,
the contiguity gap and its typed resend are **MAP-13**.

**The M10 acceptance clause that a per-feature version never decreases**, deferred to **MAP-11** with the
reasoning and the trigger in `specs/log.md` under 2026-08-07. The type chosen here must not foreclose it.

**The schema narrowing re-check**, which fired at this pickup and came back negative: MAP-9 consumes no
target type, so nothing here forces `TargetPath`, `TenantTarget`, `ProjectTarget` or `LayerTarget` back into
the generated schema. It re-arms at **MAP-10**.

**The TypeScript gap.** That the alias gives no protection is a recorded fact, not a problem to solve in
this slice, and the mechanism that would close it is refused by ADR-0009 section 4.

## Boundary decisions the owner closed

All three were closed 2026-08-07 at pickup and written into the documents that own them **before** this file
existed. This is the pointer, not the record.

- **The axes are structural, not conventional.** PRD M10 Shape; the measurement is `specs/dependencies.md`
  section 2 and `specs/log.md` under 2026-08-07.
- **The per-project version is envelope-borne, on the server half.** PRD M8 Shape, Acceptance and
  Provenance, and M10 Shape. This **reverses** the four-axis count M8 carried since 2026-08-05, and the
  Provenance line says so rather than quietly renumbering.
- **The never-decreases clause defers to MAP-11.** `specs/log.md` under 2026-08-07.

## Evidence handed over

Bought by probe on 2026-08-07 at the pinned versions, against a throwaway crate rather than this repository.
The general form is already in `specs/dependencies.md` section 2; what follows is what a window would
otherwise have to buy twice.

**A `#[serde(transparent)]` newtype protects two runtimes of three.** In Rust the newtype is nominal, which
matters here more than it looks: measured on disk before the probe, the axes come in **two pairs of
identical primitive** (`mutation_number: u64` beside `feature_version: u64`;
`operation_schema_version: u32` beside `conflict_rule_version: u32` and `applied_rule_version: u32`), so
today the compiler accepts the substitution the acceptance forbids. In Python the generated form is
`RootModel[int]` and mypy `--strict` raises `arg-type` on the substitution, measured. In TypeScript the
generated form is `export type Name = number`, a structural alias, and the substitution compiles; the field
is typed to the alias and carries none of the undefined-bare-name defect `Uuid` and `DateTime<Utc>` have.

**The wire does not move.** Bare integer in, bare integer out, round trip byte-identical against the
generated Pydantic reader. The existing envelope and catalog fixtures keep their integer literals.

**One trap, and its shape was corrected mid-task, so read this version rather than the first.** The pickup
handed over "a newtype without a `///` is inlined by schemars"; the implementation window removed
`#[serde(transparent)]` on its own measurement, which prompted a full matrix re-probe (2026-08-07) that
found the first reading had mistaken a correlation for a cause. **The dependency is on the attribute:** a
plain newtype reaches `$defs` documented or not, and only a `transparent` one inlines when undocumented,
degrading the Python side to a bare `Annotated[int, Field(ge=0)]`. The rule that follows is in
`specs/dependencies.md` section 2, and the contract freshness gate is what would catch a regression, not a
test.

**A cost, so nobody discovers it in review.** On the Python side the parsed attribute is the model rather
than the scalar, so a server-side read goes through `.root`.

**Two module docs are stale the moment this lands.** `libs/core/src/envelope.rs` and
`libs/core/tests/envelope.rs` both open with a trace line reading "the four envelope-borne version axes".
The test file's copy is Window A's to correct, because Window B may not edit a test.

## Acceptance

From PRD **M10**, the clause reachable in this slice:

> the five axes are distinct fields and no code path reads one as another

and from PRD **M8** as sharpened 2026-08-07:

> an operation carries its type and operation-schema version, and the five version axes (M10) are present
> and distinct in the envelope

The four M10 clauses that need the flush (dedup by mutation number, the typed resend-from-cursor on a gap,
and a per-feature version that never decreases) are out of scope above, each with the issue that owns it.
