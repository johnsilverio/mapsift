# MAP-15 and MAP-17: an offline edit survives a restart as the same operation, under the same number, from the same installation

## Trace

**Requirements:** PRD **T1.2** (MAP-15's); **T1.3** and **M3** (MAP-17's); **M4** (the clientID, and a store
with none being a new installation); **M9**'s Requirement for the address an operation carries and the closed catalog it belongs to; **M10**'s
Requirement and Shape for the mutation-number axis, whose first value zero is in the Shape; **M11** and
**M12** for what crosses the boundary and how its types reach TypeScript.

**Invariants and constraints:** **I1**, **I3**, **I9**; **C1**, **C3**, **C11**, **C12**.

**ADR sections:** **ADR-0015** in full, which is this task's mechanism, decision 7 above all for what the
queue stamps; **ADR-0006** decisions 1, 3 and 4; **ADR-0009** sections 3 to 5, with section 3's note of
2026-09-28; **ADR-0001** section 7 for where the tests live; **ADR-0002** decision 1 for generating with Cargo's own
commands, which `.claude/rules/rust-core.md` restates as `cargo add` for a dependency.

**Foundation:** section 4's v0.7 decision (the mutation number) and its v0.8 decision (the clientID per
installation) with the v0.18 sharpening of the flush domain; section 5's decision of v0.2; sections 9.6.2
and 9.6.4.

**Rules:** `.claude/rules/rust-core.md`, which fires on the first `.rs` or `Cargo.toml` file opened under
`libs/core`, and which gained ADR-0015's restatement on 2026-09-28. The lockfile and the pkg do not trigger
it, so read it before anything else there.

## What this task owns

The client's operation queue exists in `libs/core` and is durable: an operation appended offline is stamped
and numbered within its flush domain and handed back as records for the platform to write, and a queue opened
from those records is the same queue, with the same installation, the same operations under the same
identifiers and numbers, and the same next number in every domain. The identifiers that name the
installation and each operation are minted by the core, the generator is published for any identifier the
platform needs before it composes an operation, and the queue is reachable across the WASM boundary.

## Out of scope

- **What the queue does with a flush response**: the echoed cursor, the typed resend, reacting to either
  refusal, and what becomes of an entry once the server has decided it. **MAP-77**, split off at this pickup;
  ADR-0015 decision 2 names the stream record it acts on.
- **The optimistic preview**, and showing the edit before any network call. **MAP-16** and T1.1.
- **The client half of M2's served-versus-element clause**, which MAP-66's spec parked on MAP-15 and MAP-19.
  The queue carries the operations it is given, and nothing ADR-0015 decision 7 lists as reaching it names a
  layer's storage class, so this task's share of that pointer moves to **MAP-16**, whose working copy knows its layers; MAP-19 keeps
  its own.
- **A real store, a real restart and the wire.** **MAP-18** chooses the web store, **MAP-19** writes the
  adapter, proves the force-close and sends what the queue offers, and **MAP-20** is the surface that produces
  an element. The web client's own port onto the core, `apps/web/src/app/core/mapsift-core.ts`, is MAP-19's
  to extend.
- **Composing the platform's part of an operation**, the part ADR-0015 decision 7 gives the platform. What
  the queue receives it carries as given; the session material's proof is OQ-18's and MAP-37's.
- **The geometry encoding** inside an entry (MAP-33). The queue carries the operation as the envelope types it.
- **The existing export's live handle.** `geodesicDistance` returns a class with `free()`, which M11's
  Acceptance forbids; that is **MAP-78**, and this task neither fixes it nor lets it decide a case.
- **The Dart half of the generated contract and any FFI binding**, on ADR-0009 section 6's trigger.
- **How a record written by an older core is upcast** (OQ-15). ADR-0015 decision 5 fixes only that the
  version is on every record and that an unreadable record is refused.
- **Protection of the store on the device** (OQ-17).

## Boundary decisions the owner closed

On **2026-09-28** unless dated otherwise, each written into the document that owns it before any window was
dispatched; items 7, 8 and 9 reached their documents after this file's first commit, at its pre-dispatch reads.

1. **The storage interface is a record contract**, the core holding no store and no callback: ADR-0015 by
   ruling, with its decisions 2 to 5, which the orchestrator wrote from that ruling and the canon, ratified.
2. **A record's value is opaque to the platform**, a JSON string the core writes and parses, and **an
   operation crosses the same way**, in and out: ADR-0015 decision 6.
3. **tsify moves to 0.5.8 and a crossing signature uses `Ts<T>`**: ADR-0009 section 3's note of 2026-09-28.
   The bump goes through the toolchain (ADR-0002). Which window makes it, and which makes the `getrandom`
   change of ADR-0015 decision 7, follows from the `test` skill's rule that Window A writes the minimum
   surface its tests need to compile.
4. **The client halves earlier rounds left under MAP-15's name are split.** They are minting the clientID
   (MAP-12, MAP-13, MAP-46), which is MAP-17's and batched here; persisting the queue (MAP-12, MAP-13,
   MAP-46, MAP-68, MAP-72), which is this task's; the four that concern a flush response, namely advancing
   from the echo (MAP-12, MAP-13, MAP-46, and MAP-43's "client half of the axis"), the typed resend (MAP-13),
   reacting to either refusal (MAP-13, MAP-46) and the refused entry (ADR-0014, ADR-0010, MAP-66), which are **MAP-77**'s; and M2's
   served-versus-element half (MAP-66), routed above. The preview those same sources name stays MAP-16's. The
   three dated notes, two in ADR-0014's Consequences and one in ADR-0010 decision 6, move the pointers in both
   ADRs; the task specs named are closed rounds and keep their text as history.
5. **MAP-17 rides with MAP-15** as one window pair, which `specs/testing.md` section 1.2 allows, and one pull
   request, which is the owner's ruling recorded in MAP-15's Linear pickup note.
6. **The queue crosses the WASM boundary in this task**, so MAP-19 is an adapter that decides nothing:
   ADR-0015 decision 6 and Consequences.
7. **The task runs in the main checkout, alone**, and MAP-76 waits rather than running as a parallel lane
   (`specs/log.md`, 2026-09-28).
8. **The two build-time versions the queue stamps have values**, 1 for every catalog member's schema and 0
   for a runtime with no conflict rule: PRD M10's Shape, 2026-09-29.
9. **The opened queue's state lives in the core's instance and no handle crosses**, rather than the
   platform handing every record over on every call: ADR-0015 decision 1, 2026-09-29.

**Written by the orchestrator and ratified by the owner on 2026-09-29 with the go for Window A:**
ADR-0015 decision 7, what the queue stamps and what the platform supplies, written after this file's first
pre-dispatch read found the envelope's field ownership undecided; three additions made after the second
read, each derived rather than chosen, namely decision 4's sentence that a record read back on open is
confirmed, decision 6's that an operation the core cannot parse is refused at the append, and decision 6's
paragraph that a refusal crosses as a value because a thrown error is in no generated signature and M12
leaves no boundary value untyped, which binds every refusal of decisions 5, 6 and 7, the unreadable record
and the refused randomness included; and the routing of M2's client half to MAP-16 in Out of scope. **Recorded rather than
decided:** the correction to `CLAUDE.md` C12 and PRD T2.3, which now point at the flush domain.

## Evidence handed over

**The toolchain's behaviour at the boundary is measured, and it lives in `specs/dependencies.md` section 2**
under "Crossing the boundary with tsify and minting with uuid, measured 2026-09-28". It is not restated here.
Four of its facts shape this task and are named so the window opens that subsection rather than
rediscovering them: the route that mints without a panic, and the lock change it brings, measured in its
addition of 2026-09-29; the pinned tsify 0.5.6 leaking on a failed input conversion where 0.5.8's `Ts<T>`
does not; the outermost type's serializer settings governing everything nested inside it; and a thrown error
appearing in no generated TypeScript signature.

**What the tree carries, read 2026-09-28 on this branch unless marked.**

- `libs/core/Cargo.toml` declares `uuid` with `features = ["serde"]`, and `libs/core/Cargo.lock` carries **no
  `getrandom` at all** (`grep -c getrandom` returns 0). A lockfile records no features, so the feature set is
  the manifest's plus the crate's defaults.
- **No exported function crosses a tsify type today.** The envelope types derive `Tsify` as declarations only,
  and the one export returns a `#[wasm_bindgen]` struct (`libs/core/src/boundary.rs`,
  `libs/core/pkg/mapsift_core.d.ts`). This task publishes the first tsify crossing.
- **A web test that needs the WASM module to execute does not run in `just check`**: `angular.json` excludes
  `**/*.browser.spec.ts` from the web project's `test` target and includes it only in a separate
  `test-browser` target, which neither the `justfile` nor `.github/workflows/ci.yml` invokes. The type-level
  contract specs beside it, `apps/web/src/app/core/operation-envelope.spec.ts` and
  `operation-catalog.spec.ts`, do run, since they compile against the generated `.d.ts`.
- **The baseline, measured**: `just check` at `98ea71b` exited 0 with 385 Python, 31 Rust and 12 Angular
  cases passing. A first run the same day reported 303 errors reading `failed to resolve host 'db'`, because
  the database container had stopped two days earlier and `just check` passes `--no-deps`; starting `db`
  alone cleared it.

## Acceptance

**The delta only.** The criteria are law in the PRD and in ADR-0015, and the window reads them there.

- **T1.2's first clause, and C1's test with it, is split: the reopen has a runtime here and the restart does
  not.** The records a transition returned, handed back to open a queue, are the whole of the store in this
  task; a real store surviving a real force-close is MAP-19's. "Still flush on reconnect" is, here, the queue
  offering, for each flush domain in mutation-number order, the pending operations whose records are
  confirmed written (ADR-0015 decision 4); sending them is MAP-19's.
- **T1.2's second clause, the desktop SQLite adapter, has no runtime.** It is held by ADR-0015 decisions 3
  and 6, and nothing is built for it.
- **M3's "two clients creating features offline sync with no collision", which T1.3's Acceptance words as
  "features created offline on two clients sync without ID collision", has only its client half here**: two
  installations mint different clientIDs and different identifiers, which is a property of the minting layer
  and its real source of randomness, since bytes injected into the queue's logic would prove only what was
  injected. Its sync half is MAP-23's,
  whose trace and acceptance gained C3 and T1.3 on 2026-09-28 for that reason.
- **M3's "an identifier is unchanged by a resend" has its reopen half here**: a queue opened from its records
  offers each operation under the identifier it was appended with. A resend after a flush response is
  MAP-77's.
- **M3's "an identifier belonging to a deleted feature is never assigned to a new one" has no runtime here.**
  ADR-0006 decision 4 lists it among the rules that can be asserted, and it belongs where a feature can be
  deleted, which no catalog member does yet; the queue deletes nothing and reassigns nothing.
- **M4's Acceptance has two clauses with a client half here**: reinstalling yields a new clientID whose
  stream starts at the first mutation number, and two installations of one user hold two clientIDs. The
  cursors and the false-dedup half of the second clause are the server's, and what a client does with the
  reconciliation response a missing cursor earns is not this task's.
- **M11's Acceptance has one clause here, and it is scoped to this task's crossing.** No live handle appears
  in a signature this task publishes, asserted over the generated contract. An assertion over the whole
  `.d.ts` would be red on `MeasuredValue`, which is MAP-78's, so it is not the one this task owes. Compiling
  to an FFI library from the same source, the counted crossings of a vertex drag and an image crossing as a
  reference have no runtime here.
- **ADR-0015 decision 3 has two halves and only the core's has a runtime here**: the records a transition
  returns form its unit. That a store writes the unit atomically is MAP-19's to witness against a real store.
- **ADR-0015 decision 4's residual has no runtime anywhere yet**: whether a confirmation survives a power loss
  is a property of the store MAP-18 chooses.
