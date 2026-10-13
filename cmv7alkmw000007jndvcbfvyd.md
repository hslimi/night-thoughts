---
title: "The Future Is Both"
datePublished: 2026-10-13T23:08:48.470Z
cuid: cmv7alkmw000007jndvcbfvyd
slug: the-future-is-both
tags: ai, future, cloudcomputing, llm, local-ai

---

New to the jargon? [Start with the glossary →](https://nightthoughts.me/plain-english-glossary-ai-terms-for-the-rest-of-us)

---

Most AI systems today pick a side. They run entirely local or entirely cloud. That's a design choice, not a law of nature.

The choice made sense when local and cloud were genuinely different tools. Local was private but weak. Cloud was capable but exposed. Picking one meant accepting its weakness. That trade-off has narrowed.

Local models are now good enough for most queries. Cloud models are still better for the hardest ones. Running only local leaves capability on the table. Running only cloud sends private data out the door for no reason.

The alternative is routing. A system that decides, per query, where the query should run.

## The dial, not the switch

Essay 4 ended with a line: the line between local and cloud is not a wall. It's a dial.

A switch has two positions. A dial has a range. The range is where the interesting engineering lives.

Most production AI today sits at one of two extremes. Either the entire product runs on a local model — private, slow, capped by consumer hardware. Or the entire product runs in the cloud — fast, capable, with every request leaving the user's machine.

Both extremes are simple. Both leave value on the table. The middle position — routing — captures the best of each without inheriting either's weaknesses.

## What routing looks like in practice

Three scenarios, three scales.

**The developer.**

A coding assistant runs locally by default. Autocomplete, small refactors, docstring generation, renames — all local. Code never leaves the laptop. Fast enough, private by default, no per-query cost.

When the developer hits a hard problem — an architecture decision, a bug spanning six services, a subtle race condition — the assistant escalates the query to a cloud model. The developer doesn't press a button. The system decides.

The developer experiences one assistant. Behind the scenes, it's two. The split is based on difficulty, privacy, and latency.

**The company.**

An internal document search tool runs entirely locally. HR files, legal contracts, financial records, internal memos — none of it leaves the building. The model is small and quantized. It doesn't need to be brilliant. It needs to be accurate and private.

Customer-facing chat runs in the cloud. It needs to be fast, capable, and multilingual. The data flowing through it is public — questions from public users.

Two workloads. Two homes. One product. The company never argues about local versus cloud because it stopped treating them as mutually exclusive.

**The person.**

A phone assistant handles timers, reminders, quick lookups, and short replies on-device. No network round-trip. No data leaving the phone. Instant, private, available offline.

When the user asks something requiring real reasoning — a multi-day trip plan, a comparison of two products, a debugging session — the query escalates to a cloud model. The user sees one assistant. The phone decided the local model couldn't handle it.

The pattern in all three cases: sensitivity and difficulty decide the route. Private and easy goes local. Public and hard goes to the cloud.

## The triangle, revisited

Essay 3 ended with a triangle. Three forces, two of which you can optimize:

- **Capacity** — how much the model knows
- **Latency** — how fast it responds
- **Memory** — how much hardware it needs to run

Local and cloud sit at different points on this triangle.

| | Local | Cloud |
|---|---|---|
| **Capacity** | Limited by your hardware | Frontier-level |
| **Latency** | Slow first token, steady after | Fast, but network-dependent |
| **Memory** | Bounded by your RAM | Effectively unlimited |

Local optimizes memory and privacy, sacrificing capacity. Cloud optimizes capacity and speed, sacrificing privacy and adding dependency.

Routing lets you optimize all three at once — not by building a machine that does everything, but by picking a different point on the triangle for each task. The system is private when privacy matters, capable when capability matters, fast when speed matters. No single machine needs to do all three equally well.

## What this means for builders

Three practical takeaways.

**Design for two homes.**

Any serious AI product in 2026 should have a local path and a cloud path. Not for trend reasons. Because the cost structure, the privacy guarantees, and the latency profile are different for each, and pretending otherwise means leaving value on the table.

**Make routing invisible.**

Users shouldn't have to choose. The system should decide based on sensitivity, complexity, and latency requirements. A product that asks "would you like to use the local model or the cloud model?" has already failed. That's a question the system answers, not the user.

**Measure the dial.**

Track how often queries actually need cloud capability. Most products find the number is lower than expected. Sometimes much lower. That gap is money saved, data protected, and latency improved at the same time. The only way to find it is to look.

## What this means beyond tech

Three things shift when routing becomes standard.

**Access.** Local AI lowers the barrier. A capable model doesn't require a subscription. It requires a machine. That's a different kind of democratization — one that doesn't depend on a company's pricing page.

**Ownership.** When the model runs on your hardware, no one can change the terms. No pricing update, no rate limit, no quiet deprecation. That's a real shift in what it means to have AI. You don't rent it. You have it.

**Energy.** Local inference is less efficient per token than a hyperscale data center. It's also less total compute when you only use what you need. The energy math is more complex than either side admits, and nobody has fully worked it out yet. Anyone claiming otherwise is selling something.

## The closing

The parameter race was never about size. It was about capability, and capability has many shapes.

The local-cloud debate never was about location. It was about trade-offs, and trade-offs have many answers.

The future isn't local. It isn't cloud. It's the system that knows the difference — and chooses well.