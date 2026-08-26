\set ON_ERROR_STOP on
\set L1 '''cccccccc-0000-0000-0000-000000000001'''
\set P1 '''bbbbbbbb-0000-0000-0000-000000000001'''
\set T1 '''aaaaaaaa-0000-0000-0000-000000000001'''
DROP INDEX IF EXISTS mp.p_i;
CREATE INDEX p_i ON mp.feature (tenant_id, project_id, layer_id);
ANALYZE mp.feature;
\echo '###### INDEX (tenant_id, project_id, layer_id)'
SELECT pg_size_pretty(pg_relation_size('mp.p_i')) AS idx_size, relpages FROM pg_class WHERE oid='mp.p_i'::regclass;
BEGIN;
SET ROLE mapsift_app;
SELECT set_config('mapsift.tenant_id',:T1,true);
SET LOCAL max_parallel_workers_per_gather = 0;
\echo '### layer container (1000-row layer), z12 box'
EXPLAIN (ANALYZE, BUFFERS, COSTS OFF) SELECT count(*) FROM mp.feature WHERE layer_id=:L1::uuid AND ST_Intersects(geometry, ST_MakeEnvelope(-47.544,-17.544,-47.456,-17.456,4674));
EXPLAIN (ANALYZE, BUFFERS, COSTS OFF) SELECT count(*) FROM mp.feature WHERE layer_id=:L1::uuid AND ST_Intersects(geometry, ST_MakeEnvelope(-47.544,-17.544,-47.456,-17.456,4674));
\echo '### project container (1100 rows), z12 box'
EXPLAIN (ANALYZE, BUFFERS, COSTS OFF) SELECT count(*) FROM mp.feature WHERE project_id=:P1::uuid AND ST_Intersects(geometry, ST_MakeEnvelope(-47.544,-17.544,-47.456,-17.456,4674));
EXPLAIN (ANALYZE, BUFFERS, COSTS OFF) SELECT count(*) FROM mp.feature WHERE project_id=:P1::uuid AND ST_Intersects(geometry, ST_MakeEnvelope(-47.544,-17.544,-47.456,-17.456,4674));
ROLLBACK;
DROP INDEX IF EXISTS mp.p_i;
CREATE INDEX p_i ON mp.feature (tenant_id, layer_id, project_id);
ANALYZE mp.feature;
\echo '###### INDEX (tenant_id, layer_id, project_id)'
SELECT pg_size_pretty(pg_relation_size('mp.p_i')) AS idx_size, relpages FROM pg_class WHERE oid='mp.p_i'::regclass;
BEGIN;
SET ROLE mapsift_app;
SELECT set_config('mapsift.tenant_id',:T1,true);
SET LOCAL max_parallel_workers_per_gather = 0;
\echo '### layer container (1000-row layer), z12 box'
EXPLAIN (ANALYZE, BUFFERS, COSTS OFF) SELECT count(*) FROM mp.feature WHERE layer_id=:L1::uuid AND ST_Intersects(geometry, ST_MakeEnvelope(-47.544,-17.544,-47.456,-17.456,4674));
EXPLAIN (ANALYZE, BUFFERS, COSTS OFF) SELECT count(*) FROM mp.feature WHERE layer_id=:L1::uuid AND ST_Intersects(geometry, ST_MakeEnvelope(-47.544,-17.544,-47.456,-17.456,4674));
\echo '### project container (1100 rows), z12 box'
EXPLAIN (ANALYZE, BUFFERS, COSTS OFF) SELECT count(*) FROM mp.feature WHERE project_id=:P1::uuid AND ST_Intersects(geometry, ST_MakeEnvelope(-47.544,-17.544,-47.456,-17.456,4674));
EXPLAIN (ANALYZE, BUFFERS, COSTS OFF) SELECT count(*) FROM mp.feature WHERE project_id=:P1::uuid AND ST_Intersects(geometry, ST_MakeEnvelope(-47.544,-17.544,-47.456,-17.456,4674));
ROLLBACK;
DROP INDEX IF EXISTS mp.p_i;
CREATE INDEX p_i ON mp.feature (tenant_id, layer_id);
ANALYZE mp.feature;
\echo '###### INDEX (tenant_id, layer_id)'
SELECT pg_size_pretty(pg_relation_size('mp.p_i')) AS idx_size, relpages FROM pg_class WHERE oid='mp.p_i'::regclass;
BEGIN;
SET ROLE mapsift_app;
SELECT set_config('mapsift.tenant_id',:T1,true);
SET LOCAL max_parallel_workers_per_gather = 0;
\echo '### layer container (1000-row layer), z12 box'
EXPLAIN (ANALYZE, BUFFERS, COSTS OFF) SELECT count(*) FROM mp.feature WHERE layer_id=:L1::uuid AND ST_Intersects(geometry, ST_MakeEnvelope(-47.544,-17.544,-47.456,-17.456,4674));
EXPLAIN (ANALYZE, BUFFERS, COSTS OFF) SELECT count(*) FROM mp.feature WHERE layer_id=:L1::uuid AND ST_Intersects(geometry, ST_MakeEnvelope(-47.544,-17.544,-47.456,-17.456,4674));
\echo '### project container (1100 rows), z12 box'
EXPLAIN (ANALYZE, BUFFERS, COSTS OFF) SELECT count(*) FROM mp.feature WHERE project_id=:P1::uuid AND ST_Intersects(geometry, ST_MakeEnvelope(-47.544,-17.544,-47.456,-17.456,4674));
EXPLAIN (ANALYZE, BUFFERS, COSTS OFF) SELECT count(*) FROM mp.feature WHERE project_id=:P1::uuid AND ST_Intersects(geometry, ST_MakeEnvelope(-47.544,-17.544,-47.456,-17.456,4674));
ROLLBACK;
DROP INDEX IF EXISTS mp.p_i;
