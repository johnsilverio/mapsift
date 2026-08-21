\set ON_ERROR_STOP on
SET ROLE mapsift_app;
BEGIN;
SELECT set_config('mapsift.tenant_id','aaaaaaaa-0000-0000-0000-000000000001', true);
\timing on
SELECT count(*) AS features
FROM (
  SELECT DISTINCT client_half->'target'->>'feature_id' AS feature_id
  FROM map50_probe.oplog
  WHERE project_id = 'bbbbbbbb-0000-0000-0000-000000000001' AND client_half->>'operation_type' = 'feature.geometry.set'
    AND ST_Intersects(ST_SetSRID(ST_GeomFromGeoJSON(client_half->'payload'->'geometry'),4674), ST_MakeEnvelope(-47.5,-17.5,-47.0,-17.0,4674))
) c;
SELECT count(*) AS features
FROM (
  SELECT DISTINCT client_half->'target'->>'feature_id' AS feature_id
  FROM map50_probe.oplog
  WHERE project_id = 'bbbbbbbb-0000-0000-0000-000000000001' AND client_half->>'operation_type' = 'feature.geometry.set'
    AND ST_Intersects(ST_SetSRID(ST_GeomFromGeoJSON(client_half->'payload'->'geometry'),4674), ST_MakeEnvelope(-47.5,-17.5,-47.0,-17.0,4674))
) c;
SELECT count(*) AS features
FROM (
  SELECT DISTINCT client_half->'target'->>'feature_id' AS feature_id
  FROM map50_probe.oplog
  WHERE project_id = 'bbbbbbbb-0000-0000-0000-000000000001' AND client_half->>'operation_type' = 'feature.geometry.set'
    AND ST_Intersects(ST_SetSRID(ST_GeomFromGeoJSON(client_half->'payload'->'geometry'),4674), ST_MakeEnvelope(-47.5,-17.5,-47.0,-17.0,4674))
) c;
SELECT count(*) AS features
FROM (
  SELECT DISTINCT client_half->'target'->>'feature_id' AS feature_id
  FROM map50_probe.oplog
  WHERE project_id = 'bbbbbbbb-0000-0000-0000-000000000001' AND client_half->>'operation_type' = 'feature.geometry.set'
    AND ST_Intersects(ST_SetSRID(ST_GeomFromGeoJSON(client_half->'payload'->'geometry'),4674), ST_MakeEnvelope(-47.5,-17.5,-47.0,-17.0,4674))
) c;
SELECT count(*) AS features
FROM (
  SELECT DISTINCT client_half->'target'->>'feature_id' AS feature_id
  FROM map50_probe.oplog
  WHERE project_id = 'bbbbbbbb-0000-0000-0000-000000000001' AND client_half->>'operation_type' = 'feature.geometry.set'
    AND ST_Intersects(ST_SetSRID(ST_GeomFromGeoJSON(client_half->'payload'->'geometry'),4674), ST_MakeEnvelope(-47.5,-17.5,-47.0,-17.0,4674))
) c;
SELECT count(*) AS features
FROM (
  SELECT DISTINCT client_half->'target'->>'feature_id' AS feature_id
  FROM map50_probe.oplog
  WHERE project_id = 'bbbbbbbb-0000-0000-0000-000000000001' AND client_half->>'operation_type' = 'feature.geometry.set'
    AND ST_Intersects(ST_SetSRID(ST_GeomFromGeoJSON(client_half->'payload'->'geometry'),4674), ST_MakeEnvelope(-47.5,-17.5,-47.0,-17.0,4674))
) c;
\timing off
COMMIT;
RESET ROLE;
