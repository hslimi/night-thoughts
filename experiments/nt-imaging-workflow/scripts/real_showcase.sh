#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
export INFERENCE_MODE=REAL DATA_ROOT=./var/real-showcase DASHBOARD_PORT=8003 LOG_BASENAME=real-showcase
exec ./scripts/production.sh
