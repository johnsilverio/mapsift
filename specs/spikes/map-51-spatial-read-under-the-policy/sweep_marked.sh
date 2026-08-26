#!/usr/bin/env bash
# usage: sweep_marked.sh <outfile.jsonl> <config...>
# The same grid under the assertion ADR-0013 decision 1 refuses, so the two can be compared. The
# marking happens INSIDE the measuring transaction and the transaction ROLLS BACK, so nothing is
# left marked on the database. `teardown.sql` checks that; run it after this.
set -euo pipefail
SP="$(cd "$(dirname "$0")" && pwd)"
OUT="$1"; shift
: > "$OUT"

declare -A IDX
IDX[cfgM1_gist_marked]="CREATE INDEX p_gist ON map51_probe.feature USING gist (geometry);"
IDX[cfgM2_gist_t_marked]="CREATE INDEX p_gt ON map51_probe.feature USING gist (tenant_id, geometry);"
IDX[cfgM3_gist_btpl_marked]="CREATE INDEX p_gist ON map51_probe.feature USING gist (geometry); CREATE INDEX p_btpl ON map51_probe.feature (tenant_id, project_id, layer_id);"
IDX[cfgM4_gist_tl_marked]="CREATE INDEX p_gtl ON map51_probe.feature USING gist (tenant_id, layer_id, geometry);"

DROPS="DROP INDEX IF EXISTS map51_probe.p_gist, map51_probe.p_btl, map51_probe.p_gt, map51_probe.p_gtl, map51_probe.p_btpl, map51_probe.p_inc;"
mark_prologue() {
  cat <<'SQL'
DO $$
DECLARE f record; n int := 0;
BEGIN
  FOR f IN SELECT p.oid::regprocedure AS sig
           FROM pg_proc p JOIN pg_language l ON l.oid = p.prolang
           WHERE p.prosupport = 'postgis_index_supportfn'::regproc AND l.lanname = 'c'
  LOOP
    EXECUTE format('ALTER FUNCTION %s LEAKPROOF', f.sig); n := n + 1;
  END LOOP;
  RAISE NOTICE 'marked % functions', n;
END $$;
SELECT count(*) FILTER (WHERE proleakproof) AS marked_inside_txn
FROM pg_proc WHERE prosupport='postgis_index_supportfn'::regproc;
SQL
}

for cfg in "$@"; do
  echo ">>> $cfg" >&2
  { echo "$DROPS"; echo "${IDX[$cfg]}"; echo "ANALYZE map51_probe.feature;"; } | "$SP/psql.sh"
  { echo "BEGIN;"
    mark_prologue
    "$SP/gen_queries.sh" | grep -v -E '^(BEGIN;|ROLLBACK;)$'
    echo "ROLLBACK;"
  } | "$SP/psql.sh" -t -A | python3 "$SP/parse.py" "$cfg" >> "$OUT"
done
echo "$DROPS" | "$SP/psql.sh"
