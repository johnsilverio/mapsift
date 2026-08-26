-- Grades the instrument. Run this before trusting any timing in this directory.
-- The wall answers an unbound read with no rows (ADR-0005 sections 3 and 4), so a query that
-- forgets the transaction-scoped binding returns instantly and empty, which reads as fast. Step 1
-- is what catches that: if it does not return zero, the whole sweep is measuring an empty table.

\set ON_ERROR_STOP on
\echo '--- 0. total rows, as superuser (RLS is bypassed here: this is the WRONG number to time) ---'
SELECT count(*) AS total_all_tenants FROM map51_probe.feature;
SELECT tenant_id, count(*) FROM map51_probe.feature GROUP BY 1 ORDER BY 1;

\echo '--- 1. unbound read as mapsift_app: the wall must answer with zero ---'
BEGIN;
SET ROLE mapsift_app;
SELECT current_user, count(*) AS unbound_rows FROM map51_probe.feature;
RESET ROLE;
ROLLBACK;

\echo '--- 2. bound read as mapsift_app: exactly the reader tenant, one distinct tenant, never the total ---'
BEGIN;
SET ROLE mapsift_app;
SELECT set_config('mapsift.tenant_id', 'aaaaaaaa-0000-0000-0000-000000000001', true);
SELECT current_user, count(*) AS reader_rows FROM map51_probe.feature;
SELECT count(DISTINCT tenant_id) AS distinct_tenants_visible FROM map51_probe.feature;
RESET ROLE;
ROLLBACK;

\echo '--- 3. bound to a tenant that owns nothing: zero rows, not an error ---'
BEGIN;
SET ROLE mapsift_app;
SELECT set_config('mapsift.tenant_id', 'aaaaaaaa-0000-0000-0000-000000009999', true);
SELECT count(*) AS empty_tenant_rows FROM map51_probe.feature;
RESET ROLE;
ROLLBACK;

\echo '--- 4. the starting state every unmarked measurement assumes: nothing is marked LEAKPROOF ---'
SELECT count(*) FILTER (WHERE proleakproof) AS marked,
       count(*) AS index_support_predicates
FROM pg_proc WHERE prosupport = 'postgis_index_supportfn'::regproc;

\echo '--- 5. how much of each prefix each box actually selects (the denominator of the 3.5% crossover) ---'
BEGIN;
SET ROLE mapsift_app;
SELECT set_config('mapsift.tenant_id','aaaaaaaa-0000-0000-0000-000000000001',true);
SELECT b.name,
  count(*) AS tenant_1044k,
  count(*) FILTER (WHERE f.project_id='bbbbbbbb-0000-0000-0000-000000000001') AS proj_261k,
  count(*) FILTER (WHERE f.layer_id='cccccccc-0000-0000-0000-000000000004') AS l200k,
  count(*) FILTER (WHERE f.layer_id='cccccccc-0000-0000-0000-000000000003') AS l50k,
  count(*) FILTER (WHERE f.layer_id='cccccccc-0000-0000-0000-000000000002') AS l10k,
  count(*) FILTER (WHERE f.layer_id='cccccccc-0000-0000-0000-000000000001') AS l1k
FROM (VALUES ('b12',0.088::float8),('b10',0.352),('b8',1.408),('b6',5.632)) AS b(name,side)
JOIN map51_probe.feature f
  ON ST_Intersects(f.geometry, ST_MakeEnvelope(-47.5-b.side/2,-17.5-b.side/2,-47.5+b.side/2,-17.5+b.side/2,4674))
GROUP BY 1 ORDER BY 1;
RESET ROLE;
ROLLBACK;
