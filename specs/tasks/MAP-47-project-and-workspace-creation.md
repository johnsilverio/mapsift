# MAP-47: a workspace and a project are created through a published service, inside the wall, under the identifier the client minted

## Trace

**Requirement:** PRD **M1** (the account tree; a workspace and a project each resolve to exactly one tenant,
immutable in the ordinary write path, and a project carries its workspace by M1's Shape; "required, with no
nullable parent" is boundary decision 1's reading, grounded in T6.4 rather than in M1's words) and PRD
**M3** (the identifier of a workspace and a project is the client's, and the server neither allocates nor
rewrites it). PRD **A2** is the origin the issue names; its acceptance is about isolation and reachability
and carries no clause about the act of creation, so nothing here is derived from it beyond the fact that a
project is created **within a workspace, under a tenant**.

**Invariants and constraints:** foundation **I3** and **I4**; **C3** and **C4**.

**Code shape:** **ADR-0005 sections 3, 4 and 5** (who binds and how often, the wall's silence and the
application's guard, the composite reference between two tenant-owned tables); **ADR-0006 section 3**
(no server-side identifier for an object a client can create); **ADR-0007 sections 3, 5 and 7** (what
`services.py` holds, why a service is not a capability, when the registry exists); **ADR-0010 decision 6**
as the pattern for where a binding is opened relative to a writer, not as a requirement of this task.
`specs/testing.md` sections 2, 3, 6, 7 (the ORM is not tested) and 9.

**Named as future consumers and not as this task's requirement:** **MAP-39** and **MAP-20**; the tracker
carries the relations.

## What this task owns

A workspace and a project can be created through a published service in `accounts`, and the rows land
inside the wall under the identifier the client minted, so the flush, the web client and the shared fixtures
all stand on one sanctioned path instead of building the rows by hand.

## Out of scope

- **An HTTP surface.** There is no route on this path; MAP-20 adds one if it needs one. This task publishes
  the service.
- **Who may create a workspace or a project.** The detailed permission model is T6.3's and T6.4's Open/ADR,
  and the licence tiers it depends on are OQ-7 (T6.2). The service is the path and not the grant.
- **The capability, the registry and the description contract.** Foundation OQ-4 keeps the public capability
  surface outside this slice by name and ADR-0007 section 7 creates the registry at the second capability;
  no `capabilities.py` is created here.
- **A default or first workspace at account creation.** Refused as a mint (boundary decision 1) and left
  open as an onboarding question that no requirement carries today (A2 and K2 are the nearest and are silent;
  M1's acceptance names the tenant and the owner membership only), a candidate for PRD section 10 rather
  than for this task; no test here may assume a new account holds a workspace.
- **Whether a batch's project belongs to the verified tenant.** MAP-39.
- **A per-tenant uniqueness of a workspace or project name.** Nothing upstream asks for it, and under
  ADR-0005 section 5 it would be new schema, so introducing it here is a finding to report and not a change
  to make.
- **Deleting a workspace or a project**, which no requirement asks of this path, and **moving one across
  tenants**, which M1's Open/ADR names as a distinct recorded operation outside Layer 3's scope.
- **The client side.** Minting the identifier in the core is MAP-17; the offline `create_project` that needs
  a `workspace_id` it already knows is MAP-20.

## Boundary decisions the owner closed

Decisions 1 to 3 were closed by the owner on 2026-08-18, after a research round, and registered before this
file was written: **the pickup comment on MAP-47 is the record and this is the pointer**, and `specs/log.md`
carries the three MAP-47 lines of that date. Decision 4 was taken by the orchestrator at spec-writing and
says so; 5 and 6 are procedure. In one sentence each:

1. The workspace enters the task: `create_workspace` and `create_project`, both in `accounts/services.py`,
   both under a client-minted identifier, and a project requires an existing workspace with no nullable
   parent; a default workspace at account creation is refused, and the onboarding question is left open by
   name.
2. A service in `services.py`, not the first capability.
3. The tenant is an explicit `tenant_id` argument, the service opens no binding and requires one in force;
   `_create_tenant_owned_by` stays the one self-binding writer because it mints the tenant.
4. **Taken by the orchestrator at spec-writing under the 2026-08-04 finding in `specs/log.md`, and reported
   to the owner in the same message:** the shared fixtures that build these rows by hand (`_party` and
   `second_project_of` in `apps/api/conftest.py`) move onto the published services in **Window B's refactor
   step under green**, with no assertion changed anywhere. That is test infrastructure moving onto the path
   it exists to exercise, taken after the tests are green, and it does not touch the `implement` skill's rule
   against editing a test to make it pass. **Those two helpers and nothing else:** the three other hand-built
   rows in the suite (`accounts/tests/test_account_tree.py` line 142, `tests/test_tenant_isolation.py` lines
   235 and 243) are deliberate refusal cases inside `pytest.raises` or `refused_with`, and moving one onto a
   service destroys what it asserts.
5. The pre-dispatch spec read runs, and is not waived.
6. Acceptance is the delta below.

## Evidence handed over

Everything below is dated 2026-08-18 and labelled as what it is.

**Measured in this repository.** `apps/api/mapsift/accounts/services.py` creates the user, the tenant and
the owner membership and stops. `apps/api/conftest.py` builds the workspace and the project by hand in
`_party` (lines 80 to 99) and `second_project_of` (lines 102 to 114), inside a `tenant_scope` the fixture
opens itself. `Workspace.id` and `Project.id` carry no default (`accounts/models.py` lines 91 and 110), and
two cases already pin that: `test_no_tenant_owned_table_carries_a_server_side_default_for_its_identifier`
and `test_the_server_never_allocates_an_identifier_for_an_object_a_client_creates` (`accounts/tests/
test_account_tree.py`, the second refusing `Workspace.objects.create` with no `id`). `Project.workspace` is
non-nullable with `db_constraint=False`, and the database carries the composite reference
`project_workspace_within_the_same_tenant` over `(tenant_id, workspace_id)` from `migrations/0001_initial.py`
(lines 78 to 86). `apps/api/tests/test_tenant_isolation.py` already witnesses, by SQLSTATE through the
conftest's `refused_with`, that an insert cannot smuggle a row into another tenant (`POLICY_VIOLATION`,
line 231) and that a foreign key cannot reach another tenant's row (`FOREIGN_KEY_VIOLATION`, line 238), so
a case here that asserts one of those two mechanisms names **which** refused rather than that something did.

**Read in this repository, not measured.** `TenantOwnedManager.get_queryset` raises `TenantNotBound` when
no tenant is bound (`common/binding.py` lines 113 to 125), and Django's `Manager.create` goes through
`get_queryset`, so a service that calls `.objects.create` with no binding raises before it reaches the
database. `tenant_scope` opens `transaction.atomic()` itself, which is the recorded trap of MAP-10 to
MAP-14: a test whose only transaction is the one its own scope opened cannot witness a transactional claim.
No transactional claim is made by this task, so the trap is named rather than worked around; if a case
finds one it needs, that is a finding.

**What is still open and belongs to the window:** the exact spellings of the two services and their
parameters, in the shape the existing services in the same module already spell (keyword-only, typed) and
under ADR-0007 section 3's role for `services.py`, which says what the file holds and nothing about
signatures; what a service returns; and how a case shows that the
row it created is unreachable from another tenant without asserting the wall's silence as if it were the
guard (ADR-0005 section 4, and the `test` skill's rule about an empty result that passes for the wrong
reason).

## Acceptance

The requirement's criteria are PRD M1's and M3's and the window reads them there. What this task does
differently:

- **M1's creation clause is exercised through the new services and not through the model**, because the
  criterion "a workspace and a project each resolve to exactly one tenant, and an ordinary update cannot
  move either across tenants" is already witnessed against rows the fixture built (`test_account_tree.py`
  lines 53 to 71); the delta is that the same holds for rows the published path built.
- **M3's "the server never allocates an identifier for an object a client can create offline" has one half
  with a runtime here and one without.** The half with a runtime is that the service takes the identifier
  and stores exactly it; the half without is the client minting it, which is MAP-17 and is not asserted here.
- **C4's clause on the flush path is not this task's.** The issue's third acceptance bullet says the row
  carries "the tenant identifier the principal was verified against"; there is no route and so no principal
  on this path (MAP-20 adds the route if it needs one), so what is asserted here is that the row carries the tenant the caller
  bound and passed, and that a caller passing a tenant other than the one bound is refused by the wall
  rather than stored (boundary decision 3). The verification of the claim against the principal stays
  ADR-0010 decision 6's, at the route.
- **A2 contributes no acceptance clause**, as the Trace says, so nothing here derives from it.
