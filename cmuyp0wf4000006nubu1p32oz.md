---
title: "Who Actually Saves Money?"
datePublished: 2026-10-07T22:42:42.621Z
cuid: cmuyp0wf4000006nubu1p32oz
slug: who-actually-saves-money
tags: ai, cloudcomputing, economics, llm, local-ai

---

# Who Actually Saves Money?

New to the jargon? [Start with the glossary →](https://nightthoughts.me/plain-english-glossary-ai-terms-for-the-rest-of-us)

---

"Local AI is free."

You'll see that line in forum threads, in YouTube comments, in the pitch for every new tool that runs on your own machine. It sounds true. You download a model, you run it, and no bill arrives at the end of the month.

But it's not free. It's prepaid. And "prepaid" is a very different thing than "free."

The bill doesn't disappear — it just arrives earlier, in one lump, before you've generated a single token. And whether that prepayment actually saves you money depends entirely on what you're doing, how often, and how sensitive your data is.

This essay is about figuring out which side of that line you're on.

## The Real Bill: What Local Actually Costs

Let's start with the hardware. You need a machine capable of running the models you care about. For a 27B model at 4-bit quantization, that means a computer with 32 to 64 GB of unified memory. A capable laptop or small desktop in that range costs somewhere between $1,500 and $2,500. Let's call it $2,000 as a working number.

That's the upfront cost. It's real, and it's large.

Then there's electricity. A machine running inference under sustained load draws somewhere between 30 and 80 watts, depending on the chip and how hard you push it. At average residential electricity rates, running that machine four hours a day costs roughly $3 to $7 per month. It's not nothing, but it's small.

Then there's time. Setup, maintenance, troubleshooting, keeping models up to date, dealing with the occasional broken dependency. If you value your time at even a modest hourly rate, the first month of local AI costs more in time than in hardware.

That's the honest picture. Local AI is a capital expense followed by a small operational expense. The big number comes first.

## The Real Bill: What Cloud Actually Costs

Cloud AI flips the structure. There's no upfront cost. You pay per token, or you pay a flat subscription fee.

Take a representative example. A frontier cloud model — the kind you'd use for the hardest tasks — charges roughly $2.50 per million input tokens and $10 per million output tokens. A lighter model might cost a fraction of that. A monthly subscription to a chat interface typically runs $20.

The cloud pricing has three properties worth noticing:

**It scales with usage.** The more you use, the more you pay. There's no ceiling and no floor. A heavy month costs more than a light one.

**It's invisible until it isn't.** A $20 subscription feels small. A $200 API bill at the end of a heavy month feels very different.

**It requires the network.** Every request leaves your machine, hits a server, and comes back. That's usually fine. Sometimes it isn't.

So cloud AI is an operational expense with no capital cost. The small number comes first, and it never stops coming.

## The Break-Even Point

Now the interesting part. When does the local prepayment start paying for itself?

The math is simpler than it looks. You're comparing a one-time cost plus a small monthly cost against a monthly cost that scales with usage.

Take the $2,000 machine. Add $5 per month for electricity. Call it $2,005 in year one, then $60 per year after that.

Now compare it to two cloud scenarios:

**Light user.** Someone who uses AI casually, maybe a few queries a day. A $20 monthly subscription covers it. That's $240 per year. Break-even against local hardware happens after roughly **8 to 10 years**. Cloud wins.

**Heavy user.** Someone generating millions of tokens per month — running agents, batch jobs, or sustained development work. At $50 to $100 per month in API costs, break-even against local hardware happens in **20 to 40 months**. Local starts to win.

**Very heavy user.** Someone running overnight batch jobs or continuous agents. Cloud costs can climb into hundreds of dollars per month. Break-even happens in **under a year**. Local wins by a wide margin.

The pattern is clear: **the more you use it, the more local hardware pays for itself.** Cloud is cheaper for occasional use. Local is cheaper for sustained use.

![A line chart comparing cumulative cost over time for local hardware versus cloud API usage. The local line starts at $2,000 and stays almost flat. The cloud line starts at $0 and rises steadily. Two cloud scenarios are shown — light usage at $20 per month, and heavy usage at $80 per month. The heavy usage line crosses the local line at around month 30. The light usage line crosses much later, around year 8.](https://datawrapper.dwcdn.net/4XGwq/full.png)

*Illustrative. Actual costs depend on hardware prices, electricity rates, model choice, and usage patterns.*

## When Local Wins, and When It Doesn't

Cost is only one axis. Privacy, latency, and dependency matter too. Here's how the decision breaks down by task.

**Sensitive data — medical records, legal documents, personal journals, internal company material.** Local wins. Full stop. The moment data leaves your machine, you've lost control of it. No cloud provider, no matter how trustworthy, changes that. If the data is sensitive, local is the only real option.

**Overnight batch jobs — processing thousands of documents, summarizing archives, running evaluations.** Local wins. Latency doesn't matter here. You're not waiting for the answer. The model can churn through the work at 5 tokens per second, and nobody cares. Cloud costs scale with volume here, which means the bill grows fast.

**Offline work — on a plane, in a remote area, anywhere the network is unreliable.** Local wins. Cloud is simply unavailable.

**Frontier capability — the hardest reasoning tasks, the most complex coding, the newest and best models.** Cloud wins. The best models are still too large to run locally on consumer hardware, and they may stay that way for a while. If you need the best possible answer, you pay for it.

**Real-time conversation — a chat interface you use throughout the day.** Cloud usually wins. Cloud inference is fast. Local inference, on a 27B model at 4-bit, runs at maybe 10 to 20 tokens per second. That's fine for reading but slow for real-time back-and-forth.

**One-off experiments — trying a new model, testing a prompt idea, playing around.** Cloud wins. You don't want to download 20 GB and configure a runtime just to try something once.

**Long-term daily use, any task.** Local starts to win. The longer your horizon, the more the math tilts.

## The Quiet Costs Nobody Talks About

There are costs that don't show up in the spreadsheet but show up in daily life.

**Fan noise.** Running a 27B model at full tilt on a laptop means the fans spin up. If you work in a shared space, this matters more than the electricity bill.

**Slow first token.** Local inference has a longer warm-up. The model loads from disk, the context gets processed, and only then does it start generating. Cloud models hide this latency behind fast servers.

**Model drift.** The models you can run locally are not the same as the ones you can access in the cloud. When a new frontier model drops, you can't run it on your machine the day it's released. You wait for a smaller, distilled, or quantized version to appear. That gap is a real cost.

**Maintenance drift.** Local setups break. Dependencies change. A model that worked last month stops working this month. Cloud, for all its flaws, is someone else's problem to maintain.

None of these costs are deal-breakers. But they're real, and anyone considering a local setup should account for them.

## The Question That Actually Matters

So which is cheaper — local or cloud?

The honest answer is that this was never a binary choice. The right question isn't "which one is cheaper?" It's "for this task, at this frequency, with this data, which one is the better fit?"

For sensitive data, offline work, and sustained heavy use, local wins. For frontier capability, real-time interaction, and occasional use, cloud wins. For most people, most of the time, the answer is **both** — and the interesting part is figuring out where the line is.

That line is not a wall. It's a dial.

And that dial is exactly what the next essay is about.

---

*Sources: Cloud pricing based on representative public rates for a frontier model as of 2026. Hardware pricing based on typical consumer configurations. Electricity costs based on average residential rates.*