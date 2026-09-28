# MAP-15 and MAP-17: an offline edit survives a restart as the same operation, under the same number, from the same installation

## Trace

**Requirements:** PRD **T1.2** (MAP-15's); **T1.3** and **M3** (MAP-17's); **M4** (the clientID, and a store
with none being a new installation); **M10**'s Requirement for the mutation-number axis; **M11** and **M12**
for what crosses the boundary and how its types reach TypeScript.

**Invariants and constraints:** **I1**, **I3**, **I9**; **C1**, **C3**, **C11**, **C12**.

**ADR sections:** **ADR-0015** in full, which is this task's mechanism; **ADR-0006** decisions 1 and 3;
**ADR-0009** sections 3 to 5, with section 3's note of 2026-09-28; **ADR-0001** section 7 for where the
tests live; **ADR-0002** for generating with the toolchain, a dependency change included.

**Foundation:** section 4's v0.7 decision with its v0.18 sharpening of the flush domain; section 5's decision
of v0.2; sections 9.6.2 and 9.6.4.

**Rules:** `.claude/rules/rust-core.md`, which fires on the first file this task opens in `libs/core`, and
which gained ADR-0015's restatement on 2026-09-28.

## What this task owns

The client's operation queue exists in `libs/core` and is durable: an operation appended offline is numbered
within its flush domain and handed back as records for the platform to write, and a queue opened from those
records is the same queue, with the same installation, the same operations under the same numbers, and the
same next number in every domain. The identifiers that name the installation and each operation are minted
by the core, and the queue is reachable across the WASM boundary.

## Out of scope

- **What the queue does with a flush response**: the echoed cursor, the typed resend, a refused entry, and
  what becomes of an entry once the server has decided it. **MAP-77**, split off at this pickup; ADR-0015
  decision 2 names the stream record it acts on.
- **The optimistic preview**, and showing the edit before any network call. **MAP-16** and T1.1.
- **A real store, a real restart and the wire.** **MAP-18** chooses the web store, **MAP-19** writes the
  adapter, proves the force-close and sends what the queue offers, and **MAP-20** is the surface that produces
  an element. The web client's own port onto the core, `apps/web/src/app/core/mapsift-core.ts`, is MAP-19's
  to extend.
- **Composing an operation**: which catalog member, its target and payload, the author's session material
  (OQ-18, MAP-37) and the claimed creation time. What this task owns in an envelope is what M4 and M10 give
  the client for its queue, the clientID and the mutation number.
- **The geometry encoding** inside an entry (MAP-33). The queue carries the operation as the envelope types it.
- **The existing export's live handle.** `geodesicDistance` returns a class with `free()`, which M11's
  Acceptance forbids; that is **MAP-78**, and this task neither fixes it nor lets it decide a case.
- **The Dart half of the generated contract and any FFI binding**, on ADR-0009 section 6's trigger.
- **How a record written by an older core is upcast** (OQ-15). ADR-0015 decision 5 fixes only that an
  unreadable record is refused.
- **Protection of the store on the device** (OQ-17).

## Boundary decisions the owner closed

All on **2026-09-28**, each written into the document that owns it before this file existed.

1. **The storage interface is a record contract**, the core holding no store and no callback: ADR-0015. The
   owner ruled on the shape and ratified decisions 2 to 5, which the orchestrator wrote from that ruling and
   the canon.
2. **A record's value is opaque to the platform**, a JSON string the core writes and parses, and **an
   operation crosses the same way**, in and out: ADR-0015 decision 6.
3. **tsify moves to 0.5.8 and a crossing signature uses `Ts<T>`**: ADR-0009 section 3's note of 2026-09-28.
   The bump is part of this task and goes through the toolchain (ADR-0002).
4. **The four client halves earlier rounds left under MAP-15's name are split**, and the reaction to a flush
   response is **MAP-77**: the dated notes in ADR-0014's Consequences and ADR-0010 decision 6 move the
   pointers.
5. **MAP-17 rides with MAP-15** as one window pair and one pull request (`specs/testing.md` section 1.2).
6. **The queue crosses the WASM boundary in this task**, so MAP-19 is an adapter that decides nothing:
   ADR-0015 decision 6 and Consequences.
7. **The task runs in the main checkout, alone**, and MAP-76 waits rather than running as a parallel lane.

Recorded with them rather than decided: ADR-0015 decision 1's rule that the opened queue's state lives in the
core's instance and no handle crosses, which is M11's Acceptance applied, and the correction to `CLAUDE.md` C12
and PRD T2.3 that now point at the flush domain (`specs/log.md`, 2026-09-28).

## Evidence handed over

**The toolchain's behaviour at the boundary is measured, and it lives in `specs/dependencies.md` section 2**
under "Crossing the boundary with tsify and minting with uuid, measured 2026-09-28". It is not restated here.
Four of its facts shape this task, and are named so the window opens that subsection rather than
rediscovering them: the web target mints only with `uuid`'s `js` feature and the lock changes with it; the
pinned tsify 0.5.6 leaks on a failed input conversion and 0.5.8's `Ts<T>` does not; the outermost type's
serializer settings govern everything nested inside it; and `Uuid::new_v4` panics when randomness is
unavailable, read in its source, beside the rule's ban on a panic on a recoverable path. Whether an
unavailable source of randomness is a recoverable path is the window's to argue, not this file's.

**What the tree carries, measured 2026-09-28 on this branch.**

- `libs/core/Cargo.lock` carries `uuid 1.24.0` with only `default`, `serde` and `std`, and **no `getrandom`
  at all**. A test that calls a minting function which does not exist yet is red by compilation, and nothing
  random can be generated in a test before the dependency changes, so a fixture needing an identifier spells
  one.
- **No exported function crosses a tsify type today.** The envelope types derive `Tsify` as declarations only,
  and the one export returns a `#[wasm_bindgen]` struct (read in `libs/core/src/boundary.rs` and
  `libs/core/pkg/mapsift_core.d.ts`). This task publishes the first tsify crossing.
- **A web test that needs the WASM module to execute does not run in `just check`**: `angular.json` excludes
  `**/*.browser.spec.ts` from the web project's `test` target and includes it only in a separate
  `test-browser` target, which neither the `justfile` nor any workflow invokes. The type-level
  contract specs beside it, `apps/web/src/app/core/operation-envelope.spec.ts` and
  `operation-catalog.spec.ts`, do run, since they compile against the generated `.d.ts`.
- **The baseline**, `just check` at `98ea71b`: exit 0, with 385 Python, 31 Rust and 12 Angular cases passing.
  A first run the same day reported 303 errors reading `failed to resolve host 'db'`, because the database
  container had stopped two days earlier, and `just check` passes `--no-deps`. Starting `db` alone cleared it.

## Acceptance

**The delta only.** The criteria are law in the PRD and in ADR-0015, and the window reads them there.

- **T1.2's first clause, and C1's test with it, is split: the reopen has a runtime here and the restart does
  not.** The records a transition returned, handed back to open a queue, are the whole of the store in this
  task; a real store surviving a real force-close is MAP-19's. "Still flush on reconnect" is, here, the queue
  offering its pending operations for each flush domain in mutation-number order; sending them is MAP-19's.
- **T1.2's second clause, the desktop SQLite adapter, has no runtime.** It is held by ADR-0015 decision 6,
  and nothing is built for it.
- **M3 and T1.3's "two clients creating features offline sync with no collision" has only its client half
  here**: two installations mint different clientIDs and different identifiers. Its sync half, two clients'
  offline creations meeting on the server, is MAP-23's.
- **M3's "an identifier belonging to a deleted feature is never assigned to a new one" has no runtime**: the
  queue deletes nothing and reassigns nothing, and the property is ADR-0006's randomness.
- **M4's Acceptance has one clause here**, a new installation. Its other clauses are about the server's
  cursor, and what a client does with the reconciliation response a missing cursor earns is not this task's.
- **M11's Acceptance has one clause here, and it is scoped to this task's crossing.** No live handle appears
  in a signature this task publishes, asserted over the generated contract. An assertion over the whole
  `.d.ts` would be red on `MeasuredValue`, which is MAP-78's, so it is not the one this task owes. Compiling
  to an FFI library from the same source, the counted crossings of a vertex drag and an image crossing as a
  reference have no runtime here.
- **ADR-0015 decision 3 has two halves and only the core's has a runtime here**: the records a transition
  returns form its unit. That a store writes the unit atomically is MAP-19's to witness against a real store.
- **ADR-0015 decision 4's residual has no runtime anywhere yet**: whether a confirmation survives a power loss
  is a property of the store MAP-18 chooses.
