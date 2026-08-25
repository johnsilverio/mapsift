# ADR-0013: The spatial read under the isolation policy

- **Status:** accepted (2026-08-24)
- **Deciders:** the owner, on the MAP-51 round (four research strands and the orchestrator's independent reproduction, all 2026-08-24)
- **Authority:** derives from `specs/mapsift-foundation.md` v0.18.1 (I4, I6, section 6's tiling gate, section 9's security posture, section 10's performance rule) and `specs/PRD.md` v0.16 (N1, N2, M2). Where this ADR and the foundation disagree, the foundation wins and this ADR is the one that is wrong.
- **Supersedes:** nothing. **Superseded by:** nothing. **Extends:** ADR-0005 decision 5, whose tenant-leading rule this carries one column further for a spatial read, and corrects the direction of that ADR's Consequences note of 2026-08-21.
- **Delivers:** the second acceptance clause of MAP-51 (the decision itself; its first clause, the test, is the implementation round that follows) and item 18 of the ADR agenda in `specs/dependencies.md` section 6.

---

## Context

I4 puts the wall in the database and ADR-0005 built it out of row-level security. PostgreSQL charges for that wall with a rule most of its users never meet: it will not use a qual as an **index condition** unless every function in that qual is declared `leakproof`, because an index condition is evaluated before the policy and a function that talks about its arguments would talk about rows the policy hides. Its own row-security chapter states the exception:

> This expression will be evaluated for each row prior to any conditions or functions coming from the user's
> query. (The only exceptions to this rule are leakproof functions, which are guaranteed to not leak
> information; the optimizer may choose to apply such functions ahead of the row-security check.)

No PostGIS predicate is leakproof. Measured on the running container 2026-08-24 (PostgreSQL 18.6, PostGIS 3.6.4, GEOS 3.14.1, PROJ 9.8.1): **zero of 776 PostGIS functions**, zero of 212 in `btree_gist`, all fourteen members of `gist_geometry_ops_2d`, and all twenty-one functions carrying `postgis_index_supportfn` report `proleakproof = false`. `geometry_overlaps` is not among those twenty-one, carries no support function of its own, and reports `false` as well; `uuid_eq` reports `true`.

So a bounding-box qual and the wall are mutually exclusive as shipped, and what that costs is not a slow query but a query whose **cost scales with how much the tenant owns rather than with how large the box is**. That reaches the tile path of ADR-0005 decision 6, which performs exactly this read as `mapsift_tile` with the policy applied, so foundation I6's per-tile budget sits on top of it. That is the read as it arrives, before decision 2 narrows the prefix from the tenant to the container; past that decision the cost is set by the size of the layer rather than by everything the tenant owns, and that is the form the tile path inherits (this ADR's decision 6).

MAP-51 opened this and named the candidate remedy: `ALTER FUNCTION st_intersects(geometry, geometry) LEAKPROOF`. One statement, which asserts something about the isolation wall this product sells, which is why it is an ADR rather than a migration somebody writes on the way past.

**The upstream position and the operational particularities of that statement are in `specs/dependencies.md` section 6 item 18**, verified 2026-08-24, with their quotes and their dates. They are cited here and deliberately not copied, because a second copy of a dependency finding is exactly what the survey exists to prevent. The short of it, for a reader deciding whether to open that item: PostGIS audited its own leakproof surface and excluded both candidate surfaces **by name**, leaving the broader review open; the marking is superuser-only, is silently reset by an extension upgrade, and is dropped by a non-binary `pg_dump`, which is the restore path N12 requires rehearsing.

**An earlier draft of this document argued the opposite conclusion and is superseded by measurement rather than by preference.** It proposed marking the twenty-one index-support predicates as a pair with a mandatory tenant-leading spatial index. The round that was commissioned to check its numbers measured a plan the draft had not tried, and the plan needs nothing marked. It also demonstrated, on the draft's own mandated index shape, the leak the draft had classified as theoretical. Both are below. The draft is not on this branch; what survives of it is its Context, its measurement discipline, and the record of what the assertion would have bought, which is kept here so nobody re-derives it from scratch.

---

## What was measured

Everything below was measured rather than read, on **PostgreSQL 18.6, PostGIS 3.6.4, GEOS 3.14.1, PROJ 9.8.1, on 2026-08-24**, single-process, against a **2,088,000-row fixture**: two tenants sharing one region, four projects each, four layers per project at 1,000, 10,000, 50,000 and 200,000 features, heap clustered by layer. Reads run as `mapsift_app` with the tenant bound under `FORCE ROW LEVEL SECURITY` and ADR-0005 decision 3's exact policy expression. The plan and the law were measured twice independently, once by a research strand and once by the orchestrator reviewing it.

### The plan that needs nothing marked

A read that names a **container** as well as the tenant puts both keys in the index condition with nothing marked:

```
Index Cond: ((tenant_id = (NULLIF(current_setting('mapsift.tenant_id'::text, true), ''::text))::uuid)
             AND (layer_id = '...'::uuid))
Filter: st_intersects(geometry, '...'::geometry)
```

`uuid_eq` is leakproof, so the container half of the condition is eligible. `current_setting` is not, and it does not need to be: the leakproof test governs a **user qual pushed ahead of the policy**, and this qual **is** the policy, which is why it reaches the `Index Cond` above rather than being held behind anything. Its argument is a literal setting name rather than a column, so it has no row to reveal either way.

**Across every unmarked container-scoped measurement the index entries visited equalled exactly what the reader owns, with zero foreign entries.** That is the same structural property the marking was being bought for: the foreign row is never fetched, so it is never handed to a predicate that could talk about it.

### The law: linear in the container prefix, independent of the box

Fitted across three decades of prefix size, at **0.035 buffers per prefix row**:

| prefix named | rows in the prefix | buffers | time |
|---|---|---|---|
| tenant only | 1,044,000 | 36,930 | 438 ms |
| tenant and project | 261,000 | 9,234 | 143 ms |
| tenant and layer | 50,000 | 1,789 | 17.2 ms |
| tenant and layer | 10,000 | 371 | 2.5 ms |
| tenant and layer | 1,000 | 50 | 0.24 ms |

The box does not appear in that table because it does not appear in the cost. A 200,000-feature layer costs **7,091 buffers at a z12 tile and at the whole world alike**.

### The four conditions the result depends on, and the fourth is the boundary

1. **Every spatial read names a container.** Without one the prefix is the tenant, which is the first row of the table.
2. **A `(tenant_id, project_id, layer_id)` btree exists.** It costs **15 MB at two million rows**, against 275 MB for the three-column GiST.
3. **The heap stays clustered by layer.** Scattered, the same reads cost **10 to 25 times the buffers**, and a 200,000-row layer becomes slower than a full sequential scan of the whole two-million-row table.
4. **The layer stays small**, because the cost is linear and unbounded in it.

### Where it stops, as a number rather than as a worry

A served layer is by M2's construction the large case. At **200,000 features a tile costs 126 ms**. The million-row point is measured directly rather than extrapolated: it is the tenant-scoped row of the same sweep, **36,930 buffers and 438 ms**.

### The covering index is disqualified rather than merely expensive

`INCLUDE (geometry)` on that btree removes the heap-locality penalty of condition 3 entirely, and costs **550 MB against a 563 MB heap**. It then **refuses the write**: a feature above roughly **260 vertices** fails at `INSERT` with `index row size exceeds btree version 4 maximum 2704`. A watercourse preservation-area polygon or a rural-registry perimeter reaches that routinely.

### What the assertion would have bought, recorded rather than argued

Marked, the cost becomes **O(answer)** instead of O(prefix), and the two cross where the box selects about **3.5% of the prefix**. Below that the marking wins by orders of magnitude. Above it the container prefix wins, and the inversion is not marginal: at low zoom on a 200,000-feature layer the **unmarked container read beat the earlier draft's own chosen index shape, 7,091 buffers against 33,719**.

### The residual the refusal closes

`st_intersects(geometry,geometry)` ships with a declared cost of **5000**, and at that cost the policy expression is cheaper and sorts first, which is why the earlier draft classified the leak below as unreachable. With the declared cost forced to 1 so the channel is exercised at its limit, **marked**, on a schema carrying **the earlier draft's own mandated index**, on a wide-box sequential scan, the read answers `ERROR: Unknown geometry type: 13 - PolyhedralSurface` (2026-08-24). That is a hidden row's geometry type reaching a reader entitled to nothing in that box, through the product's ordinary bounding-box read, with no injection and no privilege. What stood between it and production was an upstream performance heuristic.

**With nothing marked, `st_intersects` is never eligible ahead of the policy on any plan**, that sequential scan included. A handed-over reading from the research round, recorded as a reading because this document did not verify its source: the published attack on this channel also requires a **pushable leakproof predicate**, so it does not reach the unmarked configuration on the geometry qual.

---

## Decision

### 1. The leakproof assertion is refused

**Neither `st_intersects` nor `geometry_overlaps` nor any other PostGIS predicate is marked `LEAKPROOF` by this product**, on any connection, in any database, by migration or by provisioning. This is a decision not to do something, and it is taken rather than deferred.

Four things carry it, and the first alone would be enough.

**The assertion is formally false.** PostgreSQL's own `CREATE FUNCTION` reference, version 18:

> LEAKPROOF indicates that the function has no side effects. It reveals no information about its arguments
> other than by its return value. For example, a function which throws an error message for some argument
> values but not others, or which includes the argument values in any error message, is not leakproof.

`st_intersects(geometry,geometry)` does both halves of that, on four error surfaces, two of which name the argument's SRID as well as its geometry type (2026-08-24).

**The conditional form of it was demonstrated to fail on its own terms.** The earlier draft's answer was that the throw is unreachable while the index condition carries the tenant key. On a plan with no index condition the guarantee has nothing to stand on, and that is not a hypothetical plan: it is what a wide box gets. Measured on a schema carrying the draft's own mandated index, marked, with the declared cost forced to 1, the leak fires and names a hidden row's geometry type. The remaining protection was upstream's cost model, which is a number this product does not own and which the draft's own test would only have watched rather than held.

**Upstream is on the other side of the question and its review is open.** PostGIS excluded both candidate surfaces by name and left the broader review outstanding (`specs/dependencies.md` item 18). Asserting on behalf of a project that declined to assert about the same functions is signing over somebody else's code with less knowledge of it than they have.

**It does not survive the paths the product must rehearse.** The marking is superuser-only, an extension upgrade silently resets it, and a non-binary `pg_dump` drops it, so it survives the upgrade path that gets tested and vanishes on the restore path N12 requires rehearsing (item 18). A security property that is present in the tested environment and absent in the restored one is worse than no property, because it is believed.

**And it is not needed**, which is decision 2. The structural property the marking was being bought for is available with nothing asserted.

### 2. The container-scoped spatial read is the sanctioned shape

**A spatial read on a tenant-owned table names a layer, a layer set, or a project as well as the tenant.** The index condition is then built entirely from `uuid_eq`, which is already leakproof in core, and the geometry predicate stays behind the policy as a heap filter where it belongs.

The security half is stated plainly, because it is what the refusal buys. With nothing marked, a spatial read that reaches production **without** its container is slow and closed. It is never fast and open. Under the refused assertion the same omission would have been an isolation defect; here it is a performance defect. That asymmetry is the decision, and the rest of this ADR is the price of it.

The performance half is the law above: cost linear in the container prefix and independent of the box, which is the right shape for the map, where a reader zoomed into one layer pays for that layer and not for everything the tenant owns.

**The tile path takes the same shape and cannot take a different one.** ADR-0005 decision 6 hands whichever tile server wins a read of the same tables under the same policies, so the same plan applies. What decision 6's contract does not yet say is that its function source must name the container as well as carry the verified tenant. That clause is owed to the fan-out and is named in the Consequences rather than written here, because this ADR touches one file.

### 3. The result is conditional, and the four conditions are part of the decision

The four measured conditions above are part of the decision rather than observations recorded beside it, because a positive result whose conditions are unwritten is a result that decays without anybody noticing. They do not all carry the same status, and the difference is written out rather than left to be inferred.

Conditions 1 and 2 are enforced, and decision 4 says by what. Condition 3, the heap staying clustered by layer, has **no operational answer in this product today**, and this ADR does not invent one: it is named as a revisit trigger with its measured penalty, so the first deployment that meets it meets a documented risk rather than a mystery. Condition 4, the layer staying small, is where the shape stops, and decision 6 says what answers it.

### 4. What enforces the container obligation, and the guarantee each gate actually gives

**This obligation is a rule on every call site, and that is the same objection the earlier draft used to reject its own narrow alternative.** Refusing that alternative for moving the guarantee to every call site and then replacing it with something that also lives at every call site would be one standard for the rejected option and another for the chosen one. So the standard is applied here, and it is applied honestly: what separates the two is **not** enforceability, since the same class of gate is available to both. What separates them is the direction the omission fails in (slow and closed here, slow and open there), and that the narrow alternative additionally needed the tenant-leading index anyway and rested on a premise nobody measured.

Three mechanisms, in descending order of what they actually guarantee.

**A seam, so the ordinary shape cannot omit the container.** The spatial read is published as a selector under ADR-0007 that takes the container as a **required argument**. There is no spatial read in the application that does not, so the ordinary caller cannot express the unqualified form; it is not a rule the caller remembers. This is the same move ADR-0005 decision 3 makes by binding the tenant once per request and ADR-0011 makes by putting redaction on the logging path.

**A catalogue case, by construction.** Every tenant-owned table carrying a geometry column carries a btree whose leading columns are the tenant and the container keys, asserted from the catalogue in the shape ADR-0005 decision 7 established, so a table that gains a geometry column without one fails the build the way a table added without a policy already does. This gate is total for what it covers, because the catalogue cannot hide a table from it.

**A source gate, and its guarantee is stated rather than wished for.** No spatial lookup or spatial SQL outside the seam module. ADR-0002 section 5 fixes the three rules a gate of this class lives by, and the third is the one that matters here: state the guarantee it gives rather than the one the author wants. **It catches the ORM spatial lookup**, which is the shape that arrives by accident, since `__intersects` and its siblings are one word a developer adds to a filter without thinking about plans at all. **It does not catch** a predicate assembled in raw SQL through a cursor, nor one built dynamically. That residual is not closed, and it is not closed because it fails slow rather than open.

**What happens when the enforcement is absent** is therefore the load-bearing sentence and is written out: the read scans the tenant's whole prefix, costs 438 ms at a million rows (2026-08-24), and returns the correct answer. It is a defect with a performance symptom, which foundation section 10 grades as a defect rather than as a tradeoff, and it is not a hole in the wall.

### 5. The test, extending ADR-0005 decision 7's list with cases 7 and 8

Cases 1 to 6 stand unchanged. Both new cases are **by construction rather than by diligence**, in the shape decision 7 established.

7. **From the catalogue.** Enumerate every function belonging to a PostGIS extension and every function this product defines, and assert that none reports `proleakproof = true`, so a marking added by hand on a live database fails the build; and every tenant-owned table carrying a geometry column carries a btree whose leading columns are the tenant and the container keys. Core's own markings are outside this case and have to stay outside it: `uuid_eq` is marked in core (2026-08-24) and decision 2's entire plan rests on that, so a case widened to the whole catalogue would fail the build on a clean install and would be refusing what this ADR depends on.
8. **From the plan.** A bounding-box read through the published seam, bound to a tenant, with the policy in force, witnesses the **plan** and not the rows: the index condition carries the tenant and the container and is built only from `uuid_eq`, and the number of index entries visited equals the number the reader owns. MAP-51's own acceptance names the trap this closes, "a test that asserts only the returned rows passes for the wrong reason here", and it is the same trap ADR-0005's append-only addition met on 2026-08-07, where asserting that nothing changed passed for the wrong reason under two different causes.

### 6. Where the container prefix stops is foundation section 6's tiling gate, not a security decision

A served layer is the large case by M2's construction, and the cost is linear and unbounded in layer size. At 200,000 features a tile costs 126 ms and at a million rows the same shape costs 438 ms (2026-08-24). No index shape fixes that, and the marked plan does not either: at low zoom the marked read was measured **worse** than the unmarked container read, 33,719 buffers against 7,091, because O(answer) is no bargain when the answer is the layer.

**So the answer past the prefix is pre-generated tiles plus merge-on-demand, which foundation section 6 already decided and gated.** Its trigger is dynamic MVT ceasing to be responsive at real feature counts, expressed as I6's per-tile budget. This ADR does not declare that trigger fired, because I6's value is set by measurement and that measurement is still owed (PRD N1's open clause, PRD section 10.5). What this finding does is tell the product **where** the gate will fire and **why it arrives earlier than anyone had written down**: the per-tile cost on the served path is set by the size of the layer rather than by the contents of the tile, so it does not improve as the user zooms in. The numbers above are the first ones a per-tile budget can be set against, and the crossing itself is measured under the N1 protocol with its device, versions, fixture and date.

**A further loosening of the wall is not the next lever, and this decision closes that door rather than leaving it ajar.**

### 7. The two alternatives that lost, with their numbers

**Marking only `geometry_overlaps` and writing every spatial filter as an explicit `&&` conjunction.** It is a much smaller assertion: `geometry_overlaps` declares a cost of 1, compares cached bounding boxes, and could not be made to raise across eleven inputs, which is a negative result from eleven attempts and not a proof. It carries no support function, so unlike the twenty-one it can become an index condition directly rather than through a rewrite. It loses because it buys a smaller assertion and not a smaller mechanism: it still needs the container prefix to keep foreign entries out of the scan, so it is decision 2 plus an assertion, and decision 2 alone is decision 2 with no assertion. Its own premise, that a clause written as `&&` from the start takes its index condition from a marked `geometry_overlaps`, was measured on neither side and would need its own probe.

**A covering index, `INCLUDE (geometry)` on the container btree.** It is the clean answer to condition 3 and removes the heap-locality penalty entirely, at 550 MB against a 563 MB heap, which is a price worth discussing. It is disqualified rather than priced, because it **refuses the write**: a feature above roughly 260 vertices fails at `INSERT` with `index row size exceeds btree version 4 maximum 2704`, and the geometry this product exists to hold reaches that routinely.

---

## Consequences

**What this buys.** The tenant-scoped spatial read stops scaling with everything the tenant owns and starts scaling with the container the user is actually looking at, at 0.035 buffers per prefix row (2026-08-24), and it does so with **nothing asserted about anybody's code**. The foreign row is kept out of that read's index scan structurally rather than by a cost estimate, which is the property the assertion was being bought for. The product signs no claim it would have to defend, inherits no marking to re-apply after an upgrade, and loses nothing on a restore. And the failure mode is slow, never open, on the **qual** path this decision governs: an unqualified bounding-box read scans the tenant's whole prefix and still answers only what the reader owns. The **ordering** path is the measured exception and is recorded rather than smoothed over. The leakproof gate applies to quals and not to `ORDER BY` pathkeys, so a nearest-neighbour ordering takes the plain GiST on `layers_feature.geometry` with nothing marked and visits index entries belonging to a tenant the reader cannot see (`Rows Removed by Filter: 4`, measured 2026-08-24 after this document was drafted), with the tenant comparison left as a filter above the ordering. Nothing is handed to a throwing predicate there, so the refusal still closes what it claims to close, the error surface and the plan-choice channel on the geometry qual. Whether the ordering path wants an answer of its own is a later round's question and not this document's.

**What this costs, and who pays.**

- **Every spatial read pays a required argument, and the developer writing one pays it.** There is no sanctioned unqualified spatial read. The gate that holds the ordinary shape catches the ORM lookup and does not catch raw SQL, so the residual is real and is named in decision 4 rather than implied away.
- **A genuinely tenant-wide spatial read costs what the first row of the table says**, 36,930 buffers and 438 ms at a million rows (2026-08-24). It is not a sanctioned shape, and that number is what one costs when it reaches production past the residual of decision 4. The product pays it as a limit on any future capability that wants to search a tenant's whole holdings spatially, which has to be built out of container-scoped reads rather than out of an unqualified one, and that limit is stated here so it is designed around rather than discovered.
- **The write path pays a wider btree**, which is the cheap half and is said as such: 15 MB at two million rows.
- **The operator pays a clustering obligation the product has no answer for.** Scattered, the same reads cost 10 to 25 times the buffers and a 200,000-row layer loses to a sequential scan of the whole table. Nobody is assigned to it today, and revisit trigger 3 is where it lives rather than a sentence somebody hopes is read.
- **The served path pays a ceiling.** 126 ms a tile at 200,000 features, unchanged by zoom. That is the tiling gate's bill and not this decision's to reduce.
- **The product gives up the marked plan below 3.5% selectivity**, where it would have won by orders of magnitude. Because the unmarked cost is independent of the box, that loss lands wherever the prefix is large and the box is small: at 200,000 features a tile pays the layer's 126 ms rather than the answer's (2026-08-24). Where the prefix is small there is little to give up, the 1,000 to 50,000-row layers costing 0.24 to 17.2 ms whatever the box selects, and the large layer is where the tiling gate takes over anyway.
- **The implementation round pays two tests, one index change and one seam**, and the fan-out round pays several documents, listed below.

**What this forecloses.**

- **Marking any PostGIS predicate `LEAKPROOF` in this product**, by any role and through any path, and with it the O(answer) plan and everything below the 3.5% crossover.
- **The unqualified spatial read.** A bounding-box read naming only the tenant is not a sanctioned shape, whatever it costs.
- **The covering index**, refused on a write failure rather than on price.
- **The composite `(tenant_id, geometry)` under `btree_gist` as the remedy for this problem.** What the read needs is a btree with no geometry in it at all. That is a correction owed to MAP-5's spec section 3 and is named below rather than made here.
- Nothing else. The tile server product, the native kit, ADR-0005's wall, the permission model above it, and foundation section 6's tiling gate are all untouched, and the last of those is pointed **at** rather than closed.

**What must be revisited, and when.**

1. **PostGIS completing the function-by-function review its own ticket leaves open** (`specs/dependencies.md` item 18). A future release could ship the marking as something **inherited rather than asserted**, which changes the question this ADR answered: the claim would be upstream's, and by the mechanism item 18 records the two operational particularities largely dissolve with it, since a marking emitted by the extension's own definitions travels through `CREATE OR REPLACE` and through a restore. Reopen then, and re-measure rather than assume, because the crossover above is a property of this fixture and this schema. **PostgreSQL learning to scope `LEAKPROOF`, by role or by access method, does not reopen this**: what was refused is a claim about the function, not a question of who benefits from it.
2. **A served layer measured past the container prefix.** That is foundation section 6's gate to pre-generated tiles plus merge-on-demand, triggered by I6's per-tile budget under the N1 protocol with its device, versions, fixture and date. It is that decision arriving, not this one reopening, and decision 6 is written so a reader in that moment knows which document moves.
3. **The heap-clustering obligation, which has no operational answer today.** The trigger is the first deployment whose heap scatters, or the first measurement showing the 10-to-25-times penalty on real data. What answers it (an offline `CLUSTER`, a repack-class tool, partitioning by layer, or accepting the penalty and moving the gate of trigger 2 forward) is its own decision with its own cost and is deliberately not taken here.
4. **The element budget.** M2 makes the element layer the small case and the served layer the large one, and the container law is linear in layer size, so the element path sits comfortably inside this shape today. The element budget is still unmeasured (PRD N1, M2). If it is ever set high enough that an element layer reaches these numbers, condition 4 binds the element path too and this ADR is reopened with it.

**What the fan-out owes, named here and deliberately not run here.** ADR-0005's Consequences correction of 2026-08-21 is wrong in the direction that matters and needs a dated note: its conclusion that leading with the tenant "narrows nothing" holds only for a read that names nothing below the tenant, and the shape it evaluated, the composite `(tenant_id, geometry)`, is not the shape that works. ADR-0005 decision 6's tile contract gains the container clause of decision 2. MAP-5's spec section 3 loses its composite-adoption trigger, which named an index this ADR does not adopt. **A correction to this document's own first reading of the same file, measured 2026-08-24 after it was drafted:** the plain GiST on `layers_feature.geometry` **is** scanned under the policy, by the ordering path recorded above, which makes it the only path a nearest-neighbour query has. It is not idle write maintenance, and the reason this ADR would otherwise have handed MAP-5 for dropping it is withdrawn. `specs/dependencies.md` item 18 is closed by this ADR and owes the line that says so, since it still reads as the open question this ADR answered. MAP-51's issue body still frames the marking as the candidate remedy. And `specs/index.md` and `specs/log.md` carry this document the way they carry the other twelve. The fan-out is a later step of this round, and running it from inside the document that caused it would propagate prose nobody has read adversarially yet.
