# Implementation Plan: Expense Tracker

**Branch**: `001-expense-tracker` | **Date**: 2026-11-03 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-expense-tracker/spec.md` and the user-provided React, TypeScript, Vite, testing, accessibility, and demo-mode requirements.

## Summary

Build a polished, responsive, frontend-only expense tracker for one person. Use React and TypeScript with Vite; keep exact-cent validation and calculations in pure domain modules, localStorage behind a typed adapter, and the dashboard/forms in React UI. Cover business rules and important interactions with Vitest and React Testing Library, then verify persistence recovery, native-dialog focus, strict demo isolation, and responsive layouts in Playwright Chromium.

## Technical Context

**Language/Version**: TypeScript with React; browser-targeted ES2022 or newer.

**Primary Dependencies**: React, Vite, Vitest, React Testing Library, `@testing-library/user-event`, jsdom, and Playwright with Chromium.

**Storage**: Browser `localStorage`, accessed through one adapter; persisted records contain integer cents and local `YYYY-MM-DD` dates. Demo mode is in-memory only.

**Testing**: Vitest for pure domain, persistence-adapter, and RTL UI tests; Playwright Chromium for a small set of real-browser flows and screenshots.

**Target Platform**: Current desktop and mobile browsers with native `<dialog>` support; no server or backend.

**Project Type**: Single-page frontend web application.

**Performance Goals**: No numerical latency target or user study is in scope for this small demonstration. Keep interactions and summary updates responsive for a small personal dataset; no network requests or server-side processing are involved.

**Constraints**: Positive exact USD cents only, no more than USD 100,000.00 per expense; en-US display with two decimal places; announce unsafe aggregate errors instead of rounding; local calendar month boundaries without UTC conversion; persistence failures and malformed data must be visible and must not silently overwrite data; only the exact `?demo=1` query enables demo mode, which must not access or listen to real expense storage.

**Scale/Scope**: One user, one browser, one dashboard, five fixed categories, and a concise tutorial-sized codebase. No accounts, synchronization, currency conversion, backend, or general-purpose state-management layer.

## Constitution Check

*GATE: Pass before Phase 0 research; re-checked after Phase 1 design.*

| Principle | Plan decision | Gate |
|---|---|---|
| I. Exact Monetary Arithmetic | Parse and calculate integer cents; cap each expense at USD 100,000.00; announce unsafe aggregate errors instead of rounding; format only at the UI boundary. | Pass |
| II. Accessible Keyboard-First Interactions | Use semantic, named controls, announced validation/status/aggregate errors, and a native modal dialog with Cancel focus, keyboard containment, and specified focus restoration after cancel or deletion. | Pass |
| III. Meaningful Business-Logic Testing | Test validation, local date boundaries, totals, filtering, and stable sorting separately from UI tests. | Pass |
| IV. Separation of Concerns | Keep pure domain logic, the persistence adapter, deterministic demo data, and React presentation in separate small modules. | Pass |
| V. Confirmed Destructive Actions | Require confirmation before permanent deletion; cancellation does not mutate data. | Pass |
| VI. Visible Persistence Outcomes | Announce load/save/malformed-data failures; retain failed-write work in memory, restore durable data on reload, and persist the full current collection after a later success. Require informed start-fresh confirmation and preserve malformed raw data on failure. | Pass |
| Proportionate Delivery | Use one frontend project and only the requested test tools; no backend, routing, global state package, or elaborate service layers. | Pass |

No constitution violations or unresolved requirement clarifications remain.

## Project Structure

### Documentation (this feature)

```text
specs/001-expense-tracker/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── ui.md
└── tasks.md
```

### Source Code (project root)

```text
src/
├── main.tsx
├── App.tsx
├── styles.css
└── expenses/
    ├── model.ts
    ├── domain.ts
    ├── persistence.ts
    └── demo.ts

tests/
├── domain.test.ts
├── persistence.test.ts
└── App.test.tsx

e2e/
└── expenses.spec.ts
```

**Structure Decision**: One Vite application. The `expenses` modules own typed domain data, pure rules/calculations, storage, and fixture data; `App.tsx` owns the small React experience. Unit/component tests stay in one test directory and a concise `e2e/` suite uses a real browser. This keeps the boundaries explicit without introducing a separate backend or extra architectural layers.

## Post-Design Constitution Check

The proposed data model and contracts retain integer cents and the per-expense cap, date-only local calendar strings, accessible keyboard interactions, explicit deletion and start-fresh confirmations, durable-versus-memory persistence outcomes, malformed-data preservation, and isolated exact-query demo mode. The test plan covers safe aggregate boundaries, failed read/write recovery, full-collection saves, focus fallbacks, and zero demo storage access. No new dependencies or layers weaken the initial gate. **Pass.**
