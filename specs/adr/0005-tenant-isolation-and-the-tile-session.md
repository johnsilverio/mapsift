# ADR-0005: Tenant isolation, the database roles, and the tile path's session wiring

- **Status:** accepted (2026-08-04)
- **Deciders:** the owner, on the probes recorded below
- **Authority:** derives from `specs/mapsift-foundation.md` v0.17 (section 9, invariant I4) and `specs/PRD.md` v0.12 (T6.1, T6.5, N2, M1). Where this ADR and the foundation disagree, the foundation wins and this ADR is the one that is wrong.
- **Supersedes:** nothing. **Superseded by:** nothing.
- **Delivers:** MAP-1, and item 1 of the ADR agenda in `specs/dependencies.md` section 6; section 8 (added 2026-08-05) delivers the MAP-27 decision.

---

## Context

I4 puts the wall in the database rather than in the ORM, and the reason is its own scar: the tile server reads PostGIS directly, so an ORM-level tenant filter leaves that path wide open. PRD T6.1 left the mechanism open between row-level security and per-tenant views, and left the tile role's session wiring open beside it. The first migration settles both whether or not anybody writes them down, and a migration is the one artifact in this stack that is expensive to take back, which is why this ADR lands before the account tree exists.

The choice was decidable because the defeat conditions are documented and testable, so they were **measured rather than argued**. What follows is what a real connection to a real cluster actually did.

---

## What was measured

Against **PostgreSQL 18.4** (`postgis/postgis:18-3.6`) in this project's own compose stack, on **2026-08-04**, in a throwaway database created and dropped inside the run. Four **real login roles** were used rather than `SET ROLE`, so each result is what an actual connection does. The candidate policy under test was `tenant_id = current_setting('mapsift.tenant_id', true)::uuid`, on a three-row table holding two tenants.

| # | What was run | Result |
|---|---|---|
| A | plain role, parameter never set | **0 rows**, fail closed |
| B | `set_config(..., true)` inside the transaction | 2 of 3 rows, the tenant's own |
| C | same session, next statement, nothing set | **`ERROR: invalid input syntax for type uuid: ""`** |
| D | `set_config(..., false)`, then a later transaction | **2 rows**, the setting survived the transaction |
| E | after `REVOKE SET ON PARAMETER ... FROM` the role | the role **still sets it**; `pg_parameter_acl` is empty |
| F | insert a row for another tenant while bound | `new row violates row-level security policy` |
| G | `SECURITY DEFINER` function owned by the table owner, RLS enabled and **not** forced | **3 rows** against the invoker's 2 |
| H | insert a child row whose foreign key points at another tenant's row | **accepted** |
| I | insert a primary key that exists in another tenant's invisible row | `duplicate key value violates unique constraint` |
| J | the **table owner**, RLS enabled and **not** forced | **3 rows** |
| K | the same owner after `FORCE ROW LEVEL SECURITY` | 2 rows, and G's definer drops to 2 with it |
| L | a role holding **`BYPASSRLS`**, after FORCE | **3 rows** |
| N | the same reference as H through a composite key `(tenant_id, id)` | foreign-key violation across tenants, success within one |

**Five findings came out of that, and each one changed the design.**

**The empty-string trap (C), which is the one nobody expects.** A transaction-scoped setting does not revert to *unset* when the transaction ends. It reverts to the session value, which for a custom parameter nobody has set is the **empty string**, and `''::uuid` throws. So the obvious policy expression works perfectly on the first transaction of a connection and raises a type error on every one after it, which is a failure that appears only on a **pooled or persistent connection** and looks like a broken database rather than a broken policy. The fix is `nullif(current_setting('mapsift.tenant_id', true), '')::uuid`, and it is not cosmetic.

**The leak has a shape and it is the session-scoped write (D).** Django keeps a connection open across requests under `CONN_MAX_AGE`, and the psycopg pool hands a connection to the next client in idle state without clearing session state, its own documentation putting that cleanup in an application-supplied `reset` callback. Django's manual says the same thing in the other direction: if you modify connection parameters you must restore them, force them per request, or stop reusing connections. A session-scoped tenant binding therefore reaches the **next request on that connection**, which may belong to another tenant. A transaction-scoped binding cannot, because the transaction is over before the connection is reusable.

**The parameter is a binding, not a capability (E).** An unprivileged role sets the tenant parameter to whatever it likes, and there is nothing to revoke, because a custom two-part parameter is a placeholder that the server accepts from anyone and `pg_parameter_acl` holds no entry for it. So row-level security stops **a query** from crossing a tenant boundary; it does not stop **code that can execute arbitrary SQL on that connection** from re-binding the tenant first. That is the honest edge of what this wall buys, and it is why parameterised statements on the binding path are a security control here rather than a style preference.

**Referential integrity is a hole in the wall, and it is documented as such (H, I).** PostgreSQL states that referential integrity checks always bypass row security to keep data integrity, and the probe shows what that means in practice: a row in one tenant successfully referenced a row in another, and a primary-key collision against an invisible row reported itself. Both are cross-tenant channels that no policy closes. **A composite key closes the first one completely (N)** and costs one unique index per table.

**FORCE is what makes the whole thing true, including in tests (J, K, G).** The owner bypasses its own policies by default, which also means a `SECURITY DEFINER` function owned by the owner bypasses them, and `FORCE ROW LEVEL SECURITY` closes both at once. This matters beyond production: migrations and the test database are created by the owning role, so **without FORCE the entire test suite would run outside the wall it is supposed to prove**.

---

## Decision

### 1. Row-level security, and per-tenant views are rejected

The wall is `ENABLE ROW LEVEL SECURITY` plus `FORCE ROW LEVEL SECURITY` plus one policy per tenant-owned table, keyed on the tenant identifier that M1 already puts on every row.

Per-tenant views lose on three counts. They need **DDL for every new tenant**, which turns creating a personal account into a schema migration and contradicts M1's shape, where a freelancer's account is a tenant like any other. A view protects **reads** and protects writes only with `WITH CHECK OPTION`, while a policy carries `USING` and `WITH CHECK` in one object that a catalogue query can verify. And a single parameterised view, the version that avoids per-tenant DDL, is row-level security with the guarantees removed, since any role holding privileges on the underlying table reads straight past it.

### 2. Four roles, none of them privileged

- **`mapsift_owner`** owns the schema, the tables and the policies, and runs migrations. `NOSUPERUSER`, `NOBYPASSRLS`, and subject to its own policies because of FORCE.
- **`mapsift_app`** is the Django runtime. It owns nothing, holds `SELECT, INSERT, UPDATE, DELETE` on the tenant-owned tables, and has no `CREATE` on the schema.
- **`mapsift_tile`** is the direct-to-PostGIS reader. It owns nothing and holds `SELECT` plus `EXECUTE` on the tile functions, nothing more.
- **`mapsift_tokens`** owns the tile capability key and the function that verifies it, and holds **no privilege on any data table**, so the one role that can read the signing key is the one role that cannot read a feature.

Superuser is used once at provisioning for `CREATE EXTENSION postgis` and by no application, ever. **No role in this system is granted `BYPASSRLS`**, and the migration that would grant it is a defect rather than a shortcut (L).

Two connection profiles select the role from the environment: **migrate** connects as the owner, **runtime** connects as the application role. Tests and CI use the owner profile, which is safe **only** because of FORCE, and that is the second reason FORCE is not optional.

> **Addition (2026-08-07), at the MAP-10 pickup: `mapsift_app`'s grant is per table, and the append-only log is the first table that takes less than the full set.** The bullet above states the grant `mapsift_app` holds on **the tenant-owned tables** as one shape, which was true while every such table was a mutable projection. PRD M15 makes the operation log **append-only**, and its acceptance asks for that to be asserted by a test. A test is the weaker instrument here for the reason this ADR already argues about the wall itself: **`SELECT, INSERT` and no `UPDATE, DELETE, TRUNCATE`** makes the guarantee true by construction at the same layer the isolation is, so the runtime path cannot rewrite an entry however the application code is later refactored, rather than only on the code paths somebody remembered to cover. **`TRUNCATE` is named because it is a separate privilege and row-level security does not apply to it**, so a role holding it empties every tenant's entries in one statement while `UPDATE` and `DELETE` stay absent; a grant assertion that enumerates four privileges and calls itself the whole grant misses exactly the one that defeats append-only. The privilege set is independent of row-level security, so the log still carries its policy and its tenant column like any other tenant-owned table; this narrows what the role may do, it does not exempt the table from the wall.
>
> **What this does not reach, corrected 2026-08-07 the same day the addition was written, because the first version of this paragraph claimed it did.** It said the rewrite was refused "for every caller including a migration data-fix and a psql session", which is **false and was measured false**: on `layers_feature` this cluster reports `mapsift_owner` holding `UPDATE`, `DELETE` and `TRUNCATE`, because a table's owner holds them implicitly and a `REVOKE` aimed at `mapsift_app` never reaches it. Migrations connect as the owner (decision 2), and so do the tests and CI. **So the guarantee is the runtime path's, and the owner profile is outside it.** Extending it to the owner is a separate and more expensive decision (an event trigger, or a log owned by a role nobody migrates as) and is deliberately not taken here. The error is recorded rather than quietly rewritten because it is the third instance this week of a measurement generalized past the configuration it was taken in.
>
> **The trap it creates, and it is section 4's silence generalized:** a refused in-place write surfaces as a *permission* error rather than a logical one, so a test that asserts append-only must distinguish the grant denying it from a statement that simply matched no rows. Asserting only that nothing changed passes for the wrong reason under both.

> **Addition (2026-08-10), at the MAP-11 pickup: the per-project version table is the counter-example to the addition above, and it takes `UPDATE`.** The log narrowed its grant because rewriting an entry is the one thing it exists to prevent. The ADR-0004 version row is the opposite shape: its normal operation **is** an in-place increment, so `mapsift_app` holds `SELECT, INSERT, UPDATE` on it and anything narrower stops a flush from running at all.
>
> This is written here rather than left for a reviewer to infer, because after 2026-08-07 a grant carrying `UPDATE` reads against this repository's newest habit, and somebody will eventually flag it as the defect the log's grant was. **The two guarantees do not touch:** different tables, and the log's privileges are unchanged by this.
>
> **What the pair establishes is the rule the bullet above did not carry: the grant is decided per table by what that table guarantees.** A new tenant-owned table states its own set rather than inheriting the sentence about "the tenant-owned tables", and the version table is the second table to exercise that, in the opposite direction from the first.

### 3. The tenant binding is transaction-scoped, parameterised, and guarded against the empty string

The first statement inside the transaction that serves a request or a background task is

```sql
SELECT set_config('mapsift.tenant_id', %s, true)
```

with the tenant passed as a **parameter and never interpolated into the string**, and with `is_local` **true**, always. A session-scoped binding (`SET`, or `is_local` false) is prohibited by name, because measurement D shows exactly where it lands. The binding is made **once per request and once per background task**, in the same place N9 binds the correlation keys, rather than by each caller remembering.

Every policy reads the parameter through the guarded cast:

```sql
USING      (tenant_id = nullif(current_setting('mapsift.tenant_id', true), '')::uuid)
WITH CHECK (tenant_id = nullif(current_setting('mapsift.tenant_id', true), '')::uuid)
```

`current_setting` is stable, so the expression is evaluated once per query rather than once per row. A policy expression never calls a volatile function.

### 4. The wall is silent by construction, so the application fails loudly beside it

An unbound transaction returns zero rows, which is indistinguishable from a tenant that owns nothing. That silence is correct for a wall and wrong for a product whose rule is that nothing fails silently (N9, N12). So both exist: **row-level security denies, and the application refuses to run a tenant-scoped query with no binding in force**, raising rather than returning an empty result. The wall is the guarantee; the guard is the signal.

### 5. Every reference and every natural key between tenant-owned rows is composite

A foreign key between two tenant-owned tables is declared over `(tenant_id, <key>)` and the referenced table carries the matching `UNIQUE (tenant_id, id)`, which is what probe N closes and probe H proves is otherwise open. Any **natural** unique key (a name, a slug, a code) is unique **per tenant** and never globally, because a global unique index answers questions across the wall (I). The synthetic identifier of MAP-2 stays globally unique, and its collision oracle is not reachable in practice against a 128-bit identifier, which is a property of that ADR rather than of this one.

Every index that serves a tenant-scoped query **leads with `tenant_id`**, because the policy adds that predicate to every query on the table. That is structural performance under foundation section 10, so it is free at design time and not optional.

### 6. The tile path's contract, which binds whichever tile server wins

The tile server choice stays its own ADR, gated where ADR-0001 section 8 left it. What this ADR fixes is the contract that choice must satisfy, and a candidate that cannot satisfy it is not adopted whatever else it offers:

1. it connects as **`mapsift_tile`**, which owns nothing and holds neither superuser nor `BYPASSRLS`;
2. the tenant reaches the session **inside the same transaction that serves the tile**, from a claim **the database verifies**, never from a raw identifier a client put in a URL;
3. an absent, expired or unverifiable claim **raises**, and never returns an empty tile, because an empty tile is a wrong answer and a wrong answer presented as data is the silent-discard sin wearing a different hat (N12).

**The mechanism that satisfies it today**, recorded against Martin's documentation as read on 2026-08-04 rather than from memory: a Martin function source receives `z`, `x`, `y` and a `query_params json`, **and nothing else**, with no headers, no token and no identity of its own. So the claim travels in the query string as a **short-lived signed capability** that the API tier mints after it has authenticated the user and resolved the tenant. The tile function is `SECURITY INVOKER`; its first act is to call the verifier owned by `mapsift_tokens`, which checks the signature and the expiry and returns the tenant or raises; it then binds the tenant with the transaction-scoped `set_config` of decision 3 and only afterwards touches a table, where the policies apply exactly as they do for the API.

Two alternatives were considered and are recorded with their reason. **A connection pool per tenant** dies on the tenant population M1 describes, where most tenants are personal accounts, so connections would grow with the customer count. **An authenticating proxy in front of the tile server** cannot help, because there is no way to carry a session variable over HTTP into somebody else's pooled connection; the claim has to reach the database as data, which is what mechanism 2 does.

### 7. What the first migration carries, and the test that proves it

The migration that creates the account tree (MAP-3) carries, in the same change: the roles and grants of decision 2, `ENABLE` **and** `FORCE ROW LEVEL SECURITY` on every tenant-owned table, one policy per table using the guarded expression of decision 3, and the composite unique keys and foreign keys of decision 5. It cites this ADR by number.

> **Correction (2026-08-04), found while implementing MAP-3 and recorded rather than silently worked around.** The sentence above asks for something **impossible** in one of its four parts: the migration cannot create `mapsift_owner`, because that is the role which **runs** the migration and must therefore exist before it, and because a role that logs in needs a credential while a migration is tracked in git and a credential is not (N3, C6). The roles therefore split by what each one needs, and the split is the correction rather than a preference. **`mapsift_owner` is born in provisioning**, beside the extension and the database itself, where a credential can be supplied from the environment. **The three runtime roles are born in the migration**, `NOLOGIN` and with no credential at all, because what the schema owes them is grants rather than a way in; deployment gives a role its login and its password when it gives it a home. Everything else in decision 2 stands untouched, including the part that matters most: none of the four is privileged and none holds `BYPASSRLS`. This is a correction to an operative instruction that could not be executed, not a change of decision, so it is recorded here rather than in a superseding ADR.

The test PRD N2 requires is **by construction rather than by diligence**, and it now has five cases the probes wrote for it:

1. enumerate every tenant-owned table from the catalogue and assert `relrowsecurity` **and** `relforcerowsecurity` are both true, so a table added later without a policy fails the build;
2. assert that no role used by any application holds `BYPASSRLS` and that no application role owns a tenant-owned table;
3. a query with no binding in force returns nothing **and** the application guard raises;
4. a write bound to one tenant cannot create, read, update or delete a row of another, including through a foreign key to a row it cannot see;
5. the tile path is exercised as the tile role with a forged and with an expired claim, and both are refused rather than served an empty tile.

**Which tables are inside the wall.** Every row that belongs to a tenant, per M1, which includes `tenant` itself, `membership`, `workspace`, `project`, `layer` and `feature`. The **global user** record is deliberately outside it, because a user spans tenants by design (M1) and its confidentiality is the permission layer's job rather than a second wall.

### 8. The login question: a second permissive policy on `membership`, keyed on the authenticated user

> **Added (2026-08-05, owner decision, MAP-27), under the revised ADR convention (ADR-0001).** A new decision in the ADR that owns the wall, because a reader who opens this document must not conclude the wall forbids the login path's first question. Decisions 1 to 7 stand untouched.

**The question this answers.** "Which tenants does this user belong to" is the first question the login path asks, and it is cross-tenant by nature: at login there is no tenant to bind, because choosing one is what the answer is for. `membership` is inside the wall, so the tenant-keyed policy of decision 3 answers nothing before a tenant is bound. PRD M1 makes the user the global identity that may belong to several tenants, so the question is legitimate, and it is the only legitimate question of that shape.

**The mechanism.** `membership` gains a second **permissive** policy, **`FOR SELECT` only**, keyed on a second parameter bound beside the tenant:

```sql
USING (user_id = nullif(current_setting('mapsift.user_id', true), '')::uuid)
```

Permissive policies on one table combine with `OR`, PostgreSQL's own rule, so the tenant policy answers exactly as it does today and this one adds exactly one thing: the session user's own rows. `FOR SELECT` is load-bearing rather than stylistic: a `FOR ALL` variant would carry a `WITH CHECK` letting any user insert themselves into any tenant, a self-service door through the wall. Writes on `membership` stay under the tenant policy alone, and the catalogue case below pins that.

**The binding.** `mapsift.user_id` obeys decision 3 unchanged: transaction-scoped (`is_local` true, always), parameterised and never interpolated, read through the guarded `nullif` cast because measurement C applies to it identically, and bound **once per authenticated request beside the tenant binding and the N9 correlation keys** rather than by each caller (owner decision, 2026-08-05). The accepted consequence is named rather than implied: in a tenant-bound transaction a `membership` query can also see the session user's own rows from other tenants. Those rows reveal only the reader's own places, which the reader is entitled to in each of those tenants separately, so what I4 protects, one tenant's data against another tenant's session, is untouched.

**The guard.** Decision 4 extends to the new parameter, keyed on what this read actually needs: the login-question read requires the **user** binding, so the application refuses to run it without one in force, whatever else is bound, raising rather than returning an empty result, because answering from the tenant policy alone would hand back every member of that tenant as the reader's own. With the user binding in force, an empty answer is a genuine answer, a user who belongs nowhere, and is returned rather than raised. With both bindings in force the read answers the reader's own rows alone, including those held in other tenants: the two permissive policies combine wider than the question, so the read path narrows to its own key, and that narrowing is witnessed by test rather than trusted to a comment, as are the binding discipline's two arms, the same-user re-entry that is a no-op and the second user that is refused. (Refined 2026-08-05 closing the Window A review: the original sentence said "neither binding" and left the tenant-only refusal and the genuine-absence answer unstated. Extended the same day closing the Window B review, which traced the both-bound state and found its correct answer hanging on one unwitnessed line whose deletion left the whole suite green.)

**The index.** The new query pattern is by user with no tenant bound, so `membership` carries an index on the user column (structural performance, foundation section 10; decision 5's tenant-leading rule governs tenant-scoped queries and does not apply to this one).

**The surface, and where this changes (owner decision, 2026-08-05).** No HTTP surface consumes this yet, deliberately: no authentication surface exists in the data-foundation milestone, and a login endpoint here would drag T6 surface work into it. The deliverable is the policy plus the read path in `accounts` (a selector, ADR-0007), which is the seam the login surface will consume. The trigger for change is the authentication surface itself: when it is built, the endpoint consumes this same selector and nothing about the wall moves. The exit is tracked as MAP-30 rather than remembered, per the owner's rule that a temporary exception leaves when its condition appears.

> **Note (2026-08-07): the trigger fired, and it fired from the flush rather than from login.** **ADR-0010** takes the authenticated request as its own decision, and the prediction in the paragraph above held exactly: the endpoint consumes this selector and **nothing about the wall moved**. What this selector answers with only the user binding in force is what makes a tenant claim verifiable **before** any tenant is bound, so the wall is never asked to police a value it was configured from. MAP-30 stays the exit for the login **endpoint**; the seam it consumes is MAP-34.

**The test, extending decision 7's list with case 6.** A user with memberships in two tenants enumerates exactly those two with no tenant bound; a user cannot enumerate anybody else's memberships by any path; without the user binding in force the read path raises rather than returning empty, whatever else is bound, and with it in force a user who belongs nowhere gets an empty answer rather than a raise; and the catalogue pins the wall's whole policy surface, the expected set per table with the exception's `FOR SELECT` command, reading a key that lives in `WITH CHECK` as much as one in `USING`, so a widening of any spelling fails the build, including one arriving as a separate `FOR INSERT` policy whose key exists only in `WITH CHECK`; with both bindings in force the read answers only the reader's own rows; and the user binding's two discipline arms are witnessed the way the tenant scope's are. Cases 1 to 5 stand unchanged. (Case 6's catalogue arm restated 2026-08-05 closing the Window A review, which proved the original wording satisfiable by a scan that misses exactly the door this section names.)

---

## Consequences

**What this buys.** The wall is one mechanism that covers the ORM, raw SQL, a background job and the direct-to-PostGIS reader identically, because it lives below all of them. Its defeat conditions are named, measured and turned into tests rather than into review notes. And the two channels that no policy closes are closed by the shape of the keys rather than by anybody remembering.

**What this costs, accepted with eyes open.**

- **Every tenant-scoped transaction pays one extra statement**, the binding, and a transaction that forgets it gets nothing rather than everything, which is the right direction for a mistake to fail in.
- **Composite keys cost one unique index per tenant-owned table** and make every foreign key two columns wide, which is more schema than a single-column reference and is what buys probe H's hole being shut.
- **Row-level security adds a predicate to every query on a protected table.** It is cheap when the indexes lead with the tenant identifier and expensive when they do not, which is why decision 5 makes that ordering part of the decision rather than a later tuning pass.
>   **Corrected 2026-08-21, at the MAP-50 probe, because the sentence above is false for a spatial read and
>   the tenant-leading rule cannot fix it.** Row-level security refuses to use a qual as an **index
>   condition** unless that qual's functions are `leakproof`, and `st_intersects` and `geometry_overlaps` are
>   not (`proleakproof = false`, measured on PostGIS 3.6.4). So a bounding-box read on a tenant-owned table
>   takes **no spatial index at all** under the policy: the plain GiST plans as a Parallel Seq Scan at 42.5 ms
>   over 20,000 features and 109 ms over 60,000, and **the composite `(tenant_id, geometry)` that decision 5
>   prescribes plans the same way**, at 49.0 ms and roughly twice the index size. The same query with the
>   policy bypassed is a Bitmap Index Scan at 1.4 ms. What the policy disqualifies is the **spatial** half of
>   the index condition, so leading with the tenant narrows nothing. **This is MAP-51**, and it reaches
>   decision 6, whose tile path performs exactly this read as `mapsift_tile` with the policy applied.

- **The application role cannot run migrations**, so two connection profiles exist and the deployment has to keep them straight.

**The limit this does not remove, stated rather than implied away.** Row-level security protects against a query that crosses the boundary. It does not protect against **code that can run arbitrary SQL on an already-bound connection**, because measurement E shows the binding is settable by the same unprivileged role and is not revocable. Injection on the application path therefore remains a full compromise of that tenant's session, and the controls that address it are the parameterised binding above, mypy strict, and the ORM being the ordinary path.

**What this forecloses.** Per-tenant views as an isolation mechanism, and any tile server that cannot carry a verified tenant claim into its database session. Nothing else the foundation left open: the tile server product, the identifier variant (MAP-2), and the permission model above the wall are untouched here.

**What must be revisited, and when.** If a measured need ever forces a connection pool that does not preserve transaction boundaries between the application and PostgreSQL, decision 3's transaction-scoped binding is exactly what such a pool breaks, and this ADR is amended with a dated note. If PostgreSQL ever makes a custom parameter revocable, measurement E's limit narrows and decision 2 can be tightened.
