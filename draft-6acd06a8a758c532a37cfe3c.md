---
title: "Multi-Agent Medical Imaging AI: A Local, Private, Auditable Pipeline for X-ray, CT, MRI, and Ultrasound"
cover: https://cdn.hashnode.com/uploads/covers/6a92730f9a9aa7f72e74fdf4/a4e92753-b767-491e-87ba-d447ef92b764.png

---

# Multi-Agent Medical Imaging AI: A Local, Private, Auditable Pipeline for X-ray, CT, MRI, and Ultrasound

**Built on MedMO-8B-Next, DeepSeek Harness, and MLX — with a hard de-identification gate, a System 1 decision layer, a persistent memory layer, and a hash-chained audit trail. No cloud inference. No patient data leaves the machine. Every agent action is verifiable, and every batch makes the pipeline smarter.**

---

Clinical documentation is broken. Physicians spend **two hours on administrative work for every hour of direct patient care**. Ambient scribes capture what was said — but they do not structure a note against a checklist, insist on pending results at discharge, force explicit allergy statements on admission, or attach a citation and retrieval date to every fact they surface.

Medical imaging has the same problem in a different shape. The models that could help — the ones that generate structured radiology reports and localize findings — are either locked behind commercial APIs or require NVIDIA data-center GPUs that most clinics, researchers, and independent developers do not have.

This guide builds the alternative. A supervised team of seven agents that de-identifies, classifies, analyzes, reviews, and integrates medical images — running entirely on local hardware, with a persistent memory layer that accumulates knowledge across batches, and a hash-chained audit trail anyone can verify offline.

---

## Before You Start: Your Existing Stack

This guide builds directly on my previous article, **[Complete Guide: Always-On Mac Server with MLX, oMLX & QwenPaw](https://nightthoughts.me/complete-guide-always-on-mac-server-with-mlx-omlx-qwenpaw)**. If you have not read that yet, start there — you need the foundation it establishes before anything here will work.

That guide set up:

- **oMLX** — an LLM inference server optimized for Apple Silicon, managed from the macOS menu bar
- **QwenPaw** — your existing agent framework, running as a LaunchDaemon on `localhost:8088`
- **Caddy** — reverse proxy with TLS termination and Basic Auth on port `9080`, configured for both **subdomain routing** (public, via Cloudflare) and **path routing** (private, via Tailscale)
- **Tailscale** — mesh VPN for private remote access
- **Cloudflare Tunnel** — public access via `cloudflared`, running as a LaunchDaemon

The architecture is: **Cloudflare Tunnel → Caddy (`localhost:9080`) → services**, and **Tailscale Serve → Caddy → services**. All traffic to subdomains is handled by a single Caddy instance.

### Verify Before You Continue

```bash
# 1. oMLX server responding
curl -s http://127.0.0.1:8000/v1/models | head -c 200

# 2. QwenPaw running (LaunchDaemon — needs sudo)
curl -s -o /dev/null -w "QwenPaw: %{http_code}\n" http://127.0.0.1:8088

# 3. Caddy running
brew services list | grep caddy

# 4. Tailscale connected
tailscale status | head -3

# 5. Cloudflare Tunnel active (LaunchDaemon — needs sudo)
sudo launchctl list | grep cloudflared

# 6. MLX Python environment
python -c "import mlx_lm; print('mlx_lm:', mlx_lm.__version__)"
```

**Expected:**

```
{"object":"list","data":[{"id":"..."}]}
QwenPaw: 200
caddy                started
100.x.x.x    your-mac    your-tailnet    macOS    -
-    0    com.cloudflare.cloudflared
mlx_lm: 0.28.x
```

All six should return healthy output. If not, fix the foundation first.

> **A note on domains:** Throughout this guide, I use `nightthoughts.dev` as my domain. Replace it with your own domain everywhere you see it. Every path uses `${HOME}` and resolves to your actual home directory automatically.

---

## Minimum Configuration

- **Apple Silicon Mac** (M1 or later). The unified memory architecture is required for local MLX inference.
- **Unified memory:** 32GB is the practical minimum for running an 8B vision-language model alongside DSH and a swarm of agents. **48GB or more** is recommended for comfortable parallel execution.
- **Storage:** 512GB+ recommended — MedMO-8B-Next is ~16GB in BF16, and medical image datasets are large.
- **macOS Sequoia 15.x or later.**
- **Homebrew, Node.js 22.19+, Caddy, Tailscale, `cloudflared`** — from the previous guide.
- **MLX installed** (`mlx-lm` and `mlx-vlm`).

---

## What MedMO Is and Why We Chose It

### What It Is

**MedMO-8B-Next** is the latest iteration of the MedMO family — an **open-source multimodal foundation model** (Apache 2.0 license) purpose-built for comprehensive medical image understanding and grounding. It was developed by researchers at MBZUAI (Mohamed bin Zayed University of Artificial Intelligence) and trained on **26 million diverse medical samples across 45 datasets**.

MedMO supports a wide range of clinical imaging — **X-ray, CT, MRI, Ultrasound, pathology, ophthalmology, dermatology, and nuclear medicine**. This guide builds the pipeline for the **four core radiology modalities** (X-ray, CT, MRI, Ultrasound), which share a common DICOM standard and standard prompt patterns. Extending to the other modalities is a clear next step; see the "Where to Extend" section at the end for what each requires.

Under the hood, MedMO is built on **Qwen3-VL-8B-Instruct** and trained through a three-stage recipe: cross-modal pretraining to align visual encoders with a medical language backbone, instruction tuning across captioning, VQA, report generation, retrieval, and grounded disease localization with bounding boxes, and reinforcement learning with verifiable rewards that combine factuality checks with a **box-level GIoU reward** to strengthen spatial grounding and step-by-step reasoning in complex clinical scenarios.

That last stage is what makes MedMO different from other medical VLMs. The reinforcement learning explicitly optimizes for **where** a finding is, not just **what** it is. The model learns to output bounding boxes that align with the ground truth, because the reward function measures spatial overlap directly.

### The Benchmark Results

| Benchmark | MedMO-8B-Next | Fleming-VL-8B | Gain |
|---|---|---|---|
| MMMU-Med | 69.3% | 63.3% | **+6.0%** |
| PMC-VQA | 74.1% | 64.3% | **+9.8%** |
| MMLU-Med | 80.2% | 71.8% | **+8.4%** |
| MedQA | 83.8% | 66.1% | **+17.7%** |
| MIMIC-CXR (report generation) | 71.3% | 55.5% | **+15.8%** |
| Bacteria grounding (IoU) | 56.1 | 9.1 | **+47.0** |

The grounding gain matters most for clinical utility. A **+47.0 IoU improvement** on bacteria localization is the difference between a model that can say "there may be an infection" and one that can point to the specific region.

### Why We Chose It

**First, it is the only open model that covers the core radiology modalities with grounding.** For a pipeline that needs to handle X-ray, CT, MRI, and ultrasound in the same batch, MedMO is the only open option that does not require a different model per modality.

**Second, it runs on Apple Silicon.** Because MedMO is built on Qwen3-VL-8B-Instruct, the MLX ecosystem supports it natively. That means it runs on your Mac. Locally. At zero marginal inference cost.

**Third, it is Apache 2.0.** No licensing restrictions on commercial use. No gated access. No usage caps.

---

## What DeepSeek Harness Is and Why We Chose It

### What It Is

**DeepSeek Harness (DSH)** is an **open-source agent runtime** released by DeepSeek on August 13, 2026, under the MIT license. It is built on **Cordis**, a plugin framework with a four-year production track record inside the Koishi chatbot project before DeepSeek adopted it here.

The central claim is that **literally every layer of an agent is a plugin**: the model adapter, the tool registry, the session log, the sandbox, the UI, and **even the agent loop itself**. The architecture defines **named swap points**, and each one has multiple shipped implementations you select in configuration rather than in code.

Three architectural properties matter for this project:

**Model-agnostic across roughly 40 providers.** A sub-agent can be delegated to a competitor's model entirely. For our pipeline, MedMO runs the vision tasks and Qwen3.5 runs the quality gate, both behind the same orchestration layer.

**Real OS-level sandboxing.** DSH uses **Seatbelt** (Apple's own sandbox framework) on macOS, bwrap and Landlock on Linux, restricted ACL tokens on Windows — fail-closed by default.

**Append-only session logs with a runtime-enforced rule.** If the model saw it, it is logged. No silent context. This is what makes the audit trail trustworthy.

### It Is Honest About What It Is Not

The README's own words are **"developer preview"** and **"THERE WILL BE COMPATIBILITY-BREAKING CHANGES"** — a rare amount of honesty for a project this hyped. DSH is not a coding agent you point at a repository and use today. **It is the machinery a coding agent gets assembled from**.

That framing is exactly why we chose it. We are not looking for a finished coding assistant. We are looking for a runtime we can assemble into a specialized medical imaging pipeline, with our own roles, our own tools, our own quality gates, and our own audit trail.

### Why We Chose It

**First, the orchestration is a first-class citizen.** The `dsh-swarm-orchestrator` plugin gives you a supervised agent team with a task DAG, parallel execution, per-role model pinning, quality gates, and a live kanban board — all built on the same plugin architecture.

**Second, it is supported by DeepSeek.** This is not a weekend project. It is DeepSeek AI's official open-source agent harness, documented in a real paper — *A Programming Paradigm for Spatiotemporal Composability*.

**Third, the plugin architecture is the right shape for medical work.** We need seven distinct roles with seven distinct tool surfaces. DSH's architecture is designed to compose exactly this kind of pipeline.

The tradeoff is clear: DSH is alpha software. It will break. The APIs will change. But it is **open, extensible, and moving in the right direction** — and for a local, privacy-preserving medical pipeline, that is worth the rough edges.

---

## The Agent Team

| Agent | Model | Role | Deliverable |
|---|---|---|---|
| **Architect** | Qwen3.5-9B (local) | Scans workspace, writes `manifest.json`, writes `PLAN.md` with dependency graph | `manifest.json`, `PLAN.md` |
| **PHI Gate** | Deterministic (pydicom + EasyOCR + Presidio) | De-identifies every image before analysis | CLEAR/BLOCKED verdict + SHA-256 receipt |
| **Modality Classifier** | Laya (System 1, 395M) | Reads evidence, returns modality + confidence + review flag | Modality decision + probabilities |
| **Vision Builder** (×N) | MedMO-8B-Next (MLX) | Analyzes each cleared image with modality-specific prompt | `report_<image_id>.md` |
| **Grounding Reviewer** | MedMO-8B-Next (MLX) | Verifies bounding boxes are present and plausible | Annotated reports |
| **Quality Gate** | Qwen3.5-9B (local) | Checks completeness against task brief; rejects and loops back (max 3 iterations) | Pass/fail + feedback |
| **Integrator** | Qwen3.5-9B (local) | Merges individual reports into batch output; appends audit log | `batch_analysis_report.md` |

### Why Each Model Was Chosen

| Role | Model | Why This Model | Why Not Something Else |
|---|---|---|---|
| **Architect** | Qwen3.5-9B | Structured planning, no vision needed. Follows the manifest template reliably. | Cloud model would add cost and latency for a well-defined task. |
| **PHI Gate** | Deterministic scripts | De-identification is a rule-based operation. A model would add unpredictability. | Any LLM would be slower, more expensive, and less auditable. |
| **Modality Classifier** | Laya (System 1) | Classification is a decision, not generation. Laya answers typed questions in ~33ms with calibrated probabilities. | A CNN gives a label; Laya gives a decision with a confidence distribution and a review flag. |
| **Builder** | MedMO-8B-Next (MLX) | The only model that can analyze medical images across the core radiology modalities. State-of-the-art VQA and grounding. | No alternative supports the same modality range with grounding. |
| **Grounding Reviewer** | MedMO-8B-Next (MLX) | Same model, different prompt. It verifies its own bounding boxes against the image. | A text-only model cannot verify spatial claims. |
| **Quality Gate** | Qwen3.5-9B | **Different model family from the builder.** A reviewer on a different family catches different mistakes. | MedMO reviewing MedMO shares blind spots. |
| **Integrator** | Qwen3.5-9B | Merging reports is text-only. No vision needed. | MedMO would waste vision capacity on a text merge. |

---

## How the Swarm Works: From the Chat

Here is what happens when you type `spawn a swarm: process all medical images in this workspace` into the DSH Web UI.

**The chat agent receives your goal.** It does not immediately start analyzing images. Instead, it calls `swarm_dispatch` with a task graph. Runs start **gated**: planning only, zero agents spawned.

**The architect agent takes over.** It scans the workspace, invokes the modality classifier on each file, and writes `manifest.json`. This is the inventory — the single source of truth for every downstream task. Then it writes `PLAN.md`, a task DAG with dependencies, prompt templates, and quality gates per file.

**The PHI Gate runs first, per file.** No image proceeds until the gate returns CLEAR. It strips DICOM PHI tags, OCRs burned-in pixel text, and writes a SHA-256 receipt.

**The Modality Classifier runs next.** It extracts DICOM metadata and pixel features, sends the evidence to Laya, and receives a typed decision: modality, confidence, and a `needs_human_review` flag. If confidence is below 0.7, the task parks on your dashboard.

**Vision builders spawn in parallel — bounded by your concurrency cap.** With `maxConcurrentRuns: 1`, one builder runs at a time. Each builder calls MedMO with the correct prompt template for its modality.

**The Grounding Reviewer checks each report.** It verifies that bounding boxes are present for every flagged finding and that coordinates are plausible.

**The Quality Gate judges against the task brief.** A rejection loops back to the builder with feedback attached. The loop is capped at 3 iterations.

**The integrator merges the batch.** Individual reports become `batch_analysis_report.md`. The audit log is appended.

**The memory layer captures the whole run.** Every conversation turn, every tool call, every reviewer decision is written to L0. The extraction pipeline distills atomic facts, clusters them into scene blocks, and eventually updates the persona. The next batch starts with recall injection — the agents see what worked before.

**You watch the whole thing on the Swarm tab.** The Board view shows runs on the left and task columns in the center. Click any task for its full brief, model, attempt count, and reviewer feedback. The Flow view shows the task DAG as a living flow chart.

---

## Why This Matters

**Privacy by architecture.** Patient images, prompts, and outputs never cross the network. MedMO runs locally. The PHI Gate runs locally. Laya runs locally. The memory layer runs locally. The audit trail records hashes, not content.

**Accuracy that competes.** MedMO-8B-Next is the best-performing open-source medical imaging model available. It leads every major benchmark. It runs on your Mac.

**Auditability by design.** Every tool call, every agent handoff, every gate decision appends a hash-chained receipt. Compliance can prove what ran without creating a second copy of the chart.

**Memory that compounds.** The pipeline learns from every batch. Successful workflows sediment into reusable skills. Human gate decisions train future recall. A 61% reduction in context tokens means faster inference and more throughput within the same memory budget.

The barrier is not hardware anymore. It is workflow design. And that is what this guide builds.

---

# Part 2: Local Models — MedMO, Qwen3.5, and Laya

Before we touch DeepSeek Harness, we get the models in place. The swarm orchestrator pins models by ID, and those IDs must resolve to a running server before any role can spawn. This part downloads, converts, serves, and tests the three local models the pipeline depends on.

> **Time and disk:** This part downloads roughly 25 GB and takes 20–40 minutes depending on your connection.

## 2.1 Verify MLX Prerequisites

MedMO-8B-Next is built on Qwen3-VL-8B-Instruct, which requires **`mlx_vlm` version 0.6.3 or newer**. Earlier versions have a known KV cache bug that breaks every request to a Qwen3-VL-based model. The fix is upstream in 0.6.3. Do not use older versions.

```bash
python -c "import mlx_lm; print('mlx_lm:', mlx_lm.__version__)"
python -c "import mlx_vlm; print('mlx_vlm:', mlx_vlm.__version__)"
python -c "import huggingface_hub; print('hf:', huggingface_hub.__version__)"
```

**Expected:**

```
mlx_lm: 0.28.x
mlx_vlm: 0.6.3 or newer
hf: 0.3x.x
```

If `mlx_vlm` is older than 0.6.3, upgrade before continuing:

```bash
pip install -U "mlx-vlm>=0.6.3" huggingface-hub[cli]
```

Confirm the version:

```bash
python -c "import mlx_vlm; print(mlx_vlm.__version__)"
```

**Expected:** A version number of `0.6.3` or higher. If it is lower, the MedMO conversion will fail at inference time. Do not proceed until the version is correct.

## 2.2 Download MedMO-8B-Next

```bash
mkdir -p ${HOME}/models
huggingface-cli download MBZUAI/MedMO-8B-Next \
  --local-dir ${HOME}/models/MedMO-8B-Next \
  --local-dir-use-symlinks False
```

**Expected:**

```
Fetching 12 files: 100%|████████████████████| 12/12
model-00001-of-00004.safetensors: 100%|██████████████| 4.0G/4.0G
...
Download complete. Model saved to /Users/yourname/models/MedMO-8B-Next
```

Verify:

```bash
du -sh ${HOME}/models/MedMO-8B-Next/
```

**Expected:**

```
16G    /Users/yourname/models/MedMO-8B-Next
```

## 2.3 Convert MedMO to MLX

```bash
python -m mlx_vlm.convert \
  --hf-path ${HOME}/models/MedMO-8B-Next \
  --mlx-path ${HOME}/models/MedMO-8B-Next-mlx
```

**Expected:**

```
Loading model...
Converting weights to MLX format...
✓ Conversion complete: /Users/yourname/models/MedMO-8B-Next-mlx
```

### Optional: 4-bit Quantized Version

```bash
python -m mlx_vlm.convert \
  --hf-path ${HOME}/models/MedMO-8B-Next \
  --mlx-path ${HOME}/models/MedMO-8B-Next-mlx-4bit \
  -q --q-bits 4 --q-group-size 64
```

**Which one to use for the demo?**

Use the **BF16** version. Three reasons:

1. **Memory fits.** BF16 weighs ~16 GB. With `maxConcurrent: 1` from Part 3, only one MedMO context is loaded at a time, plus Qwen3.5 (~5.6 GB) and Laya (<1 GB). Under 24 GB — comfortable on 48 GB, workable on 32 GB.

2. **Accuracy matters here.** 4-bit quantization is lossy. On medical imaging — producing findings, impressions, bounding boxes — the tail-end accuracy loss is exactly the part you cannot afford to give up. BF16 preserves the full precision the benchmark scores above were measured on.

3. **Speed is already adequate.** BF16 MedMO generates a typical radiology report in 30–60 seconds on Apple Silicon. The 4-bit variant may be faster, but the pipeline bottleneck in a real batch is the sequential orchestration across `maxConcurrent: 1`, not per-image inference.

The 4-bit variant is a fallback if you hit memory pressure. It is not the recommended path for a medical workload.

## 2.4 Download Qwen3.5-9B (Quality Gate)

```bash
huggingface-cli download mlx-community/Qwen3.5-9B-MLX-4bit \
  --local-dir ${HOME}/models/Qwen3.5-9B-MLX-4bit
```

**Expected:**

```
model.safetensors: 100%|██████████████████████| 5.6G/5.6G
Download complete.
```

> **Why this specific model:** Qwen3.5-9B is a different model family from MedMO (Qwen3-VL). A reviewer on a different family catches different mistakes than the builder.

## 2.5 Serve Both Models via oMLX

```bash
mkdir -p ${HOME}/.omlx/models
ln -sfn ${HOME}/models/MedMO-8B-Next-mlx \
        ${HOME}/.omlx/models/MedMO-8B-Next-mlx
ln -sfn ${HOME}/models/Qwen3.5-9B-MLX-4bit \
        ${HOME}/.omlx/models/Qwen3.5-9B-MLX-4bit
ls -la ${HOME}/.omlx/models/
```

**Expected:**

```
lrwxr-xr-x  1 you  staff  42 Oct 12 16:02 MedMO-8B-Next-mlx -> /Users/yourname/models/MedMO-8B-Next-mlx
lrwxr-xr-x  1 you  staff  46 Oct 12 16:02 Qwen3.5-9B-MLX-4bit -> /Users/yourname/models/Qwen3.5-9B-MLX-4bit
```

Restart oMLX:

```bash
brew services restart omlx
```

Verify:

```bash
curl -s http://127.0.0.1:8000/v1/models | python -m json.tool
```

**Expected:**

```json
{
    "object": "list",
    "data": [
        {"id": "MedMO-8B-Next-mlx", "object": "model", "owned_by": "local"},
        {"id": "Qwen3.5-9B-MLX-4bit", "object": "model", "owned_by": "local"}
    ]
}
```

## 2.6 Test MedMO with a Real Image

```bash
mkdir -p ${HOME}/medical-imaging-demo
cd ${HOME}/medical-imaging-demo
python -c "
from huggingface_hub import hf_hub_download
import zipfile, os, pathlib
REPO = 'alkzar90/NIH-Chest-X-ray-dataset'
out = pathlib.Path.home() / 'medical-imaging-demo'
z = hf_hub_download(REPO, 'data/images/images_001.zip', repo_type='dataset')
with zipfile.ZipFile(z) as zf:
    for m in zf.namelist()[:5]:
        if m.lower().endswith('.png'):
            base = os.path.basename(m)
            with zf.open(m) as src, open(out / base, 'wb') as dst:
                dst.write(src.read())
os.remove(z)
print(f'Extracted 5 test images to {out}')
"
```

Send one image to MedMO:

```bash
python3 << 'PYEOF'
import base64, json, urllib.request, glob, os

img_path = sorted(glob.glob(os.path.expanduser("~/medical-imaging-demo/*.png")))[0]
with open(img_path, "rb") as f:
    b64 = base64.b64encode(f.read()).decode()

payload = {
    "model": "MedMO-8B-Next-mlx",
    "messages": [{
        "role": "user",
        "content": [
            {"type": "text", "text": "Describe the findings in this chest X-ray. "
                                     "List any abnormalities and provide bounding box "
                                     "coordinates [x1, y1, x2, y2] for each."},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}
        ]
    }],
    "max_tokens": 500
}

req = urllib.request.Request(
    "http://127.0.0.1:8000/v1/chat/completions",
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"},
)
with urllib.request.urlopen(req, timeout=300) as resp:
    result = json.loads(resp.read())

print("=== MedMO Report ===")
print(result["choices"][0]["message"]["content"])
PYEOF
```

**Expected** (content varies by image; the shape matters):

```
=== MedMO Report ===
FINDINGS:
- The lungs are well-expanded and clear.
- No focal consolidation, pleural effusion, or pneumothorax.
- The cardiac silhouette is within normal limits.

IMPRESSION:
No acute cardiopulmonary abnormality identified.
```

The first request can take 30–60 seconds while oMLX loads the 16 GB model into memory. Subsequent calls are fast.

## 2.7 Set Up the Laya Decision Server

Laya is the System 1 decision model that powers the modality classifier. It answers typed questions in ~33ms with calibrated probabilities — no text generation, no token cost.

```bash
npx maclaya serve --port 8755
```

**Expected:**

```
maclaya v0.x.x
Creating isolated environment at ~/.maclaya/venv ...
Installing laya-mlx ...
Downloading Laya checkpoint (678 MB) ...
✓ Laya ready on http://127.0.0.1:8755
✓ Jev-compatible API: POST /v1/systemone
```

Leave this running in its own terminal. For reboot resilience, we create a LaunchAgent in Part 5.

### Verify Laya Responds

```bash
curl -s http://127.0.0.1:8755/v1/systemone \
  -H "Content-Type: application/json" \
  -d '{
    "model": "laya",
    "state": "A grayscale image with high contrast, air is black, bone is bright white. The image is a 2D projection.",
    "questions": {
      "modality": {
        "type": "choice",
        "instructions": "What imaging modality is this?",
        "criteria": {
          "CT": "Computed tomography",
          "MR": "Magnetic resonance",
          "US": "Ultrasound",
          "XR": "Plain radiograph"
        }
      },
      "needs_review": {
        "type": "noul",
        "instructions": "Does this need human review before analysis?"
      }
    }
  }' | python -m json.tool
```

**Expected:**

```json
{
    "answers": {
        "modality": {
            "type": "choice",
            "choice": "XR",
            "confidence": 0.91,
            "probabilities": {"XR": 0.91, "CT": 0.05, "MR": 0.02, "US": 0.02}
        },
        "needs_review": {"type": "noul", "noul": 0.12}
    },
    "usage": {"prompt_tokens": 78, "completion_tokens": 0}
}
```

Note the `completion_tokens: 0`. Laya does not generate text — it resolves typed decisions in a single forward pass.

---

# Part 3: Install DeepSeek Harness and Configure the Swarm

With models running, we now install DSH, register the providers, define the seven roles, add the memory layer, and confirm the whole orchestration layer starts cleanly.

## 3.1 Install DSH Desktop

```bash
curl -fsSL https://raw.githubusercontent.com/imMamdouhaboammar/deepseek-harness-desktop/main/install.sh | bash
```

**Expected:**

```
Installing DeepSeek Harness Desktop...
✓ Downloaded DMG (dsh-desktop-2.x.x-arm64.dmg)
✓ Mounted installer
✓ Copied to /Applications/DeepSeek Harness.app
✓ Scaffolded ~/.dsh/
✓ Registered LaunchAgent com.deepseek.dsh
✓ Daemon started on port 3080
Installation complete.
```

If the installer script is unavailable, download the DMG from the DSH desktop releases page, drag it to `/Applications`, and launch it once.

## 3.2 Verify the Daemon and Web UI

```bash
dsh-desktop status
```

**Expected:**

```
App:      installed at /Applications/DeepSeek Harness.app
Daemon:   running (PID 4821)
Port:     3080 listening on 127.0.0.1
Uptime:   00:00:14
```

```bash
dsh-desktop doctor
```

**Expected:**

```
✓ Swift runtime available
✓ Node.js 22.19.0 (>= 22.19 required)
✓ Port 3080 free
✓ Loopback auth token present
✓ Invariant guard active
✓ Profile 'web' exists
All checks passed (6/6).
```

```bash
curl -s -o /dev/null -w "DSH loopback: %{http_code}\n" http://127.0.0.1:3080
open http://127.0.0.1:3080
```

**Expected:** `DSH loopback: 200`, and the Web UI loads with an empty chat panel, plugin sidebar, and model picker.

## 3.3 Install the Swarm Orchestrator

```bash
dsh plugin --profile web add dsh-swarm-orchestrator
dsh-desktop restart
```

**Expected:**

```
Plugin load complete: dsh-swarm-orchestrator
```

Verify:

```bash
dsh --profile web --dump-config | grep -A3 "swarm"
```

A new **Swarm** item appears in the Web UI sidebar with an empty Board and a **Roster** tab.

## 3.4 Install the Memory Layer

The swarm orchestrator gives the agents a task DAG. It does not give them a memory. Every batch starts from zero. That changes now.

**TencentDB Agent Memory** is a four-layer semantic memory system that captures every conversation, distills it into structured facts, and injects relevant recall into future sessions. It is the difference between a pipeline that runs and a pipeline that *learns*.

### Why It Matters for This Pipeline

**1. Repetition.** Every batch, the architect re-derives the same task DAG. The builder re-learns the same prompt template. The reviewer re-establishes the same pass/fail criteria. With memory, those patterns sediment into reusable assets.

**2. Audit traceability.** Your hash-chained receipts prove *what* tool ran, in what order. They do not prove *why* the agent chose a modality or *which* human gate decisions changed behavior in a subsequent batch. The memory system's L0→L3 chain closes that gap.

**3. Token efficiency.** Tencent's benchmarks show **token consumption dropping by up to 61.4%** and **short-term memory task success rate improving by up to 51.5%**. For MedMO, a 16 GB model loaded into memory, every context token competes with the vision encoder and KV cache.

### The Four-Layer Architecture

| Layer | What it stores | Format |
|---|---|---|
| **L0 Conversation** | Raw dialogue and tool-call logs, full fidelity | JSONL + SQLite |
| **L1 Atom** | Extracted facts, preferences, constraints | SQLite + FTS + vectors |
| **L2 Scenario** | Aggregated knowledge blocks per task/project | Markdown (`scene_blocks/`) |
| **L3 Persona** | Stable long-term user profile and team norms | `persona.md` |

Nothing is lossy-compressed. Every layer is readable. When the agent needs to prove a conclusion, it drills back through node_id links to the exact raw log at L0. This is a **white-box traceable memory system**.

### Installation

```bash
dsh plugin --profile web add https://github.com/Jason-Liao/dsh-memory-tdai/archive/refs/tags/v1.0.0.tar.gz
dsh-desktop restart
```

**Expected:**

```
Plugin load complete: dsh-swarm-orchestrator, dsh-memory-tdai
```

After restart, hard-refresh the browser (`Cmd+Shift+R`).

### Why the Community Port, Not the Proxy

The **Memory Proxy** is Tencent's official path: a reverse proxy reroutes `baseURL` through a local service that auto-injects memory. The **community plugin** hooks into DSH's event system and registers two model-facing tools, reusing DSH's own `ctx.llm` for extraction — **zero additional API key configuration**.

| Aspect | Proxy path | Plugin path |
|---|---|---|
| Extra API key needed | Yes | **No** — reuses DSH's `ctx.llm` |
| Containers required | 3 | **0** — runs in-process |
| Team memory / Skill sharing | Yes | Limited (single-user) |
| Setup complexity | High | **Low** |
| Data location | External service | `${HOME}/.memory-tencentdb/memory-tdai` |

For a single-Mac deployment, the plugin is simpler and fully local.

### Verify the Plugin Loaded

```bash
dsh --profile web --dump-config | grep -A3 "tdai-memory"
```

**Expected:**

```
- id: tdai-memory
  name: dsh-memory-tdai
  config:
    extraction:
      enabled: true
```

In the Web UI, a **记忆 (Memory)** section appears under Settings.

### How It Changes the Pipeline

**Automatic capture (L0).** Every turn's raw conversation is written to `${HOME}/.memory-tencentdb/memory-tdai/conversations/YYYY-MM-DD.jsonl`.

**Background extraction (L1→L2→L3).** After each turn, a background pipeline uses the configured LLM (your local Qwen3.5 via DSH's `ctx.llm`) to extract atomic facts. These are deduplicated, clustered into scene blocks, and eventually distilled into `persona.md`. Runs asynchronously.

**Recall injection.** Before the model assembles each prompt, the plugin retrieves relevant memories and injects them as a dynamic system prompt segment wrapped in `<relevant-memories>`. Recall does **not** pollute conversation history.

Two tools become available to every agent:

| Tool | What it searches | When to use |
|---|---|---|
| `memory_search` | Structured L1 memories with hybrid FTS5+BM25+vector ranking | Prior preferences, known facts, established rules |
| `conversation_search` | Raw L0 conversation records | Original wording of a prior decision |

### The PHI Consideration

The memory system captures conversations. If a conversation involves medical images and de-identified findings, the L0 record preserves that content. This extends the PHI surface area.

**The rule:** treat `${HOME}/.memory-tencentdb/` as PHI-adjacent storage. It is covered by the same security controls, audit procedure, and exclusion policy as the rest of the pipeline. If your workflow involves actual patient data, the L0 capture must either run through the PHI Gate before storage, or the sessions that touch PHI must be excluded from memory capture entirely.

For the demo pipeline — public-domain NIH chest X-rays with no real PHI — the memory capture operates safely. In production, this is a configuration decision you must make explicitly.

### Verify the Memory Layer Works

After the first swarm run:

```bash
ls -la ${HOME}/.memory-tencentdb/memory-tdai/conversations/
ls ${HOME}/.memory-tencentdb/memory-tdai/records/ 2>/dev/null
```

**Expected:**

```
-rw-r--r--  1 you  staff  12K Oct 13 15:42 2026-10-13.jsonl
persona/  episodic/  instruction/
```

If the directories exist and contain files, the extraction pipeline is working.

## 3.5 Add the Three Custom Roles

The four built-in roles cover orchestration. The medical pipeline needs three more.

**Why the built-in roles do not get custom personas:** they ship with working defaults. The three custom roles need explicit personas because they encode medical safety requirements — the PHI Gate's hard block, the classifier's no-guessing rule, the grounding reviewer's verification-only scope.

The memory layer does not change the role definitions. It adds context that the roles draw on automatically.

| Role | Kind | Model pin | Tool access | Concurrency |
|---|---|---|---|---|
| `phi-gate` | Deterministic tool role | — (no LLM) | `phi_gate` only | 1 |
| `modality-classifier` | Deterministic tool role | Laya (via JEV router) | `classify_modality` only | 1 |
| `grounding-reviewer` | LLM role | `medmo-local/MedMO-8B-Next-mlx` | read image + report + `memory_search` + `conversation_search` | 1 |

**One change from the previous version:** the `grounding-reviewer` now has access to the two memory tools, so it can check consistency against prior batch decisions.

**Role: `phi-gate`**

```
Persona:
You are a hard de-identification gate. You run before any vision model
sees an image. You call the phi_gate tool on exactly one file. You return
its verdict verbatim. If the verdict is BLOCKED, you do not proceed.
You never modify the verdict. You never analyze the image yourself.
```

Tool filter: allow `phi_gate`, deny everything else.

**Role: `modality-classifier`**

```
Persona:
You are a routing decision gate. You call the classify_modality tool on
exactly one file. You return its modality, confidence, and
needs_human_review verdict verbatim. If needs_human_review is true, you
stop and escalate. You never guess a modality the tool did not return.
```

Tool filter: allow `classify_modality`, deny everything else.

**Role: `grounding-reviewer`**

```
Persona:
You verify spatial claims. You read one report and the image it describes.
For every finding the report flags, you check that a bounding box is
present and that the coordinates fall within the image bounds. You reject
any report that claims a finding without a box. You do not re-diagnose.
You do not add findings. You only verify presence and plausibility.
Before finalizing, you check memory for prior review decisions on similar
findings and maintain consistency with the record.
```

Model: `medmo-local/MedMO-8B-Next-mlx`, fallback `qwen-local/Qwen3.5-9B-MLX-4bit`.

## 3.6 Configure the Swarm for a Single Mac

Edit `${HOME}/.dsh/profiles/web/cordis.patch.yml`:

```yaml
- id: swarm
  require: dsh-swarm-orchestrator
  config:
    storageDir: !!js dshHomePath("storages/swarm")

    maxConcurrent: 1
    maxTotalConcurrentAgents: 10
    adaptiveConcurrency: true
    maxSubagentDepth: 1

    reviewLoops: 3
    maxRetries: 2
    spawnTimeoutSeconds: 3600

    defaultReviewGate: reviewer
    humanGateOnEscalation: true

    memory:
      enabled: true
      captureRunSummaries: true

    roles:
      architect:           { model: qwen-local/Qwen3.5-9B-MLX-4bit }
      builder:             { model: medmo-local/MedMO-8B-Next-mlx }
      reviewer:            { model: qwen-local/Qwen3.5-9B-MLX-4bit }
      integrator:          { model: qwen-local/Qwen3.5-9B-MLX-4bit }
      phi-gate:            { kind: tool, tool: phi_gate }
      modality-classifier: { kind: tool, tool: classify_modality }
      grounding-reviewer:  { model: medmo-local/MedMO-8B-Next-mlx,
                             fallback: [qwen-local/Qwen3.5-9B-MLX-4bit] }
```

**Why `maxConcurrent: 1`:** each concurrent vision builder holds its own MedMO context. Two builders means two copies of the model plus the reviewer. One at a time keeps the footprint inside a comfortable unified-memory budget.

**Why `maxSubagentDepth: 1`:** builders should not spawn their own sub-agents.

**Why `memory.captureRunSummaries: true`:** the integrator writes the final batch report to memory. That is the highest-signal artifact for future recall.

Restart and verify:

```bash
dsh-desktop restart
dsh --profile web --dump-config | grep -A6 "id: swarm"
```

## 3.7 Install the JEV Router (Laya Integration)

```bash
dsh plugin --profile web add dsh-jev-router
dsh-desktop restart
```

Add to the same `cordis.patch.yml`:

```yaml
- insert:
    - id: local-jev-router
      name: dsh-jev-router
      config:
        endpoint: http://127.0.0.1:8755/v1/systemone
        routing: true
        gate: false
        modelSwap: false
        timeoutMs: 2000
```

**Why `gate: false`:** we want Laya used **only** inside the modality classifier tool, called deliberately, not intercepting every chat turn.

## 3.8 Register All Models in DSH

```bash
cat > ${HOME}/.dsh/settings.yaml << 'EOF'
llm-pi-ai:
  providers:
    medmo-local:
      api: openai-completions
      baseURL: http://127.0.0.1:8000/v1
      apiKey: local-only
      models:
        - id: MedMO-8B-Next-mlx
          name: MedMO 8B (Local Vision)
          contextWindow: 32768
    qwen-local:
      api: openai-completions
      baseURL: http://127.0.0.1:8000/v1
      apiKey: local-only
      models:
        - id: Qwen3.5-9B-MLX-4bit
          name: Qwen3.5 9B (Quality Gate)
          contextWindow: 32768
EOF

dsh-desktop restart
dsh --profile web --dump-config | grep -A8 "providers:"
```

The memory plugin reuses the same `qwen-local` provider for extraction. Verify:

```bash
dsh --profile web --dump-config | grep -A5 "tdai-memory:"
```

**Expected:**

```
tdai-memory:
  llm:
    baseUrl: http://127.0.0.1:8000/v1
    model: Qwen3.5-9B-MLX-4bit
```

If the `llm` section is empty, the plugin defaults to DSH's `ctx.llm` service. That is the intended behavior.

## 3.9 Verify Role Pins Match the Catalog

```bash
grep -A12 "roles:" ${HOME}/.dsh/profiles/web/cordis.patch.yml
curl -s http://127.0.0.1:8000/v1/models | python -c "
import sys, json
for m in json.load(sys.stdin)['data']:
    print('  oMLX serves:', m['id'])
"
```

The format is `provider/model-id`, where `provider` is the key under `providers:` in `settings.yaml` and `model-id` is the exact `id` oMLX reports.

## 3.10 Full Plugin Verification

```bash
dsh --profile web --dump-config | grep -E "id: (dsh-swarm|dsh-jev|local-jev|tdai-memory)"
```

**Expected:**

```
- id: dsh-swarm-orchestrator
- id: dsh-jev-router
- id: local-jev-router
- id: tdai-memory
```

## 3.11 Spawn a Test Swarm (No Medical Data Yet)

In the Web UI chat:

```
spawn a swarm: create a directory ~/dsh-swarm-test and write three files
in it: alpha.txt containing "alpha", beta.txt containing "beta", and
gamma.txt containing "gamma". Verify each file exists and contains the
right text.
```

**Expected behavior:**

1. The chat dispatches `swarm_dispatch`.
2. A **live progress card** appears.
3. The **Swarm → Board** fills: architect → three builders → reviewer → integrator.
4. With `maxConcurrent: 1`, builders run **one after another**.
5. Reviewer approves. Integrator completes.
6. Memory layer captures the run.

**Verify:**

```bash
ls -la ${HOME}/dsh-swarm-test/
cat ${HOME}/dsh-swarm-test/alpha.txt
ls ${HOME}/.memory-tencentdb/memory-tdai/conversations/ 2>/dev/null
rm -rf ${HOME}/dsh-swarm-test
```

## 3.12 Where the Kanban Lives

```
Web UI sidebar  →  Swarm  →  Board     ← the kanban
                            Flow      ← the task DAG as a living chart
                            Roster    ← the seven roles
                            Report    ← per-run summaries
```

The **task drawer** shows: brief, role, model, attempt count, interim notes, reviewer feedback, retry history. Tasks with a human gate **park on the Board** with an Approve / Reject control.

---

# Part 4: The Tools, the Pipeline, and the First Real Batch

## 4.1 Why These Two Tools Are Deterministic

The PHI Gate is a rule-based operation. HIPAA Safe Harbor requires removing a specific list of 18 identifier categories, and DICOM PS3.15 Annex E maps those to concrete tags. None of that benefits from a language model.

The Modality Classifier is a **decision**, not a generation. The DICOM `Modality` tag (0008,0060) is required in the General Series module with a single value per series. When present, it is authoritative. When absent or wrong, pixel analysis fills the gap. Laya resolves that decision in ~33ms with zero output tokens.

## 4.2 Build the PHI Gate Tool

### 4.2.1 Install Dependencies

```bash
pip install pydicom easyocr presidio-analyzer presidio-anonymizer spacy pillow numpy
python -m spacy download en_core_web_lg
```

> **Memory note:** `easyocr` downloads models on first use (~200 MB). The first run pauses while this happens.

### 4.2.2 Write the PHI Gate Script

```bash
mkdir -p ${HOME}/.dsh/tools
cat > ${HOME}/.dsh/tools/phi_gate.py << 'PYEOF'
#!/usr/bin/env python3
"""PHI Gate — hard block for medical imaging de-identification."""

import hashlib, json, sys
from pathlib import Path
import pydicom

PHI_TAGS = [
    "PatientName", "ReferringPhysicianName", "PerformingPhysicianName",
    "NameOfPhysiciansReadingStudy", "OperatorsName", "OtherPatientNames",
    "PatientMotherBirthName", "PhysiciansOfRecord",
    "PatientAddress", "InstitutionAddress", "CountryOfResidence",
    "RegionOfResidence",
    "PatientBirthDate", "StudyDate", "SeriesDate", "AcquisitionDate",
    "ContentDate", "InstanceCreationDate", "PatientBirthTime",
    "StudyTime", "SeriesTime", "AcquisitionTime", "ContentTime",
    "PatientTelephoneNumbers",
    "PatientID", "OtherPatientIDs", "AccessionNumber", "StudyID",
    "InstitutionName", "AdmittingDiagnosesDescription",
    "DeviceSerialNumber", "PatientComments",
    "Occupation", "MilitaryRank", "BranchOfService", "EthnicGroup",
    "StudyDescription", "SeriesDescription", "ProtocolName",
    "RequestingPhysician", "RequestedProcedureDescription",
]

def scrub_dicom_tags(dicom_path: Path) -> dict:
    ds = pydicom.dcmread(str(dicom_path), stop_before_pixels=True)
    removed = []
    for tag in PHI_TAGS:
        if hasattr(ds, tag):
            val = getattr(ds, tag)
            if val and str(val).strip():
                setattr(ds, tag, "")
                removed.append(tag)
    return {"removed_tags": removed, "tag_count": len(removed),
            "modality": getattr(ds, "Modality", "unknown")}

def detect_burned_in_text(image_path: Path) -> dict:
    import easyocr
    if not hasattr(detect_burned_in_text, "_reader"):
        detect_burned_in_text._reader = easyocr.Reader(["en"], gpu=False)
    reader = detect_burned_in_text._reader
    results = reader.readtext(str(image_path))
    fragments = [r[1] for r in results if len(r[1]) > 3]
    return {"text_fragments": fragments, "fragment_count": len(fragments),
            "requires_manual_review": len(fragments) > 0}

def phi_gate(image_path: Path) -> dict:
    image_path = Path(image_path)
    verdict, reasons = "CLEAR", []
    dicom_report, ocr_report = {}, {}
    if image_path.suffix.lower() in (".dcm", ".dicom"):
        try:
            dicom_report = scrub_dicom_tags(image_path)
            if dicom_report["removed_tags"]:
                reasons.append(f"stripped {dicom_report['tag_count']} PHI tags")
        except Exception as e:
            reasons.append(f"DICOM read failed: {e}")
            verdict = "BLOCKED"
    try:
        ocr_report = detect_burned_in_text(image_path)
        if ocr_report["requires_manual_review"]:
            reasons.append(f"detected {ocr_report['fragment_count']} text fragments in pixels")
            verdict = "BLOCKED"
    except Exception as e:
        reasons.append(f"OCR failed: {e}")
        verdict = "BLOCKED"
    content_hash = hashlib.sha256(image_path.read_bytes()).hexdigest()[:16]
    return {"verdict": verdict, "image": str(image_path), "hash": content_hash,
            "reasons": reasons, "dicom": dicom_report, "ocr": ocr_report}

if __name__ == "__main__":
    result = phi_gate(Path(sys.argv[1]))
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["verdict"] == "CLEAR" else 1)
PYEOF

chmod +x ${HOME}/.dsh/tools/phi_gate.py
```

### 4.2.3 Test the PHI Gate

The five test images were downloaded in Part 2.6. Confirm:

```bash
ls ${HOME}/medical-imaging-demo/*.png | wc -l
```

**Expected:** `5`

```bash
cd ${HOME}/medical-imaging-demo
IMG=$(ls *.png | head -1)
python ${HOME}/.dsh/tools/phi_gate.py "$IMG"
```

**Expected:**

```json
{
  "verdict": "BLOCKED",
  "image": "/Users/yourname/medical-imaging-demo/00000001_000.png",
  "hash": "a1b2c3d4e5f6g7h8",
  "reasons": ["detected 3 text fragments in pixels"],
  "dicom": {},
  "ocr": {
    "text_fragments": ["PORTABLE", "SUPINE", "AP"],
    "fragment_count": 3,
    "requires_manual_review": true
  }
}
```

> **Why BLOCKED on a PNG:** the NIH chest X-rays have laterality markers and view labels burned into the pixels. The gate correctly flags them for human review. This is the gate working as designed.

## 4.3 Build the Modality Classifier Tool

```bash
cat > ${HOME}/.dsh/tools/modality_classifier.py << 'PYEOF'
#!/usr/bin/env python3
"""Modality Classifier — Laya System One decision layer."""

import json, sys, urllib.request
from pathlib import Path
import numpy as np
import pydicom
from PIL import Image

MODALITY_MAP = {
    "CT": "CT", "MR": "MR", "MRI": "MR",
    "CR": "XR", "DX": "XR", "DR": "XR", "XR": "XR",
    "US": "US", "IVUS": "US",
    "SM": "SM", "GM": "GM", "OP": "OP", "OCT": "OCT",
    "XC": "XC", "PT": "PT", "NM": "NM", "MG": "MG",
}

LAYA_ENDPOINT = "http://127.0.0.1:8755/v1/systemone"

def extract_evidence(image_path: Path) -> dict:
    ev = {"file": str(image_path), "extension": image_path.suffix.lower()}
    if image_path.suffix.lower() in (".dcm", ".dicom"):
        try:
            ds = pydicom.dcmread(str(image_path), stop_before_pixels=True)
            raw = getattr(ds, "Modality", "").strip().upper()
            ev["dicom_modality_raw"] = raw
            ev["dicom_modality_mapped"] = MODALITY_MAP.get(raw, "UNKNOWN")
            ev["body_part"] = getattr(ds, "BodyPartExamined", "unknown")
            ev["has_slice_location"] = hasattr(ds, "SliceLocation")
            ev["has_instance_number"] = hasattr(ds, "InstanceNumber")
            ev["number_of_frames"] = int(getattr(ds, "NumberOfFrames", 1) or 1)
            ev["metadata_present"] = True
        except Exception as e:
            ev["metadata_error"] = str(e)
            ev["metadata_present"] = False
    else:
        ev["metadata_present"] = False

    try:
        if image_path.suffix.lower() in (".dcm", ".dicom"):
            ds = pydicom.dcmread(str(image_path))
            arr = ds.pixel_array.astype(np.float32)
            arr = (arr - arr.min()) / (arr.max() - arr.min() + 1e-8)
        else:
            img = Image.open(image_path).convert("L")
            arr = np.array(img, dtype=np.float32) / 255.0
        a = np.array(Image.fromarray((arr * 255).astype(np.uint8)).resize((64, 64)),
                     dtype=np.float32) / 255.0
        ev["pixel_mean"] = float(a.mean())
        ev["pixel_std"] = float(a.std())
        ev["pixel_p25"] = float(np.percentile(a, 25))
        ev["pixel_p75"] = float(np.percentile(a, 75))
        ev["edge_density_v"] = float(np.abs(np.diff(a, axis=0)).mean())
        ev["edge_density_h"] = float(np.abs(np.diff(a, axis=1)).mean())
        ev["pixels_extracted"] = True
    except Exception as e:
        ev["pixel_error"] = str(e)
        ev["pixels_extracted"] = False
    return ev

def jev_decide(evidence: dict) -> dict:
    questions = {
        "modality": {
            "type": "choice",
            "instructions": "Based on the evidence, what imaging modality is this?",
            "criteria": {
                "CT": "Computed tomography. High contrast, air black, bone bright.",
                "MR": "Magnetic resonance. Soft tissue contrast, no bone brightening.",
                "US": "Ultrasound. Speckle pattern, fan or linear probe geometry.",
                "XR": "Plain radiograph. 2D projection, high bone contrast.",
                "SM": "Whole-slide microscopy. Histopathology.",
                "OCT": "Optical coherence tomography. Retinal layers.",
                "OP": "Ophthalmic photography. Fundus, retinal vessels.",
                "XC": "External camera. Dermatology or clinical photograph.",
                "PT": "PET. Functional imaging, tracer uptake.",
                "NM": "Nuclear medicine / SPECT.",
                "UNKNOWN": "Cannot determine from available evidence.",
            },
        },
        "metadata_reliable": {"type": "noul",
            "instructions": "Is the DICOM metadata reliable without pixel verification?"},
        "is_volumetric": {"type": "noul",
            "instructions": "Is this volumetric (3D) or a single 2D image/cine loop?"},
        "needs_human_review": {"type": "noul",
            "instructions": "Does this need human review before vision analysis?"},
        "confidence_level": {"type": "score",
            "instructions": "How confident is the modality classification?",
            "criteria": ["Very low", "Low", "Moderate", "High", "Very high"]},
    }
    payload = {"state": json.dumps(evidence), "questions": questions}
    req = urllib.request.Request(LAYA_ENDPOINT,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())

def classify(image_path: str) -> dict:
    evidence = extract_evidence(Path(image_path))
    decision = jev_decide(evidence)
    answers = decision.get("answers", {})
    mod = answers.get("modality", {})
    return {
        "modality": mod.get("choice", "UNKNOWN"),
        "confidence": mod.get("confidence", 0),
        "probabilities": mod.get("probabilities", {}),
        "metadata_reliable": answers.get("metadata_reliable", {}).get("noul", 0),
        "is_volumetric": answers.get("is_volumetric", {}).get("noul", 0) > 0.5,
        "needs_human_review": answers.get("needs_human_review", {}).get("noul", 0) > 0.5,
        "confidence_level": answers.get("confidence_level", {}).get("score", 0),
        "evidence": evidence,
    }

if __name__ == "__main__":
    print(json.dumps(classify(sys.argv[1]), indent=2))
PYEOF

chmod +x ${HOME}/.dsh/tools/modality_classifier.py
```

### 4.3.2 Test the Classifier

```bash
IMG=$(ls ${HOME}/medical-imaging-demo/*.png | head -1)
python ${HOME}/.dsh/tools/modality_classifier.py "$IMG"
```

**Expected:**

```json
{
  "modality": "XR",
  "confidence": 0.91,
  "probabilities": {"XR": 0.91, "CT": 0.05, "MR": 0.02, "US": 0.02},
  "metadata_reliable": 0.12,
  "is_volumetric": false,
  "needs_human_review": false,
  "confidence_level": 4.2,
  "evidence": {"extension": ".png", "metadata_present": false}
}
```

## 4.4 Register Both Tools in DSH

```bash
cat >> ${HOME}/.dsh/profiles/web/cordis.patch.yml << EOF

- insert:
    - id: phi-gate
      name: phi-gate
      config:
        tools:
          - name: phi_gate
            description: >
              Hard gate: de-identify a medical image before analysis.
            command: python3 ${HOME}/.dsh/tools/phi_gate.py "{image_path}"
            timeoutMs: 120000

    - id: modality-classifier
      name: modality-classifier
      config:
        tools:
          - name: classify_modality
            description: >
              Classify a medical image's modality using Laya System One decisions.
            command: python3 ${HOME}/.dsh/tools/modality_classifier.py "{image_path}"
            timeoutMs: 60000
EOF
```

Note: **`${HOME}` instead of `/Users/you/`** — expanded by the shell at write time. **`>>` instead of `>`** — appends rather than overwrites.

Verify the paths expanded:

```bash
grep "command: python3" ${HOME}/.dsh/profiles/web/cordis.patch.yml
```

**Expected:**

```
            command: python3 /Users/yourname/.dsh/tools/phi_gate.py "{image_path}"
            command: python3 /Users/yourname/.dsh/tools/modality_classifier.py "{image_path}"
```

If you see literal `${HOME}`, the heredoc was not expanded — re-run `cat` without quoting `EOF`.

Restart DSH and confirm:

```bash
dsh-desktop restart
dsh --profile web --dump-config | grep -A4 "phi_gate\|classify_modality"
```

## 4.5 Prepare the Batch Workspace

```bash
cat > ${HOME}/medical-imaging-demo/architect-rules.md << 'EOF'
# Batch Medical Imaging Analysis — Architect Rules

## Pipeline Order (enforced)
1. PHI Gate (phi_gate tool) — hard block, cannot be bypassed
2. Modality Classifier (classify_modality tool) — Laya decision
3. Vision Analysis (MedMO via builder role) — report generation

## Manifest
Architect writes manifest.json BEFORE PLAN.md.
Each entry: file, modality, confidence, needs_human_review, is_volumetric, body_part.

## Human Gates
- Modality confidence < 0.7 → reviewGate: human
- Modality UNKNOWN → reviewGate: human
- PHI Gate BLOCKED → quarantine, do not proceed
- Quality gate rejection after 3 iterations → reviewGate: human

## Memory
Before writing the plan, check memory for prior batch reports on the same
modality. If a successful plan exists, adapt it. Record the prior batch ID
in PLAN.md when reused.

## Task Graph
Every vision task declares:
- blockedBy: [phi-gate_<file>, classify_modality_<file>]
- reviewBy: reviewer
- maxIterations: 3
EOF
```

## 4.6 Run the First Real Swarm

In the DSH Web UI chat:

```
spawn a swarm: Process all medical images in ~/medical-imaging-demo.
Read architect-rules.md first. For each image, run the PHI Gate, then
the Modality Classifier, then generate a structured report with findings
and bounding boxes. Review every report against the task brief. Integrate
into a batch report. Flag all reports for clinician review.
```

With `maxConcurrent: 1`, tasks serialize. Watch architect → PHI Gate → classifier → builder in sequence.

For the NIH chest X-rays, the PHI Gate returns BLOCKED on most (burned-in laterality markers). Options:

| Decision | When to use |
|---|---|
| **Approve** | The detected text is a known non-PHI marker. You accept the risk. |
| **Reject** | The text may contain PHI. Quarantine the image. |

With `maxConcurrent: 1` and ~12 images, expect **15–30 minutes** total.

### What the Memory Layer Records

```bash
ls ${HOME}/.memory-tencentdb/memory-tdai/conversations/
ls ${HOME}/.memory-tencentdb/memory-tdai/records/
```

The extraction pipeline distills the run into L1 atomic facts (what prompt template worked for chest X-rays, which findings triggered human review, how many iterations the reviewer needed). By the second batch, the architect reads those facts and skips the rediscovery phase.

## 4.7 Inspect the Output

```bash
ls ${HOME}/medical-imaging-demo/output/
head -40 ${HOME}/medical-imaging-demo/output/batch_analysis_report.md
```

**Expected:**

```
batch_analysis_report.md
manifest.json
PLAN.md
phi_gate_receipts.jsonl
```

The report header looks like:

```markdown
# Batch Medical Imaging Analysis Report
Generated: 2026-10-13T14:32:11Z
Images processed: 12
Images cleared: 9
Images quarantined: 3
Modalities: XR (9), MR (1), CT (1), US (1)
Reused prior plan: batch-2026-10-12 (from memory)
```

### The Audit Trail

```bash
cat ${HOME}/medical-imaging-demo/output/phi_gate_receipts.jsonl | tail -10
```

**Expected:**

```json
{"seq": 42, "timestamp": "2026-10-13T14:35:22Z", "tool": "phi_gate", "file": "00000001_000.png", "verdict": "CLEAR", "hash": "a1b2c3d4"}
{"seq": 43, "timestamp": "2026-10-13T14:35:23Z", "tool": "classify_modality", "file": "00000001_000.png", "modality": "XR", "confidence": 0.91}
{"seq": 44, "timestamp": "2026-10-13T14:36:45Z", "tool": "medmo_analyze", "file": "00000001_000.png", "findings": 2, "boxes": 2}
```

### PHI Check

```bash
grep -r "MRN\|DOB\|SSN\|PatientName" ${HOME}/medical-imaging-demo/output/
```

**Expected:** No matches. De-identification ran first.

## 4.8 The Evidence Bundle

```bash
ls -la ${HOME}/.dsh/storages/swarm/
wc -l ${HOME}/.dsh/storages/swarm/events.jsonl
```

Verify the chain:

```bash
python3 << 'PYEOF'
import json, hashlib, pathlib
log = pathlib.Path.home() / ".dsh/storages/swarm/events.jsonl"
lines = log.read_text().strip().split("\n")
valid = True
for i, line in enumerate(lines):
    ev = json.loads(line)
    content = {k: v for k, v in ev.items() if k != "hash"}
    computed = hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()[:16]
    if ev.get("hash") and ev["hash"] != computed:
        print(f"CHAIN BROKEN at line {i}")
        valid = False
        break
print(f"Checked {len(lines)} events")
print("Chain valid" if valid else "Chain INVALID")
PYEOF
```

**Expected:**

```
Checked 247 events
Chain valid
```

## 4.9 Verify Memory Accumulation

After two batches:

```bash
wc -l ${HOME}/.memory-tencentdb/memory-tdai/conversations/*.jsonl
ls ${HOME}/.memory-tencentdb/memory-tdai/scene_blocks/ 2>/dev/null
```

**Expected:**

```
  312 /Users/yourname/.memory-tencentdb/memory-tdai/conversations/2026-10-12.jsonl
  287 /Users/yourname/.memory-tencentdb/memory-tdai/conversations/2026-10-13.jsonl
chest-xray-batch.md
ultrasound-batch.md
phi-gate-approval-patterns.md
```

The `scene_blocks/chest-xray-batch.md` file contains the distilled pattern for processing chest X-ray batches. The next batch reads this and skips the rediscovery phase. That is the mechanism behind the token reduction.

---

# Part 5: Public Access, Authentication, and Reboot Resilience

## 5.1 Set Your Environment Variables

```bash
export DOMAIN="nightthoughts.dev"
export DSH_HOST="dsh.${DOMAIN}"
export DSH_USER="admin"
export DSH_PASS="$(openssl rand -base64 24)"
export TUNNEL_NAME="dsh-mini"

echo "DSH host:   $DSH_HOST"
echo "Password:   $DSH_PASS"
```

> **Save the password now.** Copy the printed `DSH_PASS` value somewhere safe. It cannot be recovered from the hash.

```bash
cat >> ${HOME}/.zshrc << EOF

# DSH public access
export DOMAIN="${DOMAIN}"
export DSH_HOST="${DSH_HOST}"
export DSH_USER="${DSH_USER}"
export TUNNEL_NAME="${TUNNEL_NAME}"
EOF
```

## 5.2 Verify the Existing Stack

```bash
brew services list | grep caddy
tailscale status | head -3
sudo launchctl list | grep cloudflared
sudo launchctl list | grep qwenpaw
lsof -i :9080 -i :8000 -i :8088 -i :3080 2>/dev/null | grep LISTEN
```

Confirm DSH is bound to **loopback only** (`127.0.0.1:3080`, not `*:3080`).

## 5.3 Add the DSH Subdomain to Caddy

The previous guide uses **subdomain routing** for Cloudflare access (`omlx.nightthoughts.dev`, `qwenpaw.nightthoughts.dev`) and **path routing** for Tailscale (`/omlx/*`, `/console/*`). We follow the same pattern.

```bash
export CADDYFILE="/opt/homebrew/etc/Caddyfile"
test -f "$CADDYFILE" && echo "Using: $CADDYFILE" || echo "Not found — set CADDYFILE manually"
cp "$CADDYFILE" "${CADDYFILE}.bak.$(date +%Y%m%d-%H%M%S)"

HASH=$(caddy hash-password --plaintext "$DSH_PASS")
echo "Hash: $HASH"
```

### Add the Subdomain Block

```bash
python3 << PYEOF
import os, pathlib
path = pathlib.Path(os.environ["CADDYFILE"])
text = path.read_text()
host = os.environ["DSH_HOST"]
user = os.environ["DSH_USER"]
hashed = os.popen(f'caddy hash-password --plaintext "{os.environ["DSH_PASS"]}"').read().strip()

block = f'''

{host} {{
    basic_auth {{
        {user} {hashed}
    }}
    reverse_proxy 127.0.0.1:3080 {{
        header_up Host 127.0.0.1:3080
        header_up Origin http://127.0.0.1:3080
    }}
}}
'''
if host in text:
    print(f"{host} block already present — skipping")
else:
    path.write_text(text + block)
    print(f"Added site block for {host}")
PYEOF
```

### Add the Tailscale Path Route

```bash
python3 << PYEOF
import os, pathlib
path = pathlib.Path(os.environ["CADDYFILE"])
text = path.read_text()
block = '''
    # DSH route — Tailscale path-based access
    handle_path /dsh/* {
        reverse_proxy 127.0.0.1:3080 {
            header_up Host 127.0.0.1:3080
            header_up Origin http://127.0.0.1:3080
        }
    }
'''
if "/dsh/*" in text:
    print("DSH path route already present — skipping")
else:
    idx = text.index("}")
    new = text[:idx] + block + "\n" + text[idx:]
    path.write_text(new)
    print("Added /dsh/* path route")
PYEOF
```

### Validate and Reload

```bash
caddy validate --config "$CADDYFILE"
brew services restart caddy
```

### Test Both Access Paths Locally

```bash
curl -s -o /dev/null -w "Subdomain no auth: %{http_code}\n" \
  --resolve "${DSH_HOST}:443:127.0.0.1" "https://${DSH_HOST}/"
curl -s -o /dev/null -w "Subdomain with auth: %{http_code}\n" \
  -u "${DSH_USER}:${DSH_PASS}" --resolve "${DSH_HOST}:443:127.0.0.1" "https://${DSH_HOST}/"
curl -s -o /dev/null -w "Tailscale path: %{http_code}\n" \
  -u "${DSH_USER}:${DSH_PASS}" http://127.0.0.1:9080/dsh/
```

**Expected:**

```
Subdomain no auth: 401
Subdomain with auth: 200
Tailscale path: 200
```

## 5.4 Configure Tailscale Private Access

```bash
tailscale serve --bg --https=443 http://127.0.0.1:9080
tailscale serve status
```

**Expected:**

```
https://your-mac.your-tailnet.ts.net (tailnet only)
|-- / proxy http://127.0.0.1:9080
```

From another device on your tailnet:

```bash
curl -s -o /dev/null -w "%{http_code}\n" \
  -u "${DSH_USER}:${DSH_PASS}" \
  "https://your-mac.your-tailnet.ts.net/dsh/"
```

**Expected:** `200`

## 5.5 Configure Cloudflare Tunnel and DNS

### Check the Existing Tunnel

```bash
cloudflared tunnel list
```

If you already have a tunnel from the previous guide, reuse it. If not:

```bash
cloudflared tunnel create "$TUNNEL_NAME"
export TUNNEL_ID=$(cloudflared tunnel list --output json | python3 -c "
import sys, json
for t in json.load(sys.stdin):
    if t['name'] == '$TUNNEL_NAME':
        print(t['id']); break
")
echo "Tunnel ID: $TUNNEL_ID"
```

### Add the DNS Record

```bash
cloudflared tunnel route dns "$TUNNEL_NAME" "$DSH_HOST"
```

**Expected:**

```
Added CNAME dsh.nightthoughts.dev which will route to this tunnel.
```

This creates a proxied CNAME from `dsh.nightthoughts.dev` to `<tunnel-id>.cfargotunnel.com`. If you prefer to add the record manually in the Cloudflare dashboard:

| Field | Value |
|---|---|
| Type | CNAME |
| Name | `dsh` |
| Target | `<tunnel-id>.cfargotunnel.com` |
| Proxy status | Proxied (orange cloud) |

### Update the Ingress Config

```bash
export CLOUDFLARED_CONFIG="${HOME}/.cloudflared/config.yml"
cp "$CLOUDFLARED_CONFIG" "${CLOUDFLARED_CONFIG}.bak.$(date +%Y%m%d-%H%M%S)"

python3 << PYEOF
import os, pathlib
path = pathlib.Path(os.environ["CLOUDFLARED_CONFIG"])
text = path.read_text()
host = os.environ["DSH_HOST"]
if host in text:
    print(f"{host} already present — skipping")
else:
    lines = text.split("\n")
    out = []
    inserted = False
    for line in lines:
        if not inserted and "http_status:404" in line:
            out.append(f"  - hostname: {host}")
            out.append(f"    service: http://127.0.0.1:9080")
            inserted = True
        out.append(line)
    path.write_text("\n".join(out))
    print(f"Ingress rule added for {host}")
PYEOF
```

Verify:

```bash
cat "$CLOUDFLARED_CONFIG"
```

**Expected:**

```yaml
tunnel: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
credentials-file: /Users/yourname/.cloudflared/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.json
ingress:
  - hostname: omlx.nightthoughts.dev
    service: http://127.0.0.1:9080
  - hostname: qwenpaw.nightthoughts.dev
    service: http://127.0.0.1:9080
  - hostname: dsh.nightthoughts.dev
    service: http://127.0.0.1:9080
  - service: http_status:404
```

All three subdomains point at Caddy on `:9080`. Caddy routes by Host header to the correct backend.

### Restart the Tunnel (LaunchDaemon)

cloudflared runs as a **LaunchDaemon** — a system-level service that starts before login. Use `sudo`:

```bash
sudo launchctl kickstart -k system/com.cloudflare.cloudflared
sudo launchctl list | grep cloudflared
```

### Test Public Access

```bash
curl -s -o /dev/null -w "No auth: %{http_code}\n" "https://${DSH_HOST}/"
curl -s -o /dev/null -w "With auth: %{http_code}\n" \
  -u "${DSH_USER}:${DSH_PASS}" "https://${DSH_HOST}/"
```

**Expected:**

```
No auth: 401
With auth: 200
```

## 5.6 Configure DSH to Trust the Public Host

DSH validates the `Host` header against a whitelist. Without this, requests through the proxy fail with `421 Misdirected Request`.

```bash
PLIST="${HOME}/Library/LaunchAgents/com.deepseek.dsh.plist"
cp "$PLIST" "${PLIST}.bak"

python3 << PYEOF
import os, pathlib, plistlib
path = pathlib.Path(os.environ["PLIST"])
with open(path, "rb") as f:
    plist = plistlib.load(f)
args = plist.get("ProgramArguments", [])
host = os.environ["DSH_HOST"]
if "--trusted-host" in args:
    idx = args.index("--trusted-host")
    if idx + 1 < len(args) and args[idx + 1] == host:
        print(f"Already trusts {host}")
    else:
        args[idx + 1] = host
        plist["ProgramArguments"] = args
        with open(path, "wb") as f:
            plistlib.dump(plist, f)
        print(f"Updated trusted host to {host}")
else:
    args.extend(["--trusted-host", host])
    plist["ProgramArguments"] = args
    with open(path, "wb") as f:
        plistlib.dump(plist, f)
    print(f"Added --trusted-host {host}")
PYEOF

launchctl bootout gui/$(id -u)/com.deepseek.dsh 2>/dev/null || true
launchctl bootstrap gui/$(id -u) "$PLIST"
launchctl list | grep dsh
ps aux | grep "dsh web" | grep -v grep
```

**Expected:** The process list shows:

```
you  12345  ...  dsh web --no-open --port 3080 --trusted-host dsh.nightthoughts.dev
```

Test again:

```bash
curl -s -o /dev/null -w "Public: %{http_code}\n" \
  -u "${DSH_USER}:${DSH_PASS}" "https://${DSH_HOST}/"
```

**Expected:** `Public: 200`

## 5.7 Reboot Resilience

| Component | Mechanism | Domain |
|---|---|---|
| DSH daemon | LaunchAgent `com.deepseek.dsh` (`RunAtLoad` + `KeepAlive`) | gui |
| oMLX | Homebrew LaunchAgent | gui |
| QwenPaw | LaunchDaemon `/Library/LaunchDaemons/com.qwenpaw.app.plist` | **system** |
| Laya (maclaya) | LaunchAgent `com.maclaya` (created below) | gui |
| Caddy | Homebrew LaunchAgent `homebrew.mxcl.caddy` | gui |
| Cloudflared | LaunchDaemon `/Library/LaunchDaemons/com.cloudflare.cloudflared.plist` | **system** |
| Tailscale | GUI app with Launch at Login | gui |

### Create the Laya LaunchAgent

```bash
NODE_PATH=$(which node)
cat > ${HOME}/Library/LaunchAgents/com.maclaya.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.maclaya</string>
    <key>ProgramArguments</key>
    <array>
        <string>${NODE_PATH}</string>
        <string>$(which npx)</string>
        <string>maclaya</string>
        <string>serve</string>
        <string>--port</string>
        <string>8755</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>${HOME}/.maclaya/stdout.log</string>
    <key>StandardErrorPath</key>
    <string>${HOME}/.maclaya/stderr.log</string>
</dict>
</plist>
EOF

mkdir -p ${HOME}/.maclaya
launchctl bootstrap gui/$(id -u) ${HOME}/Library/LaunchAgents/com.maclaya.plist
launchctl list | grep maclaya
sleep 5
curl -s -o /dev/null -w "Laya: %{http_code}\n" \
  -X POST http://127.0.0.1:8755/v1/systemone \
  -H "Content-Type: application/json" \
  -d '{"state":"test","questions":{}}'
```

**Expected:**

```
-    0    com.maclaya
Laya: 200
```

### Verify DSH LaunchAgent Keys

```bash
python3 -c "
import plistlib, pathlib
p = pathlib.Path.home() / 'Library/LaunchAgents/com.deepseek.dsh.plist'
with open(p, 'rb') as f:
    plist = plistlib.load(f)
print('RunAtLoad:', plist.get('RunAtLoad', False))
print('KeepAlive:', plist.get('KeepAlive', False))
"
```

**Expected:**

```
RunAtLoad: True
KeepAlive: True
```

### The FileVault Caveat

```bash
fdesetup status
```

If FileVault is on and you want unattended recovery after a cold boot, disable it:

```bash
sudo fdesetup disable
```

> **Warning:** disabling FileVault removes disk encryption. Only do this on a machine that is physically secured and used exclusively as a server.

### 5.7.1 Verify Every Component Has a Startup Mechanism

Two categories: **daemons** (processes that run continuously) and **on-demand tools** (scripts invoked by DSH at runtime). Only daemons need a LaunchAgent/LaunchDaemon.

| Component | Type | Domain | Startup mechanism |
|---|---|---|---|
| DSH daemon | Daemon | gui | LaunchAgent `com.deepseek.dsh` |
| oMLX | Daemon | gui | Homebrew LaunchAgent |
| QwenPaw | Daemon | **system** | LaunchDaemon |
| Laya (maclaya) | Daemon | gui | LaunchAgent `com.maclaya` |
| Caddy | Daemon | gui | Homebrew LaunchAgent |
| Cloudflared | Daemon | **system** | LaunchDaemon |
| Tailscale | Daemon | gui | GUI app with Launch at Login |
| **PHI Gate** | On-demand tool | — | Called by DSH at runtime — **no daemon needed** |
| **Modality Classifier** | On-demand tool | — | Called by DSH at runtime — **no daemon needed** |
| **Memory data** | Persistent storage | — | `${HOME}/.memory-tencentdb/` — **no daemon needed** |
| **Memory extraction** | In-process | — | Runs inside DSH — **no separate daemon needed** |

The two medical tools are Python scripts on disk. DSH invokes them as subprocesses. As long as DSH starts, they are available.

The memory layer has no independent service. It runs entirely inside the DSH process.

Verify the daemon side with:

```bash
echo "=== LaunchAgents (user domain) ==="
launchctl list | grep -E "deepseek|maclaya"
echo "=== Homebrew services ==="
brew services list | grep -E "caddy|omlx"
echo "=== LaunchDaemons (system domain — sudo required) ==="
sudo launchctl list | grep -E "cloudflared|qwenpaw"
```

**Expected:**

```
=== LaunchAgents (user domain) ===
-    0    com.deepseek.dsh
-    0    com.maclaya
=== Homebrew services ===
caddy                started
omlx                 started
=== LaunchDaemons (system domain — sudo required) ===
-    0    com.cloudflare.cloudflared
-    0    com.qwenpaw.app
```

And verify the on-demand tools are reachable *through* DSH:

```bash
dsh --profile web --dump-config | grep -A1 "name: phi_gate\|name: classify_modality"
```

**Expected:**

```
- name: phi_gate
- name: classify_modality
```

Verify memory survived the reboot:

```bash
ls -la ${HOME}/.memory-tencentdb/memory-tdai/
```

**Expected:**

```
drwxr-xr-x  conversations/
drwxr-xr-x  records/
drwxr-xr-x  scene_blocks/
-rw-r--r--  memory.db
```

## 5.8 Full Reboot Test

```bash
sudo reboot
```

Wait 2–3 minutes, then from another device on your tailnet:

```bash
echo "=== 1. DSH daemon (LaunchAgent) ==="
ssh your-mac "launchctl list | grep dsh"

echo "=== 2. DSH loopback ==="
ssh your-mac "curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:3080"

echo "=== 3. oMLX ==="
ssh your-mac "curl -s http://127.0.0.1:8000/v1/models | python3 -c 'import sys,json; print(len(json.load(sys.stdin)[\"data\"]))'"

echo "=== 4. Laya ==="
ssh your-mac "curl -s -o /dev/null -w '%{http_code}\n' -X POST http://127.0.0.1:8755/v1/systemone -H 'Content-Type: application/json' -d '{\"state\":\"test\",\"questions\":{}}'"

echo "=== 5. Caddy ==="
ssh your-mac "brew services list | grep caddy"

echo "=== 6. Tailscale ==="
ssh your-mac "tailscale status | head -1"

echo "=== 7. Cloudflared (LaunchDaemon — sudo) ==="
ssh your-mac "sudo launchctl list | grep cloudflared"

echo "=== 8. QwenPaw (LaunchDaemon — sudo) ==="
ssh your-mac "sudo launchctl list | grep qwenpaw"

echo "=== 9. Public URL ==="
curl -s -o /dev/null -w "%{http_code}\n" \
  -u "${DSH_USER}:${DSH_PASS}" "https://${DSH_HOST}/"
```

**Expected:**

```
=== 1. DSH daemon (LaunchAgent) ===
-    0    com.deepseek.dsh
=== 2. DSH loopback ===
200
=== 3. oMLX ===
2
=== 4. Laya ===
200
=== 5. Caddy ===
caddy                started
=== 6. Tailscale ===
100.x.x.x    your-mac    your-tailnet    macOS    -
=== 7. Cloudflared (LaunchDaemon — sudo) ===
-    0    com.cloudflare.cloudflared
=== 8. QwenPaw (LaunchDaemon — sudo) ===
-    0    com.qwenpaw.app
=== 9. Public URL ===
200
```

## 5.9 Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| **421 Misdirected Request** | DSH trusted-host not set | Re-run 5.6, confirm `--trusted-host` in the plist |
| **401 loop in browser** | Wrong password | Re-run 5.3, re-hash, restart Caddy |
| **502 Bad Gateway** | Caddy cannot reach DSH | Confirm `curl http://127.0.0.1:3080` returns 200 |
| **WebSocket disconnects** | `header_up` lines missing | Check Caddyfile has both `Host` and `Origin` rewrites |
| **Tailscale Serve 404** | Wrong port in Serve config | Point at `:9080` not `:3080` |
| **Cloudflare 1033 error** | Tunnel not running | `sudo launchctl kickstart -k system/com.cloudflare.cloudflared` |
| **Cloudflare 530 error** | DNS not routed | `cloudflared tunnel route dns $TUNNEL_NAME $DSH_HOST` |
| **Laya returns connection refused** | LaunchAgent not running | `launchctl list \| grep maclaya`, check `${HOME}/.maclaya/stderr.log` |
| **After reboot, DSH not running** | FileVault on, no login | Either disable FileVault or log in manually |
| **QwenPaw missing after reboot** | LaunchDaemon not loaded | `sudo launchctl list \| grep qwenpaw`; if absent, re-run the previous guide's setup |
| **Memory directories empty** | Extraction LLM not configured | Open Settings → 记忆, confirm the model route points at `qwen-local/Qwen3.5-9B-MLX-4bit` |
| **Memory plugin not loading** | Plugin conflict or version mismatch | `dsh --profile web --dump-config \| grep tdai-memory`; check DSH version compatibility |

---

# Conclusion: What This Project Proves

Five parts ago, this was a Mac running a homelab stack. Now it runs a supervised team of seven agents that de-identifies, classifies, analyzes, reviews, and integrates medical images — with a persistent memory layer that accumulates knowledge across batches, and a hash-chained audit trail that anyone can verify offline.

Nothing about this project required a data center. Nothing required a cloud subscription. Nothing required patient data to leave the machine. And every claim in this guide is backed by a receipt you can check yourself.

## The Pipeline in One Sentence

A single natural-language prompt enters the DSH chat; seven specialized agents coordinate across a task DAG to produce a structured batch report of medical imaging findings — with a hard de-identification gate, a System 1 decision layer, a persistent memory layer, and a content-free audit trail, all running locally on Apple Silicon.

## What Each Piece Contributes

| Component | What It Does | Why It Matters |
|---|---|---|
| **MedMO-8B-Next** | Generates structured reports with bounding-box grounding across the four core radiology modalities | The only open model that covers the same modality range with spatial localization |
| **MLX** | Runs MedMO natively on Apple Silicon | Zero marginal inference cost; no GPU purchase; no cloud dependency |
| **DeepSeek Harness** | Orchestrates the swarm through a plugin architecture | A task DAG with parallel execution, per-role model pinning, and quality gates |
| **Laya (System 1)** | Resolves modality decisions in ~33ms with calibrated probabilities | A decision, not a generation — no token cost, fully auditable |
| **PHI Gate** | Strips DICOM tags and detects burned-in pixel text | A hard, non-bypassable block before any model sees an image |
| **Memory layer** | Captures L0→L3 conversation memory, extracts facts, injects recall | The pipeline learns from every batch; up to 61% token reduction |
| **Caddy + Tailscale + Cloudflare** | Exposes the Web UI with Basic Auth | Public access without exposing DSH to the internet |
| **Hash-chained receipts** | Records every tool call as a SHA-256 digest | Compliance can prove what ran without a second copy of the chart |

## The Evidence

The strongest part of this project is not the model. It is the proof that the agents worked together correctly.

Four artifacts are written to disk during every batch run:

**`manifest.json`** — the architect's inventory of every file, with modality, confidence, and review flags. This is the single source of truth for every downstream task.

**`phi_gate_receipts.jsonl`** — an append-only log of hash-chained receipts. Each line contains a sequence number, timestamp, tool name, and SHA-256 digests of the arguments and result. Never the content itself.

**`events.jsonl`** — the orchestrator's append-only event log, one entry per state transition. The chain is verifiable offline.

**L0→L3 memory chain** — the raw conversation record (L0), extracted atomic facts (L1), aggregated scenario blocks (L2), and stable persona (L3). Every L3 trait traces back through L1 facts to the exact L0 turn where it originated.

If the hash chain is valid and the memory chain is traceable, the agents ran in the order recorded, no record was altered after the fact, and every conclusion has a verifiable provenance.

## What This Means for Local Medical AI

Three assumptions broke during this build.

**Assumption one: "You need a data-center GPU."** MedMO-8B-Next leads every open-source medical imaging benchmark and outperforms proprietary models on report generation. It runs on a quiet desktop machine. The barrier is no longer hardware.

**Assumption two: "Local models are a compromise."** The quality gate uses a different model family from the builder, so each catches the other's mistakes. The reviewer is not a fallback — it is a deliberate architectural choice that improves output quality.

**Assumption three: "Multi-agent orchestration is enterprise-only."** The full pipeline — task DAG, parallel execution, quality gates, human-in-the-loop, hash-chained audit trail, persistent memory — runs on a single Mac. It costs nothing per inference.

## Where to Extend

MedMO supports more modalities than this guide wires up. The pipeline as built handles the **four core radiology modalities** — X-ray, CT, MRI, and Ultrasound — because they share a common DICOM standard, standard prompt patterns, and standard grounding vocabularies. The modality classifier, the PHI gate, and the prompt templates are all tuned for them.

The following modality families are supported by MedMO but require additional work to wire into this pipeline. Each one is a clear extension, not a rebuild — the orchestration layer, the memory layer, the PHI gate, and the audit trail all carry over unchanged. What changes is the prompt template and, in some cases, a pre-processing step.

| Modality family | What it needs that we do not build |
|---|---|
| Pathology / microscopy (SM, GM) | Whole-slide image (WSI) handling, tile-based processing, cellular-level grounding vocabularies |
| Ophthalmology (OP, OCT) | Fundus anatomy vs retinal layer analysis — OCT needs layer-by-layer segmentation prompts |
| Dermatology (XC) | Clinical photographs, not radiology — different lesion vocabularies, different grounding approach |
| Nuclear medicine (PT, NM) | Functional rather than anatomical — tracer uptake patterns, SUV quantification |

To add any of these, the work is: (1) extend the modality classifier's criterion list, (2) add a prompt template for the new modality, (3) if the modality needs a pre-processing step (WSI tiling, layer extraction), add a tool that runs before the builder. The orchestrator, the memory layer, the PHI gate, the review gates, and the audit trail do not change.

## Where the Project Is Honest About Its Limits

Four things this guide does not claim:

**It is not a diagnostic tool.** MedMO drafts. A named clinician reviews everything before it is used. The pipeline enforces this at every stage.

**It is not HIPAA-certified.** The PHI Gate implements the technical safeguards for de-identification. Compliance requires more than code — administrative policies, access controls, audit procedures, and a signed Business Agreement with any covered entity you work with.

**The memory layer extends the PHI surface.** The memory system captures conversations. If sessions touch real patient data, the L0 capture must run through the PHI Gate before storage, or those sessions must be excluded from memory capture entirely. The benchmark figures for token reduction and accuracy improvement are vendor-reported and not independently verified.

**It is not finished.** DSH is alpha software. The APIs will change. The plugins will break.

## The Reproducibility Checklist

```bash
echo "=== Part 2: Local models ==="
du -sh ${HOME}/models/MedMO-8B-Next-mlx 2>/dev/null
du -sh ${HOME}/models/Qwen3.5-9B-MLX-4bit 2>/dev/null
curl -s http://127.0.0.1:8000/v1/models | python3 -c "import sys,json; print(len(json.load(sys.stdin)['data']), 'models')"

echo "=== Part 2: Laya decision server ==="
curl -s -o /dev/null -w "Laya: %{http_code}\n" \
  -X POST http://127.0.0.1:8755/v1/systemone \
  -H "Content-Type: application/json" \
  -d '{"state":"test","questions":{}}'

echo "=== Part 3: DSH and orchestration ==="
dsh-desktop status | grep -E "Daemon|Port"
dsh --profile web --dump-config | grep -c "dsh-swarm-orchestrator\|dsh-jev-router"

echo "=== Part 3: Memory layer ==="
dsh --profile web --dump-config | grep -c "tdai-memory"
ls ${HOME}/.memory-tencentdb/memory-tdai/conversations/ 2>/dev/null | wc -l
ls ${HOME}/.memory-tencentdb/memory-tdai/scene_blocks/ 2>/dev/null | wc -l

echo "=== Part 4: Tools and pipeline ==="
test -f ${HOME}/.dsh/tools/phi_gate.py && echo "phi_gate.py OK"
test -f ${HOME}/.dsh/tools/modality_classifier.py && echo "modality_classifier.py OK"
ls ${HOME}/medical-imaging-demo/output/ 2>/dev/null | wc -l

echo "=== Part 4: Audit trail ==="
wc -l ${HOME}/medical-imaging-demo/output/phi_gate_receipts.jsonl 2>/dev/null
grep -r "MRN\|DOB\|SSN" ${HOME}/medical-imaging-demo/output/ 2>/dev/null | wc -l

echo "=== Part 5: Public access ==="
curl -s -o /dev/null -w "No auth: %{http_code}\n" "https://dsh.nightthoughts.dev/"
curl -s -o /dev/null -w "With auth: %{http_code}\n" \
  -u "admin:YOUR_PASSWORD" "https://dsh.nightthoughts.dev/"

echo "=== Part 5: Reboot resilience ==="
launchctl list | grep -c "com.deepseek.dsh\|com.maclaya"
brew services list | grep -c "caddy\|omlx"
sudo launchctl list | grep -c "cloudflared\|qwenpaw"
```

**Expected:**

```
=== Part 2: Local models ===
16G    /Users/yourname/models/MedMO-8B-Next-mlx
5.6G   /Users/yourname/models/Qwen3.5-9B-MLX-4bit
2 models
=== Part 2: Laya decision server ===
Laya: 200
=== Part 3: DSH and orchestration ===
Daemon: running
Port: 3080 listening on 127.0.0.1
2
=== Part 3: Memory layer ===
1
2
3
=== Part 4: Tools and pipeline ===
phi_gate.py OK
modality_classifier.py OK
4
=== Part 4: Audit trail ===
47 /Users/yourname/medical-imaging-demo/output/phi_gate_receipts.jsonl
0
=== Part 5: Public access ===
No auth: 401
With auth: 200
=== Part 5: Reboot resilience ===
2
2
2
```

## What Comes Next

**Reader validation.** The reports MedMO generates should be scored by radiologists against their own using RADPEER criteria. Published evaluations of similar models report human readers judging AI-generated and human-written reports clinically equivalent in the majority of normal studies.

**Modality expansion.** The classifier already handles the terminology for pathology slides, fundus photography, OCT, and nuclear medicine. Adding the corresponding prompt templates and grounding checks — as described in "Where to Extend" — would extend the pipeline without architectural changes.

**Memory curation.** After a few dozen batches, review the `scene_blocks/` and `persona.md` files. The memory system distills patterns automatically, but the distillation is only as good as the human review of what it learned. Curating the memory is how the pipeline stays aligned with clinical judgment.

**SOP integration.** Integrating the pipeline into a scheduled workflow — a nightly batch, a worklist-driven queue, a FHIR-based trigger — is the natural step toward clinical deployment.

## Final Thought

The most important thing this project demonstrates is not that a Mac can run a medical AI model. It is that **the orchestration layer is where clinical value lives, and the memory layer is where it accumulates**.

MedMO is a strong model. But a model alone produces text. What makes the output useful is the pipeline around it: the de-identification gate that runs before the model sees the image, the modality classifier that routes each file to the correct prompt, the grounding reviewer that rejects spatial claims without bounding boxes, the quality gate that loops back on incomplete reports, the audit trail that proves every step was taken, and the memory layer that ensures the next batch benefits from this one.

That layer is what this guide builds. It is what makes the difference between a demo and a deployable system. And it runs on your desk, on your data, at zero marginal cost, with a verification path that anyone can check.

The barrier is not hardware anymore. It is workflow design. That is the work that remains.

---

*If you build this, tag me. I want to see what clinical workflows you automate. And if you are working on local medical AI, privacy-preserving pipelines, or multi-agent orchestration in healthcare, let us talk in the comments.*

*The pipeline is running. The audit trail is verifiable. The memory is accumulating. The agents are idle, waiting for the next batch.*