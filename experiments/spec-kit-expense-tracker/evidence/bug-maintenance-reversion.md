# Bug Maintenance Demonstration: Month-Clear Crash

## Origin

This was a genuine defect discovered by the initial Spec Kit convergence run, not a synthetic bug invented for the article. Clearing the native Month control supplied an empty string to `summarizeMonth`, which threw `Expected a valid local month` and unmounted the application.

Convergence added and completed T051. The guard and regression test passed, followed by 260 unit tests and 165 Chromium checks.

## Maintenance reversion

To exercise Spec Kit's separate assess → fix → test workflow against the original symptom, the T051 guard is temporarily removed from `selectMonth` in `src/state/useExpenseStore.ts`. The regression test and convergence report are retained unchanged. This is a disclosed maintenance reversion of a genuine defect, not a claim that the final application contains it.

The bug workflow must reproduce the failure, assess the cause, restore validation at the store boundary, rerun the original reproduction, and record its verdict. The final source must retain the validated month behavior.
