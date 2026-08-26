-- ADR-0013 Consequences, "the ordering path is the measured exception". The leakproof gate governs
-- quals, not ORDER BY pathkeys, so a nearest-neighbour ordering takes the plain GiST with nothing
-- marked and visits index entries belonging to a tenant the reader cannot see. Watch for
-- `Rows Removed by Filter` above the ordering: those are the foreign entries.
--
-- Nothing is marked here and nothing is left behind. Self-contained, rolls back.

\pset border 0
\set ON_ERROR_STOP off
BEGIN;
CREATE SCHEMA k;
CREATE TABLE k.feat (id bigserial primary key, tenant_id uuid not null, layer_id uuid not null,
  geometry geometry(Geometry,4674) not null);
-- the two tenants are interleaved 0.005 degrees apart, so the reader's nearest neighbour and the
-- hidden tenant's are always adjacent in the index
INSERT INTO k.feat (tenant_id, layer_id, geometry)
SELECT '0000000a-0000-0000-0000-000000000000'::uuid, '0000000c-0000-0000-0000-000000000000'::uuid,
       ST_SetSRID(ST_MakePoint(-60.0 + (g % 500)*0.02, -20.0 + (g / 500)*0.1), 4674)
FROM generate_series(1,25000) g;
INSERT INTO k.feat (tenant_id, layer_id, geometry)
SELECT '0000000b-0000-0000-0000-000000000000'::uuid, '0000000d-0000-0000-0000-000000000000'::uuid,
       ST_SetSRID(ST_MakePoint(-60.0 + (g % 500)*0.02 + 0.005, -20.0 + (g / 500)*0.1), 4674)
FROM generate_series(1,25000) g;
CREATE INDEX ON k.feat USING gist (geometry);
CREATE INDEX ON k.feat (tenant_id, layer_id);
ALTER TABLE k.feat ENABLE ROW LEVEL SECURITY;
ALTER TABLE k.feat FORCE ROW LEVEL SECURITY;
CREATE POLICY t ON k.feat USING (tenant_id = nullif(current_setting('mapsift.tenant_id', true), '')::uuid);
GRANT USAGE ON SCHEMA k TO mapsift_app; GRANT SELECT ON k.feat TO mapsift_app;
ANALYZE k.feat;
SET ROLE mapsift_app;
SELECT set_config('mapsift.tenant_id','0000000a-0000-0000-0000-000000000000', true) \g /dev/null

\echo '--- nearest-neighbour ordering under the policy, nothing marked ---'
EXPLAIN (ANALYZE, COSTS OFF, TIMING OFF, SUMMARY OFF)
 SELECT id FROM k.feat ORDER BY geometry <-> ST_SetSRID(ST_MakePoint(-55,-17.5),4674) LIMIT 5;

\echo '--- and the same read scoped to one layer, which is decision 2''s shape ---'
EXPLAIN (ANALYZE, COSTS OFF, TIMING OFF, SUMMARY OFF)
 SELECT id FROM k.feat WHERE layer_id='0000000c-0000-0000-0000-000000000000'::uuid
 ORDER BY geometry <-> ST_SetSRID(ST_MakePoint(-55,-17.5),4674) LIMIT 5;
RESET ROLE;
ROLLBACK;
SELECT count(*) AS leftover_schemas FROM pg_namespace WHERE nspname='k';
