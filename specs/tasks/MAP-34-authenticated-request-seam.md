# MAP-34: a request arrives with a principal, and the tenant it claims is verified before anything is bound

## Trace

**ADR-0010**, which is this task's decision document and was written at its pickup. PRD **T5.1** (the
authoritative identity is the authenticated session, "not a free client field"), **T6.1** and **T6.5** (the
cross-tenant denial is indistinguishable from a resource that does not exist), **M8** (the envelope is
self-describing enough to route without inferring from context). Invariants **I4** and **I10**; constraints
**C4**, **C13**, **C5**. **ADR-0005** sections 3 and 8 for the binding and for the selector this consumes,
**ADR-0007** sections 1, 3 and 4 for where each file goes and what it may import.

## What this task owns

A request reaching a protected route carries a principal, and the tenant that request claims is checked
against that principal before any tenant binding is opened.

## Out of scope

Named explicitly, each with the owner it goes to.

- **The login endpoint.** Owner: **MAP-30**, which consumes this seam rather than building it.
- **The flush itself, the log table and everything transactional.** Owner: **MAP-10**, which this unblocks.
- **The bearer-token implementation.** Owner: the first non-browser client, which is ADR-0010 decision 5's
  named trigger. Building it now would be two mechanisms where one is needed.
- **The offline authorship proof and the credential lifetime.** Owner: OQ-18 and the open half of T5.2.
  `author_session_material` stays opaque and this task does not read it.
- **The permission model above membership.** Owner: T6.2, waiting on OQ-7. Membership is the only grant this
  task knows about.
- **The web client's side of the CSRF configuration and the dev-server proxy.** Owner: **MAP-20**, which is
  where the first real browser request happens and therefore the only place the same-origin premise can be
  proven. ADR-0010's Consequences say so.
- **The session store.** `SESSION_ENGINE` stays Django's default; ADR-0010 decision 7 names the Redis
  trigger that changes it.

## Boundary decisions the owner closed

All on **2026-08-07**, and they are **ADR-0010's seven decisions** rather than a second list. Read them
there. The two that most shape what a test asserts: the tenant is **read from the envelope and verified**,
never trusted and never duplicated into a path or a header (decision 6), and the mechanism lives at **one
swappable point** with everything below it consuming the principal and never the mechanism (decision 4).

## Evidence handed over

Transcribed rather than cited, because it was bought with a probe and exists nowhere else in runnable form.
The full record is `specs/dependencies.md` section 1.

**The unauthenticated refusal is the framework's, not ours.** Measured at the pins: an unauthenticated
request to a route carrying `django_auth` returns `401 {"detail": "Unauthorized"}` with no code of ours
entered. That clause is therefore **asserted, never implemented**.

**Django's default test client hides the CSRF check.** `django_auth` is `SessionAuth` over `APIKeyCookie`,
whose `__init__` carries `csrf: bool = True` and calls `check_csrf`; `Client()` carries
`enforce_csrf_checks=False`. Measured: authenticated through the default client gives `200`, the same
request through `Client(enforce_csrf_checks=True)` gives `403 {"detail": "CSRF check Failed"}`, and with the
token `200`. **A test over a write route that uses the default client proves nothing about whether a browser
can reach it.**

**Measured on disk at the pickup.** `user_scope` and `session_user_in_force` exist in
`mapsift/common/binding.py`, and `memberships_of_the_session_user()` exists in
`mapsift/accounts/selectors.py`. **Neither has a single caller outside tests.** This task is what gives them
one. The `User` model is an `AbstractBaseUser` with `USERNAME_FIELD = "email"`, and
`django.contrib.sessions` with its middleware are already in place.

**What this suite cannot prove, stated so it is not mistaken for coverage.** The Django test client is
same-process: it exercises neither the origin nor the cookie, so the same-origin premise ADR-0010 decision 2
rests on is out of reach here and is MAP-20's to prove.

## Acceptance

From the requirements, with the clause of each this slice carries.

- **T5.1 and C13:** the identity the server acts on is the authenticated session's, never a field the
  request supplied. An unauthenticated request to a protected route is refused, and no binding is opened.
- **T6.5, cross-tenant half:** a request claiming a tenant the principal holds no membership in is refused
  as **not-found, indistinguishable from a resource that never existed**, and the refusal happens **before**
  the binding, so the wall is not what catches it. The within-tenant denial-with-resolution half of T6.5 is
  the permission model's and is not this slice's.
- **C4 and ADR-0005 section 3:** a claim the principal does hold binds exactly that tenant, transaction
  scoped, parameterised, once per request, with the binding discipline's two arms unchanged (same value
  re-entered is a no-op, a second value raises).
- **ADR-0005 section 8:** a user holding memberships in two tenants reaches each only by claiming it, and
  never the other in the same request. The selector answers with only the user binding in force, which is
  what makes the check possible before a tenant exists.
- **ADR-0010 decision 6:** all operations of one batch must agree on their tenant, and a disagreement is a
  typed refusal rather than a first-wins read.
- **ADR-0010 decision 1:** the suite exercises a write route through `Client(enforce_csrf_checks=True)`.
