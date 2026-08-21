\set ON_ERROR_STOP on
SET ROLE mapsift_app;
BEGIN;
SELECT set_config('mapsift.tenant_id','aaaaaaaa-0000-0000-0000-000000000001', true);
\timing on
WITH folded AS (
  SELECT DISTINCT ON (client_half->'target'->>'feature_id')
         ST_SetSRID(ST_GeomFromGeoJSON(client_half->'payload'->'geometry'),4674) AS geometry
  FROM map50_probe.oplog
  WHERE project_id = 'bbbbbbbb-0000-0000-0000-000000000001' AND client_half->>'operation_type' = 'feature.geometry.set'
  ORDER BY client_half->'target'->>'feature_id', project_version DESC
)
SELECT count(*) AS features, sum(ST_NPoints(geometry)) AS vertices
FROM folded WHERE ST_Intersects(geometry, ST_MakeEnvelope(-47.5,-17.5,-47.0,-17.0,4674));
WITH folded AS (
  SELECT DISTINCT ON (client_half->'target'->>'feature_id')
         ST_SetSRID(ST_GeomFromGeoJSON(client_half->'payload'->'geometry'),4674) AS geometry
  FROM map50_probe.oplog
  WHERE project_id = 'bbbbbbbb-0000-0000-0000-000000000001' AND client_half->>'operation_type' = 'feature.geometry.set'
  ORDER BY client_half->'target'->>'feature_id', project_version DESC
)
SELECT count(*) AS features, sum(ST_NPoints(geometry)) AS vertices
FROM folded WHERE ST_Intersects(geometry, ST_MakeEnvelope(-47.5,-17.5,-47.0,-17.0,4674));
WITH folded AS (
  SELECT DISTINCT ON (client_half->'target'->>'feature_id')
         ST_SetSRID(ST_GeomFromGeoJSON(client_half->'payload'->'geometry'),4674) AS geometry
  FROM map50_probe.oplog
  WHERE project_id = 'bbbbbbbb-0000-0000-0000-000000000001' AND client_half->>'operation_type' = 'feature.geometry.set'
  ORDER BY client_half->'target'->>'feature_id', project_version DESC
)
SELECT count(*) AS features, sum(ST_NPoints(geometry)) AS vertices
FROM folded WHERE ST_Intersects(geometry, ST_MakeEnvelope(-47.5,-17.5,-47.0,-17.0,4674));
WITH folded AS (
  SELECT DISTINCT ON (client_half->'target'->>'feature_id')
         ST_SetSRID(ST_GeomFromGeoJSON(client_half->'payload'->'geometry'),4674) AS geometry
  FROM map50_probe.oplog
  WHERE project_id = 'bbbbbbbb-0000-0000-0000-000000000001' AND client_half->>'operation_type' = 'feature.geometry.set'
  ORDER BY client_half->'target'->>'feature_id', project_version DESC
)
SELECT count(*) AS features, sum(ST_NPoints(geometry)) AS vertices
FROM folded WHERE ST_Intersects(geometry, ST_MakeEnvelope(-47.5,-17.5,-47.0,-17.0,4674));
WITH folded AS (
  SELECT DISTINCT ON (client_half->'target'->>'feature_id')
         ST_SetSRID(ST_GeomFromGeoJSON(client_half->'payload'->'geometry'),4674) AS geometry
  FROM map50_probe.oplog
  WHERE project_id = 'bbbbbbbb-0000-0000-0000-000000000001' AND client_half->>'operation_type' = 'feature.geometry.set'
  ORDER BY client_half->'target'->>'feature_id', project_version DESC
)
SELECT count(*) AS features, sum(ST_NPoints(geometry)) AS vertices
FROM folded WHERE ST_Intersects(geometry, ST_MakeEnvelope(-47.5,-17.5,-47.0,-17.0,4674));
WITH folded AS (
  SELECT DISTINCT ON (client_half->'target'->>'feature_id')
         ST_SetSRID(ST_GeomFromGeoJSON(client_half->'payload'->'geometry'),4674) AS geometry
  FROM map50_probe.oplog
  WHERE project_id = 'bbbbbbbb-0000-0000-0000-000000000001' AND client_half->>'operation_type' = 'feature.geometry.set'
  ORDER BY client_half->'target'->>'feature_id', project_version DESC
)
SELECT count(*) AS features, sum(ST_NPoints(geometry)) AS vertices
FROM folded WHERE ST_Intersects(geometry, ST_MakeEnvelope(-47.5,-17.5,-47.0,-17.0,4674));
\timing off
COMMIT;
RESET ROLE;
