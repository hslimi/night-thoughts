# Troubleshooting

## Current application checks

Run `make doctor` before REAL execution. Rediscover exact model IDs rather than guessing. Inspect port ownership instead of killing unknown processes. Application logs are in `var/logs/`; runtime databases, checkpoints, uploads, derivatives, and exports are local-only state.

- **Login fails:** verify the provisioned account and rate-limit cooldown. Reset with `./scripts/create_doctor.sh --reset`; never recover hashes or use default credentials.
- **Local app unavailable:** inspect `com.nightthoughts.imaging.api` and `com.nightthoughts.imaging.worker`, port 8001, and API/worker logs.
- **Public fails while local works:** validate only the existing imaging Caddy/Cloudflare route and DNS. Do not expose internal services or alter unrelated ingress.
- **Worker/queue issue:** inspect heartbeat, queue depth, and memory. One inference runs at a time; 8 active+queued jobs fill the bound and later uploads return 429.
- **oMLX unauthorized/model missing:** run `./scripts/configure_models.sh` and `make doctor`. Never print the key or silently select MOCK.
- **Readiness failure:** inspect `readiness_status`, preparation receipt, source/derivative hashes, dimensions, operations, and warnings. Approval cannot override it.
- **Export unavailable:** check PHI, modality, readiness, derived PHI, contract/visual/quality gates, approval, cancellation, and attempt/revision limits.
- **Restart recovery:** eligible in-flight work needs explicit technical retry. Do not manually create exports; replay of an approved export must preserve hashes and event counts.
- **Mobile issues:** use a current browser, 100% zoom, and reconnect polling. Chromium viewport tests are not physical-device certification.

## Resolved implementation issues

- Python 3.11 uses pinned NumPy 2.3.5 in isolated `.venv`, never the shared MLX environment.
- Vision OCR requires `None` handler options, documented recognition level, and a bounded raster variant. OCR failures quarantine.
- REAL tests require `RUN_REAL_TESTS=1 INFERENCE_MODE=REAL`; `make test-real` sets both with isolated state.
- Decision timestamps are audit data, not fields accepted from model/client decision schemas. Manifest self-hashes are external evidence hashes.
- MedMO/Qwen structured output uses native oMLX `json_schema`, bounded prompts, and disabled template reasoning where required. Failed calls remain closed and budgeted.
- LaunchDaemons run as the unprivileged account with explicit `HOME`, not root, so protected uploads remain accessible without exposing secrets.
- Revision prompts keep concise actionable feedback. Revision and model-call budgets are independent; either can fail closed without export.

The complete doctor/operator recovery table is in [the user guide](doctor-pipeline-user-guide.md#8-all-supported-scenarios-and-recovery-actions).
