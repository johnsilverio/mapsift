# MAP-3: the account tree and the wall under it

> **What this is.** The spec-per-task the authority chain ends at (`CLAUDE.md`, Process and tracking): what an
> implementing window reads, assembled from the documents that already decided it. It **cites and never
> restates**; where this file and a cited document disagree, the cited document wins and this one is the
> defect. Read `specs/testing.md` before writing a line of either window.
>
> **Trace.** PRD **M1** (the account tree and the tenant identifier), **M3** (identity of every created
> object), **T6.1**, **N2**; foundation **I3**, **I4**; **C3**, **C4**; **ADR-0005** (the wall, the roles, the
> binding, the composite keys), **ADR-0006** (the identifier variant).
>
> **This is the first product code in the repository.** Everything before it was scaffold or decision.

---

## 1. What this task delivers

The five entities of M1 as persisted shapes, the tenant identifier on every tenant-owned row, and the
**isolation wall of ADR-0005 in the same migration that creates them**, proven by tests that were written
first.

It is the first migration, which is the artifact this stack is worst at taking back, so the two ADRs that
precede it are not optional reading: **ADR-0005 sections 2, 3, 5 and 7**, and **ADR-0006 sections 1, 3 and
4**.

## 2. The shape

M1 fixes it and this file does not re-derive it: **user**, **tenant** (kind personal or organization, always
materialised as a record so a freelancer and a company take the same isolation path), **membership**
(user to tenant, carrying governance role and licence), **workspace**, **project**. Every tenant-owned row
carries the tenant identifier, and a workspace and a project each resolve to exactly one tenant, immutable in
the ordinary write path.

Two entities are deliberately **not** tenant-owned and must not grow a tenant column: **user**, which is the
durable cross-tenant identity by design (M1), and **membership's** join to it. Membership itself is
tenant-owned because it names a tenant.

## 3. What the migration carries, beyond the tables

Each item names the decision it comes from, so a reviewer checks it against that document rather than against
this list.

- **Row-level security `ENABLE`d and `FORCE`d** on every tenant-owned table, with one policy per table using
  the guarded expression, `nullif(current_setting('mapsift.tenant_id', true), '')::uuid` (ADR-0005 §3). The
  bare cast is a defect, and the reason is measured in that ADR.
- **The four roles and their grants**, none privileged, `BYPASSRLS` to nobody (ADR-0005 §2). The two
  connection profiles, migrate as owner and runtime as the application role, come with them.
- **Composite uniqueness and composite foreign keys** over `(tenant_id, key)` between tenant-owned tables
  (ADR-0005 §5), plus every natural unique key scoped per tenant rather than globally.
- **Identifiers as the native `uuid` type, with no server-side default** on anything a client can create
  offline (ADR-0006 §3, M3).
- **Indexes lead with `tenant_id`** where the query is tenant-scoped (ADR-0005 §5).

**Deliberately deferred to MAP-11 and named here so nobody adds it early:** the narrow per-project version
table and its autovacuum settings. It belongs to the flush, not to the account tree, and ADR-0004 owns it.

## 4. Window A, the tests

Write these as **failing** tests and nothing else. Do not write, sketch, or look at an implementation
(`testing.md` §1). Each test **names its requirement ID** (§6 of the same document), and each asserts a
behaviour rather than a shape.

**The pure decision, which carries the bulk of the suite.** Tenant resolution is a decision over plain data:
given a session's memberships and a target resource, which tenant is in force, and when is the answer "none".
It needs no database and it is where the edge cases live: a user with two memberships, a user with none, a
resource whose tenant the session does not hold. Pull it out and test it as a function (`testing.md` §3).

**The invariant acceptance tests, against a real database, because the wall is the database's.** These are
the C4 and N2 tests and they may never be weakened:

1. every tenant-owned table has row-level security **enabled and forced**, enumerated from the catalogue so a
   table added later without a policy fails the build (N2, and the reason is measured in ADR-0005);
2. no application role holds `BYPASSRLS`, and no application role owns a tenant-owned table;
3. a query with no tenant binding in force **returns nothing and the application raises**, since the policy's
   silence is indistinguishable from an empty tenant (ADR-0005 §4, N9);
4. a read or write bound to one tenant cannot reach another tenant's row **by any path**, including through a
   foreign key and including a unique-key collision that would reveal the row exists (N2, ADR-0005 §5);
5. the binding does not survive its transaction, asserted rather than assumed, because the leak measured in
   ADR-0005 is a session-scoped binding on a reused connection.

**The shape's own invariants** (M1, M3): creating a personal account creates its tenant with exactly one owner
membership and no organization; a user in two tenants is one identity with two memberships; a workspace and a
project each resolve to exactly one tenant and an ordinary update cannot move either across tenants; no
tenant-owned table carries a server-side default for its identifier.

**What window A must not test** (`testing.md` §7): that Django saves a row, that a foreign key constrains, or
any generated type. Those test Django and the generator. The subject here is the wall and the shape's rules.

## 5. Window B, the implementation

Read the tests as a contract authored by someone else and write the **minimum** to green. **A test may not be
edited to make it pass**; a test that looks wrong is a finding reported back, never a licence to rewrite the
contract (`testing.md` §1 and §9). Design happens in the refactor step under green.

Generate rather than hand-write: `python manage.py startapp`, `python manage.py makemigrations`, never a
hand-written migration file (ADR-0002 §1, `dev-workflow` §3). The policies, roles and grants that the
autodetector cannot produce go in a `RunSQL` operation inside the generated migration, and that migration
**cites ADR-0005 and ADR-0006 by number** rather than restating their reasoning.

## 6. Out of scope, named so neither window drifts in

The operation envelope and the catalog (MAP-7 to MAP-9), the flush and the version axes (MAP-10 to MAP-14),
anything in the client core or the web client, the permission model above the wall (T6.2 to T6.5, which is
grants rather than isolation), the legal-weight marker (M7, which waits on OQ-8), and layers and features
(MAP-5, which is the next issue and not this one).

## 7. Done

The five points of the `linear-workflow` definition of done, with one of them doing real work here: the
behaviour is proven by tests **written first**, which for this task is checkable, because window A's commits
land before window B's and the tests are red in between.
