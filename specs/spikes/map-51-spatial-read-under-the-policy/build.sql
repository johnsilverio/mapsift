-- MAP-51 measurement fixture: 2,088,000 rows, the shape every number in ADR-0013 was taken on.
-- Two tenants sharing one region, four projects each, four layers per project at 1,000, 10,000,
-- 50,000 and 200,000 features. Insert order is (tenant, project, layer, feature), so the heap
-- starts CLUSTERED by layer, which is ADR-0013 condition 3 holding. `scatter.sql` breaks it.
--
-- Mirrors the real DDL of public.layers_feature (the five columns a spatial read touches) and
-- ADR-0005 decision 3's policy expression verbatim, in a scratch schema so it drops in one
-- statement. Build time on the reference container: about 2m20s.

\set ON_ERROR_STOP on
\timing on

DROP SCHEMA IF EXISTS map51_probe CASCADE;
CREATE SCHEMA map51_probe;

CREATE FUNCTION map51_probe.r(seed text) RETURNS double precision
LANGUAGE sql IMMUTABLE PARALLEL SAFE AS
$$ SELECT ((hashtext(seed) % 1000000 + 1000000) % 1000000)::float8 / 1000000.0 $$;

-- A ring rather than a point: vertex count drives both the stored size and the recheck cost, and
-- `segments` is what vertex_limit.sql sweeps to find the covering index's write refusal.
CREATE FUNCTION map51_probe.ring(x double precision, y double precision, segments int)
RETURNS geometry LANGUAGE sql IMMUTABLE PARALLEL SAFE AS
$$ SELECT ST_SetSRID(ST_MakePolygon(ST_MakeLine(ARRAY(
       SELECT ST_MakePoint(x + 0.001 * cos(2 * pi() * t / segments),
                           y + 0.001 * sin(2 * pi() * t / segments))
       FROM generate_series(0, segments) AS t))), 4674) $$;

CREATE TABLE map51_probe.feature (
    id uuid NOT NULL PRIMARY KEY,
    geometry geometry(Geometry,4674),
    project_id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    layer_id uuid NOT NULL
);

-- ADR-0005 decision 3, copied verbatim from layers/0001.
ALTER TABLE map51_probe.feature ENABLE ROW LEVEL SECURITY;
ALTER TABLE map51_probe.feature FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON map51_probe.feature
    USING (tenant_id = nullif(current_setting('mapsift.tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = nullif(current_setting('mapsift.tenant_id', true), '')::uuid);

GRANT USAGE ON SCHEMA map51_probe TO mapsift_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON map51_probe.feature TO mapsift_app;

CREATE TABLE map51_probe.plan AS
SELECT ti, pi, li,
       (ARRAY[1000, 10000, 50000, 200000])[li] AS fcount,
       ('aaaaaaaa-0000-0000-0000-' || lpad(ti::text, 12, '0'))::uuid AS tenant_id,
       ('bbbbbbbb-0000-0000-0000-' || lpad(((ti-1)*4 + pi)::text, 12, '0'))::uuid AS project_id,
       ('cccccccc-0000-0000-0000-' || lpad(((ti-1)*16 + (pi-1)*4 + li)::text, 12, '0'))::uuid AS layer_id
FROM generate_series(1,2) a(ti), generate_series(1,4) b(pi), generate_series(1,4) c(li);

-- Both tenants are uniform over the SAME region, lon [-50,-45] x lat [-20,-15]. Overlapping is the
-- point: a fixture whose tenants occupy disjoint boxes would hide every foreign index entry behind
-- geometry rather than behind the policy, and would grade the wall for the wrong reason.
INSERT INTO map51_probe.feature (id, geometry, project_id, tenant_id, layer_id)
SELECT
    ('11111111-0000-0000-0000-' || lpad((row_number() OVER ())::text, 12, '0'))::uuid,
    map51_probe.ring(
        -50.0 + 5.0 * map51_probe.r('x' || p.layer_id || '-' || s.fi),
        -20.0 + 5.0 * map51_probe.r('y' || p.layer_id || '-' || s.fi),
        8),
    p.project_id, p.tenant_id, p.layer_id
FROM map51_probe.plan p,
     LATERAL generate_series(1, p.fcount) s(fi)
ORDER BY p.ti, p.pi, p.li, s.fi;

ANALYZE map51_probe.feature;
\timing off

\echo '--- the prefix sizes the ADR-0013 law table is indexed by ---'
SELECT tenant_id, count(DISTINCT project_id) AS projects, count(DISTINCT layer_id) AS layers, count(*) AS rows
FROM map51_probe.feature GROUP BY 1 ORDER BY 1;
SELECT layer_id, count(*) FROM map51_probe.feature
WHERE tenant_id='aaaaaaaa-0000-0000-0000-000000000001' AND project_id='bbbbbbbb-0000-0000-0000-000000000001'
GROUP BY 1 ORDER BY 1;

\echo '--- condition 3: tenant/project/layer correlation near 1 is the heap clustered by layer ---'
SELECT attname, correlation FROM pg_stats WHERE schemaname='map51_probe' AND tablename='feature' ORDER BY 1;
SELECT pg_size_pretty(pg_relation_size('map51_probe.feature')) AS heap,
       (SELECT relpages FROM pg_class WHERE oid='map51_probe.feature'::regclass) AS pages;
