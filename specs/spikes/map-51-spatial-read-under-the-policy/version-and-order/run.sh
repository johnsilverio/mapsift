#!/usr/bin/env bash
# usage: run.sh <container> <outfile.jsonl> <cfgname> <ddl>
set -euo pipefail
SP="$(cd "$(dirname "$0")" && pwd)"
C="$1"; OUT="$2"; CFG="$3"; DDL="${4:-}"
docker exec -i "$C" psql -q -U probe -d probe -P pager=off <<SQL
DROP INDEX IF EXISTS map51_probe.p_btpl, map51_probe.p_btl, map51_probe.p_btp, map51_probe.p_gist;
$DDL
ANALYZE map51_probe.feature;
SQL
docker exec -i "$C" psql -qAt -U probe -d probe -P pager=off -c \
  "SELECT indexrelid::regclass::text||' '||pg_size_pretty(pg_relation_size(indexrelid)) FROM pg_index WHERE indrelid='map51_probe.feature'::regclass;" \
  > "${OUT%.jsonl}.idxsize.txt"
"$SP/gen_queries.sh" | docker exec -i "$C" psql -qAt -U probe -d probe -P pager=off | python3 "$SP/parse.py" "$CFG" > "$OUT"
