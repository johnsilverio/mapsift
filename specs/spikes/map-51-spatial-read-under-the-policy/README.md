# The measurement behind ADR-0013

What survives of MAP-51's probe round: **the experiment, not the harness**, on the rule
`specs/spikes/map-50-projection-strategy/README.md` states and `SP-1` section 2 sets. The value is the
answer rather than the code, and what is kept is the smaller thing that rule does not cover: **enough
to re-run the numbers ADR-0013 rests on**, which is what MAP-54 exists to close for ADR-0004 and what
this directory closes here.

Discarded deliberately: the exploratory fixtures, the seventeen staged variants, the downloaded
upstream source and documentation, the handed-over prior art from another project, and every probe
that answered a question ADR-0013 does not cite.

**Nothing here is product code and nothing here is a test.** It does not run in CI, no gate covers it,
and every schema it creates is dropped by `teardown.sql`. The two cases ADR-0013 decision 5 designs
are a separate implementation round and are not these files.

## Running it

Everything goes through `psql.sh`, which pipes stdin into the container's psql with the `--env-file`
compose needs. In order, because most of it needs the fixture and one step is one way:

```
./psql.sh < catalogue.sql        # no fixture needed
./psql.sh < errors.sql           # no fixture needed
./psql.sh < leak_wide.sql        # self-contained, rolls back
./psql.sh < knn.sql              # self-contained, rolls back
./psql.sh < build.sql            # about 2m20s
./psql.sh < safety.sql           # grades the instrument, see below
./sweep.sh out.jsonl cfg0_none cfg3_btree_tpl cfg8_gist_btl_btpl cfg4_gist_t cfg5_gist_tl
./sweep_marked.sh marked.jsonl cfgM2_gist_t_marked cfgM1_gist_marked
./psql.sh < include.sql          # then vertex_limit.sql, which needs p_inc in place
./psql.sh < vertex_limit.sql
./psql.sh < scatter.sql          # ONE WAY: breaks the clustering, only build.sql restores it
./sweep.sh scattered.jsonl cfg8_gist_btl_btpl cfg0_none
./psql.sh < teardown.sql         # drops the fixture and proves nothing stayed marked
```

Then grade the run against the committed baseline, which is the step that makes a re-run mean
something without a copy of the ADR open beside it:

```
python3 report.py check out.jsonl clustered
python3 report.py check marked.jsonl clustered
python3 report.py check scattered.jsonl scattered
```

`report.py` renders the sweep output into the three tables the ADR quotes:

```
python3 report.py law out.jsonl cfg8_gist_btl_btpl        # the prefix law and the buffers-per-row fit
python3 report.py box out.jsonl cfg8_gist_btl_btpl        # every box, which is the independence claim
python3 report.py compare out.jsonl scattered.jsonl cfg8_gist_btl_btpl cfg8_gist_btl_btpl
```

A full pass is roughly 20 minutes: 2m20s to build, 9m for the five-config sweep, 2m35s for the two
marked configs, 2m for the scattered re-sweep, and seconds for the rest.

**It also needs disk, and that is the failure mode that hurts.** Measured 2026-08-25: the heap is
563 MB and its primary key 73 MB, so the bare fixture is about 640 MB; the largest single index in the
sweep is the three-column GiST at 275 MB and `include.sql` builds one of 550 MB, which puts the peak
around 1.2 GB, plus write-ahead log from a two-million-row insert. Give the container a few GB of
headroom. A host that ran out of space during `build.sql` on 2026-08-25 wedged the postmaster for an
hour with no startup process and no log line, and needed a container restart, after which redo finished
in 5.91 seconds.

## Before trusting a number from this

**Run `safety.sql` first, and read step 1.** The wall answers an unbound read with no rows (ADR-0005
sections 3 and 4), so a query that forgets the transaction-scoped tenant binding returns instantly and
empty, which reads as fast. Step 1 is the check that catches a whole sweep timing an empty table.

**Buffers transfer between machines; milliseconds do not.** `baseline.jsonl` is the comparison the
committed files are graded against, and `report.py check` is what grades them. It compares buffers,
index entries, the plan shape and the index condition, and it **deliberately ignores milliseconds**,
because a run whose timings drift is a machine while a run whose buffers or plan shape drift is a
finding. Re-run on 2026-08-25 against the original round's own result files, **224 of these 252 cells
had a counterpart there and all 224 matched to the block** on buffers and on index entries, with zero
differences; that is where `baseline.jsonl` comes from, so those carry both readings at once. The
remaining 28 are `cfg5_gist_tl`. The round's files **do** carry that configuration, 32 cells across
`r1.jsonl` and `s_scattered.jsonl`, and **none of the 32 is comparable**: they were taken on an earlier
fixture generation whose tenant prefix is 200,000 rows against this one's 1,044,000, which is what the
`v2_` prefix on the other files always meant. So the 275 MB three-column GiST that ADR-0013 quotes is
corroborated against the ADR's prose and against this run, and not against a second reading. The reason
is comparability, not absence, and the next paragraph is why the difference matters more than it looks.
**Four separate runs on 2026-08-25 then reproduced the law table to
the block**, one of them against a fixture built by a different invocation on a different machine, which
is what says `build.sql` is deterministic and the baseline portable rather than local.

The milliseconds did none of that. Across the compared cells the ratio to the round's figures ran from
0.54 to 1.75 with a median of 1.08. The tenant row alone, whose ADR figure is 438 ms, was measured at
515, 494 and 457 ms on three runs and at **429 ms on a fourth**, so the spread straddles the published
number instead of sitting above it: there is no correction to make here, only noise to stop reading as
signal. Read the buffer column as the measurement and the millisecond column as one machine on one
afternoon.

**A result file's key is not unique across fixture generations, and `check` guards that before it
compares anything.** The key is `(cfg, shape, box)`, and the round's own pre-v2 files reuse it: sixteen
of those `cfg5_gist_tl` cells collide with keys in this baseline while describing a fixture five times
smaller. Keyed alone they pair up and report as sixteen differences, which would read as numbers that
moved rather than as the wrong fixture. So `check` compares the largest prefix in the run against the
baseline's first and **refuses with exit 2** if they disagree, before a single cell is diffed. Three
exit codes: 0 identical, 1 differences, 2 wrong fixture.

**Grade the checker before you trust it.** Change one buffer count in a result file by one block, or
overwrite one `index_cond` while leaving every count correct, and re-run `report.py check`: it must
report both and exit 1. Feed it a pre-v2 file and it must exit 2 without diffing. Same reason
`negative_control.sql` sits beside MAP-50's correct queries. An instrument that cannot catch a planted
defect cannot grade a real one, and all three of these were run on 2026-08-25, the last one against the
round's own `r1.jsonl` rather than against anything synthetic.

**Both tenants occupy the same region on purpose.** A fixture whose tenants sat in disjoint boxes would
keep every foreign index entry out of the scan by geometry rather than by the policy, and would grade
the wall for the wrong reason.

**`scatter.sql` is one way.** Take every clustered measurement before it. `build.sql` is the only way
back, and it costs another two and a half minutes.

**`sweep_marked.sh` and `leak_wide.sql` mark functions `LEAKPROOF`,** inside transactions that roll
back. `teardown.sql` check 2 is what proves the rollback held, and it is the check that matters most
in this directory, because ADR-0013 decision 1 is a decision that nothing is ever marked.

## What answers which claim

| file | the claim in ADR-0013 |
|---|---|
| `catalogue.sql` | Context: zero of 776 PostGIS functions, zero of 212 in `btree_gist`, all 14 `gist_geometry_ops_2d` members and all 21 `postgis_index_supportfn` predicates report `proleakproof = false`; `uuid_eq` is `true`, which is what decision 2 rests on; `st_intersects` declares cost 5000 and `geometry_overlaps` declares 1 with no support function; the marking is superuser only |
| `errors.sql` | Decision 1, "the assertion is formally false": the error surfaces where `st_intersects` throws for some argument values and not others and names the argument. Part B is decision 7's negative result on `geometry_overlaps`, eleven inputs and none raised |
| `leak_wide.sql` | Decision 1, "the conditional form was demonstrated to fail on its own terms": marked, cost forced to 1, on the earlier draft's own mandated index, a wide box gets a sequential scan and the read answers with a hidden row's geometry type |
| `build.sql`, `sweep.sh`, `report.py` | Decision 2 and the law table: the index condition built only from `uuid_eq`, index entries equal to what the reader owns with zero foreign entries, 0.035 buffers per prefix row, and cost independent of the box |
| `sweep_marked.sh` | The crossover at about 3.5 percent selectivity, and the inversion at low zoom, 7,091 unmarked container buffers against 33,719 marked |
| `scatter.sql` | Condition 3, the clustering obligation with no operational answer: 10 to 25 times the buffers |
| `include.sql`, `vertex_limit.sql` | Decision 7's covering index: 550 MB against a 563 MB heap, then the write refusal above roughly 260 vertices |
| `knn.sql` | The Consequences exception: the ordering path takes the plain GiST with nothing marked and visits foreign index entries, `Rows Removed by Filter: 4` |
| `safety.sql`, `teardown.sql` | Neither. They grade the instrument and the round |
| `baseline.jsonl` | Neither. It is what `report.py check` grades a fresh run against: 252 cells of buffers, index entries, plan shape and index condition. 224 of them are agreed to the block by the original round and by the re-run of 2026-08-25; the 28 `cfg5_gist_tl` cells rest on the re-run alone, for the reason above |

## What did not reproduce as written, recorded rather than smoothed

Three items, and this heading carries no count on purpose: a count in a heading goes stale the moment
somebody finds a fourth, and an artifact whose own tally is wrong is the thing this directory exists to
prevent.

**The four error surfaces are a family, not one signature.** ADR-0013 decision 1 says
"`st_intersects(geometry,geometry)` does both halves of that, on four error surfaces, two of which name
the argument's SRID as well as its geometry type". Four surfaces reproduce and two of them name an SRID,
but only **two of the four sit on the `(geometry,geometry)` overload**, and only **one** of those names
an SRID. The other two belong to the `geography` and `text` overloads (`errors.sql` A3 and A4). The
decision is untouched by this: `errors.sql` A1 alone satisfies the `CREATE FUNCTION` disqualification on
the exact signature a spatial qual uses, and A2 is the surface `leak_wide.sql` actually drives.

**The scattered 200,000-row layer loses to the sequential scan on time, not on buffers.** Measured
2026-08-25: 68,285 buffers and 876 to 1,105 ms against the full scan's 72,000 buffers and 378 to 525 ms.
Fewer blocks, worse wall clock, because they are random rather than sequential. The ADR's sentence is
true as a statement about what the operator experiences and is not true block for block.

**"10 to 25 times the buffers" is measured at 9.6 to 25.1**, so the stated range misses at both ends.
This one is recorded rather than argued: the gap is a rounding, the conclusion it supports does not move
at either end, and whether the ADR's prose is worth amending for it is the fan-out's call and not this
directory's. It is written down so that call is made against a measurement instead of against a number
nobody kept. Run `python3 report.py compare out.jsonl scattered.jsonl cfg8_gist_btl_btpl
cfg8_gist_btl_btpl` and read the ratio column.

## The container these numbers belong to

PostgreSQL 18.6, PostGIS 3.6.4, GEOS 3.14.1, PROJ 9.8.1, from `postgis/postgis:18-3.6` as
`mapsift-db-1`, single process, verified 2026-08-25. Identical to the configuration ADR-0013 was
measured on, which is what makes a figure that fails to reproduce here a finding about the figure.

The fixture mirrors the five columns of `public.layers_feature` a spatial read touches and ADR-0005
decision 3's policy expression verbatim, in the scratch schema `map51_probe`. It does **not** mirror
that table's current indexes: the real table carries `(tenant_id, layer_id)` today, and the
`(tenant_id, project_id, layer_id)` btree the sweep's `cfg8` builds is the index change ADR-0013
decision 4 owes to the implementation round.
