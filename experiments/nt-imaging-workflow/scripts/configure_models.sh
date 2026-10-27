#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
export OMLX_VISION_MODEL="${OMLX_VISION_MODEL:-MedMO-8B-Next}"
uv run python - <<'PY'
import json, os, urllib.request
from nt_imaging.config import get_omlx_api_key
request = urllib.request.Request('http://127.0.0.1:8000/v1/models', headers={'Authorization': f'Bearer {get_omlx_api_key()}'})
with urllib.request.urlopen(request, timeout=10) as response:
    ids = [item['id'] for item in json.load(response)['data']]
for index, model in enumerate(ids, 1):
    print(f'{index}. {model}')
vision_default = os.getenv('OMLX_VISION_MODEL') or ('MedMO-8B-Next' if 'MedMO-8B-Next' in ids else (ids[0] if ids else ''))
text_default = os.getenv('OMLX_TEXT_MODEL') or ('Qwen3.5-9B-MLX-4bit' if 'Qwen3.5-9B-MLX-4bit' in ids else vision_default)
if os.getenv('CONFIGURE_NONINTERACTIVE') == '1':
    vision, text = vision_default, text_default
else:
    vision = input(f'Exact vision model ID [{vision_default}]: ').strip() or vision_default
    text = input(f'Exact text model ID [{text_default}]: ').strip() or text_default
if vision not in ids or text not in ids:
    raise SystemExit('Selected IDs must exactly match the discovered inventory')
values = {'OMLX_BASE_URL': 'http://127.0.0.1:8000/v1', 'OMLX_VISION_MODEL': vision, 'OMLX_TEXT_MODEL': text}
lines = []
if os.path.exists('.env'):
    lines = open('.env').read().splitlines()
for key, value in values.items():
    replacement = f'{key}={value}'
    if any(line.startswith(key + '=') for line in lines):
        lines = [replacement if line.startswith(key + '=') else line for line in lines]
    else:
        lines.append(replacement)
with open('.env', 'w') as handle:
    handle.write('\n'.join(lines) + '\n')
os.chmod('.env', 0o600)
print('Non-secret model IDs written to local .env; credentials were not persisted.')
PY
./scripts/doctor.sh
