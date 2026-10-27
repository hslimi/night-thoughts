# Build a Local Medical Imaging Workflow with LangGraph, oMLX, and a Doctor Review Console

This guide reproduces **NT Imaging Workflow** on an existing always-on Mac mini. It covers the deterministic Imaging Readiness Agent, durable single-worker LangGraph runtime, local graph inspector, authenticated doctor console, synthetic showcases, backup, recovery, and optional public proxy integration.

> **Research demonstration only. Use synthetic or authorized de-identified images. AI-assisted drafts require qualified human review and are not for clinical use.** This is not a clinically validated, certified, or institutionally hardened deployment.

## 1. Architecture and data flow

```text
Browser
→ existing HTTPS/Cloudflare/Caddy path (optional public access)
→ FastAPI + local React assets on 127.0.0.1:8001
→ bounded SQLite queue
→ one dedicated LangGraph worker + SQLite checkpoints
→ existing oMLX on 127.0.0.1:8000
```

The corrected graph is:

```text
Upload → ingest_validate → phi_screen → modality_gate
→ imaging_readiness → derived_image_safety_check → generate_draft
→ deterministic_contract_gate → visual_consistency_review → text_quality_review
→ human_approval → export_approved_draft
```

The vision model drafts and reviews visual consistency; the text model reviews writing quality. Neither can authorize export or alter routing. Only deterministic policy and a typed doctor approval can reach idempotent export.

Inference and application state remain on the Mac. If the public route is enabled, requests and responses transit Cloudflare. Do not describe that deployment as air-gapped.

![Populated operational console from genuine REAL workflow runs](../docs/images/doctor-pipeline-user-guide/02-dashboard-desktop.png)

## 2. Supported scope and limitations

- One synthetic or authorized de-identified single-frame CR/DX chest radiograph per run.
- PNG/JPEG with explicit `XR` declaration, or constrained uncompressed little-endian CR/DX DICOM.
- 8/10/12/16-bit grayscale, signed pixels, rescale, one VOI LUT/window, MONOCHROME1/2.
- No CT/MRI/ultrasound, multi-frame/3D study, compressed transfer syntax, or general DICOM anonymization claim.
- No clinical accuracy evaluation, regulatory clearance, autonomous diagnosis, or exactly-once inference guarantee.

PHI screening fails closed but is not guaranteed anonymization. Preparation preserves defined display semantics; it does not prove diagnostic preservation. Doctor approval authorizes a research-draft export, not radiologist sign-off.

## 3. Existing foundation prerequisites

Follow the separate [always-on Mac server foundation guide](https://nightthoughts.me/complete-guide-always-on-mac-server-with-mlx-omlx-qwenpaw) first. The expected existing stack is:

- oMLX at `127.0.0.1:8000`, managed by `com.omlx.server`, with models already registered.
- QwenPaw at `127.0.0.1:8088`, managed by `com.qwenpaw.app`.
- Caddy at `127.0.0.1:9080`, existing Cloudflare Tunnel, Tailscale, SSH, and launchd configuration.
- Python 3.11, `uv`, Homebrew, and the shared MLX environment.

Do not rerun foundation installers, use `brew services` for oMLX, replace its daemon, download duplicate models, or install this project into `~/.mlx-venv`. Do not change power, headless, SSH, DNS, Tailscale, or unrelated service configuration.

## 4. Verify the foundation read-only

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8088/  # inspect only; response content is not important here
launchctl print system/com.omlx.server
launchctl print system/com.qwenpaw.app
```

Confirm Caddy and Cloudflare with their existing validated configuration/tools; do not print credentials. Check port 8001 before starting a foreground application. Never kill an unknown listener.

## 5. Repository and isolated Python setup

From the canonical experiment directory:

```bash
cd experiments/nt-imaging-workflow
cp .env.example .env
make bootstrap
make fixtures
```

`make bootstrap` uses the compatible existing Python interpreter to create repository-local `.venv` and `uv.lock`. It does not modify shared MLX or QwenPaw environments. Install browser assets separately:

```bash
cd frontend
npm ci
npm run build
cd ..
```

## 6. Exact dependencies and their roles

Pinned versions are in `pyproject.toml` and `uv.lock`; frontend versions are in `frontend/package-lock.json`.

- `langgraph==1.2.17`: StateGraph, interrupts, routing, replay.
- `langgraph-checkpoint-sqlite==3.1.2`: durable local checkpoints.
- `fastapi==0.162.0`, `uvicorn==0.54.0`: authenticated control plane.
- `pydantic==2.14.1`: typed state-adjacent report/review/error/decision contracts.
- `pydicom==3.0.2`: DICOM parsing, transfer syntax, pixel decoding, Modality LUT/rescale, VOI handling.
- `numpy==2.3.5`: typed pixel operations and deterministic metrics.
- `SimpleITK==2.5.6`: spatially aware bounded resampling without arbitrary flips.
- `pillow==13.0.0`: safe raster decoding and lossless PNG derivatives.
- `httpx==0.28.1`: local oMLX OpenAI-compatible inference and health checks.
- `argon2-cffi==25.1.0`: password hashing.
- Apple Vision via `pyobjc-framework-Vision/Quartz==12.2.2`: existing local OCR mechanism on macOS.
- React 19, TypeScript, and Vite: locally served doctor console.

OpenCV is not needed by the default profile. MONAI and PyTorch are deliberately absent; they belong to a possible future study-level transform pipeline, not this single-frame workflow.

## 7. Configure existing oMLX models

```bash
./scripts/configure_models.sh
make doctor
```

The configuration script securely reads the existing inference key in memory, queries authenticated `/v1/models`, and writes only endpoint/model IDs to ignored `.env`. The verified local IDs are `MedMO-8B-Next` and `Qwen3.5-9B-MLX-4bit`; always rediscover exact IDs on another machine. Do not print or commit the key.

REAL mode requires both IDs and never falls back to MOCK. `make doctor` checks isolation, foundation presence, OCR, model inventory, and minimal real text/vision calls.

## 8. LangGraph, checkpoints, worker, and FastAPI

`src/nt_imaging/graph.py` is the only graph factory. FastAPI receives an upload, creates typed initial state, enqueues it, and returns an opaque run ID. It does not hold the request open during inference.

The worker:

1. Claims one queued job.
2. Opens the SQLite checkpointer for the stable thread ID.
3. Streams graph updates and stores current-node snapshots/heartbeats.
4. Pauses at the typed `interrupt()` for doctor review.
5. Resumes that thread after an authenticated decision.
6. Checks cancellation before advancing and again inside export.

SQLite uses WAL, transactions, migrations, bounded queues, and unique idempotency constraints. State survives ordinary restarts. In-flight model calls are not claimed to be exactly once; recovery requires explicit eligible retry. Export files and audit side effects are idempotent.

## 9. Install the Imaging Readiness Agent policy

The policy is already versioned in `policies/cxr_preparation_v2.json`; no separate model or installer is required. Review [the readiness policy](imaging-readiness-policy.md).

```json
{
  "policy_version": "cxr-preparation-v2",
  "max_input_dimension": 1024,
  "thumbnail_dimension": 512,
  "resampling": "SimpleITK BSpline",
  "border_crop": "Disabled",
  "encoding": "Lossless PNG; separate display thumbnail"
}
```

Preparation performs Modality LUT/rescale before calibrated VOI/window mapping, correct signed and MONOCHROME1/2 semantics, preserves decoded orientation and aspect ratio, records lineage/metrics/library versions, verifies the derivative, and re-screens derived pixels. CLAHE, equalization, sharpening, denoising, elastic/random transforms, lesion cropping, lossy recompression, and generic per-image min-max scaling are prohibited.

![PHI-screened source and prepared model input with the readiness receipt summary](../docs/images/doctor-pipeline-user-guide/31-source-prepared-comparison.png)

## 10. Local graph inspector instead of hosted Studio

No LangSmith account, hosted Studio, Agent Server, `langgraph-cli[inmem]`, SDK, `LANGSMITH_*`, or `LANGCHAIN_TRACING_*` configuration is required. Open a run's **Local graph** tab to inspect:

- current, completed, and pending nodes;
- failed/blocked edge, attempts, revisions, checkpoint thread;
- timestamps/durations, preparation receipt, human decisions;
- model ID, call status, latency, and output hash.

![Local graph inspector with completed nodes and genuine model-call receipts](../docs/images/doctor-pipeline-user-guide/32-local-graph-inspector.png)

Optional self-hosted Arize Phoenix/OpenTelemetry is not enabled. A future integration must bind only to loopback/Tailscale, avoid public Caddy routes, exclude prompts/report text/DICOM metadata/pixels/credentials, and remain optional for execution and tests.

## 11. Authentication and first account

```bash
./scripts/create_doctor.sh
```

Use an interactive hidden prompt or protected `NT_DOCTOR_USERNAME`/`NT_DOCTOR_PASSWORD` process environment. If no password is supplied, a strong random one is printed once only in the local terminal. There is no default credential, public registration, or public reset. Only Argon2id hashes are stored.

Reset and invalidate all sessions:

```bash
./scripts/create_doctor.sh --reset
```

Sessions use opaque hashed tokens, Secure/HttpOnly/SameSite cookies, an eight-hour absolute limit, a 30-minute idle limit, CSRF validation, and login rate limiting. Public examples should use `<your-doctor-password>`, never the real value.

## 12. SQLite, artifacts, backups, and migration

Runtime state is under ignored `var/`: application and checkpoint databases, controlled uploads, PHI-screened/prepared derivatives, receipts, audit events, and exports. None of those runtime artifacts belongs in Git.

Before migration, the executed online backup was saved at:

```text
var/migration-backups/20261027T160203Z
```

It contains SQLite online backups, non-secret configuration, and artifact manifests. The migration report is `var/migration-backups/v3-migration.json`. Run the reversible snapshot migration with:

```bash
uv run python scripts/migrate_v3.py
```

Existing run IDs/history are preserved. Legacy runs without a receipt display `LEGACY_NO_PREPARATION_RECEIPT`; they are not silently assigned a new derivative.

## 13. Build and run the application

Foreground deployed-style runtime:

```bash
make production
```

Open `http://127.0.0.1:8001`. Health checks:

```bash
curl http://127.0.0.1:8001/health/live
curl http://127.0.0.1:8001/health/ready
curl http://127.0.0.1:8000/health
```

Application-only LaunchDaemons, when installed from `deploy/`, are `com.nightthoughts.imaging.api` and `com.nightthoughts.imaging.worker`. They use absolute paths and explicit non-secret environment, run as the unprivileged account, bind loopback, and read oMLX's key only at runtime. Repository plists contain `__PROJECT_ROOT__`, `__SERVICE_USER__`, and `__HOME__` placeholders; the reload script substitutes local values into validated configured copies under `var/deploy-backups/` without embedding workstation details in Git.

```bash
sudo ./scripts/reload_installed_services.sh
```

For a restart without changing plist contents:

```bash
sudo launchctl kickstart -k system/com.nightthoughts.imaging.api
sudo launchctl kickstart -k system/com.nightthoughts.imaging.worker
```

Stop only this application with the corresponding `sudo launchctl bootout ...` commands. Review active jobs before restarting the worker. Do not restart oMLX or QwenPaw for this application.

## 14. Existing Caddy and Cloudflare integration

Only surgical additions are permitted for `imaging.nightthoughts.dev`: one application hostname block, one ingress rule before catch-all 404, and the corresponding DNS route if needed. Never expose oMLX, QwenPaw, the worker, SQLite, checkpoints, internal metrics, debug endpoints, or unrestricted API documentation.

Before any change, create timestamped backups and inspect/merge existing files without overwriting unrelated blocks. The previous deployment backups are:

```text
var/deploy-backups/20261026T164431Z/Caddyfile
var/deploy-backups/20261026T164431Z/config.yml
```

Validate configuration before restarting only the service whose configuration changed:

```bash
caddy validate --config /opt/homebrew/etc/Caddyfile
cloudflared tunnel ingress validate
```

Keep those files available for tested rollback. Do not add another public hostname or tunnel for local evidence services.

## 15. Tailscale-only operator access

The application and internal observability should bind to `127.0.0.1`. Where remote operator access is appropriate, use the existing Tailscale path without changing its configuration or adding a public internal port. Phoenix, if ever enabled, must remain loopback/Tailscale-only. Do not modify Tailscale Serve for this showcase.

## 16. Deterministic demonstration fixtures

```bash
make fixtures
make fixtures
diff -u fixtures/expected/fixture_hashes.json fixtures/expected/fixture_hashes.json
```

The second command regenerates byte-identical files, including deterministic DICOM identifiers. All fixtures are original artificial pixels under CC0-1.0. They include clean PNG/DICOM, MONOCHROME1, signed/windowed, PHI metadata/private tags/burned-in invented text, unsupported CT, multi-frame, corrupt, oversized, and uniform preparation-failure inputs. No external patient dataset is used.

## 17. Run the genuine multi-scenario showcases

Use separate loopback runtimes so production state and accounts are not mixed with evidence:

```bash
./scripts/real_showcase.sh       # REAL on 8003, var/real-showcase
./scripts/mock_guide.sh          # MOCK/FAULT on 8002, var/guide-mock
```

In another terminal, after each is healthy:

```bash
uv run python scripts/run_showcase.py --mode REAL --base-url http://127.0.0.1:8003 --data-root var/real-showcase --output evidence/showcase/real-runs.json
uv run python scripts/run_showcase.py --mode MOCK --base-url http://127.0.0.1:8002 --data-root var/guide-mock --output evidence/showcase/mock-runs.json
```

The verified curated execution contains six REAL and 31 MOCK/FAULT runs. It covers approval/export, rejection, regenerated revisions and limits, PHI/modality/input blocks, preparation/derived-safety failure, malformed output, independent gate retries/exhaustion, model timeout/unavailability, technical retry, queued/active cancellation, and queue saturation. All outcomes pass through authenticated APIs and the real graph; no completed rows are seeded in SQL.

## 18. Verification and screenshots

```bash
make test
make test-real
make test-browser
uv run python scripts/build_v3_evidence.py
```

The current record is 85 non-real tests, one REAL test, and ten responsive browser viewports with interventions/export/session recovery. The browser matrix covers phones, tablet, desktop, and landscape using Chromium emulation, not physical devices.

After showcase runs exist:

```bash
uv run python scripts/capture_showcase_evidence.py
```

Ordinary captures use 1440×900 desktop or 390×844 mobile viewports with `fullPage: false`. Inspect every image before publishing. Mock and fault screenshots must remain labelled and cannot be presented as REAL model successes.

## 19. Troubleshooting, recovery, and rollback

- **Login fails:** verify provisioned credentials, wait out rate limiting, or use the protected local reset. Never recover plaintext from hashes.
- **Local unavailable, public works:** inspect API/worker labels, health, port ownership, and application logs; do not kill unknown processes.
- **Public unavailable, local works:** validate the existing imaging Caddy/Cloudflare route and DNS without altering unrelated ingress.
- **Worker not processing:** inspect queue depth, heartbeat, memory, and worker logs. Queue saturation is HTTP 429, not permission to bypass the limit.
- **oMLX unauthorized/model missing:** run `make doctor` and rediscover exact registered IDs. Never print the credential or silently select MOCK.
- **Preparation failure:** inspect readiness status/receipt/warnings. Doctor approval cannot override it.
- **Export unavailable:** verify all gates, readiness, derived PHI, approval, attempts/revisions, and cancellation.
- **Restart recovery:** in-flight work requires explicit technical retry when eligible; approved exports remain idempotent.

Rollback a proxy change by restoring the timestamped Caddy/Cloudflare backups and revalidating before any approved restart. Unload only application daemons to remove the app. Do not roll back or restart unrelated foundation services as part of application troubleshooting.

## 20. Security checklist and non-production boundary

- Keep `.env`, credentials, hashes, sessions, CSRF tokens, databases, checkpoints, uploads, derivatives, exports, logs, models, and caches out of Git and screenshots.
- Preserve Argon2id, CSRF, session expiry, rate limits, CSP, run ownership, and fail-closed gates.
- Use only synthetic or authorized de-identified images.
- Do not expose internal services or claim the hosted public path is air-gapped.
- Keep REAL, MOCK, and FAULT INJECTION visibly distinct.
- Treat audit chains as tamper-evident demonstration records, not an immutable ledger.
- Treat model review and human approval as research workflow controls, not clinical validation.

The canonical source and additional limitations are in the [NT Imaging Workflow README](../README.md) and [verification record](verification.md).
