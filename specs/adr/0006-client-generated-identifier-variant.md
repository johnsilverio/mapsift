# ADR-0006: The client-generated identifier variant

- **Status:** accepted (2026-08-04)
- **Deciders:** the owner, on the probes recorded below
- **Authority:** derives from `specs/mapsift-foundation.md` v0.17 (section 4, invariants I3 and I10) and `specs/PRD.md` v0.13 (M3, M4, T1.3, N5). Where this ADR and the foundation disagree, the foundation wins and this ADR is the one that is wrong.
- **Supersedes:** nothing. **Superseded by:** nothing.
- **Delivers:** MAP-2, and item 2 of the ADR agenda in `specs/dependencies.md` section 6.

---

## Context

Every feature, layer, operation and client instance carries an identifier the **client** mints, with no coordination and no server round trip, because an offline creation cannot wait for the server to name it (I3, M3). What was open is only the variant: a **random** 128-bit identifier, or a **time-ordered** one that carries a millisecond timestamp in its leading bits.

The case for time-ordered is index locality. Rows arriving in key order append to the right-hand edge of a B-tree and pack tightly; rows arriving in random order scatter across it. The case against is that the leading bits would be a **clock reading taken on the device**, and this product distrusts that clock in writing: I10 separates the client's `created-at` claim from the server's authoritative `applied-at` precisely because the field tablet's clock lies, and SP-1 tested a client a month out on its own clock as an ordinary case rather than an exotic one.

That framing hides the question that actually decides it, which nobody had asked: **the locality benefit assumes the clocks are right.** So it was measured with the clocks wrong.

---

## What was measured

Against **PostgreSQL 18.4** (`postgis/postgis:18-3.6`) in this project's compose stack, on **2026-08-04**, in a throwaway database. Three arms, **500,000 rows each**, inserted as **500 batches of 1,000** rather than one bulk statement, because the real write path is a flush of queued operations and a bulk build would sort the keys for free, which is the effect under test. Server settings recorded with the numbers: `shared_buffers` 128 MB, `full_page_writes` on, `wal_compression` off.

- **ordered:** `uuidv7()`, every clock perfect.
- **random:** `uuidv4()`.
- **skewed:** `uuidv7()` where **one row in five** is minted on a device whose clock is wrong by up to **thirty days** in either direction. This is the population this product actually has.

| arm | insert time | primary-key index | WAL written | leaf density | leaf fragmentation |
|---|---|---|---|---|---|
| ordered | 2.29 s | **15 MB** | 97 MB | **89.98 %** | 0 |
| random | 2.94 s | 19 MB | 104 MB | 71.87 % | 50.1 |
| **skewed** | 2.39 s | **37 MB** | 109 MB | **52.86 %** | 7.83 |

**The finding that decides this ADR: with realistic clock skew the time-ordered identifier is worse than random on its own metric.** Its index is **2.45 times** the size of the well-behaved ordered one and roughly **twice** the random one, and its pages end **half empty** (52.9 % against random's 71.9 %). The mechanism is visible in the density column: perfectly ordered keys append at the right edge and pack to 90 %, random keys spread evenly and settle near 72 %, and skewed keys do the worst of both, repeatedly splitting pages in a band that is being appended to and leaving the halves behind.

So the choice was never "ordered against random". It is **"ordered if every clock is right, against random always"**, and the first option's guarantee is one this product refuses to make anywhere else.

**Two honesty notes on the numbers, because a measurement without its conditions is decoration.**

- **The insert-time column is the weakest one here and is not what the decision rests on.** The whole dataset fit inside `shared_buffers`, which is the regime where random keys are cheapest, since no page had to be read back from disk. At a size where the index no longer fits in memory the random arm's penalty grows and the ordered arm's does not. The size and density columns are structural and do not depend on memory.
- **The skew arm is a model, not a census.** One row in five and thirty days are chosen as a plausible field population, not observed from real devices. The direction of the result is robust (any material skew destroys the packing); the exact multiple is not.

**A second property was measured rather than argued.** PostgreSQL 18 ships `uuid_extract_timestamp()`, and against a time-ordered identifier it returns the creation instant directly. Against a random one it returns nothing. A time-ordered identifier is therefore **not opaque**: it publishes when the thing it names was created, to anyone who can read it.

---

## Decision

### 1. The identifier is a random 128-bit value, generated on the client

Version 4 UUID, one canonical textual form across Rust, Python, TypeScript and Dart (M3), stored in PostgreSQL as the native 16-byte `uuid` type and never as text. The same mechanism produces the **clientID** of M4 and T1.3, which is a persistent installation identifier and never an author identity.

Four reasons, in the order of their weight.

**The locality argument does not survive this product's clocks.** Measured above: the benefit is contingent on a trustworthy clock, and the invariant that governs offline authorship already declares the client clock untrustworthy (I10). Choosing a variant whose only advantage evaporates under the exact condition the product designs for is buying a promise the product does not believe.

**M3 requires the identifier to be opaque, and time-ordered is not.** M3 says it carries no meaning, no ordering authority and no embedded permission. A time-ordered identifier carries a timestamp that `uuid_extract_timestamp()` reads out in one function call. Adopting it would mean writing a rule that the embedded time is never read as evidence, and then defending that rule forever against a field that visibly contains the answer. A property enforced by the shape of the data beats a property enforced by a paragraph.

**The privacy consequence is specific rather than theoretical.** Identifiers travel in URLs, exports, tile requests, and log lines, and N9 puts the operation identifier in **every** log line on the sync path by design. With a time-ordered identifier those logs would carry the creation instant of every captured vertex, and N5 already draws the line this crosses: a parcel vertex is the subject matter of the work, while the sequence of instants at which a person captured vertices in the field is that **person's whereabouts over time**. A random identifier keeps that out of the record by construction, which is cheaper than redacting it later on a path whose redaction rule already has enough to do.

**Nothing in the system needs the identifier to sort.** ADR-0004 gave the model a server-assigned **per-project version** as the resync cursor and a **per-feature version** for conflict detection, both monotonic and both authoritative. Ordering is a solved problem with an owner; the identifier does not need to take a second job it would do badly.

### 2. The cost is accepted with its mitigations named

Random keys scatter inserts across the index, and at a scale where that index no longer fits in memory the write path pays for it. Two mitigations are already decided elsewhere and are not new work:

- **The hot index is not the identifier's.** ADR-0005 makes every tenant-scoped index lead with `tenant_id`, and the isolation policy adds that predicate to every query, so the pages a working tenant touches are that tenant's range rather than the whole key space.
- **Writes arrive in batches, not one row at a time.** ADR-0004's flush allocates its version range in one statement and inserts the batch inside one transaction, so a flush of 500 operations pays one round of index maintenance rather than 500.

### 3. Where the identifier is generated, and what that binds

Generation lives in the Rust core (`libs/core`), so one implementation serves web, desktop and mobile (C11, 9.6.4). The `uuid` crate documents that **WebAssembly needs its `js` feature** in addition to the version feature, which is a build-configuration cost the random variant pays for randomness alone; the time-ordered variant would additionally depend on the host clock reaching into the core, which is the same clock this ADR just declined to trust. *(Documentary, from the crate's own documentation as read on 2026-08-04, rather than measured here.)*

The server **never** generates an identifier for an object a client can create offline, so no tenant-owned table carries a database-side default such as `gen_random_uuid()`; a default there would quietly make the server the allocator the moment a code path forgot to send one (M3). Server-generated defaults remain available only for rows the server alone owns.

### 4. What the migration and the tests inherit

The first migration (MAP-3) declares these columns as `uuid`. The test suite gets one case per rule that can be asserted rather than reviewed: two clients creating offline produce no collision (C3); an identifier is unchanged by a resend; no code path derives meaning, ordering or authority from an identifier's content; and an identifier belonging to a deleted feature is never reassigned (M3).

---

## Consequences

**What this buys.** The identifier keeps the one property M3 asked of it, opacity, enforced by the data rather than by a rule somebody has to remember. No creation timestamp leaks through a URL, an export or a log line. And the variant's behaviour does not depend on the correctness of a clock the rest of the architecture spends effort not trusting.

**What this costs.** Index locality on the identifier's own index, which is real and which this harness measured in the regime where it is cheapest. The mitigations in decision 2 are structural rather than additional work, and the honest position is that the cost is accepted rather than eliminated.

**What this forecloses.** Reading creation order from an identifier, which nothing may do anyway under M3. It does not foreclose a time-ordered **surrogate** for physical layout if a measured problem ever appears: that would be a server-assigned column, decided against numbers, and it would leave the identifier itself unchanged.

**What must be revisited, and when.** A measured insert or index-size problem at real volume, on real hardware, with the index exceeding memory. The answer at that point is **not** this ADR reversed, because the skew arm measured that road and it leads somewhere worse; it is a layout column, an index-maintenance policy, or partitioning. The other revisit condition, that the clients' clocks become trustworthy, is not expected: the device in question is the field tablet.
