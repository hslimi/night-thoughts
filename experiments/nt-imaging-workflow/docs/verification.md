# Verification record

The sanitized machine-readable source is [`evidence/manifest-v3.json`](../evidence/manifest-v3.json). This document distinguishes executed evidence from unverified or future work.

## Final executed checks

| Check | Actual result |
|---|---|
| `make test` | 85 passed, 0 failed, 1 deselected; Ruff, formatting, and strict mypy passed |
| `make test-real` | 1 passed, 0 failed, 85 deselected using configured oMLX |
| `npm run build` | Production React/TypeScript build passed |
| `make test-browser` | 10 viewport happy paths plus revision, rejection, cancellation, export download, and session expiry/recovery passed |
| Curated REAL showcase | 6 genuine runs: 4 approved exports, 1 rejection without export, 1 awaiting review |
| Curated MOCK/FAULT showcase | 31 genuine API/graph runs with expected terminal states and no-export checks |
| Screenshots | 34 genuine captures inspected; desktop ≤1440×900 and phone 390×844, no full-page tall captures |
| Public login capture | Actual `https://imaging.nightthoughts.dev` login captured without authentication |

The browser viewports are 320×568, 360×800, 375×812, 390×844, 412×915, 768×1024, 1024×768, 1440×900, 844×390, and 568×320. Assertions cover document overflow, off-screen primary controls, touch-target sizes, navigation, monitoring, image zoom/reset, decisions, exports, and session recovery. No physical device was tested.

## Readiness and safety coverage

Tests cover MONOCHROME1/2 equivalence, rescale before VOI/window, signed pixels, implicit/explicit little-endian syntax, VOI LUT, aspect-ratio preservation, no arbitrary orientation flip, corrupt/uniform/oversized inputs, derived OCR, preparation idempotency, policy/code mismatch, derivative-hash tampering, migration, API authorization, local-only configuration, independent export gate rechecks, and no inference after readiness failure.

The API-driven showcases cover approval, rejection, revisions and limits, PHI and modality blocks, malformed input, preparation/derived-safety failure, malformed model output, independent gate recovery/exhaustion, service/timeout faults, technical retry, queued/active cancellation, and queue saturation. REAL drafting receipts use `MedMO-8B-Next` and `Qwen3.5-9B-MLX-4bit`; fault cases remain labelled MOCK/FAULT INJECTION.

## Migration and preservation

The pre-migration backup is `var/migration-backups/20261027T160203Z`; the report is `var/migration-backups/v3-migration.json`. Fifteen snapshots were migrated with IDs/history preserved and `LEGACY_NO_PREPARATION_RECEIPT` shown for legacy records. Existing checkpoints were not erased. Proxy backups are `var/deploy-backups/20261026T164431Z/Caddyfile` and `config.yml`.

oMLX, QwenPaw, Caddy, Cloudflare, Tailscale, SSH, power settings, and unrelated launchd services were not reinstalled or reconfigured by the readiness revision. Only application services were candidates for reload.

## Local-only verification

Source, scripts, deployment examples, and tests contain no required LangSmith account, `LANGSMITH_*`, `LANGCHAIN_TRACING_*`, Agent Server SDK/CLI, hosted Studio, or tracing callback. LangGraph's transitive `langsmith` package may remain in the lockfile; it is not a required integration. The local inspector uses snapshots, SQLite checkpoints, structured events, preparation receipts, and model-call audit records.

## Not verified or limited

- No clinical evaluation, diagnostic accuracy benchmark, anonymization guarantee, or regulatory assessment was performed.
- No physical phone/tablet, institutional identity, multi-node high availability, or formal hospital security assessment was tested.
- Optional Phoenix is not enabled. MONAI/PyTorch and study-level 2D/3D transforms are future work.
- Public traffic transits Cloudflare; the deployment is not air-gapped.
- The public login was captured. A public REAL upload reached review, but the new `/graph-inspector` endpoint returned 404 and the installed plists retained their old environment entries, proving the current readiness API revision is not deployed. A complete public REAL decision/export cycle is therefore not claimed. The final application-only reload script is `scripts/reload_installed_services.sh`; it still needs an effective privileged run and post-reload verification.
- Runtime databases, checkpoints, controlled uploads, derivatives, exports, credentials, logs, and model files are intentionally excluded from publication.

Refer to the evidence manifest for actual run/thread/model-call correlation, fixture hashes, screenshot hashes, runtime status counts, and current limitations.
