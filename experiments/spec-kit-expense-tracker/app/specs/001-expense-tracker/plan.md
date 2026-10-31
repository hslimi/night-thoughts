# Implementation Plan: Personal Expense Tracker

**Branch**: `001-expense-tracker` | **Date**: 2026-10-31 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-expense-tracker/spec.md`

**Note**: This template is filled in by the `/skill:speckit-plan` command; its definition describes the execution workflow.

## Summary

Build a polished, responsive, frontend-only personal expense tracker with React, TypeScript, and Vite. Users can add, edit, delete after accessible confirmation, and review exact USD monthly/category totals; filter and sort transactions without changing summaries; and retain real expenses in localStorage. Pure typed domain modules own validation and exact integer-cent calculations, a separate storage adapter owns all durable access, and React components own presentation and interaction. Guarded recovery performs no write before confirmation for readable malformed or unreadable storage. Exact first-value `demo=1` activation supplies the fixed fictional baseline and 2026-10 without storage reads, writes, or listeners. Vitest/React Testing Library and Playwright Chromium verify the reproducible quickstart case sets, focus and WCAG behavior, persistence failures, demo isolation, and responsive layouts. Article evidence uses separate macOS window-only captures of VS Code.

## Technical Context

**Language/Version**: TypeScript 5.x; Node.js 20+ for development and test tooling.

**Primary Dependencies**: React and ReactDOM runtime; Vite with the official React plugin; native CSS, browser `<dialog>`, fixed-locale `Intl.NumberFormat`, and localStorage. No router, state library, UI framework, CSS framework, backend, or remote service.

**Storage**: One versioned, strictly validated, all-or-nothing JSON envelope in browser localStorage; fixed separate in-memory collection in demo mode.

**Testing**: Vitest, jsdom, React Testing Library, Testing Library user events/assertions, and Playwright with reference Chromium; manual keyboard and VoiceOver-with-Chromium review plus automated WCAG 2.2 AA checks.

**Target Platform**: Playwright Chromium is the sole real-browser acceptance target, including desktop and mobile-sized viewports. Other browsers remain unverified and are not claimed as supported by acceptance.

**Project Type**: Single-page frontend web application.

**Performance Goals**: With the deterministic 1,000-record quickstart dataset, every add/edit/delete, month selection, filter, and sort result is visible within 2 seconds in reference Chromium; reload preserves every record and exact summary. No runtime network requests.

**Constraints**: Amounts are positive integer cents up to `99999999999`; unsafe aggregates produce visible errors rather than rounding. Dates remain local `YYYY-MM-DD` strings with no UTC conversion. USD formatting is fixed en-US independent of locale. All destructive/replacement actions require confirmation; recovery performs no pre-confirmation write. Demo mode never accesses or listens to real storage. Completion requires zero known WCAG 2.2 AA violations, 200% zoom, 320px reflow, and 24-by-24-CSS-pixel minimum targets. Minimal dependencies; no backend.

**Scale/Scope**: One user, one browser profile, five categories, monthly dashboard, add/edit/delete, list filter/sort, local persistence and recovery, and isolated deterministic demo. Concurrent normal-tab synchronization/conflict resolution is excluded. No accounts, cross-device synchronization, import/export, budgets, recurring expenses, undo, or multi-currency support.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-design gate

- **I. Exact Money Representation — PASS**: The design parses directly to bounded integer cents, persists integer cents, checks aggregate safe-integer bounds, and formats only for display without silent rounding.
- **II. Accessible by Design — PASS**: All enumerated flows require keyboard operation, associated announced feedback, safe dialog focus, 200% zoom, 320px reflow, 24px targets, and zero known WCAG 2.2 AA violations.
- **III. Meaningful Behavioral Testing — PASS**: Planned domain, persistence, UI, and Chromium tests cover defined outcomes, boundaries, keyboard flows, failure cases, and reproducible data sets.
- **IV. Separated, Typed Modules — PASS**: Domain, persistence, state coordination, demo data, and React rendering have separate typed module boundaries.
- **V. Explicit Destructive Confirmation — PASS**: Deletion and both replacement paths require informed confirmation with safe cancellation and no pre-confirmation mutation or write.
- **VI. Transparent, Non-Destructive Persistence Recovery — PASS**: Missing, readable malformed, unreadable, and failed-write states are distinct and visible; unreadable raw values are never claimed inspectable, and all guarded states prohibit writes before confirmation.
- **Additional constraints — PASS**: The application remains frontend-only with localStorage as its sole durable boundary.

No violations require justification. Research in [research.md](research.md) resolved all technical decisions; no clarification markers remain.

### Post-design gate

- **I — PASS**: [data-model.md](data-model.md) defines the exact accepted syntax, maximum, positive safe-integer `amountCents`, checked integer summaries, and locale-independent USD presentation.
- **II — PASS**: [contracts/ui-contract.md](contracts/ui-contract.md) enumerates all core flows and specifies validation focus, associated announcements, equivalent deletion/replacement dialogs, zoom/reflow/targets, and zero known AA violations.
- **III — PASS**: [quickstart.md](quickstart.md) defines reusable case sets, deterministic scale data, requirement traceability, accessibility methods, and real Chromium failure-path and demo-isolation evidence.
- **IV — PASS**: The concrete source tree and contracts isolate pure domain logic, storage, React state coordination, and UI; summaries and preferences are derived/ephemeral rather than duplicated durable state.
- **V — PASS**: The UI and persistence contracts prevent deletion or replacement until explicit informed confirmation; cancellation leaves data unchanged and performs no write.
- **VI — PASS**: The persistence model distinguishes empty, ready, readable malformed, unreadable, unsaved-change, failed-replacement, and demo states with explicit reload and warning lifecycle outcomes.
- **Quality gates — PASS**: End-to-end validation, build/tests, responsive and accessibility reviews, recovery review, required reruns, and zero known AA violations are completion requirements. Any otherwise accepted exception must be explicit and recorded. No complexity exception is needed.

## Design Details

### Domain and derived state

- Define `Expense`, `Category`, draft, local date/month, summary, and view-preference types from [data-model.md](data-model.md).
- Trim amount input, apply the exact decimal grammar, reject prohibited syntax/excess precision/values above the maximum, and parse dollars/fractional digits directly into cents without floating-point input conversion. Reuse the validator for add/edit and persisted-record validation.
- Validate real local calendar dates with leap-year/month-length rules. Derive month membership from validated strings and use local getters only for the initial current month.
- Calculate monthly and all five category totals with safe-integer checks on every addition. Return an aggregate-error result for overflow and render announced feedback rather than an approximate total.
- Derive the visible list separately by filter and exact-cent/date comparator; use ID ascending as the deterministic tie-breaker in both directions and never mutate source order.
- Format every rendered monetary value with fixed `en-US` USD options independent of browser locale.

### State and persistence

- A single React store hook owns expenses, selected preferences, form/dialog targets, and user-facing persistence status. Components receive typed values/callbacks and do not access localStorage.
- The storage adapter accepts a browser-storage-like dependency for isolated tests and returns discriminated success/error results rather than throwing into UI code. It owns the key, JSON serialization, strict all-or-nothing schema validation, and all reads/writes.
- Normal mutations expose the next complete in-memory collection within the performance limit, then save that collection. Quota, serialization, and mid-session access failures produce an unsaved-changes warning; reload restores the last durable collection. A later successful save persists all current work and clears the warning only after success.
- Missing data is ready/empty. Readable malformed data and read exceptions enter recovery-required state with empty memory; only the former permits byte-for-byte raw-value assertions. Both perform no write before confirmation.
- Start fresh proposes an empty envelope; the first guarded save proposes the complete current collection. Cancellation retains memory and warning without writing. Failed replacement retains guarded memory and announces failure; confirmed success enters ready state and clears recovery status.
- Concurrent normal-tab synchronization is not implemented or required. Demo initialization branches before real-storage loading and never registers storage listeners. The same mutation/calculation paths operate only on demo memory, including add, with every persistence effect disabled.
- Mode is selected from the first case-sensitive `demo` query value at fresh document initialization. Navigation/reload/history transitions create fresh destination state rather than transferring collection or preferences.

### UI and accessibility

- Use one reusable expense form for add/edit with labeled controls, programmatically associated errors, first-invalid-field focus, announced feedback, and preserved nonblank notes. Keep the selected month unchanged after add/edit; after a cross-month edit, announce the move and focus the selected-month control. After a same-month edit, restore focus to the edit requester if it remains visible; if an active category filter hides it, announce the result and focus the category filter.
- Build the dashboard from summary, category-total, preference-control, transaction-list, empty-state, and status components. Empty-month add focuses the amount input; no-match clear restores results and focuses the filter control.
- Implement deletion and both replacement paths with the same native-dialog component and rules: `showModal()`, accessible name/description, Cancel autofocus, Escape/cancel without mutation, and native focus containment. Cancellation restores focus to the requester. After deletion, focus the next visible transaction edit requester, else the previous visible requester, else Clear filter when a filter is active, else Add expense.
- Handcrafted responsive CSS provides visible focus, AA contrast, non-color status meaning, 200% zoom/text resizing, 320px reflow, minimum 24-by-24-CSS-pixel targets, and reduced-motion support without hiding functionality.

### Verification

- Use the quickstart AMOUNT, DATE, MONEY, OVERFLOW, CORE, FILTER, SORT, EMPTY, DELETE, PERSIST, RECOVERY, DEMO, A11Y, and SCALE case sets as the acceptance baseline; each requirement has a traceable row in the quickstart matrix.
- Vitest covers exact syntax/boundaries, integer persistence and arithmetic, aggregate overflow, local month/leap/future boundaries, cross-month edits, filters, both sort fields/directions, deterministic ties, and note normalization.
- Persistence tests cover every load classification, all-or-nothing invalid collections, read/write exceptions, quota and serialization failures, no-write-before-confirmation, cancellation, both replacement paths, failed replacement, later full-collection success, warning clearance, and post-failure reload outcomes.
- React Testing Library tests observable add/edit validation and focus, announcements, recalculation, empty-state focus, deletion/replacement dialog behavior, and demo labeling and interaction behavior.
- Playwright reference Chromium exercises native-dialog Tab containment/restoration, actual reload persistence, injected ordinary and replacement failures, readable raw-value preservation, unreadable no-write behavior, exact demo activation/reset/transitions, and timezone-sensitive local months.
- Instrument storage before demo application initialization to count reads, writes/clears/removals, and both forms of storage-listener registration. Assert all three counts remain zero through initialization and add/edit/delete/month/filter/sort interactions with populated, missing, malformed, and unreadable real-data preconditions, including a concurrently open normal tab.
- Accessibility verification combines automated WCAG 2.2 AA checks with manual keyboard-only and VoiceOver-with-Chromium review of every core flow, including errors, warnings, both dialogs, empty states, 200% zoom, 320px reflow, and measured 24px targets. Completion permits zero known AA violations.
- Playwright checks deterministic populated demo layouts at fixed desktop/mobile viewports and times updates using the deterministic SCALE dataset. The completion sequence is `npm run test:unit`, `npm run build`, and `npm run test:e2e`, followed by responsive, accessibility, and recovery review and rerun of every affected check. Article screenshots are captured separately from real VS Code windows.

## Project Structure

### Documentation (this feature)

```text
specs/001-expense-tracker/
├── plan.md              # This file (/skill:speckit-plan command output)
├── research.md          # Phase 0 output (/skill:speckit-plan command)
├── data-model.md        # Phase 1 output (/skill:speckit-plan command)
├── quickstart.md        # Phase 1 output (/skill:speckit-plan command)
├── contracts/
│   └── ui-contract.md   # Browser entry points and observable UI behavior
└── tasks.md             # Phase 2 output (/skill:speckit-tasks command - NOT created here)
```

### Source Code (repository root)

```text
index.html
package.json
tsconfig.json
vite.config.ts
vitest.config.ts
playwright.config.ts
src/
├── main.tsx
├── App.tsx
├── styles.css
├── domain/
│   ├── expense.ts           # Types, categories, draft and record validation
│   ├── money.ts             # Exact cents parsing and USD formatting
│   ├── dates.ts             # Local date/month validation and derivation
│   └── dashboard.ts         # Totals, filtering, deterministic sorting
├── persistence/
│   └── expenseStorage.ts    # Sole real localStorage boundary and schema results
├── state/
│   └── useExpenseStore.ts   # React state/persistence/recovery coordination
├── demo/
│   └── demoData.ts          # Fixed fictional records and selected month
├── components/
│   ├── ExpenseForm.tsx
│   ├── Dashboard.tsx
│   ├── TransactionList.tsx
│   ├── ConfirmDialog.tsx
│   └── StatusMessage.tsx
└── test/
    └── setup.ts             # Vitest/jsdom test setup only
tests/
├── domain/                  # Pure business-rule Vitest suites
├── persistence/             # Storage schema and failure Vitest suites
├── ui/                      # React Testing Library interaction suites
└── fixtures/
    ├── expenses.ts          # Independent records, envelopes, clocks, and summaries
    ├── verification.ts      # Quickstart case-ID evidence helpers
    ├── scaleData.ts         # Deterministic 1,000-record SCALE generator
    └── scaleData.test.ts    # SCALE formula and fixture verification
e2e/
├── core.spec.ts
├── persistence.spec.ts
├── edit-delete.spec.ts
├── transaction-list.spec.ts
├── demo.spec.ts
├── scale.spec.ts
├── accessibility.spec.ts
└── responsive.spec.ts
```

**Structure Decision**: Use one Vite application at the repository root. Domain code has no React or browser-storage imports; only `persistence/expenseStorage.ts` accesses real localStorage. React state coordinates those boundaries, while components render observable behavior. Unit/component tests are separated from Playwright browser tests so each runner has a clear environment.

## Complexity Tracking

None. The design passes all constitution gates without exceptions.
