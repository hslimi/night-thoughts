---
title: "Running LLMs Locally: How to Pick the Right Tool and Model for Your Machine"
datePublished: 2026-10-09T05:45:20.752Z
cuid: cmv0jk9jn000006ntalv28qqn
slug: running-llms-locally-how-to-pick-the-right-tool-and-model-for-your-machine
cover: https://cdn.hashnode.com/uploads/covers/6a92730f9a9aa7f72e74fdf4/fe942459-d087-49d0-9769-0ec5136af2f9.jpg
tags: ai, llm, gguf, ollama, local-llm

---

## Before you start: what local LLMs can and can't do

Running a model on your own machine buys you privacy, offline access, no rate limits, and no per-token bill. It does not buy you frontier-level intelligence. A 7B model running on your laptop is roughly "a competent assistant for drafts, summaries, translations, simple code, and offline Q&A." It is not a substitute for the largest cloud models on hard reasoning tasks. Set that expectation first, because most disappointment with local LLMs comes from comparing a 4 GB model to a trillion-parameter cloud service.

**Minimum viable hardware.** If you are below these numbers, you can still run something, but the experience will be limited. This is the honest floor:

| Your RAM / VRAM | What you can realistically run | What to expect |
|---|---|---|
| Under 8 GB | 1–3B models, Q4 | Works, but slow and shallow. Fine for autocomplete or toy chat. |
| 8 GB | 3–4B comfortably; 7–8B at Q4 is tight | Usable for light chat. Close other apps. |
| 16 GB | 7–8B at Q4 comfortably; 13B at Q4 tight | The realistic starting point for a useful local assistant. |
| 32 GB | 13B comfortable; 30B at Q4 possible on Apple Silicon | Good quality without cloud. |
| 64 GB+ | 70B at Q4 on Apple Silicon; 30B+ on a 24 GB GPU | Near-cloud quality for everyday tasks. |

Two things eat memory beyond the model file: the **context window** (longer conversations cost more RAM) and the **KV cache** that grows with it. A model that "fits" at 4K context may not fit at 32K.

---

## The landscape in one page

People compare tools that operate at different layers. Sort them before comparing:

| Layer | Examples | What it means for you |
|---|---|---|
| **Inference engine** | llama.cpp, MLX, ExLlamaV2, uzu | The thing that actually runs the math. Maximum control, minimum hand-holding. |
| **Wrapper / launcher** | Ollama | Sits on top of an engine, adds model management, an API, and one-command installs. |
| **Desktop app** | LM Studio, Jan, GPT4All, Mirai | A GUI on top of an engine. Point, click, download, chat. |
| **Serving stack** | vLLM, SGLang, TensorRT-LLM | Built for many concurrent users. Out of scope for a personal machine, but you'll see the names. |

Ollama is not a competitor to llama.cpp — it *contains* llama.cpp. LM Studio wraps llama.cpp and MLX. Knowing this stops a lot of confused forum arguments.

---

## Step 1: Know your machine

The single most important spec is memory, not CPU speed. Then it's which accelerator you have, because that determines which engine backends are available to you.

| Your chip | Backend you get | Practical consequence |
|---|---|---|
| Apple Silicon (M1–M4) | Metal | Unified memory means the GPU can use most of your RAM. Excellent for local LLMs. |
| NVIDIA GPU | CUDA | Best-supported path. Almost every tool works. |
| AMD GPU (Linux) | ROCm / HIP | Works well with recent ROCm. |
| AMD GPU (Windows) | Vulkan (ROCm limited) | Vulkan works everywhere but is slower than ROCm. |
| Intel Arc / integrated | SYCL / Vulkan | Supported in llama.cpp; expect modest performance. |
| CPU only | AVX2 / AVX-512 / NEON | Works, but expect single-digit tokens/sec on 7B models. |
| Intel Mac (pre-M1) | CPU only | No GPU acceleration. Treat as CPU-only. |

The rule of thumb for model sizing at 4-bit quantization is roughly **0.6–0.8 GB per billion parameters**, plus 1–2 GB overhead, plus context. That gives you this:

| Model size | Q4 file size | Comfortable RAM/VRAM |
|---|---|---|
| 1–3B | 0.7–2 GB | 4 GB |
| 7–8B | 4–5 GB | 8 GB |
| 13–14B | 7–9 GB | 12–16 GB |
| 30–34B | 18–20 GB | 24–32 GB |
| 70B | 40–42 GB | 48 GB+ |

---

## Step 2: Pick your tool

No single tool wins everywhere. Here is the neutral comparison:

| Tool | Type | Runs on | Best for | Watch out for |
|---|---|---|---|---|
| **Ollama** | Wrapper | Mac, Windows, Linux | Easiest setup, model library, OpenAI-compatible API | Slightly slower than raw llama.cpp; less control over flags |
| **LM Studio** | Desktop app | Mac, Windows, Linux | GUI, model discovery, shows what fits your RAM | Proprietary (free to use); heavier footprint |
| **llama.cpp** | Engine | Almost everything | Maximum control, fastest on CPU, widest backend support | Command line; you configure everything yourself |
| **Jan** | Desktop app | Mac, Windows, Linux | Lightweight, open source, clean UI | Smaller model selection than LM Studio |
| **GPT4All** | Desktop app | Mac, Windows, Linux | Very lightweight, good on old hardware | Limited to smaller models |
| **MLX** | Engine (Apple) | Apple Silicon only | Apple-native, fast on Macs, growing model ecosystem | Apple-only; models must be in MLX format |
| **uzu / Mirai** | Engine (Apple) | Apple Silicon only (iPhone, iPad, Mac) | Claimed fastest inference on Macs; Rust-based, MIT licensed | Narrow model ecosystem; models must be converted with lalamo; no GGUF |
| **ExLlamaV2** | Engine | NVIDIA only | Fast on consumer GPUs with EXL2 models | Narrow model format support |
| **Text Gen WebUI** | Web GUI | Mac, Windows, Linux | Power users who want many backends in one UI | Setup is more involved |

Now map that to your machine. Both columns are legitimate choices — the trade-off is stated so you can decide:

| Your machine | Easiest path | More control | What you trade |
|---|---|---|---|
| Mac M1–M4, 16 GB+ | Ollama or LM Studio | uzu, MLX, or llama.cpp | uzu claims the fastest Mac inference but has the smallest model library; MLX is Apple-native with more models; llama.cpp needs manual setup |
| Windows + NVIDIA | LM Studio or Ollama | llama.cpp | GUI convenience vs. flag-level control and slightly more speed |
| Windows + AMD | LM Studio (Vulkan) | llama.cpp | ROCm on Windows is unreliable; Vulkan is the safe path |
| Linux + NVIDIA | Ollama | llama.cpp | Ollama is simpler; llama.cpp is faster and scriptable |
| CPU only, 16 GB | Ollama | llama.cpp | Ollama manages models for you; llama.cpp is the fastest CPU path |
| Old laptop, 8 GB | Jan or GPT4All | Ollama with a 3B model | Ollama's library is bigger but the app itself is heavier |

**One footnote:** vLLM and SGLang are excellent tools, but they are built for serving many users at once, are Linux-first, and vLLM has no native Windows build. You do not need them for personal use. Note the names and move on.

---

## "Ready to run" vs. raw engine

Some tools ship with the model's context length, chat template, sampling parameters, and quant level already chosen. Others make you specify all of it. This is the convenience-versus-control axis, and it matters more than most beginners realize.

| Tool | What's pre-configured | What you can still change |
|---|---|---|
| Ollama | Chat template, context length, sampling defaults, system prompt — all in a Modelfile | Anything, by editing the Modelfile |
| LM Studio | Chat template, context length, GPU offload, sampling presets | All of it, via the UI |
| llama.cpp | Almost nothing. You pass flags yourself. | Everything |
| MLX | Sensible defaults per model | Most parameters via Python |
| uzu / Mirai | Chat template, sampling defaults, quant level per curated model | Limited — the curated library is opinionated |

The trade-off is real. A "ready to run" bundle gets you chatting in two minutes but may silently cap context at 4K or pick a quant that doesn't suit your RAM. A raw engine gives you exactly what you ask for — including the mistakes.

---

## A note on uzu (Mac only)

uzu is worth knowing about if you're on Apple Silicon. It's a Rust-based inference engine, MIT licensed, and it claims to be the fastest option on Macs — ahead of both MLX and llama.cpp in its own benchmarks. The catch is the model ecosystem. uzu does not read GGUF. Models are converted through a companion toolkit called **lalamo** into uzu's own format, and the curated library is much smaller than what you'll find on Hugging Face. If you want maximum Mac speed and you're happy with the models in their library, uzu is the pick. If you want the widest model selection, stick with GGUF and a tool that reads it.

Install is simple: `brew install mirai` gives you both the Mac app and a `mirai` CLI.

Two honest caveats. The performance numbers are self-reported by the Mirai team, and their llama.cpp comparison uses quant selections they chose — so read "fastest" as "fastest in their benchmarks," not as an independent verdict. And the model library is the real constraint. For most beginners, GGUF plus Ollama or LM Studio still gives the widest choice. uzu is for Mac users who've decided speed is the priority.

---

## Step 3: Model types, minus the math

Two distinctions matter for choosing.

**Dense vs. Mixture-of-Experts (MoE).** A dense model activates all its parameters for every token. An MoE model has many "experts" but only activates a few per token, so a 30B MoE might only use 3B parameters at a time.

| | Dense | MoE |
|---|---|---|
| Parameters active per token | All | A subset |
| Memory needed | Proportional to total size | Proportional to total size (all experts must be loaded) |
| Speed | Predictable | Can be much faster than its size suggests |
| Quality per GB of RAM | Usually better at small sizes | Better at large total sizes |
| When to pick it | Single consumer machine | Large RAM or multi-GPU |

The practical takeaway: an MoE model is faster than a dense model of the *same total size*, but not better than a dense model of the *same active size*. On a single laptop, a well-trained dense model is often the safer pick. On a 64 GB Mac, a large MoE can feel surprisingly quick.

**Base vs. instruct (chat) models.** Base models complete text; instruct models follow instructions. Beginners want **instruct** or **chat** variants, usually marked `-instruct`, `-it`, or `-chat`. Downloading a base model and wondering why it won't answer questions is a rite of passage — skip it.

---

## Step 4: What "optimized" means

Four techniques show up in the wild. Only one of them is something you'll actively choose.

| Technique | One-line explanation | Do you choose it? |
|---|---|---|
| **Quantization** | Store weights at lower precision (16-bit → 4-bit) | Yes — this is the main lever you control |
| **Pruning** | Remove unimportant weights or whole layers | No — it's baked into the model by its authors |
| **Distillation** | Train a small model to imitate a large one | No — it's how the model was made |
| **Low-rank approximation** | Factorize weight matrices into smaller pieces | No — usually folded into a quantized release |

Quantization is where your decisions live. Lower bits mean smaller files and faster inference, at the cost of quality. This table is the one to internalize:

| Quant | Size vs. FP16 | Quality | Use when |
|---|---|---|---|
| Q8_0 | ~50% | Near-lossless | You have memory to spare |
| Q6_K | ~40% | Excellent | Good balance |
| Q5_K_M | ~35% | Very good | Safe default |
| **Q4_K_M** | **~28%** | **Good** | **Most people, most of the time** |
| Q3_K_M | ~22% | Noticeable degradation | Tight memory |
| Q2_K | ~15% | Poor, often broken | Last resort |

A note on the naming: `Q` = quantized, the number = bits, `K` = K-quant (better quality at the same size), `_S`/`_M`/`_L` = small/medium/large variant, `IQ` = importance-matrix quant (slower to produce, better quality at the same size). **Q4_K_M is the sweet spot** for almost everyone. IQ quants are worth trying if you're squeezing a model onto a device where Q4_K_M just barely doesn't fit.

---

## Step 5: File formats

This is where most beginners get stuck, because a model you download may or may not work with the tool you installed.

| Format | Type | CPU? | NVIDIA | AMD | Apple | Read by |
|---|---|---|---|---|---|---|
| **GGUF** | Single file | Yes — best CPU path | Yes | Yes | Yes | Ollama, LM Studio, llama.cpp, Jan, GPT4All |
| **GPTQ** | safetensors directory | No | Yes | Limited | No | vLLM, ExLlamaV2 |
| **AWQ** | safetensors directory | No | Yes | Limited | No | vLLM |
| **EXL2** | safetensors directory | No | Yes | No | No | ExLlamaV2 |
| **MLX** | safetensors directory | No | No | No | Yes | MLX only |
| **uzu** | Converted via lalamo | No | No | No | Yes | uzu / Mirai only |
| **bitsandbytes** | Various | No | Yes | Limited | Limited | transformers, some others |

Two things to take from this table.

First, **GGUF is the only format that runs everywhere**, including CPU. If you are on a personal machine and not sure what you're doing, GGUF is the answer. It is also the format Ollama, LM Studio, and llama.cpp all natively consume.

Second, **GGUF is a single file**; the others are directories of `safetensors` shards plus config files, or in uzu's case a converted representation. If you download a GPTQ model and point Ollama at it, it will not work — not because something is broken, but because you have the wrong kind of file for that tool.

---

## Step 6: Finding models in practice

### On Hugging Face

1. Go to **huggingface.co/models**.
2. In the left filter panel, open **Libraries** and select **GGUF**.
3. Search by base model family (e.g., `Qwen`, `Llama`, `Gemma`, `Mistral`).
4. Sort by **Trending** for what's current, or **Most downloads** for what's proven.
5. Open a model page and check the **Files** tab — GGUF repos list every quant with its file size. Pick the one that fits your RAM.
6. Many pages have a **"Use this model"** dropdown that offers one-click import to Ollama or LM Studio.

The model card is worth reading. Good ones include a quant table with file sizes, a recommended context length, and sometimes a perplexity comparison so you can see how much quality each quant step costs.

### Trusted uploaders

Quantization quality varies by who did it. These accounts have good reputations: **bartowski**, **unsloth**, **lmstudio-community**, **mradermacher**, and the now-archived **TheBloke** collections (still useful as references). The model's original authors also frequently publish their own GGUF builds.

### Other places to look

| Source | What you get | Best for |
|---|---|---|
| Hugging Face | The largest catalog, all formats | Everything, especially GGUF |
| Ollama library (ollama.com/library) | Curated models, one-command pull | Fastest path from zero to chatting |
| LM Studio's built-in search | Models filtered by what fits your RAM | Beginners who want a GUI |
| Mirai model library (trymirai.com/models) | Curated uzu-format models | Mac users who've chosen speed over selection |
| ModelScope | Large catalog, strong on Chinese-language models | Non-English models |

---

## Step 7: The cheat sheet

Find your machine, pick the column that matches your appetite for setup, and run the model class listed. Speed figures are rough and depend heavily on the specific model and context length.

| Your machine | Tool | Model class | Format / quant | Rough speed |
|---|---|---|---|---|
| MacBook Air M1, 8 GB | Ollama or LM Studio | 3–4B instruct | GGUF Q4_K_M | 15–25 tok/s |
| MacBook Pro M3 Pro, 18 GB | LM Studio or Mirai (uzu) | 7–8B instruct | GGUF Q4_K_M or uzu 4-bit | 25–50 tok/s |
| Mac Studio M2 Ultra, 64 GB | Mirai (uzu) or Ollama | 27B dense, or 70B at Q3 | uzu 4-bit or GGUF Q4 | 15–40 tok/s |
| Windows laptop, 16 GB, no dGPU | Jan or llama.cpp | 3–7B instruct | GGUF Q4_K_M | 5–12 tok/s |
| Windows desktop, RTX 3060 12 GB | LM Studio | 7–8B instruct | GGUF Q4_K_M | 30–50 tok/s |
| RTX 4090, 24 GB | LM Studio or llama.cpp | 30B at Q4, or 8B at Q8 | GGUF | 60–100 tok/s |
| Linux + RTX 3090/4090 | llama.cpp or Ollama | 30B at Q4 | GGUF | 50–90 tok/s |
| CPU-only server, 32 GB | llama.cpp | 7–8B instruct | GGUF Q4_K_M | 3–8 tok/s |

If you take nothing else from this article: **GGUF, Q4_K_M, an instruct model that fits in your RAM.** That combination works on every platform and every tool mentioned here.

---

## Three quick-start recipes

**Ollama (any platform, easiest):**
