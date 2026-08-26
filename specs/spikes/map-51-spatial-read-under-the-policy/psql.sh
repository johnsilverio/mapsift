#!/usr/bin/env bash
# usage: psql.sh [psql args...] < sqlfile
set -euo pipefail
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
exec docker compose -f infra/compose.yaml --env-file infra/.env exec -T db \
  psql -q -U mapsift -d mapsift -P pager=off "$@"
