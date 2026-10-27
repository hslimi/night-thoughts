# V2 deployment review

Target: `https://imaging.nightthoughts.dev` (unused at inspection time).

## Proposed application changes

- Install `com.nightthoughts.imaging.api` and `com.nightthoughts.imaging.worker` from `deploy/` as system LaunchDaemons. Both use absolute project Python paths, explicit non-secret environment values, loopback only, and no credentials in plist XML. They run as `night-thoughts`, not root, with an explicit `HOME` so the existing oMLX inference key can be read securely at runtime. This was required after the initial root service could not access protected home-directory uploads.
- API listens on `127.0.0.1:8001` with one process; worker owns one durable SQLite checkpoint connection and one inference at a time.
- Add native newsyslog rules for bounded rotation of only `var/logs/*-service*.log`.
- Create/reset the doctor account with `./scripts/create_doctor.sh` or `./scripts/create_doctor.sh --reset`. Passwords are supplied interactively or through protected process environment, never stored in plist files.

## Proposed proxy changes

- Append `deploy/Caddyfile.imaging.snippet` to the existing Caddyfile without changing other host blocks.
- Insert `deploy/Cloudflare.imaging.snippet.yml` immediately before the existing catch-all `service: http_status:404`.
- Create the DNS route with `cloudflared tunnel route dns night-thoughts imaging.nightthoughts.dev`.
- Restart only Caddy with `sudo launchctl kickstart -k system/com.caddy.server` after validation.

Cloudflared runs as `/opt/homebrew/bin/cloudflared tunnel run` with no exposed LaunchDaemon label. The user restarted that existing process in its current supervisor after the ingress was validated; no duplicate tunnel or unknown-process kill was used.

## Backups and rollback

Timestamped backups are stored under `var/deploy-backups/20261026T164431Z/Caddyfile` and `var/deploy-backups/20261026T164431Z/config.yml`. The plists and newsyslog file will also be preserved if replaced. Rollback restores those two configuration files, removes only the imaging ingress/hostname block, and validates before any approved restart. Application LaunchDaemons can be unloaded and removed without touching oMLX, QwenPaw, internal development services, or unrelated routes.

## Service management

```bash
sudo launchctl kickstart -k system/com.nightthoughts.imaging.api
sudo launchctl kickstart -k system/com.nightthoughts.imaging.worker
sudo launchctl bootout system/com.nightthoughts.imaging.api
sudo launchctl bootout system/com.nightthoughts.imaging.worker
```

Bootstrapping uses the plist files under `/Library/LaunchDaemons/`. Restart the worker only after reviewing queued/running jobs. Recovery does not automatically repeat in-flight model calls or exports. Do not restart oMLX or QwenPaw for this application.

## Security and recovery checks

- Public root shows login; API/run/audit/export endpoints require application authentication.
- Only API and worker are installed; oMLX, QwenPaw, internal development services, SQLite, metrics, and internal checkpoints are not proxied.
- API/worker stop-start recovery uses persisted jobs and checkpoints. In-flight work fails closed for explicit retry; exports remain idempotent. No exactly-once model-inference claim is made.
- Public requests and responses transit Cloudflare. Inference and application state remain on the Mac. This Internet-accessible research showcase is not air-gapped, clinically validated, or institutionally hardened.
