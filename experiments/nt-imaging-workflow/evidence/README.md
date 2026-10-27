# Evidence

> **Research demonstration only. AI-assisted drafts require qualified human review and are not for clinical use.**

`manifest-v3.json` is the authoritative current record: workflow/preparation versions, lock hashes, model IDs, fixture provenance/hashes, curated run/thread/model-call correlation, test totals, migration details, screenshot hashes, and explicit limitations. `showcase/` contains sanitized API-driven REAL and MOCK/FAULT run reports. `responsive/console-browser-tests.json` records actual layout and intervention assertions.

The 34 guide screenshots under `docs/images/doctor-pipeline-user-guide/` are genuine normal viewport captures, not mockups or multi-thousand-pixel full-page images. Mock/fault evidence is workflow behavior only, not model-quality evidence. Hosted Studio is not part of the current architecture; local graph inspector evidence uses actual deployed-state receipts.

Run `make test`, `make test-real`, `make test-browser`, and `uv run python scripts/build_v3_evidence.py`. See `docs/verification.md` for the execution record and unverified items. Older manifests and Studio captures are historical and are not the current acceptance record.
