# MAP-27: the login path can ask which tenants a user belongs to, without a hole in the wall

## Trace

PRD M1, T6.1, T6.5; foundation I4; C4. The decision this task implements is **ADR-0005 section 8**
(added 2026-08-05), which extends decisions 3 (the binding), 4 (the guard), 5 (indexes) and 7 (the
catalogue tests) of the same ADR. Where the read path lives is ADR-0007.

## What this task owns

An authenticated user's own memberships are enumerable with no tenant bound, through the `accounts`
read path, with every other guarantee of the wall unchanged.

## Out of scope

- The HTTP login surface. Deferred with its trigger recorded in ADR-0005 section 8 (owner, 2026-08-05).
- The permission model above the wall (T6.2 to T6.5), which the issue itself excludes.
- The `accounts` creation services the shared fixtures work around (`specs/log.md`, 2026-08-04): a
  different seam.

## Boundary decisions the owner closed

2026-08-05, all registered before this file was written: the mechanism, the binding scope and the
surface deferral in ADR-0005 section 8; the ADR convention that amendment rode in on in ADR-0001's
conventions note. This is the pointer, not the record.

## Evidence handed over

Nothing was measured for this task. Everything it rests on is the probe table of ADR-0005, and the one
measurement worth re-reading before writing a test is C, the empty-string trap, which applies to the
new parameter identically.

## Acceptance

ADR-0005 section 8, test case 6, with decision 7's cases 1 to 5 unchanged.
