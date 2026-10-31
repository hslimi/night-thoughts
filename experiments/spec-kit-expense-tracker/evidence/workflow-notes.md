# Workflow Review Notes

## Initialisation

- Installed `specify-cli` 1.2.5 with `uv tool install specify-cli` after consulting the official quickstart.
- Selected the officially supported `kimi` integration; Kimi Code 2.3.0 was available.
- Ran `specify init experiments/spec-kit-expense-tracker/app --integration kimi --script sh --non-interactive`.
- The first agent invocation, `kimi --auto -p ...`, failed before changing files because Kimi Code does not allow `--auto` with `--prompt`. Subsequent stages used `kimi -p ...` successfully.

## Constitution

- Ratified six principles as version 1.0.0.
- Review confirmed exact integer-minor-unit arithmetic, accessibility, behavior tests, module separation, destructive confirmation, and non-destructive persistence recovery were all explicit.

## Specification and clarification

- The baseline specification added useful assumptions, including USD, list-only category filtering, newest-first sorting, and local-only persistence.
- Clarification integrated seven supplied decisions into acceptance scenarios, FR-004, FR-009 through FR-014, FR-021 through FR-029, and SC-002 through SC-010.
- Demo activation was made exact: `?demo=1`, fixed fictional in-memory records, fixed month, and no real-storage reads or writes.

## Plan

- Review confirmed that the React/TypeScript/Vite plan passed all six constitution gates.
- The generated plan initially called for Playwright browser screenshots. The user subsequently narrowed article evidence to genuine macOS window-only VS Code screenshots. `plan.md`, `research.md`, and `quickstart.md` were corrected before task generation: Playwright still verifies responsive layouts but does not create article images.
- No backend or additional state/UI framework was introduced.

## Requirements-quality checklist

- The generated custom checklist produced 37 unchecked requirements-quality findings across accessibility, money, persistence, demo isolation, and verification.
- Useful genuine findings included imprecise amount syntax, no explicit aggregate-overflow rule, incomplete failed-write reload semantics, and insufficient proof that demo mode avoids storage reads and listeners.
- `assets/screenshots/03-quality-gate-findings.png` preserves the original unchecked findings.
- The reviewer remediation pass updated the specification, plan, data model, UI contract, research, and quickstart before task generation. All 37 items were re-reviewed and checked only after concrete corrections. The markers concern requirements quality, not implementation completion.
- The corrected artifacts now define exact amount syntax and limits, safe-integer overflow handling, operation-specific failed-write behavior, a fixed ten-record demo baseline, a deterministic 1,000-record SCALE fixture, Chromium-only acceptance, and FR-001–FR-029 verification traceability.
- Installed the bundled Bug Triage Workflow extension 1.0.1 with `specify extension add bug`; it provides assess, fix, and test skills and registers no hooks.

## Task breakdown

- Generated 73 dependency-ordered tasks with test-first implementation mandatory.
- T001–T007 establish the toolchain and require an early runnable red result caused by the missing `src/App.tsx`, not a broken test runner.
- Domain, persistence, UI, and Chromium tests precede their corresponding implementation within each story. Every FR-001–FR-029 requirement maps to verification tasks.
- Added `@axe-core/playwright` to the planned development toolchain for automated accessibility checks; manual keyboard, VoiceOver, responsive, and recovery reviews remain separate tasks.

## Consistency analysis

- The first `/skill:speckit-analyze` process ended after 32 seconds with exit code `-1` before reading artifacts or producing a report. The truncated log is preserved as `09-analysis-failed.txt`; it contains no diagnostic and no files were changed.
- Retried with the minimal official `/skill:speckit-analyze` invocation and preserved the successful 425.053-second run separately as `09-analysis.txt` (exit code 0).
- The report found no critical or high-severity issue and no constitution violation. It reported three medium findings: nondeterministic focus fallback after filtered edits/deletion (A1), missing explicit demo-locale coverage (C1), and missing persistence round-trips for accepted AMOUNT cases (C2). One low finding (I1) identified the plan's stale test-file layout.
- The remediation pass corrected all four findings and consolidated the plan from 73 to 50 tasks. Validation found 50 unique sequential IDs, no undefined task references, and T001–T009 unchanged. The final set retains all named cases, manual reviews, eight Playwright suites, test-first checkpoints, and FR-001–FR-029 traceability.
- A1 now has deterministic focus fallbacks and integrated CORE-006/DELETE-005 coverage; C1 adds demo checks under `en-US` and `de-DE`; C2 adds AMOUNT persistence round-trips and SCALE traceability; I1 updates the planned test layout.
- The second `/skill:speckit-analyze` completed with exit code 0 and no findings. It confirmed zero ambiguity, duplication, constitution, or critical issues and 100% coverage (38/38 requirements) across 50 tasks. Its full report is `09b-analysis.txt`.
- Implementation started only after that report. The first implementation invocation was restricted to T001–T009 and the early missing-App red checkpoint.

## Implementation checkpoints

- T001–T009 completed with no application source beyond `src/test/setup.ts`. Dependencies were installed exactly as recorded in `app/package.json` and `package-lock.json`.
- The independently rerun `npm run test:unit` failed with exit code 1 because `../../src/App` did not exist. This was the intended test-first failure, not a broken runner. The sanitized output is `test-first-red.txt`.
- `04-tests-before-implementation.png` and `05-genuine-failing-test.png` were captured before `src/App.tsx` existed.
- After the setup agent's final response, Kimi emitted a non-actionable `workspace ... is not materialized` checkpoint error. The process itself completed, files and test output were verified independently, and no additional retry was needed. The message remains in `11-implementation-setup.txt`.
- User Story 1 (T010–T020) completed with 126 unit tests, a successful production build, and 16 passing desktop/mobile Chromium checks. Code review confirmed direct string-to-cents parsing, local calendar arithmetic, checked safe-integer totals, and no storage access.
- An initial Chromium DATE-002 failure showed that the native date input would not accept an impossible date programmatically. The test switched only that control to text within the invalid-date scenario, preserving the application and assertion; the rerun passed. This was a test-harness correction, not a product-code workaround.
- `06-exact-money-implementation.png` shows the reviewed direct integer-cent parser.
- Persistence (T021–T026) completed with 171 unit tests, a successful production build, and 58 passing desktop/mobile Chromium checks. The implementation uses a sole strict storage boundary, guarded no-write recovery, optimistic in-memory changes, and confirmed replacement only.
- Edit/deletion (T027–T032) completed with 210 unit tests, 24 new Chromium scenarios, 58 core/persistence regression scenarios, and a successful build. Native dialogs and deterministic focus behavior were reviewed.
- Filtering/sorting (T033–T037) completed with 231 unit tests, 106 passing desktop/mobile Chromium checks, and a successful build. It includes non-mutating exact sorting, useful empty states, and deterministic integrated edit/delete focus fallbacks.
- Demo isolation (T038–T041) completed with 257 unit tests, all 126 desktop/mobile Chromium checks, and a successful build. Both locales and populated/missing/malformed/unreadable real-storage preconditions reported zero demo reads, writes, and listener registrations.
- Automated SCALE/accessibility/responsive verification (T042–T046) completed with 259 unit tests, 165 Chromium checks, one intentional mobile zoom skip, a successful build, and zero automated accessibility violations. Every SCALE interaction completed within 2 seconds. Test-harness mistakes were corrected without weakening assertions; no application defect was demonstrated.
- Six production UI states were captured with six independent Playwright contexts. Initial desktop/mobile framings were rejected for hiding transaction content and retaken after scrolling to the real summary and list. Each PNG passed exact viewport-dimension and visual checks; browser console errors were zero.
- An independent production scenario passed 12 checks covering CRUD, exact totals, filtering/sorting, keyboard submission, deletion confirmation, reload persistence, invalid amounts, month boundaries, malformed storage, responsive overflow, and console output.
- T048 and T049 are complete in `verification.md`. VoiceOver was activated for a validation attempt and then stopped without reliable audible/caption evidence; it was turned off. T047 and T050 remain open, and no screen-reader verification is claimed.
- Initial convergence found a genuine month-clear crash. T051 added a store-boundary validity guard and regression coverage, and the full sequence passed with 260 unit tests and 165 Chromium checks. Overall completion remains open because T047 and T050 are not complete.
- The genuine month-clear defect was temporarily reverted for the dedicated bug workflow, with the reversion disclosed in `bug-maintenance-reversion.md`. Assessment reproduced the crash in unit and Chromium checks, rated it valid/high, and proposed the store guard without changing source. The fix restored the guard and added a Chromium regression. Independent bug verification returned `verified`: original CORE-002 and real desktop/mobile clear-month checks passed, alongside 260 unit tests and 167 Chromium checks.
- Final convergence was **not converged**. It preserved the month fix but appended T052–T056 for the missing VoiceOver review, an intermittent CORE-006 failure, final gate, and incomplete case-by-case T048/T049 evidence. The first browser run had one intermittent failure; 10 targeted repetitions and the full rerun passed.
- T053/T055/T056 are complete. The CORE-006 draft-initialization race was corrected without changing assertions: the unchanged scenario passed 100/100 desktop repetitions after failing 2/30 before correction. All 63 quickstart case IDs and 29 functional requirements now have detailed evidence. The final sequence passed with 260 unit tests and 167 Chromium checks.
- T052 and T054 remain open because VoiceOver cannot be enabled without asking, and no final gate may be claimed without it. A final convergence pass is running.

## Separate Copilot demonstration

- Initialized `copilot-demo/` with the official Copilot integration (`specify init copilot-demo --integration copilot --script sh --non-interactive`). This does not alter or relabel the Kimi-generated application workflow.
- Both an isolated profile and the clean named profile initially required GitHub sign-in. After the user completed the normal sign-in, Copilot became available in the named `spec-kit-copilot` profile.
- The intended demonstration is a genuine read-only `/speckit-analyze` in Copilot Chat against a stable final artifact snapshot. No Copilot report or screenshot existed before authentication, and no Copilot-generated implementation is claimed.

## Evidence capture

- Uses a fresh isolated VS Code profile under `/tmp`, VS Code 1.143.1, and macOS `screencapture -l<window-id>` for workflow images. Final application images may use Playwright viewport-only capture with a fresh browser profile.
- Earlier images were reviewed and retaken to remove Chat/update UI, `.kimi-code` Explorer entries, `/skill:` text, and private paths. The first image now shows a genuine prompt-to-artifact editor trace rather than a fabricated Copilot conversation.
- `03-quality-gate-findings.png` uses a clearly labelled excerpt of the unchanged original findings because the live checklist now shows the resolved state.
- Playwright failure screenshots are disabled; traces and video remain diagnostic-only disposable artifacts.
- AppleScript keystroke automation was unavailable due to macOS permissions. File opening uses the VS Code CLI; window activation uses System Events without simulated typing.
