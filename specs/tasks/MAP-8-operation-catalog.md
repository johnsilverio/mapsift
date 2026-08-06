# MAP-8: the operation catalog is closed, and every operation addresses one target path

## Trace

PRD **M9** (the catalog, the granularity rule, the acceptance); **M8** (the envelope this catalog
narrows: `operation_type` and the opaque payload were left wide by MAP-7 with this task named as the
exit); **M2** (the layer's declared geometry family, which the deferred refusal clause arms); **M5**
(the storage frame the geometry payload rides in); **M3** (the identifiers inside a target path);
foundation section 4 (resolution by granularity, no sub-geometric merge); I2; C2, C7. The generation
toolchain and its guard rules are **ADR-0009** (sections 2, 3 and 5); the freshness-gate principle is
ADR-0001 section 5; the generated Python model's home is ADR-0007.

## What this task owns

The catalog exists as a closed set in the envelope contract, carrying only what the slice uses (create
a feature, set its geometry), each operation with its typed payload and its one target path; an unknown
operation type is a typed rejection; and no-conflict-by-target-path is a pure decision the tests pin.

## Out of scope

- The geometry-family refusal clause of M9's acceptance (typed refusal, flag and retain): **milestone 3**,
  where the flush machinery its retention half needs exists, on the T5.2 shape; checked again at MAP-10
  pickup (owner, 2026-08-06).
- The T3.3 two-whole-geometries conflict presentation: the **conflict slice**, which this project excludes
  by name.
- The conflict rule, any Python twin of the disjointness decision, and the golden corpus: the conflict
  slice; the corpus location blocker is **MAP-32**.
- The flush endpoint and every server-side application of a catalog operation: **milestone 3** (MAP-10 to
  MAP-14).
- The concrete geometry encoding across the boundary: **MAP-33**, triggered by the first UI-core geometry
  crossing.
- Any catalog member beyond the two the slice uses: adding one is a decision, per the issue.

## Boundary decisions the owner closed

2026-08-06, each registered in `specs/log.md` (and MAP-33 created) before this file was written; this is
the pointer, not the record:

- The set-geometry payload is a **GeoJSON-shaped structure in the M5 storage frame** inside the JSON
  envelope, an interim whose recorded exit is MAP-33.
- The geometry-family refusal clause is deferred to milestone 3, on the same precedent as MAP-7's T5.1
  deferral.
- The target-path disjointness decision lands in `libs/core` as a pure function, with no Python twin and
  no golden corpus this slice.

2026-08-06, closing the Window A review (`specs/log.md` is the record): the **MAP-7 suite revision is
authorized** in the correction round, because the catalog's closure is the requirement change those tests
ride on (the two payload-opacity pins retire, the three canonical fixtures re-pair, the structurally broken
assertion reframes; the session-material opacity pins stay, OQ-18); the **type-to-target-kind pairing is
contract**, a mismatch refused with a typed error (M9's acceptance sharpened the same day); and the Python
`feature.create` positive-parse witness is **sanctioned deliberately green at red**, in the ADR-0009
section 5 guard class.

2026-08-06, closing the correction-round review (`specs/log.md` is the record): the pairing is enforced
**structurally**, each catalog member's target typed to its declared kind variant in the contract and both
generated forms, with the guard-test re-pins and the new pairing witnesses authorized by name in the log;
the nested ancestor-descendant disjointness case is **deferred to the conflict slice** (T3.4), recorded in
the granularity module doc; and the `CATALOG` order is **canonical and append-only**, the const's rustdoc
owning the rule once it exists.

2026-08-06, closing the implementation review (`specs/log.md` is the record): the tsify flatten annotation
is **ratified** (ADR-0009 section 3, dated note); the mis-paired-target TS test is corrected by the
**named-const rewrite**, the one authorized test edit of the round; `TargetKind` keeps its five rungs; the
OperationType-to-Operation drift witness is recorded debt triggered by the next catalog member; and the
schema narrowing carries its re-check at MAP-9 and MAP-10 pickup.

## Evidence handed over

From the MAP-7 rounds (2026-08-05 and 2026-08-06), living in `specs/log.md` and `dependencies.md`
section 2 with sources; repeated here only because this window trips on them mid-flight:

- datamodel-code-generator silently degrades a duplicated or unresolvable discriminator to a plain
  union; the discriminator survives only through the `#[schemars(extend(...))]` annotation plus a
  `title` per variant with `--use-title-as-name`. The ADR-0009 section 5 guard test exists for this and
  extends to any union the catalog adds.
- Unsigned integers emit their floor (`ge=0`) and no ceiling; the boolean-true schema for
  `serde_json::Value` appears only without a doc comment, and the generator emits `Any` either way.
- `ng build web` does not type-check spec files (`tsconfig.app.json` excludes them), so the TypeScript
  contract is enforced by `ng test`, not by the build.
- The MAP-7 red landed exactly on the missing generated forms in all three ecosystems; that is the shape
  of a right-reason red for a contract task.
- `just contracts` is the freshness gate (committed schema diff plus the generator's native `--check`);
  `just contracts-generate` is the restore path; both write through a temp file, so a crashed emitter
  reports itself.

## Acceptance

The issue's three bullets, which are PRD M9's acceptance minus the two clauses deferred with their
owners above, as registered 2026-08-06. The ADR-0009 section 5 guard rules are part of this task's
acceptance for every union it adds. The generation freshness gates of ADR-0001 section 6, concretized
by ADR-0009, stay green.
