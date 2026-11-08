# Analysis Remediation: Expense Tracker

This record documents resolutions to findings A1, A2, D1, and G1 in [`evidence/workflow/analysis-original.md`](../../evidence/workflow/analysis-original.md).

## A1 — Performance goal is not objectively verifiable

**Resolution:** The plan now explicitly states that no numerical latency target is in scope for this small demonstration. Responsiveness remains a qualitative expectation for a small personal dataset, without introducing a benchmark or dataset-size acceptance criterion.

**Updated artifact:** [`plan.md`](./plan.md), Performance Goals.

## A2 — Timed usability outcome lacks a repeatable protocol

**Resolution:** SC-001 no longer specifies a timed usability study. It is now a functional Chromium browser check: create an expense with amount, category, date, and note; verify all entered details in the transaction list and after reload.

**Updated artifacts:** [`spec.md`](./spec.md), SC-001; [`tasks.md`](./tasks.md), T006 and T016; [`quickstart.md`](./quickstart.md), automated browser validation.

## D1 — Failed-write recovery is duplicated

**Resolution:** FR-012 is the authoritative requirement for failed-write behavior, including in-memory retention, unchanged durable data, reload restoration, and full-collection recovery saves. FR-005 now covers successful persistence and points to FR-012 for the shared failure behavior. No recovery behavior was removed.

**Updated artifact:** [`spec.md`](./spec.md), FR-005 and FR-012.

## G1 — SC-001 has no matching validation task

**Resolution:** The revised browser-check criterion is covered by the existing test-first tasks: T006 adds keyboard-driven creation and save/reload browser coverage, and T016 runs the final Chromium checks. The matching checks are also required in the quickstart. No usability-study task was added.

**Updated artifacts:** [`tasks.md`](./tasks.md), T006 and T016; [`quickstart.md`](./quickstart.md), automated browser validation.

## Scope preserved

The plan remains 16 tasks, with tests preceding implementation for each user story. Browser validation explicitly requires keyboard-driven create, edit, filter, sort, and delete checks, plus no page-level horizontal overflow at 390x844, 768x1024, and 1440x900. Application source has not been implemented as part of this remediation.
