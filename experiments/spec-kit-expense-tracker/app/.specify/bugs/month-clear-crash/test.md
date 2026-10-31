# Bug Verification: Clearing Month preserves the last valid dashboard

- **Slug**: month-clear-crash
- **Tested**: 2026-11-01
- **Assessment**: ./assessment.md
- **Fix**: ./fix.md
- **Result**: verified

## Summary

The original CORE-002 reproduction no longer fails, and clearing the native Month control in real desktop and mobile Chromium preserves the selected month, total, transaction list, and application heading without page errors. The full unit, build/type-check, and browser regression checks passed; no regressions were found.

## Checks Performed

| Check | Command / Action | Result | Notes |
|-------|------------------|--------|-------|
| Original reproduction (post-fix) | `npm run test:unit -- tests/ui/monthlyDashboard.test.tsx -t CORE-002` | pass | Exit 0; 1 passed, 4 skipped. Clearing Month retained `2026-10`, the `$3.00` total, and two transactions. |
| Real Chromium regression | `npm run test:e2e -- e2e/core.spec.ts -g "clearing native Month"` | pass | Exit 0; 2 passed across desktop and mobile Chromium. The actual `input[type=month]` was filled with `''`; November, `$8.88`, and its transaction remained, with no page errors or unmount. |
| Unit regression suite | `npm run test:unit` | pass | Exit 0; 18 files and 260 tests passed. |
| Lint / type-check and production build | `npm run build` | pass | Exit 0; `tsc --noEmit` and Vite production build completed successfully. No separate lint script is configured. |
| Browser regression suite | `npm run test:e2e` | pass | Exit 0; 167 passed and 1 skipped across desktop and mobile Chromium. The skip is the existing mobile 200% browser-zoom case. |

## Output Excerpts

```text
CORE-002 unit reproduction:
Test Files  1 passed (1)
Tests       1 passed | 4 skipped (5)

Targeted Chromium regression:
2 passed (716ms)

Full unit suite:
Test Files  18 passed (18)
Tests       260 passed (260)

Build:
tsc --noEmit && vite build
✓ built in 65ms

Full Chromium suite:
1 skipped
167 passed (30.8s)
```

## Residual Risks

- Browser verification covered the configured desktop and mobile Chromium projects, not other browser engines.
- VoiceOver behavior was not tested; no screen-reader verification is claimed.
- The full browser suite retained its existing mobile 200% browser-zoom skip, unrelated to this clear-month path.

## Recommendation

Close the bug — the original crash no longer reproduces, the real-Chromium clear action preserves the dashboard, and all requested regression checks passed.
