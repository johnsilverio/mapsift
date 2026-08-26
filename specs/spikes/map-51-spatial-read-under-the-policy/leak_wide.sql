-- ADR-0013 decision 1, "the conditional form of it was demonstrated to fail on its own terms".
-- Self-contained: builds its own small schema inside a transaction that ROLLS BACK, so it needs no
-- fixture and leaves nothing behind, the marking and the forced cost included.
--
-- The setup is the earlier draft's own answer taken at its word: the composite GiST
-- (tenant_id, geometry) as the only spatial index, st_intersects marked, and its declared cost
-- forced from 5000 to 1 so the planner stops preferring the policy expression. Reading the forced
-- cost as cheating inverts what it shows: the cost is upstream's number, this product does not own
-- it, and a security property that holds only while somebody else's heuristic holds is not a
-- property. The reader owns 20,000 plain Points, all SRID 4674, so no row the reader is entitled to
-- can raise. The 50 PolyhedralSurfaces belong to the OTHER tenant and share the reader's SRID.
--
-- Expected: the narrow box gets an index condition and answers. The wide box, which is the ordinary
-- zoomed-out read, gets a sequential scan, and the marked predicate is then free to run ahead of
-- the policy on rows the policy hides. What comes back names a hidden row's geometry type.

\pset border 0
\set ON_ERROR_STOP off
BEGIN;
CREATE SCHEMA w;
CREATE TABLE w.feat (id bigserial primary key, tenant_id uuid not null,
  geometry geometry(Geometry,4674) not null);
INSERT INTO w.feat (tenant_id, geometry)
SELECT '0000000a-0000-0000-0000-000000000000'::uuid,
       ST_SetSRID(ST_MakePoint(-60.0 + (g % 200)*0.05, -20.0 + (g / 200)*0.05), 4674)
FROM generate_series(1,20000) g;
INSERT INTO w.feat (tenant_id, geometry)
SELECT '0000000b-0000-0000-0000-000000000000'::uuid,
       ST_SetSRID('POLYHEDRALSURFACE(((0 0,0 1,1 1,1 0,0 0)))'::geometry, 4674)
FROM generate_series(1,50) g;
CREATE INDEX ON w.feat USING gist (tenant_id, geometry);
ALTER TABLE w.feat ENABLE ROW LEVEL SECURITY;
ALTER TABLE w.feat FORCE ROW LEVEL SECURITY;
CREATE POLICY t ON w.feat USING (tenant_id = nullif(current_setting('mapsift.tenant_id', true), '')::uuid);
GRANT USAGE ON SCHEMA w TO mapsift_app; GRANT SELECT ON w.feat TO mapsift_app;
ANALYZE w.feat;
ALTER FUNCTION st_intersects(geometry,geometry) LEAKPROOF;
ALTER FUNCTION st_intersects(geometry,geometry) COST 1;
SET ROLE mapsift_app;
SELECT set_config('mapsift.tenant_id','0000000a-0000-0000-0000-000000000000', true) \g /dev/null

\echo '--- NARROW box over the hidden region: index condition, answers normally ---'
EXPLAIN (COSTS OFF) SELECT count(*) FROM w.feat WHERE ST_Intersects(geometry, ST_MakeEnvelope(-0.1,-0.1,1.1,1.1,4674));
SELECT count(*) FROM w.feat WHERE ST_Intersects(geometry, ST_MakeEnvelope(-0.1,-0.1,1.1,1.1,4674));

\echo '--- WIDE box, the ordinary zoomed-out read: sequential scan, no index condition ---'
EXPLAIN (COSTS OFF) SELECT count(*) FROM w.feat WHERE ST_Intersects(geometry, ST_MakeEnvelope(-70,-30,10,10,4674));
SELECT count(*) FROM w.feat WHERE ST_Intersects(geometry, ST_MakeEnvelope(-70,-30,10,10,4674));
ROLLBACK;

\echo '--- and the counterpart: with NOTHING marked, the same wide read answers ---'
BEGIN;
CREATE SCHEMA w;
CREATE TABLE w.feat (id bigserial primary key, tenant_id uuid not null,
  geometry geometry(Geometry,4674) not null);
INSERT INTO w.feat (tenant_id, geometry)
SELECT '0000000a-0000-0000-0000-000000000000'::uuid,
       ST_SetSRID(ST_MakePoint(-60.0 + (g % 200)*0.05, -20.0 + (g / 200)*0.05), 4674)
FROM generate_series(1,20000) g;
INSERT INTO w.feat (tenant_id, geometry)
SELECT '0000000b-0000-0000-0000-000000000000'::uuid,
       ST_SetSRID('POLYHEDRALSURFACE(((0 0,0 1,1 1,1 0,0 0)))'::geometry, 4674)
FROM generate_series(1,50) g;
CREATE INDEX ON w.feat USING gist (tenant_id, geometry);
ALTER TABLE w.feat ENABLE ROW LEVEL SECURITY;
ALTER TABLE w.feat FORCE ROW LEVEL SECURITY;
CREATE POLICY t ON w.feat USING (tenant_id = nullif(current_setting('mapsift.tenant_id', true), '')::uuid);
GRANT USAGE ON SCHEMA w TO mapsift_app; GRANT SELECT ON w.feat TO mapsift_app;
ANALYZE w.feat;
SET ROLE mapsift_app;
SELECT set_config('mapsift.tenant_id','0000000a-0000-0000-0000-000000000000', true) \g /dev/null
SELECT count(*) AS unmarked_wide_read FROM w.feat WHERE ST_Intersects(geometry, ST_MakeEnvelope(-70,-30,10,10,4674));
ROLLBACK;

\echo '--- nothing survived either transaction ---'
SELECT proleakproof, procost FROM pg_proc WHERE oid='st_intersects(geometry,geometry)'::regprocedure;
SELECT count(*) AS leftover_schemas FROM pg_namespace WHERE nspname='w';
