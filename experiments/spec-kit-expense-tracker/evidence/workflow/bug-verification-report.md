# Bug Verification: Muted text contrast below target

- **Slug**: muted-text-contrast
- **Tested**: 2026-11-03T08:08:30+08:00
- **Assessment**: ./assessment.md
- **Fix**: ./fix.md
- **Result**: verified

## Summary

The post-fix `--muted` token exceeds the 4.5:1 normal-text contrast target on all four reported light backgrounds, so the original contrast defect no longer reproduces. Focused and full Vitest suites, the production build, and production-browser verification passed; the recorded fix patches match the authorized change scope.

## Checks Performed

| Check | Command / Action | Result | Notes |
|-------|------------------|--------|-------|
| Reproduction (post-fix) | Recomputed WCAG relative luminance ratios from the `--muted` token in `src/styles.css` against white, page, category-tile, and gradient-endpoint backgrounds. | pass | All four ratios exceed 4.5:1. |
| New / updated tests | `npm test -- tests/muted-contrast.test.ts` | pass | 1 file; 4 tests passed. |
| Regression suite | `npm test` | pass | 4 files; 56 tests passed. |
| Production build / type-check | `npm run build` | pass | `tsc -b` and Vite production build completed successfully. |
| Production-browser verification | Rebuilt app served at `http://127.0.0.1:4174`; ran `APP_URL=http://127.0.0.1:4174 node ../../../scripts/verify-production.mjs` from this bug directory. | pass | 16 Chromium checks passed against the rebuilt production app; HTTP 200; no browser console errors or uncaught page errors. |
| Change-scope verification | Reviewed the recorded `tool.execution_start` `apply_patch` entries and compared them directly with the resulting files. | pass | Only `tests/muted-contrast.test.ts` (add and environment correction), `src/styles.css` (the `--muted` token), and `.specify/bugs/muted-text-contrast/fix.md` were patched. |
| Lint / type-check | `npm run build` | pass | TypeScript project build passed; no separate lint command is configured. |

## Output Excerpts

```text
#5f6e67 on white (#ffffff): 5.367:1
#5f6e67 on page (#f5f7f5): 4.985:1
#5f6e67 on category tile (#f6f8f6): 5.029:1
#5f6e67 on gradient endpoint (#e8f2ed): 4.691:1

Test Files  4 passed (4)
     Tests  56 passed (56)
Production browser verification passed: 16 checks
```

## Residual Risks

- No screen-reader verification was performed.

## Recommendation

Close the bug — the original contrast defect is resolved, requested regression and production-browser checks passed, and the recorded fix scope was verified.
