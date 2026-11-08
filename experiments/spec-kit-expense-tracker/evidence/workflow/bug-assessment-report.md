# Bug Assessment: Muted text contrast below target

- **Slug**: muted-text-contrast
- **Created**: 2026-11-03
- **Source**: pasted text
- **Verdict**: valid
- **Severity**: medium

## Report (verbatim or summarized)

> Muted secondary text in the expense tracker does not meet the normal-text contrast target. The source token `--muted` is `#74817c` in `src/styles.css`. Independent WCAG relative-luminance calculation measured 4.059:1 on white and 3.770:1 on the `#f5f7f5` page background, below 4.5:1. Affected content includes dates, transaction metadata, and introductory text. Expected: choose a muted color that remains visually secondary while achieving at least 4.5:1 on its actual backgrounds, add a reproducible contrast regression check, and leave layout and behavior unchanged. This is a genuine implementation-review defect, not deliberately introduced.

The reported measurements are also recorded in `evidence/verification/contrast-before.txt`.

## Symptom

Secondary text styled with `var(--muted)` falls below the 4.5:1 normal-text contrast target on reported light backgrounds. The expected behavior is a visually secondary color meeting that target on every background where the token is used, without changing layout or behavior.

## Reproduction

1. Inspect the `--muted` declaration in `src/styles.css`.
2. Calculate its WCAG relative-luminance contrast ratio against the reported white and `#f5f7f5` backgrounds.
3. Compare the results (4.059:1 and 3.770:1) with the 4.5:1 normal-text target.

## Suspected Code Paths

- `src/styles.css:9` — defines `--muted` as `#74817c`.
- `src/styles.css:92-95` — applies the token to introductory copy.
- `src/styles.css:193-195` — applies it to category-total metadata on `#f6f8f6`.
- `src/styles.css:469-472` — applies it to transaction descriptions and dates.
- `src/styles.css:486-493` — applies it to empty-state text.
- `src/App.tsx:378` and `src/App.tsx:645-647` — render the introductory copy and transaction metadata affected by the shared token.
- `evidence/verification/contrast-before.txt` — records the reported independent contrast measurements and the affected content.

## Root Cause Hypothesis

The shared muted color was selected without a sufficient contrast constraint for normal-sized text. Because multiple components inherit this token, the deficiency affects several kinds of secondary text across page, card, and tile backgrounds. Confidence: high; the token, its usages, and the reported measurements are present in the repository.

## Proposed Remediation

**Preferred**: Adjust only `--muted` to a visually secondary color whose contrast is at least 4.5:1 against every actual background on which the token appears. Add a reproducible automated contrast regression check that reads or otherwise ties its assertion to the source token, and verifies all relevant backgrounds, including the category tile and the page background/gradient. Keep markup, layout, and behavior unchanged.

**Files likely to change**:
- `src/styles.css`
- A new focused Vitest test under `tests/`

**Tests to add or update**:
- Verify the `--muted` color's WCAG contrast ratio is at least 4.5:1 against each applicable background; ensure the test fails if the token regresses.

## Risks & Considerations

- The adjusted token may look darker than the current muted text, but should remain visually secondary.
- Test coverage must include all surfaces using the shared token, not only the two backgrounds in the report; the category totals use `#f6f8f6`, and the page background includes a light gradient.
- No API, data, layout, or behavior changes are expected.

## Open Questions

- None.
