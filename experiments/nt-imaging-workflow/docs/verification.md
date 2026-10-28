# Verification record

The sanitized machine-readable source is [`evidence/manifest-v4.json`](../evidence/manifest-v4.json). This document distinguishes executed evidence from unverified or future work.

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

## Live execution root cause and correction

The original two REAL jobs `17477107-2b44-41cb-82bb-512c09e2e077` and `fdba621b-d8bf-431f-a460-06ef1b5f2c72` remained `QUEUED` with `heartbeat_at = NULL`. The canonical control database existed, but `deployed-checkpoints.sqlite3` did not exist because no canonical worker had opened it. The obsolete worker's stdout/stderr logs were empty, so there was no evidence of a lock, crash, checkpoint exception, or model failure.

Process and plist inspection showed the actual mismatch: API PID 70924 ran `/Users/night-thoughts/night-thoughts/experiments/nt-imaging-workflow/.venv/bin/python` with canonical `DATA_ROOT`, while worker PID 70634 ran `/Users/night-thoughts/healthcare/nt-imaging-workflow/.venv/bin/python -m nt_imaging.controlplane.worker` with the obsolete working directory and `DATA_ROOT`. The running worker therefore never consumed the canonical queue. Process existence was not a valid health check.

The correction is to run both services from the canonical Python and data root and verify identity/heartbeat rather than delete or reseed jobs. `scripts/deploy_canonical.sh` builds the frontend, runs migrations, validates plists, reloads only the two application services, and checks program paths, `DATA_ROOT`, code fingerprint, data fingerprint, and readiness. The two queued jobs were preserved. A non-daemon canonical recovery process then emitted matching fingerprints and heartbeat; the first original job reached human approval and all six preserved jobs reached that interrupt without deletion. Public REAL scenarios also passed approval/export, revision, and rejection, with desktop/mobile login and export controls verified. These application checks do not by themselves prove LaunchDaemon persistence.

## Durable events and live verification

`app_events` stores global and per-run sequences transactionally with snapshots. Graph nodes, preparation operations, model calls, attempts, revisions, human decisions, exports, cancellation, retries, and worker lifecycle emit safe structured events. SSE provides initial snapshots, Last-Event-ID replay, real gap `resync`, heartbeat packets, and session revalidation. Multiple tabs do not create duplicate events.

The live frontend uses event snapshots to update worklist lanes and run state. It includes real node states, elapsed stages, attempts, revision comparison, model-call state, global activity, and a debugging center with traces/logs/diagnostics/support bundles. Event parsing and initialization races were fixed after browser evidence showed stale `QUEUED` state. The frontend now yields to received SSE events rather than late initial REST responses.

Actual checks at this revision: 95 non-real tests, one REAL oMLX test, ten responsive browser workflows, and a dedicated live-experience test covering approval, revision, rejection, debug tabs/support bundle, and mobile approval with reduced motion. The isolated live screenshots are under `docs/images/live-operations/`.

## Not verified or limited

- No clinical evaluation, diagnostic accuracy benchmark, anonymization guarantee, or regulatory assessment was performed.
- No physical phone/tablet, institutional identity, multi-node high availability, or formal hospital security assessment was tested.
- Optional Phoenix is not enabled. MONAI/PyTorch and study-level 2D/3D transforms are future work.
- Public traffic transits Cloudflare; the deployment is not air-gapped.
- Public REAL approval/export and desktop/mobile export controls passed with live events. The installed worker plist still pointed to the obsolete path at last inspection, so LaunchDaemon persistence is not yet claimed. `scripts/deploy_canonical.sh` remains the final application-only installation step.
- Runtime databases, checkpoints, controlled uploads, derivatives, exports, credentials, logs, and model files are intentionally excluded from publication.

Refer to the evidence manifest for actual run/thread/model-call correlation, fixture hashes, screenshot hashes, runtime status counts, and current limitations.
