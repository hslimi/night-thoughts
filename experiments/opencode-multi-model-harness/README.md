# OpenCode multi-model harness

Companion folder for the article on building a multi-model coding harness with OpenCode Desktop. Status: **candidate harness; the acceptance protocol has run with known gaps.** See `evidence/protocol-results.md`.

## Tested versions

| Component | Version |
|---|---|
| OpenCode Desktop (macOS, bundled CLI) | 2.2.5 |
| opencode-model-router | 2.9.1 |
| opencode-runtime-fallback | 0.3.1 |
| Node.js | 22.23.3 |
| poppler (`pdftotext`, `pdftoppm`) | 26.10.0 |

## Contents

- `config/best/`: the three Best configuration files. They contain no keys.
- `config/cheap/`: the low-cost chains (GLM orchestrator, DeepSeek direct and OpenRouter), plus `AGENTS.orchestrator-rule.md`, which belongs in `~/.config/opencode/AGENTS.md`. They contain no keys.
- `config/failover-test/` and `scripts/mock_provider.mjs`: the local mock provider used for failure tests. Readers setting up the harness do not need these.
- `scripts/check_capability_contract.py`: static check of advertised capabilities.
- `evidence/`: sanitized results. Start with `evidence/manifest.md`.

## Reproduce the Best setup

1. Install OpenCode Desktop and connect Anthropic and OpenRouter accounts. Set spend limits first.
2. Back up `~/.config/opencode`, then install the plugins with the CLI bundled in the app. On macOS it is at `/Applications/OpenCode.app/Contents/Resources/opencode-cli`.

   ```bash
   opencode-cli plugin add opencode-model-router@2.9.1
   opencode-cli plugin add opencode-runtime-fallback@0.3.1
   ```

   `plugin add` writes `opencode.json`. Replace it with the `.jsonc` file in the next step so that only one config file remains.
3. Copy the three files from `config/best/` to `~/.config/opencode/`.
4. Quit and reopen OpenCode Desktop.
5. Check that both plugins appear:

   ```bash
   opencode-cli plugin list
   ```

Run `plugin list` against the running app. With `--standalone`, 2.2.5 printed `No plugins found` every time, even with both plugins configured. Straight after adding a plugin or reloading the config, the list can also be briefly incomplete, so run it again after a few seconds.

## Run the static check

Python 3 only. It needs no key and makes no model calls.

```bash
python3 scripts/check_capability_contract.py
```

It compares advertised limits and capabilities per route and per primary-to-backup edge, using models.dev and the OpenRouter models API. A pass does not show that a route works. Its route-independence check compares the hosted route, not the upstream behind it.

## Known limitations

- Protocol results are in `evidence/protocol-results.md`. Test 14's dashboard reconciliation is unfinished, and semantic memory (test 9) was dropped as out of scope because the tool was not reliably available.
- OpenCode's free routes hit a usage limit almost immediately, so the Cheap setup moved to low-cost paid models. See `evidence/desktop-pings-2026-11-05.md`.
- Cheap routing needs the orchestrator rule and worked best with GLM. Each result is one or two runs.
- OpenRouter models outside the default picker list must be switched on under Manage models before Desktop can select them.
- Pinning the OpenRouter backup to a specific upstream is untested.
