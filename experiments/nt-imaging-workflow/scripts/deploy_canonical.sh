#!/bin/bash
set -euo pipefail
EXPECTED_ROOT="/Users/night-thoughts/night-thoughts/experiments/nt-imaging-workflow"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [ "$ROOT" != "$EXPECTED_ROOT" ]; then
  echo "Refusing non-canonical deployment root: $ROOT" >&2
  exit 1
fi
if [ "$(id -u)" -ne 0 ]; then
  echo "Run with sudo. Dependencies are built as the invoking user; only application services are reloaded." >&2
  exit 1
fi
SERVICE_USER="${SUDO_USER:-$(id -un)}"
cd "$ROOT"
run_as_user() {
  sudo -u "$SERVICE_USER" "$@"
}
if [ ! -f .env ]; then
  echo "Missing protected .env; copy .env.example and configure exact oMLX model IDs first." >&2
  exit 1
fi
run_as_user uv sync
if [ ! -d frontend/node_modules ]; then
  run_as_user npm --prefix frontend ci
fi
run_as_user npm --prefix frontend run build
if [ ! -f frontend/dist/index.html ]; then
  echo "Frontend build is missing; refusing service startup." >&2
  exit 1
fi
run_as_user uv run python scripts/migrate_v3.py
for label in com.nightthoughts.imaging.api com.nightthoughts.imaging.worker; do
  plutil -lint "deploy/${label}.plist"
done
./scripts/reload_installed_services.sh
for label in com.nightthoughts.imaging.api com.nightthoughts.imaging.worker; do
  plist="/Library/LaunchDaemons/${label}.plist"
  program="$(/usr/libexec/PlistBuddy -c 'Print :ProgramArguments:0' "$plist")"
  data_root="$(/usr/libexec/PlistBuddy -c 'Print :EnvironmentVariables:DATA_ROOT' "$plist")"
  if [[ "$program" != "$ROOT/.venv/bin/python" || "$data_root" != "$ROOT/var" ]]; then
    echo "Service identity mismatch after reload: $label" >&2
    exit 1
  fi
done
for attempt in {1..30}; do
  if curl --fail --silent http://127.0.0.1:8001/health/ready >/dev/null; then
    break
  fi
  if [ "$attempt" -eq 30 ]; then
    echo "Application did not become ready." >&2
    exit 1
  fi
  sleep 1
done
sleep 3
run_as_user uv run python - <<'PY'
from nt_imaging.config import Settings
from nt_imaging.controlplane.db import ControlDB
from nt_imaging.controlplane.runtime import runtime_identity
settings = Settings.from_env()
identity = runtime_identity(settings)
worker = ControlDB(settings.data_root / 'controlplane.sqlite3').worker_status()
assert worker and worker['code_fingerprint'] == identity['code_fingerprint'], 'Worker code identity mismatch'
assert worker['data_fingerprint'] == identity['data_fingerprint'], 'Worker data-root mismatch'
print('Canonical URL: http://127.0.0.1:8001')
print('Public URL: https://imaging.nightthoughts.dev')
print(f"Instance: {identity['instance_id']}")
print(f"Code fingerprint: {identity['code_fingerprint']}")
print(f"Data-root fingerprint: {identity['data_fingerprint']}")
print(f"Worker heartbeat: {worker['last_heartbeat']}")
PY
