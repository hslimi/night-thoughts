# Bug Verification: Muted text contrast below target

- **Slug**: muted-text-contrast
- **Tested**: 2026-11-03T08:05:34+08:00
- **Assessment**: ./assessment.md
- **Fix**: ./fix.md
- **Result**: partial

## Summary

The post-fix source token measures at least 4.5:1 on all four reported light backgrounds; the focused and full Vitest suites, production build, and independent browser checks passed. The exact-change-scope check remains inconclusive because the experiment directory is untracked in the enclosing Git repository, so Git cannot establish that only the muted token and focused test changed.

## Checks Performed

| Check | Command / Action | Result | Notes |
|-------|------------------|--------|-------|
| Reproduction (post-fix) | Recomputed WCAG relative luminance ratios from `src/styles.css` token `--muted` against white, page, tile, and gradient backgrounds using an inline Node.js script. | pass | `#5f6e67` measured 5.367:1, 4.985:1, 5.029:1, and 4.691:1, respectively; all exceed 4.5:1. |
| New / updated tests | `npm test -- tests/muted-contrast.test.ts` | pass | 1 file; 4 tests passed. |
| Regression suite | `npm test` | pass | 4 files; 56 tests passed. |
| Production build / type-check | `npm run build` | pass | `tsc -b` and Vite production build completed successfully. |
| Independent production-browser script | `./node_modules/.bin/vite preview --host 127.0.0.1 --port 4174 --strictPort`; then `APP_URL=http://127.0.0.1:4174 node ./scripts/verify-production.mjs` | pass | Preview returned HTTP 200; 16 browser checks passed against the rebuilt local preview. The script's generated JSON was kept outside the project and removed afterward. Port 4173 was occupied, so the preview was run on 4174. |
| Change-scope verification | Checked Git tracking status and the fix record. | inconclusive | The enclosing repository reports the entire experiment directory as untracked; no baseline diff is available to independently verify only the token and focused test changed. |

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

- The exact application change set could not be independently audited against a Git baseline because this experiment directory is untracked.
- No screen-reader verification was performed.

## Recommendation

Hold the final verification as partial until the change scope can be confirmed against a tracked baseline. The contrast defect itself no longer reproduces, and all requested regression, build, and production-browser checks passed.
