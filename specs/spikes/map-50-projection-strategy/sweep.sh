#!/usr/bin/env bash
set -euo pipefail
SP="$(dirname "$0")"
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
run() { "$SP/run.sh" "$1"; }
med() { grep -oP '(?<=^Time: )[0-9.]+' | tail -n +2 | sort -g | awk '{a[NR]=$1} END{printf "%.1f", (NR%2)?a[(NR+1)/2]:(a[NR/2]+a[NR/2+1])/2}'; }
for spec in "2000 21" "20000 2" "20000 6" "20000 21" "60000 21"; do
  set -- $spec; n=$1; k=$2
  echo "=================== n=$n k=$k ==================="
  cat "$SP/build.sql" | (docker compose -f infra/compose.yaml --env-file infra/.env exec -T db psql -q -U mapsift -d mapsift -v n=$n -v k=$k -v vtx=60) 2>&1 | grep -vE 'NOTICE|DETAIL|drop cascades' || true
  run "$SP/sweep_index.sql" >/dev/null
  for t in map50_probe.oplog map50_probe.feature; do
    (cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)" && docker compose -f infra/compose.yaml --env-file infra/.env exec -T db psql -q -U mapsift -d mapsift -c "VACUUM (ANALYZE) $t;") >/dev/null
  done
  run "$SP/sweep_shape.sql"
  printf 'A  (maintained table, policy on)  median = %s ms\n' "$(run "$SP/qA.sql" | med)"
  printf 'B3 (fold from the jsonb log)      median = %s ms\n' "$(run "$SP/qB3.sql" | med)"
  echo
done
