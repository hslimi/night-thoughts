---
description: "Test-first implementation tasks for Personal Expense Tracker"
---

# Tasks: Personal Expense Tracker

**Input**: Design documents from `/specs/001-expense-tracker/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/ui-contract.md, quickstart.md

**Tests**: Test-first implementation is mandatory. Write the listed domain, persistence, UI, and browser tests before their corresponding implementation, run them against the missing or incomplete behavior, and confirm meaningful failures before proceeding.

**Organization**: Tasks are grouped by user story. Quickstart case IDs remain the acceptance identifiers, and the traceability section maps every functional requirement to its verification tasks.

**Consolidation**: Redundant per-file/module implementation and related verification suites were combined to reduce 73 tasks to **50 tasks** without dropping requirements, named quickstart cases, test-first checkpoints, manual reviews, traceability, or any of the eight Playwright suites.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel with other marked tasks in the same group because files and dependencies do not conflict.
- **[Story]**: US1–US5 map to the user stories in spec.md.
- All paths are relative to the repository root.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish the application and test toolchain without implementing application source.

- [X] T001 Initialize `package.json` with React, ReactDOM, TypeScript 5.x, Vite and its React plugin, Vitest, jsdom, React Testing Library, Testing Library user events and jest-dom assertions, Playwright, and `@axe-core/playwright`; define `dev`, `build`, `test:unit`, and `test:e2e` scripts using Node.js 20+.
- [X] T002 [P] Configure strict TypeScript and Vite React compilation in `tsconfig.json` and `vite.config.ts`, separating browser-test files from the Vitest run.
- [X] T003 [P] Configure Vitest with jsdom and shared Testing Library setup in `vitest.config.ts` and `src/test/setup.ts`, including cleanup and accessible-query assertions without adding application code.
- [X] T004 [P] Configure Playwright reference Chromium, the local Vite web server, fixed desktop/mobile contexts, and failure diagnostics in `playwright.config.ts`; do not configure Firefox or WebKit as acceptance targets.
- [X] T005 [P] Create the semantic HTML entry shell and application mount point in `index.html` without creating `src/App.tsx` or other application source.
- [X] T006 Add a runnable smoke test that imports the not-yet-created App and expects the Personal Expense Tracker heading in `tests/ui/app.smoke.test.tsx`.
- [X] T007 Install dependencies and generate `package-lock.json`, then run `npm run test:unit` and confirm T006 fails because `src/App.tsx` does not exist rather than because the test toolchain is broken.

**Checkpoint — early runnable red**: T006 executes and fails for the intended missing application behavior before any application source implementation. Do not proceed until the runner itself is working.

---

## Phase 2: Foundational (Blocking Test Infrastructure)

**Purpose**: Provide reusable, deterministic test infrastructure shared by every story.

**Critical**: No user-story implementation begins before this phase and the red checkpoint are complete.

- [X] T008 [P] Create reusable valid-expense, draft, version-1-envelope, fixed-local-clock, and independent exact-cent summary builders in `tests/fixtures/expenses.ts`, keeping expectations independent of application calculation functions.
- [X] T009 [P] Create helpers that label automated results with quickstart case ID, precondition, input, and actual outcome in `tests/fixtures/verification.ts`, preserving the named case sets used by `specs/001-expense-tracker/quickstart.md`.

**Checkpoint**: Test setup and shared fixtures are ready; the only expected red application test is still caused by unimplemented behavior.

---

## Phase 3: User Story 1 - Record Expenses and Review Monthly Spending (Priority: P1) — MVP

**Goal**: Add valid expenses and review exact transactions and totals for any selected local month.

**Independent Test**: Add expenses on different dates and in different categories, select each affected month, and verify the transaction list, monthly total, and category totals without editing, deletion, filtering, sorting, or durable persistence.

### Tests for User Story 1 — write and confirm red first

- [X] T010 [P] [US1] Cover AMOUNT-001–008 and MONEY-001/002 plus accepted-value parsing for MONEY-004 in `tests/domain/money.test.ts`, proving exact integer-cent parsing, all accepted/rejected syntax, the `999999999.99` USD maximum, no floating-point input conversion or rounding, and fixed en-US USD formatting including `$0.00` and `$1,234.56`.
- [X] T011 [P] [US1] Cover CORE-003/004 and expense record invariants in `tests/domain/expense.test.ts`, including all five categories, invalid-category rejection, stable nonempty unique IDs, positive safe integer cents, blank/whitespace note omission, exact nonblank note preservation, and rejection of invalid persisted records.
- [X] T012 [P] [US1] Cover CORE-001/002, DATE-001–004, and the pure-domain part of OVERFLOW-001 in `tests/domain/dates.test.ts` and `tests/domain/dashboard.test.ts`, including exact local dates, first/last-day membership, leap-year February, future months, fixed current-local-month derivation, non-UTC timezone independence, exact monthly/five-category totals, explicit zeros, and safe-integer aggregate errors with unchanged records.
- [X] T013 [P] [US1] Cover every AMOUNT row for add, CORE-001–004, DATE-001/003, and the UI part of OVERFLOW-001 in `tests/ui/addExpense.test.tsx` and `tests/ui/monthlyDashboard.test.tsx`, asserting no mutation on rejection, first-invalid-field focus, associated announced text/icon errors, preserved valid note input, selected-month membership, all category totals, future-month isolation, visible recalculation, and announced calculation errors instead of apparently valid unsafe totals.
- [X] T014 [P] [US1] Add reference-Chromium CORE-001–004, DATE-001–004, and MONEY-001–003 scenarios in `e2e/core.spec.ts`, including fixed local clock/timezone, keyboard add/month selection, exact rendered results, and identical fixed en-US USD transaction and monthly/category summary output under both `en-US` and `de-DE` locales.

### Implementation for User Story 1

- [X] T015 [US1] Define expense/category/draft/local-date types and validation in `src/domain/expense.ts` and `src/domain/dates.ts`: stable nonempty unique IDs; positive safe integer cents from `1` through `99999999999`; exactly the five categories; blank-note normalization and exact nonblank notes; exact local `YYYY-MM-DD` validation with leap-year/month-length rules; `month = date.slice(0, 7)` after validation; lexical chronological dates; and local getters only for the initial current month, with no UTC conversion.
- [X] T016 [P] [US1] Implement the exact amount grammar `(?:\d+(?:\.\d{1,2})?|\.\d{1,2})`, direct positive integer-cent conversion, zero/above-maximum rejection, and fixed `en-US` USD display formatting in `src/domain/money.ts`, reusing the same parser contract needed by add and edit.
- [X] T017 [P] [US1] Implement selected-month membership and checked exact integer monthly/category summaries in `src/domain/dashboard.ts`, returning an aggregate-error result on every unsafe addition while preserving the source records and all five explicit zero totals.
- [X] T018 [US1] Implement normal-mode in-memory expenses, stable unique ID generation, valid add, selected-month state, and derived dashboard state in `src/state/useExpenseStore.ts`, keeping the selected month unchanged after add and leaving persistence behind a later story boundary.
- [X] T019 [P] [US1] Build the accessible reusable add form and announced status presentation in `src/components/ExpenseForm.tsx` and `src/components/StatusMessage.tsx`, with labeled amount/category/date/note controls, shared validation, associated errors, first-invalid-field focus, text/icon meaning rather than color alone, and blank-note normalization.
- [X] T020 [US1] Build the month selector, summaries, and semantic newest-first transaction list in `src/components/Dashboard.tsx` and `src/components/TransactionList.tsx`; integrate the store and components in `src/App.tsx` and `src/main.tsx`; and add the polished responsive baseline in `src/styles.css`, including announced unsafe totals, exact fixed-locale values, visible focus, accessible contrast, non-color status meaning, 24-by-24-CSS-pixel minimum targets, reduced motion, and mobile reflow. Make the smoke test and all US1 tests pass without storage access.

**Checkpoint**: US1 domain, UI, and Chromium tests pass; adding and monthly review work independently with exact local-date and money behavior.

---

## Phase 4: User Story 2 - Retain Expenses Across Browser Sessions (Priority: P1)

**Goal**: Restore valid expenses after reload and handle unavailable, malformed, and failed persistence visibly and non-destructively.

**Independent Test**: Save representative expenses, reload, and compare every transaction and summary; separately inject missing, malformed, unreadable, quota, serialization, and mid-session storage failures and verify guarded recovery, retained memory, and durable reload outcomes.

### Tests for User Story 2 — write and confirm red first

- [X] T021 [P] [US2] Cover PERSIST-001–008/011–013 and MONEY-004 in `tests/persistence/expenseStorage.load.test.ts` and `tests/persistence/expenseStorage.write.test.ts`: classify missing/valid/malformed/invalid-version/invalid-record/duplicate-ID/unreadable data all-or-nothing; inject quota, serialization, and mid-session access failures; prove complete-current-collection saves and later success; and round-trip every accepted AMOUNT-001–003 input through persistence, inspecting both stored JSON and reloaded values for exact integer-cent numbers rather than dollar floats or rounded values.
- [X] T022 [P] [US2] Cover RECOVERY-001–007 and failed-add/later-success behavior from PERSIST-008/011–013 in `tests/ui/recovery.test.tsx` and `tests/ui/persistenceStatus.test.tsx`, asserting guarded empty memory, both replacement confirmations, Cancel/Escape no-write behavior, safe Cancel focus and restoration, success and failed-replacement retention, task-associated announced non-color warnings, no durability claim on failure, and warning clearance only after a complete durable save.
- [X] T023 [P] [US2] Add reference-Chromium PERSIST-001–008/011–013 and RECOVERY-001–007 scenarios in `e2e/persistence.spec.ts`, seeding before initialization, comparing readable malformed raw strings byte-for-byte, counting writes for unreadable data, injecting real failures, and verifying reload and native-dialog behavior.

### Implementation for User Story 2

- [X] T024 [US2] Implement the sole real localStorage boundary in `src/persistence/expenseStorage.ts` using key `personal-expense-tracker:expenses:v1`, a strict version-1 envelope, all-or-nothing domain validation, duplicate-ID rejection, JSON serialization, and discriminated missing/valid/readable-malformed/unreadable/saved/write-failed results.
- [X] T025 [US2] Integrate all normal persistence and recovery transitions in `src/state/useExpenseStore.ts`: restore valid collections without duplication; start readable-malformed or unreadable data in empty guarded memory with no pre-confirmation write; retain optimistic complete-collection add work on failure; save all retained work on later success; clear warnings only after durable success; and implement start-fresh, first-replacement-save, cancellation, confirmed success, and failed replacement using respectively an empty envelope or the complete current in-memory collection.
- [X] T026 [US2] Implement the reusable native `<dialog>` in `src/components/ConfirmDialog.tsx` and wire recovery and persistence feedback through `src/App.tsx`, `src/components/Dashboard.tsx`, and `src/components/StatusMessage.tsx`, including `showModal()`, accessible name/description, irreversible-replacement explanation, Cancel initial focus, native containment, Escape/Cancel without mutation or write, requester focus restoration, guarded-save actions, and distinct readable/unreadable and ordinary-unsaved-change messaging.

**Checkpoint**: US2 persistence, recovery, UI, and Chromium tests pass; valid data survives reload and no guarded state writes before informed confirmation.

---

## Phase 5: User Story 3 - Correct and Safely Remove Transactions (Priority: P2)

**Goal**: Edit every expense field with shared validation and permanently delete only after explicit accessible confirmation.

**Independent Test**: Edit each field and verify same-month and cross-month recalculation; exercise deletion Cancel, Escape, confirmation, focus behavior, and failed durable writes without relying on filtering, sorting, or demo mode.

### Tests for User Story 3 — write and confirm red first

- [X] T027 [P] [US3] Cover every AMOUNT row for edit plus CORE-004/005 in `tests/ui/editExpense.test.tsx`, asserting identical add/edit validation, unchanged original records and summaries on rejection, first-invalid-field focus, same-ID updates, both cross-month directions, selected-month stability, visible same-month edit-requester focus restoration, move announcement, and month-control focus.
- [X] T028 [P] [US3] Cover DELETE-001–003 and deletion formatting for MONEY-003 in `tests/ui/deleteExpense.test.tsx`, asserting exact amount/category/date identity, no-undo consequence text, accessible dialog naming, Cancel initial focus, cancellation without mutation, only-target removal, recalculation, next-visible/previous-visible/Add expense focus fallbacks, fixed-locale values, and no undo.
- [X] T029 [P] [US3] Add reference-Chromium edit/delete scenarios for CORE-005, DELETE-001–004, PERSIST-009/010, and deletion MONEY-003 in `e2e/edit-delete.spec.ts`, proving native Tab/Shift+Tab containment, Escape/restoration, failed edit/delete reload outcomes, fixed-locale dialog values, deterministic unfiltered post-deletion focus, and updates visible within 2 seconds.

### Implementation for User Story 3

- [X] T030 [US3] Implement same-ID editing and confirmed only-target deletion with complete-collection durable saves in `src/state/useExpenseStore.ts`, applying shared validation, leaving originals unchanged on invalid input, recalculating affected months, preventing mutation before confirmation, and retaining only in-memory edits/removals plus warnings after write failure.
- [X] T031 [P] [US3] Extend `src/components/ExpenseForm.tsx` for editing with existing-value population, identical amount/date/category/note validation, accessible edit feedback, and valid nonblank note preservation.
- [X] T032 [US3] Extend `src/components/ConfirmDialog.tsx` for deletion identification and no-undo text, add keyboard-operable edit/delete requesters in `src/components/TransactionList.tsx`, and integrate edit/delete tasks in `src/App.tsx`: restore a visible same-month edit requester; announce cross-month moves and focus the month control; after deletion focus the next visible edit requester, else the previous visible requester, else Add expense; preserve durable-failure feedback and stable record identity.

**Checkpoint**: US3 edit/delete UI and Chromium tests pass, including failed-write reload restoration and all dialog focus requirements.

---

## Phase 6: User Story 4 - Focus and Order the Transaction List (Priority: P3)

**Goal**: Filter only the visible transaction list and sort by local date or exact cents with deterministic ties, distinct useful empty states, and deterministic integrated edit/delete focus.

**Independent Test**: With a multi-category, multi-date month, apply every category filter and both date/amount directions, verify membership/order and unchanged summaries/raw records, then exercise empty-month and no-match actions independently of add/edit/delete.

**Integrated Focus Test**: Complete CORE-006 by editing a record out of the active category filter without changing its month, and DELETE-005 by deleting the last visible filtered result while other month records remain hidden.

### Tests for User Story 4 — write and confirm red first

- [X] T033 [P] [US4] Cover FILTER-001/002 and SORT-001/002 in `tests/domain/dashboard.list.test.ts`, using `tie-a`, `tie-b`, and `tie-c` to prove exact membership, both fields/directions, ID-ascending ties in both directions, nonmutation, and summaries based on the unfiltered month.
- [X] T034 [P] [US4] Cover FILTER-001/002, SORT-001/002, EMPTY-001/002, CORE-006, and DELETE-005 in `tests/ui/transactionPreferences.test.tsx`, asserting list-only filtering, stable unfiltered summaries, result announcements, distinct non-error empty states, add-action amount focus, clear-action filter focus, same-month filtered-edit announcement and category-filter focus, and deletion of the last visible result with Clear filter focus.
- [X] T035 [P] [US4] Add keyboard-driven reference-Chromium FILTER, SORT, EMPTY, CORE-006, and DELETE-005 scenarios in `e2e/transaction-list.spec.ts`, verifying all categories, all orderings/ties, unchanged durable raw data and unfiltered summaries, restored results, same-month edit focus when visible and when filtered out, every next/previous/Clear filter/Add expense deletion fallback, visible focus, and each update within 2 seconds.

### Implementation for User Story 4

- [X] T036 [US4] Implement pure category filtering and date/exact-cent comparators with `id` ascending as the secondary order in both directions in `src/domain/dashboard.ts`, deriving from month expenses without mutating source order or summary inputs.
- [X] T037 [US4] Add ephemeral category/sort preferences with defaults `all`, `date`, and `desc` in `src/state/useExpenseStore.ts` and integrate the controls and derived views in `src/components/TransactionList.tsx` and `src/components/Dashboard.tsx`: labeled filter/sort controls, distinct empty states and actions, result announcements, unchanged durable data and unfiltered summaries, same-month filtered-edit announcement and category-filter focus, and the complete next-visible/previous-visible/Clear filter/Add expense deletion focus order.

**Checkpoint**: US4 domain, UI, and Chromium tests pass; every FILTER, SORT, EMPTY, CORE-006, and DELETE-005 case is independently verified.

---

## Phase 7: User Story 5 - Capture Fictional Demo Evidence (Priority: P3)

**Goal**: Provide an explicitly activated, repeatable fictional demo whose complete interactions never read, write, or listen to real storage.

**Independent Test**: Save known real data, open normal and demo modes separately, compare repeated baseline sessions and navigation/history resets, and instrument storage before initialization through every interaction with populated, missing, malformed, unreadable, and concurrent-normal-tab preconditions.

### Tests for User Story 5 — write and confirm red first

- [X] T038 [P] [US5] Verify the normative demo baseline and DEMO-002 values in `tests/domain/demoData.test.ts`, including all ten exact records/notes/integer cents, selected month `2026-10`, total `173265`, category totals food `12275`, transport `5090`, housing `145000`, entertainment `2400`, other `8500`, adjacent-month exclusion, and initial IDs `demo-008` through `demo-001` in the specified newest-first order.
- [X] T039 [P] [US5] Cover DEMO-001/003/004 and store-level isolation in `tests/ui/demoMode.test.tsx`, asserting first-value activation, fictional labeling, all demo interactions, fresh baseline/preferences on activation, no cross-mode form/dialog/status leakage, and zero mocked storage reads/writes/listeners.
- [X] T040 [P] [US5] Add reference-Chromium DEMO-001–007 and demo MONEY-003 scenarios in `e2e/demo.spec.ts`, instrumenting storage methods and both `addEventListener('storage', ...)` and `onstorage` before application scripts, exercising URL/reload/history transitions and all interactions under every real-data precondition plus a normal tab, asserting all read/write/listener counters equal zero, and explicitly verifying every demo October transaction and monthly/category summary under both `en-US` and `de-DE` with identical fixed en-US USD output matching DEMO-002.

### Implementation for User Story 5

- [X] T041 [US5] Create the readonly fixed baseline and exact first-value activation parser in `src/demo/demoData.ts`, integrate a separate no-storage demo collection and all interactions in `src/state/useExpenseStore.ts`, and initialize fresh destination state and the persistent fictional label in `src/App.tsx` and `src/main.tsx`. Baseline: `demo-001` 145000 housing 2026-10-01 “October rent”; `demo-002` 4275 food 2026-10-03 “Groceries at Green Market”; `demo-003` 1850 transport 2026-10-05 “Metro card top-up”; `demo-004` 2400 entertainment 2026-10-08 “Cinema tickets”; `demo-005` 1280 food 2026-10-12 “Coffee and pastry”; `demo-006` 8500 other 2026-10-15 “Household supplies”; `demo-007` 6720 food 2026-10-18 “Dinner with friends”; `demo-008` 3240 transport 2026-10-21 “Airport train”; `demo-009` 2000 food 2026-09-30 “Previous month lunch”; `demo-010` 3000 entertainment 2026-11-02 “Future concert deposit”; selected month `2026-10`. Branch before real-storage loading, register no storage listeners or persistence effects, derive no real recovery/durability status, reset demo records/preferences/forms/dialogs/status on every fresh activation, and keep normal mode free of demo content.

**Checkpoint**: All DEMO cases and both-locale demo MONEY-003 checks pass in reference Chromium, with exact baseline repetition and explicit zero storage read, write, and listener counts.

---

## Phase 8: Polish & Cross-Cutting Verification

**Purpose**: Verify deterministic scale, performance, accessibility, responsive behavior, recovery, and complete requirement traceability. Browser checks use assertions and reviews only; no browser screenshot tasks are included because article evidence uses separate macOS VS Code window captures.

- [X] T042 Write failing deterministic SCALE fixture and MONEY-004 tests in `tests/fixtures/scaleData.test.ts` that require exactly 1,000 ID-ordered records, IDs `scale-0001`–`scale-1000`, amounts/categories/dates/notes from the quickstart formulas, an exact integer `amountCents` for every record, 100 records in each month January–October 2026, 200 records per category, and independently computed exact summaries.
- [X] T043 Implement the reusable SCALE generator in `tests/fixtures/scaleData.ts` using only integer arithmetic for `i = 1..1000`: `amountCents = ((i * 7919) % 100000) + 1`; zero-based category `(i - 1) % 5`; year 2026, month `((i - 1) % 10) + 1`, day `((i - 1) % 28) + 1`; note `Scale expense ` plus unpadded `i`; return records in ID order inside a valid version-1 envelope.
- [X] T044 [P] Add SCALE-001/002 reference-Chromium verification in `e2e/scale.spec.ts`, comparing all 1,000 reloaded records, every integer-cent amount, and every summary to independent expectations and timing three repetitions of add, same-month/cross-month edit, delete, month selection, every category filter, and both date/amount sort directions from committed activation to visible exact result within 2 seconds.
- [X] T045 [P] Add automated WCAG 2.2 AA and observable accessibility checks in `e2e/accessibility.spec.ts` and responsive assertions in `e2e/responsive.spec.ts` for every UI-contract core-flow state at fixed desktop and 320px mobile layouts, covering valid/invalid forms, associated errors, unsafe totals, deletion/replacement dialogs, deterministic edit/delete focus, write/recovery warnings, empty states, transaction results, labeled demo, 200% browser zoom, 200% text resize, unobscured visible focus, no two-dimensional scrolling/overlap or lost functionality, and measured minimum 24-by-24-CSS-pixel pointer targets, without producing screenshots.
- [X] T046 Use SCALE-002 measurements and automated accessibility/responsive results to remove demonstrated bottlenecks and resolve every known semantic, keyboard, focus, announcement, contrast, target-size, non-color-meaning, zoom, text-resize, reflow, overlap, and focus-obscuring issue in `src/domain/dashboard.ts`, `src/state/useExpenseStore.ts`, all files in `src/components/`, and `src/styles.css`, preserving exact results, module boundaries, identical content and operation across layouts, all prior behavioral tests, and zero known WCAG 2.2 AA violations.
- [ ] T047 Complete the quickstart keyboard-only and VoiceOver-with-Chromium review for every UI-contract core flow, including errors, warnings, both dialogs, same-month filtered and cross-month edits, every deletion focus fallback, and empty-state focus; perform the manual responsive review at desktop/mobile widths, 200% browser zoom, 200% text resize, and 320 CSS pixels with contrast and target measurements; and record case-ID results and corrections in `specs/001-expense-tracker/verification.md` without browser screenshots.
- [X] T048 Perform the manual PERSIST and RECOVERY review for readable/unreadable raw-data claims, no-write-before-confirmation, cancellation, failed replacement, retained work, warning lifecycle, and post-failure reload, recording case-ID outcomes in `specs/001-expense-tracker/verification.md`.
- [X] T049 Audit FR-001–FR-029 against the requirement-to-verification matrix in `specs/001-expense-tracker/quickstart.md`, recording each mapped case's precondition, input, actual outcome, reference Chromium version, and automated/manual evidence in `specs/001-expense-tracker/verification.md` with no unmapped requirement.
- [ ] T050 Run `npm run test:unit`, `npm run build`, and `npm run test:e2e` in that order after all reviews, resolve every defect/governance violation, rerun every affected check and manual review, then repeat the complete sequence and record the final zero-known-AA-violation and zero-unresolved-recovery-defect gate in `specs/001-expense-tracker/verification.md`.

---

## Dependencies & Execution Order

### Phase and story dependencies

- **Setup → early red checkpoint → Foundational**: T001–T009 block all application source and story work.
- **US1 (P1)**: Depends on Foundational only; delivers the MVP without persistence, editing, deletion, preferences, or demo.
- **US2 (P1)**: Depends on US1's add/dashboard/store boundaries; completes the persistence-critical P1 product.
- **US3 (P2)**: Depends on US1 and US2 because edit/delete reuse validation, recalculation, dialogs, and durable mutation handling.
- **US4 (P3)**: Functionally depends on US1 for preferences and on US3 for the integrated edit/filter and deletion/filter focus cases; sequential integration avoids conflicting store, dashboard, and transaction-list changes.
- **US5 (P3)**: Depends on US1–US4 for the complete demo interaction surface and on US2 for proof that demo bypasses the real persistence path.
- **Polish**: Depends on all desired stories; SCALE fixture work T042–T043 can begin once shared test fixtures are stable, but SCALE browser verification requires US1–US4.

### Within each story

1. Write all listed tests and run them against missing/incomplete behavior; confirm they fail for the intended reason.
2. Implement pure domain or storage boundaries before state coordination.
3. Implement state and presentational components before application integration.
4. Run the complete story checkpoint and relevant prior-story regression tests before advancing.

### Parallel execution examples

- **Setup/Foundation**: T002–T005 can run in parallel; T008 and T009 can run in parallel.
- **US1**: T010–T014 can be authored in parallel; after T015, T016/T017 can run in parallel; T019 can proceed once domain contracts exist, and T020 integrates last.
- **US2**: T021–T023 can be authored in parallel; T026 can proceed alongside store coordination after the storage contract T024 is defined.
- **US3**: T027–T029 can be authored in parallel; T030/T031 can run in parallel before T032 integration.
- **US4**: T033–T035 can be authored in parallel; T037 follows the pure list operations in T036.
- **US5**: T038–T040 can be authored in parallel before the demo implementation T041.
- **Polish**: T042 precedes T043; T044/T045 can run in parallel once T043 and the relevant story implementations are complete; T046 follows their measurements and findings.

---

## Requirement-to-Verification Traceability

This preserves, rather than replaces, the normative case definitions and matrix in `specs/001-expense-tracker/quickstart.md`.

| Requirement | Quickstart coverage | Primary verification tasks |
|---|---|---|
| FR-001 | CORE-001; DEMO-003 | T013, T014, T039, T040 |
| FR-002 | CORE-003 | T011, T013 |
| FR-003 | AMOUNT-001–008; A11Y | T010, T013, T027, T045, T047 |
| FR-004 | DATE-001–004 | T012, T013, T014 |
| FR-005 | CORE-004 | T011, T013, T027 |
| FR-006 | Every AMOUNT row in add and edit | T010, T013, T027 |
| FR-007 | CORE-005/006; AMOUNT edit rejection | T027, T029, T034, T035 |
| FR-008 | DELETE-001–003/005 | T028, T029, T034, T035 |
| FR-009 | DELETE-001; MONEY-003 | T028, T029, T045 |
| FR-010 | DELETE-002–004; PERSIST-010 | T028, T029 |
| FR-011 | CORE-002; DATE-001 | T012, T013, T014 |
| FR-012 | CORE-001/003; DEMO-002 | T012, T013, T038, T040 |
| FR-013 | CORE-005; DATE-001–004 | T012, T014, T027, T029 |
| FR-014 | AMOUNT-003/005/008; MONEY-001–004; OVERFLOW-001; SCALE fixture verification and SCALE-001 | T010, T012, T013, T014, T021, T028, T029, T038, T040, T042, T043, T044 |
| FR-015 | SCALE-002; DELETE-003/005 timing | T029, T035, T044 |
| FR-016 | FILTER-001/002 | T033, T034, T035 |
| FR-017 | FILTER-001/002; SORT-002 | T033, T034, T035 |
| FR-018 | SORT-001/002; DEMO-002 | T033, T034, T035, T038, T040 |
| FR-019 | FILTER-001; SORT-001/002 | T033, T034, T035 |
| FR-020 | PERSIST-002; SCALE-001 | T021, T023, T044 |
| FR-021 | PERSIST-001–007 | T021, T022, T023 |
| FR-022 | RECOVERY-001–007; A11Y dialogs | T022, T023, T045, T047, T048 |
| FR-023 | PERSIST-008–013; DELETE-004 | T021, T022, T023, T029 |
| FR-024 | EMPTY-001/002; FILTER-002 | T034, T035, T045, T047 |
| FR-025 | A11Y over every core flow; zero-known-violation gate | T013, T022, T027, T028, T034, T039, T040, T045, T046, T047, T048, T050 |
| FR-026 | CORE-005/006; DELETE-001–003/005; every RECOVERY dialog; A11Y | T022, T023, T027, T028, T029, T034, T035, T045, T047 |
| FR-027 | DEMO-001/004 | T039, T040 |
| FR-028 | DEMO-002/003 | T038, T039, T040 |
| FR-029 | DEMO-003/005/006/007 | T039, T040 |

---

## Implementation Strategy

### MVP first

1. Complete Setup, prove the early runnable red checkpoint, and complete Foundational test infrastructure.
2. Implement US1 test-first and stop at its independent checkpoint.
3. Validate exact add/month/category behavior and demo the in-memory MVP.
4. Complete US2 before treating the P1 product as trustworthy across reloads.

### Incremental delivery

1. Deliver US1, then US2, validating each without requiring later-story controls.
2. Add US3 safe correction/deletion, then US4 list preferences and integrated focus behavior, rerunning prior-story tests at each checkpoint.
3. Add US5 only after all normal interactions exist, using explicit instrumentation as the isolation gate.
4. Finish deterministic SCALE, Playwright accessibility/responsive checks, manual reviews, traceability, and the full completion sequence.

### Completion rules

- A story is complete only when its own tests and affected prior-story tests pass.
- Do not convert a red test to a weaker assertion to accommodate implementation.
- Completion requires every quickstart-mapped requirement to have recorded objective coverage, zero known WCAG 2.2 AA violations, and zero unresolved persistence-recovery defects.
- Article screenshots are separate VS Code window captures and are neither implementation tasks nor substitutes for verification.

---

## Phase 9: Convergence

- [X] T051 Preserve the last valid selected month and dashboard when the native Month control supplies an empty or invalid value; add behavioral regression coverage for the Chromium-reproduced application crash per FR-011 and US1/AC2 (partial)

---

## Phase 10: Convergence

- [ ] T052 Complete and record the VoiceOver-with-Chromium review for every UI-contract core flow, including control/dialog names, roles, states, instructions, field-error associations, and required announcements; keep T047 open until this and its other manual evidence are complete per FR-025, SC-007, and T047 (missing)
- [X] T053 Investigate and resolve the intermittent desktop Chromium failure in the CORE-006 visible same-month amount-resorting scenario in `e2e/transaction-list.spec.ts` without weakening its behavioral assertions; rerun affected and complete browser checks per FR-026 and T050 (partial)
- [ ] T054 After all remaining reviews and corrections, complete the original T050 ordered final sequence and record the zero-known-AA-violation and zero-unresolved-recovery-defect gate; do not mark T047 or T050 complete on automated evidence alone per SC-007 and T050 (partial)
- [X] T055 Record case-ID outcomes for the manual PERSIST-001–013 and RECOVERY-001–007 review in `specs/001-expense-tracker/verification.md`, including raw-data claims, no-write behavior, cancellation, failed replacement, retained work, warning lifecycle, and post-failure reload per T048 (partial)
- [X] T056 Expand the requirement-to-evidence audit in `specs/001-expense-tracker/verification.md` to record each mapped case's precondition, input, actual outcome, reference Chromium version, and automated/manual evidence per T049 (partial)
