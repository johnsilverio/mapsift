# MAP-7: the operation envelope exists as one generated cross-language contract

## Trace

PRD **M8** (the envelope, its two halves, its acceptance); **M3** (the operation identifier), **M4** (the clientID and the mutation number), **M9** (the target path), **M10** (the axes, and which of them ride the envelope), **M11** and **M12** (what may cross the boundary and how contracts are generated); foundation I8, I9, I10 and section 9.6.7; C10, C12, C13. The toolchain is **ADR-0009**; the generation-and-freshness principle is ADR-0001 section 5; where the generated Python model lives is ADR-0007.

## What this task owns

An operation travels in one envelope defined once in `libs/core`, the client half and the server half never mixing, and TypeScript and Python read generated forms of it whose staleness is a red build.

## Out of scope

- The operation catalog and the per-type payload shapes: **MAP-8** (M9 owns the rule). The payload here is deliberately opaque (owner, 2026-08-05).
- The five-axes behavioural tests across the system: **MAP-9** (M10).
- The flush endpoint and every server behaviour that fills the server half in anger: milestone 3 (MAP-10 to MAP-14). Here the server half is a shape, exercised by construction only.
- Authorship and mediation validation: the fields are carried, the behaviours are OQ-18's and later slices' (the issue names this scope).
- The Rust-to-Dart generation: open in ADR-0009 section 6 with its trigger.

## Boundary decisions the owner closed

2026-08-05, all registered before this file was written: the toolchain, its guard rules and the single-TypeScript-shape rule in ADR-0009 (with `dependencies.md` section 2 corrected in the same round); the payload opaque with the target path typed per M9, the catalog staying MAP-8's (`specs/log.md`). This is the pointer, not the record.

## Evidence handed over

All from the MAP-31 research round of 2026-08-05, living in `dependencies.md` section 2 with sources; repeated here only because a window will trip on them mid-flight:

- datamodel-code-generator silently degrades a duplicated or unresolvable discriminator to a plain union, which is why ADR-0009 section 5's guard test (the discriminator survives into the generated Pydantic model) exists.
- `serde_json::Value` emits the boolean schema `true`; whether the generator accepts it is confirmed in the window, with `#[schemars(schema_with = ...)]` as the escape hatch.
- tsify's exact output for a `tag`/`content` union is undocumented; it is confirmed empirically before the choice counts as pinned, and ADR-0009 section 3 names the exit if it fails.
- The pins that keep the `--check` gate stable: `--disable-timestamp`, formatters passed explicitly, a fixed invocation path (the generated header embeds the input filename), `--target-python-version 3.13`.

## Acceptance

The issue's three acceptance bullets, which are PRD M8's acceptance as revised 2026-08-05 (the four envelope-borne version axes) minus the T5.1 claimed-author divergence clause, which is flush behaviour and belongs to milestone 3. The generation freshness gates are ADR-0001 section 6's class, concretized by ADR-0009 sections 2 and 3. The guard rules of ADR-0009 section 5 are part of this task's acceptance.
