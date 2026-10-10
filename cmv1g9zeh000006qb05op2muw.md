---
title: "Complete Guide: Always-On Mac Server with MLX, MLX Manager & QwenPaw"
datePublished: 2026-10-09T21:01:08.387Z
cuid: cmv1g9zeh000006qb05op2muw
slug: complete-guide-always-on-mac-server-with-mlx-mlx-manager-qwenpaw
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
Currently in use:
 hibernatemode        0
 powernap             0
 displaysleep         0
 sleep                0
 disablesleep         1
```

### 1.2 Enable SSH (Remote Login)

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

MLX Manager requires Python 3.11 or 3.12. Install Python 3.11 as a uv-managed Python:

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
python -c "import mlx; print(mlx.__version__)"
```

**Expected output:** `0.x.x`

## Part 4: Install MLX Manager (Web UI + Background Service)

MLX Manager provides a browser-based interface for downloading MLX models from Hugging Face and running them as persistent services.

### 4.1 Install

```bash
brew tap tumma72/mlx-manager https://github.com/tumma72/mlx-manager
brew install mlx-manager
```

**Expected output:** `/opt/homebrew/Cellar/mlx-manager/x.x.x: ...`

### 4.2 Start the Web UI

```bash
mlx-manager serve
```

**Expected output:**

```
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080
```

Open `http://localhost:8080` in your browser (or `http://your-mac-ip:8080` from another device).

### 4.3 Create Your Account

On first visit, you'll see a registration page. The **first user automatically becomes admin**. Create your account and log in.

### 4.4 Install as Persistent launchd Service

This is the key step for always-on operation. Stop the foreground server first (`Ctrl+C`), then:

```bash
mlx-manager install-service
```

**Expected output:**

```
✅ launchd service installed: com.mlx-manager.server
Service will auto-start on login.
Use `mlx-manager status` to check.
```

Verify it's running:

```bash
mlx-manager status
```

**Expected output:** Shows the service as `running` with a PID.

### 4.5 Download & Deploy a Model

1. In the web UI, click **Browse** to search Hugging Face for MLX models (e.g., `mlx-community/Qwen3.5-4B-8bit`)
2. Click **Download** — watch the progress bar
3. Click **Configure** to create a server profile (GPU layers, context length, etc.)
4. Click **Run** to start serving

Once running, the model is available at:

```
http://localhost:10242/v1
```

Test it:

```bash
curl http://localhost:10242/v1/models
```

**Expected output:**

```json
{"object":"list","data":[{"id":"mlx-community/Qwen3.5-4B-8bit","object":"model"}]}
```

## Part 5: Install QwenPaw (Agent Framework)

QwenPaw is a local-first AI agent framework that can connect to your MLX-served models.

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

### 5.3 Configure QwenPaw to Use MLX Manager

Edit the QwenPaw config to point to your MLX Manager API:

```bash
vim ~/.qwenpaw/config.json
```

In vim, press `i` to enter insert mode, make your changes, then press `Esc` and type `:wq` to save and exit.

Find the `model` section and set:

```json
{
  "model": {
    "backend": "openai",
    "base_url": "http://localhost:10242/v1",
    "api_key": "not-needed",
    "model_name": "mlx-community/Qwen3.5-4B-8bit"
  }
}
```

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

Create a launchd plist so QwenPaw starts automatically on login:

```bash
cat > ~/Library/LaunchAgents/com.qwenpaw.app.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.qwenpaw.app</string>
  <key>ProgramArguments</key>
  <array>
    <string>/Users/YOUR_USERNAME/.qwenpaw/bin/qwenpaw</string>
    <string>app</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>WorkingDirectory</key>
  <string>/Users/YOUR_USERNAME</string>
  <key>StandardOutPath</key>
  <string>/Users/YOUR_USERNAME/.qwenpaw/logs/qwenpaw.log</string>
  <key>StandardErrorPath</key>
  <string>/Users/YOUR_USERNAME/.qwenpaw/logs/qwenpaw.error.log</string>
</dict>
</plist>
EOF
```

Replace `YOUR_USERNAME` with your actual macOS username (`whoami` to check).

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
# MLX Manager
mlx-manager status

# QwenPaw
launchctl list | grep qwenpaw

# MLX Manager web UI
curl -s http://localhost:8080/health

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

Your MLX Manager (port 8080) and QwenPaw (port 8088) web interfaces can be accessed securely over HTTPS using Tailscale Serve. This provides a valid TLS certificate automatically and encrypts all traffic.

**With MagicDNS enabled, you access these services by name instead of IP.** Tailscale Serve keeps your web UIs bound to localhost while giving your tailnet an HTTPS MagicDNS hostname.

**Exposing your web UIs:**

Run these commands on your Mac server:

```bash
tailscale serve --bg --https=443 http://localhost:8080
tailscale serve --bg --https=443 http://localhost:8088
```

**Expected output:**

```
Available within your tailnet:
https://my-mac.your-tailnet.ts.net/
|-- proxy http://localhost:8080
```

Tailscale will print the HTTPS MagicDNS URL for your services.

**Accessing your services using MagicDNS:**

Open the HTTPS URL provided by Tailscale in your browser from any device on your tailnet:

```
https://my-mac.your-tailnet.ts.net (for MLX Manager)
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
|-- / proxy http://localhost:8080
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
tailscale funnel 8080
```

**Expected output:**

```
Available on the internet:
https://my-mac.your-tailnet.ts.net/
|-- proxy http://127.0.0.1:8080
```

> **Warning:** Funnel exposes your service to the public internet. Anyone with the URL can access it. Do not use Funnel for services containing sensitive data. Always enable password authentication for any service exposed via Funnel.

To stop public access:

```bash
tailscale funnel --terminate-on 8080
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
| Services don't start after reboot | Verify auto-login is enabled; check FileVault is OFF |
| `mlx-manager` not found | Run `eval "$(/opt/homebrew/bin/brew shellenv)"` and retry |
| QwenPaw can't reach MLX | Confirm MLX Manager is running: `curl http://localhost:10242/v1/models` |
| Out of memory errors | Use smaller quantized models (4-bit); reduce context window in MLX Manager |
| Port conflicts | Change MLX Manager port with `MLX_MANAGER_DEFAULT_PORT_START` env var |
| MagicDNS name doesn't resolve | Verify MagicDNS is enabled in the Tailscale admin console under DNS settings; check Tailscale is running on both devices |
| `ts.net` URL doesn't resolve | MagicDNS may be off for that resolver; enable it, or use `curl --resolve :443:` |
| SSH over Tailscale times out | Verify Remote Login is enabled (`sudo systemsetup -getremotelogin`); check Tailscale SSH policy in admin console |
| HTTPS URL gives certificate error | Verify HTTPS Certificates are enabled in the Tailscale admin console under DNS settings |
| Tailscale Serve not working | Run `tailscale serve status` to check active configurations; ensure the target services are running locally |
| Funnel URL not accessible | Verify Funnel is enabled in the admin console; check your ACL policy allows Funnel; ensure HTTPS certificates are enabled |