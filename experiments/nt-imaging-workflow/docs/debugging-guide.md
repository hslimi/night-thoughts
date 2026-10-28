# Debugging and recovery guide

Open **Debugging center** from the live worklist. It is available only through the authenticated application and exposes operational metadata, not secrets, raw patient data, full prompts, or hidden model reasoning.

## Overview

Use Overview for application/workflow version, inference mode, model IDs, canonical instance ID, code/data/database fingerprints, worker heartbeat, queue depth, active job, SSE connection count, and last durable event sequence. A mismatch between API and worker fingerprints is an alert, not a cosmetic warning.

## Run inspector and trace waterfall

Select an opaque run ID to inspect typed state, checkpoint thread, current/previous nodes, gate results, preparation receipt, job history, event gaps, model-call receipts, and cancellation/retry eligibility. Trace waterfall uses actual event durations and shows queue wait, human wait, export duration, failures, and retries. No percentage progress is inferred.

## Logs

Structured logs can be filtered by run, event type, and safe text. They include run/thread/job/node/attempt/revision/model-call correlation. They exclude credentials, cookies, CSRF tokens, API keys, raw DICOM metadata, full sensitive prompts, and patient identifiers.

## Diagnostics and support bundle

Diagnostics checks database read/write, checkpoint and artifact availability, oMLX health/model inventory, OCR, frontend build, SSE, worker freshness, queue saturation, and API/worker identity. **Download sanitized support bundle** contains those checks, safe configuration, recent structured errors, selected run events, receipts, and versions. It contains no medical-image artifacts or secrets.

## Stale-state rules and recovery

- Worker heartbeat older than 15 seconds: stale worker.
- Running job without progress for more than 60 seconds: stale execution.
- Queued job without a fresh worker: no worker available.
- Model call older than its configured timeout without completion: model timeout alert.
- API/worker code or data-root fingerprint mismatch: incompatible runtime.

Use **Retry technical failure** only when the run is failed and explicitly retryable. The API also requires the previous job to be `FAILED` or `CANCELLED`, proving it is no longer executing. It creates a new run; every gate and approval is still required. Never repeat uncertain in-flight inference or export automatically. Queued/active work can be cancelled where supported; late responses cannot export. Open the failed node/error and download diagnostics before changing service configuration.

Do not restart oMLX, QwenPaw, Caddy, Cloudflare, Tailscale, or unrelated services for application debugging. Only `com.nightthoughts.imaging.api` and `com.nightthoughts.imaging.worker` are in the application recovery boundary.
