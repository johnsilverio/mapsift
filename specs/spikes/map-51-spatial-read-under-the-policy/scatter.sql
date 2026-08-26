-- ADR-0013 condition 3, the one with no operational answer in this product today. Breaks the heap
-- clustering `build.sql` starts with, by CLUSTERing on a hash of the primary key, then drops the
-- index that did it. Re-run `sweep.sh` afterwards and compare: the same reads cost 10 to 25 times
-- the buffers, and the 200,000-row layer loses to a sequential scan of the whole table.
--
-- This is one-way. Everything clustered has to be measured before this runs; `build.sql` is the
-- only way back. About 16 seconds.

\set ON_ERROR_STOP on
\timing on
CREATE INDEX p_scat ON map51_probe.feature (((hashtext(id::text))));
CLUSTER map51_probe.feature USING p_scat;
DROP INDEX map51_probe.p_scat;
ANALYZE map51_probe.feature;
\timing off
SELECT attname, correlation FROM pg_stats WHERE schemaname='map51_probe' AND tablename='feature' ORDER BY 1;
SELECT pg_size_pretty(pg_relation_size('map51_probe.feature')) AS heap,
       (SELECT relpages FROM pg_class WHERE oid='map51_probe.feature'::regclass) AS pages;
