---
title: "Complete Guide: Always-On Mac Server with MLX, oMLX & QwenPaw"
datePublished: 2026-10-09T21:01:08.387Z
cuid: cmv1g9zeh000006qb05op2muw
slug: complete-guide-always-on-mac-server-with-mlx-omlx-qwenpaw
cover: https://cdn.hashnode.com/uploads/covers/6a92730f9a9aa7f72e74fdf4/040513aa-a14f-4cc7-9b62-45d63fc9e230.jpg
tags: ai, mlx, macmini, qwenpaw

---

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
git clone https://github.com/thairc-dev/mac-server-mode.git
cd mac-server-mode
./build.sh
nohup ./mac-server-mode >/dev/null 2>&1 &
./install-launch-agent.sh
```

A ⚡ icon appears in your menu bar. Press `Ctrl + Option + Cmd + S` to toggle server mode (screen off, system awake).

## Part 2: Install uv & Python 3.11

### 2.1 Install uv

`uv` is a fast, all-in-one Python package and version manager written in Rust. Install it via the official one-liner:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Expected output:** Installation progress bars, then a success message.

After installation, restart your shell or source your profile:

```bash
source ~/.zshrc
```

Verify:

```bash
uv --version
```

**Expected output:** `uv 0.x.x`

### 2.2 Install Python 3.11 with uv

Install Python 3.11 as a uv-managed Python:

```bash
uv python install 3.11
```

**Expected output:** Download progress, then `Installed Python 3.11.x`

Verify:

```bash
uv python list | grep 3.11
```

**Expected output:** Shows the installed Python 3.11 version.

### 2.3 Create a Virtual Environment for MLX

Create a dedicated virtual environment using Python 3.11:

```bash
uv venv --python 3.11 ~/.mlx-venv
```

Activate it:

```bash
source ~/.mlx-venv/bin/activate
```

Verify the Python version inside the venv:

```bash
python --version
```

**Expected output:** `Python 3.11.x`

> **Critical:** Ensure you are NOT using a Rosetta (x86) Python. Run this check:
> ```bash
> python -c "import platform; print(platform.processor())"
> ```
> **Expected output:** `arm` — if you see `i386`, you have the wrong Python.

## Part 3: Install MLX Framework

MLX is Apple's native machine learning framework for Apple Silicon.

With your virtual environment activated:

```bash
uv pip install mlx mlx-lm
```

**Expected output:** `Successfully installed mlx-x.x.x mlx-lm-x.x.x ...`

Verify:

```bash
python -c "import mlx.core as mx; print(mx.__version__)"
```

**Expected output:** `0.32.x`

> **Note:** The top-level `mlx` module does **not** export `__version__`. If you try `python -c "import mlx; print(mlx.__version__)"`, you'll get `AttributeError: module 'mlx' has no attribute '__version__'`. The version attribute lives on `mlx.core`. Alternatively, you can read the version from package metadata:
> ```bash
> python -c "import importlib.metadata as md; print(md.version('mlx'))"
> ```

## Part 4: Install oMLX (Web Dashboard + Background Service)

oMLX is an LLM inference server optimized for Apple Silicon, built on the MLX framework. It provides continuous batching, tiered KV caching (hot in-memory + cold SSD), and a web-based admin dashboard for managing models. It is actively maintained (v0.6.4 as of September 2026) and ships as a Homebrew formula with native launchd service integration[reference:0].

> **Note:** oMLX is a community project maintained by `jundot`. It is built directly on top of Apple's MLX framework (which *is* official). Unlike mlx-manager, oMLX is actively maintained and has a much larger user base (22k+ stars)[reference:1].

It is distributed via a Homebrew tap, so we need to install Homebrew first.

### 4.1 Install Homebrew

Homebrew is the missing package manager for macOS. Install it with the official one-liner:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

**Expected output:** Installation progress messages, followed by:

```
==> Installation successful!

==> Homebrew has enabled anonymous aggregate formulae and cask analytics.
...
==> Next steps:
- Run these commands in your terminal to add Homebrew to your PATH:
    echo >> ~/.zprofile
    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
    eval "$(/opt/homebrew/bin/brew shellenv)"
```

Follow the printed **Next steps** to add Homebrew to your `PATH` (Apple Silicon uses `/opt/homebrew`; Intel uses `/usr/local`):

```bash
echo >> ~/.zprofile
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

Verify:

```bash
brew --version
```

**Expected output:** `Homebrew 4.x.x`

> **Note:** If Homebrew is already installed, this command will detect it and skip installation. You can safely run it again.

### 4.2 Tap and Trust the oMLX Repository

```bash
brew tap jundot/omlx https://github.com/jundot/omlx
```

**Expected output:**

```
==> Tapping jundot/omlx
Cloning into '/opt/homebrew/Library/Taps/jundot/homebrew-omlx'...
Tapped 1 formula (xxx files, x.xMB).
```

Now **trust the tap**. Recent versions of Homebrew refuse to load formulas from third-party taps unless you explicitly trust them — this is a security feature to prevent arbitrary code execution from untrusted sources[reference:2]:

```bash
brew trust jundot/omlx
```

**Expected output:** A confirmation message listing the tap as trusted.

> **Why is this needed?** If you run `brew install omlx` without trusting the tap first, you'll see:
>
> ```
> Error: Refusing to load formula jundot/omlx/omlx from untrusted tap jundot/omlx.
> Run `brew trust --formula jundot/omlx/omlx` or `brew trust jundot/omlx` to trust it.
> ```
>
> That error is safe to resolve with `brew trust` as long as you've reviewed the tap source.

### 4.3 Install oMLX via Homebrew

```bash
brew install jundot/omlx/omlx
```

**Expected output:** `/opt/homebrew/Cellar/omlx/x.x.x: ...`

> **Platform requirement:** The oMLX formula requires **Apple Silicon** and **macOS 15.0 (Sequoia) or later**. An Intel Mac or macOS 14 machine is rejected during installation[reference:3].

### 4.4 Start the Web Dashboard (Foreground, for First-Time Setup)

For the very first run, start it in the foreground so you can see logs and complete the initial setup:

```bash
omlx serve --model-dir ~/models
```

**Expected output:**

```
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Open `http://localhost:8000/admin` in your browser (or `http://your-mac-ip:8000/admin` from another device). The admin dashboard requires session-based authentication on first visit[reference:4].

> **Note:** oMLX automatically discovers LLMs, VLMs, embedding models, and rerankers from subdirectories of your model directory[reference:5].

### 4.5 Create Your Account

On first visit to `/admin`, you'll be prompted to set up authentication. Create your credentials and log in.

### 4.6 Run oMLX as an Always-On Background Service

This is the key step for always-on operation. Stop the foreground server first (`Ctrl+C`), then register oMLX with `brew services`, which installs a launchd agent that auto-starts on login and restarts on crash:

```bash
brew services start omlx
```

**Expected output:**

```
==> Successfully started `omlx` (label: homebrew.mxcl.omlx)
```

Verify it's running:

```bash
brew services list
```

**Expected output:**

```
Name    Status  User      File
omlx    started yourname  ~/Library/LaunchAgents/homebrew.mxcl.omlx.plist
```

The `Status` should be `started`. `brew services` writes the launchd plist automatically — no manual plist creation needed[reference:6].

> **Note:** The service runs `omlx serve` with zero-config defaults (`~/.omlx/models`, port 8000). To customize the model directory or port, either set environment variables (`OMLX_MODEL_DIR`, `OMLX_PORT`) or run `omlx serve --model-dir /your/path` once to persist settings to `~/.omlx/settings.json`[reference:7].

**Useful `brew services` commands:**

```bash
brew services stop omlx      # stop the service
brew services restart omlx   # restart the service
brew services info omlx      # show detailed status
```

### 4.7 Download & Deploy a Model

1. In the admin dashboard (`http://localhost:8000/admin`), go to the **Models** section
2. Search for MLX models on Hugging Face (e.g., `mlx-community/Qwen3.5-4B-8bit`)
3. Click **Download** — watch the progress bar
4. Configure per-model settings (sampling parameters, context length, etc.)
5. Click **Load** to start serving

Once running, the model's OpenAI-compatible API endpoint is available at:

```
http://localhost:8000/v1
```

Test it:

```bash
curl http://localhost:8000/v1/models
```

**Expected output:**

```json
{"object":"list","data":[{"id":"mlx-community/Qwen3.5-4B-8bit","object":"model"}]}
```

> **Note:** oMLX provides both OpenAI-compatible (`/v1/chat/completions`) and Anthropic-compatible (`/v1/messages`) API endpoints. It also supports `/v1/embeddings`, `/v1/rerank`, and `/v1/responses` for broader compatibility[reference:8].

## Part 5: Install QwenPaw (Agent Framework)

QwenPaw is a local-first AI agent framework that can connect to your oMLX-served models.

### 5.1 Install via One-Line Script

```bash
curl -fsSL https://qwenpaw.agentscope.io/install.sh | bash
```

**Expected output:**

```
✅ QwenPaw installed successfully to ~/.qwenpaw
✅ uv Python environment created
Run `qwenpaw init --defaults` to configure.
```

This script installs QwenPaw into `~/.qwenpaw` with a self-contained `uv`-managed Python environment. It automatically installs `uv`, creates a virtual environment, and downloads dependencies without requiring manual Python setup.

### 5.2 Initialize QwenPaw

```bash
qwenpaw init --defaults
```

**Expected output:**

```
✅ Configuration initialized at ~/.qwenpaw/config.json
✅ Default model backend configured
```

### 5.3 Configure QwenPaw to Use oMLX

Edit the QwenPaw config to point to your oMLX API:

```bash
vim ~/.qwenpaw/config.json
```

Find the `model` section and set:

```json
{
  "model": {
    "backend": "openai",
    "base_url": "http://localhost:8000/v1",
    "api_key": "not-needed",
    "model_name": "mlx-community/Qwen3.5-4B-8bit"
  }
}
```

> **Important:** When adding oMLX as a custom OpenAI-compatible provider in QwenPaw, you must manually set `support_model_discovery: true` and `support_connection_check: true` in the provider JSON. Also ensure `base_url` includes the `/v1` suffix — QwenPaw's OpenAI client appends `/models` etc. after `base_url`, so a missing `/v1` causes requests to the wrong paths[reference:9].

### 5.4 Start QwenPaw

```bash
qwenpaw app
```

**Expected output:**

```
QwenPaw Console running at http://127.0.0.1:8088/
```

Open `http://localhost:8088` to access the QwenPaw web console.

### 5.5 Make QwenPaw Persistent (launchd)

Create a launchd plist so QwenPaw starts automatically on login. The heredoc below is **unquoted** (`<< EOF`, not `<< 'EOF'`), so the shell expands `$HOME` to your actual home directory when the file is written:

```bash
mkdir -p ~/.qwenpaw/logs

cat > ~/Library/LaunchAgents/com.qwenpaw.app.plist << EOF
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
  <key>StandardOutPath</key>
  <string>$HOME/.qwenpaw/logs/qwenpaw.log</string>
  <key>StandardErrorPath</key>
  <string>$HOME/.qwenpaw/logs/qwenpaw.error.log</string>
</dict>
</plist>
EOF
```

Verify the paths resolved correctly (they should show your real username, not `$HOME`):

```bash
grep -A1 ProgramArguments ~/Library/LaunchAgents/com.qwenpaw.app.plist
```

**Expected output:** The `<string>` lines should contain e.g. `/Users/yourname/.qwenpaw/bin/qwenpaw`.

Load it:

```bash
launchctl load ~/Library/LaunchAgents/com.qwenpaw.app.plist
```

Verify:

```bash
launchctl list | grep qwenpaw
```

**Expected output:** `- 0 com.qwenpaw.app`

## Part 6: Verify Everything Survives a Reboot

Restart your Mac:

```bash
sudo reboot
```

After reboot, wait 30 seconds, then SSH in from another machine:

```bash
ssh your-username@your-mac-ip
```

Check all services:

```bash
# oMLX (should be "started")
brew services list | grep omlx

# QwenPaw
launchctl list | grep qwenpaw

# oMLX admin dashboard
curl -s http://localhost:8000/admin

# QwenPaw console
curl -s http://localhost:8088/
```

All should return healthy responses without any manual intervention.

## Part 7: Remote Access from Anywhere with Tailscale & MagicDNS

Tailscale creates a secure mesh VPN between your devices, giving each one a stable private IP address that works from any network — even behind CGNAT or corporate firewalls, with no port forwarding required.

**MagicDNS** is Tailscale's built-in DNS feature that lets you reach your server by its machine name (e.g., `my-mac`) instead of remembering IP addresses. This section sets up MagicDNS as the primary access method for all your services.

### 7.1 Install Tailscale on Your Mac Server

```bash
brew install --cask tailscale
```

**Expected output:** `tailscale was successfully installed!`

Open the Tailscale app from your Applications folder or menu bar, and sign in with Google, GitHub, Microsoft, or email.

Once authenticated, the Tailscale icon appears in your menu bar and shows a green "Connected" status.

> **Note:** The `--cask` version provides the GUI app and includes the `tailscale` CLI command automatically. For a headless server setup, this is the recommended approach.

### 7.2 Install Tailscale on Your Client Device

Install Tailscale on any device you'll use to connect — your laptop, phone, or tablet:

- **macOS:** `brew install --cask tailscale` or download from the Mac App Store
- **Windows:** Download the installer from [tailscale.com/download](https://tailscale.com/download)
- **Linux:** `curl -fsSL https://tailscale.com/install.sh | sh && sudo tailscale up`
- **iOS/Android:** Download from the App Store or Play Store

**Critical:** Sign in with the **same account** on every device. All devices must belong to the same "tailnet" (your private Tailscale network) to see each other.

### 7.3 Enable MagicDNS and HTTPS Certificates (One-Time Setup)

MagicDNS and HTTPS Certificates are required for secure, name-based access to your services.

1. Go to the [**DNS page**](https://console.tailscale.com/admin/dns) of the Tailscale admin console.
2. Ensure **MagicDNS** is enabled. Tailnets created on or after October 20, 2022 have MagicDNS enabled by default.
3. Under the **HTTPS Certificates** section, click **Enable HTTPS**. This allows Tailscale to automatically provision TLS certificates for your devices.

> **Important:** Enabling HTTPS certificates publishes your machine names and tailnet DNS name on a public ledger (Certificate Transparency). If your machine names contain sensitive information, rename them before enabling HTTPS.

### 7.4 Find Your MagicDNS Name

Once MagicDNS is enabled, you can reach your Mac server by its machine name. There are two ways to find the name:

**Method 1 — Menu Bar (Easiest):** Click the Tailscale icon in your Mac's menu bar. Your machine name appears under "This Device".

**Method 2 — Terminal:**

```bash
tailscale status
```

**Expected output:**

```
100.101.102.10   my-mac        your-email@example.com  macOS  -
100.101.102.11   my-laptop     your-email@example.com  macOS  -
```

Your MagicDNS name is the second column (e.g., `my-mac`).

**Method 3 — Admin Console:** Go to [console.tailscale.com/admin/machines](https://console.tailscale.com/admin/machines), find your Mac in the list, and copy the machine name.

> **Tip:** You can rename your device to something memorable (like `ai-server`) by editing the machine name in the admin console. The MagicDNS entry will update automatically.

### 7.5 Verify MagicDNS Resolution

From your client device (e.g., your laptop), test that MagicDNS resolves the machine name:

```bash
ping my-mac
```

**Expected output:**

```
PING my-mac (100.101.102.10): 56 data bytes
64 bytes from 100.101.102.10: icmp_seq=0 ttl=64 time=12.3 ms
```

If you get a response, MagicDNS is working. Press `Ctrl+C` to stop.

> **Note:** Some CLI tools on macOS like `host` or `nslookup` bypass system DNS resolution and will not work with MagicDNS. Use `ping` or `curl` instead.

### 7.6 SSH into Your Mac Server Using MagicDNS

Once MagicDNS is working, SSH becomes much simpler — no more remembering IP addresses:

```bash
ssh your-username@my-mac
```

**Expected output:**

```
The authenticity of host 'my-mac (100.101.102.10)' can't be established.
ED25519 key fingerprint is SHA256:...
Are you sure you want to continue connecting (yes/no)?
```

Type `yes` and enter your Mac's login password. You are now remotely connected to your always-on AI server from any network in the world, using a human-readable name.

> **Tip:** For shared devices, you must use the full domain name: `ssh your-username@my-mac.your-tailnet.ts.net`.

### 7.7 Optional — Enable Tailscale SSH (Passwordless)

Tailscale SSH lets you authenticate using your Tailscale identity instead of your macOS password. This is useful for automation and scripting.

On your Mac server, run:

```bash
tailscale set --ssh
```

**Expected output:** No output (success).

Verify with:

```bash
tailscale status --json | grep -i ssh
```

**Expected output:** `"ssh": true`

Now when you SSH from another Tailscale device, Tailscale handles authentication automatically:

```bash
ssh your-username@my-mac
```

> **Important:** Tailscale SSH requires you to configure an access control policy. Go to [console.tailscale.com/admin/acls](https://console.tailscale.com/admin/acls) and add:
> ```json
> "ssh": [
>   {
>     "action": "accept",
>     "src": ["your-tailscale-username"],
>     "dst": ["autogroup:self"],
>     "users": ["autogroup:nonroot"]
>   }
> ]
> ```
> This allows devices you own to SSH into each other without a password.

### 7.8 Secure Remote Access to Web UIs with HTTPS via MagicDNS

Your oMLX admin dashboard (port 8000) and QwenPaw (port 8088) web interfaces can be accessed securely over HTTPS using Tailscale Serve. This provides a valid TLS certificate automatically and encrypts all traffic.

**With MagicDNS enabled, you access these services by name instead of IP.** Tailscale Serve keeps your web UIs bound to localhost while giving your tailnet an HTTPS MagicDNS hostname.

**Exposing your web UIs:**

Run these commands on your Mac server:

```bash
tailscale serve --bg --https=443 http://localhost:8000
tailscale serve --bg --https=443 http://localhost:8088
```

**Expected output:**

```
Available within your tailnet:
https://my-mac.your-tailnet.ts.net/
|-- proxy http://localhost:8000
```

Tailscale will print the HTTPS MagicDNS URL for your services.

**Accessing your services using MagicDNS:**

Open the HTTPS URL provided by Tailscale in your browser from any device on your tailnet:

```
https://my-mac.your-tailnet.ts.net (for oMLX admin dashboard)
https://my-mac.your-tailnet.ts.net (for QwenPaw)
```

Your connection will be fully encrypted, and the browser will show a valid HTTPS certificate (padlock icon). No port forwarding, no firewall changes, and no certificate warnings.

**Verify the configuration:**

```bash
tailscale serve status
```

**Expected output:**

```
https://my-mac.your-tailnet.ts.net
|-- / proxy http://localhost:8000
|-- / proxy http://localhost:8088
```

> **Note:** If you need to serve on a different port (e.g., 8443), use `--https=8443` instead. The MagicDNS URL will include the port number.

### 7.9 Optional — Public Access with Tailscale Funnel

If you need to share your services with someone outside your tailnet (e.g., a client reviewing a prototype), Tailscale Funnel exposes a local port to the public internet over a stable HTTPS URL — without port forwarding, DNS records, or a public IP address.

**Enabling Funnel:**

1. Go to the [**DNS page**](https://console.tailscale.com/admin/dns) of the admin console.
2. Ensure **MagicDNS** and **HTTPS Certificates** are enabled (both are required for Funnel).
3. Under the **Funnel** section, turn on Funnel. You need to be an Owner, Admin, or Network admin.

**Exposing a service publicly:**

```bash
tailscale funnel 8000
```

**Expected output:**

```
Available on the internet:
https://my-mac.your-tailnet.ts.net/
|-- proxy http://127.0.0.1:8000
```

> **Warning:** Funnel exposes your service to the public internet. Anyone with the URL can access it. Do not use Funnel for services containing sensitive data. Always enable password authentication for any service exposed via Funnel.

To stop public access:

```bash
tailscale funnel --terminate-on 8000
```

### 7.10 Verify Tailscale Survives Reboot

Tailscale runs as a system extension and automatically reconnects on reboot. After restarting your Mac, verify from your client device:

```bash
ping my-mac
```

If the ping succeeds, Tailscale and MagicDNS are active and your server is reachable by name.

## Troubleshooting Quick Reference

| Symptom | Fix |
|---------|-----|
| `systemsetup: Turning Remote Login on or off requires Full Disk Access privileges` | Grant Terminal Full Disk Access in System Settings → Privacy & Security → Full Disk Access, then **quit and reopen Terminal** |
| `pmset -g` shows `SleepDisabled 1` instead of `disablesleep 1` | Normal on macOS Ventura+. Same setting, different label |
| `sleep 0 (sleep prevented by powerd, bluetoothd)` | Informational, not an error. Sleep is disabled as intended |
| `brew: command not found` | Run `eval "$(/opt/homebrew/bin/brew shellenv)"` or add it to `~/.zprofile` as shown in §4.1 |
| `Error: Refusing to load formula ... from untrusted tap` | Run `brew trust jundot/omlx`, then retry `brew install jundot/omlx/omlx` |
| oMLX install rejected on Intel Mac or macOS 14 | oMLX requires Apple Silicon (M1/M2/M3/M4) and macOS 15.0 (Sequoia) or later[reference:10] |
| `AttributeError: module 'mlx' has no attribute '__version__'` | Expected — version lives on `mlx.core`. Use `python -c "import mlx.core as mx; print(mx.__version__)"` or `python -c "import importlib.metadata as md; print(md.version('mlx'))"` |
| oMLX isn't running after reboot | Run `brew services list` — status should be `started`. If it says `error`, check `$(brew --prefix)/var/log/omlx.log` |
| Admin dashboard shows 404 at `localhost:8000` | The correct path is `/admin`, not `/`. Use `http://localhost:8000/admin` |
| Services don't start after reboot | Verify auto-login is enabled; check FileVault is OFF |
| `omlx` not found | Run `eval "$(/opt/homebrew/bin/brew shellenv)"` and retry |
| QwenPaw can't reach oMLX | Confirm oMLX is running: `curl http://localhost:8000/v1/models`. Also ensure `base_url` in QwenPaw config includes `/v1`[reference:11] |
| QwenPaw custom provider shows no models | Manually set `support_model_discovery: true` and `support_connection_check: true` in the provider JSON, then restart QwenPaw[reference:12] |
| Out of memory errors | Use smaller quantized models (4-bit); reduce context window per-model in oMLX admin settings |
| Port conflicts | Change oMLX port via `OMLX_PORT` env var or `omlx serve --port <port>` |
| MagicDNS name doesn't resolve | Verify MagicDNS is enabled in the Tailscale admin console under DNS settings; check Tailscale is running on both devices |
| `ts.net` URL doesn't resolve | MagicDNS may be off for that resolver; enable it, or use `curl --resolve :443:` |
| SSH over Tailscale times out | Verify Remote Login is enabled (`sudo systemsetup -getremotelogin`); check Tailscale SSH policy in admin console |
| HTTPS URL gives certificate error | Verify HTTPS Certificates are enabled in the Tailscale admin console under DNS settings |
| Tailscale Serve not working | Run `tailscale serve status` to check active configurations; ensure the target services are running locally |
| Funnel URL not accessible | Verify Funnel is enabled in the admin console; check your ACL policy allows Funnel; ensure HTTPS certificates are enabled |