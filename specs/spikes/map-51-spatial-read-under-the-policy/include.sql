-- ADR-0013 decision 7, first half of the covering-index alternative: what it costs. The second
-- half, why it is disqualified rather than merely expensive, is `vertex_limit.sql`.
-- Compare the index size against the heap size `build.sql` and `scatter.sql` both print.

\set ON_ERROR_STOP on
\timing on
DROP INDEX IF EXISTS map51_probe.p_gist, map51_probe.p_btl, map51_probe.p_gt, map51_probe.p_gtl,
                     map51_probe.p_btpl, map51_probe.p_inc;
CREATE INDEX p_inc ON map51_probe.feature (tenant_id, project_id, layer_id) INCLUDE (geometry);
VACUUM (ANALYZE) map51_probe.feature;
\timing off
SELECT pg_size_pretty(pg_relation_size('map51_probe.p_inc')) AS include_index,
       pg_size_pretty(pg_relation_size('map51_probe.feature')) AS heap;
SELECT relallvisible, relpages FROM pg_class WHERE oid='map51_probe.feature'::regclass;
