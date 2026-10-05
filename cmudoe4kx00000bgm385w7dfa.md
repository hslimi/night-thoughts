---
title: "Fast Brain, Slow Brain: A Beginner's Guide to System 1 and System 2 AI"
datePublished: 2026-09-23T05:41:50.408Z
cuid: cmudoe4kx00000bgm385w7dfa
slug: fast-brain-slow-brain-a-beginner-s-guide-to-system-1-and-system-2-ai
cover: https://cdn.hashnode.com/uploads/covers/6a92730f9a9aa7f72e74fdf4/031588b9-1bd9-4e63-a9c7-7fde47ce28f2.jpg
tags: ai, llm, jev

---

You ask an AI "is this email spam?" and it writes you a 200-word essay explaining its reasoning, citing signals, and hedging its conclusion.

Your brain doesn't work that way. You'd just *know*.

In September 2026, a model called Jev hit 140,000 waitlist signups in 36 hours by doing exactly that: no essays, just decisions. This article explains what it is, why it matters, and when you'd actually use it.

* * *

## The Two Systems of the Mind

In his book *Thinking, Fast and Slow*, psychologist Daniel Kahneman described two modes of thought.

**System 1** is fast, automatic, and silent. You're walking on a trail and see a curved shape in the grass. Before you can form the word "snake," your body has already flinched. No reasoning. No explanation. Just a decision.

**System 2** is slow, deliberate, and verbal. You're doing your taxes. You read the instructions, consider each deduction, check your arithmetic. It's effortful and it feels like thinking.

Here's the mapping that matters for AI:

*   **Today's famous models** — ChatGPT, Claude, Gemini — are artificial System 2. They think by writing, one token at a time. That's why they're brilliant at reasoning and terrible at reflexes.
    
*   **A new category of models** aims to be artificial System 1: instant, silent, typed decisions.
    

* * *

## Why This Matters Now

Most AI calls in production aren't creative questions. They're judgments:

*   "Which team should handle this support ticket?"
    
*   "Is this transaction risky?"
    
*   "Should this agent be allowed to run this tool?"
    

Right now, we pay System 2 prices — 10 to 40 seconds and cents per call — for System 1 jobs that should take milliseconds and fractions of a cent.

To be fair, classifiers and rerankers have existed for years. What's new is packaging a frontier-quality decision model as a hosted API that anyone can call with a credit card.

And the adoption has been fast. When Jev launched on September 15, 2026, roughly 13% of Vercel's paid AI Gateway teams were using it within 24 hours — more than double any previous model launch.

* * *

## What Is a System One Model?

Simple definition: unstructured input goes in, typed probabilistic decisions come out. No text generated.

Think of a restaurant host. A party walks in. The host doesn't write an essay about seating theory. They glance at the room and make a decision — instantly, silently, and in one of three shapes:

| Decision shape | What the host does | What it returns |
| --- | --- | --- |
| **Choice** | Picks one option from a fixed list | "Booth section" |
| **Score** | Rates something on a scale | "Wait time: 0.7 out of 1" |
| **Noul** | Answers a yes/no question with confidence | "Reservation on file: yes, 0.95" |

That's the whole idea. The host never explains. They never write a paragraph. They just return a typed answer your system can act on directly.

Yes, LLMs can also output JSON. System One models are different in *what they're trained to do* — calibrated decisions, not just formatted text. Vercel's own comparison notes that Jev "evaluates each question independently against the same state, returning typed answers with probabilities over the defined outcomes," while LLM probabilities are "generated estimates."

The first public example is Jev by TypeSafe AI. You can call it on OpenRouter with the model ID `typesafe/jev-1.13`, or through Vercel AI Gateway as `typesafe-ai/jev`.

* * *

## So How Much Faster and Cheaper, Really?

Independent testers ran Jev against a comparable LLM on the same decision tasks:

| Metric | Jev | Comparable LLM |
| --- | --- | --- |
| Median latency | 105 ms | 710 ms |
| Cost per 1,000 decisions | $0.04 | $0.16 |
| Accuracy (vendor dashboard) | 67.8% | 74.1% |

Read that table carefully. Jev is faster and cheaper by an order of magnitude — and slightly *less* accurate. TypeSafe's own claims of 20–200x speed and 40–400x cost reduction are self-tested against agreement with other frontier models rather than ground truth, and the one independent check (Every) found roughly 25x faster and 580x cheaper on extraction tasks specifically — "good but not perfect."

So here's the honest trade-off. Jev isn't more accurate than the best large models. It's slightly less accurate, and dramatically cheaper and faster. For most production decisions, that's the right trade. For a legal contract or a medical diagnosis, it isn't.

The framing to remember: you don't hire a decision model because it's smarter. You hire it because most decisions don't need smart. They need fast, cheap, and consistent.

* * *

## Which Jobs for Which Brain?

| Task | System One (decide fast) | System Two (think in words) |
| --- | --- | --- |
| "Is this ticket urgent?" | ✅ ideal | overkill |
| Routing requests to the right model or agent | ✅ ideal | ✅ common today |
| Agent guardrails ("is this tool call dangerous?") | ✅ ideal, but pair with deterministic checks | works, but slow |
| Fraud, spam, or moderation triage at scale | ✅ ideal | too costly |
| Real-time in-app decisions (games, bidding) | ✅ only option | impossible (3–30s latency) |
| Evaluating agent outputs (LLM-as-judge) | ✅ promising | ✅ common today |
| Writing an email, essay, or code | ❌ can't generate text | ✅ |
| Counting, arithmetic, exact dates | ❌ weak | ✅ (or use code) |
| Novel problem, open-ended answer | ❌ answers must be predefined | ✅ |

The punchline: the winning architecture is hybrid. System One routes, scores, and guards at high volume. System Two handles the escalated hard cases. Plain code does arithmetic.

**The constant trap:** Archestra tested Jev on 100 real agent tool calls and found that 79% of calls were harmless and stayed local. A classifier with 75% accuracy is therefore *worse than a hardcoded "benign" constant*. Accuracy alone is meaningless — you need to know the base rate.

* * *

## Getting Jev Into Your Stack

There are several ways to call Jev, and the right one depends on whether you want to manage credentials yourself or let a gateway handle them.

| Route | Model ID | Best for |
| --- | --- | --- |
| **TypeSafe direct** | `typesafe/jev-1.13` | Tightest control, newest features first |
| **OpenRouter** | `typesafe/jev-1.13` | One key for many models |
| **Vercel AI Gateway** | `typesafe-ai/jev` | Existing Vercel/Next.js apps, zero data retention |
| **LiteLLM proxy** | `typesafe/jev-1.13` | Enterprise routing, cost tracking, multi-provider |

### If you're already running a gateway

This is where Jev's adoption story gets interesting, because gateways didn't just pass it through — they built on it.

**LiteLLM** added Jev in `v1.103.0-rc` and proxies its `/systemone` endpoint with logging and cost tracking. Your TypeSafe key stays on the proxy; clients only need a LiteLLM virtual key. Spend is logged under the versioned model TypeSafe reports (`typesafe/jev-1.13.0`).

But LiteLLM went further and uses Jev for two jobs inside the proxy itself:

*   **Context compaction.** LiteLLM asks Jev whether older tool results are still relevant. If Jev scores a result below 0.2, it replaces the result with a short notice — saving input tokens on long agent runs.
    
*   **Auto Router classification.** LiteLLM's router uses Jev to decide which model tier a request belongs to. In their benchmark, Jev matched expected tiers on 95% of calls versus 73.75% for Claude Haiku, at 5.43x the speed and 96% lower cost.
    

**Vercel AI Gateway** exposes Jev with zero data retention and no output token charge. Vercel's AI SDK ships an experimental `evaluate` API that surfaces typed answers directly in TypeScript — so a department choice can select a support queue, a severity score can influence priority, and an uncertain result can trigger human review.

**Cloudflare Workers AI**, **Netlify AI Gateway**, and **OpenRouter** all serve Jev as well. Netlify's integration is zero-config: install `@typesafe-ai/sdk` in a Netlify Function, and AI Gateway handles credentials and billing.

The pattern across all of them is the same: Jev is cheap enough to call *inside* infrastructure, not just from application code. That's why routers use it as a classifier and proxies use it as a guardrail.

* * *

## Limitations You Should Know

**Typed ≠ correct.** A wrong answer from your allowed list is still wrong.

**No explanations.** That makes audits harder. Keep humans in the loop for high-stakes calls.

**Prompt injection is real and vendor-acknowledged.** TypeSafe's own limitations page for Jev 1.13 states that "content written to adversarially steer the model, whether that is an injected instruction, a deliberately misleading framing, or text that argues for its own classification, can move the answer." An independent security benchmark found 10 false positives and 13 false negatives out of 662 prompt-injection tests. A guard built on Jev belongs *alongside* deterministic checks, not instead of them.

**Weak at arithmetic, dates, counting, and adversarial input.** Leave those to code.

**Not a replacement for LLMs.** It's a different tool for a different job.

* * *

## The Takeaway

System Two writes. System One decides. The future is both.

You're running 10 million classifications per day. A decision model gets 29 out of 30 right for a fraction of a cent each. A large LLM gets 30 out of 30 for a hundred times more. Where's your cutoff — and what would you never trust to a decision model?

* * *

## References

*   TypeSafe AI — Jev API documentation and limitations page: https://docs.typesafe.ai/api
    
*   LiteLLM — "TypeSafe Jev on LiteLLM" (Sep 20, 2026): https://docs.litellm.ai/blog/typesafe\_jev
    
*   LiteLLM — "Reduce agent context with TypeSafe Jev and LiteLLM" (Sep 18, 2026): https://docs.litellm.ai/blog/typesafe-jev-compaction
    
*   LiteLLM — "JEV Classifier: 5.43x as Fast as Haiku, 96% Lower Cost" (Sep 20, 2026): https://docs.litellm.ai/blog/jev-classifier
    
*   Vercel — "How to classify, route, and score with Jev and AI SDK": https://vercel.com/kb/guide/typesafe-jev-and-ai-sdk
    
*   CryptoBriefing — "TypeSafe opens Jev AI to public after rapid adoption forces waitlist removal" (Sep 21, 2026): https://cryptobriefing.com/typesafe-jev-ai-public-access/
    
*   explainx.ai — "Is Jev's 200x-Faster, 400x-Cheaper Claim Actually True?" (Sep 19, 2026): https://www.explainx.ai/blog/jev-speed-cost-claims-fact-check-2026
    
*   Archestra — "We Tested Jev on 100 Real Agent Calls. How Easy Is It To Beat a Constant?" (Sep 21, 2026): https://archestra.ai
    
*   VentureBeat — "Jev AI agent security: Prompt injection risk" (Sep 21, 2026): https://venturebeat.com
    
*   Layer3Labs — "Jev Benchmarks: How Accurate Is TypeSafe AI's Model?" (Sep 22, 2026): https://www.layer3labs.io
    
*   Daniel Kahneman — *Thinking, Fast and Slow* (2011)