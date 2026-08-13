# ADR-0010: The authenticated request, its same-origin premise, and where the mechanism is allowed to change

- **Status:** accepted (2026-08-07)
- **Deciders:** the owner, on the probes recorded below
- **Authority:** derives from `specs/mapsift-foundation.md` v0.17.1 (section 9, the security posture and the authorship rule; I10) and `specs/PRD.md` v0.16 (T5.1, T5.2, T6.1, T6.5, M8, N1), and from **ADR-0005** sections 3 and 8, whose deferral this ADR converts into a decision. Where this ADR and the foundation disagree, the foundation wins and this ADR is the one that is wrong.
- **Supersedes:** nothing. **Superseded by:** nothing.
- **Delivers:** MAP-34, and it unblocks MAP-10.

---

## Context

`apps/api` has no authenticated request. `config/api.py` builds its `NinjaAPI` with no `auth`, no middleware binds a principal, and the two pieces MAP-27 built for exactly this, `user_scope` in `mapsift/common/binding.py` and `memberships_of_the_session_user()` in `mapsift/accounts/selectors.py`, have **zero callers outside tests**. ADR-0005 section 8 recorded that absence deliberately and named its exit as MAP-30.

**What forced the decision now is a defect rather than a plan.** The MAP-10 Window A review of 2026-08-07 found that the flush endpoint, having no principal, could only take its tenant from the request body and bind the wall from it. Two independent review axes reached it. That is C13's "free client field" and it is OWASP API1:2023, in the first server-side write path of a product whose whole moral position is that a legal-weight edit is never silently lost.

The decision could not be deferred a second time, because every write endpoint after this one inherits whatever shape the first one takes.

---

## What was measured

Probed 2026-08-07 against the versions in the lockfile (django-ninja 1.6.2, Django 5.2.16, pydantic 2.13.4) and against the installed Angular 22.1.0, by reading the installed source and then running the behaviour end to end.

**django-ninja's session authentication, and the trap under it.**

| Case | Result |
|---|---|
| unauthenticated, default test client | `401 {"detail": "Unauthorized"}` |
| authenticated, default test client | `200` |
| authenticated, `Client(enforce_csrf_checks=True)` | `403 {"detail": "CSRF check Failed"}` |
| authenticated, strict, with the CSRF token | `200` |

`django_auth` is `SessionAuth`, which subclasses `APIKeyCookie`, whose `__init__` takes `csrf: bool = True` and runs `check_csrf`. Django's default test `Client()` carries `enforce_csrf_checks=False`. **So a suite written with the default client goes green while the real browser POST is refused**, which is this project's recurring failure shape rather than a new one.

**The two stacks disagree on the token's name, and neither default is wrong.** Django ships `CSRF_COOKIE_NAME = "csrftoken"` and `CSRF_HEADER_NAME = "HTTP_X_CSRFTOKEN"`; Angular 22.1.0 ships `XSRF-TOKEN` and `X-XSRF-TOKEN`, with `withXsrfConfiguration` provided to change them. Neither name carries a security property: the mechanism is the double-submit pattern, and what secures it is that the cookie is readable by same-origin JavaScript (Django's `CSRF_COOKIE_HTTPONLY` defaults to `False` precisely for this, and setting it `True` breaks the pattern without buying anything), that a cross-origin page cannot set a custom header, and `SameSite`.

**The topology is the thing that actually decides, and today it is wrong.** There is no reverse proxy in `infra/`; the api publishes 8000 and the web 4200, and no CORS is configured anywhere. Cross-origin cookies would require `SameSite=None`, which requires `Secure`, which requires HTTPS that development does not have, plus CORS with credentials, `withCredentials`, and `allowedOrigins`. That is seven settings across two stacks whose common failure mode is a silent `403` in production over a green suite. Same-origin collapses it to two.

---

## Decision

### 1. The authenticated request is a Django session, and CSRF stays on

The web client authenticates with Django's own session and django-ninja's `django_auth`. It is the most-exercised authentication path in this ecosystem, and under decision 2 `SameSite=Lax`, which is Django's default, refuses the cross-site POST on its own; the CSRF token is then the second layer rather than the only one, which is the shape [OWASP asks for](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html) when it says `SameSite` co-exists with a token rather than replacing it.

**The consequence that binds the suite:** a test exercising a write endpoint uses `Client(enforce_csrf_checks=True)`. The default client is the measurement above wearing a green checkmark.

### 2. The web client and the API are served on one origin, and this is a requirement rather than an observation

**What satisfies it is deliberately not decided.** In development the Angular dev server proxies the API path, which is one `proxyConfig` key on the `serve` target and one JSON file, no container and no reverse proxy. In production the requirement stands and the thing that meets it, a reverse proxy, a CDN, or something else, is chosen when a deployment target exists, which is the same trigger that already holds back `infra/compose.prod.yaml`.

Recording the requirement rather than the tool is the whole point: the security posture of decision 1 rests on it, and a premise that lives only in somebody's head is how a `SameSite=None` gets added one afternoon to make a demo work.

### 3. The CSRF names stay Django's, and the web client is what adapts

`withXsrfConfiguration({cookieName: 'csrftoken', headerName: 'X-CSRFToken'})` in the web client. One line, in the stack that owns the concern.

**CSRF is a browser concern and only a browser concern**, which is what makes this the right side to adapt. A Tauri webview is a browser and inherits it unchanged. Flutter is not, will never see a CSRF token, and reaches this system under decision 5. Changing Django's defaults instead would move a value that every middleware, every piece of its documentation and every debugging `curl` assumes, to buy nothing.

### 4. The mechanism lives at one point, and nothing below it knows what it is

The authentication callable resolves a request to a principal, and everything downstream, the `user_scope` binding, the membership verification, the tenant binding and the services, consumes **the principal** and never the mechanism. Swapping session for something else is then a class, not a refactor.

This is the same rule the codebase already applies to effects (`specs/testing.md` section 3), applied to the one boundary that is most likely to change.

### 5. The token path is the named exit, and its trigger is a client that is not a browser

`apps/mobile` cannot carry a session cookie comfortably and `apps/desktop` reaches the API from a webview whose origin is its own. **When the first non-browser client is built, the mechanism at decision 4's single point gains a bearer-token implementation**, and this ADR is amended with a dated note rather than superseded. Nothing about the wall, the binding or the verification moves, which is what decision 4 buys.

The token's lifetime, its rotation and the offline-authenticated window are **not** decided here and are not this ADR's: they are the open half of PRD T5.2 and OQ-18, and they are about proving authorship on an operation created offline, which is a different question from transporting a session on a request.

> **Note (2026-08-07), from the MAP-34 review, and it is the one thing this trigger must not meet unprepared.** The seam types its principal as a structural contract, which is what lets tier 0 name an identity without importing a domain model. **Nothing statically binds the mechanism's output to that contract**, because the framework assigns it dynamically and types it loosely, so the type checker verifies every *consumer* and no *supplier*. Today that holds by inspection (the session mechanism yields the user model, whose identifier is the M3 one) and it is pinned at runtime as a side effect, because the suite's binding recorder parses the bound value and a non-conforming identifier raises there. **When this decision's trigger fires, that safety disappears in both directions at once:** a token implementation returning a record, a string or a mapping type-checks everywhere, and a session-cookie suite exercises none of the token path. So the conformance assertion this seam does not owe today is owed **by the slice that lands the token**, and it is named here rather than left to be rediscovered.

### 6. The tenant is read from the envelope and verified, never trusted and never duplicated

PRD M8 requires the envelope to be self-describing enough to route without inferring from context, and M9 makes a target carry its ancestors, so the tenant already travels there by contract. A second copy in a path or a header would be exactly the duplication this repository's governance exists to prevent.

**So the claim is read from the envelope and checked against the principal** through `memberships_of_the_session_user()`, which answers with only the user binding in force (ADR-0005 section 8) and is therefore available before any tenant is bound. All operations of one flush must agree on their tenant, and a disagreement is a typed refusal; ADR-0004 already makes cross-project atomicity inexpressible and ADR-0005 section 3 already refuses a second binding, so one flush addressing one tenant is forced rather than chosen.

**A claim the principal cannot back is refused as not-found**, indistinguishable from a resource that never existed, which is PRD T6.5's cross-tenant half rather than this ADR's invention. The refusal happens **before** the binding, so the wall is never asked to police a value it was configured from.

> **Addition (2026-08-07), closing the MAP-34 Window A review, which found three contract facts this decision left for a window to invent.**
>
> **The route is `POST /api/operations` and its body is `{"operations": [<client half>, ...]}`.** The named key rather than a bare array is the point: a bare `list[ClientHalf]` binds (measured, `specs/dependencies.md` section 1) and would have to change shape the moment MAP-12 adds the echoed cursor to the response's sibling request contract, so the key is what lets this grow without a wire break. This ADR fixes the request shape; **the response body stays MAP-10's** and nothing here constrains it.
>
> **What this decision turned out to be load-bearing for, recorded 2026-08-11 because it was not visible when the decision was taken.** Fixing one tenant and one project per flush **fixes the domain of the mutation-number contiguity rule**, and therefore the key of the per-client cursor: the guarantee that a hole in the stream means loss holds only while the stream has one destination, so PRD M10's contiguity and PRD M4's cursor are both keyed by clientID, tenant and project. **The MAP-12 pickup keyed the cursor on tenant and clientID alone and had to be corrected at its own review**, because the project half of this decision was one day old and nobody read the two together. The general shape is in `specs/log.md`: a decision that partitions a request partitions every per-client guarantee measured across requests.
>
> **An empty batch is its own typed refusal and is not a disagreement.** A batch of no operations does not disagree with itself, it names no tenant at all, so there is nothing to verify and nothing to bind. Collapsing the two into one exception makes two different refusals indistinguishable to the client, which is the same defect this decision refuses on the first-wins read. Two named refusals, not one.
>
> **Not-found is a property of the whole response, not of its status line.** T6.5 says indistinguishable from a resource that never existed, so a body naming the tenant, the membership, or the reason defeats it while the status code still reads 404. The testable form is comparative: **the answer to a claim on a real tenant the principal does not hold, and the answer to a claim on a tenant that does not exist, are the same response.** Anything that differs between those two is the leak. **The comparison is over the status and the body**, settled the same day: both requests are identical in shape so the headers are set by the same middleware for both, and comparing them would pin framework noise inside a test about a leak. The leak T6.5 describes lives in the body.
>
> **The availability probes are exempted from the credential, explicitly and by name.** Putting authentication on the API makes every published operation require one, so without an exemption N12's liveness and readiness stop being reachable and a probe that cannot answer restarts a healthy service. The exemption is a **direct consequence of decision 4**: the mechanism sits at one point, so what that point does not cover has to be stated rather than left to whichever route forgot to ask. **Written here 2026-08-07 after a review found it recorded only in the MAP-34 task spec while this ADR was the document being cited for it**, which is the fan-out defect the canon rule names and the third instance this week; the rule that governs which routes may be published without a credential belongs where the next task will look for it, not inside a closed task's spec.
>
> **Both malformed-batch refusals answer `422`, and they are told apart by their bodies.** Ratified 2026-08-07 rather than left as a window's derivation, because three tests rest on it and MAP-10 inherits it. It is not a product decision: it follows from C5, since the batch is refused where Pydantic validates the boundary, and it is django-ninja's own answer to a body that violates the contract it declares. **Refusing at the boundary is also what makes "nothing was bound" true by construction** rather than by the diligence of whoever writes the handler, which is the property decision 6 exists to protect. The two refusals stay distinguishable in the body, per the clause above; the status is what they share.

> **Addition (2026-08-10), at the MAP-11 pickup: one flush addresses exactly one project as well, and the reason was already half of the argument for the tenant.** The paragraph above forces one tenant per flush and cites ADR-0004's cross-project inexpressibility as one of the two things that force it, then fixes the refusal on the tenant alone. The project half stayed implied and unenforced, which was harmless while nothing took a per-project lock and stops being harmless at MAP-11, where the ADR-0004 allocation **is** that lock.
>
> A batch spanning two projects takes two locks, which puts back the repeated acquisition the RANGE rule exists to remove and opens a deadlock between two flushes that order their locks differently. The heavier objection is not performance: one transaction covering both makes the batch **atomic across projects**, which ADR-0004's Consequences state is not expressible under this strategy. So the batch composition rule is not a new decision here, it is the enforcement of one that was already taken and never written down.
>
> **A batch whose operations disagree on their project is therefore a third typed refusal beside the two named above**, at the same Pydantic boundary, answering `422` and told apart by its body, under every clause of the addition above. The cost falls on the client, which groups its queue by project before flushing; that is work it already owes, because the resync cursor is per project.
>
> **What this deliberately does not answer:** an operation whose target carries no project at all. The M9 target ladder has a tenant granularity, and the closed catalog declares no member at it today, so the case is unreachable rather than handled. When a tenant-granularity operation joins the catalog, this decision is what it must be reconciled against.

> **Addition (2026-08-11), at the MAP-12 Window A review: one flush addresses exactly one clientID, and the order the three agreements are checked in is part of this decision.** A batch whose operations disagree on their clientID is a **fourth typed refusal** beside the three above, at the same Pydantic boundary, answering `422` and told apart by its body, under every clause of the additions above.
>
> **This is enforcement of a rule the repository already practised, which is the same footing the project half stood on.** `client_id` had **no reader in `apps/api` at all** until this task: the field has travelled on every envelope since MAP-7 and nothing on the server consulted it, which is why its batch composition never had to be decided. Meanwhile every multi-operation batch in the sync suite already pins one, by hand, with the variable named `one_client`, and `test_project_version_allocation.py`'s helper states the rule in its own docstring: *one client's queue, in one project of one tenant, in contiguous mutation order*. Three windows wrote that independently. What was missing was the boundary, not the belief.
>
> **What forces it is the response contract rather than a lock.** T2.3 has the server echo **the** last-applied number and C12 has the client advance from that echo alone, so the answer carries one number. A batch of two installations has no defined echo, and whichever cursor the implementation picks, the other installation advances onto a number the server never applied for it, which is the silent client-side loss C12 exists to prevent. The alternative shape, an echo keyed per clientID, is a map that carries exactly one entry for every batch a correct client can produce, since **two installations cannot share one HTTP request**.
>
> **The clientID is checked last, and that position is empirical rather than aesthetic.** Four cases in `apps/api/tests/test_authenticated_request.py` build batches that disagree on their tenant or their project **and disagree on their clientID as well**, because `a_feature_create_claiming` mints a fresh one whenever a caller does not pin it. A clientID check reached before either of those hands those batches the wrong refusal, and **two of the four assert the status and the empty binding list without ever comparing the body**, `test_a_disagreeing_batch_binds_nothing_rather_than_the_tenant_its_first_operation_claims` and `test_a_batch_disagreeing_on_its_project_binds_nothing_rather_than_the_tenant_they_share`, so **both would keep passing for the wrong reason**. (Corrected 2026-08-11 at the fourth review: the first form of this sentence said one case and cited it by line number, which understated its own argument and would have rotted the first time anything was inserted above it. Cases are cited by name here because a name greps.) An implementing window may not edit them. The full order is therefore tenant, then project, then clientID, and **the two halves of that sentence rest on different things, which is written out because the first form of this paragraph fixed the whole order while arguing only the last position** (corrected 2026-08-11 at the Window A round that had to test it). Tenant before project is the rule the existing validator already carries in its own comment, that the order between these checks is contract and not sequence; **what this addition establishes is only that the clientID comes after both**, and no evidence here argues the relative order of the two that precede it.
>
> **Where this would live if the owed document existed.** PRD M8's Open / ADR names *the wire encoding of the envelope and the batching format of a flush* as an ADR; MAP-33 carries the wire-encoding half and cites only that, so **the batching-format half has no issue and no home**. Until it does, the four composition rules stay here, because here is where the other three are and where the next reader will look.

> **Addition (2026-08-11), and it retires this decision's own declination: the flush response is `{"last_applied_mutation_number": <integer>}`.** The addition of 2026-08-07 said the response body stayed MAP-10's and that nothing here constrained it, which was right while MAP-10 and MAP-11 both answered with none. **MAP-12 gives it one, so the declination has to become a decision rather than lapse into whatever a test module happened to name.** It was found as a constant in a test file at that task's review, which is a public wire contract decided in the one place with no reader outside the suite.
>
> **The key names its axis rather than reading `last_applied`**, because PRD M10 has five version axes and forbids any code path reading one as another, and this body **grows**: MAP-22 adds the per-project version to the same object as the resync cursor, and a bare name would then sit beside a second number it could be confused with. **The client reads this and nothing else to advance**, per T2.3 and C12, so the object is closed rather than open: an unexpected key is a contract change and goes through this ADR.
>
> **What this deliberately does not answer:** the shape once MAP-22 adds the second axis, and whether the two travel as siblings or nested. That is that task's, and this addition exists so it inherits a named key rather than a convention.

> **Addition (2026-08-13), at the MAP-13 pickup: this route gains a second answer, it is `409`, and it carries why it refuses rather than only where to restart.**
>
> Every refusal this decision has named so far is taken at the Pydantic boundary and answers `422`, which holds because each of the four is decidable from the request body alone. **A gap against the cursor is not.** Deciding it needs the cursor, which needs the tenant bound and a read, so it is taken after the binding and cannot join the four without lying about which contract was violated: the batch satisfies the one this decision declares.
>
> **So a gap answers `409` with a closed object, and the status is load-bearing rather than a free pick.** `200` is the shape that had to be refused. A client reading the status and not the body would take a refusal for an acknowledgement, and under C12 it advances its cursor from the echo alone, so on its next flush its own dedup would drop exactly the operations the gap was reporting. That is the silent loss this response exists to prevent, reintroduced one layer above it. **I9's scar is why the distinction has to be visible at all:** a client recovers from a lost acknowledgement by resending the same batch and from a gap by resending from the cursor, and an answer it cannot tell apart from a transport failure sends it to the wrong recovery.
>
> **The object carries a reason from a closed set of two, because the gap and the absent cursor are not the same refusal.** PRD M10 names the first a resend-from-cursor response and PRD M4 names the second a reconciliation, and MAP-13's issue treats them as one on the argument that an absent cursor is a gap from nothing. **That is true of the comparison and false of the remedy.** A client meeting a gap holds the missing operations in its persistent queue and can resend them. A client the server holds no cursor for **may not hold them at all**, because the cursor may have been collected under a policy MAP-42 has not written yet, so telling it to resend from the first mutation number asks for what it no longer has. One status, one object, two named reasons, so the recovery can differ where the remedy differs and MAP-42 inherits the distinction rather than having to add it.
>
> **The keys are `reason` and `resend_from_mutation_number`, and the second names its axis for the reason the addition of 2026-08-11 gives:** PRD M10 carries five version axes and forbids any code path reading one as another, and a bare `resend_from` sitting in a response beside `last_applied_mutation_number` is the confusion that rule exists to refuse. The restart point is an integer for `gap_above_cursor` and null for `no_cursor_in_this_domain`, where there is nothing to restart from, and the null is what makes the second reason actionable instead of decorative.
>
> **The integer is the cursor plus one, the first mutation number the server has not applied, and this sentence exists because the value was decided nowhere.** Added 2026-08-13 at the Window A review, where the Canon and the Spec axes reached it independently and the window itself reported it as the one choice it was not confident in. **It is the defect the addition of 2026-08-11 exists to close, arriving one round later:** a public wire contract living as a constant in a test module. PRD M10's prose asks the client to "resend from the cursor" and reads the other way, so the two had to be reconciled rather than left to whichever reader got there first. **Plus one wins on two grounds that are already in the code and in the name.** The dedup keeps operations strictly above the cursor (`the_operations_this_cursor_has_not_seen`), so the first number the server still needs is the cursor plus one, and any other value gives one axis two meanings. And the key reads `resend_from`, so a client handed the cursor itself would have to add one, which is the off-by-one that must not live on a wire.
>
> **Contiguity inside the batch is a fifth composition rule and stays at `422` beside the other four.** A batch whose own mutation numbers **do not ascend by exactly one at every step** is refused from the request body alone, so it is refused where nothing has been bound, which is the property the addition of 2026-08-07 says these refusals exist to protect. **That phrasing is a correction of the same day, and the first form is why it is written out rather than fixed in silence:** it read "skip, or arrive out of ascending order", and **a batch repeating a number is neither**, since a repeat is non-decreasing and skips nothing. Two things rested on the gap. PRD M10's Shape calls the axis contiguous and a repeat is not, so a real violation had no refusal; and the positional argument in the paragraph below **is about batches that break the rule by repeating zero**, so under the first form it argued from a refusal that would never have fired. Found by the Spec axis at the Window A review, which noticed the tests covered only the skipping arm, and confirmed by reading the one shape the Craft axis had ruled out: a check written as a set against a range admits a repeat, because a repeat vanishes into the set. **Ascending is part of the rule rather than a nicety:** `append_to_the_operation_log` stamps the per-project version in list order, so a batch contiguous as a set and shuffled as a list records a chain in an order the client never authored, and PRD M15 replays that order as evidence.
>
> **The fifth check is taken last, after the three agreements, and that position is empirical exactly the way the clientID's was.** `apps/api/tests/test_authenticated_request.py` builds its disagreeing batches from `a_feature_create_claiming` without pinning a mutation number, and that helper defaults every operation to zero, so **those batches collide on their mutation numbers as a side effect of a default nobody chose for this purpose**. A contiguity check reached before the tenant or the project hands them the wrong refusal, and the two cases the addition of 2026-08-11 already names, `test_a_disagreeing_batch_binds_nothing_rather_than_the_tenant_its_first_operation_claims` and `test_a_batch_disagreeing_on_its_project_binds_nothing_rather_than_the_tenant_they_share`, assert the status and the empty binding list without comparing the body, so **they would keep passing for the wrong reason a second time, one position further down**. Measured 2026-08-13 at the MAP-13 pickup by reading the fixtures rather than by reasoning about them. The full order is therefore tenant, then project, then clientID, then contiguity, and an implementing window may not edit those cases.
>
> **What this deliberately does not answer:** how a client rehandshakes after `no_cursor_in_this_domain`, which is MAP-42's along with the collection policy that produces it, and whether a later reason joins the closed set, which goes through this decision the same way an unexpected key does.

### 7. The session store is the database until Redis exists

Django's `SESSION_ENGINE` defaults to `backends.db`, one primary-key lookup per authenticated request. Beside a flush that opens a transaction, sets a parameter, verifies a membership and inserts in bulk, that is noise, and PRD N1 is a floor rather than a target to optimise against without a number.

**Redis is ratified in foundation section 10 and is not in `infra/compose.yaml` yet.** When it lands, `cached_db` removes the query. That is a named trigger, not work, and it is recorded here so the default is a decision rather than an oversight.

---

## Consequences

**What this buys.** The first server-side write path gets a principal before it gets a writer, so no endpoint in this system is ever born taking its tenant from the caller. The security posture rests on two settings that fail loudly instead of seven that fail silently. And the piece most likely to change is the piece nothing depends on the shape of.

**What this costs, accepted with eyes open.**

- **The same-origin premise is not true today**, and MAP-34's suite cannot prove it, because the Django test client is same-process and exercises neither origin nor cookie. **The first real browser request is what proves it, and that is MAP-20**, which gains the dev-server proxy as a prerequisite. This is named rather than discovered, which is the whole difference.
- **A write test that forgets `enforce_csrf_checks=True` passes for the wrong reason.** The measurement is in the table above and in `specs/dependencies.md`.
- **One database query per authenticated request** until decision 7's trigger fires.
- **A second authentication implementation will exist** when decision 5 fires. That is two implementations of one seam, which is the cost decision 4 is designed to bound.

**What this forecloses.** Cookie-borne authentication across origins, which is what `SameSite=None` would mean and what decision 2 refuses by construction. Nothing the foundation left open: the offline authorship proof (OQ-18), the credential lifetime (T5.2) and the permission model above membership (T6.2, OQ-7) are all untouched.

**What must be revisited, and when.** Decision 5's trigger is the first non-browser client. Decision 7's is Redis entering compose. Decision 2's production half is the first deployment target. And if the same-origin premise is ever abandoned, decision 1 is what has to be reopened with it, because it is the premise the whole posture rests on.
