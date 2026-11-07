# Night Thoughts Experiments

This directory contains companion code for selected Night Thoughts articles.

Each experiment should provide:

- a focused README;
- exact setup and execution commands;
- held-out evaluation where relevant;
- limitations and intended use;
- attribution for external datasets and models;
- no secrets or large generated artifacts.

Planned experiments are not listed as completed work.

## Available Experiments

### NT Imaging Workflow

[NT Imaging Workflow](nt-imaging-workflow/): a local LangGraph/oMLX chest-radiograph drafting workflow with a deterministic Imaging Readiness Agent, durable single-worker execution, local graph inspection, and mandatory doctor review before idempotent export. Includes REAL and labelled MOCK/FAULT showcases, responsive console tests, two private-draft blog sources, and sanitized v3 evidence.

This is an Internet-accessible research showcase, not a clinically validated or institutionally hardened deployment. Its public GitHub source is readable even while the corresponding Hashnode guides remain private drafts.

### DDXPlus MLX LoRA

[DDXPlus MLX LoRA experiment](ddxplus-mlx-lora/): an educational local-AI workflow using synthetic DDXPlus cases, MLX LM LoRA, identical 490-case held-out evaluations, independent fused-model verification, and oMLX/QwenPaw deployment and rollback.

The experiment is not clinically validated and must not be used for patient care. See its README for the full metrics, reproduction stages, rejected fused artifact, licensing, and safety limitations. Datasets, weights, credentials, and private run artifacts are excluded.

### Spec Kit Expense Tracker

[Spec Kit Expense Tracker](spec-kit-expense-tracker/): a completed GitHub Copilot and Spec Kit workflow covering constitution through convergence and structured bug fixing. Includes a new React/TypeScript/Vite expense tracker, exact-cent calculations, localStorage recovery, keyboard and responsive checks, 56 Vitest tests, 17 Chromium scenarios, 16 independent production-browser checks, sanitized workflow evidence, 18 inspected images, and the article source.

The experiment is a frontend-only tutorial, not a hosted finance service. Its README documents exact versions, reproduction commands, the genuine convergence finding and contrast repair, evidence regeneration, limitations, and attribution.

### Incident Triage with Unsloth

[Incident triage with Colab, Unsloth, and QLoRA](incident-triage-unsloth/): fine-tunes `unsloth/Qwen2.5-1.5B-Instruct` with QLoRA to turn synthetic incident alerts into a strict six-field JSON object, with whole scenarios held out from training. On the same 40 held-out alerts, JSON and schema validity rose from 0.00% to 100.00% while exact-match accuracy stayed at 0.00%: the adapter learned the output interface, not the full label mapping.

Published article: [Teaching a Small Language Model to Triage Incidents](https://nightthoughts.me/teaching-a-small-language-model-to-triage-incidents-a-beginner-s-unsloth-and-qlora-tutorial). All alerts are synthetic; the model does not diagnose real infrastructure or run remediation.

### Campus Voices (Belle)

[Campus Voices](campus-voices/): Belle, a local voice application for university seminar rehearsal. It listens to what a student says, replies with spoken follow-ups and one respectful challenge, and generates closing feedback from the conversation, using a local MiniCPM-o 4.5 engine. English and Mandarin are supported; Cantonese is not claimed.

Audio is held in memory by default and nothing is sent to an external service. Feedback is not a validated assessment, and an ethics-approved pilot remains future work.

### AI Agent Engineering Feedback Loops

[AI Agent Engineering Feedback Loops](ai-agent-engineering-feedback-loops/): a small TypeScript experiment around one subscription trial-ending reminder policy, showing a requirement interview, a behavior contract and glossary, an ADR, tests written before the implementation (red, then green), and an architecture review.

The companion article source is in the folder; the Hashnode version is an unpublished draft.
