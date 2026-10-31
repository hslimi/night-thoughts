# Spec Kit Expense Tracker

A reproducible specification-driven development experiment: a frontend-only personal expense tracker built with GitHub Spec Kit, React, TypeScript, and Vite. The repository preserves the constitution, specifications, plans, tasks, analysis, convergence reports, bug-fix records, tests, and sanitized evidence.

**Article source:** [`article/article.md`](article/article.md)

## Purpose

The experiment demonstrates that specifications, technical plans, task breakdowns, implementation, and verification are different activities. It also demonstrates maintenance: a genuine month-clear crash discovered during convergence was assessed, fixed, and independently verified through Spec Kit's bug workflow.

The final application supports CRUD operations, exact integer-cent money, five categories, local calendar months, monthly/category totals, filtering, deterministic sorting, deletion confirmation, keyboard-accessible forms/dialogs, responsive layouts, localStorage persistence, and guarded malformed-data recovery.

## Current status and limitations

- Final ordered verification: **260 unit tests passed**, **production build passed**, and **167 Chromium checks passed** with one intentional mobile duplicate of the desktop browser-zoom scenario skipped.
- Independent production scenario: **12 checks passed** with no browser console errors.
- CORE-006 intermittent regression: **100/100** single-worker desktop repetitions passed after correction.
- Bug workflow verdict: **verified** for the genuine month-clear crash.
- Final convergence: **no new gaps**, but **not fully converged**. T047, T050, T052, and T054 remain open because VoiceOver review was not completed and the dependent final accessibility gate is unresolved. No screen-reader verification is claimed.
- SC-001 was not measured because no first-time-user study was conducted.
- Acceptance used Chromium only. Firefox, WebKit/Safari, and other browsers are unverified.
- Data is local to one browser profile. There is no backend, sync, authentication, import/export, multi-currency support, or financial advice.
- Demo records are fictional and exist only in memory. They never read, write, or listen to real saved expenses.

## Exact prerequisites and versions used

| Tool                          | Version                                 |
| ----------------------------- | --------------------------------------- |
| Spec Kit CLI                  | 1.2.5                                   |
| Spec Kit Bug Triage Workflow  | 1.0.1                                   |
| Main coding-agent integration | Kimi Code 2.3.0                         |
| Node.js / npm                 | 22.23.3 / 10.9.9                        |
| uv / Spec Kit Python runtime  | 0.13.0 / 3.12.15                        |
| React / ReactDOM              | 19.3.1                                  |
| TypeScript                    | 5.9.3                                   |
| Vite / React plugin           | 8.3.5 / 6.1.2                           |
| Vitest / jsdom                | 4.1.12 / 29.1.1                         |
| Playwright                    | 1.64.1                                  |
| Reference Chromium            | Chrome for Testing 156.0.8078.4 (v1248) |
| `@axe-core/playwright`        | 4.14.0                                  |
| VS Code                       | 1.143.1                                 |
| Hashnode CLI                  | 0.1.1                                   |

The declared minimum is Node.js 20.19. Use `npm ci` so `package-lock.json` determines the application dependencies.

## Setup and execution

From this experiment folder:

```bash
cd app
npm ci
npx playwright install chromium
npm run dev
```

Open `http://localhost:5173/` for normal mode or `http://localhost:5173/?demo=1` for the fixed fictional dataset. Normal mode does not inject demo data.

## Tests and production build

```bash
npm run test:unit
npm run build
npm run test:e2e
```

Serve the production build:

```bash
npx vite preview --host 127.0.0.1 --port 4173
```

With the preview running, execute the independent production-browser scenario and capture UI evidence from the experiment root:

```bash
cd ..
node scripts/verify-production.mjs
node scripts/capture-ui.mjs
```

`capture-ui.mjs` creates six independent Chromium contexts. It sets each viewport explicitly, waits for the application and demo records, uses `page.screenshot({ fullPage: false })`, and verifies PNG dimensions. Desktop is 1440×900; mobile is 390×844.

## Evidence and workflow inspection

Key artifacts:

- Constitution: `app/.specify/memory/constitution.md`
- Specification, plan, data model, tasks, quickstart, and verification: `app/specs/001-expense-tracker/`
- Requirements-quality checklists: `app/specs/001-expense-tracker/checklists/`
- Bug assessment, fix, and verification: `app/.specify/bugs/month-clear-crash/`
- Sanitized commands, versions, failures, corrections, and results: `evidence/`
- Original screenshots: `assets/screenshots/`
- Optimized article images and cover: `article/assets/`
- Separate genuine Copilot read-only analysis: `copilot-demo/`

The Copilot workspace is not a second application implementation. Its `/speckit-analyze` run analyzed a frozen artifact snapshot and did not generate the application. See `copilot-demo/ANALYSIS-ATTEMPTS.md` for the failed active-feature attempt and successful result.

Regenerate derived article assets:

```bash
node scripts/create-cover.mjs
node scripts/prepare-article-assets.mjs
```

The cover uses the actual dashboard and experiment workflow. No stock imagery is used. Screenshot provenance and rejected-capture handling are recorded in `evidence/screenshot-manifest.md`.

## Repository layout

```text
app/             React application, tests, Spec Kit artifacts, and bug records
article/         Tutorial source and optimized images
assets/          Original genuine screenshots
copilot-demo/    Separate read-only Copilot integration and frozen artifacts
evidence/        Sanitized textual evidence and review notes
scripts/         Production verification and asset-generation scripts
```

## Intended use

Use this as an educational reference for specification-driven development, exact frontend money handling, local persistence recovery, and browser verification. It is not a hosted service, accounting system, backup solution, or accessibility certification.

## Attribution

- [GitHub Spec Kit](https://github.com/github/spec-kit) — workflow scaffolding and bug extension (MIT)
- [React](https://react.dev/), [TypeScript](https://www.typescriptlang.org/), and [Vite](https://vite.dev/) — application toolchain
- [Vitest](https://vitest.dev/) and [Testing Library](https://testing-library.com/) — domain and UI tests
- [Playwright](https://playwright.dev/) and Chrome for Testing — real-browser verification
- [axe-core](https://github.com/dequelabs/axe-core) — automated accessibility checks
- [Hashnode CLI](https://www.npmjs.com/package/@hashnode/cli) — private-draft and image-upload tooling
- System fonts and the actual application UI — cover and article images

All demo expenses are fictional. No external datasets, credentials, production user data, or third-party images are included.
