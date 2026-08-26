\set ON_ERROR_STOP on
DROP INDEX IF EXISTS map51_probe.p_btpl, map51_probe.p_btl, map51_probe.p_gist;
CREATE INDEX p_gist ON map51_probe.feature USING gist (geometry);
ANALYZE map51_probe.feature;
SELECT pg_size_pretty(pg_relation_size('map51_probe.p_gist')) AS gist_size;
BEGIN;
SET ROLE mapsift_app;
SELECT set_config('mapsift.tenant_id','aaaaaaaa-0000-0000-0000-000000000001',true);
SET LOCAL max_parallel_workers_per_gather = 0;
\echo '### GiST only, tenant-scoped bbox read (the ADR Context case)'
EXPLAIN (ANALYZE, BUFFERS, COSTS OFF) SELECT count(*) FROM map51_probe.feature WHERE ST_Intersects(geometry, ST_MakeEnvelope(-47.544,-17.544,-47.456,-17.456,4674));
\echo '### GiST only, KNN ordering (the ADR Consequences exception)'
EXPLAIN (ANALYZE, BUFFERS, COSTS OFF) SELECT id FROM map51_probe.feature ORDER BY geometry <-> ST_SetSRID(ST_MakePoint(-47.5,-17.5),4674) LIMIT 5;
ROLLBACK;
DROP INDEX map51_probe.p_gist;
