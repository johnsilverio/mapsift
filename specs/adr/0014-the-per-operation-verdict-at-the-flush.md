# ADR-0014: The per-operation verdict at the flush

- **Status:** accepted (2026-09-17)
- **Deciders:** the owner, on the MAP-72 round (one research strand against the primary documentation of four sync systems, plus the canon reads listed under Context, all 2026-09-17)
- **Authority:** derives from `specs/mapsift-foundation.md` v0.19 (I2, I9, I10, section 4's v0.7 and v0.8 decisions) and `specs/PRD.md` v0.16 (T5.2, M4, M8, M9, M10, M13, M15, N9). Where this ADR and the foundation disagree, the foundation wins and this ADR is the one that is wrong.
- **Supersedes:** nothing. **Superseded by:** nothing. **Extends:** ADR-0010 decision 6, whose closed refusal set it splits in two and whose third member it moves; ADR-0004 decision 4, whose log columns it grows; ADR-0011 section 4, whose closed event set it grows; ADR-0012 decisions 1 and 3, whose projection fold it narrows.
- **Delivers:** MAP-72's mechanism, which that issue deliberately left undecided, and unblocks MAP-15, MAP-19, MAP-37 and MAP-66.

---

## Context

Every refusal the flush path can make today refuses the **whole batch**. That was harmless while each refusal was either a malformed batch, which is a client defect, or a cursor mismatch, whose remedy is a resend. It stopped being harmless when refusals began to judge **the content a client authored** against server state: `no_layer_in_this_project` (ADR-0010 decision 6, addition of 2026-09-08) and the two layer-declaration refusals MAP-66 wrote and did not ship.

Three rules already closed in the canon combine into a permanent stall. The client's queue is persistent and **append-only** (foundation section 4, v0.7), so a client can neither remove nor rewrite the operation the server refuses. The server applies a stream **only in contiguous mutation-number order** (M10), so nothing above the refused operation can be applied while it is refused. And resending reproduces the refusal forever. One polygon drawn on the wrong layer at operation 17 of an offline day therefore blocks every operation that installation captured after it, permanently, which is the divergence **I2** forbids. It was found at MAP-66's final review by two axes independently, and MAP-66 is parked behind this decision rather than shipping a latent break.

What the requirements ask for is not a better batch refusal. T5.2 and M9 both describe a verdict **per operation**: flagged, not applied, not dropped. Nothing on the flush path can say that today.

**What was read for this decision:** foundation section 4 (the v0.7 and v0.8 decisions) and OQ-23; PRD T5.2, M4, M8, M9's Acceptance, M10, M13's Requirement and M15; ADR-0004 decision 4 with its additions; ADR-0010 decision 6 with all six additions; ADR-0011 section 4; ADR-0012's decision list; and `mapsift/sync/models.py`, `rules.py` and `services.py` with `libs/core/src/envelope.rs`.

## What was researched

The foundation cites Replicache and its successor Zero as the origin of the per-client mutation number and its cursor, so what those systems do when a mutation is refused is evidence rather than opinion. All sources were read on **2026-09-17**; the Zero source is `rocicorp/mono` at commit `606adc2`.

- **Replicache** (`doc.replicache.dev/reference/server-push`): *"If a mutation is invalid or cannot be handled, the server must still mark the mutation as processed by updating the `lastMutationID`. Otherwise, the client will keep trying to send the mutation and be blocked forever."* A transient error aborts without advancing, and the documentation warns that this blocks synchronisation and is only correct when the server *"definitely will be able to process the mutation later."*
- **Zero** (`zero.rocicorp.dev/docs/mutators.md`, `packages/zero-server/src/process-mutations.ts`): the mutator's transaction rolls back, then a **second** transaction advances the cursor **and** writes an error row together. If that second transaction cannot commit, the push fails and the stream halts rather than skip.
- **PowerSync** (`docs.powersync.com/handling-writes/handling-write-validation-errors.md`): the client queue is a blocking FIFO, and the backend *"should respond with 'success' (HTTP 2xx) even in the case of write conflicts or validation failures"*, which is the same move without a server cursor.
- **ElectricSQL**: a demo pattern only, classifying by status code and wiping local state on rejection.

**Two findings shape this decision.** Advancing the cursor past a refused mutation is the established technique in every system with this shape, so nothing exotic is being invented here. And **none of them retains the refused operation**: Zero keeps only an error message and deletes it once the client acknowledges, and PowerSync's retaining strategy is an optional pattern left to the developer. Mapsift's no-drop rule is therefore **stricter** than the pattern the foundation cites, and the foundation's "nothing is lost" holds there for idempotency and resend and not for retention. That gap is the reason decision 3 exists.

---

## Decision

### 1. A refusal about an authored operation is a verdict on that operation, and the rest of the batch still applies

The flush stops being all-or-nothing about the operations it accepts. Each operation of a batch receives a verdict, and an operation the server refuses is **recorded, not applied, and never dropped**, while the operations around it apply normally. This is the shape T5.2 and M9 already require and is what makes a stalled stream impossible to reach.

**The criterion that decides which refusals stay whole-batch is the remedy, not the layer the check sits at.**

- **The batch is refused whole** when the batch itself is malformed (the five composition rules of ADR-0010 decision 6, `422`), when the **domain** is refused (the tenant claim or the project claim, `404`), or when the **remedy is a resend** (`gap_above_cursor` and `no_cursor_in_this_domain`, `409`). In all three the client's next act is defined and reaches the server: fix the batch, address a project it holds, resend from the named point.
- **The operation is refused alone** when the refusal judges **what the client authored** against server state it could not have known. There the client's next act does not exist on the wire: the queue is append-only, so there is nothing it can send that changes the answer.

**The failure mode of the criterion is deliberate.** A refusal misfiled as whole-batch stalls a stream, which I2 forbids; a refusal misfiled as per-operation refuses one operation the batch might have survived, which loses nothing and is visible. When in doubt, the verdict is per operation.

**An unexpected error is never a verdict.** Zero converts a transient database failure on the first attempt into a permanent skip whenever its bookkeeping transaction commits; under no-drop that is exactly a discard. Here the verdicts are **pure decisions computed before any write** (the ADR-0004 rule that validation, dedup, contiguity and the conflict rule all run outside the critical section), so a refusal is never an exception caught mid-write. Anything unexpected fails the whole flush, writes nothing, advances nothing, and the client resends: `request.failed` and not `request.refused` (ADR-0011 section 4).

### 2. `no_layer_in_this_project` moves out of the stream-refusal set, which returns to two members

The closed reason set of ADR-0010 decision 6's addition of 2026-08-13 keeps **`gap_above_cursor`** and **`no_cursor_in_this_domain`**, both about the cursor and both answered by a resend. The third member added on 2026-09-08 fails the criterion of decision 1 in every clause: the stream is contiguous, the cursor is intact, and resending reproduces the refusal forever, which that addition itself wrote down one paragraph before concluding the opposite. It becomes the first **operation** verdict reason instead.

That addition is corrected in place under this ADR rather than deleted, because its reasoning about why the refusal must be typed rather than a `500` stands unchanged; only the granularity moves.

**The two refusals MAP-66 wrote, `served_layer_takes_no_operations` and `geometry_outside_the_layers_family`, are operation verdicts by the same criterion**, and that is what unparks MAP-66. This ADR does not restate their rules, which already sit in `layers/rules.py`; it fixes only where their verdict lands.

### 3. The refused operation is retained on the append-only log, with its verdict and its reason as columns

The log entry is written exactly as an applied one is: the client half verbatim (M8 forbids the server rewriting it), inside the tenant's wall, with its allocated per-project version. It gains two columns, `verdict` and `refusal_reason`, and the second is null for an applied entry.

**The log is the retention M9 and T5.2 mean.** A separate table would be a second home for the same authored operation, and M15's chain would then have to be read from two places to be complete. This is where the decision departs from every system researched, and it is the departure the product exists to make: the geometry was drawn in the field, and a refusal that keeps only an error message has discarded the work while reporting it.

**A refused entry is not part of the current state.** The projection fold of ADR-0012 decision 3 walks the applied operations only, so nothing refused reaches `layers_feature`, and the reproducibility clause of M15 replays the applied chain.

**A refused entry has no applied-at, and the column says so rather than a window deciding it.** `applied_at` is the authoritative stamp T5.3 and M15 require of every entry in an attributed **chain**, and a chain is of applied operations; stamping a refusal with an apply time would put a lie in the one field M15 replays. So the column ADR-0012 decision 5 decided is **nullable, and non-null exactly when the verdict is applied**, enforced as a check constraint rather than by whoever writes the next inserter. *(Corrected 2026-09-17, hours later, at the pre-dispatch read of the MAP-72 spec: the first form said the column "becomes" nullable and read as an alteration of something on disk. **There is no timestamp column on the log today**, MAP-53 being the task that lands it and still in Backlog, so this clause binds MAP-53 rather than describing a change MAP-72 has anything to alter. What MAP-72 owes is the verdict and its reason.)* The three remaining server-half fields (the per-feature version, the applied rule version, and M7's legal weight in force) have no column to be null in, each still belonging to work nobody has finished, so nothing here decides them. *(Corrected 2026-09-17 at the third pre-dispatch read: the first form said each belongs to work "with its own owner", and the applied rule version has none anywhere in the canon, which ADR-0004 decision 4's addition of 2026-08-10 says in as many words.)* **`ServerHalf` stays the shape of an applied operation** and a refused entry assembles none: the server half is assembled at the read boundary (ADR-0004 decision 4), and the read it is assembled for is the resync, which filters to applied by the clause above.

**It consumes a per-project version anyway**, because the allocation is one statement for the whole flush (ADR-0004 decision 2) and a nullable ordering column would buy a hole in exchange for a second code path. The consequence is named rather than left to be discovered: **the resync read must filter on the verdict**, since a resync stream is a stream of applied operations (ADR-0004 decision 4, M8). MAP-22 inherits that clause.

### 4. The verdict is a member of the envelope's closed verdict set, and its name is `refused`

PRD M8 already puts a **resolution verdict** on the envelope's server half, and `libs/core` already declares it as a closed set grown additively, with one member today. The refusal verdict joins that set rather than opening a parallel concept: one field answers "what did the server decide about this operation", and the log's column is storage for that contract and never a second declaration of it (ADR-0004 decision 4's rule, applied unchanged).

**The name is `refused` and not `flagged`, because M13 already owns a `flag and preserve both`** for a conflict, where two whole versions are retained and a human chooses between them. A refusal applies nothing at all. Two outcomes under one word in one enum is the confusion M10 refuses between version axes, arriving in a different field. "Flagged" stays the word the requirements use for the property the user sees, and this is the sentence that reconciles the two spellings.

**The set therefore has two declarants and says so:** M13 declares the conflict-rule members, and this ADR declares the refusal member with its reason. The rustdoc in `libs/core/src/envelope.rs` names M13 as the sole declarant and is **wrong from the moment this decision is accepted**; correcting it is MAP-72's implementation, not this document's, because a decision that edits code is a decision the two-window protocol exists to keep out of the orchestrator's hands.

### 5. The cursor advances over a refused operation, and it is renamed to say what it now means

The per-client cursor advances to the highest mutation number the flush **decided**, applied or refused, in the same transaction that records both. A refused operation is therefore deduplicated on a resend exactly as an applied one is, which is what keeps the stream moving and what makes the resend idempotent (I9, C12).

**The one piece of Zero's mechanism that transfers is the atomicity**, and it transfers in a stronger form: there is no second transaction here, because the verdicts are decided before the writes, so the applied rows, the refused rows and the cursor commit together or not at all. There is no state in which the cursor has moved past an operation the log does not hold.

**The name changes with the meaning: the axis is the per-client mutation number and the cursor on it is `last_decided_mutation_number`**, on the wire, in the canon and in the column. A cursor that includes refused operations while being called last-applied is a name that lies, and this repository's own rule is that an explanation of what the code does is a naming failure. The rename is taken now for a reason that expires: no client reads this key, `libs/contracts` does not generate it yet (MAP-35), and every document that carries the old word is being edited in this same fan-out anyway, so the marginal cost is one migration and a word.

### 6. The response says which operations were refused, and its status stays `200`

The flush answers `{"last_decided_mutation_number": <integer>, "refused": [{"mutation_number": <integer>, "reason": "<value>"}, ...]}`. The list is empty when nothing was refused.

**`200` rather than a partial-success status**, because the batch was processed: the server decided every operation in it, and the client advances from the echo alone (T2.3, C12). `409` keeps meaning "this stream cannot continue here", which is now true of exactly the two cursor reasons, and a client that reads only the status still behaves correctly, because there is nothing to resend.

**The list is in ascending mutation-number order**, which ADR-0010 decision 6 fixes as part of the body it owns rather than this decision restating it.

**The keys name their axis** under the rule of ADR-0010 decision 6's addition of 2026-08-11, which is why the refusal carries `mutation_number` and not a bare index into the batch: a position in a list is not an axis and does not survive a client regrouping its queue. **The object is closed**, so a new key goes through ADR-0010 decision 6 the way the existing ones did.

**Reason values are the `rules.py` enum's**, exactly as ADR-0011 section 4 delegates the `409`'s, and the refusal reasons are a closed set of their own owned there.

### 7. Each operation is judged against the state the operations before it leave

The verdicts are computed in mutation-number order, over the state the **applied** operations of the batch produce. An operation that becomes invalid because an earlier one was refused earns its own verdict, by the same rules, rather than a cascade of its own; nothing is refused for being downstream of a refusal.

**What this deliberately does not answer:** what a create addressing a feature that already exists means (MAP-68), what a wire-legal geometry payload is (MAP-70), and whether an operation addressing a feature no applied operation ever created is refused or applied. The third is reachable only through the second, and this ADR states the position rather than inventing a rule inside it.

> **Addition (2026-09-24), at the MAP-68 pickup: two of the three are answered, and a held operation is not judged.** The first and the third are answered by the owner and land in ADR-0010 decision 6's addition of the same date, as two operation refusals under decision 1's criterion, `feature_already_created` and `no_feature_at_this_address`, judged exactly as this decision says: over the state the applied operations before them leave, so a create refused earlier in a batch leaves nothing held, and an operation other than a create after it on the same feature is refused in its own right while a second create of it is admitted. What a wire-legal geometry payload is stays MAP-70's. **An operation the log already holds, resent under a different mutation number, receives no new verdict**: it is answered with the one the log holds and is not projected again (PRD T2.3 as sharpened 2026-09-24, MAP-74), because this decision's premise is a batch of operations the server has not decided, and a second judgement of a decided one was measured contradicting the log it is kept on, including by projecting an operation decision 3 records as refused.

### 8. A per-operation refusal is one record per operation, and the event name is `flush.refused`

ADR-0011 section 4 fixes one record per **decision** and says that where a decision is genuinely per operation it gets a record per operation, naming the dedup drop as that shape today. This is the second. The closed event set of that section gains **`flush.refused`**, carrying `operation_ids` with its one identifier, the four correlation keys, and `reason`. It carries **no `status`**, which is that section's own rule: the response answered `200`, so no status was the refusal's to give.

**It is emitted after the commit, and that is this decision changing the category rather than an exception to ADR-0011's rule.** That section sorts a record by asking what it would be false about if the transaction vanished, and puts a refusal with the records that stay where they are taken, because a refusal was true whether or not anything committed. Decision 3 makes that false here: this refusal **is a write**, and a record emitted before the commit would assert a retention that may never exist, which is the failure the sorting test exists to catch. A refusal that decides nothing and writes nothing keeps the old position; this one moves with its write.

---

## Consequences

- **MAP-66 is unblocked and its tests need rework**, exactly as its parking note predicted: the cases asserting that a refused batch applies nothing at all pin a shape this decision removes for those two reasons.
- **MAP-22 inherits a clause**: the resync read filters on the verdict, or it streams refused operations to every other client as if they had happened.
- **MAP-37 inherits the mechanism** its flagged-at-flush clause needs, and adds a reason to the set rather than a new shape.
- **A client learns of a refusal once.** A resent batch is deduplicated, so the refusal is not repeated; a client that discards the response loses the report and not the operation, which stays on the log. The local handling, and whether the client marks its own queue entry, is MAP-15 and MAP-16's.
- **The client's optimistic preview of a refused operation is an I2 obligation, not a nicety.** The cursor passes the refusal, so nothing on the wire brings it up again; a client that keeps its preview holds a state the server will never hold, which is divergence with the sign reversed. MAP-15 and MAP-16 own it and this sentence is what names it as owed.
- **What a human does with a refused operation is not answered here.** The resolution surface is a PRD decision T5.2 already holds open, and retention of the refused entry falls under OQ-20 with the rest of the log.
- **The flush's write volume grows by the refused rows**, which is bounded by the batch bound N10 already declares and needs no new knob.
- **One migration and one rename cross four ecosystems' worth of prose**, and the freshness gate regenerates the Python envelope from the Rust one, so the verdict member exists once.
