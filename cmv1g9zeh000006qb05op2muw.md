---
title: "Complete Guide: Always-On Mac Server with MLX, oMLX & QwenPaw"
datePublished: 2026-10-09T21:01:08.387Z
cuid: cmv1g9zeh000006qb05op2muw
slug: complete-guide-always-on-mac-server-with-mlx-omlx-qwenpaw
cover: https://cdn.hashnode.com/uploads/covers/6a92730f9a9aa7f72e74fdf4/e8731940-c0fb-4aa5-b7be-8ba95a19041e.png
tags: ai, mlx, macmini, qwenpaw

---

## Tested Environment

Everything in this guide was verified on the following setup. If your versions are close, the commands should work unchanged.

| Component | Version | Notes |
| --- | --- | --- |
| **macOS** | 15.x (Sequoia) or later | Required for oMLX |
| **Chip** | Apple Silicon (M1/M2/M3/M4/M5) | Required for MLX and oMLX |
| **Homebrew** | 4.x | Package manager for oMLX, Caddy, and Tailscale |
| **uv** | 0.8.x or later | Python version + package manager |
| **Python (MLX venv)** | 3.11.x | Managed by uv at `~/.mlx-venv` |
| **Python (QwenPaw)** | 3.12.x | Bundled by QwenPaw's installer |
| **MLX** | 0.32.x | Apple's ML framework |
| **mlx-lm** | 0.28.x | LLM extensions for MLX |
| **oMLX** | latest via `jundot/omlx` | Inference server + admin dashboard |
| **QwenPaw** | latest via `agentscope.io` | Agent framework + web console |
| **Caddy** | 2.x | Reverse proxy + authentication layer |
| **Tailscale** | latest via `--cask` | Mesh VPN, SSH, TLS termination |
| **cloudflared** | latest via Homebrew | Public access via custom domain |

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

```plaintext
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

### 1.1b Prevent App Nap with caffeinate

`pmset` stops the system from sleeping, but macOS can still throttle background processes via **App Nap**. On an always-on server, App Nap causes services to respond slowly — a request that should take milliseconds can hang for seconds while the process is deprioritized. This is especially noticeable on MLX inference: token generation rate can drop dramatically when macOS decides the process is "idle" between requests.

The `caffeinate` command prevents App Nap by holding IOKit power assertions:

```bash
caffeinate -dimsu -t 2147483647
```

| Flag | Effect |
| --- | --- |
| `-d` | Prevent the display from sleeping |
| `-i` | Prevent idle system sleep — this is what blocks App Nap |
| `-m` | Prevent disk idle sleep |
| `-s` | Prevent system sleep on AC power |
| `-u` | Declare the user is active |
| `-t 2147483647` | Hold the assertion for the maximum duration (~68 years) |

To make it persistent across reboots, create a dedicated launch agent. This runs independently of your other services, so it survives their restarts:

```bash
cat > ~/Library/LaunchAgents/com.caffeinate.server.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.caffeinate.server</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/caffeinate</string>
    <string>-dimsu</string>
    <string>-t</string>
    <string>2147483647</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
</dict>
</plist>
EOF
```

Load it:

```bash
launchctl bootout gui/$(id -u)/com.caffeinate.server 2>/dev/null
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.caffeinate.server.plist
```

Verify it's running:

```bash
launchctl list | grep caffeinate
```

**Expected output:**

```plaintext
-	0	com.caffeinate.server
```

Confirm the assertions are active:

```bash
pmset -g assertions | grep -A 5 "caffeinate"
```

**Expected output:** A list showing `PreventUserIdleSystemSleep`, `PreventUserIdleDisplaySleep`, and related assertions attributed to `caffeinate`.

> **Note:** Some reports suggest that `pmset -g assertions` on certain macOS versions no longer lists all assertions. Even if the output is sparse, the `caffeinate` process running under `launchctl` is sufficient — the assertions are held at the kernel level regardless of what `pmset` displays.

### 1.2 Enable SSH (Remote Login)

On macOS Catalina (10.15) and later, the `systemsetup` command requires **Full Disk Access** to toggle Remote Login. Running it without that permission will fail with:

```plaintext
setremotelogin: Turning Remote Login on or off requires Full Disk Access privileges.
```

This is a macOS security feature (TCC), and `sudo` alone does not bypass it. Follow these steps to fix it permanently.

**Step 1: Grant Full Disk Access to Terminal**

1.  Open **System Settings**.
    
2.  Go to **Privacy & Security** → **Full Disk Access**.
    
3.  Click the **+** button.
    
4.  Navigate to **Applications** → **Utilities** and select **Terminal.app** (or your terminal of choice, e.g., iTerm).
    
5.  Toggle Terminal **on** in the list.
    
6.  **Quit Terminal completely** (`Cmd+Q`) and reopen it. The permission only takes effect for new sessions.
    

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

### 1.3 Enable Auto-Login (Required for LaunchAgents)

launchd user agents only start after a user logs in. Without auto-login, your services won't run after a reboot.

1.  Open **System Settings** → **Users & Groups**
    
2.  Click **Automatic Login** → select your user account
    
3.  Enter your password when prompted
    

> **Note:** FileVault must be OFF for auto-login to work. Go to **System Settings → Privacy & Security → FileVault** and turn it off if it's enabled. This is acceptable for a physically secure home server.

### 1.4 LaunchAgents vs. LaunchDaemons (Understanding the Difference)

As you build this server, you'll encounter two types of background services. It's important to know the difference:

- **LaunchAgents** (`~/Library/LaunchAgents/`) run **only after you log in** to the Mac. The graphical user interface (`WindowServer` and `loginwindow`) must be running. If the Mac boots headless and fails to start the GUI, LaunchAgents never start. Examples in this guide: **Caddy**, and **caffeinate**.
- **LaunchDaemons** (`/Library/LaunchDaemons/`) run **at system boot**, long before any user logs in. They run in the background and do not need a GUI. Examples in this guide: **oMLX**, **QwenPaw**, and **cloudflared**.

**Why does this matter?** If your Mac mini reboots but the desktop session gets stuck (which happens on headless Macs), your LaunchAgents won't load. By installing the core external-access services (oMLX, QwenPaw, and cloudflared) as LaunchDaemons, we guarantee you can reach the server from the internet even if the GUI hangs.

If the GUI *does* fail to start, SSH in and run this diagnostic to see what's happening:

```bash
echo "=== Login window running? ===" && pgrep -l loginwindow
echo "=== WindowServer running? ===" && pgrep -l WindowServer
```

If both return nothing, the GUI never started. Check that FileVault is OFF, auto-login is enabled, and consider adding an HDMI dummy plug (a cheap hardware trick that forces the Mac to output a video signal so `WindowServer` starts).

> **Managing LaunchDaemons:** Because they run in the system domain, you must use `sudo` and the `system/` path to manage them. For example: `sudo launchctl kickstart -k system/com.omlx.server`. Attempting to use `gui/$(id -u)` will fail with `Could not find service`.

### 1.5 Optional: Menu Bar Server Mode Toggle

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

```plaintext
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
> 
> ```bash
> python -c "import importlib.metadata as md; print(md.version('mlx'))"
> ```

## Part 4: Install oMLX (Web Dashboard + Background Service)

oMLX is an LLM inference server optimized for Apple Silicon, built on the MLX framework. It provides continuous batching, tiered KV caching (hot in-memory + cold SSD), and a web-based admin dashboard for managing models. It is actively maintained and ships as a Homebrew formula with native launchd service integration.

> **Note:** oMLX is a community project maintained by `jundot`. It is built directly on top of Apple's MLX framework (which *is* official).

> **Platform requirement:** oMLX requires **Apple Silicon** (M1/M2/M3/M4/M5) and **macOS 15.0 (Sequoia) or later**. Intel Macs and earlier macOS versions are rejected during installation.

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

```plaintext
==> Tapping jundot/omlx
Cloning into '/opt/homebrew/Library/Taps/jundot/homebrew-omlx'...
Tapped 1 formula.
==> Successfully trusted tap jundot/omlx.
==> Installing omlx from jundot/omlx
/opt/homebrew/Cellar/omlx/x.x.x: ...
```

> **Why** `brew trust` **is needed:** Recent versions of Homebrew refuse to load formulas from third-party taps unless you explicitly trust them — a security feature to prevent arbitrary code execution from untrusted sources. If you skip this, you'll see `Error: Refusing to load formula jundot/omlx/omlx from untrusted tap jundot/omlx.`

### 4.3 Set the API Keys (The Right Way)

oMLX uses **two distinct keys**, and confusing them is the most common setup error:

| Key | Purpose | Where It's Used |
| :--- | :--- | :--- |
| **`api_key`** | Authenticates inference requests. | The `/v1/*` endpoints (clients send this as a Bearer token). |
| **`secret_key`** | Signs the session cookies for the Admin Dashboard. | The web UI at `/admin`. Prevents you from being logged out on restart. |

**The correct home for these keys is `~/.omlx/settings.json`.** 
While oMLX can read an environment variable (`OMLX_API_KEY`), putting it in a Homebrew-managed plist is fragile. The next time you run `brew upgrade omlx`, Homebrew will rewrite the plist and wipe your key, locking you out.

Run this block to generate strong cryptographic keys and inject them directly into oMLX's configuration file:

```bash
# 1. Generate keys (api_key gets a suffix, secret_key is base hex)
BASE_KEY=$(openssl rand -hex 32)
API_KEY="${BASE_KEY}@81"

# 2. Ensure the directory exists
mkdir -p ~/.omlx

# 3. Inject into settings.json (creating it if missing)
if [ -f ~/.omlx/settings.json ]; then
    jq --arg ak "$API_KEY" --arg sk "$BASE_KEY" \
       '.auth = {api_key: $ak, secret_key: $sk}' \
       ~/.omlx/settings.json > ~/.omlx/settings.json.tmp && mv ~/.omlx/settings.json.tmp ~/.omlx/settings.json
else
    jq -n --arg ak "$API_KEY" --arg sk "$BASE_KEY" \
       '{auth: {api_key: $ak, secret_key: $sk}}' > ~/.omlx/settings.json
fi

# 4. Lock down file permissions
chmod 600 ~/.omlx/settings.json

# 5. Print the keys so you can save them for QwenPaw
echo "API Key:    $(jq -r '.auth.api_key' ~/.omlx/settings.json)"
echo "Secret Key: $(jq -r '.auth.secret_key' ~/.omlx/settings.json)"
```

**Expected output:** Two long random strings. Save the `API Key` (the one ending in `@81`) — you will need it for QwenPaw in §5.2.

### 4.3b Rotating the API Key Later

If you ever need to change the keys, do not edit `settings.json` manually or use the admin UI (which might desync your QwenPaw config). Re-run the generation block from §4.3. 

Because we are using a custom LaunchDaemon (see §4.4) that does not hardcode the keys in the plist, you simply need to restart oMLX and update QwenPaw:

```bash
sudo launchctl kickstart -k system/com.omlx.server
jq -r '.auth.api_key' ~/.omlx/settings.json # Copy this into QwenPaw's config
```

### 4.4 Start oMLX as an Always-On Background Service

Because we want oMLX to start at boot (even if the GUI fails), we will run it as a LaunchDaemon. But instead of relying on Homebrew's `brew services` (which wipes custom env vars on upgrade), we create our own daemon that simply points to the Homebrew binary. oMLX will read the keys directly from `settings.json`.

First, stop the default Homebrew service to avoid port conflicts:

```bash
brew services stop omlx 2>/dev/null
launchctl bootout gui/$(id -u)/sh.brew.omlx 2>/dev/null
```

Now create the LaunchDaemon:

```bash
USER_NAME=$(whoami)
HOME_DIR=$HOME

sudo tee /Library/LaunchDaemons/com.omlx.server.plist > /dev/null << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.omlx.server</string>
  <key>UserName</key>
  <string>${USER_NAME}</string>
  <key>GroupName</key>
  <string>staff</string>
  <key>ProgramArguments</key>
  <array>
    <string>/opt/homebrew/bin/omlx</string>
    <string>serve</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>WorkingDirectory</key>
  <string>${HOME_DIR}</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>HOME</key>
    <string>${HOME_DIR}</string>
    <key>PATH</key>
    <string>/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin:${HOME_DIR}/.local/bin</string>
  </dict>
  <key>StandardOutPath</key>
  <string>/tmp/omlx.out.log</string>
  <key>StandardErrorPath</key>
  <string>/tmp/omlx.err.log</string>
</dict>
</plist>
EOF

sudo launchctl bootout system/com.omlx.server 2>/dev/null
sudo launchctl bootstrap system /Library/LaunchDaemons/com.omlx.server.plist
sleep 3
sudo launchctl list | grep omlx
```

**Expected output:**

```plaintext
12345	0	com.omlx.server
```

### 4.5 Open the Admin Dashboard

oMLX binds to `http://localhost:8000` by default. Open the admin dashboard in your browser:

```plaintext
http://localhost:8000/admin
```

> **Note:** The dashboard lives at `/admin`, not `/`. Hitting the root URL returns a 404 by design. Log in using the `secret_key` you generated in §4.3.

### 4.6 Verify the API Key Works

Before moving on, confirm the key is accepted:

```bash
API_KEY=$(jq -r '.auth.api_key' ~/.omlx/settings.json)
curl -s -H "Authorization: Bearer $API_KEY" http://localhost:8000/v1/models
```

**Expected output:** `{"object":"list","data":[]}` — an empty list is correct at this stage because no model is loaded yet. The important thing is that you don't see `{"detail":"API key required"}` or a `401`.

### 4.7 Download & Deploy a Model

1.  In the admin dashboard (`http://localhost:8000/admin`), go to the **Models** section
    
2.  Search Hugging Face for MLX models (e.g., `mlx-community/Qwen3.5-4B-8bit`)
    
3.  Click **Download** — watch the progress bar
    
4.  Configure per-model settings (sampling parameters, context length, etc.)
    
5.  Click **Load** to start serving
    

Verify the model is live:

```bash
API_KEY=$(jq -r '.auth.api_key' ~/.omlx/settings.json)
curl -s -H "Authorization: Bearer $API_KEY" http://localhost:8000/v1/models
```

**Expected output:**

```json
{"object":"list","data":[{"id":"mlx-community/Qwen3.5-4B-8bit","object":"model"}]}
```

> **Note:** oMLX provides both OpenAI-compatible (`/v1/chat/completions`) and Anthropic-compatible (`/v1/messages`) endpoints. It also supports `/v1/embeddings`, `/v1/rerank`, and `/v1/responses` for broader compatibility.

![oMLX admin dashboard with a model loaded and serving](https://cdn.hashnode.com/uploads/gql/6a92730f9a9aa7f72e74fdf4/2cf4e346-d538-46b3-9247-bcad2487131a.png align="center")

## Part 5: Install QwenPaw (Agent Framework)

QwenPaw is a local-first AI agent framework that can connect to your oMLX-served models.

### 5.1 Install via One-Line Script

The installer writes a `qwenpaw` wrapper to `~/.qwenpaw/bin/` and adds it to your `PATH` via `~/.zshrc`. Because your current shell session hasn't re-read that file yet, the command needs a `source ~/.zshrc` in between:

```bash
curl -fsSL https://qwenpaw.agentscope.io/install.sh | bash && source ~/.zshrc && qwenpaw init --defaults
```

**Expected output:**

```plaintext
[qwenpaw] QwenPaw installed successfully
[qwenpaw] Wrapper created at /Users/<you>/.qwenpaw/bin/qwenpaw
[qwenpaw] Updated /Users/<you>/.zshrc
✅ Configuration initialized at ~/.qwenpaw/config.json
✅ Default model backend configured
```

> **If you already ran the installer and got** `command not found: qwenpaw`**:** the install itself succeeded — you just need to reload your shell. Run `source ~/.zshrc && qwenpaw init --defaults` and continue.

This script installs QwenPaw into `~/.qwenpaw` with a self-contained `uv`\-managed Python environment. It automatically installs `uv`, creates a virtual environment, and downloads dependencies without requiring manual Python setup.

### 5.2 Configure QwenPaw to Use oMLX

Write the QwenPaw config in one command. Note that the `api_key` here **must match** the `api_key` in `~/.omlx/settings.json`:

```bash
API_KEY=$(jq -r '.auth.api_key' ~/.omlx/settings.json)

cat > ~/.qwenpaw/config.json << EOF
{
  "model": {
    "backend": "openai",
    "base_url": "http://localhost:8000/v1",
    "api_key": "${API_KEY}",
    "model_name": "mlx-community/Qwen3.5-4B-8bit"
  }
}
EOF
```

> **If** `~/.qwenpaw/config.json` **already exists** — for example, if QwenPaw has written preferences or other settings — do **not** overwrite it with this heredoc. Use `jq` to update just the `api_key` field:
> ```bash
> API_KEY=$(jq -r '.auth.api_key' ~/.omlx/settings.json)
> jq --arg key "$API_KEY" '.model.api_key = $key' ~/.qwenpaw/config.json > ~/.qwenpaw/config.json.tmp && mv ~/.qwenpaw/config.json.tmp ~/.qwenpaw/config.json
> ```

> **Path note:** `base_url` must include the `/v1` suffix. QwenPaw's OpenAI client appends `/models`, `/chat/completions`, etc. after `base_url`, so a missing `/v1` sends requests to the wrong paths.

### 5.3 Start QwenPaw

```bash
source ~/.zshrc && qwenpaw app
```

**Expected output:**

```plaintext
QwenPaw Console running at http://127.0.0.1:8088/
```

Open `http://localhost:8088` to access the QwenPaw web console.

### 5.4 Make QwenPaw Persistent (LaunchDaemon)

Because QwenPaw is the service you'll rely on most for remote access, we install it as a **LaunchDaemon**. This means it starts at boot, before you log in, and doesn't depend on the desktop GUI starting successfully.

We also pin QwenPaw's internal log rotation to **2 MiB × 2 backups** via `EnvironmentVariables` so the log directory can never exceed ~6 MiB.

Copy and paste the entire block. It dynamically pulls your current username and home directory to avoid placeholder errors:

```bash
USER_NAME=$(whoami)
HOME_DIR=$HOME

sudo tee /Library/LaunchDaemons/com.qwenpaw.app.plist > /dev/null << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.qwenpaw.app</string>
  <key>UserName</key>
  <string>${USER_NAME}</string>
  <key>GroupName</key>
  <string>staff</string>
  <key>ProgramArguments</key>
  <array>
    <string>${HOME_DIR}/.qwenpaw/bin/qwenpaw</string>
    <string>app</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>WorkingDirectory</key>
  <string>${HOME_DIR}</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>HOME</key>
    <string>${HOME_DIR}</string>
    <key>PATH</key>
    <string>/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin:${HOME_DIR}/.local/bin</string>
    <key>QWENPAW_LOG_MAX_SIZE</key>
    <string>2MiB</string>
    <key>QWENPAW_LOG_MAX_BACKUPS</key>
    <string>2</string>
  </dict>
  <key>StandardOutPath</key>
  <string>/tmp/qwenpaw.out.log</string>
  <key>StandardErrorPath</key>
  <string>/tmp/qwenpaw.err.log</string>
</dict>
</plist>
EOF

sudo launchctl bootout system/com.qwenpaw.app 2>/dev/null
sudo launchctl bootstrap system /Library/LaunchDaemons/com.qwenpaw.app.plist
sleep 5
sudo launchctl list | grep qwenpaw
```

**Expected output:**

```plaintext
12345	0	com.qwenpaw.app
```

The first column is the PID (a number means it's running), the second is the last exit status (`0` = clean), and the third is the label.

**Useful launcher management commands:**

```bash
sudo launchctl list | grep qwenpaw                                           # check status
sudo launchctl bootout system/com.qwenpaw.app                                # stop and unregister
sudo launchctl bootstrap system /Library/LaunchDaemons/com.qwenpaw.app.plist # start and register
sudo launchctl kickstart -k system/com.qwenpaw.app                           # restart in place
```

> **After editing the plist**, you must `bootout` then `bootstrap` for changes to take effect — launchd caches the plist at load time.

![QwenPaw web console with an agent conversation open](https://cdn.hashnode.com/uploads/gql/6a92730f9a9aa7f72e74fdf4/f3ac7a7b-3fd4-48fd-8e72-b138b735fc34.png align="center")

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
API_KEY=$(jq -r '.auth.api_key' ~/.omlx/settings.json)
brew services list | grep caddy && sudo launchctl list | grep -E "omlx|qwenpaw" && curl -s -H "Authorization: Bearer $API_KEY" http://localhost:8000/v1/models && curl -s -o /dev/null -w "QwenPaw HTTP %{http_code}\n" http://localhost:8088/
```

**Expected output:**

```plaintext
caddy    started    yourname    ~/Library/LaunchAgents/homebrew.mxcl.caddy.plist
12345	0	com.omlx.server
12345	0	com.qwenpaw.app
{"object":"list","data":[...]}
QwenPaw HTTP 200
```

All services should return healthy responses without any manual intervention.

## Part 7: Remote Access from Anywhere

This part sets up secure access to both oMLX and QwenPaw from anywhere. **Tailscale** provides encrypted SSH and private tailnet access; **Cloudflare Tunnel** provides public HTTPS via your own domain. **Caddy** runs locally as a reverse proxy in front of both services.

### 7.0 Create a Tailscale Account

If you don't already have a Tailscale account, sign up first. It's free for personal use and takes about a minute.

1.  Go to [tailscale.com](https://tailscale.com/) and click **Get Started**.
2.  Sign up using a **single sign-on (SSO) identity provider** — Google, GitHub, Microsoft, Apple, or a custom email address.
3.  After signing in, choose **Personal use**.
4.  You land on the **Admin Console** at [console.tailscale.com/admin](https://console.tailscale.com/admin).

> **Tip:** The same account must be used on every device you want on your tailnet.

### 7.1 Install Tailscale on Your Mac Server

```bash
brew install --cask tailscale
```

**Expected output:** `tailscale-app was successfully installed!`

Open the Tailscale app from your Applications folder or menu bar, and sign in with the same account you just created. Once authenticated, the Tailscale icon appears in your menu bar and shows a green "Connected" status.

> **Note:** The `--cask` version installs the GUI app but does **not** add the `tailscale` CLI to your `$PATH`. See §7.1b below to enable it.

### 7.1b Enable the Tailscale CLI

The cask bundles the CLI inside the app binary. **Do not symlink the app binary** — it crashes with `Fatal error: The current bundleIdentifier is unknown to the registry`. Instead, add a shell alias:

```bash
echo 'alias tailscale="/Applications/Tailscale.app/Contents/MacOS/Tailscale"' >> ~/.zshrc && source ~/.zshrc && tailscale status
```

**Expected output:**

```plaintext
100.x.x.x    my-mac-mini     user@example.com  macOS    -
100.x.x.x    my-laptop       user@example.com  macOS    -
```

### 7.2 SSH Config for Tailnet Access (No MagicDNS Required)

MagicDNS is convenient but it isn't always compatible with other DNS setups on your Mac — particularly when Cloudflare is managing a public domain. The fix is a **per-client SSH config file**.

**Get the Tailscale IP first** (from the server or any tailnet device):

```bash
tailscale status | grep night-thoughts | awk '{print $1}'
```

**Expected output:** Something like `100.64.x.x` — the Tailscale IP of your Mac server.

**Then, on every client device you SSH from** (not the server itself), append the alias to `~/.ssh/config`:

```bash
mkdir -p ~/.ssh && cat >> ~/.ssh/config << 'EOF'

Host nt
    HostName 100.64.x.x
    User your-macos-username
EOF
```

Replace:

- `100.64.x.x` with the actual Tailscale IP from above
- `your-macos-username` with the account you log in as on the Mac server

**Verify:**

```bash
ssh nt
```

> **Why not `/etc/hosts`?** It requires `sudo`, breaks on OS updates that re-generate the file, and is global to the machine. `~/.ssh/config` is scoped to SSH, requires no elevated privileges, and survives system updates.

### 7.3 Enable HTTPS Certificates

Tailscale Serve needs HTTPS certificates enabled for your tailnet before it can terminate TLS on port 443.

1.  Go to the [**DNS page**](https://console.tailscale.com/admin/dns) of the Tailscale admin console.
2.  Under the **HTTPS Certificates** section, click **Enable HTTPS**.

### 7.4 Install Caddy

Caddy is the always-on reverse proxy that routes each service and provides a single entry point. Install it via Homebrew:

```bash
brew install caddy
```

**Expected output:** `caddy was successfully installed!`

Verify:

```bash
caddy version
```

**Expected output:** `v2.x.x`

### 7.5 Configure Caddy

Caddy handles two routing modes at once:

1.  **Subdomain routing** for Cloudflare — `omlx.nightthoughts.dev` and `qwenpaw.nightthoughts.dev` each map to their service at the root.
2.  **Path routing** for Tailscale Serve — a single hostname (`night-thoughts.<your-tailnet>.ts.net`) with `/omlx/*` and `/console/*` prefixes.

```bash
sudo mkdir -p /opt/homebrew/etc && sudo tee /opt/homebrew/etc/Caddyfile > /dev/null << 'EOF'
# ── Cloudflare subdomains (plain HTTP, tunnel forwards here) ──
http://omlx.nightthoughts.dev:9080 {
    # Paths oMLX actually owns — pass through to the backend
    @known path /admin /admin/* /v1 /v1/* /static/* /health /favicon.ico
    handle @known {
        reverse_proxy localhost:8000
    }

    # Root and any unmatched path → redirect to the dashboard
    handle {
        redir * /admin 302
    }
}

http://qwenpaw.nightthoughts.dev:9080 {
    reverse_proxy localhost:8088
}

# ── Tailscale Serve target (path-based, single hostname) ──────
:9080 {
    # oMLX entry point
    @omlx_bare path /omlx
    redir @omlx_bare /omlx/admin 302

    handle_path /omlx/* {
        reverse_proxy localhost:8000
    }

    # oMLX absolute paths (dashboard + assets + API)
    @omlx_absolute path /admin /admin/* /static/* /v1 /v1/* /health
    handle @omlx_absolute {
        reverse_proxy localhost:8000
    }

    # QwenPaw: full console + backend
    @qwenpaw path /console/* /api/* /assets/* /login /logout /voice/* /favicon.ico
    handle @qwenpaw {
        reverse_proxy localhost:8088
    }

    # QwenPaw: public files (SVG, PNG) at root
    @qwenpaw_public path_regexp \.(svg|png|ico|gif|jpg|jpeg|webp|woff|woff2|ttf|eot)$
    handle @qwenpaw_public {
        reverse_proxy localhost:8088
    }

    # Fallback: oMLX
    handle {
        reverse_proxy localhost:8000
    }
}
EOF
```

> **Why both blocks?** The subdomain blocks (`http://omlx.nightthoughts.dev:9080`) only match requests where the `Host` header is that subdomain — which is what Cloudflare sends. The `:9080` block catches everything else, which is what Tailscale Serve sends.

> **Why `http://` on the subdomains?** Without it, Caddy would try to provision its own TLS certificate for `omlx.nightthoughts.dev`, which fails because Cloudflare already holds one for that hostname and Caddy can't complete the ACME challenge. The `http://` prefix tells Caddy to serve that hostname over plain HTTP only.

> **The `*` matcher in `redir * /admin 302` is essential.** Caddy's `redir` directive is ambiguous when the destination starts with `/`: without an explicit matcher, Caddy can interpret `/admin` as a **path matcher** rather than the destination.

Verify the syntax:

```bash
caddy validate --config /opt/homebrew/etc/Caddyfile
```

**Expected output:** `Valid configuration`

### 7.6 Start Caddy as an Always-On Service

Caddy runs as a LaunchAgent managed by `brew services`. It starts on login and restarts on crash.

```bash
brew services start caddy
```

**Expected output:** `==> Successfully started 'caddy' (label: homebrew.mxcl.caddy)`

Confirm it's running and registered to auto-start:

```bash
brew services list | grep caddy
lsof -i :9080 | grep caddy
```

**Expected output:**

```plaintext
caddy    started    yourname    ~/Library/LaunchAgents/homebrew.mxcl.caddy.plist
caddy   39606    yourname    9u  IPv6  ...  TCP *:9080 (LISTEN)
```

### 7.7 Point Tailscale Serve at Caddy

Tailscale Serve exposes your services to devices on your tailnet — encrypted, private, and without requiring a public domain.

```bash
tailscale serve reset
tailscale serve --bg --https=443 http://localhost:9080
```

Verify:

```bash
tailscale serve status
```

**Expected output:**

```plaintext
https://night-thoughts.<your-tailnet>.ts.net (tailnet only)
|-- / proxy http://localhost:9080
```

> **Important — Tailscale DNS hijack:** If `dig` resolves your Cloudflare subdomains but `curl` from the server returns `Could not resolve host`, Tailscale's MagicDNS resolver is capturing all system DNS queries. Fix it with:
> ```bash
> tailscale set --accept-dns=false
> sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder
> ```

### 7.8 Enable QwenPaw Authentication

Tailscale controls network-level access, but **anyone on your tailnet — and anyone on the internet once §7.9 is set up — can reach QwenPaw**. Enabling QwenPaw's built-in web authentication adds a login prompt.

Rewrite the plist with the auth variables added, then reload the service. Replace `your-secure-password` with a strong password of your choice:

```bash
USER_NAME=$(whoami)
HOME_DIR=$HOME

sudo launchctl bootout system/com.qwenpaw.app 2>/dev/null

sudo tee /Library/LaunchDaemons/com.qwenpaw.app.plist > /dev/null << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.qwenpaw.app</string>
  <key>UserName</key>
  <string>${USER_NAME}</string>
  <key>GroupName</key>
  <string>staff</string>
  <key>ProgramArguments</key>
  <array>
    <string>${HOME_DIR}/.qwenpaw/bin/qwenpaw</string>
    <string>app</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>WorkingDirectory</key>
  <string>${HOME_DIR}</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>HOME</key>
    <string>${HOME_DIR}</string>
    <key>PATH</key>
    <string>/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin:${HOME_DIR}/.local/bin</string>
    <key>QWENPAW_LOG_MAX_SIZE</key>
    <string>2MiB</string>
    <key>QWENPAW_LOG_MAX_BACKUPS</key>
    <string>2</string>
    <key>QWENPAW_AUTH_ENABLED</key>
    <string>true</string>
    <key>QWENPAW_AUTH_USERNAME</key>
    <string>admin</string>
    <key>QWENPAW_AUTH_PASSWORD</key>
    <string>your-secure-password</string>
  </dict>
  <key>StandardOutPath</key>
  <string>/tmp/qwenpaw.out.log</string>
  <key>StandardErrorPath</key>
  <string>/tmp/qwenpaw.err.log</string>
</dict>
</plist>
EOF

sudo launchctl bootstrap system /Library/LaunchDaemons/com.qwenpaw.app.plist
sleep 3
sudo launchctl list | grep qwenpaw
```

**Expected output:**

```plaintext
12345	0	com.qwenpaw.app
```

Verify auth is active by checking that the console redirects to a login page:

```bash
curl -s -o /dev/null -w "QwenPaw HTTP %{http_code}\n" http://localhost:8088/
```

**Expected output:**

```plaintext
QwenPaw HTTP 200
```

> **Forgot the password?** Reset it with:
> ```bash
> QWENPAW_AUTH_ENABLED=true qwenpaw auth reset-password
> ```

### 7.9 Public Access with Subdomains

This section extends your setup from tailnet-only access to the public internet. After completing these steps, your services become reachable from any browser — no Tailscale client required — using subdomains on your own domain.

The result:

| Service | Public URL |
| --- | --- |
| **oMLX admin dashboard** | `https://omlx.nightthoughts.dev/admin` |
| **oMLX API** | `https://omlx.nightthoughts.dev/v1/models` |
| **QwenPaw web console** | `https://qwenpaw.nightthoughts.dev/` |

> **Security warning:** These URLs are reachable by **anyone on the internet**. You **must** have authentication enabled on both services before exposing them publicly.

**Step 1: Add your domain to Cloudflare**

1.  Sign up at [cloudflare.com](https://cloudflare.com) (free tier is enough).
2.  Click **Add a site** and enter `nightthoughts.dev`.
3.  Choose the **Free** plan.
4.  Cloudflare will scan your existing DNS records and display **two nameservers** assigned to your account.

**Step 2: Point the domain to Cloudflare at your registrar**

Cloudflare needs to be the authoritative DNS provider for your domain. This means replacing your registrar's default nameservers with the two Cloudflare nameservers shown in Step 1.

The process is the same for every registrar:

1.  Log in to your registrar account and find the DNS or nameserver settings for `nightthoughts.dev`.
2.  Locate the current nameservers.
3.  **Delete** them.
4.  **Paste** the two Cloudflare nameservers.
5.  **Save** your changes.

> **Important:** If DNSSEC is enabled at your registrar, disable it before changing nameservers. DNSSEC conflicts with the new authoritative DNS provider.

**Verify propagation**

After saving, check that the new nameservers are live:

```bash
dig +short NS nightthoughts.dev @1.1.1.1
```

**Expected output:**

```plaintext
april.ns.cloudflare.com.
damien.ns.cloudflare.com.
```

**Step 3: Install cloudflared**

```bash
brew install cloudflared
```

**Step 4: Authenticate**

```bash
cloudflared tunnel login
```

This opens a browser — select `nightthoughts.dev` and authorize.

**Step 5: Create the tunnel**

```bash
cloudflared tunnel list | grep -q night-thoughts || cloudflared tunnel create night-thoughts
```

**Step 6: Route DNS for both subdomains**

```bash
cloudflared tunnel route dns night-thoughts omlx.nightthoughts.dev
cloudflared tunnel route dns night-thoughts qwenpaw.nightthoughts.dev
```

Each command creates a **proxied CNAME** at Cloudflare pointing the subdomain to your tunnel.

**Step 7: Configure the tunnel**

```bash
TUNNEL_ID=$(cloudflared tunnel list | awk '/night-thoughts/ {print $1}') && \
cat > ~/.cloudflared/config.yml << EOF
tunnel: $TUNNEL_ID
credentials-file: $HOME/.cloudflared/$TUNNEL_ID.json

ingress:
  - hostname: omlx.nightthoughts.dev
    service: http://localhost:9080
  - hostname: qwenpaw.nightthoughts.dev
    service: http://localhost:9080
  - service: http_status:404
EOF
```

**Step 8: Install the tunnel as a LaunchDaemon**

> **Do not use `sudo cloudflared service install` on macOS.** It writes a broken launchd plist that omits the `tunnel run` subcommand, so the daemon exits immediately with `use cloudflared tunnel run to start tunnel <UUID>` in a loop.

Just like QwenPaw, cloudflared should be a LaunchDaemon so it starts at boot, before login. This block dynamically injects your username and home path:

```bash
USER_NAME=$(whoami)
HOME_DIR=$HOME

sudo tee /Library/LaunchDaemons/com.cloudflare.cloudflared.plist > /dev/null << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.cloudflare.cloudflared</string>
  <key>UserName</key>
  <string>${USER_NAME}</string>
  <key>GroupName</key>
  <string>staff</string>
  <key>ProgramArguments</key>
  <array>
    <string>/opt/homebrew/bin/cloudflared</string>
    <string>tunnel</string>
    <string>run</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>WorkingDirectory</key>
  <string>${HOME_DIR}</string>
  <key>StandardOutPath</key>
  <string>/tmp/cloudflared.out.log</string>
  <key>StandardErrorPath</key>
  <string>/tmp/cloudflared.err.log</string>
</dict>
</plist>
EOF

sudo launchctl bootout system/com.cloudflare.cloudflared 2>/dev/null
sudo launchctl bootstrap system /Library/LaunchDaemons/com.cloudflare.cloudflared.plist
sleep 5
sudo launchctl list | grep cloudflared
```

**Expected output:**

```plaintext
12345	0	com.cloudflare.cloudflared
```

**Step 9: Verify**

Now check the log to confirm the tunnel is actually connected:

```bash
tail -20 /tmp/cloudflared.err.log
```

**Expected output:** A health precheck summary followed by connection logs:

```plaintext
INF |  SUMMARY: Environment is healthy. cloudflared will use 'quic' as primary protocol.  |
INF precheck complete hard_fail=false run_id=... suggested_protocol=quic
INF Registered tunnel connection connIndex=0 connection=... location=hkg
INF Registered tunnel connection connIndex=1 connection=... location=hkg
```

Then test publicly. The first test checks that unmatched paths redirect properly:

```bash
curl -sL -o /dev/null -w "/typo → %{http_code} %{url_effective}\n" https://omlx.nightthoughts.dev/typo
curl -s -o /dev/null -w "/ → %{http_code}\n" https://omlx.nightthoughts.dev/
curl -s -o /dev/null -w "/admin → %{http_code}\n" https://omlx.nightthoughts.dev/admin
curl -s -o /dev/null -w "/v1/models → %{http_code}\n" https://omlx.nightthoughts.dev/v1/models
curl -s -o /dev/null -w "QwenPaw / → %{http_code}\n" https://qwenpaw.nightthoughts.dev/
```

**Expected output:**

```plaintext
/typo → 200 https://omlx.nightthoughts.dev/admin
/ → 302
/admin → 200
/v1/models → 401    (no key sent)
QwenPaw / → 200
```

**Useful commands:**

```bash
# Check tunnel status
sudo launchctl list | grep cloudflared

# View cloudflared logs
tail -20 /tmp/cloudflared.err.log

# Restart the tunnel after config changes
sudo launchctl kickstart -k system/com.cloudflare.cloudflared

# Remove the tunnel entirely
sudo launchctl bootout system/com.cloudflare.cloudflared
sudo rm /Library/LaunchDaemons/com.cloudflare.cloudflared.plist
cloudflared tunnel delete night-thoughts
```

### 7.10 Verify Everything Survives Reboot

Restart your Mac:

```bash
sudo reboot
```

After reboot, wait 30 seconds, then SSH in from another machine:

```bash
ssh nt
```

Check all services in one command:

```bash
brew services list | grep caddy && sudo launchctl list | grep -E "omlx|qwenpaw|cloudflared" && tailscale serve status
```

**Expected output:**

```plaintext
caddy   started    yourname    ~/Library/LaunchAgents/homebrew.mxcl.caddy.plist
12345	0	com.omlx.server
12345	0	com.qwenpaw.app
12345	0	com.cloudflare.cloudflared
https://night-thoughts.<your-tailnet>.ts.net (tailnet only)
|-- / proxy http://localhost:9080
```

All components should be running without any manual intervention:

| Component | Managed by | Domain | Auto-starts on login? | Auto-starts at boot? |
| --- | --- | --- | --- | --- |
| **oMLX** | `launchd` | **System** | ✅ | **✅** |
| **Caddy** | `brew services` | GUI | ✅ | ❌ |
| **QwenPaw** | `launchd` | **System** | ✅ | **✅** |
| **cloudflared** | `launchd` | **System** | ✅ | **✅** |
| **Tailscale Serve** | Tailscale daemon | System | ✅ | ✅ |

Then verify public access works end-to-end:

```bash
curl -s -o /dev/null -w "Public oMLX:    HTTP %{http_code}\n" https://omlx.nightthoughts.dev/admin
curl -s -o /dev/null -w "Public QwenPaw: HTTP %{http_code}\n" https://qwenpaw.nightthoughts.dev/
```

## Troubleshooting Quick Reference

| Symptom | Fix |
| --- | --- |
| `systemsetup: Turning Remote Login on or off requires Full Disk Access privileges` | Grant Terminal Full Disk Access in System Settings → Privacy & Security → Full Disk Access, then **quit and reopen Terminal** |
| `pmset -g` shows `SleepDisabled 1` instead of `disablesleep 1` | Normal on macOS Ventura+. Same setting, different label |
| `sleep 0 (sleep prevented by powerd, bluetoothd)` | Informational, not an error. Sleep is disabled as intended |
| Services respond slowly or hang under load | App Nap is throttling them. Verify `caffeinate` is running: `launchctl list | grep caffeinate` |
| **Services don't start after reboot** | The GUI session didn't load. oMLX, QwenPaw, and cloudflared will still start because they are LaunchDaemons, but Caddy won't. Check `loginwindow` and `WindowServer` per §1.4 |
| **`Could not find service "com.qwenpaw.app" in domain for user gui: 501`** | QwenPaw is a LaunchDaemon. Use `sudo launchctl kickstart -k system/com.qwenpaw.app` instead of the `gui/` domain. See §1.4 |
| `brew: command not found` | Run `eval "$(/opt/homebrew/bin/brew shellenv)"` or add it to `~/.zprofile` |
| `Error: Refusing to load formula ... from untrusted tap` | Run `brew trust jundot/omlx`, then retry `brew install jundot/omlx/omlx` |
| oMLX install rejected on Intel Mac or macOS 14 | oMLX requires Apple Silicon and macOS 15.0 (Sequoia) or later |
| `AttributeError: module 'mlx' has no attribute '__version__'` | Expected — version lives on `mlx.core`. Use `python -c "import mlx.core as mx; print(mx.__version__)"` |
| Admin dashboard shows 404 at `localhost:8000` | The correct path is `/admin`, not `/`. |
| **`omlx.nightthoughts.dev/typo` returns a blank page instead of redirecting to `/admin`** | The `redir` directive is missing its `*` matcher. Change `redir /admin 302` to `redir * /admin 302` in the oMLX subdomain block |
| `401 Unauthorized` from oMLX | The `api_key` in QwenPaw's config doesn't match the key in `~/.omlx/settings.json`. Both must be **exactly** the same string |
| **Need to change the oMLX API key** | Re-run the generation block in §4.3, then restart the daemon (`sudo launchctl kickstart -k system/com.omlx.server`) and update QwenPaw |
| `jq: command not found` | Install with `brew install jq` |
| Forgot the QwenPaw password | Run `QWENPAW_AUTH_ENABLED=true qwenpaw auth reset-password`, or delete `~/.qwenpaw.secret/auth.json` and restart the daemon |
| **QwenPaw login fails with "Invalid credentials"** | The username in `auth.json` doesn't match the plist. Check `cat ~/.qwenpaw.secret/auth.json` — if it says `night-thoughts` but you're typing `admin`, either log in as `night-thoughts` or delete the file and restart to regenerate it from the plist |
| **QwenPaw daemon exits with code 78 (`EX_CONFIG`)** | A placeholder value was left in the plist. Check with `sudo plutil -p /Library/LaunchDaemons/com.qwenpaw.app.plist` and fix `UserName` and `WorkingDirectory` |
| **Telegram: `Conflict: terminated by other getUpdates request`** | Two QwenPaw instances are polling the same bot token. Kill the duplicate with `sudo pkill -9 -f qwenpaw`, remove `~/.qwenpaw/desktop_backend.pid`, and revoke the token via `@BotFather` |
| **Telegram: `invalid bot token — not retrying`** | The token was revoked. Get a fresh one from `@BotFather` and paste it into the QwenPaw console at Channels → Telegram |
| `cloudflared tunnel route dns` says "neither the ID nor the name of any of your tunnels" | Run `cloudflared tunnel list` to see actual tunnel names, then retry with the exact name or ID |
| cloudflared log spams `use cloudflared tunnel run to start tunnel <UUID>` | `sudo cloudflared service install` wrote a broken plist. Use the LaunchDaemon block in §7.9 Step 8 instead |
| Nameserver change at your registrar isn't propagating | Confirm DNSSEC is disabled at your registrar. Check status with `dig +short NS <domain> @1.1.1.1` |
| `dig` works but `curl` returns `Could not resolve host` | Tailscale MagicDNS is hijacking the system resolver. Run `tailscale set --accept-dns=false` then `sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder` |
| `ssh nt` returns `Could not resolve hostname` | Your `~/.ssh/config` entry is missing or malformed |
| `ssh nt` returns `Permission denied` | Wrong username in `~/.ssh/config`. Verify with `whoami` on the server |

---

If you build this stack, tag me — I want to see what agents and local workflows you are running on your Mac. And if you are working on local LLM inference, Apple Silicon optimization, or self-hosted AI, let us talk in the comments or connect directly.

— Haithem Slimi, [nightthoughts.dev](https://nightthoughts.dev)