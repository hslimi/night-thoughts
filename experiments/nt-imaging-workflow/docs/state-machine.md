# State machine

`ingest_validate` accepts only regular supported files within byte/pixel limits. `phi_screen` routes concerns to `QUARANTINED`. `modality_gate` accepts only validated single-frame CR/DX DICOM or raster with a user `XR` declaration; other outcomes reach `NEEDS_HUMAN_REVIEW` before drafting.

`imaging_readiness` creates and verifies a versioned lossless derivative. `derived_image_safety_check` re-screens it. Either failure ends `IMAGE_PREPARATION_FAILED` with zero model calls and no export. Success exposes only the prepared artifact ID to drafting.

`generate_draft` increments `attempt`, clears old human decisions, and resets contract, visual-consistency, and quality statuses. Malformed output gets at most one syntax/schema repair call within the same attempt and total budget. Persistent invalid output ends `MODEL_OUTPUT_INVALID`; retryable provider failures end `FAILED` without export.

A deterministic contract pass is required before visual consistency. Visual pass is required before text quality. Every failure either regenerates while `attempt < max_attempts` or reaches `NEEDS_HUMAN_REVIEW`. A later quality result cannot change visual status.

`human_approval` emits a typed interrupt. APPROVE requires every gate; REJECT ends `HUMAN_REJECTED`; REQUEST_CHANGES starts a bounded revision or ends `NEEDS_HUMAN_REVIEW` when exhausted. Cancellation ends `CANCELLED` and blocks late export.

Only the separate export node writes files. It rechecks PHI, modality, readiness, derived PHI, all three draft gates, attempt bounds, cancellation, typed approval, and draft schema before atomic idempotent export, ending `APPROVED_DRAFT_EXPORTED`.
