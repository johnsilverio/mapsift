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

### 6. The tenant is read from the envelope and verified, never trusted and never duplicated

PRD M8 requires the envelope to be self-describing enough to route without inferring from context, and M9 makes a target carry its ancestors, so the tenant already travels there by contract. A second copy in a path or a header would be exactly the duplication this repository's governance exists to prevent.

**So the claim is read from the envelope and checked against the principal** through `memberships_of_the_session_user()`, which answers with only the user binding in force (ADR-0005 section 8) and is therefore available before any tenant is bound. All operations of one flush must agree on their tenant, and a disagreement is a typed refusal; ADR-0004 already makes cross-project atomicity inexpressible and ADR-0005 section 3 already refuses a second binding, so one flush addressing one tenant is forced rather than chosen.

**A claim the principal cannot back is refused as not-found**, indistinguishable from a resource that never existed, which is PRD T6.5's cross-tenant half rather than this ADR's invention. The refusal happens **before** the binding, so the wall is never asked to police a value it was configured from.

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
