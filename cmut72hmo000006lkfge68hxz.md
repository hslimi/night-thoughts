---
title: "Plain English Glossary: AI Terms for the Rest of Us"
datePublished: 2026-10-04T02:21:12.800Z
cuid: cmut72hmo000006lkfge68hxz
slug: plain-english-glossary-ai-terms-for-the-rest-of-us
tags: machine-learning, beginners-guide, glossary, local-ai

---

## The Basics

| Term | What it actually means |
|---|---|
| **Parameter** | A dial the model tuned while learning. Billions of them. Think of them as the model's settings. |
| **Model size (e.g., 70B)** | How many dials the model has. 70B = 70 billion. Bigger isn't automatically smarter. |
| **Quantization** | Storing the model in lower resolution, like a compressed photo. Slightly blurrier, much smaller. |
| **FP16 / INT8 / INT4** | The "resolution" of the model. FP16 is high-res (2 bytes per parameter). INT4 is compressed (0.5 bytes each). Lower numbers mean smaller files but slightly lower quality. |
| **Inference** | Running the model to get an answer. The moment you hit "send." |
| **Training** | The long, expensive process of teaching the model. Happens once, before you ever use it. |
| **Tokens** | Chunks of text the model reads and writes. Roughly ¾ of a word each. |
| **Tokens per second** | How fast the AI writes. 1–2/sec is a crawl. 40+/sec feels instant. |
| **Time-to-first-token** | How long you wait before the AI starts replying. The "thinking" pause. |
| **VRAM** | Special memory on a graphics card. The model has to fit here to run fast. |
| **RAM** | Your computer's regular memory. More RAM = you can hold more of the model at once. |
| **KV cache** | The model's short-term memory of your conversation so far. It grows as you chat. |

---

## The Runner-Ups

| Term | What it actually means |
|---|---|
| **MoE (Mixture of Experts)** | A model made of specialist teams. Only a few wake up per question, so it's cheaper to run. |
| **Active vs. total parameters** | How many dials are *used* per answer vs. how many *exist*. A huge model can still be cheap. |
| **Dense model** | A model that uses all its dials for every answer. Simple but expensive. |
| **Sparse model** | A model that only uses part of itself per answer. Cheaper, often just as good. |
| **Pruning** | Trimming the model. Removing weights that aren't pulling their weight (setting them to zero) so the model takes up less space and runs faster. |
| **Distillation** | Teaching a small model to copy a big one. Like a student learning from a professor. |
| **Sparse attention** | A shortcut for long conversations. Instead of looking at every word it has ever seen, the model focuses only on the parts that matter right now. |
| **Speculative decoding** | Guessing ahead to speed up answers. If the guess is right, you save time. |
| **Test-time compute** | Letting the model think longer before answering. Smarter, but slower. |
| **NPU** | A chip built specifically for AI. Like a GPU, but for math instead of graphics. |
| **Layer streaming / offloading** | Keeping most of the model on disk, pulling in only what's needed, one piece at a time. |
| **NVFP4 / FP8** | Extra-compact number formats. Save memory, keep most of the quality. |
| **Local inference** | Running the model on your own machine. Private, offline, no subscription. |
| **Cloud inference** | Running the model on someone else's servers. Faster, stronger, but your data leaves home. |
| **Hybrid routing** | Small model handles easy questions; cloud handles the hard ones. The best of both. |

---

## Going Deeper (Optional)

These come up less often, but you might see them in the wild.

| Term | What it actually means |
|---|---|
| **Fine-tuning** | Teaching an already-trained model a specific skill. |
| **RAG (Retrieval-Augmented Generation)** | Letting the model look things up before answering. |
| **Context window** | How much text the model can "hold in mind" at once. |
| **Benchmark** | A standard test used to compare models. Useful, but imperfect. |
| **Scaling laws** | The old rule that bigger models get predictably better. Now more nuanced. |
| **FLOPs** | A measure of raw computing work. Like counting how many math problems a chip can do. |
| **Unified memory** | A design where the CPU and GPU share the same pool of memory. Apple's approach. |

---

*This glossary is part of the [**Big Models, Small Machines**](https://nightthoughts.hashnode.dev/series/big-models-small-machines) series.*