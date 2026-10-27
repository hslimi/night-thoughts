#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
requested_mode="${INFERENCE_MODE:-}"
requested_root="${DATA_ROOT:-}"
requested_port="${DASHBOARD_PORT:-}"
set -a
source .env
set +a
if [ -n "$requested_mode" ]; then export INFERENCE_MODE="$requested_mode"; fi
if [ -n "$requested_root" ]; then export DATA_ROOT="$requested_root"; fi
if [ -n "$requested_port" ]; then export DASHBOARD_PORT="$requested_port"; fi
export DASHBOARD_PORT="${DASHBOARD_PORT:-8001}"
export LOG_BASENAME="${LOG_BASENAME:-production}"
mkdir -p var/logs
api_pid=""
worker_pid=""
cleanup() {
  trap - EXIT INT TERM
  [ -z "$api_pid" ] || kill "$api_pid" 2>/dev/null || true
  [ -z "$worker_pid" ] || kill "$worker_pid" 2>/dev/null || true
  wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM
uv run uvicorn nt_imaging.controlplane.api:app --host 127.0.0.1 --port "$DASHBOARD_PORT" --workers 1 >"var/logs/${LOG_BASENAME}-api.log" 2>&1 &
api_pid=$!
uv run python -m nt_imaging.controlplane.worker >"var/logs/${LOG_BASENAME}-worker.log" 2>&1 &
worker_pid=$!
echo "Authenticated console: http://127.0.0.1:${DASHBOARD_PORT}"
echo "Durable worker: running with SQLite checkpointing"
while true; do
  if ! kill -0 "$api_pid" 2>/dev/null || ! kill -0 "$worker_pid" 2>/dev/null; then
    echo "A production child stopped; inspect var/logs/production-*.log" >&2
    exit 1
  fi
  sleep 2
done
