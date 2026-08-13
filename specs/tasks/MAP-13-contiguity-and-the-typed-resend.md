# MAP-13: the server applies a stream only in contiguous order, and answers a hole by asking for it back

## Trace

PRD **M10**'s Requirement and its acceptance **as narrowed 2026-08-13**, which is the ordering rule this task
exists for, and **M10**'s Shape for the axis and its first value. PRD **M4**'s Requirement and acceptance for
the missing-cursor case. PRD **T2.3** for the dedup this runs beside and must not disturb, and PRD **M15** for
why the order a batch arrives in is not cosmetic. Invariants **I9** and **I2**; constraints **C12**, **C2**
and **C4**. **ADR-0010** decision 6 with its additions of 2026-08-07, 2026-08-10, 2026-08-11 and
**2026-08-13**, which carry the batch composition rules, the refusal boundary and both response shapes.
**ADR-0004** decision 2 for why a refused batch never reaches the allocation. **ADR-0005** sections 1, 2 and 3
for the wall, the grants and the transaction-scoped binding. **ADR-0007** sections 1 and 3 for where a file
goes and what it may import.

## What this task owns

The comparison between a batch's mutation numbers and the cursor that installation left behind, taken before
anything is applied, and the second answer this route gains when that comparison fails.

**The route, the request body, the dedup, the cursor, the append and the version allocation already exist**
(`mapsift/sync/`, delivered by MAP-34, MAP-10, MAP-11 and MAP-12). This task adds the refusal that stands in
front of them, and it closes by construction the silent-loss shape MAP-12 left open and recorded in its issue:
a batch of zero and five against an absent cursor applies both and echoes five, so a later batch carrying one
to four is deduplicated away and echoed as applied.

## Out of scope

Named with the owner of each, because a vague boundary is the measured root cause of a window doing work
nobody asked for.

- **The cursor's expiry and collection, and how a client rehandshakes after being told the server holds no
  cursor for it.** **MAP-42**. This task produces that answer; it does not decide what makes it happen or what
  the client does next.
- **The two-connection harness.** **MAP-43**. Nothing in this task needs two concurrent flushes to be
  witnessed, and a case that would need one belongs there.
- **The per-project version in the response.** **MAP-22**, which inherits a named key from ADR-0010 decision 6
  rather than a convention.
- **The per-feature version.** MAP-38. **The correlation keys on the flush path.** MAP-14. **The author
  normalization.** MAP-37.
- **The check that a batch's project belongs to the verified tenant.** **MAP-39**, and this task does not close
  it. It narrows the blast radius by refusing an unknown domain that starts above the first mutation number
  instead of applying it, and the authorisation hole ADR-0004 decision 4 records is untouched.
- **Any read of the log, and no projection.** The refusal is decided from the batch and the cursor, never by
  querying what was written before.
- **Every client half:** minting the clientID, persisting the queue, advancing from the echo, and reacting to
  either refusal. MAP-15, MAP-17 and MAP-19, in milestones 4 and 5.
- **The generated TypeScript for the second response shape.** MAP-35.

## Boundary decisions the owner closed

All four were ruled 2026-08-13 and written into the documents that own them **before this file existed**. This
block is the pointer, not the record; a window reads the cited section.

1. **A gap against the cursor answers `409` with a closed object**, because the batch satisfies the contract
   the boundary declares and because a `200` would let a client that reads the status and not the body take a
   refusal for an acknowledgement. **ADR-0010 decision 6**, addition of 2026-08-13, which carries the argument
   and I9's scar behind it.
2. **The object carries a reason from a closed set of two**, so the gap and the absent cursor stay
   distinguishable where their remedies differ. **ADR-0010 decision 6**, same addition, which also fixes both
   keys and why the restart point names its axis.
3. **A batch whose own mutation numbers do not ascend by exactly one at every step is a fifth composition
   rule**, refused at the Pydantic boundary with `422` beside the other four, and **taken last, after the
   three agreements**. **ADR-0010 decision 6**, same addition, which carries the measurement that fixes the
   position, and whose correction of 2026-08-13 is the reason this line does not read "skip, or arrive out
   of ascending order": a batch repeating a number is neither, and under that form it had no refusal.
4. **A gap refuses the whole batch and applies nothing at all**, rather than the wider form that would let a
   flush both apply and refuse. **PRD M10's acceptance**, narrowed the same day, which carries why C12 makes
   the wider form untenable.

**Deliberately left to the implementing window**, and a review that asks for a different one needs a reason
that is not preference: where the comparison lives between `rules.py` and `services.py` under ADR-0007
section 3, which expression decides contiguity, and how the two response shapes are declared on one route.
The acceptance says what must be true, never which symbol makes it true.

## Evidence handed over

Transcribed rather than cited, because it exists nowhere else yet.

- **A green case posts a batch that starts below the cursor**, and it is I9's first acceptance clause:
  `test_a_queue_resent_whole_after_a_partial_flush_lands_only_what_was_missing` flushes two operations and
  then resends four, from zero, against a cursor the first flush left at one. Named because a name greps.
  **No conclusion is drawn here about what the rule must therefore be**, and the omission is deliberate:
  MAP-12's own review found a wrong inference riding through this block unchallenged, because
  `specs/testing.md` section 1.1 tells a window that handed-over evidence is not its to question. The fact is
  the hand-over; the rule is the window's.
- **`tenant_scope` opens `transaction.atomic()` itself** (`mapsift/common/binding.py`, measured 2026-08-10 at
  MAP-11 and repeated here because a window reads this file rather than its predecessor). A test whose only
  transaction is the one its own context manager opened is **green against an implementation that has none**,
  so anything asserting that a refused flush left nothing behind has to go through the route.
- **What was not measured, said plainly so nobody treats it as handed over:** nothing about what the
  comparison costs, whether it is cheaper beside the cursor read or as its own pass, and nothing about a batch
  large enough for the difference to be visible. No probe was taken. The bound on batch size is ADR-0004
  decision 3's and is not a measurement of this check.

## Acceptance

Each bullet names its own upstream, and nothing here is invented in this file.

**From PRD M10's acceptance, as narrowed 2026-08-13.**

- a flush with a gap above the cursor returns a typed resend-from-cursor response and applies nothing at all,
  rather than merely nothing from the gap onward

**From PRD M4's acceptance.**

- a client whose cursor was collected and then flushes above the first mutation number receives a typed
  reconciliation response rather than a silent re-apply

**From ADR-0010 decision 6's addition of 2026-08-13.**

- the two refusals are told apart by a reason from a closed set of two, and the one with nothing to restart
  from says so rather than naming a restart point it cannot justify
- a batch whose own mutation numbers do not ascend by exactly one at every step is refused at the boundary
  before anything is bound, and its refusal is distinguishable from the four it stands beside
- the contiguity check is reached after the tenant, the project and the clientID

**From ADR-0004 decision 2**, which the Trace already carries and whose guard this is at its limit.

- a flush that is refused takes no per-project version, because it never reaches the allocation

**From PRD T2.3, which this task must leave standing rather than re-prove.**

- a flush at or below the cursor is deduplicated with no error

**One clause is deliberately split, for the reason MAP-11 and MAP-12 both split one.** M10 has the response
ask the client to resend from the cursor, which is the cursor plus one as that requirement was sharpened
2026-08-13. The server half, that the answer carries the restart point and its reason, is this task's and is
provable today. The half where a client receives it and resends is MAP-15's and
MAP-19's, where a queue exists to resend from. Recorded here rather than done silently, because a task spec
that quietly loses half a clause is indistinguishable from one that never carried it.
