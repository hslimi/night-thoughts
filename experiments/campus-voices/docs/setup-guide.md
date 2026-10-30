# Reproduce Campus Voices

This guide builds and verifies the scripted Campus Voices prototype on the existing Night Thoughts Mac mini foundation. It does not start a student study or collect real student data.

## 1. Get the source and install

```bash
git clone https://github.com/hslimi/night-thoughts.git
cd night-thoughts/experiments/campus-voices
npm ci
```

If the repository is already present, enter `experiments/campus-voices` from its root. The experiment uses npm and includes a lockfile.

## 2. Configure local environment

```bash
cp .env.example .env
```

Keep `HOST=127.0.0.1` and `PORT=3000`. Set `OMLX_BASE_URL` and `OMLX_MODEL` to the local endpoint and an installed model. Set the server-only `OMLX_API_KEY` locally; never place it in `app/`, a screenshot, or Git.

Query the installed models without printing the key:

```bash
curl --fail --silent --show-error \
  -H "Authorization: Bearer ${OMLX_API_KEY}" \
  http://127.0.0.1:8000/v1/models
```

The application uses scripted feedback when oMLX is absent or incomplete. Both feedback modes are labelled in the interface.

## 3. Check the application

```bash
npm run format:check
npm run lint
npm run typecheck
npm test
npx playwright install chromium
npm run test:e2e
npm run build
node scripts/verify-static.mjs
```

The tests use synthetic interactions only. They verify the complete scenario, the automatic five-minute ending, early ending, disabled Dessa provider, same-origin browser requests, and deletion of local data.

## 4. Run locally

For development:

```bash
npm run dev
```

For the production build:

```bash
npm start
```

Open `http://127.0.0.1:3000`. Confirm the health endpoint:

```bash
curl --fail --silent --show-error http://127.0.0.1:3000/api/health
```

The response identifies the `scripted` provider and `disabled` Dessa provider. Complete “My First Seminar Contribution” with synthetic choices. No microphone prompt should appear.

## 5. Add only the Campus Voices Caddy route

Merge this block into the existing Caddyfile; do not replace unrelated routes:

```caddy
http://campusvoices.nightthoughts.dev {
    encode zstd gzip
    reverse_proxy 127.0.0.1:3000
}
```

The `http://` hostname is intentional in the reference architecture: Cloudflare terminates public HTTPS and connects to the local tunnel, while Caddy receives the tunnel traffic on port `9080`.

Validate before reloading:

```bash
caddy validate --config /path/to/Caddyfile
```

Restart or reload Caddy with the service manager already configured on the machine. Keep oMLX on localhost and do not add a Caddy route for it.

A launchd template is provided in `infra/`. Replace its absolute-path placeholders, keep credentials in an ignored local `.env`, and use the normal user or system service domain appropriate to the installation.

## 6. Add the tunnel ingress and DNS route

Preserve the existing tunnel rules and add the Campus Voices hostname before the final catch-all:

```yaml
- hostname: campusvoices.nightthoughts.dev
  service: http://127.0.0.1:9080
```

Validate and restart the existing tunnel service, then create the DNS route with an existing tunnel name:

```bash
cloudflared tunnel route dns EXISTING_TUNNEL_NAME campusvoices.nightthoughts.dev
```

Do not commit the tunnel configuration or credentials JSON. See [`../infra/cloudflare-tunnel.md`](../infra/cloudflare-tunnel.md) for the route boundaries.

## 7. Verify public HTTPS

```bash
curl --fail --silent --show-error https://campusvoices.nightthoughts.dev/api/health
```

Open the public URL and repeat the synthetic scenario. A future real-time microphone provider requires HTTPS outside localhost; browser microphone permission is origin-specific. The current scripted provider does not request microphone access. Use Cloudflare Access to restrict development traffic.

## 8. Capture and clean up

```bash
node scripts/capture.mjs http://127.0.0.1:3000
node scripts/capture.mjs https://campusvoices.nightthoughts.dev
```

Inspect every screenshot before sharing. Use synthetic data and a clean `1440×1000` browser viewport. Delete local practice data through the interface when finished. Logs, generated media, real student data, and temporary sensitive screenshots are excluded by `.gitignore`.
