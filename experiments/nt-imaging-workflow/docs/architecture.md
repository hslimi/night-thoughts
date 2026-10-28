# NT Imaging Workflow architecture

## Scope and trust boundaries

NT Imaging Workflow is a single-node research console, not an agent swarm or diagnostic service. One `StateGraph` factory in `src/nt_imaging/graph.py` is shared by direct CLI tests and the durable FastAPI/worker runtime. Models propose structured content; deterministic routing and export policy remain authoritative.

The request path is:

```text
Browser
  → HTTPS imaging.nightthoughts.dev (existing public route)
  → Cloudflare Tunnel and Caddy on 127.0.0.1:9080
  → authenticated FastAPI/static React application on 127.0.0.1:8001
  → bounded job queue in controlplane.sqlite3 (WAL)
  → one dedicated worker and deployed-checkpoints.sqlite3
  → existing oMLX on 127.0.0.1:8000
```

Only API and worker are application-managed services. oMLX, QwenPaw, Caddy, Cloudflare, Tailscale, SSH, power settings, and unrelated launchd jobs are foundation dependencies. Public web traffic transits Cloudflare; inference and application state stay on the Mac. This is not air-gapped.

## Graph and terminal policy

```text
Upload
→ ingest_validate
→ phi_screen
→ modality_gate
→ imaging_readiness
→ derived_image_safety_check
→ generate_draft
→ deterministic_contract_gate
→ visual_consistency_review
→ text_quality_review
→ human_approval
→ export_approved_draft
```

Ingestion validates and stores the original before screening. PHI clearance and supported modality are prerequisites for readiness. Readiness failure or derived-image screening failure prevents every model call and ends as `IMAGE_PREPARATION_FAILED`. `PREPARING_IMAGE` and `IMAGE_READY` are non-terminal operational states.

Draft, visual-consistency, and text-quality calls use strict structured schemas. Deterministic retry routes allow only bounded regeneration. Visual failure prevents quality review. Every regeneration resets downstream statuses. Human review is a typed LangGraph `interrupt()` with APPROVE, REJECT, and REQUEST_CHANGES decisions and its own bounded revision history.

Terminal/review states include `QUARANTINED`, `NEEDS_HUMAN_REVIEW`, `IMAGE_PREPARATION_FAILED`, `MODEL_OUTPUT_INVALID`, `FAILED`, `HUMAN_REJECTED`, `CANCELLED`, and `APPROVED_DRAFT_EXPORTED`. Failed, rejected, cancelled, exhausted, and unapproved runs cannot export.

Only `export_approved_draft` writes final files. It independently validates PHI, modality, readiness, derived PHI, contract, visual consistency, text quality, attempt bounds, draft schema, cancellation, and typed approval. Its run-ID/draft-hash/workflow idempotency key is unique in SQLite. Existing exports are hash-verified on replay.

## Imaging Readiness Agent

`src/nt_imaging/imaging/readiness.py` is deterministic, versioned preparation code. Its only external identifiers are a PHI-cleared artifact ID, supported profile, policy version, run ID, and thread ID; API callers never supply filesystem paths.

The lineage is:

```text
original_upload → phi_cleared_artifact → prepared_model_input → display_thumbnail
```

DICOM handling uses pydicom pixel decoding, Modality LUT/rescale, one VOI LUT or calibrated window, signed-range handling, and MONOCHROME1/2 semantics. SimpleITK performs bounded, aspect-ratio-preserving BSpline resampling only above the policy maximum. Pillow writes lossless PNG working and thumbnail artifacts. No arbitrary laterality flip or universal per-image min-max normalization occurs.

A receipt records source/derivative/thumbnail SHA-256, dimensions, source dtype/bit depth/signedness/transfer syntax, prepared intensity and saturation metrics, operations, warnings, policy/code/library versions, timing, and lineage. Reuse requires matching source, policy, code, file hash, and decoded dimensions. Changed inputs or policy create a different readiness key. Writes use atomic replacement. Derived pixels pass the same fail-closed OCR mechanism before drafting.

The default profile prohibits CLAHE, equalization, sharpening, denoising, elastic/random transforms, lesion cropping, lossy recompression, source overwrite, and destructive enhancement. MONAI and PyTorch are not installed.

## Durable control plane

FastAPI enqueues work and returns run IDs. A single worker owns graph execution and checkpoint connections. Additional requests enter a bounded queue; saturation returns HTTP 429. Jobs, snapshots, users, hashed sessions, security events, and idempotency state use transactions and unique constraints in WAL-mode SQLite.

The worker streams graph updates, persists the current node and heartbeat, and checks cooperative cancellation before the next node. The export node also checks cancellation directly. Late worker responses cannot authorize export after cancellation. Recovery marks in-flight work for explicit technical retry rather than claiming exactly-once inference. Approved exports and external side effects are idempotent.

Clinical/run/audit/artifact/export APIs require application authentication. Sessions use opaque random tokens stored only as hashes, absolute/idle expiry, Secure/HttpOnly/SameSite cookies, CSRF checks, and rate-limited Argon2id login. Object IDs and run ownership are validated. No arbitrary client paths, public registration, raw traces, hidden model reasoning, or public OpenAPI endpoints are exposed.

## Durable events, SSE, and local observability

There is no Agent Server, hosted Studio, LangSmith account, tracing configuration, SDK, CLI, or callback requirement. `app_events` in the canonical control database stores global and per-run sequences, transition types, aggregate status, node, attempts, revisions, model-call sequence, UTC timestamps, measured durations, safe payloads, workflow version, and inference mode. Snapshot/job changes and event appends share transactions; replay detects gaps without duplicating events.

Graph wrappers emit actual node boundaries, preparation operations, model calls, attempts, revisions, human decisions, export, cancellation, and technical retry. Worker startup, idle/active heartbeat, and shutdown include canonical instance/code/data fingerprints. Model-call running does not imply token streaming.

Authenticated SSE endpoints `GET /api/events` and `GET /api/runs/{run_id}/events` send initial snapshots, durable event IDs, Last-Event-ID replay, gap `resync`, heartbeat packets, and session-expiry closure. Headers disable buffering. Browser connections do not hold the inference worker open and multiple tabs cause no duplicate writes. A bounded JSON snapshot fallback exists only when EventSource is unavailable.

The worklist, workflow graph, attempts/revisions/model calls, and debugging center update from event snapshots. `LIVE` requires recent packets; stale/reconnecting/offline states are explicit. The local graph and debugging views show current/completed/pending/failed/skipped/waiting nodes, traces, durations, gate results, and receipts without prompts or hidden reasoning. See `docs/event-schema.md` and `docs/debugging-guide.md`.

Optional Phoenix/OpenTelemetry is not enabled. If added later it must be loopback/Tailscale-only, carry bounded operational metadata only, and remain optional for tests and execution.

## Repository interfaces

- `src/nt_imaging/graph.py`, `state.py`, `routing.py`: graph, typed state, deterministic routes.
- `src/nt_imaging/nodes/`: ingestion, PHI/modality, readiness, draft/gates, approval, terminal states, export.
- `src/nt_imaging/imaging/`: DICOM/raster handling, preparation, OCR, receipts.
- `src/nt_imaging/inference/`: separate REAL oMLX and labelled MOCK providers.
- `src/nt_imaging/controlplane/`: authentication, versioned API, SQLite jobs/snapshots, single worker.
- `frontend/src/`: responsive React/TypeScript doctor console and local inspector.
- `fixtures/`, `tests/`, `scripts/`: deterministic synthetic inputs, verification, API-driven showcases, evidence.
- `evidence/manifest-v4.json`: sanitized machine-readable execution record and limitations.
