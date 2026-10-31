# Bug Assessment: Clearing Month crashes and unmounts the expense tracker

- **Slug**: month-clear-crash
- **Created**: 2026-11-01
- **Source**: pasted text
- **Verdict**: valid
- **Severity**: high

## Report (verbatim or summarized)

> Clearing the native Month control crashes the expense tracker instead of preserving the previous valid month. This is a disclosed maintenance reversion of a genuine convergence defect. Reproduce with the existing regression test tests/ui/monthlyDashboard.test.tsx CORE-002 and, if practical, a real Chromium clear action. Expected: no exception or unmount; the last valid month and dashboard remain. Do not change source code.

The convergence record confirms this is a reversion: `specs/001-expense-tracker/tasks.md:278` marks T051 complete for preserving the last valid month, and `specs/001-expense-tracker/verification.md:15` records both the pre-fix crash and successful post-fix Chromium verification.

## Symptom

Clearing the native Month control commits an empty string as the selected month. Rendering then throws `Expected a valid local month`, and the entire application unmounts instead of retaining the previous valid month, summary, and transaction list.

## Reproduction

### Existing regression test

1. Run `npm run test:unit -- tests/ui/monthlyDashboard.test.tsx -t CORE-002`.
2. CORE-002 renders the app with October fixtures and fires a Month change whose value is `''` at `tests/ui/monthlyDashboard.test.tsx:46-57`.
3. Observed: one failed test and four skipped tests. The failure is `Error: Expected a valid local month`, thrown at `src/domain/dashboard.ts:56` through `src/state/useExpenseStore.ts:201`.
4. Expected: no exception; Month remains `2026-10`, Monthly total remains `$3.00`, and two transactions remain visible.

### Real Chromium clear action

1. Start the Vite app and open it in headless Chromium using Playwright.
2. Observe the initial native Month value (`2026-11` in this run) and Monthly total (`$0.00`).
3. Perform `page.getByLabel('Month', { exact: true }).fill('')` on the actual `input[type=month]` and capture browser page errors.
4. Observed: Chromium reports `Expected a valid local month`. After the clear, the Month control, Monthly total, Transactions list, and Personal Expense Tracker heading each have a locator count of zero, confirming application unmount.
5. Expected: no page error or unmount; the initial valid month and dashboard remain.

## Suspected Code Paths

- `src/components/Dashboard.tsx:111-117` — the controlled native Month input forwards every `event.target.value`, including the empty value produced by clearing it.
- `src/state/useExpenseStore.ts:103-105` — `selectMonth` blindly commits the supplied value without calling the already imported `isMonth` validator.
- `src/state/useExpenseStore.ts:200-203` — the summary memo recalculates immediately with the invalid selected month.
- `src/domain/dashboard.ts:51-57` — `summarizeMonth` enforces its valid-month invariant by throwing on the empty string.
- `src/domain/dates.ts:32-42` — `isMonth` is the existing runtime validator for `YYYY-MM` month values; `MonthString` is only a string alias and provides no runtime protection.
- `tests/ui/monthlyDashboard.test.tsx:46-58` — CORE-002 is the existing regression test and currently fails before its assertions because rendering throws.

## Root Cause Hypothesis

**Confidence: high.** The Month UI boundary treats the native control's transient empty value as a valid `MonthString`. `selectMonth` stores it unconditionally, after which `summarizeMonth` rejects it by throwing during React rendering. Both the unit stack trace and Chromium page error identify this exact path, and the subsequent empty locators confirm the resulting unmount. This matches the disclosed reversion of T051.

## Proposed Remediation

**Preferred**: Guard the state transition in `useExpenseStore` by accepting only values for which `isMonth(month)` is true and otherwise leaving `selectedMonth` unchanged. This preserves the last valid month, lets the controlled input retain that value, and keeps `summarizeMonth`'s domain invariant intact. The validator is already imported by this module, so the fix should be small and require no new dependency or persistence change.

**Alternatives**:
- Ignore empty or invalid values in `Dashboard`'s `onChange` handler. This fixes the known UI path but leaves the store setter unsafe for other current or future callers; it could be added as defense in depth rather than used as the sole safeguard.
- Replace invalid input with the current month or another fallback. This avoids the throw but violates the requirement to preserve the last user-selected valid month and can unexpectedly change the dashboard.

**Files likely to change**:
- `src/state/useExpenseStore.ts`
- `tests/ui/monthlyDashboard.test.tsx` only if the existing CORE-002 coverage needs clarification; its current assertions already express the required behavior.
- A suitable existing Playwright spec, such as `e2e/core.spec.ts`, for persistent browser-level regression coverage.

**Tests to add or update**:
- Keep CORE-002 and verify it passes unchanged after the fix, including the retained month, total, and transaction count.
- Add or retain a Chromium regression that clears the native Month control and asserts no page error, no unmount, the prior month and total, and the prior transaction list.
- Exercise another invalid month value through the store/UI boundary if practical, since T051 covers both empty and invalid values.

## Risks & Considerations

- The crash blocks the complete core workflow and removes all controls and dashboard content until reload, which warrants high severity despite the narrow trigger.
- No expense mutation or durable-storage write occurs in this path. However, any unsaved in-memory work present before a crash could be lost if the user reloads to recover.
- Ignoring invalid input must not swallow valid month changes or alter expense data, filters, sorting, persistence, or demo-mode behavior.
- A UI-only guard risks leaving the same crash reachable through other store callers; the state boundary should enforce the invariant.
- No API, schema, migration, security, or performance impact is expected from the preferred guard.

## Open Questions

- None. The failure and expected behavior are reproduced and specified by the existing regression and convergence records.

## Assessment Scope

No source or test files were changed during this assessment. The only written artifact is this report under `.specify/bugs/month-clear-crash/`.
