# Screenshot Manifest

Workflow images are genuine macOS window-only captures of VS Code 1.143.1. Application images, when added, will be genuine Playwright viewport captures from a fresh browser profile. No image may contain Kimi/Kimi Code UI, agent panels, orchestration commands, account details, or private paths. No full-screen crop, generated illustration, or fabricated terminal output is permitted.

## Capture environment

- Workspace: the experiment folder opened in an isolated VS Code profile under `/tmp`.
- Window: 1440 × 900 CSS pixels. PNG pixel dimensions vary with the active display scale; the verified files are 1920 × 1112 or 2880 × 1800 pixels.
- Theme: Default Dark Modern; editor font size 16; minimap, Chat, secondary sidebar, update prompts, and tips disabled. The Explorer excludes `.kimi-code` and `node_modules`.
- Files are opened with the VS Code CLI. The window is brought to the foreground with System Events.
- Actual capture form: `screencapture -x -o -l<window-id> assets/screenshots/<descriptive-name>.png`.
- Window IDs are discovered from Core Graphics using the isolated VS Code process ID. Each image is read back and checked for content, legibility, prohibited orchestration details, and sensitive information.

## Verified images

| File | Actual source shown | Verification |
| --- | --- | --- |
| `01-requirement-interview.png` | `evidence/prompt-artifact-trace.md`: actual prompt, generated specification response, clarification exchange, and resulting requirements | Complete VS Code window only; genuine editor trace, not a fabricated chat-UI capture |
| `02-behavior-contract.png` | `app/specs/001-expense-tracker/spec.md`, edge cases and functional requirements | Complete VS Code window only; consistent theme and no orchestration folders |
| `03-quality-gate-findings.png` | Clearly labelled excerpt of the original unchecked CHK001–CHK008 items | Complete VS Code window only; unchanged pre-remediation findings |
| `04-tests-before-implementation.png` | `tests/ui/app.smoke.test.tsx` as written before `src/App.tsx` existed | Complete VS Code window only; test imports the then-missing App |
| `05-genuine-failing-test.png` | Sanitized output from an independent `npm run test:unit` run | Complete VS Code window only; genuine exit-1 missing-App failure with `<project>` path substitution |
| `06-exact-money-implementation.png` | `src/domain/money.ts`, direct decimal-string parsing into checked integer cents | Complete VS Code window only; no orchestration or private content |
| `07-final-passing-tests.png` | Output excerpt from clean install, 260 unit tests, production build, and 167 Chromium checks | Complete VS Code window only; actual final results |
| `08-architecture-review.png` | Reviewed domain, persistence, state, demo, and component boundaries | Complete VS Code window only; actual final module tree |
| `09-final-convergence.png` | Final convergence result with verified checks and open VoiceOver gate | Complete VS Code window only; no full-convergence claim |
| `10-desktop-dashboard.png` | Production demo summary and actual transactions at 1440×900 | Fresh Playwright context; application viewport only; console errors 0 |
| `11-expense-creation.png` | Production form filled with fictional `16.40` food expense and Team lunch note | Fresh Playwright context; application viewport only; fictional demo label visible |
| `12-category-filtering.png` | Food filter with three matching transactions and unfiltered monthly total | Fresh Playwright context; application viewport only; console errors 0 |
| `13-invalid-amount-validation.png` | Negative `-1` input with visible associated validation | Independent fresh Playwright context; application viewport only; console errors 0 |
| `14-deletion-confirmation.png` | Native dialog for the fictional `$32.40` transport expense | Independent fresh Playwright context; Cancel initially focused |
| `15-mobile-dashboard.png` | Production demo summary and controls at 390×844 | Independent fresh Playwright mobile context; application viewport only; no horizontal overflow |
| `16-copilot-read-only-analysis.png` | Genuine `/speckit-analyze` prompt and Copilot report beside the frozen specification | Complete VS Code window only; separate read-only demonstration; no application-generation claim |

The six UI states use six independent Playwright contexts. Every capture uses `page.setViewportSize`, `page.screenshot({ fullPage: false })`, and a PNG dimension check. A rejected full-desktop OS screenshot containing agent UI was deleted and is excluded from the article, commit, and Hashnode upload.

Earlier captures were reviewed and retaken to remove Chat/update UI, orchestration folders and commands, and private paths. No affected image is approved for upload.
