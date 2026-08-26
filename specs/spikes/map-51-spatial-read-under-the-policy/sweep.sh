#!/usr/bin/env bash
# usage: sweep.sh <outfile.jsonl> <config...>
# Runs the (prefix x box) grid once per index configuration, NOTHING marked LEAKPROOF.
# Index sizes land in <outfile>.idxsize.txt. Full five-config run: about 8 minutes.
#
# cfg8 is the sanctioned shape of ADR-0013 decision 2 and the row the law table quotes; cfg3 is the
# same btree without the plain GiST beside it; cfg0 is the no-index control. cfg4 is the composite
# ADR-0005 decision 5 evaluated, kept because decision 2 is partly a refutation of it.
set -euo pipefail
SP="$(cd "$(dirname "$0")" && pwd)"
OUT="$1"; shift
: > "$OUT"

declare -A IDX
IDX[cfg0_none]=""
IDX[cfg3_btree_tpl]="CREATE INDEX p_btpl ON map51_probe.feature (tenant_id, project_id, layer_id);"
IDX[cfg4_gist_t]="CREATE INDEX p_gt ON map51_probe.feature USING gist (tenant_id, geometry);"
IDX[cfg5_gist_tl]="CREATE INDEX p_gtl ON map51_probe.feature USING gist (tenant_id, layer_id, geometry);"
IDX[cfg8_gist_btl_btpl]="CREATE INDEX p_gist ON map51_probe.feature USING gist (geometry); CREATE INDEX p_btpl ON map51_probe.feature (tenant_id, project_id, layer_id);"

DROPS="DROP INDEX IF EXISTS map51_probe.p_gist, map51_probe.p_btl, map51_probe.p_gt, map51_probe.p_gtl, map51_probe.p_btpl, map51_probe.p_inc;"
for cfg in "$@"; do
  echo ">>> $cfg" >&2
  {
    echo "$DROPS"
    echo "${IDX[$cfg]}"
    echo "ANALYZE map51_probe.feature;"
    echo "\\echo ###IDXSIZE $cfg"
    echo "SELECT indexrelid::regclass::text, pg_size_pretty(pg_relation_size(indexrelid)) FROM pg_index WHERE indrelid='map51_probe.feature'::regclass;"
  } | "$SP/psql.sh" -t -A >> "${OUT%.jsonl}.idxsize.txt"
  "$SP/gen_queries.sh" | "$SP/psql.sh" -t -A | python3 "$SP/parse.py" "$cfg" >> "$OUT"
done
echo "$DROPS" | "$SP/psql.sh"
