# Quickstart: Personal Expense Tracker

## Prerequisites

- Node.js 20 or newer and npm.
- Chromium installed for Playwright (`npx playwright install chromium`). The Playwright-pinned Chromium build is the reference and only acceptance browser; record its version with results. Firefox, WebKit/Safari, and all other browsers remain unverified.
- No backend, database, environment variables, or remote services.

## Install and run

From the repository root:

```sh
npm install
npm run dev
```

Open the local URL printed by Vite. The normal entry point starts in the current local month. Open `http://localhost:5173/?demo=1` for the fixed fictional baseline; use a separate browser context when checking isolation from real data.

## Standard verification commands

```sh
npm run test:unit
npm run build
npm run test:e2e
```

- `test:unit` runs Vitest domain, persistence, and React Testing Library interaction suites.
- `build` runs TypeScript checking and the production Vite build.
- `test:e2e` starts the configured local web server and runs the reference-Chromium scenarios. Desktop/mobile demo states are verified without producing article screenshots.
- Run the manual A11Y and recovery reviews below in addition to the commands. After any correction, rerun every affected automated check and manual review; rerun the complete sequence before completion.

See [data-model.md](data-model.md) for normative stored, derived, and demo values and [contracts/ui-contract.md](contracts/ui-contract.md) for observable behavior.

## Verification conventions

- Case IDs below are reusable acceptance sets, not claims that implementation tests already pass. Each automated case records its ID, precondition, input, and actual outcome. “All cases” means every row in the named set in both add and edit where stated.
- Use fresh browser contexts unless a case explicitly requires reload, history, or another tab. Seed storage before application initialization. For readable malformed values, retain and compare the exact raw string; for unreadable values, inject a read exception and assert behavior/no writes without claiming to inspect the raw value.
- Reference-Chromium timing starts at the user's committed control activation and ends when the updated total/list is visible. At the required scale, every result must appear within 2 seconds.
- Test locale independence by repeating MONEY-003 with a non-English browser locale such as `de-DE`; expected USD output does not change.

## Reproducible verification case sets

### AMOUNT — syntax, boundaries, and accessible rejection

Precondition: run every row in add and against an existing `$10.00` expense in edit. Surrounding quotes below delimit input and are not entered. On rejection, expect no new/changed record, unchanged summaries, focus on the amount field, and an associated announced text/icon error with no color-only meaning.

| ID | Input | Expected |
|---|---|---|
| AMOUNT-001 | `"1"`, `"1.2"`, `"1.23"` | Accept as 100, 120, and 123 cents respectively. |
| AMOUNT-002 | `"  001.2  "`, `"000.50"`, `".50"` | Trim and accept as 120, 50, and 50 cents. |
| AMOUNT-003 | `"0.01"`, `"999999999.99"` | Accept as 1 and 99999999999 cents; the latter renders `$999,999,999.99`. |
| AMOUNT-004 | `""`, `"   "`, `"0"`, `"0.00"`, `"000"`, `"-1"` | Reject blank/zero/negative values. |
| AMOUNT-005 | `"."`, `"1."`, `"1.234"` | Reject missing digits, trailing decimal point, and excess precision; never round. |
| AMOUNT-006 | `"1,000"`, `"$1"`, `"+1"`, `"1e2"` | Reject grouping, currency symbols, explicit plus signs, and exponent notation. |
| AMOUNT-007 | `"abc"`, `"NaN"`, `"Infinity"` | Reject non-numeric/non-finite input. |
| AMOUNT-008 | `"1000000000.00"`, `"1000000000"` | Reject values above 999999999.99 USD. |

### CORE and DATE — monthly accounting, editing, and notes

| ID | Precondition and action | Expected |
|---|---|---|
| CORE-001 | Empty normal collection; add food 25.50 on 2026-10-15. | One record; October monthly/food totals `$25.50`; other categories `$0.00`. |
| CORE-002 | Fix local current date to 2026-10-31 and open normal mode. | Selected month is 2026-10. |
| CORE-003 | Add one valid expense in each of food, transport, housing, entertainment, and other; attempt an invalid category in draft/persisted validation. | Each valid category works; invalid category is rejected without mutation or makes a persisted collection invalid. |
| CORE-004 | Add/edit with blank, whitespace-only, and nonblank notes. | Blank/whitespace notes are absent; nonblank note is preserved exactly. |
| CORE-005 | Edit amount, category, date, and note; separately move a record from September into October and out of October. | Same record ID, exact recalculation in both months, and selected month unchanged; a visible same-month edit requester regains focus, while cross-month completion announces the move and focuses the month control. |
| CORE-006 | With a category filter active, edit a matching expense into another category without changing its month. | The edited record leaves the visible results, the result is announced, summaries still use the unfiltered month, and focus moves to the category filter. |
| DATE-001 | Seed records on 2026-09-30, 2026-10-01, 2026-10-31, and 2026-11-01; select October. | Only October 1/31 records and amounts contribute to October. |
| DATE-002 | Submit 2024-02-29 and 2023-02-29; select February in each year. | Leap-day 2024 value is valid and included; impossible 2023 date is rejected with associated error. |
| DATE-003 | Add a future record in 2027-01 while viewing 2026-10. | No October effect; record and totals appear only in 2027-01. |
| DATE-004 | Repeat boundary cases in a non-UTC local timezone. | Dates and month membership remain the entered local calendar values; no UTC shift. |

### MONEY and OVERFLOW — exact arithmetic and display

| ID | Input | Expected |
|---|---|---|
| MONEY-001 | Empty month and categories. | Every applicable rendered zero is `$0.00`. |
| MONEY-002 | Amount 1234.56, plus fractional-cent-boundary values such as 0.01, 0.10, and 0.99. | 123456 cents renders `$1,234.56`; integer sums are exact with no drift. |
| MONEY-003 | Under each of the `en-US` and `de-DE` browser locales, render normal transactions, monthly/category totals, and deletion confirmation, plus every demo October transaction and the demo monthly/category summaries. | Both locales produce identical fixed en-US USD output with explicit `$`, grouping, and two decimals in every location; demo transaction and summary values exactly match DEMO-002. |
| MONEY-004 | Round-trip every accepted input in AMOUNT-001–003 through normal persistence, inspect the stored JSON and reloaded value, and inspect every generated SCALE record. | Each accepted input persists and reloads as its exact expected integer-cent JSON number, never a dollar float; every SCALE `amountCents` is an exact integer, and no excess precision is silently rounded. |
| OVERFLOW-001 | Pure-domain summary with 90,072 unique same-month, same-category records at the individual maximum 99999999999 cents. | Monthly and affected category aggregates report visible/announced error results in UI coverage; no rounded, clamped, wrapped, or apparently valid total, and records are unchanged. |

### FILTER, SORT, and EMPTY — list behavior and focus

| ID | Precondition and action | Expected |
|---|---|---|
| FILTER-001 | Use a month containing all five categories; select each and then all. | Exact category membership; monthly/category summaries and durable raw collection remain unchanged. |
| FILTER-002 | Select a category absent from a nonempty month, then activate clear filter. | Distinct no-match message, unchanged summaries, restored list/result announcement, and focus on category filter. |
| SORT-001 | Seed `tie-a` and `tie-b` at 200 cents and `tie-c` at 100 cents, all on 2026-10-01; add older/newer records. | Date ascending/descending follows local dates; every same-date group is ID ascending. |
| SORT-002 | Sort the same fixture by amount in both directions. | Descending begins `tie-a`, `tie-b`; ascending ends `tie-a`, `tie-b`; all amount ties remain ID ascending and summaries/raw data do not change. |
| EMPTY-001 | Select a month with no records and activate add expense. | Distinct non-error empty-month message; add task opens with amount input focused. |
| EMPTY-002 | Compare EMPTY-001 and FILTER-002. | Messages/actions are distinct and neither is presented as an error. |

### DELETE — confirmation and failed durability

Precondition: one identified expense with known formatted amount/category/date.

| ID | Action | Expected |
|---|---|---|
| DELETE-001 | Open dialog by keyboard; inspect it and press Tab/Shift+Tab. | Correct expense/consequence text, accessible name/description, Cancel initial focus, and contained visible focus. |
| DELETE-002 | Cancel and separately press Escape. | No mutation/write, and focus returns to the delete requester. |
| DELETE-003 | Confirm with durable success in cases with a following visible result, only a preceding visible result, and no remaining unfiltered result. | Only target removed within 2 seconds and summaries recalculated; focus moves respectively to the next visible transaction edit requester, previous visible edit requester, or Add expense; no undo is offered. |
| DELETE-004 | Inject write failure, confirm, then reload. | Removal and warning remain only in memory before reload; last durable collection and target record return afterward. |
| DELETE-005 | With a category filter active and other month records hidden, delete the last visible filtered result. | The visible result and summaries update within 2 seconds, the no-matches result is announced, and focus moves to Clear filter rather than Add expense. |

### PERSIST — load classifications and ordinary write failures

| ID | Precondition and action | Expected |
|---|---|---|
| PERSIST-001 | Missing key; open tracker. | Normal ready/empty state without recovery warning. |
| PERSIST-002 | Valid envelope; reload. | Exact complete collection restored without duplication/alteration. |
| PERSIST-003 | Readable malformed JSON; open and cancel recovery. | Empty guarded memory, announced warning, no salvage, no write, and exact raw string unchanged. |
| PERSIST-004 | Readable envelope with unsupported version or invalid envelope shape. | Same all-or-nothing recovery outcome as PERSIST-003. |
| PERSIST-005 | Envelope with one invalid record among otherwise valid records. | Entire collection rejected; no valid-looking record is loaded. |
| PERSIST-006 | Envelope with duplicate IDs. | Entire collection rejected with recovery warning. |
| PERSIST-007 | Storage read throws; open tracker and cancel replacement. | Empty guarded memory and warning; no raw-inspection claim and zero writes before/after cancellation. |
| PERSIST-008 | Inject quota failure on add, then reload. | Added record remains visible with announced unsaved warning until reload; reload omits it and restores last durable collection. |
| PERSIST-009 | Inject write failure on edit, then reload. | Edited work remains only in memory; reload restores original field values. |
| PERSIST-010 | Inject write failure on delete, then reload. | Deleted record is absent only in memory; reload restores it. |
| PERSIST-011 | Inject serialization failure on a normal mutation. | Visible write failure, retained in-memory work, no durability claim, and no destructive fallback. |
| PERSIST-012 | Make storage unavailable mid-session and attempt a mutation. | Same visible write-failure and retention behavior as quota/serialization failures. |
| PERSIST-013 | After one or more failures, make a later mutation succeed; inspect saved value and warning, then reload. | Complete current collection with all retained work is saved, warning clears only after success, and reload retains that collection. |

### RECOVERY — replacement lifecycle

Run each dialog with the same accessible-name, Cancel-focus, containment, Escape/Cancel, and restoration assertions as DELETE. Readable cases compare exact raw bytes before every confirmed write; unreadable cases instead assert no pre-confirmation write and make no raw-value claim.

| ID | Action | Expected |
|---|---|---|
| RECOVERY-001 | In readable malformed state, choose start fresh, then Cancel/Escape. | No write; raw value and empty memory unchanged; recovery warning remains. |
| RECOVERY-002 | Confirm start fresh successfully. | Written envelope is version 1 with an empty expenses array; ready/empty state and recovery-warning clearance. |
| RECOVERY-003 | Inject failure on confirmed start-fresh write. | Empty guarded memory, recovery/write warning, no success claim or automatic retry. |
| RECOVERY-004 | In guarded state, add valid work, attempt first save, then Cancel/Escape. | No write; new work remains visible in memory; raw value and recovery warning remain. |
| RECOVERY-005 | Confirm the first replacement save successfully. | Complete current in-memory collection replaces the old value; ready state and warning clearance survive reload. |
| RECOVERY-006 | Inject serialization/quota/access failure on first replacement. | Current work and recovery-required/write-failure status remain visible without success claim or retry. |
| RECOVERY-007 | Repeat cancellation, failed replacement, and successful replacement from unreadable state. | Same memory/status outcomes and zero writes before explicit confirmation; no assertion or message implies raw inspection. |

### DEMO — activation, fixed baseline, transitions, and isolation

| ID | Precondition and action | Expected |
|---|---|---|
| DEMO-001 | Open `?demo=1`, `?source=x&demo=1`, `?demo=1&demo=0`, and separately `?demo=0&demo=1`, `?demo=01`, `?demo=true`, `?Demo=1`, and no parameter. | Only the first three activate demo; unrelated parameters are allowed and only the first exact case-sensitive `demo` value controls mode. |
| DEMO-002 | Fresh activate demo and compare to [the normative baseline](data-model.md#demo-dataset). | Selected 2026-10; all exact records; total `$1,732.65`; food `$122.75`, transport `$50.90`, housing `$1,450.00`, entertainment `$24.00`, other `$85.00`; IDs 008,007,006,005,004,003,002,001 in newest-first order. |
| DEMO-003 | Add, edit, delete, select adjacent months, filter, and sort; fresh reload/activation. | All interactions work in demo memory, including add with normal validation; fresh activation restores exact baseline/month/default preferences and shows fictional label. |
| DEMO-004 | Modify normal and demo records/view state; switch modes through URL navigation, reload, and back/forward history. | Fresh destination state every time; no records, month, filter, sort, form, dialog, or status leaks across modes. |
| DEMO-005 | For each populated, missing, readable malformed, and read-throwing real-storage precondition, instrument storage before app initialization; perform initialization and all DEMO-003 interactions. | Zero storage reads, zero writes/clears/removals, and zero storage-event listener registrations; no real recovery warning or persistence-success claim. |
| DEMO-006 | Repeat DEMO-005 with a normal tab open; inspect listener registration via both `addEventListener('storage', ...)` and `onstorage`. | Demo neither reacts to nor causes real-storage events; all three isolation counters remain zero. |
| DEMO-007 | Return to normal mode with known real data. | No demo records/content appear; previously readable known real value remains byte-for-byte unchanged. |

For DEMO-005/006, instrument the storage methods used for reads and all write/clear/remove paths and instrument window storage-listener registration before any application script runs. An unchanged raw value alone is insufficient evidence: the read, write, and listener counts must each explicitly equal zero.

### A11Y — manual and automated accessibility review

- **Automated**: In reference Chromium, run WCAG 2.2 AA accessibility checks and observable assertions for every core-flow state: initial dashboard, valid/invalid add/edit, associated field errors, monthly/unsafe-total feedback, deletion and both replacement dialogs, ordinary/replacement write warnings, empty month/no matches, transaction results, and labeled demo. Cover fixed desktop and 320px mobile layouts.
- **Keyboard manual**: Complete every flow in the UI contract core-flow inventory without a pointer. Verify logical order, visible/unobscured focus, no trap, first-invalid-field focus, dialog Cancel initial focus/containment/Escape/restoration, same-month edit focus both when the requester survives and when CORE-006 leaves the active filter, every DELETE-003/005 post-deletion fallback, cross-month-edit focus, and empty-state action focus.
- **Assistive technology manual**: Use VoiceOver with reference Chromium to verify control/dialog names, roles, states, instructions, field-error associations, and announcement of validation, status, recovery, calculation, empty-state, and demo messages. Confirm text/icon meaning remains when color is removed or not perceived.
- **Visual/responsive manual**: At 200% browser zoom and 200% text resize, verify no loss of content/function. At 320 CSS pixels, verify reflow without two-dimensional scrolling or overlap. Check text/non-text contrast and measure every pointer target as at least 24 by 24 CSS pixels at desktop and mobile widths.
- **Acceptance**: Record automated results and manual review evidence by core flow and case ID. Automated scanning alone is insufficient. Completion requires zero known WCAG 2.2 AA violations; no severity-based exception permits a known AA violation to remain.

### SCALE — deterministic 1,000-record dataset and timing

Generate exactly 1,000 valid expenses for integer `i = 1..1000` using only integer arithmetic:

- `id`: `scale-` followed by `i` zero-padded to four digits (`scale-0001` through `scale-1000`).
- `amountCents`: `((i * 7919) % 100000) + 1`, yielding 1 through 100000 cents.
- `category`: cycle `[food, transport, housing, entertainment, other]` using zero-based `(i - 1) % 5`.
- `date`: year 2026; month `((i - 1) % 10) + 1` (January through October); day `((i - 1) % 28) + 1`.
- `note`: `Scale expense ` followed by the unpadded integer `i`.

This yields 100 records in each month January–October 2026 and 200 records per category overall. Store the records in ID order in a valid version-1 envelope. Compute expected summaries independently with exact integer-cent arithmetic; do not use displayed rounded values as expectations.

- **SCALE-001**: Reload the seeded collection in reference Chromium and compare all 1,000 records and every monthly/category summary with the independent expectations.
- **SCALE-002**: From a fresh loaded SCALE state, perform add, same-month edit, cross-month edit, delete, month selection, every category filter, and date/amount sorts in both directions. Repeat each timing three times; every updated result must be visible within 2 seconds and exact.

## Requirement-to-verification traceability

| Requirement | Objective acceptance coverage |
|---|---|
| FR-001 | CORE-001; DEMO-003 |
| FR-002 | CORE-003 |
| FR-003 | AMOUNT-001–008; A11Y keyboard/announcements |
| FR-004 | DATE-001–004 |
| FR-005 | CORE-004 |
| FR-006 | Every AMOUNT row in both add and edit |
| FR-007 | CORE-005/006; AMOUNT rejection precondition |
| FR-008 | DELETE-001–003/005 |
| FR-009 | DELETE-001; MONEY-003 |
| FR-010 | DELETE-002–004; PERSIST-010 |
| FR-011 | CORE-002; DATE-001 |
| FR-012 | CORE-001/003; DEMO-002 |
| FR-013 | CORE-005; DATE-001–004 |
| FR-014 | AMOUNT-003/005/008; MONEY-001–004; OVERFLOW-001; SCALE fixture verification and SCALE-001 |
| FR-015 | SCALE-002; DELETE-003/005 timing |
| FR-016 | FILTER-001/002 |
| FR-017 | FILTER-001/002; SORT-002 |
| FR-018 | SORT-001/002; DEMO-002 |
| FR-019 | FILTER-001; SORT-001/002 |
| FR-020 | PERSIST-002; SCALE-001 |
| FR-021 | PERSIST-001–007 |
| FR-022 | RECOVERY-001–007; A11Y dialog review |
| FR-023 | PERSIST-008–013; DELETE-004 |
| FR-024 | EMPTY-001/002; FILTER-002 |
| FR-025 | A11Y all methods over every UI-contract core flow; SC-007 zero-known-violation gate |
| FR-026 | CORE-005/006; DELETE-001–003/005; every RECOVERY dialog; A11Y keyboard review |
| FR-027 | DEMO-001/004 |
| FR-028 | DEMO-002/003 |
| FR-029 | DEMO-003/005/006/007 |

## Completion gate

The feature is complete only when:

1. All required unit, build, and reference-Chromium checks pass, every mapped requirement has recorded objective coverage, and all manual A11Y and persistence-recovery reviews pass.
2. Zero known WCAG 2.2 AA violations and zero unresolved persistence-recovery defects remain; “non-critical” severity is not an exception to either requirement.
3. No known failing required check or unresolved critical review finding remains. Corrections trigger relevant reruns and a final full verification run.
4. Any other exception is explicitly accepted by the user and recorded with scope, rationale, affected cases, and rerun evidence. An accepted exception cannot waive the zero-known-AA-violation or required recovery behavior above.

Article screenshots are captured separately as macOS window-only images of VS Code and are not a substitute for any verification case.
