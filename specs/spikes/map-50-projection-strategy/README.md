# The measurement behind ADR-0012

What survives of MAP-50's probe round: **the experiment, not the harness.** `SP-1` section 2 fixes the rule
that a spike's harness is throwaway and its value is the answer rather than the code, and that holds here.
What is kept is the smaller thing that rule does not cover and that ADR-0004 already promised without
delivering (MAP-54): **enough to re-run the numbers an ADR rests on.**

Discarded deliberately: the exploration files, the downloaded documentation, the intermediate outputs, the
plan-capture variants, and every probe that answered a question the ADR does not cite.

## What is here

- `build.sql` builds the fixture, parameterised: `-v n=<features> -v k=<operations each> -v vtx=<ring segments>`.
  It creates schema `map50_probe` carrying the **real DDL** of `layers_feature` and `sync_operationlogentry`,
  including the `tenant_isolation` policy, `ENABLE` plus `FORCE ROW LEVEL SECURITY`, and the `mapsift_app` grants.
- `qA.sql` reads current geometry in a bounding box from the maintained current-state table.
- `qB1.sql`, `qB2.sql`, `qB3.sql` fold the same answer out of the log: naive, careful, and careful with the
  covering index.
- `qC.sql` is the **known-wrong** variant, which filters the log spatially before folding. It is here because
  the negative control needs something to catch.
- `negative_control.sql` grades the instrument: it counts what `qC.sql` returns that it must not, against the
  mover count `build.sql` guarantees by construction.
- `sweep.sh` varies the fixture to find where the ratio stops holding. `run.sh` pipes one file into the
  container's psql.

## Before trusting a number from this

**Run `negative_control.sql` first.** An instrument that cannot catch `qC.sql` cannot grade `qA.sql`, and that
ordering is the whole reason `qC.sql` is kept beside the queries that are correct.

**Bind the tenant, or measure nothing.** The wall answers an unbound read with no rows (ADR-0005 section 4),
so a query that forgets the transaction-scoped binding returns instantly and empty, which reads as fast.

**The numbers in ADR-0012 were taken on PostgreSQL 18.4 while the sanctioned minor was 18.6**, because the
image was deliberately not pulled mid-round. Ratios transfer between machines; absolute milliseconds do not.

**Nothing here is product code and nothing here is a test.** It does not run in CI, it is not covered by the
gate, and the schema it creates is dropped by the round that creates it.
