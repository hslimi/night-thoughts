# Implementation and review notes

## Test-first checkpoints

- T003 ran `npm run test -- tests/App.test.tsx` before application source existed. Vitest failed specifically while resolving `../src/App`; the sanitized output is preserved in `missing-app-test.txt`.
- Domain, persistence, dashboard, edit, and deletion tests were added before their corresponding implementation tasks.
- T017 added two component and two Chromium regressions before its fix. Both reproduced deletion leaving edit mode active; all four passed after the coordinated state reset.

## Material corrections during implementation

- Copilot initially invoked the prerequisite script from the repository root and received exit code 127. It corrected the working directory to the experiment root and reran the script successfully.
- The first strict build identified missing React and Node declaration packages. Copilot added the type dependencies rather than weakening TypeScript checking.
- Early Chromium helpers made incorrect assumptions about traversal through native date and select controls. The helpers were corrected while retaining keyboard interaction and behavior assertions.
- A real browser check showed that Tab could leave the two-button modal after the last control. Copilot added explicit Tab/Shift+Tab wrapping and reran the dialog checks.
- Two full-suite browser tests deadlocked because they awaited a click before accepting native `window.confirm`. Playwright dialog event handling was corrected before the final rerun.
- Final validation changed the no-neighbor deletion fallback to the actual Add expense submit button.
- The first independent production-script run used the wrong focus expectation after deleting the last amount-sorted record. The application correctly focused the remaining previous record's Edit control; the script assertion was corrected and the complete production check then passed.
- The first convergence run found that deletion during an active edit left a stale draft and could focus Save changes. T017 cleared edit/draft state and added regression coverage.
- A small manual presentation correction changed the demo badge to `Demo mode · fictional data · resets on reload`, making the nature of the records explicit without changing application behavior.

## Validation chronology

- Initial implementation completion: 50 Vitest tests, 15 Chromium tests, and a passing production build.
- T017 completion: 52 Vitest tests, 17 Chromium tests, and a passing production build.
- Independent production-browser verification and the structured contrast bug fix are separate later gates; this file does not claim their results.

## Accessibility scope

No VoiceOver review was performed. See `evidence/verification/accessibility-scope.txt` for the verification boundary.
