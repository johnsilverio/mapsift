\set ON_ERROR_STOP on
-- RLS bypassed on purpose: what is under test here is which features come back, not how fast.
-- `feature` is the fold's own output (build.sql builds it with the same DISTINCT ON), so using it
-- as the correct answer compares the two readings rather than two different folds.
\set box 'ST_MakeEnvelope(-47.5,-17.5,-47.0,-17.0,4674)'
\timing on
CREATE TEMP TABLE correct AS
  SELECT id AS feature_id FROM map50_probe.feature WHERE ST_Intersects(geometry, :box);
CREATE TEMP TABLE control AS
  SELECT DISTINCT (client_half->'target'->>'feature_id')::uuid AS feature_id
  FROM map50_probe.oplog
  WHERE client_half->>'operation_type' = 'feature.geometry.set'
    AND ST_Intersects(ST_SetSRID(ST_GeomFromGeoJSON(client_half->'payload'->'geometry'), 4674), :box);
\timing off
SELECT (SELECT count(*) FROM correct) AS fold_returns,
       (SELECT count(*) FROM control) AS control_returns,
       (SELECT count(*) FROM (SELECT * FROM control EXCEPT SELECT * FROM correct) e) AS control_returns_but_should_not,
       (SELECT count(*) FROM (SELECT * FROM correct EXCEPT SELECT * FROM control) e) AS control_misses,
       (SELECT count(*) FROM map50_probe.feature) / 50 AS movers_by_construction;

\echo '--- three features the control wrongly returns, checked against their current geometry ---'
WITH wrong AS (SELECT * FROM control EXCEPT SELECT * FROM correct ORDER BY 1 LIMIT 3)
SELECT w.feature_id,
       ST_Intersects(f.geometry, :box) AS current_geometry_in_the_box,
       (SELECT count(*) FROM map50_probe.oplog o
         WHERE (o.client_half->'target'->>'feature_id')::uuid = w.feature_id
           AND o.client_half->>'operation_type' = 'feature.geometry.set'
           AND ST_Intersects(ST_SetSRID(ST_GeomFromGeoJSON(o.client_half->'payload'->'geometry'), 4674), :box))
         AS superseded_rows_of_this_feature_in_the_box
FROM wrong w JOIN map50_probe.feature f ON f.id = w.feature_id;
