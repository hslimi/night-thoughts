---
title: "The New Shape of AI Models"
datePublished: 2026-10-13T22:22:41.309Z
cuid: cmv78y9hk000002peas2g9v6g
slug: the-new-shape-of-ai-models

---

# The New Shape of AI Models

New to the jargon? [Start with the glossary →](https://nightthoughts.me/plain-english-glossary-ai-terms-for-the-rest-of-us)

---

Here's a riddle. Two AI models are released on the same day. Both have 70 billion parameters. One runs comfortably on a laptop. The other needs a data center. On paper, they are the same size. They are not the same machine.

That gap—between what a model *is* on paper and what it *does* when it runs—is the story of this essay. The parameter race didn't just slow down. It split into different questions entirely.

## Size was always a proxy

In Essay 1, we talked about why "bigger equals smarter" broke. The short version: parameter count was never a direct measure of intelligence. It was a rough proxy, and for a while, that proxy worked well enough.

But it was always a proxy for something else—the model's capacity to learn patterns. More parameters meant more room to store what it learned. That's it. It said nothing about *how* the model used that space.

Two models with the same parameter count can store their knowledge in completely different ways. One might use every single parameter for every question. The other might use a small fraction, on purpose, every time. Same number on the box. Different machine inside.

That's what changed.

## The model that doesn't use all of itself

Most people imagine an AI model like a brain where every neuron fires for every thought. An MoE model doesn't work that way. Here's what it actually is: instead of one giant model where every parameter fires for every question, it's made of many smaller specialist sub-networks—the "experts." A router sits on top. When a question comes in, the router decides which experts are best suited to answer. Only those experts wake up. The rest stay dormant.

Think of it like a hospital. You don't need every doctor, nurse, and specialist in the building to look at a sprained ankle. You need the triage nurse and the orthopedic specialist. The rest of the hospital is there, ready if needed, but they're not all crowding into the room.

Mixtral 8x7B illustrates this perfectly. It has roughly 47 billion total parameters. But for any given token, it activates only around 13 billion of them. That's the compute cost of a 13B model, with the capability that comes from something much larger.

The same pattern appears at larger scales. DeepSeek-V3 has 671 billion total parameters. Per token, it activates only about 37 billion. That's the compute footprint of a mid-sized model, running on a system that's 18 times bigger on paper.

Here's the catch that's easy to miss. MoE reduces compute, not memory. The full 671 billion parameters still have to be loaded — all of them, into memory, before the model can answer a single question. The architecture changes what runs per token. It doesn't change what has to live in RAM. That's why a 671B MoE model still needs serious hardware. Quantization is what makes it fit. MoE is what makes it fast.

## The number that actually matters

This is where the vocabulary splits. We now have to distinguish between two things that used to be the same:

**Total parameters** — the number on the box. How much the model *can* know.

**Active parameters** — how much the model *uses* per answer. How much compute it *actually spends*.

The first number tells you about capability. The second tells you about cost. And the second is the one you'll feel when you're actually running the thing.

A 671B model with 37B active parameters is not the same as a 37B model. It has more depth to draw from. But it runs at roughly the speed and cost of a 37B model, which is why it fits on hardware that couldn't dream of running a dense 671B model.

This is what people mean when they say MoE "decouples size from cost." It's the same reason a laptop can run a model that looks like it should need a data center.

This connects directly to what we saw in Essay 2. MoE is one piece of the puzzle — it's also what lets a 671B model fit on hardware that couldn't run a dense version at all. Combined with quantization and unified memory, "fits on my machine" becomes a real thing.

## Small specialists vs. big generalists

There's a second shift happening alongside MoE. Small models got much better — but not because small is inherently better. They got better because they're being taught by larger models.

The technique is distillation. A large teacher model generates answers, reasoning chains, and corrections. A small student model learns from those outputs instead of from raw data. The student doesn't rediscover knowledge from scratch. It copies what the teacher already figured out, at a fraction of the size.

That's why a well-trained 8B model today can outperform a 70B model from two years ago. It's not that the architecture got smarter. It's that the training recipe changed. The student is learning from a better teacher than the older model ever had.

Look at Granite 3.2 8B. IBM trained it to match or exceed models several times its size on math and reasoning benchmarks. Look at Llama 3 8B, which beats the original Llama 2 70B on most tasks. The pattern is everywhere.

But there's a limit worth naming. Small models are excellent at reasoning, style, and structured tasks. They are not as good at factual recall for long-tail queries. Ask a small model about an obscure historical figure, a niche technical detail, or a specific legal precedent, and it's more likely to hallucinate than a larger model that actually stored the fact. Knowledge has to live somewhere, and compression has a ceiling.

The honest version of the story: small models aren't smaller versions of big models. They're differently trained. They got better at some things, and they still can't do others.

## Thinking longer, not bigger

The third shift is the strangest one. Some models now get smarter by thinking *longer*, not by being *bigger*.

Instead of answering immediately, these models produce a chain of reasoning before giving their final response. They check their work. They try approaches and abandon them. They take more time—and in many cases, the extra time translates directly into better answers.

Models like OpenAI's o3 and DeepSeek-R1 don't just answer your question—they think through it first, producing a chain of reasoning before committing to an answer. You give them more time (more tokens), and they beat larger models that fire off instant responses. Extra compute at inference time is the new parameter count arms race.

Think of it like the difference between a quick answer and a considered one. If you ask someone a hard question, the immediate reply and the reply after thirty seconds of thought are not the same quality. Models learned this too.

The practical implication: "how smart is this model?" now depends partly on how long you let it think. That's not a question you can answer by looking at the parameter count at all.

There's a tax here, though, and it's worth naming. Thinking longer means waiting longer. For a research task, a batch job, or a careful analysis you'll read once — fine. For a voice assistant, a real-time coding tool, or anything interactive, that latency is fatal.

The industry is converging on the idea of two modes. A fast, intuitive mode for quick tasks. A slow, deliberate mode for hard ones. The best systems switch between them on demand. Neither replaces the other.

## The new scorecard

Put those three shifts together—MoE, better small models, test-time compute—and the old scorecard doesn't work anymore.

Parameter count was never enough, but now it's barely a starting point. The questions that actually matter when you're choosing a model are different. You want to know how many parameters it actually uses per answer, not just how many it has. You want to know how well it was trained and on what data. You want to know how many tokens per second it will give you on your hardware, how much it costs per answer, per day, per month, and whether it fits on the machine you already have.

That's a more complicated set of questions than "how big is it?" But it's a more honest one. And every model released in the last two years has been designed with at least one of those questions in mind.

The parameter race didn't disappear. It fragmented. The old race was one-dimensional: who can build the biggest model. The new race is a triangle — capacity, latency, and memory. You can optimize two. The third will always demand a tax. There is no single number that captures a model anymore. There never really was.

---

*Written in early 2026. Model examples reflect the landscape at that time.*