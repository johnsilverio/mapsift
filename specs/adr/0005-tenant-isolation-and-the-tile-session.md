# ADR-0005: Tenant isolation, the database roles, and the tile path's session wiring

- **Status:** accepted (2026-08-04)
- **Deciders:** the owner, on the probes recorded below
- **Authority:** derives from `specs/mapsift-foundation.md` v0.17 (section 9, invariant I4) and `specs/PRD.md` v0.12 (T6.1, T6.5, N2, M1). Where this ADR and the foundation disagree, the foundation wins and this ADR is the one that is wrong.
- **Supersedes:** nothing. **Superseded by:** nothing.
- **Delivers:** MAP-1, and item 1 of the ADR agenda in `specs/dependencies.md` section 6.

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

---

## Consequences

**What this buys.** The wall is one mechanism that covers the ORM, raw SQL, a background job and the direct-to-PostGIS reader identically, because it lives below all of them. Its defeat conditions are named, measured and turned into tests rather than into review notes. And the two channels that no policy closes are closed by the shape of the keys rather than by anybody remembering.

**What this costs, accepted with eyes open.**

- **Every tenant-scoped transaction pays one extra statement**, the binding, and a transaction that forgets it gets nothing rather than everything, which is the right direction for a mistake to fail in.
- **Composite keys cost one unique index per tenant-owned table** and make every foreign key two columns wide, which is more schema than a single-column reference and is what buys probe H's hole being shut.
- **Row-level security adds a predicate to every query on a protected table.** It is cheap when the indexes lead with the tenant identifier and expensive when they do not, which is why decision 5 makes that ordering part of the decision rather than a later tuning pass.
- **The application role cannot run migrations**, so two connection profiles exist and the deployment has to keep them straight.

**The limit this does not remove, stated rather than implied away.** Row-level security protects against a query that crosses the boundary. It does not protect against **code that can run arbitrary SQL on an already-bound connection**, because measurement E shows the binding is settable by the same unprivileged role and is not revocable. Injection on the application path therefore remains a full compromise of that tenant's session, and the controls that address it are the parameterised binding above, mypy strict, and the ORM being the ordinary path.

**What this forecloses.** Per-tenant views as an isolation mechanism, and any tile server that cannot carry a verified tenant claim into its database session. Nothing else the foundation left open: the tile server product, the identifier variant (MAP-2), and the permission model above the wall are untouched here.

**What must be revisited, and when.** If a measured need ever forces a connection pool that does not preserve transaction boundaries between the application and PostgreSQL, decision 3's transaction-scoped binding is exactly what such a pool breaks, and this ADR is superseded rather than edited. If PostgreSQL ever makes a custom parameter revocable, measurement E's limit narrows and decision 2 can be tightened.
