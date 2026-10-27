#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
export INFERENCE_MODE=MOCK DATA_ROOT=./var/guide-mock OMLX_VISION_MODEL= OMLX_TEXT_MODEL=
export MAX_TOTAL_MODEL_CALLS="${MAX_TOTAL_MODEL_CALLS:-16}"
mkdir -p var/guide-mock var/logs
api_pid=""
worker_pid=""
cleanup() {
  trap - EXIT INT TERM
  [ -z "$api_pid" ] || kill "$api_pid" 2>/dev/null || true
  [ -z "$worker_pid" ] || kill "$worker_pid" 2>/dev/null || true
  wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM
uv run uvicorn nt_imaging.controlplane.api:app --host 127.0.0.1 --port 8002 --workers 1 >var/logs/guide-mock-api.log 2>&1 &
api_pid=$!
uv run python -m nt_imaging.controlplane.worker >var/logs/guide-mock-worker.log 2>&1 &
worker_pid=$!
echo "MOCK guide console: http://127.0.0.1:8002"
while true; do
  kill -0 "$api_pid" 2>/dev/null || exit 1
  kill -0 "$worker_pid" 2>/dev/null || exit 1
  sleep 2
done
