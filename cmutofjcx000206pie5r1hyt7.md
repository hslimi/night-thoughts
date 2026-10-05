---
title: "How a Laptop Learned to Run a Giant"
datePublished: 2026-10-04T10:27:15.014Z
cuid: cmutofjcx000206pie5r1hyt7
slug: how-a-laptop-learned-to-run-a-giant
tags: ai, machine-learning, hardware, llm, local-ai

---

New to the jargon? [Start with the glossary →](https://nightthoughts.hashnode.dev/plain-english-glossary-ai-terms-for-the-rest-of-us)

---

A 70-billion-parameter model is roughly 140 GB of data. A mid-range gaming laptop has between 8 and 16 GB of video memory.

That's like trying to pour a swimming pool into a teacup. It shouldn't fit. So how is it running?

The answer is that we stopped trying to force the whole model into memory at once. Instead, we shrink it, we share the load, and we only use the parts we actually need. Here are the three tricks that make it possible.

## Trick 1: Shrinking the Model

The first problem is pure size. You can't fit 140 GB into an 8 GB space. So we make the model smaller.

**Quantization** is the biggest lever. Think of it like a high-resolution photo. The original model uses 16-bit precision (called FP16), where every single parameter takes up 2 bytes of memory. That's the "high-res" version. Quantization drops that down to 8-bit (INT8), then 4-bit (INT4). At INT4, every parameter takes just 0.5 bytes.

That 140 GB model suddenly drops to around 35 GB. You lose a little bit of quality—the photo gets slightly blurrier—but you save an enormous amount of memory.

**Pruning** is the second lever. Researchers look at the model's billions of parameters and find the ones that aren't pulling their weight. They zero them out, effectively deleting them. It's like trimming dead branches off a tree so the rest can breathe.

**Knowledge distillation** is the third. Instead of compressing a big model, you train a small model to copy a big one. The small model learns from the big model's answers and reasoning, like an apprentice learning from a master. You end up with a model a fraction of the size, carrying a surprising amount of the original's capability.

## Trick 2: Sharing the Load

Shrinking helps, but a 35 GB compressed model still doesn't fit comfortably into 16 GB of video memory. So we use everything the computer has.

**Unified memory** changed the game on Apple Silicon. In a traditional PC, the CPU has its own RAM, and the GPU has its own VRAM. Moving data between them is slow. Apple's M-series chips use a single pool of memory shared by both the CPU and the GPU. A MacBook Pro with 128 GB of unified memory can hold a ~65B model comfortably—no copying required.

**CPU offloading** is the PC equivalent. Instead of demanding that the entire model live on the graphics card, tools like `llama.cpp` split the model up. The "hot" layers that are needed right now stay on the GPU. The rest sit in system RAM, and the CPU handles them.

Is it slower than pure GPU inference? Yes. But it's a thousand times better than not running at all.

## Trick 3: Doing Less Work

The final trick is architectural. Modern models are simply smarter about how they use themselves.

**Mixture of Experts (MoE)** is the biggest shift. Instead of a monolithic model that uses all 70 billion parameters for every single question, an MoE model is made of many smaller specialist teams. When a question comes in, a router sends it to just a few of those experts—maybe 8 to 10 billion parameters' worth. The model is huge on paper, but computationally cheap in practice. Examples like Mixtral, Qwen2.5-MoE, and Grok use this to deliver massive capability without massive compute costs.

**Sparse attention** reduces the memory and compute required for long contexts. Instead of forcing the model to look at every single word it has ever seen, sparse attention focuses only on the relevant parts. It cuts the math down drastically.

And then there's just better design. Models like Llama 3 and Qwen 2.5 are simply more parameter-efficient than their predecessors. A smaller model today beats a bigger model from two years ago.

## The Reality Check

So what does this actually look like on your desk?

If you have a **Mac Mini (M-series) with 32 GB of RAM**, you can run Qwen2.5-14B or Llama-3-8B comfortably at INT4. You might even squeeze in a 32B model if you're aggressive with quantization and don't have much else open.

If you have a **MacBook Pro with 64 GB or 128 GB of unified memory**, the world opens up. You can run a 70B model at INT4. It's slow—roughly 5-10 tokens per second—but it runs, completely offline, no API calls needed. We're talking batch processing and careful prompting, not instant chat.

There is a tradeoff. Larger models mean slower inference, more heat, and louder fans. But here's the part that surprises most people.

Training an AI model requires massive, sustained compute. It's like running a marathon at sprint speed for weeks. But inference—just using the model to get an answer—doesn't need that same intensity. You're reading a huge matrix multiplication table, not calculating it from scratch.

That's why a laptop can do this. It's not performing miracles. It's just reading the answer, one compressed piece at a time.

---

**Next in the series:** [The New Shape of AI Models →](#)

**New to the jargon?** Every term in this series has a plain-English explanation in the [glossary](https://nightthoughts.hashnode.dev/plain-english-glossary-ai-terms-for-the-rest-of-us).