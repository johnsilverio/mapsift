#!/usr/bin/env bash
# usage: run.sh <sqlfile>
set -euo pipefail
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
cat "$1" | docker compose -f infra/compose.yaml --env-file infra/.env exec -T db \
  psql -q -U mapsift -d mapsift -P pager=off
