\set ON_ERROR_STOP on
SET ROLE mapsift_app;
BEGIN;
SELECT set_config('mapsift.tenant_id','aaaaaaaa-0000-0000-0000-000000000001', true);
\timing on
SELECT count(*) AS features, sum(ST_NPoints(geometry)) AS vertices
FROM map50_probe.feature
WHERE project_id = 'bbbbbbbb-0000-0000-0000-000000000001'
  AND ST_Intersects(geometry, ST_MakeEnvelope(-47.5,-17.5,-47.0,-17.0,4674));
SELECT count(*) AS features, sum(ST_NPoints(geometry)) AS vertices
FROM map50_probe.feature
WHERE project_id = 'bbbbbbbb-0000-0000-0000-000000000001'
  AND ST_Intersects(geometry, ST_MakeEnvelope(-47.5,-17.5,-47.0,-17.0,4674));
SELECT count(*) AS features, sum(ST_NPoints(geometry)) AS vertices
FROM map50_probe.feature
WHERE project_id = 'bbbbbbbb-0000-0000-0000-000000000001'
  AND ST_Intersects(geometry, ST_MakeEnvelope(-47.5,-17.5,-47.0,-17.0,4674));
SELECT count(*) AS features, sum(ST_NPoints(geometry)) AS vertices
FROM map50_probe.feature
WHERE project_id = 'bbbbbbbb-0000-0000-0000-000000000001'
  AND ST_Intersects(geometry, ST_MakeEnvelope(-47.5,-17.5,-47.0,-17.0,4674));
SELECT count(*) AS features, sum(ST_NPoints(geometry)) AS vertices
FROM map50_probe.feature
WHERE project_id = 'bbbbbbbb-0000-0000-0000-000000000001'
  AND ST_Intersects(geometry, ST_MakeEnvelope(-47.5,-17.5,-47.0,-17.0,4674));
SELECT count(*) AS features, sum(ST_NPoints(geometry)) AS vertices
FROM map50_probe.feature
WHERE project_id = 'bbbbbbbb-0000-0000-0000-000000000001'
  AND ST_Intersects(geometry, ST_MakeEnvelope(-47.5,-17.5,-47.0,-17.0,4674));
\timing off
COMMIT;
RESET ROLE;
