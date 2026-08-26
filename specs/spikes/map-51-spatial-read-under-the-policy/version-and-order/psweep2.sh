#!/usr/bin/env bash
set -euo pipefail
C="$1"
for P in 4 20 100 400; do
  FILL=$(( 440000 / P - 1000 ))
  docker exec -i "$C" psql -q -U probe -d probe -P pager=off >/dev/null 2>&1 <<SQL
\set ON_ERROR_STOP on
DROP SCHEMA IF EXISTS ps CASCADE;
CREATE SCHEMA ps;
CREATE TABLE ps.feature (LIKE map51_probe.feature INCLUDING ALL);
ALTER TABLE ps.feature ENABLE ROW LEVEL SECURITY;
ALTER TABLE ps.feature FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON ps.feature
  USING (tenant_id = nullif(current_setting('mapsift.tenant_id', true), '')::uuid);
GRANT USAGE ON SCHEMA ps TO mapsift_app;
GRANT SELECT ON ps.feature TO mapsift_app;
CREATE TABLE ps.plan AS
SELECT ti, pi, li, (ARRAY[1000, $FILL])[li] AS fcount,
       ('aaaaaaaa-0000-0000-0000-'||lpad(ti::text,12,'0'))::uuid AS tenant_id,
       ('bbbbbbbb-0000-0000-0000-'||lpad(((ti-1)*$P+pi)::text,12,'0'))::uuid AS project_id,
       ('cccccccc-0000-0000-0000-'||lpad(((ti-1)*$P*2+(pi-1)*2+li)::text,12,'0'))::uuid AS layer_id
FROM generate_series(1,2) a(ti), generate_series(1,$P) b(pi), generate_series(1,2) c(li);
INSERT INTO ps.feature (id, geometry, project_id, tenant_id, layer_id)
SELECT ('33333333-0000-0000-0000-'||lpad((row_number() OVER ())::text,12,'0'))::uuid,
       map51_probe.ring(-50.0+5.0*map51_probe.r('x'||p.layer_id||'-'||s.fi),
                        -20.0+5.0*map51_probe.r('y'||p.layer_id||'-'||s.fi), 8),
       p.project_id, p.tenant_id, p.layer_id
FROM ps.plan p, LATERAL generate_series(1,p.fcount) s(fi)
ORDER BY p.ti, p.pi, p.li, s.fi;
SQL
  for ORDER in "tenant_id, project_id, layer_id" "tenant_id, layer_id, project_id"; do
    docker exec -i "$C" psql -q -U probe -d probe -P pager=off >/dev/null 2>&1 <<SQL
DROP INDEX IF EXISTS ps.p_i; CREATE INDEX p_i ON ps.feature ($ORDER); ANALYZE ps.feature;
SQL
    for TARGET in "layer_id='cccccccc-0000-0000-0000-000000000001'::uuid" "project_id='bbbbbbbb-0000-0000-0000-000000000001'::uuid"; do
      for run in 1 2 3; do
        OUT=$(docker exec -i "$C" psql -qAt -U probe -d probe -P pager=off <<SQL
BEGIN;
SET ROLE mapsift_app;
SELECT set_config('mapsift.tenant_id','aaaaaaaa-0000-0000-0000-000000000001',true);
SET LOCAL max_parallel_workers_per_gather = 0;
EXPLAIN (ANALYZE, BUFFERS, COSTS OFF, FORMAT JSON)
SELECT count(*) FROM ps.feature WHERE $TARGET
  AND ST_Intersects(geometry, ST_MakeEnvelope(-47.544,-17.544,-47.456,-17.456,4674));
ROLLBACK;
SQL
)
      done
      echo "P=$P|${ORDER// /}|${TARGET%%=*}|$(printf '%s' "$OUT" | tr -d '\n')"
    done
  done
done
