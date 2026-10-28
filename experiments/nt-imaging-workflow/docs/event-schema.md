# Durable event and SSE schema

## `app_events`

Every meaningful application transition appends one immutable event in the same transaction as its snapshot/job transition.

| Field | Meaning |
|---|---|
| `sequence` | Monotonically increasing global event ID used by SSE and Last-Event-ID |
| `event_id` | Opaque UUID |
| `run_id` / `thread_id` | Run and stable LangGraph checkpoint thread; null for worker-only events |
| `job_id` | Control-plane job where applicable |
| `run_sequence` | Monotonically increasing sequence within each run; unique per run |
| `event_type` | Typed transition listed below |
| `run_status` | Aggregate workflow status, never inferred from prose |
| `node_name` | Graph node, queue, model-call stage, or worker |
| `attempt` / `revision` | Bounded drafting attempt and doctor revision |
| `model_call_sequence` | Provider call sequence within the run, when applicable |
| `timestamp_utc` | UTC transition timestamp |
| `duration_ms` | Measured node/model/export duration when available |
| `payload_json` | Safe structured metadata and sanitized state snapshot; no source path or prompts |
| `workflow_version` / `inference_mode` | Workflow identity and REAL or MOCK label |

Required types are `RUN_CREATED`, `RUN_QUEUED`, `RUN_STARTED`, `NODE_STARTED`, `NODE_PROGRESS` (only for measurable progress), `NODE_COMPLETED`, `NODE_FAILED`, `GATE_RESULT`, `PREPARATION_STARTED`, `PREPARATION_OPERATION_COMPLETED`, `PREPARATION_COMPLETED`, `DERIVED_SAFETY_RESULT`, `MODEL_CALL_STARTED`, `MODEL_CALL_COMPLETED`, `MODEL_CALL_FAILED`, `ATTEMPT_STARTED`, `ATTEMPT_EXHAUSTED`, `REVISION_REQUESTED`, `REVISION_STARTED`, `REVISION_COMPLETED`, `HUMAN_APPROVAL_REQUIRED`, `HUMAN_DECISION_RECORDED`, `EXPORT_STARTED`, `EXPORT_COMPLETED`, `RUN_CANCELLED`, `RUN_FAILED`, `RUN_COMPLETED`, `WORKER_HEARTBEAT`, `WORKER_STARTED`, `WORKER_STOPPED`, and `TECHNICAL_RETRY_REQUESTED`.

`PREPARATION_OPERATION_COMPLETED` is emitted only after a real operation. `MODEL_CALL_STARTED` means running; it never implies token streaming. Percentage progress is not fabricated. The legacy audit/provenance records remain separate; `app_events` is the live operational stream.

## SSE endpoints

- `GET /api/events`: global authenticated stream.
- `GET /api/runs/{run_id}/events`: run-scoped authenticated stream with run ownership checks.

Responses use `text/event-stream`, `Cache-Control: no-cache, no-store`, and `X-Accel-Buffering: no`. Each durable event has `id: <sequence>` and `event: <event_type>`. `Last-Event-ID` replays events after that sequence. A detected gap emits `resync` with a full safe snapshot before continuing. Initial `snapshot` events provide current state.

Named `heartbeat` events allow the client to measure packet age. The server revalidates the session periodically and sends `session-expired` before closing an invalid stream. Session tokens never appear in URLs. Multiple tabs are read-only with respect to the event ledger.

The frontend displays `LIVE` only for recent packets, `RECONNECTING` for an open/retrying or stale connection, and `OFFLINE` when updates are too old or unavailable. A bounded JSON snapshot fallback is used only when `EventSource` is unavailable.
