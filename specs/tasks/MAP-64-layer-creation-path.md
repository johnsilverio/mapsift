# MAP-64: a layer is created through a published service, inside the wall, under the identifier the client minted

## Trace

**Requirement:** PRD **C1** (create a layer, choosing its geometry type, as the structure a feature is drawn
into; its attribute-schema half is M6 and is deferred by Out of scope below), PRD **M2** for the layer's
Shape alone (the project, the declared geometry kind and the storage class as properties of the layer), PRD
**M3** (the identifier is the client's and the server neither allocates nor rewrites it), and PRD **M1** for
its isolation clause alone, which is the one of its four that reaches this path. *(Narrowed 2026-08-28 at the
correction round, which found this line crediting M1 with the project a layer resolves to while the
Acceptance below credited M1 with the isolation clause only; M1 is the account tree and says nothing about a
layer, so M2's Shape is the upstream and the Acceptance was the half that was right.)* What carries the fact
that the structure is created before anything is
drawn into it is C1's **Description** and its **Rule**; its Origin field is MC-03 parity alone and
contributes nothing here.

**Invariants and constraints:** foundation **I3** and **I4**; **C3** and **C4**.

**Code shape:** **ADR-0005 sections 3, 4 and 5** (who binds and how often, the wall's silence beside the
application's guard, the composite reference between two tenant-owned tables); **ADR-0006 section 3** (no
server-side identifier for an object a client can create); **ADR-0007 sections 3, 5 and 7** (what
`services.py` holds, why a service is not a capability, when the registry exists). `specs/testing.md`
sections 2, 3, 6, 7 (the ORM is not tested) and 9.

**Named as a future consumer and not as this task's requirement:** **MAP-65**, which cannot write the
projection until a layer row can exist; the tracker carries the relation.

## What this task owns

A layer can be created through a published service in `layers`, and the row lands inside the wall in one
project of one tenant under the identifier the client minted, so the sanctioned path exists for the flush,
the web client and the fixtures to stand on instead of building the row by hand. **Nothing is moved onto it
here**: its first caller is MAP-65's, and boundary decision 3 leaves the existing helpers where they are.

## Out of scope

- **The attribute schema half of C1.** It is M6 and MAP-5 already deferred it. This task publishes the
  structural layer and not its fields, so no case here may assert a field definition.
- **Both refusals a layer's declarations make.** Whether an operation reaches the queue at all under the
  storage class, and whether a geometry belongs to the declared family, are **MAP-66**. The two pure rules
  already exist in `layers/rules.py`; giving either a caller here is work nobody asked for.
- **The projection write.** MAP-65. No production code here touches the flush, `sync/services.py` or
  `layers_feature`. **A case may still insert a feature**, because the third clause of C1's acceptance below
  is exactly that the created layer is one a feature can reference; what is out of scope is a writer, never
  an assertion.
- **The shared fixtures and the flush suites.** Every batch those suites post carries a `layer_id` that
  names no layer, and today that is harmless. Making them name a real one is **MAP-65's Window A**, because
  it is that task's tests that need it; changing them here would be a change with no failing case behind it.
- **An HTTP surface.** There is no route on this path; MAP-20 adds one if it needs one.
- **Who may create a layer.** The permission model is T6's Open/ADR and the licence tiers it rests on are
  OQ-7. This publishes the path and not the grant that guards it.
- **The capability, the registry and the description contract.** Foundation OQ-4 keeps the public capability
  surface outside this slice by name and ADR-0007 section 7 creates the registry at the second capability;
  no `capabilities.py` is created here.
- **Renaming, deleting or reclassifying a layer**, and **moving one between projects**. No requirement asks
  any of them of this path, and OQ-6 holds the promotion question.
- **A per-tenant uniqueness of a layer name.** Nothing upstream asks for it, and under ADR-0005 section 5 it
  would be new schema, so introducing it here is a finding to report and not a change to make.
- **The client side.** Minting the identifier in the core is MAP-17; the offline path that would call this
  is MAP-20.

## Boundary decisions the owner closed

Decisions 1 and 2 were closed by the owner on 2026-08-28 at this pickup. Both are **execution state rather
than contract**, so the record is the tracker and this is the pointer: MAP-64, MAP-65 and MAP-66 exist with
their blocking relations, and no canon document owns either. Decision 3 was taken by the orchestrator at
spec-writing and says so; 4 and 5 are procedure.

1. The layer-creation path is its own task **ahead of** the projection write, on the MAP-47 precedent, rather
   than being absorbed into it or replaced by fixtures building the row directly.
2. The two refusals stay out of both this task and the projection, in **MAP-66**.
3. **Taken by the orchestrator at spec-writing and reported to the owner in the same message:** the two
   module-local layer helpers in `layers/tests/` do **not** move onto the new service, in this task or in its
   refactor step. MAP-47's decision 4 moved `_party` and `second_project_of` because they are **shared**
   fixtures in the root `conftest.py` that the whole suite stands on; these two are local to the modules that
   use them, one of which builds a large fixture for a plan measurement where a service buys nothing. The
   caveat that decision carried applies here and is the reason a blanket move would be wrong anyway: three
   of the five `Layer.objects.create` sites are deliberate refusal cases inside `refused_with(...)`, and
   moving one onto a service destroys what it asserts.
4. The pre-dispatch spec read runs, and is not waived.
5. Acceptance is the delta below.

**What is decided for MAP-65 and is deliberately not this task's:** an operation addressing a layer that does
not exist is answered as a typed refusal carrying its reason rather than as a bare 404. It is recorded here
only so nobody implements it early; its fan-out into ADR-0010 decision 6 and ADR-0011 section 4 happens
before that task's window, not before this one's.

## Evidence handed over

Everything below is dated **2026-08-28** and labelled as what it is.

**Measured, in this project's own `db` container, inside a transaction that was rolled back.** A row inserted
into `layers_feature` whose `(tenant_id, project_id, layer_id)` names no `layers_layer` row is refused:

```
ERROR:  insert or update on table "layers_feature" violates foreign key constraint
        "feature_layer_within_the_same_tenant_and_project"
DETAIL: Key (tenant_id, project_id, layer_id)=(...) is not present in table "layers_layer".
```

With the layer row present beforehand, the identical insert succeeds. **The conclusion this does not
support, refused in writing:** it says nothing about what a layer whose `project_id` names no project at all
does, because that direction was not run. The other-tenant direction of that second key is already witnessed
by `test_a_layer_cannot_reference_a_project_of_another_tenant` through `FOREIGN_KEY_VIOLATION`
(`layers/tests/test_layers_and_features.py:230`); whether the nowhere-at-all direction needs a case of its
own is the window's to decide.

**Measured, in this repository.** `mapsift/layers/` carries `models.py`, `rules.py` and `selectors.py` and no
`services.py`, so the package has no writer at all. `Layer.objects.create` appears at exactly five sites and
every one is under `mapsift/layers/tests/`: a module-local helper at `test_layers_and_features.py:43`, a
second at `test_the_container_scoped_spatial_read.py:187`, and three deliberate refusal cases inside
`refused_with(...)` at `test_layers_and_features.py:199`, `:230` and `:313`. `Layer.id` carries no default
(`layers/models.py:25`), and `test_the_server_never_allocates_an_identifier_for_a_layer` already pins that
through `NOT_NULL_VIOLATION`. `test_an_ordinary_update_cannot_move_a_layer_to_another_tenant`
(`test_layers_and_features.py:287`, naming M2 and M1) already covers the immutability the Acceptance below
declines to add a second time. The table carries `UNIQUE (tenant_id, project_id, id)` as
`layer_identity_within_its_tenant_and_project` (`layers/models.py:50`), which is what the feature's composite
reference points at, and the database carries `layer_project_within_the_same_tenant` over
`(tenant_id, project_id)` into `accounts_project (tenant_id, id)` from `layers/migrations/0001_initial.py`.

**Read in this repository, not measured.** `TenantOwnedManager.get_queryset` raises `TenantNotBound` with no
tenant bound (`common/binding.py`), and Django's `Manager.create` goes through `get_queryset`, so a service
calling `.objects.create` unbound raises before it reaches the database. `tenant_scope` opens
`transaction.atomic()` itself, which is the recorded trap of MAP-10 to MAP-14: a test whose only transaction
is the one its own scope opened cannot witness a transactional claim. **No transactional claim is made by
this task**, so the trap is named rather than worked around; a case that finds it needs one is a finding.
`create_workspace` and `create_project` in `accounts/services.py` are the nearest precedent, and a precedent
rather than a template. **The other two writers in that module are the shape this task must not copy**, and
that module's own docstring says why: creating an account is the one write there that binds a tenant itself,
because it is the one that mints it.

**What is still open and belongs to the window:** the spelling of the service and its parameters, in the
idiom the sibling services already use and under ADR-0007 section 3, which says what `services.py` holds and
nothing about signatures; what it returns; whether the two declared properties cross the boundary as their
`StrEnum` members or as their values; and how a case shows the row is unreachable from another tenant
without asserting the wall's silence as though it were the guard (ADR-0005 section 4).

## Acceptance

The criteria are PRD C1's, M2's, M3's and M1's, and the window reads them there. What this task does
differently:

- **C1's acceptance splits three ways rather than two.** "Defines attribute fields" is M6 and is deferred.
  "The user names a layer and picks point, line or polygon" keeps its runtime here and loses only its actor:
  the surface is MAP-20's, and what is asserted is that the service stores both the name and the declared
  kind it was given. **Both are asserted rather than assumed**, because a mutant dropping `name=name` from
  the two services MAP-47 published left all ten of its cases green, a `CharField` with no default landing
  the empty string (`specs/log.md`, 2026-08-19). The third clause is the one the measured foreign key above
  turns from rhetorical into testable: a layer created this way is one a feature can then reference.
- **None of M2's five acceptance clauses is this task's, and they leave by three different doors.** The two
  about the storage class deciding a path and the geometry family being enforced are MAP-66's. The one about
  a feature not changing path leaves by two doors of its own, and Out of scope names both: its promotion half
  is OQ-6's and its reclassification half is asked by no requirement. The **import pair** waits on the
  element budget, a PRD 10.5 measurement with nothing built to import yet, and MAP-66's own Not in scope
  block says that pair is not its either. What this task takes from M2 is its **Shape**, narrowed to the two
  declared properties: the layer carries a geometry kind and a storage class as properties of the layer
  rather than of any feature in it. **The persisted shape is otherwise unchanged and no column is added**, so
  the rest of what that Shape names is not this task's to create.
- **M3's upstream here is its Requirement sentence and not its acceptance list**, which is the correction
  **MAP-10** earned on 2026-08-10 and MAP-11 records, and which MAP-47's equivalent bullet already respects.
  The sentence is that the
  server "never allocates an identifier for an object a client can create offline, and never rewrites an
  identifier it received". Its half with a runtime here is that the service stores exactly the identifier it
  was handed; its half without is the client minting it, which is MAP-17. **None of M3's four acceptance
  clauses is asserted by this task.**
- **M1 contributes one clause and withholds three.** The clause that reaches this path is the isolation one,
  through the bullet below. The three that do not are the account-tree ones: a personal account creating its
  tenant with one owner membership, a user with two memberships, and a workspace and a project each resolving
  to one tenant under an update that cannot move them. **That last one names a workspace and a project and
  not a layer**, and the layer-shaped equivalent of it already exists as a case from MAP-5, so it is neither
  this task's to invent nor this task's to add a second time.
- **The issue's C4-derived bullet has no principal on this path**, exactly as MAP-47's did. There is no route
  and therefore no verified principal, so what is asserted is that the row carries the tenant the caller
  bound and passed, and that a caller passing a tenant other than the bound one is refused by the wall rather
  than stored. Verifying a claim against a principal stays ADR-0010 decision 6's, at the route.
