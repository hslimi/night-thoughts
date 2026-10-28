# Account management without service restarts

Use the canonical project directory. The account CLI refuses the obsolete installation and supports an explicit isolated `--data-root` for tests.

```bash
./scripts/create_doctor.sh
./scripts/create_doctor.sh --reset
./scripts/create_doctor.sh --reset --data-root /absolute/path/to/isolated/var
```

Provide `NT_DOCTOR_USERNAME` and `NT_DOCTOR_PASSWORD` through protected process environment or use the interactive hidden prompt. A blank password generates a strong random value shown once in the local terminal. Public examples use `<your-doctor-password>`.

The command prints the canonical runtime and a non-secret target database fingerprint before and after success, the username, and the number of invalidated sessions. It never prints a password hash, cookie, token, or service secret.

`ControlDB.upsert_user` updates the Argon2id hash and deletes sessions in one transaction. Authentication reads current SQLite state on every attempt; no in-memory credential cache survives a reset. The new credentials work immediately and neither LaunchDaemon is restarted.

The automated test starts with an authenticated session, resets through the CLI operation, verifies that old session is rejected, logs in with the new password immediately, and confirms logout. The obsolete data root is also rejected. Services remain running throughout.

If the original password is unknown, use the local reset command rather than attempting to recover plaintext from Argon2id hashes. There is no public registration or public password reset.
