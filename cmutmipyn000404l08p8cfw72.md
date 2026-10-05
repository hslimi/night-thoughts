---
title: "Bigger Isn't Always Smarter"
datePublished: 2026-10-04T09:33:44.309Z
cuid: cmutmipyn000404l08p8cfw72
slug: bigger-isn-t-always-smarter
tags: ai, technology, machine-learning, llm, local-ai

---

*New to the jargon? Start with the [plain-English glossary](https://nightthoughts.hashnode.dev/plain-english-glossary-ai-terms-for-the-rest-of-us).*

---

For years, the rule was simple: bigger AI meant smarter AI.

More parameters, more brainpower. Every new model was just the last one, scaled up. A 70-billion-parameter model was smarter than a 7-billion one, the way a bigger library holds more books. And if you wanted to run one of those giants, you needed a data center.

That rule just broke.

A 70-billion-parameter model now runs on a 4GB graphics card — the kind you'd find in a mid-range gaming laptop. Slowly, yes. But it runs. Under the old rule, that shouldn't be possible.

To understand why it matters, it helps to see where the old rule came from — and why it was right for so long.

## The rule that worked

In 2020, researchers noticed something remarkable. As they made AI models bigger, the models got better in a way that was almost predictable. Double the size, and performance improved by a measurable amount. Double it again, and it improved again.

They called this "scaling laws." And for a few years, scaling laws were the closest thing AI had to a recipe.

The recipe went something like this:

- More parameters: better.
- More training data: better.
- More compute: better.

If you wanted a smarter model, you made a bigger one.

And it worked. Models went from millions of parameters to billions, then to hundreds of billions. Each generation outclassed the last. The rule seemed less like a pattern and more like a law of nature.

Let's be fair: the old rule wasn't wrong. It was incomplete. For most of a decade, scaling up really did work. The problem wasn't that the rule failed — it's that we mistook it for the whole story.

Because something else was happening underneath.

## The crack

In 2022, a paper called [Chinchilla](https://arxiv.org/abs/2203.15556) made a quiet but important point. Many of the biggest models weren't just big — they were undertrained. They had billions of parameters but hadn't seen enough data to use them well.

The implication was uncomfortable: a smaller model, trained on more data, could beat a bigger one trained on less.

At first, this was a footnote. Then it became a pattern. Small models started showing up on leaderboards next to giants. A well-trained 7-billion-parameter model could hold its own against one three times its size. In some cases, it beat them outright.

The old rule had a hole in it. And once you saw the hole, you couldn't unsee it.

## Why the rule broke

Four things changed at roughly the same time. None of them alone explains the shift, but together they rewrote the rule.

**Better data.** For years, "more data" meant "scrape more of the internet." Then researchers started curating it — filtering, cleaning, and in some cases generating high-quality training data on purpose. A model fed clean, dense, well-chosen examples learns faster than one fed a mountain of noise. Quality started to matter as much as quantity.

**Better teaching.** Techniques like distillation let a small model learn from a big one. Instead of training from scratch, the small model copies the big model's answers and reasoning, the way an apprentice learns by watching a master. The result is a model a fraction of the size, with a surprising amount of the capability.

**Smarter designs.** The biggest shift might be architectural. Mixture-of-experts models are built from many specialist sub-models. When a question comes in, only a few of them wake up to answer. On paper, the model is enormous. In practice, only a slice of it runs at any given moment. Huge on paper, cheap in practice.

**Better hardware.** New chips, new number formats, and new software tricks let small machines hold more of the model at once. We'll dig into this in the next essay, but the short version is: the hardware caught up to the software's ambitions.

![A scatter plot showing parameter count on the horizontal axis and benchmark performance on the vertical axis. Many small models appear above the trend line, and many larger models appear below it, illustrating that size alone does not predict capability.](https://datawrapper.dwcdn.net/xnb1K/full.png)

*Sources: Official model cards, technical reports, and papers from Meta, Mistral AI, Alibaba Cloud, IBM, and DeepSeek (2023-2024). Scores are approximate and rounded.*

Each of these forces pushed in the same direction: capability stopped being tied to raw size. A smaller model, designed and trained well, could do what used to require something much bigger.

## What "smart" actually means

Here's the part that's easy to miss. "Smarter" was never a single number.

When we say a model is smart, we usually mean it's good at a specific set of tasks: answering questions, writing code, summarizing documents, reasoning through a math problem. But no model is good at everything. A model that writes beautiful prose might fail at arithmetic. A model that codes brilliantly might be hopeless at creative writing.

Benchmarks try to measure this, but they're imperfect. They get gamed. They get outdated. A model that tops one leaderboard can look mediocre on another.

So when we say "bigger isn't smarter," we're not saying size doesn't matter. We're saying size is one dimension of a model that has many dimensions — and that the other dimensions have gotten much more interesting.

## The new question

If size isn't the measure, what is?

The honest answer is: it depends on what you need. For a chatbot that responds instantly, speed matters most. For a background process that runs overnight, speed matters less than cost. For a medical application, privacy might matter more than either.

The old question was "how big is it?" The new question is closer to: "how useful is it, how cheap is it, and how fast can it run — for what I'm actually doing?"

That question is harder to answer. But it's a much better one.

And it's the reason a 70-billion-parameter model can now live on a laptop.

That story — the how — is the next essay.