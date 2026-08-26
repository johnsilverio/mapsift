#!/usr/bin/env bash
# Emits the (prefix x box) grid ADR-0013's law table is a slice of: seven prefix shapes crossed
# with four box sizes, each measured three times with only the third plan captured, so the first
# two warm the cache. Written to stdout for psql; the plan JSON is read by parse.py.
#
# The boxes are square degrees at the reference latitude: b12 is roughly one z12 tile, b6 roughly
# a z6 tile. b6 at 5.632 degrees covers more than the whole fixture extent, which is the
# "whole world" end of the box-independence claim.
set -euo pipefail
READER='aaaaaaaa-0000-0000-0000-000000000001'
PROJ='bbbbbbbb-0000-0000-0000-000000000001'
L1='cccccccc-0000-0000-0000-000000000001'   # 1,000 rows
L2='cccccccc-0000-0000-0000-000000000002'   # 10,000
L3='cccccccc-0000-0000-0000-000000000003'   # 50,000
L4='cccccccc-0000-0000-0000-000000000004'   # 200,000
LANY="ARRAY['$L1','$L2','$L3','$L4']::uuid[]"

cat <<SQL
BEGIN;
SET ROLE mapsift_app;
SELECT set_config('mapsift.tenant_id','$READER',true);
SET LOCAL max_parallel_workers_per_gather = ${PAR:-0};
SQL

for box in "b12 0.088" "b10 0.352" "b8 1.408" "b6 5.632"; do
  set -- $box; bname=$1; side=$2
  ENV="ST_MakeEnvelope(-47.5-$side/2, -17.5-$side/2, -47.5+$side/2, -17.5+$side/2, 4674)"
  for shape in tenant proj lany l200k l50k l10k l1k; do
    case $shape in
      tenant) PRED="";;
      proj)   PRED="project_id = '$PROJ'::uuid AND ";;
      lany)   PRED="layer_id = ANY($LANY) AND ";;
      l200k)  PRED="layer_id = '$L4'::uuid AND ";;
      l50k)   PRED="layer_id = '$L3'::uuid AND ";;
      l10k)   PRED="layer_id = '$L2'::uuid AND ";;
      l1k)    PRED="layer_id = '$L1'::uuid AND ";;
    esac
    Q="SELECT count(*) FROM map51_probe.feature WHERE ${PRED}ST_Intersects(geometry, $ENV)"
    echo "\\echo ###MEASURE shape=$shape box=$bname"
    echo "EXPLAIN (ANALYZE, BUFFERS, COSTS OFF, FORMAT JSON) $Q;"
    echo "EXPLAIN (ANALYZE, BUFFERS, COSTS OFF, FORMAT JSON) $Q;"
    echo "\\echo ###PLAN"
    echo "EXPLAIN (ANALYZE, BUFFERS, COSTS OFF, FORMAT JSON) $Q;"
  done
done
echo "RESET ROLE;"
echo "ROLLBACK;"
