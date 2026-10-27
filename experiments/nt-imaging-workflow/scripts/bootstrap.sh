#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
if ! command -v uv >/dev/null; then
  echo "uv is required; complete the separate foundation guide first" >&2
  exit 1
fi
if [ -x "$HOME/.mlx-venv/bin/python3" ]; then
  PYTHON="$HOME/.mlx-venv/bin/python3"
else
  PYTHON="$(command -v python3)"
fi
uv sync --python "$PYTHON"
echo "Project dependencies installed only in repository-local .venv"
