# Bug Fix: Clearing Month preserves the last valid dashboard

- **Slug**: month-clear-crash
- **Fixed**: 2026-11-01
- **Assessment**: ./assessment.md
- **Status**: applied

## Summary

Guarded the selected-month state transition with the existing `isMonth` validator so empty or otherwise invalid values cannot replace the last valid month. Added persistent Chromium coverage for clearing the native Month control without an exception, unmount, or change to the selected month, total, or transaction list.

## Changes

| File | Change | Notes |
|------|--------|-------|
| `src/state/useExpenseStore.ts` | modified | `selectMonth` now updates state only when `isMonth(month)` is true; invalid values leave the previous selection unchanged. |
| `e2e/core.spec.ts` | added regression test | Clears the real native Month input after selecting November and checks the retained November value, `$8.88` total, November transaction, application heading, and absence of page errors. |
| `tests/ui/monthlyDashboard.test.tsx` | unchanged | Existing CORE-002 assertions for the retained month, `$3.00` total, and two transactions were preserved exactly. |

## Tests Added or Updated

- `e2e/core.spec.ts` — `CORE-002: clearing native Month preserves the last valid dashboard` exercises a real Chromium `fill('')` action in both desktop and mobile projects.
- `tests/ui/monthlyDashboard.test.tsx` — existing `CORE-002: preserves the last valid month when the native control is cleared` retained unchanged and now passes.

## Local Verification

- Pre-fix reproduction: `npm run test:unit -- tests/ui/monthlyDashboard.test.tsx -t CORE-002` → failed with `Expected a valid local month`, matching the assessment.
- `npm run test:unit -- tests/ui/monthlyDashboard.test.tsx -t CORE-002` → passed: 1 test, 4 skipped.
- `npm run test:e2e -- e2e/core.spec.ts -g "clearing native Month"` → passed: 2 tests across desktop and mobile Chromium.
- `npm run build` → passed: TypeScript checking and Vite production build.
- `npm run test:unit` → passed: 18 files, 260 tests.
- `npm run test:e2e` → passed: 167 tests; 1 existing skip (mobile 200% browser zoom).
- Manual checks: none; browser behavior was verified by the automated real-Chromium regression above.

## Deviations from Assessment

None. The preferred store-boundary guard was applied without changing the existing CORE-002 unit assertions, domain invariant, persistence, or dependencies. A separate non-empty invalid-value test was not added because the native Month control's practical regression action is clearing; the store guard itself uses `isMonth` for all invalid values.

## Follow-ups

- Run `/skill:speckit-bug-test slug=month-clear-crash` for independent verification if desired.
- The existing open VoiceOver-with-Chromium limitation remains unchanged; this fix does not claim screen-reader verification.
