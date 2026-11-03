# Bug Fix: Muted text contrast below target

- **Slug**: muted-text-contrast
- **Fixed**: 2026-11-03
- **Assessment**: ./assessment.md
- **Status**: applied

## Summary

Changed only the shared `--muted` color from `#74817c` to `#5f6e67`, retaining its secondary green-gray appearance while meeting the 4.5:1 normal-text contrast target on all four tested light backgrounds. Added a focused Vitest regression that reads the token from `src/styles.css`.

## Changes

| File | Change | Notes |
|------|--------|-------|
| `src/styles.css` | modified | Updated only `--muted` to `#5f6e67`. |
| `tests/muted-contrast.test.ts` | added test | Calculates WCAG contrast against white, the page background, category tile, and gradient endpoint. |

## Diff Highlights

| Background | Before (`#74817c`) | After (`#5f6e67`) |
|------------|-------------------:|------------------:|
| White (`#ffffff`) | 4.059:1 | 5.367:1 |
| Page (`#f5f7f5`) | 3.770:1 | 4.985:1 |
| Category tile (`#f6f8f6`) | 3.803:1 | 5.029:1 |
| Gradient endpoint (`#e8f2ed`) | 3.548:1 | 4.691:1 |

## Tests Added or Updated

- `tests/muted-contrast.test.ts::muted text contrast` — checks the source `--muted` token meets 4.5:1 on each applicable background.

## Local Verification

- Commands run:
  - `npm test -- tests/muted-contrast.test.ts` against the original token → expected failure; all four assertions failed (white 4.059:1, page 3.770:1, tile 3.803:1, gradient 3.548:1).
  - `npm test -- tests/muted-contrast.test.ts` after the change → passed, 4 tests.
  - `npm test` → passed, 4 files and 56 tests.
  - `npm run build` → passed TypeScript build and Vite production build.
- Manual checks: verified the tested gradient endpoint is the `#e8f2ed` radial-gradient color in `src/styles.css`; markup, layout, and behavior were unchanged.

## Deviations from Assessment

None.

## Follow-ups

- Run `/speckit-bug-test slug=muted-text-contrast`.
