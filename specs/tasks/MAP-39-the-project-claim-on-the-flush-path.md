# MAP-39: a flush addressing a project the verified tenant does not hold is refused as a project that never existed

## Trace

**Requirement:** PRD **T6.5**, its cross-tenant clause (refused as not-found, indistinguishable from a
resource that never existed), and PRD **T6.4** as the requirement that puts access at the whole project;
what this task takes from each is narrowed in Acceptance, because neither has its grant model yet. PRD
**M1** (a project belongs to exactly one workspace and one tenant) and **M9** (a target carries its
ancestors, so the project travels in the envelope) are why the claim is there to verify at all. PRD **N9**
reaches this task through ADR-0011 section 4, which names MAP-39 as one of the decisions that joins the
trail.

**Invariants and constraints:** **I4** and **C4** are cited to say what this task is not: the wall keys on
the tenant and is intact, the hole is authorisation one level down (ADR-0004 decision 4, the "what this
costs" paragraph; `specs/log.md` 2026-08-10). **C5** at the boundary, as everywhere.

**Code shape:** **ADR-0010 decision 6**, above all its addition of **2026-08-20**, which fixes where this
verification stands and what its refusal looks like; its addition of 2026-08-07 for the comparative form of
not-found. **ADR-0004 decision 4's addition of 2026-08-10**, for why there is no schema constraint to lean
on (its "nothing creates a Project" ground is dated stale since 2026-08-19; the decision stands on the
forcing half). **ADR-0005 sections 3, 4 and 8** (the binding, the wall's silence and what that silence can
mean, what is answerable unbound). **ADR-0011 section 4** (the record's closed names; the 404's reason
value is the window's). **ADR-0007 section 3** (which file holds a read, which holds a route).
`specs/testing.md` sections 2, 3 and 6.

## What this task owns

A flush whose operations address a project the verified tenant does not hold is refused as not-found,
indistinguishable in status and body from a project that never existed, before any cursor is read and
before anything lands (asserted on the log alone; the cursor half is MAP-46's, as Out of scope states),
and the refusal leaves a record.

## Out of scope

- **T6.5's within-tenant half**, the explicit denial with a resolution path: there is no per-project grant
  to deny yet. Owner: the detailed permission model T6.3 to T6.5 defer to.
- **T6.5's listings clause.** No project listing or enumeration exists on this path or anywhere in
  `apps/api` today; the clause binds whoever builds the first listing. Owner: that task, none filed today.
- **T6.4's three sharing modes**, any per-project access below membership. Owner: the detailed permission
  model.
- **A schema constraint.** ADR-0004 decision 4's addition of 2026-08-10 settled that neither the log's
  `project_id` nor the counter references `accounts_project`; the check lives on the flush path. Not
  reopened here.
- **The direct writer.** `append_to_the_operation_log` stays free of the check; the evidence block says why
  this is forced rather than chosen.
- **The cursor half of "nothing happened".** That a refused flush has not advanced the cursor is MAP-46's
  witness and its instrument (`statements_reaching`); this task may assert that nothing landed in the log,
  and no more.
- **Batch composition.** A batch *disagreeing* on its project is already the third typed refusal at 422
  (ADR-0010 decision 6, addition of 2026-08-10) and is not this task's.
- **The claimed author** (MAP-37), **the per-feature version** (MAP-38), **the credential refusals'
  records** (MAP-48).

## Boundary decisions the owner closed

Decisions 1 to 4 were closed by the owner on 2026-08-20 at pickup and registered before this file was
written; the pickup comment on MAP-39 is the record and this is the pointer, and `specs/log.md` carries the
line of that date, extended the same day where decision 2 says so. Item 5 is standing procedure (ADR-0008
section 9), restated here rather than closed at this pickup.

1. The verification runs after the binding and before anything `apply_the_flush` does; ADR-0010 decision 6
   carries the addition of 2026-08-20, including why it precedes the cursor read.
2. Window A pins the project claim to a real project of the claimed tenant at the call sites the
   evidence block measures, changing no assertion anywhere: the four cases that turn red, and the five in
   `tests/test_authenticated_request.py` that would otherwise stay green while the request they witness
   stopped being an accepted one. For seven of the nine that project is the `Party` fixture's; the two
   two-tenant cases (lines 294 and 307) build their tenants inline through the account services, which
   create nothing below the membership, so their arrange first creates a workspace and a project through
   the published services inside the tenant the batch claims, and then pins (corrected 2026-08-20 at the
   second spec-read pass; the first form said "the fixture's real project" over all nine). The five entered
   at the pre-dispatch spec read, an extension the
   orchestrator took under the owner's decision's own rationale and reported in the same message as the
   read's findings. The footing is `specs/testing.md` section 2: a test changes only when a requirement
   changes, and the requirement reached this path, so the arrange follows it. The pinning is at the call
   site, through the file's own `a_batch_of_one_tenant_claiming` or an explicit argument; the
   `a_batch_claiming` helper's own default is not edited, because among its callers are the disagreement
   cases ADR-0010 decision 6's additions of 2026-08-11 and 2026-08-13 say an implementing window may not
   edit. *(Note of 2026-08-20, after the Window B review: "changing no assertion anywhere" bound this
   pinning pass, which changed none. The correction round the review ordered then gave the same five cases
   a status assertion each, measured blind without it by two mutants; that round's authorization and
   measurements are in `specs/log.md` under this date, and the two texts are a sequence rather than a
   contradiction.)*
3. Acceptance is the delta below; the issue's Acceptance block is a copy of T6.5 and T6.4 and the delta
   replaces it for the windows' reading. The issue itself stays as it is: ADR-0008 section 9 keeps a Linear
   issue's acceptance copied from the requirement.
4. The N9 record is in scope, the mirror of the tenant refusal's.
5. The pre-dispatch spec read runs, and is not waived.

## Evidence handed over

Everything below is dated 2026-08-20 and labelled as what it is. Both "measured" blocks are measurements of
the suite's text (greps and paren-matched enumeration), not of a run; the run is Window A's and is the
check on every count here.

**Measured: the call sites the new check reaches.** The conftest operation helpers default the project to a
fresh random identifier (`apps/api/conftest.py` lines 389 and 422: `project_id or uuid4()`). Four cases
assert success through the route while their arrange inherits that default, so they turn red the moment the
verification exists:

- `mapsift/sync/tests/test_flush.py` lines 87 and 104, the two replay cases: each posts one operation with
  an unpinned project and then reads the single entry back with `.get()`, which raises once the post is
  refused.
- `apps/api/tests/test_authenticated_request.py` lines 137 and 280: both assert `HTTPStatus.OK` on batches
  built by `a_batch_claiming`, which pins no project.

Five more cases in `tests/test_authenticated_request.py` post an unpinned single-tenant batch and assert
only what was bound (lines 151, 164, 179, 294 and 307); three run on `alice`, and the two at 294 and
307 hold no project to pin, as boundary decision 2 records. They stay green under the new check, because the
binding they witness precedes it, and they stop witnessing an accepted request without any assertion
noticing; boundary decision 2 reaches them for that reason. *(The noticing half was closed by the
correction round of 2026-08-20: each of the five now asserts the status it witnesses.)* Every other post to the route, in this file and
in every other module, either pins `by.project_id` or a `second_project_of` row, or expects a refusal (a
credential, CSRF or not-found case, or a 422 at the Pydantic boundary) that fires before this check can
run. Window A re-verifies by running the suite and reports the actual red
set, which is the check on this reading.

**Measured, on the same footing: where the check cannot live.** Direct callers of
`append_to_the_operation_log` outside `services.py` are exactly `test_append_only_log.py` (through
`_an_entry_of`, which inherits the random default) and `test_flush.py`'s
`test_an_operation_addressed_at_another_tenant_is_refused_by_the_wall`, which must reach the policy and not
an earlier guard. Neither may be edited, so the writer stays free of the check (ADR-0004 decision 4's
forcing half, still standing after MAP-47).

**Read in this repository, not measured.** Inside the wall, a read on `Project` under the bound tenant
answers nothing for a foreign project and for an absent one alike, so the indistinguishability T6.5 asks
for is the mechanism itself rather than something to defend. The standing trap takes a narrower form
here: the guard ADR-0005 section 4 describes raises only where nothing is bound, and this check runs under
the binding, so it cannot fire on this path; what is left is that the wall's filtered silence and a genuine
absence are one answer, and a case reading an empty result has to know which of the two it is asserting. The
shape that does not pass for the wrong one is the comparative form already in the suite,
`test_a_claim_on_a_tenant_the_principal_lacks_is_answered_exactly_as_one_that_never_existed`
(`tests/test_authenticated_request.py`), whose docstring states the form. The comparative pair on this axis
is a real project of another tenant against a project that exists nowhere, both claimed by a principal
whose tenant claim is good. The N9 mirror is
`test_a_claim_the_principal_cannot_back_is_recorded_though_the_client_is_told_nothing`
(`mapsift/sync/tests/test_the_flush_decision_trail.py`), including why the reason is asserted present and
not pinned to a literal.

**What is still open and belongs to the window:** the spelling and home of the read (ADR-0007 section 3
says which file holds a read and nothing about names); the home of the check itself, in the
route's module or at the head of `apply_the_flush`, a module placement and never a call position: wherever
it lives, the call runs inside the binding, in the order the addition of 2026-08-20 fixes, under ADR-0007
section 3's roles; the reason value on the record
(ADR-0011 section 4 leaves the 404's open); and how the new refusal's constant relates to the existing
`NO_MEMBERSHIP_IN_THE_TENANT_CLAIMED` in `mapsift/sync/api.py`, whose comment states the rule it was named
under.

## Acceptance

The criteria are T6.5's and the window reads them in the PRD. What this task does differently:

- **T6.5 contributes its cross-tenant clause only.** The within-tenant explicit-denial clause and the
  listings clause have no runtime on this path; both are out of scope by name above.
- **T6.4 contributes no clause of its own.** Granting access per whole project is ADR-0004's Consequences'
  reading of T6.4, whose own text is the three sharing operations, and there is no grant model yet; what
  stands in for it here is membership plus containment: a project inside the verified tenant is addressable
  by its members, and one outside it is answered as never having existed.
- **The comparison is over status and body**, ADR-0010 decision 6's addition of 2026-08-07, extended to
  this refusal by the addition of 2026-08-20.
- **The N9 clause is inherited from ADR-0011 section 4 rather than from T6.5:** the refusal leaves a
  `request.refused` record carrying status 404 and a non-empty reason, the value unpinned.
- **"Nothing lands" is asserted on the log alone**; the cursor's non-advancement is MAP-46's, as Out of
  scope states.
- **The ordering half is a criterion of this task and is enumerated here** (added 2026-08-20 at the Window A
  review, where the Spec axis found it stated in "What this task owns" and in boundary decision 1 but
  missing from this block): the refusal precedes the cursor read, per ADR-0010 decision 6's addition of
  2026-08-20; its witness is the status a foreign-project batch opening above an absent cursor earns, the
  not-found and never the 409 rehandshake.
