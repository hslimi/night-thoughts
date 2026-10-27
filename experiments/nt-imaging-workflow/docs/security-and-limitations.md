# Security and limitations

## Demonstration boundary

NT Imaging Workflow is an Internet-accessible research showcase, not a clinically validated, certified, or institutionally hardened deployment. It does not provide autonomous diagnosis, clinical sign-off, regulatory clearance, diagnostic accuracy evidence, or production hospital readiness. Use only synthetic or authorized de-identified images.

Public requests and responses transit the existing Cloudflare/Caddy route. Inference and application state remain on the Mac mini. The system is not air-gapped.

## Controls implemented

- Application-level Argon2id password hashes; no default credentials, public registration, or public reset.
- Opaque random sessions stored only as token hashes, eight-hour absolute and 30-minute idle expiration, logout/reset invalidation, CSRF checks, and login rate limiting.
- Secure, HttpOnly where appropriate, SameSite=Strict `__Host-` cookies; restrictive CSP, frame/MIME/referrer protections, and no browser CDN dependencies.
- Loopback API/worker, bounded uploads/pixels/queue/model calls/revisions, one inference worker, safe structured errors, and no public API documentation.
- Opaque artifact/run IDs, run-scoped authorization, atomic artifact/export writes, idempotency constraints, WAL SQLite, and restart recovery.
- Fail-closed PHI/modality/readiness/derived-image/draft gates and mandatory typed doctor approval. Model output cannot change routing or authorize export.
- REAL and explicitly labelled MOCK/FAULT providers; loopback-only fault profiles and no silent fallback.

## Important limitations

- PHI screening is not guaranteed anonymization or DICOM PS3.15 confidentiality-profile conformance. OCR can miss or misread text. Do not upload identifiable patient information.
- Supported input is deliberately narrow: single-frame CR/DX chest radiographs and declared PNG/JPEG. Study-level 2D/3D, CT/MRI/ultrasound, and compressed DICOM are not implemented.
- Preparation verifies deterministic transformation and basic derivative integrity; it does not prove diagnostic preservation or clinical suitability.
- Model-assisted visual consistency is not independent clinical verification. Text quality is not clinical truth. Doctor approval is research-draft authorization only.
- Audit hashes are tamper-evident demonstration records, not an immutable ledger; an administrator can alter SQLite.
- Cooperative active cancellation takes effect after the current call. Completed exports cannot be cancelled. Exactly-once inference is not claimed; side effects are idempotent.
- SQLite and local files require normal host backups and access control. No institutional key management, multi-user RBAC, SIEM, high availability, or formal threat assessment is claimed.
- Browser tests use Chromium touch emulation, not physical devices or an accessibility certification.
- LangSmith/hosted Studio are absent; local observability is operational metadata, not hidden model reasoning. Phoenix is optional and not enabled.
- Public authentication has not been evaluated as an institutional identity solution. Additional perimeter controls must not replace application authentication or safety gates.

See [verification](verification.md) for what was actually executed and any pending deployment action.
