\set ON_ERROR_STOP on
DROP INDEX IF EXISTS map51_probe.p_btpl, map51_probe.p_btl;
CREATE INDEX p_btpl ON map51_probe.feature (tenant_id, project_id, layer_id);
ANALYZE map51_probe.feature;
SELECT relpages AS idx_pages FROM pg_class WHERE oid='map51_probe.p_btpl'::regclass;
BEGIN;
SET ROLE mapsift_app;
SELECT set_config('mapsift.tenant_id','aaaaaaaa-0000-0000-0000-000000000001',true);
SET LOCAL max_parallel_workers_per_gather = 0;
\echo '### tenant 1, layer l1k (1000 rows), z12 box'
EXPLAIN (ANALYZE, BUFFERS, COSTS OFF) SELECT count(*) FROM map51_probe.feature WHERE layer_id='cccccccc-0000-0000-0000-000000000001'::uuid AND ST_Intersects(geometry, ST_MakeEnvelope(-47.544,-17.544,-47.456,-17.456,4674));
EXPLAIN (ANALYZE, BUFFERS, COSTS OFF) SELECT count(*) FROM map51_probe.feature WHERE layer_id='cccccccc-0000-0000-0000-000000000001'::uuid AND ST_Intersects(geometry, ST_MakeEnvelope(-47.544,-17.544,-47.456,-17.456,4674));
ROLLBACK;
BEGIN;
SET ROLE mapsift_app;
SELECT set_config('mapsift.tenant_id','aaaaaaaa-0000-0000-0000-000000000002',true);
SET LOCAL max_parallel_workers_per_gather = 0;
\echo '### tenant 2 (the LAST tenant in index order), its own 1000-row layer'
EXPLAIN (ANALYZE, BUFFERS, COSTS OFF) SELECT count(*) FROM map51_probe.feature WHERE layer_id='cccccccc-0000-0000-0000-000000000017'::uuid AND ST_Intersects(geometry, ST_MakeEnvelope(-47.544,-17.544,-47.456,-17.456,4674));
EXPLAIN (ANALYZE, BUFFERS, COSTS OFF) SELECT count(*) FROM map51_probe.feature WHERE layer_id='cccccccc-0000-0000-0000-000000000017'::uuid AND ST_Intersects(geometry, ST_MakeEnvelope(-47.544,-17.544,-47.456,-17.456,4674));
ROLLBACK;
