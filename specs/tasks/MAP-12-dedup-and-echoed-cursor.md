# MAP-12: the server remembers how far each installation got, and says so in its answer

## Trace

PRD **T2.3** (the mutation number, the dedup, and the echo) and **M4** (the clientID and its server cursor),
with **M10**'s Shape for the axis itself. Invariant **I9**; constraints **C12** and **C4**. **ADR-0004**
decision 2 with its extension of 2026-08-11, which places the cursor's read and its write on opposite sides
of the critical section. **ADR-0005** sections 1, 2 and 3 for the wall, the role grants and the
transaction-scoped binding. **ADR-0007** sections 1 and 3 for where a file goes and what it may import.
**ADR-0010** decision 6 for the request body and the boundary its refusals are taken at, and for the
sentence in which it declines to constrain the response.

## What this task owns

The server's memory of how far each installation has got, and the answer that hands it back. A flush
compares its batch against the per-client cursor, ignores what is at or below it, applies the rest, advances
the cursor, and **answers with the last-applied number**, which is the first response body this API has
carried.

**The route, the request body, the append and the version allocation already exist**
(`mapsift/sync/api.py` and `mapsift/sync/services.py`, delivered by MAP-34, MAP-10 and MAP-11). This task
adds the comparison that runs before them and the answer that follows them.

## Out of scope

Named with the owner of each, because a vague boundary is the measured root cause of a window doing work
nobody asked for.

- **The contiguity check, the typed resend on a gap, and M4's missing-cursor reconciliation.** **MAP-13**,
  in this milestone. The third moved there on 2026-08-11 and the issue carries why. A batch with a gap above
  the cursor is applied by this task; refusing it is MAP-13's.
- **The cursor's expiry and collection, and the `last-seen time` M4's Shape names.** **MAP-42**, opened
  2026-08-11 at this pickup. No column for it, because the only thing that would read it is the policy that
  issue decides.
- **The per-feature version.** MAP-38.
- **The correlation keys on the flush path.** MAP-14.
- **The author normalization.** MAP-37.
- **The check that a batch's project belongs to the verified tenant.** MAP-39.
- **Any read of the log**, and no projection. The response is built from the cursor, never by querying what
  was just written.
- **The per-project version in the response.** MAP-22, whose shape depends on the gap protocol MAP-13 has
  not designed.
- **Every client half of the cursor**: minting the clientID, persisting the queue, and advancing the cursor
  from the echo. MAP-15, MAP-17 and MAP-19, in milestones 4 and 5.

## Boundary decisions the owner closed

All nine were ruled 2026-08-11 and registered in the documents that own them before the window that needed
each was dispatched. **The count read "seven" over a list of eight until Window B greped it**, which is the
smallest possible instance of the failure this whole task kept meeting: a sentence about a set, written once
and never re-read against the set.
This block is the pointer, not the record; a window reads the cited section.

**Two of them were defective and were corrected at this task's review on the same day**, which is why this
block says so rather than reading as though the pickup got it right. Decision 1 keyed the cursor on tenant
and clientID alone, contradicting a decision one day old; decision 6 was registered in the tracker only,
which is execution state and not contract. **Both were found by readers who had not written them**, which is
the property the review exists to buy and the reason a pickup's own confidence is not evidence.

1. **The cursor is keyed by clientID, tenant and project together**, matching the flush domain, and **an
   absent cursor is the absence of its row** rather than a stored zero. **PRD M4's Shape**, sharpened
   2026-08-11 and **corrected the same day at this task's review**, which carries why the first key was
   wrong. **PRD M10's Requirement** carries the matching domain for the contiguity rule and the reason it is
   fixed by ADR-0010 decision 6 rather than chosen.
2. **The first mutation number is zero.** **PRD M10's Shape**, sharpened the same day, with the reason it is
   the generated contract's call rather than a preference.
3. **The cursor is read early and written late**, the write guarded against moving backwards. **ADR-0004
   decision 2**, extension of 2026-08-11, which also refuses one shape by name.
4. **A resent operation the server already holds is answered as applied rather than refused.** **PRD T2.3's
   acceptance**, added the same day.
5. **The response carries the echoed last-applied and nothing else in this slice.** T2.3 already requires the
   echo and **ADR-0010 decision 6 declines to constrain the response body**, so this is scope rather than a
   new rule.
6. **A batch deduplicated away entirely allocates nothing** (**ADR-0004 decision 2**, moved there 2026-08-11
   from the issue that first held it, beside the cost model that is the reason for it) **and still echoes the
   existing cursor** (**PRD T2.3**, whose requirement sentence has the server echo the last-applied number
   whether or not this flush moved it). The two halves are cited separately because the first form of this
   line credited both to ADR-0004, which carries only the allocation half.
7. **M4's reconciliation and M4's retention each left for a named issue**, as in Out of scope above.
8. **A flush addresses exactly one clientID**, and **the three agreements are checked tenant, then project,
   then clientID**. **ADR-0010 decision 6**, addition of 2026-08-11, which carries both the evidence that
   made this enforcement rather than a new rule and the four existing cases that fix the order. Taken after
   the review rather than at the pickup, because it is a **precondition of this task's own deliverable**: a
   dedup keyed by clientID has to read one off the batch, and reading it off the first operation applies one
   installation's cursor to another's work.
9. **The flush answers `{"last_applied_mutation_number": <integer>}`, a closed object.** **ADR-0010
   decision 6**, addition of 2026-08-11, which retires that decision's own earlier refusal to constrain the
   response body now that a body exists, and says why the key names its axis rather than reading
   `last_applied`.

**Deliberately left to the implementing window**, and a review that asks for a different one needs a reason
that is not preference: which single statement advances the cursor row, and where the comparison lives
between `rules.py` and `services.py` under ADR-0007 section 3. The acceptance says what must be true, never
which symbol makes it true.

## Evidence handed over

Transcribed rather than cited, because it exists nowhere else yet. The first three were measured at MAP-11
and are repeated here because they bite this task in the same place, and a window reads this file rather
than its predecessor.

- **`tenant_scope` opens `transaction.atomic()` itself** (`mapsift/common/binding.py`, read 2026-08-10). A
  test whose only transaction is the one its own context manager opened is **green against an implementation
  that has none**, so anything asserting that the read and the write share a transaction has to go through
  the route.
- **The wall's suite cannot see a table that does not carry the tenant column** (read 2026-08-10).
  `apps/api/conftest.py`'s `tenant_owned_tables` enumerates from the catalogue **by that column**, and every
  case in `tests/test_tenant_isolation.py` consumes that set. A cursor table built without it does not fail
  those cases, it **disappears from them**. A width assertion does not close it either.
- **The append-only grant does not reach the owner profile**, and migrations, tests and CI all connect as the
  owner (ADR-0005 section 2, correction of 2026-08-07). ~~A grant assertion written against the owner proves
  nothing.~~ **That conclusion was wrong and is struck rather than deleted, because it was handed over as
  measured evidence and a window is told not to question those.** The premise holds and the inference does
  not: a connection as the owner cannot prove anything about **its own** privileges, and it is exactly what
  can ask about **another role's**. `test_append_only_log.py` has asserted the log's whole grant that way
  since MAP-10, through `has_table_privilege(<role>, <table>, <privilege>)` with the runtime role passed as a
  parameter. Found by the Spec axis at the Window B review, after the wrong form had already reached a module
  docstring on disk.
- **What was not measured, said plainly so nobody treats it as handed over:** nothing about contention on the
  cursor row, and nothing about whether the comparison is cheaper as one query or as a join against the
  batch. No probe was taken. ADR-0004's extension decides the **placement** of the read and the write on the
  argument that a second row lock inside the critical section is a second thing that can be held too long,
  and that argument is not a measurement of this table.

## Acceptance

**Nothing here is invented in this file, and each bullet names its own upstream** rather than leaving one
attribution to cover a list, which is the defect the Spec axis found in this block's first form: it credited
the whole list to T2.3 "and for the last bullet" to an ADR, while the ADR's bullet was the first.

**The three from PRD T2.3's acceptance, pasted rather than paraphrased.** The first form of this block
reworded two of them, which is the middle ground the same day's `log.md` entry says does not exist.

- interrupt a flush after the server applies part of the queue, resend the full queue, and the final state
  is identical with no duplicated feature and no lost edit
- two clients of the same user (distinct clientIDs) do not collide and neither loses an operation to false
  dedup
- an operation the server already holds, resent and surviving the dedup filter because it arrived under a
  different mutation number, is answered as applied rather than refused, **so the flush succeeds and echoes**

**From ADR-0010 decision 6's addition of 2026-08-11.**

- a batch whose operations disagree on their clientID is refused at the boundary, before anything is bound,
  and its refusal is distinguishable from the three it stands beside
- the clientID is checked after the tenant and after the project

**From PRD M4's Shape and ADR-0004 decision 2, both as corrected 2026-08-11.** These were provable only from
the Boundary block until the Spec axis pointed out that a reader checking tests against this block alone
reads their witnesses as uncommissioned work.

- a cursor is keyed by clientID, tenant and project, so one installation's two projects never dedup against
  each other
- a batch deduplicated away entirely takes no per-project version
- the flush answers with the last-applied mutation number, which is the server half of T2.3's echo clause
  and is promoted here from this block's closing prose, where three cases already rested on it

**The three words in bold were dropped from this bullet when this file was first written on 2026-08-11, and
the Spec axis caught it the same day.** They are T2.3's and they are load-bearing: that path is the only one
where *applied* and *inserted* come apart, so an implementation that answers with a stale cursor there
satisfies the short form, and under C12 the client advances only from the echo and resends that operation
forever. This file's own closing paragraph names the defect it then committed.

**One T2.3 clause is split rather than carried whole, and it is split because half of it has no runtime
yet.** T2.3 reads "the client advances its cursor from the echoed last-applied". The server half, that the
flush answers with the last-applied number, is this task's and is provable today. The client half is
MAP-15's and MAP-19's, where a queue and a cursor exist to advance. This is the same move MAP-11's spec made
with the batch-bound clause, and it is recorded here rather than done silently, because a task spec that
quietly loses half a clause is indistinguishable from one that never carried it.
