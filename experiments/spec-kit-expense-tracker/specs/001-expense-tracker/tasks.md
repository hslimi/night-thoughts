---

description: "Dependency-ordered implementation tasks for Expense Tracker"
---

# Tasks: Expense Tracker

**Input**: Design documents in `specs/001-expense-tracker/`

**Prerequisites**: `plan.md`, `spec.md`, `data-model.md`, `contracts/ui.md`, `research.md`, `quickstart.md`

**Organization**: Tasks are ordered by setup, shared foundation, then independently testable user stories in priority order. Tests are written before their corresponding implementation.

## Phase 1: Setup

**Purpose**: Establish the React, TypeScript, Vite, and test-tool project.

- [X] T001 Initialize `package.json`, `index.html`, `tsconfig.json`, and `vite.config.ts` for React + TypeScript + Vite; add Vitest, React Testing Library, user-event, jsdom, and Playwright Chromium dependencies and `dev`, `test`, `test:e2e`, and `build` scripts.
- [X] T002 Configure Vitest/jsdom and Playwright Chromium in `vite.config.ts`, `tests/setup.ts`, and `playwright.config.ts`, including a Vite web server for browser tests.

---

## Phase 2: Foundational Checkpoint

**Purpose**: Prove the test runner works before creating application source.

- [X] T003 Add a minimal render smoke test in `tests/App.test.tsx` that imports `src/App.tsx`; run `npm run test -- tests/App.test.tsx` and confirm it fails specifically because `src/App.tsx` is missing, not because test tooling is broken. Keep application source absent for this checkpoint.

**Checkpoint**: The test command runs and reports the expected missing-App failure before any application source is added.

---

## Phase 3: User Story 1 - Record expenses (Priority: P1) 🎯 MVP

**Goal**: Create valid expenses, preserve successful saves across reloads, clearly handle persistence and malformed-data outcomes, and keep opt-in demo data isolated.

**Independent Test**: Add a valid expense with an optional note and reload to verify every detail persists. Verify invalid amounts are rejected with correction guidance, storage failures are visible and recoverable as specified, malformed data is preserved until informed confirmation, and exact-query demo mode never accesses real expense storage.

### Tests for User Story 1

> Write and run these tests before implementing the corresponding domain, persistence, or UI behavior.

- [X] T004 [P] [US1] Add `tests/domain.test.ts` cases for exact amount syntax and cent conversion (accept `1`, `1.2`, `1.20`, USD 0.01, and USD 100,000.00; reject blank, zero, negative, signed, whitespace-padded, comma-separated, currency-prefixed, exponent, nonnumeric, over-precision, and USD 100,000.01); cover allowed categories, real `YYYY-MM-DD` dates, trimmed/omitted notes, and future local dates.
- [X] T005 [P] [US1] Add `tests/persistence.test.ts` cases for validated version-1 envelopes, read retry errors, failed-write durability and in-memory retention, full-collection save after recovery, malformed raw-value preservation and blocked writes, and informed start-fresh success/failure.
- [X] T006 [US1] Extend `tests/App.test.tsx` and begin `e2e/expenses.spec.ts` with keyboard-driven create, validation/accessibility, and save/reload flows; cover visible load/write failures and retry, malformed-data warning and confirmation, and exact `?demo=1` isolation, in-memory interactions, reload determinism, and non-exact query strings.

### Implementation for User Story 1

- [X] T007 [US1] Define the `Expense` and category types plus pure amount, category, date, note, and local-calendar validation in `src/expenses/model.ts` and `src/expenses/domain.ts`; represent money as positive integer cents capped at 10,000,000 cents.
- [X] T008 [US1] Implement the typed localStorage adapter in `src/expenses/persistence.ts` using one app-owned key and `{ "version": 1, "expenses": [...] }`; validate every record, distinguish load errors from malformed data, preserve raw malformed values, and expose explicit save/start-fresh outcomes without silently replacing durable data.
- [X] T009 [US1] Implement the app entry, accessible create form, expense list, persistence status/retry and informed start-fresh UI, responsive base layout, and exact-query demo isolation in `src/main.tsx`, `src/App.tsx`, `src/styles.css`, and deterministic fixtures in `src/expenses/demo.ts`; demo mode must not read, write, or register storage-event listeners for real expenses.

**Checkpoint**: US1 creation and reload work; amount validation and persistence failure/malformed-data outcomes are visible; demo behavior is isolated.

---

## Phase 4: User Story 2 - Review monthly spending (Priority: P2)

**Goal**: Review exact monthly and category totals, then filter and stably sort the selected month's transactions.

**Independent Test**: With expenses across months and categories, verify month scoping, every category total including zeros, exact safe totals and announced overflow errors, filter/sort behavior and defaults, distinct empty states, and future expenses appearing only in their local calendar month.

### Tests for User Story 2

> Add these tests before implementing the derived selectors and dashboard controls.

- [X] T010 [US2] Extend `tests/domain.test.ts`, `tests/App.test.tsx`, and `e2e/expenses.spec.ts` for local-month totals and category breakdowns, safe-integer aggregate boundaries and announced overflow, keyboard-driven category filtering and date/amount sorting in both directions with stable ties and defaults, month selection, future-date scoping, zero categories, and distinct empty-month/filter-result actions.

### Implementation for User Story 2

- [X] T011 [US2] Add pure monthly/category total, safe aggregate, category-filter, and stable-sort selectors in `src/expenses/domain.ts`; scope by local `YYYY-MM` without UTC conversion and preserve source order for equal sort keys.
- [X] T012 [US2] Add the current-local-month picker, totals for all five categories, accessible filter/sort controls, USD formatting, announced unsafe-total errors, and distinct empty-month/filter-result states in `src/App.tsx` and `src/styles.css`.

**Checkpoint**: US2 passes its independent dashboard, boundary, filter, sort, and empty-state tests.

---

## Phase 5: User Story 3 - Correct or remove expenses (Priority: P3)

**Goal**: Edit expenses with creation-equivalent validation and permanently delete only after accessible confirmation.

**Independent Test**: Edit an expense across amount/category/month and verify both affected summaries; cancel deletion without mutation and restore invoker focus; confirm deletion and verify no undo, updated summaries, and next/previous/Add focus fallback.

### Tests for User Story 3

> Add these tests before implementing edit and deletion behavior.

- [X] T013 [US3] Extend `tests/App.test.tsx` and `e2e/expenses.spec.ts` for keyboard-driven editing and deletion, edit validation and summary updates, native-dialog accessible title and initial Cancel focus, focus containment, Escape/Cancel without mutation and invoker focus restoration, permanent confirmed deletion, and next/previous/Add focus fallback in current filtered/sorted order.

### Implementation for User Story 3

- [X] T014 [US3] Implement editing of amount, category, date, and optional note with the same validation and save outcomes as creation in `src/App.tsx`; ensure moving a record between months or categories updates both affected summaries.
- [X] T015 [US3] Implement permanent deletion through a native `<dialog>` in `src/App.tsx` and `src/styles.css`, with Cancel initially focused, keyboard containment, Escape/Cancel focus restoration, and confirmed-delete focus fallback in current visible order.

**Checkpoint**: US3 edit and delete flows pass their independent keyboard, persistence, and summary tests.

---

## Phase 6: Polish & Cross-Cutting Validation

**Purpose**: Verify the full acceptance set and documented run commands.

- [X] T016 Run `npm run test`, `npm run test:e2e`, and `npm run build`; complete the Chromium checks in `e2e/expenses.spec.ts` for durable reload/recovery, malformed-data start-fresh outcomes, demo isolation, keyboard-driven create/edit/filter/sort/delete and focus behavior, and layouts at 390x844, 768x1024, and 1440x900 with no page-level horizontal overflow, following `specs/001-expense-tracker/quickstart.md`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: T001 precedes T002; no application source is created.
- **Foundational checkpoint (Phase 2)**: T003 follows test-runner setup and must produce the expected missing-`src/App.tsx` failure before implementation.
- **US1 (Phase 3)**: Depends on the checkpoint. T004 and T005 are independent test-first work; T006 follows T003 because it extends the smoke test. Implementation follows the relevant tests: model/domain (T007), persistence (T008), then app integration and demo mode (T009).
- **US2 (Phase 4)**: Depends on US1 records and app shell. T010 tests precede domain selectors (T011) and dashboard UI (T012).
- **US3 (Phase 5)**: Depends on US1 persistence and US2 summaries/list ordering. T013 tests precede edit (T014) and deletion dialog (T015).
- **Polish (Phase 6)**: T016 follows all desired stories.

### User Story Dependencies

- **US1 (P1)**: Starts after the foundational checkpoint; no dependency on another story.
- **US2 (P2)**: Builds on the US1 expense collection and app shell.
- **US3 (P3)**: Builds on US1 persistence and US2 summaries and visible transaction ordering.

### Parallel Opportunities

- T004 and T005 can be authored in parallel after T003 because they cover separate test files.
- After T007, domain selectors and their tests can be developed independently of UI styling where their files do not overlap; UI integration must wait for the selector contract.
- Browser test authoring can be split by user story only after its prerequisite test setup; application tasks touching `src/App.tsx` remain sequential.

## Implementation Strategy

1. Complete setup and verify the early missing-App test failure before creating application source.
2. Deliver US1 as the MVP, including validation, successful persistence, explicit recovery/error states, and isolated exact-query demo mode.
3. Add US2 monthly summaries and transaction views, then US3 edit and confirmed deletion.
4. Run all quickstart validation commands and the compact Playwright suite after the desired stories are complete.

## Phase 7: Convergence

- [X] T017 Coordinate confirmed deletion with active edit state: clear the draft and exit edit mode after confirmed deletion; ensure the no-neighbor focus fallback targets the Add expense submit button. Add component and Chromium regressions and record verification in `evidence/verification/convergence-T017.txt`.
