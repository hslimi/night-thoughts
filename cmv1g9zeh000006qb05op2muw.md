---
title: "Complete Guide: Always-On Mac Server with MLX, oMLX & QwenPaw"
datePublished: 2026-10-09T21:01:08.387Z
cuid: cmv1g9zeh000006qb05op2muw
slug: complete-guide-always-on-mac-server-with-mlx-omlx-qwenpaw
cover: https://cdn.hashnode.com/uploads/covers/6a92730f9a9aa7f72e74fdf4/040513aa-a14f-4cc7-9b62-45d63fc9e230.jpg
tags: ai, mlx, macmini, qwenpaw

---

## Tested Environment

Everything in this guide was verified on the following setup. If your versions are close, the commands should work unchanged.

| Component | Version | Notes |
|-----------|---------|-------|
| **macOS** | 15.x (Sequoia) or later | Required for oMLX |
| **Chip** | Apple Silicon (M1/M2/M3/M4) | Required for MLX and oMLX |
| **Homebrew** | 4.x | Package manager for oMLX, Caddy, and Tailscale |
| **uv** | 0.8.x or later | Python version + package manager |
| **Python (MLX venv)** | 3.11.x | Managed by uv at `~/.mlx-venv` |
| **Python (QwenPaw)** | 3.12.x | Bundled by QwenPaw's installer |
| **MLX** | 0.32.x | Apple's ML framework |
| **mlx-lm** | 0.28.x | LLM extensions for MLX |
| **oMLX** | latest via `jundot/omlx` | Inference server + admin dashboard |
| **QwenPaw** | latest via `agentscope.io` | Agent framework + web console |
| **Caddy** | 2.x | Reverse proxy for custom domain routing |
| **Tailscale** | latest via `--cask` | Mesh VPN + custom domain certificates |

> **Note:** Version numbers above reflect the state of the ecosystem when this guide was written. Run `brew --version`, `uv --version`, or the relevant `--version` flag after each install to confirm what you have.

## Part 1: Prepare macOS for Headless Server Mode

These steps ensure your Mac never sleeps, is accessible remotely, and boots into a usable state without manual intervention.

### 1.1 Prevent System Sleep

Run this in Terminal to disable all sleep modes permanently:

```bash
sudo pmset -a disablesleep 1 sleep 0 disksleep 0 displaysleep 0 standby 0 autopoweroff 0 powernap 0
```

**Expected output:** You'll be prompted for your password. After entry, no confirmation message appears — that's normal.

Verify with:

```bash
pmset -g
```

**Expected output:**

```
System-wide power settings:
 SleepDisabled		1
Currently in use:
 standby              0
 Sleep On Power Button 1
 autorestartatconnect 0
 autorestart          0
 SleepServices        0
 powernap             0
 networkoversleep     0
 disksleep            0
 sleep                0 (sleep prevented by powerd, bluetoothd)
 ttyskeepawake        1
 displaysleep         0
 tcpkeepalive         1
 powermode            0
 womp                 1
```

> **Note:** On macOS Ventura (13) and later, `pmset` reports the disablesleep setting as `SleepDisabled 1` instead of `disablesleep 1`. This is expected — it means the same thing.
>
> The annotation `(sleep prevented by powerd, bluetoothd)` next to `sleep 0` is **informational, not an error**. It simply means that in addition to your `pmset` settings, system daemons are also actively preventing sleep. Your server will stay awake.

### 1.2 Enable SSH (Remote Login)

On macOS Catalina (10.15) and later, the `systemsetup` command requires **Full Disk Access** to toggle Remote Login. Running it without that permission will fail with:

```
setremotelogin: Turning Remote Login on or off requires Full Disk Access privileges.
```

This is a macOS security feature (TCC), and `sudo` alone does not bypass it. Follow these steps to fix it permanently.

**Step 1: Grant Full Disk Access to Terminal**

1. Open **System Settings**.
2. Go to **Privacy & Security** → **Full Disk Access**.
3. Click the **+** button.
4. Navigate to **Applications** → **Utilities** and select **Terminal.app** (or your terminal of choice, e.g., iTerm).
5. Toggle Terminal **on** in the list.
6. **Quit Terminal completely** (`Cmd+Q`) and reopen it. The permission only takes effect for new sessions.

**Step 2: Enable Remote Login**

Now run the command. It will succeed without the permission error:

```bash
sudo systemsetup -setremotelogin on
```

**Expected output:** `setremotelogin: remote login is now on`

Verify:

```bash
sudo systemsetup -getremotelogin
```

**Expected output:** `Remote Login: On`

Now you can SSH from another Mac: `ssh username@your-mac-ip`

### 1.3 Enable Auto-Login (Required for launchd Services at Boot)

launchd user agents only start after a user logs in. Without auto-login, your services won't run after a reboot.

1. Open **System Settings** → **Users & Groups**
2. Click **Automatic Login** → select your user account
3. Enter your password when prompted

> **Note:** FileVault must be OFF for auto-login to work. Go to **System Settings → Privacy & Security → FileVault** and turn it off if it's enabled. This is acceptable for a physically secure home server.

### 1.4 Optional: Menu Bar Server Mode Toggle

For quick control without terminal, install the `mac-server-mode` menu bar app:

```bash
git clone https://github.com/thairc-dev/mac-server-mode.git && cd mac-server-mode && ./build.sh && nohup ./mac-server-mode >/dev/null 2>&1 & ./install-launch-agent.sh
```

A ⚡ icon appears in your menu bar. Press `Ctrl + Option + Cmd + S` to toggle server mode (screen off, system awake).

## Part 2: Install uv & Python 3.11

### 2.1 Install uv

`uv` is a fast, all-in-one Python package and version manager written in Rust. Install it via the official one-liner:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh && source ~/.zshrc && uv --version
```

**Expected output:** Installation progress bars, then `uv 0.x.x`.

### 2.2 Install Python 3.11 with uv

Install Python 3.11 as a uv-managed Python:

```bash
uv python install 3.11 && uv python list | grep 3.11
```

**Expected output:** Download progress, then the installed Python 3.11 version.

### 2.3 Create a Virtual Environment for MLX

Create a dedicated virtual environment, activate it, and verify the version in one go:

```bash
uv venv --python 3.11 ~/.mlx-venv && source ~/.mlx-venv/bin/activate && python --version && python -c "import platform; print(platform.processor())"
```

**Expected output:**

```
Python 3.11.x
arm
```

> **Critical:** If you see `i386` instead of `arm`, you have a Rosetta (x86) Python. Reinstall Python 3.11 through uv and start over.

## Part 3: Install MLX Framework

MLX is Apple's native machine learning framework for Apple Silicon.

With your virtual environment activated, install the framework and verify it:

```bash
source ~/.mlx-venv/bin/activate && uv pip install mlx mlx-lm && python -c "import mlx.core as mx; print(mx.__version__)"
```

**Expected output:** `Successfully installed mlx-x.x.x mlx-lm-x.x.x ...` followed by `0.32.x`.

> **Note:** The top-level `mlx` module does **not** export `__version__`. If you try `python -c "import mlx; print(mlx.__version__)"`, you'll get `AttributeError: module 'mlx' has no attribute '__version__'`. The version attribute lives on `mlx.core`. Alternatively, you can read the version from package metadata:
> ```bash
> python -c "import importlib.metadata as md; print(md.version('mlx'))"
> ```

## Part 4: Install oMLX (Web Dashboard + Background Service)

oMLX is an LLM inference server optimized for Apple Silicon, built on the MLX framework. It provides continuous batching, tiered KV caching (hot in-memory + cold SSD), and a web-based admin dashboard for managing models. It is actively maintained and ships as a Homebrew formula with native launchd service integration.

> **Note:** oMLX is a community project maintained by `jundot`. It is built directly on top of Apple's MLX framework (which *is* official).

> **Platform requirement:** oMLX requires **Apple Silicon** (M1/M2/M3/M4) and **macOS 15.0 (Sequoia) or later**. Intel Macs and earlier macOS versions are rejected during installation.

### 4.1 Install Homebrew

If you don't already have Homebrew, install it and set up your PATH in one command:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" && echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile && eval "$(/opt/homebrew/bin/brew shellenv)" && brew --version
```

**Expected output:** Installation progress messages, then `Homebrew 4.x.x`.

> **Note:** If Homebrew is already installed, the installer will detect it and skip installation. You can safely run this command again.

### 4.2 Tap, Trust, and Install oMLX

Run all three steps in one command:

```bash
brew tap jundot/omlx https://github.com/jundot/omlx && brew trust jundot/omlx && brew install jundot/omlx/omlx
```

**Expected output:**

```
==> Tapping jundot/omlx
Cloning into '/opt/homebrew/Library/Taps/jundot/homebrew-omlx'...
Tapped 1 formula.
==> Successfully trusted tap jundot/omlx.
==> Installing omlx from jundot/omlx
/opt/homebrew/Cellar/omlx/x.x.x: ...
```

> **Why `brew trust` is needed:** Recent versions of Homebrew refuse to load formulas from third-party taps unless you explicitly trust them — a security feature to prevent arbitrary code execution from untrusted sources. If you skip this, you'll see `Error: Refusing to load formula jundot/omlx/omlx from untrusted tap jundot/omlx.`

### 4.3 Set the API Key

oMLX requires an API key for all requests to the `/v1/*` endpoints. **You choose this key yourself** — it's not generated. For this guide, we'll use:

```
omlx-night-thoughts
```

> **Important:** `omlx-night-thoughts` is just an example. You can replace it with any string you want — as long as you use the **same value** in QwenPaw's config later in §5.2. If you change it here, change it there too.

Write the key into oMLX's settings file (creating the file if needed) and restart the service:

```bash
mkdir -p ~/.omlx && cat > ~/.omlx/settings.json << 'EOF'
{
  "auth": {
    "api_key": "omlx-night-thoughts"
  }
}
EOF
```

If you haven't started the service yet, this file is read automatically on first launch. If oMLX is already running, restart it to pick up the key:

```bash
brew services restart omlx
```

### 4.4 Start oMLX as an Always-On Background Service

Register oMLX with `brew services`, which installs a launchd agent that auto-starts on login and restarts on crash:

```bash
brew services start omlx && brew services list | grep omlx
```

**Expected output:**

```
==> Successfully started `omlx` (label: sh.brew.omlx)
omlx    started    yourname    ~/Library/LaunchAgents/sh.brew.omlx.plist
```

The `Status` should be `started`. Homebrew writes the launchd plist to `~/Library/LaunchAgents/sh.brew.omlx.plist` automatically — no manual plist creation needed.

**Useful `brew services` commands:**

```bash
brew services stop omlx      # stop the service
brew services restart omlx   # restart the service
brew services info omlx      # show detailed status
```

### 4.5 Open the Admin Dashboard

oMLX binds to `http://localhost:8000` by default. Open the admin dashboard in your browser:

```
http://localhost:8000/admin
```

From another device on your network, use your Mac's IP: `http://your-mac-ip:8000/admin`.

> **Note:** The dashboard lives at `/admin`, not `/`. Hitting the root URL returns a 404 by design.

### 4.6 Verify the API Key Works

Before moving on, confirm the key is accepted:

```bash
curl -s -H "Authorization: Bearer omlx-night-thoughts" http://localhost:8000/v1/models
```

**Expected output:** `{"object":"list","data":[]}` — an empty list is correct at this stage because no model is loaded yet. The important thing is that you don't see `{"detail":"API key required"}` or a `401`.

If you do get a `401`, the key wasn't saved. Re-run the `cat > ~/.omlx/settings.json` block from §4.3 and then `brew services restart omlx`.

### 4.7 Download & Deploy a Model

1. In the admin dashboard (`http://localhost:8000/admin`), go to the **Models** section
2. Search Hugging Face for MLX models (e.g., `mlx-community/Qwen3.5-4B-8bit`)
3. Click **Download** — watch the progress bar
4. Configure per-model settings (sampling parameters, context length, etc.)
5. Click **Load** to start serving

Verify the model is live:

```bash
curl -s -H "Authorization: Bearer omlx-night-thoughts" http://localhost:8000/v1/models
```

**Expected output:**

```json
{"object":"list","data":[{"id":"mlx-community/Qwen3.5-4B-8bit","object":"model"}]}
```

> **Note:** oMLX provides both OpenAI-compatible (`/v1/chat/completions`) and Anthropic-compatible (`/v1/messages`) endpoints. It also supports `/v1/embeddings`, `/v1/rerank`, and `/v1/responses` for broader compatibility.

![oMLX admin dashboard with a model loaded and serving](https://cdn.hashnode.com/uploads/gql/6a92730f9a9aa7f72e74fdf4/2cf4e346-d538-46b3-9247-bcad2487131a.png)

## Part 5: Install QwenPaw (Agent Framework)

QwenPaw is a local-first AI agent framework that can connect to your oMLX-served models.

### 5.1 Install via One-Line Script

The installer writes a `qwenpaw` wrapper to `~/.qwenpaw/bin/` and adds it to your `PATH` via `~/.zshrc`. Because your current shell session hasn't re-read that file yet, the command needs a `source ~/.zshrc` in between:

```bash
curl -fsSL https://qwenpaw.agentscope.io/install.sh | bash && source ~/.zshrc && qwenpaw init --defaults
```

**Expected output:**

```
[qwenpaw] QwenPaw installed successfully
[qwenpaw] Wrapper created at /Users/<you>/.qwenpaw/bin/qwenpaw
[qwenpaw] Updated /Users/<you>/.zshrc
✅ Configuration initialized at ~/.qwenpaw/config.json
✅ Default model backend configured
```

> **If you already ran the installer and got `command not found: qwenpaw`:** the install itself succeeded — you just need to reload your shell. Run `source ~/.zshrc && qwenpaw init --defaults` and continue.

This script installs QwenPaw into `~/.qwenpaw` with a self-contained `uv`-managed Python environment. It automatically installs `uv`, creates a virtual environment, and downloads dependencies without requiring manual Python setup.

### 5.2 Configure QwenPaw to Use oMLX

Write the QwenPaw config in one command. Note that the `api_key` here **must match** the value you chose in §4.3 (`omlx-night-thoughts` in this guide):

```bash
cat > ~/.qwenpaw/config.json << 'EOF'
{
  "model": {
    "backend": "openai",
    "base_url": "http://localhost:8000/v1",
    "api_key": "omlx-night-thoughts",
    "model_name": "mlx-community/Qwen3.5-4B-8bit"
  }
}
EOF
```

> **Using a different key?** If you chose a different value in §4.3, replace `omlx-night-thoughts` in the `api_key` field above with that same value. The two **must match** — this is the single most common source of `401 Unauthorized` errors.

> **Path note:** `base_url` must include the `/v1` suffix. QwenPaw's OpenAI client appends `/models`, `/chat/completions`, etc. after `base_url`, so a missing `/v1` sends requests to the wrong paths.

### 5.3 Start QwenPaw

```bash
source ~/.zshrc && qwenpaw app
```

**Expected output:**

```
QwenPaw Console running at http://127.0.0.1:8088/
```

Open `http://localhost:8088` to access the QwenPaw web console.

### 5.4 Make QwenPaw Persistent (launchd)

Create a launchd plist so QwenPaw starts automatically on login. This plist does three important things:

1. Starts QwenPaw on login and keeps it running (`RunAtLoad` + `KeepAlive`)
2. Routes launchd's stdout/stderr to `/dev/null` so no unrotated files grow forever
3. Pins QwenPaw's internal log rotation to **2 MiB × 2 backups** via `EnvironmentVariables` so the log directory can never exceed ~6 MiB

The heredoc below is **unquoted** (`<< EOF`, not `<< 'EOF'`), so the shell expands `$HOME` to your actual home directory when the file is written. Copy and paste the whole block in one shot:

```bash
mkdir -p ~/.qwenpaw/logs && cat > ~/Library/LaunchAgents/com.qwenpaw.app.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.qwenpaw.app</string>
  <key>ProgramArguments</key>
  <array>
    <string>$HOME/.qwenpaw/bin/qwenpaw</string>
    <string>app</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>WorkingDirectory</key>
  <string>$HOME</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>QWENPAW_LOG_MAX_SIZE</key>
    <string>2MiB</string>
    <key>QWENPAW_LOG_MAX_BACKUPS</key>
    <string>2</string>
  </dict>
  <key>StandardOutPath</key>
  <string>/dev/null</string>
  <key>StandardErrorPath</key>
  <string>/dev/null</string>
</dict>
</plist>
EOF
```

> **Why these values?** `launchd` writes to `StandardOutPath`/`StandardErrorPath` once and never rotates them, so we route them to `/dev/null`. QwenPaw's own `RotatingFileHandler` writes structured logs to `~/.qwenpaw/qwenpaw.log`, and the two env vars cap it at **2 MiB per file × 2 backups** (≈ 6 MiB total). Worst-case log disk usage is bounded and known.

**Load the launcher** using `launchctl bootstrap` (the modern replacement for the legacy `launchctl load`, which fails with a generic `Input/output error` on Ventura and later):

```bash
launchctl bootout gui/$(id -u)/com.qwenpaw.app 2>/dev/null; launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.qwenpaw.app.plist
```

**Expected output:** No output on success.

Confirm it's running:

```bash
launchctl list | grep qwenpaw
```

**Expected output:**

```
30406	0	com.qwenpaw.app
```

The first column is the PID (a number means it's running), the second is the last exit status (`0` = clean), and the third is the label.

**Useful launcher management commands:**

```bash
launchctl list | grep qwenpaw                                             # check status
launchctl bootout gui/$(id -u)/com.qwenpaw.app                            # stop and unregister
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.qwenpaw.app.plist   # start and register
launchctl kickstart -k gui/$(id -u)/com.qwenpaw.app                       # restart in place
```

> **After editing the plist**, you must `bootout` then `bootstrap` for changes to take effect — launchd caches the plist at load time.

![QwenPaw web console with an agent conversation open](https://cdn.hashnode.com/uploads/gql/6a92730f9a9aa7f72e74fdf4/f3ac7a7b-3fd4-48fd-8e72-b138b735fc34.png)

## Part 6: Verify Everything Survives a Reboot

Restart your Mac:

```bash
sudo reboot
```

After reboot, wait 30 seconds, then SSH in from another machine:

```bash
ssh your-username@your-mac-ip
```

Check all services in one command:

```bash
brew services list | grep omlx && launchctl list | grep qwenpaw && curl -s -H "Authorization: Bearer omlx-night-thoughts" http://localhost:8000/v1/models && curl -s -o /dev/null -w "QwenPaw HTTP %{http_code}\n" http://localhost:8088/
```

**Expected output:**

```
omlx    started    yourname    ~/Library/LaunchAgents/sh.brew.omlx.plist
30406	0	com.qwenpaw.app
{"object":"list","data":[...]}
QwenPaw HTTP 200
```

All three services should return healthy responses without any manual intervention.

## Part 7: Remote Access from Anywhere with a Custom Domain

This part sets up secure HTTPS access to both oMLX and QwenPaw from anywhere in the world, using your **own custom domain** rather than Tailscale's default `.ts.net` hostname. You'll get clean, port-free URLs like:

- `https://omlx.yourdomain.com`
- `https://qwenpaw.yourdomain.com`

The architecture: **Tailscale** provides the encrypted mesh network and provision TLS certificates for your custom domain; **Caddy** runs locally as a reverse proxy to route each subdomain to the correct service.

### 7.0 Create a Tailscale Account

If you don't already have a Tailscale account, sign up first. It's free for personal use and takes about a minute.

1. Go to [tailscale.com](https://tailscale.com/) and click **Get Started** (or go directly to [login.tailscale.com/start](https://login.tailscale.com/start)).
2. Sign up using a **single sign-on (SSO) identity provider** — Google, GitHub, Microsoft, Apple, or a custom email address all work. You do not create a Tailscale-specific password; Tailscale authenticates you through your chosen provider.
3. After signing in, you'll be asked to choose **Business use** or **Personal use**. Pick Personal for a home server setup.
4. You land on the **Admin Console** at [console.tailscale.com/admin](https://console.tailscale.com/admin).

> **Note:** If you sign up with a public email domain (e.g., `@gmail.com`), you're automatically placed on the **Personal** plan, which includes up to **6 free users** and **100 devices**. That's more than enough for this guide.

> **Tip:** The same account must be used on every device you want on your tailnet. If you sign in with Google on your Mac server, sign in with Google on your laptop too — otherwise they won't see each other.

### 7.1 Install Tailscale on Your Mac Server

```bash
brew install --cask tailscale
```

**Expected output:** `tailscale-app was successfully installed!`

Open the Tailscale app from your Applications folder or menu bar, and sign in with the same account you just created.

Once authenticated, the Tailscale icon appears in your menu bar and shows a green "Connected" status.

> **Note:** The `--cask` version installs the GUI app but does **not** add the `tailscale` CLI to your `$PATH`. See §7.1b below to enable it.

### 7.1b Enable the Tailscale CLI

The cask bundles the CLI inside the app binary. **Do not symlink the app binary** — it crashes with `Fatal error: The current bundleIdentifier is unknown to the registry`. Instead, add a shell alias:

```bash
echo 'alias tailscale="/Applications/Tailscale.app/Contents/MacOS/Tailscale"' >> ~/.zshrc && source ~/.zshrc && tailscale status
```

**Expected output:**

```
100.97.7.34    haithemslimis-mac-mini  haythemslimi@  macOS    -
100.88.189.0   night-thoughts         haythemslimi@  macOS    offline, last seen 2d ago
```

If you see your machine list, the CLI is working and you can proceed.

> **Tip:** Your machine name may be long and awkward to type. You can rename it to something memorable like `night-thoughts` in the [admin console](https://console.tailscale.com/admin/machines). The MagicDNS entry updates automatically.

### 7.2 Configure Your Custom Domain in Tailscale

Tailscale can provision TLS certificates for your own domain, but you must first prove ownership by adding DNS records.

**Step 1: Add your domain to Tailscale**

1. Go to the [**DNS page**](https://console.tailscale.com/admin/dns) of the Tailscale admin console.
2. Under **HTTPS Certificates**, ensure **Enable HTTPS** is turned on.
3. In the **Custom domain** section, click **Add domain** and enter your apex domain (e.g., `yourdomain.com`).

**Step 2: Add the DNS records at your registrar**

Tailscale will display two DNS records you need to create at your domain registrar (Cloudflare, Namecheap, Route 53, etc.):

| Type | Name | Value |
|------|------|-------|
| `CNAME` | `_acme-challenge.yourdomain.com` | `<value provided by Tailscale>` |
| `CNAME` | `*.yourdomain.com` | `your-tailnet.ts.net` |

> **Note:** The `*.yourdomain.com` wildcard CNAME points all subdomains (including `omlx.` and `qwenpaw.`) to your tailnet. The `_acme-challenge` record is used by Tailscale to prove you own the domain and provision Let's Encrypt certificates.

Add these records at your registrar, then wait a few minutes for DNS propagation. Verify with:

```bash
dig +short _acme-challenge.yourdomain.com CNAME
```

**Expected output:** The value provided by Tailscale.

**Step 3: Verify the domain is active**

In the Tailscale admin console, the custom domain should now show as **Verified**. Tailscale will automatically provision and renew TLS certificates for `*.yourdomain.com` using Let's Encrypt.

### 7.3 Install Caddy

Caddy is a lightweight reverse proxy that will route each subdomain to the correct local service.

```bash
brew install caddy
```

**Expected output:** `caddy was successfully installed!`

Verify:

```bash
caddy version
```

**Expected output:** `v2.x.x`

### 7.4 Configure Caddy for Subdomain Routing

Create a Caddyfile that routes `omlx.yourdomain.com` to oMLX and `qwenpaw.yourdomain.com` to QwenPaw.

Write the configuration in one command (replace `yourdomain.com` with your actual domain):

```bash
sudo mkdir -p /opt/homebrew/etc && sudo tee /opt/homebrew/etc/Caddyfile > /dev/null << 'EOF'
omlx.yourdomain.com {
    reverse_proxy localhost:8000
}

qwenpaw.yourdomain.com {
    reverse_proxy localhost:8088
}
EOF
```

> **Important:** Replace `yourdomain.com` in both blocks with your actual domain. This is the domain you added to Tailscale in §7.2.

Verify the Caddyfile syntax:

```bash
caddy validate --config /opt/homebrew/etc/Caddyfile
```

**Expected output:** `Valid configuration`

### 7.5 Start Caddy as an Always-On Service

Register Caddy with `brew services` so it auto-starts on login:

```bash
brew services start caddy
```

**Expected output:** `==> Successfully started 'caddy' (label: homebrew.mxcl.caddy)`

Verify it's running:

```bash
brew services list | grep caddy
```

**Expected output:**

```
caddy    started    yourname    ~/Library/LaunchAgents/homebrew.mxcl.caddy.plist
```

Caddy is now listening on ports 80 and 443 locally, ready to receive traffic from Tailscale.

> **Note:** Caddy does **not** need to terminate TLS — Tailscale handles that. Caddy simply receives plain HTTP from Tailscale's local proxy and routes based on the `Host` header.

### 7.6 Point Tailscale Serve at Caddy

Now tell Tailscale to forward all HTTPS traffic on port 443 to Caddy, which will route based on hostname.

First, clear any existing serve configuration:

```bash
tailscale serve reset
```

Then set up the proxy to Caddy:

```bash
tailscale serve --bg --https=443 http://localhost:2019
```

> **Note:** Caddy's admin API listens on port 2019 by default. However, for serving regular HTTP traffic, Caddy listens on port 80. Use `http://localhost:80` instead if you want to route through Caddy's main HTTP listener:
> ```bash
> tailscale serve --bg --https=443 http://localhost:80
> ```

Verify the serve configuration:

```bash
tailscale serve status
```

**Expected output:**

```
https://yourdomain.com
|-- / proxy http://localhost:80
```

Tailscale is now terminating TLS for `*.yourdomain.com` and forwarding all requests to Caddy, which routes them to oMLX or QwenPaw based on the subdomain.

### 7.7 Access Your Services

From any device on your tailnet, open:

- **oMLX admin dashboard:** `https://omlx.yourdomain.com/admin`
- **QwenPaw web console:** `https://qwenpaw.yourdomain.com`

No ports. No path prefixes. Clean HTTPS URLs with valid certificates.

> **Note:** You must be signed into Tailscale on the client device. These URLs are only reachable from within your tailnet — the public internet cannot reach them.

### 7.8 Authentication Layer

Tailscale handles network-level access control — only devices on your tailnet can connect. However, both services still have their own authentication:

| Service | Authentication |
|---------|----------------|
| **oMLX** | Your `omlx-night-thoughts` API key (set in §4.3) |
| **QwenPaw** | Console login (if enabled) |

For oMLX, the API key protects the `/v1/*` endpoints. The admin dashboard at `/admin` may prompt for a session login on first visit.

For QwenPaw, if you want to require authentication when accessing from outside, set the following environment variables in the launchd plist (§5.4):

```xml
<key>EnvironmentVariables</key>
<dict>
  <key>QWENPAW_AUTH_ENABLED</key>
  <string>true</string>
  <key>QWENPAW_AUTH_USERNAME</key>
  <string>your-username</string>
  <key>QWENPAW_AUTH_PASSWORD</key>
  <string>your-password</string>
</dict>
```

Then reload the plist as shown in §5.4.

### 7.9 Verify Everything Survives Reboot

Restart your Mac:

```bash
sudo reboot
```

After reboot, wait 30 seconds, then verify all services:

```bash
brew services list | grep -E "omlx|caddy" && launchctl list | grep qwenpaw && tailscale serve status
```

**Expected output:**

```
omlx    started    yourname    ~/Library/LaunchAgents/sh.brew.omlx.plist
caddy   started    yourname    ~/Library/LaunchAgents/homebrew.mxcl.caddy.plist
-   0   com.qwenpaw.app
https://yourdomain.com
|-- / proxy http://localhost:80
```

All services should return healthy responses without any manual intervention.

### 7.10 Troubleshooting

| Symptom | Fix |
|---------|-----|
| `omlx.yourdomain.com` returns 404 | Verify Caddy is running (`brew services list \| grep caddy`) and the Caddyfile has the correct subdomain blocks. Check `caddy validate --config /opt/homebrew/etc/Caddyfile`. |
| Certificate error on custom domain | Verify the `_acme-challenge` and wildcard CNAME records are correctly set at your registrar. Wait 5–10 minutes for DNS propagation, then check Tailscale admin console for domain verification status. |
| `tailscale serve status` shows no configuration | Run `tailscale serve --bg --https=443 http://localhost:80` again. Ensure HTTPS certificates are enabled in the Tailscale admin console. |
| Caddy won't start | Check for port conflicts on 80 or 443: `sudo lsof -i :80` and `sudo lsof -i :443`. Stop any conflicting service (e.g., a local web server) before starting Caddy. |
| Custom domain shows "not verified" in Tailscale | DNS records haven't propagated yet. Run `dig +short _acme-challenge.yourdomain.com CNAME` to check. If empty, wait and retry. |

## Troubleshooting Quick Reference

| Symptom | Fix |
|---------|-----|
| `systemsetup: Turning Remote Login on or off requires Full Disk Access privileges` | Grant Terminal Full Disk Access in System Settings → Privacy & Security → Full Disk Access, then **quit and reopen Terminal** |
| `pmset -g` shows `SleepDisabled 1` instead of `disablesleep 1` | Normal on macOS Ventura+. Same setting, different label |
| `sleep 0 (sleep prevented by powerd, bluetoothd)` | Informational, not an error. Sleep is disabled as intended |
| `brew: command not found` | Run `eval "$(/opt/homebrew/bin/brew shellenv)"` or add it to `~/.zprofile` as shown in §4.1 |
| `Error: Refusing to load formula ... from untrusted tap` | Run `brew trust jundot/omlx`, then retry `brew install jundot/omlx/omlx` |
| oMLX install rejected on Intel Mac or macOS 14 | oMLX requires Apple Silicon (M1/M2/M3/M4) and macOS 15.0 (Sequoia) or later |
| `AttributeError: module 'mlx' has no attribute '__version__'` | Expected — version lives on `mlx.core`. Use `python -c "import mlx.core as mx; print(mx.__version__)"` |
| oMLX isn't running after reboot | Run `brew services list` — status should be `started` |
| Admin dashboard shows 404 at `localhost:8000` | The correct path is `/admin`, not `/`. Use `http://localhost:8000/admin` |
| `401 Unauthorized` from oMLX | The `api_key` in QwenPaw's config doesn't match the key in `~/.omlx/settings.json`. Both must be **exactly** the same string |
| `{"detail":"API key required"}` from curl | You forgot the `Authorization: Bearer <key>` header |
| `{"object":"list","data":[]}` from `/v1/models` | This is correct — no model is loaded yet. Download and load one via the admin dashboard |
| Forgot the oMLX API key | Read it back with `cat ~/.omlx/settings.json \| grep api_key` |
| `command not found: qwenpaw` after install | Run `source ~/.zshrc` (or open a new terminal) to reload your PATH, then retry |
| `launchctl load` fails with `Load failed: 5: Input/output error` | Use `launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.qwenpaw.app.plist` instead of the legacy `load` command |
| `tailscale: command not found` after cask install | Add the alias: `echo 'alias tailscale="/Applications/Tailscale.app/Contents/MacOS/Tailscale"' >> ~/.zshrc && source ~/.zshrc` |
| `Fatal error: The current bundleIdentifier is unknown to the registry` | You symlinked the Tailscale app binary. Remove the symlink and use the shell alias instead |
| Tailscale SSH denies access (`access denied`) with `"action": "accept"` | Switch to `"action": "check"` and use `"src": ["autogroup:member"]`. See §7.6 for the full working ACL |
| Services don't start after reboot | Verify auto-login is enabled; check FileVault is OFF |
| `omlx` not found | Run `eval "$(/opt/homebrew/bin/brew shellenv)"` and retry |
| QwenPaw can't reach oMLX | Confirm oMLX is running: `curl -H "Authorization: Bearer omlx-night-thoughts" http://localhost:8000/v1/models`. Also ensure `base_url` in QwenPaw config includes `/v1` |
| Out of memory errors | Use smaller quantized models (4-bit); reduce context window per-model in oMLX admin settings |
| Port conflicts | Change oMLX port via `OMLX_PORT` env var or `omlx serve --port <port>` |
| Custom domain not resolving | Verify DNS records are set at your registrar. Check Tailscale admin console for domain verification status. See §7.10 |
| Caddy not routing correctly | Check `caddy validate --config /opt/homebrew/etc/Caddyfile`. Ensure subdomain blocks match your Tailscale custom domain. |
| Tailscale Serve not working | Run `tailscale serve status` to check active configurations |