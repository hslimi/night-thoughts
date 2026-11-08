# Night Thoughts Experiments

This directory contains companion code for published Night Thoughts articles.

Each experiment provides:

- a focused README;
- exact setup and execution commands;
- held-out evaluation where relevant;
- limitations and intended use;
- attribution for external datasets and models;
- no secrets or large generated artifacts.

## Available Experiments

### OpenCode Multi-Model Harness

[OpenCode Multi-Model Harness](opencode-multi-model-harness/): configs, test scripts and sanitized evidence for a low-cost and a Claude-based OpenCode Desktop setup, tested with deliberate provider failures.

This is a candidate harness, with its gaps listed in [the protocol results](opencode-multi-model-harness/evidence/protocol-results.md).

### DDXPlus MLX LoRA

[DDXPlus MLX LoRA experiment](ddxplus-mlx-lora/): an educational local-AI workflow using synthetic DDXPlus cases, MLX LM LoRA, identical 490-case held-out evaluations, independent fused-model verification, and oMLX/QwenPaw deployment and rollback.

The experiment is not clinically validated and must not be used for patient care. See its README for the full metrics, reproduction stages, rejected fused artifact, licensing, and safety limitations. Datasets, weights, credentials, and private run artifacts are excluded.

### Spec Kit Expense Tracker

[Spec Kit Expense Tracker](spec-kit-expense-tracker/): a completed GitHub Copilot and Spec Kit workflow covering constitution through convergence and structured bug fixing. Includes a new React/TypeScript/Vite expense tracker, exact-cent calculations, localStorage recovery, keyboard and responsive checks, 56 Vitest tests, 17 Chromium scenarios, 16 independent production-browser checks, sanitized workflow evidence, 18 inspected images, and the article source.

The experiment is a frontend-only tutorial, not a hosted finance service. Its README documents exact versions, reproduction commands, the genuine convergence finding and contrast repair, evidence regeneration, limitations, and attribution.

### Incident Triage with Unsloth

[Incident triage with Colab, Unsloth, and QLoRA](incident-triage-unsloth/): fine-tunes `unsloth/Qwen2.5-1.5B-Instruct` with QLoRA to turn synthetic incident alerts into a strict six-field JSON object, with whole scenarios held out from training. On the same 40 held-out alerts, JSON and schema validity rose from 0.00% to 100.00% while exact-match accuracy stayed at 0.00%: the adapter learned the output interface, not the full label mapping.

Published article: [Teaching a Small Language Model to Triage Incidents](https://nightthoughts.me/teaching-a-small-language-model-to-triage-incidents-a-beginner-s-unsloth-and-qlora-tutorial). All alerts are synthetic; the model does not diagnose real infrastructure or run remediation.
