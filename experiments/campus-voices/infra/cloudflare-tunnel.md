# Cloudflare Tunnel configuration

Campus Voices uses the existing Night Thoughts tunnel. The public route ends at Caddy on `127.0.0.1:9080`; Caddy forwards only this hostname to the application on `127.0.0.1:3000`.

Do not add a public route for oMLX. The model endpoint remains on `127.0.0.1:8000` and is reachable only by the Campus Voices server.

## 1. Identify the existing tunnel

```bash
cloudflared tunnel list
```

Use an existing tunnel name or UUID. Do not copy its credentials file into this repository.

## 2. Add the application ingress rule

In the existing tunnel configuration, add this rule **before** the final catch-all rule and preserve every unrelated rule:

```yaml
- hostname: campusvoices.nightthoughts.dev
  service: http://127.0.0.1:9080
```

The final rule must remain a catch-all such as:

```yaml
- service: http_status:404
```

Keep the configuration and credentials files outside version control. Validate the edited configuration with the `cloudflared tunnel ingress validate` command supported by the installed version, then restart the existing tunnel service using its established service manager.

## 3. Add the DNS route

```bash
cloudflared tunnel route dns EXISTING_TUNNEL_NAME campusvoices.nightthoughts.dev
```

This creates a DNS record for the application hostname. It does not expose oMLX.

## 4. Verify the route

```bash
caddy validate --config infra/Caddyfile.campusvoices.example
curl --fail --silent --show-error https://campusvoices.nightthoughts.dev/api/health
```

The expected provider is `scripted`, and Dessa must remain `disabled` unless real provider access is separately configured and reviewed.

During development, restrict the public application with Cloudflare Access. A real-time microphone provider will require HTTPS or localhost before a browser can grant microphone permission; the scripted prototype does not request that permission.
