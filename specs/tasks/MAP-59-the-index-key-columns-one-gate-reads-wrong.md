# MAP-59: An index's key columns are read one way, and that way sees an expression key

## Trace

Foundation **I4**; **C4**. **The operative requirement is two sentences and neither of them is case 4's
own**: **ADR-0005 decision 5**'s rule about a global unique index, which is what the gate's docstring cites,
and PRD **N2**'s acceptance clause naming the unique-key collision. Case 4 of **ADR-0005 decision 7** is where
the gate is listed and names only the foreign-key channel, so read it for placement and those two for the
rule. Decision 7 also carries the dated note of 2026-08-25 recording that the case as built is satisfiable by
a schema violating it. **ADR-0013 decision 5**, which grew the second copy of the same defect and consumes the helper
this task publishes. **ADR-0002 section 5** for how a mutant and a probe are run, amended 2026-08-25.

## What this task owns

Every catalogue gate reads an index's key columns through one reading, and that reading does not lose an
expression key.

**That is five call sites and not two, and converting all five is the ruling rather than the window's guess.**
`grep -rn "indkey" apps/api` returns `tests/test_tenant_isolation.py`, `mapsift/accounts/tests/test_account_tree.py`
twice, `mapsift/accounts/tests/test_login_memberships.py`, and MAP-51's untracked copy. Only the first two are
unsafe today: the `test_account_tree.py` pair is filtered to `indisprimary`, where an expression key cannot
occur, and `test_login_memberships.py` asserts an index **exists**, so a dropped entry fails closed. **They are
converted anyway**, because each is safe for a reason a later edit removes without anyone noticing, and because
ADR-0005's note asks for one helper "every catalogue gate calls" rather than for two fixed and three left.

## Out of scope

- **MAP-51's container-index gate.** It consumes this helper and is blocked on it. Publishing the helper is
  this task's; using it there is not.
- **Widening what the gates enumerate.** `relkind = 'p'` for a partitioned parent, `geography` and
  domain-typed geometry columns are each real and each is about **what** is enumerated rather than **how** an
  index is read. Unowned, and deliberately not opened here.
- **`prosecdef`**, a wider hole in the same wall than the one this task closes. *Reported as empty today by
  the MAP-51 research round and not re-measured here; no migration in `apps/api` creates a function at all.*
  Decision 7 is where the catalogue cases live so it is the natural owner, but that ADR says nothing about it
  and nobody has opened it.
- **The index validity and partiality flags** (`indisvalid`, `indpred` and their siblings). They matter to a
  gate asserting an index **serves a read**, which is ADR-0013's case 7; this gate asserts an index **must not
  exist**, where a partial or invalid unique index still constrains writes. Do not import them here by
  symmetry.

## Boundary decisions the owner closed

Closed 2026-08-25.

1. **One helper, not two fixes.** Two hand-rolled joins failing the same way are one defect with two copies.
2. **MAP-59 runs before MAP-51**, carried in the tracker as a relation rather than as a status. **MAP-59** is
   `Urgent` because the gate it fixes is merged, green, and protecting a C4 channel, and because the other
   order would have MAP-51's window publish the helper as a side effect, which its own review would flag as
   scope creep.

## Evidence handed over

**Measured 2026-08-25 on PostgreSQL 18.6**, on one table carrying both forms of unique key:

* `UNIQUE (name, slug)` → flagged by the gate, correctly
* `UNIQUE ((lower(name) || slug))` → **missed in silence**

**The mechanism, and it is the thing a reader gets wrong.** For an expression key `pg_index.indkey` carries
`0` in that position. No `pg_attribute` row has `attnum = 0`, so an **inner** join on it drops the entry
entirely rather than returning something odd. In the second copy of the defect, which unnests `indkey` and
re-packs positions with `WITH ORDINALITY`, the same drop makes an index whose tenant key sits **second**
render as one that leads on it. Both failures are a **false pass**.

**Read, with its source.** `pg_get_indexdef(indexrelid, k, false)` returns the `k`-th key column's definition
as text, rendering an expression as its text rather than dropping it, and iterating `k` over
`generate_series(1, indnkeyatts)` excludes `INCLUDE` columns by construction. This is what pgTAP does.
*Handed on from the MAP-51 research round and not verified in this repository, pgTAP not being vendored here:*
that same source reads no index validity flag and carries neither a `relrowsecurity` nor a `proleakproof`
assertion, so almost everything ADR-0005 asserts is beyond it. **The technique transfers; the library does
not**, and nothing in the acceptance rests on the unverified half.

**Operational, and it decides how this case's red is manufactured.** ADR-0002 section 5 as amended
2026-08-25: a mutant goes in the artifact carrying the guarantee, a schema-level mutant runs against a
database of the run's own under `--reuse-db` because `--create-db` rebuilds from migrations and takes it with
it, and a probe never names a container path that does not already exist.

**Operational, cost three runs at MAP-39's Window B (2026-08-20).** `apps/api/pyproject.toml`'s `addopts`
already carries `-q`, so `pytest -q` swallows the final count line. Run `pytest` bare or with `--tb=short`.

## Acceptance

The requirement is the two sentences the Trace names, **ADR-0005 decision 5**'s rule and **PRD N2**'s
unique-key acceptance clause, with decision 7's case 4 and its note of 2026-08-25 for where the gate lives.
Read them there. The delta:

- **The case is strengthened rather than replaced.** Its plain-index arm exists, is green, and must stay
  green: a fix that flags the expression form by widening until it also stops distinguishing the correct
  schema is a regression wearing a green tick.
- **The new arm is red against `main` today**, and its red is defined by a schema rather than by a mutant:
  the offending table is created by the case itself, so nothing persists between runs and the `--reuse-db`
  rule below is background rather than instruction. The ADR-0002 clauses matter here for the **probe** half,
  not the mutant half.
- **The helper is Window B's to write and to shape, and Window A does not name it.** The split is clean here
  and worth stating because the helper is test infrastructure rather than production code, which is where the
  two roles blur: **Window A** writes a case that creates a table carrying an expression unique key and asserts
  the gate flags it, which is red because of how the gate reads, and **Window B** makes it green by publishing
  one reading and repointing the five call sites. A case that names a helper by import would be Window A
  choosing Window B's design.
- **The helper's second consumer is not merged, though it is on disk.** MAP-51's container case is untracked in
  this working tree and survives a branch switch, so a window will be looking at it. It is a Window A draft
  being rewritten, **not a contract**: MAP-51 adapts to the helper this round publishes, never the reverse.
