\set ON_ERROR_STOP on
\set Q 'SELECT count(*) FROM map51_probe.feature WHERE layer_id=''cccccccc-0000-0000-0000-000000000001''::uuid AND ST_Intersects(geometry, ST_MakeEnvelope(-47.544,-17.544,-47.456,-17.456,4674))'
SELECT relpages AS idx_pages FROM pg_class WHERE oid='map51_probe.p_btpl'::regclass;
ALTER TABLE map51_probe.feature ALTER COLUMN project_id SET (n_distinct = 100);
BEGIN;
SET ROLE mapsift_app;
SELECT set_config('mapsift.tenant_id','aaaaaaaa-0000-0000-0000-000000000001',true);
SET LOCAL max_parallel_workers_per_gather = 0;
\echo '### project_id n_distinct forced to 100'
EXPLAIN (ANALYZE, BUFFERS, COSTS OFF) :Q;
ROLLBACK;
ALTER TABLE map51_probe.feature ALTER COLUMN project_id SET (n_distinct = 1000);
BEGIN;
SET ROLE mapsift_app;
SELECT set_config('mapsift.tenant_id','aaaaaaaa-0000-0000-0000-000000000001',true);
SET LOCAL max_parallel_workers_per_gather = 0;
\echo '### project_id n_distinct forced to 1000'
EXPLAIN (ANALYZE, BUFFERS, COSTS OFF) :Q;
ROLLBACK;
ALTER TABLE map51_probe.feature ALTER COLUMN project_id SET (n_distinct = 1900);
BEGIN;
SET ROLE mapsift_app;
SELECT set_config('mapsift.tenant_id','aaaaaaaa-0000-0000-0000-000000000001',true);
SET LOCAL max_parallel_workers_per_gather = 0;
\echo '### project_id n_distinct forced to 1900'
EXPLAIN (ANALYZE, BUFFERS, COSTS OFF) :Q;
ROLLBACK;
ALTER TABLE map51_probe.feature ALTER COLUMN project_id SET (n_distinct = 2000);
BEGIN;
SET ROLE mapsift_app;
SELECT set_config('mapsift.tenant_id','aaaaaaaa-0000-0000-0000-000000000001',true);
SET LOCAL max_parallel_workers_per_gather = 0;
\echo '### project_id n_distinct forced to 2000'
EXPLAIN (ANALYZE, BUFFERS, COSTS OFF) :Q;
ROLLBACK;
ALTER TABLE map51_probe.feature ALTER COLUMN project_id SET (n_distinct = 5000);
BEGIN;
SET ROLE mapsift_app;
SELECT set_config('mapsift.tenant_id','aaaaaaaa-0000-0000-0000-000000000001',true);
SET LOCAL max_parallel_workers_per_gather = 0;
\echo '### project_id n_distinct forced to 5000'
EXPLAIN (ANALYZE, BUFFERS, COSTS OFF) :Q;
ROLLBACK;
ALTER TABLE map51_probe.feature ALTER COLUMN project_id SET (n_distinct = 100000);
BEGIN;
SET ROLE mapsift_app;
SELECT set_config('mapsift.tenant_id','aaaaaaaa-0000-0000-0000-000000000001',true);
SET LOCAL max_parallel_workers_per_gather = 0;
\echo '### project_id n_distinct forced to 100000'
EXPLAIN (ANALYZE, BUFFERS, COSTS OFF) :Q;
ROLLBACK;
ALTER TABLE map51_probe.feature ALTER COLUMN project_id RESET (n_distinct);
