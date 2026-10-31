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

[Spec Kit Expense Tracker](spec-kit-expense-tracker/): a frontend-only React, TypeScript, and Vite expense tracker with exact integer-cent arithmetic, local persistence recovery, deterministic demo data, responsive layouts, and a complete specification-to-verification trail. Includes 260 unit tests, 167 passing Chromium checks, production-browser evidence, a verified month-clear bug fix, and a separate read-only Copilot analysis.

Final convergence found no new gaps, but full convergence remains open because VoiceOver review and its dependent accessibility gate were not completed. See the experiment README for reproduction commands, versions, evidence, limitations, and article source.
