#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
uv run python -m nt_imaging.cli doctor
