---
title: "The Harness Is the Agent: Inside Google’s Harness²"
datePublished: 2026-10-21T14:59:37.212Z
cuid: cmvi8naew000809jtc1gmblr9
slug: the-harness-is-the-agent-inside-google-s-harness
cover: https://cdn.hashnode.com/uploads/covers/6a92730f9a9aa7f72e74fdf4/8bf790e3-6e1e-41e0-b829-fa2f446437a0.jpg
tags: ai, system-design, llm, ai-agents, google-research

---

Most conversations about AI capability still start with the model. Bigger weights, more compute, longer context, better benchmarks. The model is the thing; everything else is scaffolding.

Google Research’s **Harness²** is interesting because it quietly flips that assumption. The model weights stay fixed. What changes is the **harness** around the model — the prompts, tools, memory, guardrails, subagents, scripts, plugins, and orchestration logic that decide how the model actually behaves in the world.

And the harness can rewrite itself.

That’s the core idea behind [Harness²](https://github.com/google-research/harness2): an agentic system that improves its own operating environment through **recursive self-improvement**, without retraining the underlying model and without relying on ground-truth feedback for every task.

If that sounds like a small engineering detail, it isn’t. It’s a different bet about where the next gains come from.

---

## The bottleneck is the scaffolding

Open-world tasks are messy. There’s no clean verifier sitting at the end telling the agent whether it succeeded. A coding benchmark can run tests. A job-style task — research, planning, tool use, synthesis — often can’t. You get partial signals, behavioral evidence, maybe a rubric, maybe nothing.

Harness² starts from that constraint. Instead of asking “how do we train a better model?”, it asks: **can the agent improve the harness it runs inside, using behavioral evidence from the task itself?**

The harness here is not just a system prompt. It includes the editable surface around the model: system prompt, guardrails, memory, tool guidance, subagents, skills, scripts, and plugins. Eight components, all editable. The model is the CPU. The harness is the operating system that decides how the CPU gets used.

That analogy matters. A faster CPU with a bad OS still loses. A fixed model with a better harness can look like a different agent entirely.

---

## Two levels of recursion

The technical meat of Harness² is that recursion happens at two levels.

### 1. Task-level recursion: Propose–Probe–Compose

For a given task, the system runs a contrastive loop:

- **Propose** edits to the harness.
- **Probe** those edits by observing their behavioral effects on the same task.
- **Compose** a refined harness from the contrasts.

The key detail: this happens **without ground-truth feedback**. The agent isn’t checking against a hidden answer key. It’s comparing behaviors — what changed when we edited the harness, and what does that tell us about the next edit?

That’s a subtle but important shift. The signal isn’t “correct/incorrect.” It’s “this harness produced this behavior; that harness produced that behavior; the contrast is evidence.”

### 2. Harnessing-level recursion: the improvement harness

The second level is where it gets more interesting. Harness² maintains a persistent **improvement harness** that banks adopted harnesses and evidence-backed lessons from each task. Those lessons then guide future refinement.

So recursion isn’t just about the current task. It’s about building a reusable meta-harness that accumulates experience across tasks.

![Harness² two-level recursion diagram: Task → Propose–Probe–Compose → Improvement Harness → Next Task](https://cdn.hashnode.com/uploads/gql/6a92730f9a9aa7f72e74fdf4/963d8800-9182-4a1c-9bb8-700bb696b4bf.png)

*Diagram: Harness² two-level recursion.*

The paper also distinguishes **parallel recursion** — exploring wider by testing multiple candidate edits — from **sequential recursion** — refining deeper by chaining Propose–Probe–Compose steps. That’s the test-time scaling hook: more recursion buys more exploration or more depth.

---

## What the benchmarks actually say

The headline numbers are concrete:

- **Up to +11.5 points on WorkBuddy-Bench**
- **+4.5 on JobBench**
- **+11.8 percentage points on LAB partial pass rate**

Those are not trivial gains. But the more important claim is architectural: the improvement comes from editing the harness, not from changing the model.

If that generalizes, the implication is uncomfortable for the “just scale the model” narrative. The next leap in agent capability may come less from a bigger model and more from a model that can **rewrite its own operating environment between tasks**.

---

## What using it actually looks like

The repo keeps the demo path reasonably light: Linux, Python 3.12, and `uv`. The local demo needs no credentials. Model-backed benchmarks need Vertex AI plus Node and benchmark dependencies — Docker for WorkBuddy, Pandoc/Poppler for LAB. Executor choices include **OpenCode** as the default and **Codex**.

That’s the practical surface. The conceptual surface is more interesting: you’re not just running an agent. You’re running an agent that is editing the thing that runs it.

---

## Three late-night caveats

**1. The guardrail file is not a security boundary.**  
Editable guardrails are part of the harness, not a hard safety sandbox. If the harness can rewrite itself, the safety story has to live somewhere else — outside the editable surface.

**2. Task-specificity risk.**  
The improvement harness is supposed to accumulate lessons that transfer. But benchmarks are benchmarks. Does it generalize to genuinely novel tasks, or does it overfit to the shape of the evaluation suite? The paper claims transfer; this is exactly the kind of claim that deserves independent replication.

**3. Open-world evaluation is messy.**  
Public rubrics may be online. Network access is unrestricted in executors. Reproducibility and contamination are live questions. That doesn’t invalidate the results, but it does mean the numbers should be read as evidence, not gospel.

---

## The takeaway

Harness² is a reminder that the agent is not just the model. It’s the model plus the environment it can edit. And if the harness is the thing that learns, then the important questions shift: how do we evaluate a system that changes its own operating environment? How do we deploy it safely when the guardrails are editable? And what does it mean for trust if the scaffolding is recursive?

The model weights are fixed. The harness is not. That’s the whole bet.

---

*Links: [Harness² GitHub](https://github.com/google-research/harness2)*