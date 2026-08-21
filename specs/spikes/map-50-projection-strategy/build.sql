-- MAP-50 measurement fixture. Mirrors the real DDL of public.layers_feature and
-- public.sync_operationlogentry (columns, indexes, RLS policy text, grants), in a scratch schema
-- so the whole thing drops in one statement.
--
-- psql -v n=<features> -v k=<ops per feature>

\set ON_ERROR_STOP on

DROP SCHEMA IF EXISTS map50_probe CASCADE;
CREATE SCHEMA map50_probe;

CREATE FUNCTION map50_probe.r(seed text) RETURNS double precision
LANGUAGE sql IMMUTABLE PARALLEL SAFE AS
$$ SELECT ((hashtext(seed) % 1000000 + 1000000) % 1000000)::float8 / 1000000.0 $$;

-- A parcel-shaped ring rather than a rectangle: vertex count is the dominant term in both the
-- parse cost of a log row and the size of a stored geometry, so an envelope would flatter the
-- fold. `segments` is the fixture parameter :vtx.
CREATE FUNCTION map50_probe.ring(x double precision, y double precision, segments int)
RETURNS geometry LANGUAGE sql IMMUTABLE PARALLEL SAFE AS
$$ SELECT ST_SetSRID(ST_MakePolygon(ST_MakeLine(ARRAY(
       SELECT ST_MakePoint(x + 0.001 * cos(2 * pi() * t / segments),
                           y + 0.001 * sin(2 * pi() * t / segments))
       FROM generate_series(0, segments) AS t))), 4674) $$;

-- The maintained current-state table: public.layers_feature, minus the foreign keys to
-- accounts (they cost nothing on a read) and with the same three indexes.
CREATE TABLE map50_probe.feature (
    id uuid NOT NULL PRIMARY KEY,
    geometry geometry(Geometry,4674),
    project_id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    layer_id uuid NOT NULL
);
CREATE INDEX probe_feature_geometry_gist ON map50_probe.feature USING gist (geometry);
CREATE INDEX probe_feature_layer_by_tenant ON map50_probe.feature (tenant_id, layer_id);

-- The append-only log: public.sync_operationlogentry, same columns and same three indexes.
CREATE TABLE map50_probe.oplog (
    id uuid NOT NULL PRIMARY KEY,
    operation_id uuid NOT NULL,
    client_half jsonb NOT NULL,
    tenant_id uuid NOT NULL,
    project_id uuid NOT NULL,
    project_version bigint NOT NULL
);
CREATE UNIQUE INDEX probe_one_entry_per_operation ON map50_probe.oplog (tenant_id, operation_id);
CREATE INDEX probe_log_by_project_version ON map50_probe.oplog (tenant_id, project_id, project_version);

-- ADR-0005 section 7, copied verbatim from layers/0001 and sync/0001.
ALTER TABLE map50_probe.feature ENABLE ROW LEVEL SECURITY;
ALTER TABLE map50_probe.feature FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON map50_probe.feature
    USING (tenant_id = nullif(current_setting('mapsift.tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = nullif(current_setting('mapsift.tenant_id', true), '')::uuid);

ALTER TABLE map50_probe.oplog ENABLE ROW LEVEL SECURITY;
ALTER TABLE map50_probe.oplog FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON map50_probe.oplog
    USING (tenant_id = nullif(current_setting('mapsift.tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = nullif(current_setting('mapsift.tenant_id', true), '')::uuid);

GRANT USAGE ON SCHEMA map50_probe TO mapsift_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON map50_probe.feature TO mapsift_app;
GRANT SELECT, INSERT ON map50_probe.oplog TO mapsift_app;

-- ---------------------------------------------------------------------------------------------
-- The fixture. One tenant, one project, one layer.
--   tenant  aaaaaaaa-0000-0000-0000-000000000001
--   project bbbbbbbb-0000-0000-0000-000000000001
--   layer   cccccccc-0000-0000-0000-000000000001
-- Region: lon [-50,-45] x lat [-20,-15] (EPSG:4674). Query box: lon [-47.5,-47.0] x
-- lat [-17.5,-17.0], one percent of the region's area.
-- Per feature: v=1 is feature.create (no geometry), v=2..k are feature.geometry.set, so k-1
-- geometry versions of which k-2 are superseded.
-- Three cohorts, by feature index:
--   stayers  (first 97%): home uniform over the region, tiny jitter per version.
--   movers   (next 2%):   every version but the last inside the query box, the last far outside.
--   arrivers (last 1%):   every version but the last outside, the last inside the query box.
-- The movers are what a spatially-prefiltered log returns and a fold does not: the negative
-- control's error set, and its size is known by construction.
-- project_version interleaves the rounds ((v-1)*n + i), so one feature's versions are spread
-- across the whole table rather than clustered.
INSERT INTO map50_probe.oplog (id, operation_id, client_half, tenant_id, project_id, project_version)
SELECT
    ('dddddddd-0000-0000-0000-' || lpad(((v - 1) * :n + i)::text, 12, '0'))::uuid,
    ('eeeeeeee-0000-0000-0000-' || lpad(((v - 1) * :n + i)::text, 12, '0'))::uuid,
    CASE WHEN v = 1 THEN
        jsonb_build_object(
            'author_session_material', jsonb_build_object('scheme', 'probe', 'proof', md5(i::text)),
            'client_id', 'ffffffff-0000-0000-0000-000000000001',
            'conflict_rule_version', 1,
            'created_at', '2026-08-21T12:00:00Z',
            'mediation', NULL,
            'mutation_number', v,
            'operation_id', ('eeeeeeee-0000-0000-0000-' || lpad(((v - 1) * :n + i)::text, 12, '0')),
            'operation_schema_version', 1,
            'operation_type', 'feature.create',
            'payload', '{}'::jsonb,
            'target', jsonb_build_object(
                'feature_id', ('11111111-0000-0000-0000-' || lpad(i::text, 12, '0')),
                'kind', 'feature',
                'layer_id', 'cccccccc-0000-0000-0000-000000000001',
                'project_id', 'bbbbbbbb-0000-0000-0000-000000000001',
                'tenant_id', 'aaaaaaaa-0000-0000-0000-000000000001'))
    ELSE
        jsonb_build_object(
            'author_session_material', jsonb_build_object('scheme', 'probe', 'proof', md5(i::text)),
            'client_id', 'ffffffff-0000-0000-0000-000000000001',
            'conflict_rule_version', 1,
            'created_at', '2026-08-21T12:00:00Z',
            'mediation', NULL,
            'mutation_number', v,
            'operation_id', ('eeeeeeee-0000-0000-0000-' || lpad(((v - 1) * :n + i)::text, 12, '0')),
            'operation_schema_version', 1,
            'operation_type', 'feature.geometry.set',
            'payload', jsonb_build_object('geometry',
                ST_AsGeoJSON(map50_probe.ring(x, y, :vtx))::jsonb),
            'target', jsonb_build_object(
                'feature_id', ('11111111-0000-0000-0000-' || lpad(i::text, 12, '0')),
                'kind', 'property',
                'layer_id', 'cccccccc-0000-0000-0000-000000000001',
                'project_id', 'bbbbbbbb-0000-0000-0000-000000000001',
                'property', 'geometry',
                'tenant_id', 'aaaaaaaa-0000-0000-0000-000000000001'))
    END,
    'aaaaaaaa-0000-0000-0000-000000000001'::uuid,
    'bbbbbbbb-0000-0000-0000-000000000001'::uuid,
    (v - 1) * :n + i
FROM (
    SELECT i, v, cohort,
        CASE cohort
            WHEN 'stayer' THEN -50.0 + 5.0 * map50_probe.r('hx' || i)
                               + 0.0004 * (map50_probe.r('jx' || i || '-' || v) - 0.5)
            WHEN 'mover'  THEN CASE WHEN v = :k THEN -50.0 + 1.0 * map50_probe.r('mx' || i)
                                                ELSE -47.5 + 0.5 * map50_probe.r('bx' || i || '-' || v) END
            ELSE               CASE WHEN v = :k THEN -47.5 + 0.5 * map50_probe.r('ax' || i)
                                                ELSE -46.0 + 1.0 * map50_probe.r('ox' || i || '-' || v) END
        END AS x,
        CASE cohort
            WHEN 'stayer' THEN -20.0 + 5.0 * map50_probe.r('hy' || i)
                               + 0.0004 * (map50_probe.r('jy' || i || '-' || v) - 0.5)
            WHEN 'mover'  THEN CASE WHEN v = :k THEN -20.0 + 1.0 * map50_probe.r('my' || i)
                                                ELSE -17.5 + 0.5 * map50_probe.r('by' || i || '-' || v) END
            ELSE               CASE WHEN v = :k THEN -17.5 + 0.5 * map50_probe.r('ay' || i)
                                                ELSE -16.0 + 1.0 * map50_probe.r('oy' || i || '-' || v) END
        END AS y
    FROM (
        SELECT f.i, g.v,
            CASE WHEN f.i <= (:n::bigint * 97) / 100 THEN 'stayer'
                 WHEN f.i <= (:n::bigint * 99) / 100 THEN 'mover'
                 ELSE 'arriver' END AS cohort
        FROM generate_series(1, :n) AS f(i), generate_series(1, :k) AS g(v)
    ) AS cohorted
) AS placed;

-- The projection is the fold's own output, so the two paths cannot disagree by construction.
INSERT INTO map50_probe.feature (id, geometry, project_id, tenant_id, layer_id)
SELECT DISTINCT ON (client_half->'target'->>'feature_id')
    (client_half->'target'->>'feature_id')::uuid,
    ST_SetSRID(ST_GeomFromGeoJSON(client_half->'payload'->'geometry'), 4674),
    'bbbbbbbb-0000-0000-0000-000000000001'::uuid,
    'aaaaaaaa-0000-0000-0000-000000000001'::uuid,
    'cccccccc-0000-0000-0000-000000000001'::uuid
FROM map50_probe.oplog
WHERE client_half->>'operation_type' = 'feature.geometry.set'
ORDER BY client_half->'target'->>'feature_id', project_version DESC;

ANALYZE map50_probe.oplog;
ANALYZE map50_probe.feature;
