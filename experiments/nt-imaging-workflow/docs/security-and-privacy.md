# Security and privacy

The current security and privacy record is [security-and-limitations.md](security-and-limitations.md). It replaces older Agent Server/hosted-Studio guidance with the authenticated durable FastAPI/worker runtime and local inspector.

Key residual risks remain: PHI screening is not guaranteed anonymization, audit records are not an immutable ledger, public traffic transits Cloudflare, and model/doctor review is not clinical validation. Never commit `.env`, credentials, session data, databases, checkpoints, uploads, derivatives, exports, logs, or real patient information.
