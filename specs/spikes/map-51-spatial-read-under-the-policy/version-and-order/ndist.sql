\set ON_ERROR_STOP on
DROP INDEX IF EXISTS map51_probe.p_btpl, map51_probe.p_btl;
CREATE INDEX p_btpl ON map51_probe.feature (tenant_id, project_id, layer_id);
ANALYZE map51_probe.feature;
\echo '### index pages / real ndistinct'
SELECT relpages FROM pg_class WHERE oid='map51_probe.p_btpl'::regclass;
SELECT attname, n_distinct FROM pg_stats WHERE schemaname='map51_probe' AND tablename='feature' AND attname IN ('tenant_id','project_id','layer_id') ORDER BY 1;

BEGIN;
SET ROLE mapsift_app;
SELECT set_config('mapsift.tenant_id','aaaaaaaa-0000-0000-0000-000000000001',true);
SET LOCAL max_parallel_workers_per_gather = 0;
\echo '### A baseline (real stats, project ndistinct = 8)'
EXPLAIN (ANALYZE, BUFFERS, COSTS OFF) SELECT count(*) FROM map51_probe.feature WHERE layer_id='cccccccc-0000-0000-0000-000000000001'::uuid AND ST_Intersects(geometry, ST_MakeEnvelope(-47.544,-17.544,-47.456,-17.456,4674));
ROLLBACK;
