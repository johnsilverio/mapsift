# The Canon axis, in detail

Reference for the **Canon** axis of `code-review`. Read it when reviewing a diff that touches any code
carrying an invariant. It is a checklist of **what a violation looks like in code**, not a restatement of the
decisions: each row cites the authority, and the authority is where the reasoning lives.

**Every row here blocks.** An invariant is law with a pass or fail acceptance criterion, and the answer to a
failure is never to weaken the rule. If the rule is genuinely wrong, that is a foundation revision with a
logged entry, decided by the owner, not a compromise reached inside a review.

The invariants are `specs/mapsift-foundation.md` section 11 (I1 to I11) and the constraints are `CLAUDE.md`
(C1 to C14), which are the same law stated twice for two readers. The `M`, `T`, `S`, `N` and `U` identifiers
are `specs/PRD.md`.

## The invariants and constraints, as they fail in a diff

| Rule | What a violation looks like |
| --- | --- |
| **I1, C1** offline write path | an element edit that waits on a network round trip before it is applied and shown; a queued write that does not survive a restart; an import refused **after** the file was accepted rather than before, or queued as if it would sync when it cannot |
| **I2, C2** convergence | a client that resolves and then trusts its own resolution; correctness riding on a WebSocket delivery instead of on versioning, gap detection and resync |
| **I3, C3** identifier safety | a creation that waits for the server to name it; a database-side default such as `gen_random_uuid()` on a table a client can create rows in offline; a code path deriving meaning, ordering or authority from an identifier's content (ADR-0006) |
| **I4, C4** tenant isolation | a tenant-scoped query filtered in Python rather than at the SQL layer; a new tenant-owned table with row-level security missing, or enabled without **FORCE**; any role granted `BYPASSRLS`; a session-scoped tenant binding, or one interpolated into the statement instead of parameterised; a foreign key between tenant-owned tables that is not composite over `(tenant_id, key)`; a natural unique key that is global rather than per tenant; an index serving a tenant-scoped query that does not lead with `tenant_id`. All ADR-0005 |
| **I5, C5** type safety | an incomplete signature, an `Any` with no justifying comment, a hand-written declaration of a generated type (M12) |
| **I6** large-data performance | a whole layer promoted into the client-side editable source; a budget asserted without its device, versions, fixture and date; the three budgets of N1 conflated with one another |
| **I7, C6** no production data | a production credential or production dataset in any non-production environment, in any form |
| **C7** preserve-not-discard | a legal-weight geometry conflict resolved by overwrite; a delete that silently wins over a concurrent edit; **a validation or a refusal that drops the operation instead of flagging and retaining it**, which is the same sin wearing a validation costume (M9); a geometry fused from two versions, which invents a polygon nobody drew (T3.3) |
| **C8** additive restore | a restore that removes or rewrites versions that came after it |
| **I2, C9** ordering authority | authoritative document state read from or held in the Channels tier; a flush that allocates its version range per operation rather than once; an allocation taken before validation, dedup and the conflict rule rather than last before commit (ADR-0004) |
| **I8, C10** one rule, two runtimes | the conflict rule generated rather than golden-tested; Rust running on the server; a legal-weight resolution finalised on the client; a geometric predicate compared without the declared metre tolerance, or a tolerance expressed in degrees (M13) |
| **C11** portability | client logic settling into the Angular or Flutter layer instead of `libs/core`; a live reference crossing the core or capability boundary (a map object, a database handle, a callback into a live object); bytes crossing where a reference belongs (M11) |
| **I9, C12** idempotency | a cursor advanced by assumption instead of from the server's echo; dedup keyed on the user rather than on the clientID; a gap above the cursor skipped silently instead of answered with a typed resend (M10) |
| **I10, C13** authorship | an author taken as a free client field, or from the flushing session rather than the creating one; an unauthorised offline operation silently applied or silently dropped; a legal-weight feature's authorship collapsed to a single stamp instead of the preserved ordered chain |
| **I11, C14** agent writes | an agent-originated write indistinguishable from a direct human write; an agent action on legal-weight geometry or a bulk write applied without human confirmation; an agent reaching data by any path other than the capability layer |

## The PRD rules an agent gets wrong on its own

| Rule | What a violation looks like |
| --- | --- |
| **M5** the metric frame | **any area, perimeter or distance computed in degrees**; a legal area computed in UTM; a metric with no declared purpose, frame and authority; a frame hard-coded in a formula rather than selected by the metric's purpose; geometry that leaves storage and returns changed |
| **M2** the storage class | a feature whose path is decided anywhere other than its layer's storage class; a served layer's features entering the operation queue; a geometry stored outside the family its layer declares |
| **M9** one target path | an operation addressing two properties or two features outside the named exceptions; a geometry operation carrying a vertex delta instead of the whole geometry |
| **M15** the append-only log | a log entry updated in place; a correction written as a mutation rather than as a new operation |
| **M7, M16** regulatory content | a regulatory value as a literal in a function; legal weight raised or lowered by an external registry's status; protection removed retroactively |
| **S5** capture provenance | a vertex with no capture method and precision estimate; geometry from device positioning presented as meeting the certification-grade accuracy the norm requires |
| **N9** observability | a log line on the sync path with no correlation key; geometry or personal data reaching a log; a failure with no user-visible signal and no record |
| **U1, U2, U10** the design system | a raw colour, radius, size or spacing literal in a component; a translucent surface declaring its own blur, tint or saturation; a bespoke re-implementation of a primitive `@mapsift/ui` already provides; a relative import into the library's source |

## Code shape

| Check | Authority |
| --- | --- |
| no import upward through the package tier order, and no package reaching another through its `models` | ADR-0007 section 4, enforced by `lint-imports` |
| pure decisions in `rules.py`, reads in `selectors.py`, writes in `services.py` as the only writer | ADR-0007 section 3 |
| a framework artifact generated by its own generator and then edited, never hand-written | ADR-0002 section 1 |
| migrations generated, never hand-authored | ADR-0002 section 1, `.claude/rules/python-django.md` |
| the Angular component file layout, one component per folder, the three-condition inline exception | ADR-0002 section 2 |
| every feature route lazy loaded; signal-based data access the default; one forms API per surface; the library imported from its barrel only | ADR-0003 |
| no repository pattern wrapped around the ORM without a measured reason | `CLAUDE.md`, foundation section 10 |
| an external integration sits behind a narrow interface with a real adapter and a test fake | `specs/testing.md` section 3 |
| nothing in `apps/` imports from another `apps/`; everything shared crosses through `libs/` | ADR-0001 section 1 |

## What must not be created yet

`apps/sync`, `apps/desktop`, `apps/mobile`, the sync engine's internals, and any dependency-gated ADR's
subject, each with the gate that unlocks it written in **ADR-0001 section 8**. A package created before the
code that lives in it is the same defect one tier down (ADR-0007 section 7).

## Comments

An inline comment earns its place only as a **trap**: the correct code looks wrong, or the wrong code looks
right, so without it somebody "fixes" it and reintroduces the defect. A docstring on a public surface saying
what the thing guarantees is welcome at one to three lines. **Reasoning the canon already documents is cited
by identifier and never restated**, because a restatement is a second copy outside the fan-out. An
explanation of what the code does is a naming failure.

## Prose

No em dash and no double hyphen in prose, in any document in this tree. **Enforced at write time since
2026-08-10** by `.claude/hooks/check-prose.sh`, which exempts fenced blocks, inline spans, and
`specs/index.md` and `specs/log.md` whole, those two by the exception the session-handoff header writes.
A document older than that hook carries no such guarantee, so a diff touching one is still read.
