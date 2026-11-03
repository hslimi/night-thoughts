# Spec Kit Expense Tracker

A completed end-to-end GitHub Spec Kit experiment: a frontend-only personal expense tracker, its generated engineering artifacts, automated and real-browser verification, focused evidence, a structured maintenance repair, and a step-by-step article.

The application and all Spec Kit stages in this fresh run were produced through GitHub Copilot Chat in VS Code. Small manual corrections and independent verification scripts are documented in the evidence. No prior implementation or article was restored.

## Purpose

The experiment tests whether specification-driven development makes intent and maintenance more reviewable than an unstructured coding prompt. It covers constitution, specification, clarification, planning, requirement checklists, test-first tasks, consistency analysis, implementation, convergence, and an assess → fix → test bug workflow.

The application supports create/edit/delete, exact integer-cent amounts, five categories, local-calendar month navigation, monthly/category totals, category filtering, stable sorting, deletion confirmation, validation, localStorage recovery, keyboard interaction, responsive layouts, and isolated fictional demo data.

## Article

- Title: **Beyond Vibe Coding: Building and Maintaining an Expense Tracker with GitHub Spec Kit**
- Subtitle: **A practical walkthrough of specifications, clarification, quality gates, implementation, convergence, and structured bug fixing.**
- Source: [article/article.md](./article/article.md)
- Images: [article/assets/](./article/assets/)

## Project layout

```text
.
├── .github/skills/               # Copilot Spec Kit and bug skills
├── .specify/
│   ├── memory/constitution.md
│   ├── bugs/muted-text-contrast/ # Assessment, fix, and verification
│   └── extensions.yml
├── article/
│   ├── article.md
│   └── assets/                   # Cover, workflow, and UI images
├── e2e/expenses.spec.ts          # Real Chromium scenarios
├── evidence/
│   ├── verification/             # Versions, results, manifests, browser evidence
│   └── workflow/                 # Reports, prompts, corrections, original images
├── scripts/                      # Independent verification and capture tooling
├── specs/001-expense-tracker/    # Specification, plan, tasks, contracts, analysis
├── src/                          # React UI, domain, persistence, demo fixtures
├── tests/                        # Vitest unit/component/contrast tests
├── package.json
└── package-lock.json
```

The application lives at the experiment root rather than in a nested `app/` directory. This is the single-Vite-project structure selected by the actual [technical plan](./specs/001-expense-tracker/plan.md); it avoids a redundant nesting level while keeping the experiment self-contained.

## Prerequisites and versions used

Required for the application:

- Node.js **22.23.3** and npm **10.9.9**;
- Playwright Chromium, installed with `npx playwright install chromium`.

Resolved application versions include React **19.3.1**, TypeScript **7.0.2**, Vite **8.3.5**, Vitest **5.1.0**, and Playwright **1.64.1**. The lockfile is authoritative for transitive dependencies.

Required only to repeat the Spec Kit workflow:

- Spec Kit CLI **1.2.5** with the Copilot integration;
- uv **0.13.0** and Spec Kit Python **3.12.15**;
- VS Code **1.144.1** with GitHub Copilot Chat;
- Copilot SDK **1.0.103-unstable.r40031404408.gba6c003**;
- Spec Kit Bug Triage Workflow **1.0.1**, installed with `specify extension add bug`.

Optional evidence processing uses Python and Pillow **11.3.0**. The sanitized environment record is [evidence/verification/environment.txt](./evidence/verification/environment.txt).

## Install and run

From this directory:

```bash
npm ci
npx playwright install chromium
npm run dev
```

Open the local URL printed by Vite. Normal mode starts with the current local month and persists successful changes in `localStorage` under `expense-tracker:expenses`.

For deterministic screenshots and evaluation, open exactly:

```text
http://localhost:5173/?demo=1
```

The badge identifies the records as fictional. Demo changes remain in memory and reset on reload. Additional query parameters do not activate demo mode, and demo mode never reads, writes, or registers listeners for normal expense storage.

## Test and production-build commands

```bash
npm run test
npm run test:e2e
npm run build
```

Final verified results:

| Check | Result |
|---|---|
| Clean installation | `npm ci`; 109 packages added, 110 audited, zero npm vulnerabilities |
| Vitest | **56/56 passed** across 4 files |
| Playwright Chromium | **17/17 passed** |
| Production build | TypeScript and Vite passed; 20 modules transformed |
| Independent production browser | **16/16 checks passed** |
| Browser console | Zero console errors and zero uncaught page errors |
| Final convergence | Clean; `tasks.md` unchanged byte-for-byte |
| Contrast bug verification | **Verified** on all four applicable backgrounds |

The initial implementation reported 50 unit/component tests and 15 Chromium tests. Convergence added two component and two Chromium regressions. The bug workflow added four contrast checks. These stages are retained rather than presenting only the final counts.

## Independent production verification

Build and launch the production app:

```bash
npm run build
npx vite preview --host 127.0.0.1 --port 4173
```

In another terminal, from the same directory:

```bash
node scripts/verify-production.mjs
```

The script uses fresh Playwright Chromium contexts to exercise CRUD, integer-cent persistence, negative/malformed amounts, exact totals, filtering/sorting, keyboard and dialog focus, accessibility-tree names, responsive overflow, failed-write recovery, malformed storage, read retry, and console errors. It writes [production-browser.json](./evidence/verification/production-browser.json).

No VoiceOver review was completed. Semantic roles, accessible names, keyboard behavior, native-dialog focus, and calculated contrast were checked, but screen-reader compatibility is not claimed.

## Inspect the Spec Kit workflow

Start with:

- [constitution](./.specify/memory/constitution.md);
- [specification](./specs/001-expense-tracker/spec.md);
- [technical plan](./specs/001-expense-tracker/plan.md);
- [16 original tasks plus convergence task T017](./specs/001-expense-tracker/tasks.md);
- [analysis remediation](./specs/001-expense-tracker/analysis-remediation.md);
- [first convergence finding](./evidence/workflow/convergence-first.md);
- [final clean convergence](./evidence/workflow/convergence-final.md);
- [bug assessment](./.specify/bugs/muted-text-contrast/assessment.md);
- [bug fix](./.specify/bugs/muted-text-contrast/fix.md);
- [final bug verification](./.specify/bugs/muted-text-contrast/test.md).

The [Copilot stage log](./evidence/workflow/copilot-stage-log.md) contains sanitized genuine prompts and visible results. [Implementation notes](./evidence/workflow/implementation-notes.md) record wrong-directory invocation, test-helper corrections, the dialog focus gap, and other non-ideal parts of the run. The first partial bug verdict is preserved in [bug-test-initial-partial.md](./evidence/workflow/bug-test-initial-partial.md).

To repeat the workflow in a new empty project:

```bash
specify init . --integration copilot
```

Then invoke these prompts separately in GitHub Copilot Chat and review each artifact:

```text
/speckit-constitution
/speckit-specify
/speckit-clarify
/speckit-plan
/speckit-checklist
/speckit-tasks
/speckit-analyze
/speckit-implement
/speckit-converge
```

These are Copilot Chat prompts, not shell commands. Repeating them requires new product decisions and review; this README does not pretend that rerunning them will reproduce identical generated artifacts.

## Regenerate or inspect evidence

There are **18 article-ready PNGs**: one cover, 11 workflow images, and six application states. The 11 original VS Code workflow captures are also retained under `evidence/workflow/`. [screenshot-manifest.json](./evidence/verification/screenshot-manifest.json) records dimensions, byte sizes, and SHA-256 hashes.

Text evidence includes exact sanitized test/build output, a clean-install record, accessibility scope, contrast measurements, and the production-browser JSON. No credentials, browser profiles, local databases, or private session logs are included.

To regenerate the application images, start the production preview as above, then run:

```bash
node scripts/capture-screenshots.mjs
node scripts/create-cover.mjs
python3 scripts/process-screenshots.py
```

The capture script creates fresh contexts, sets 1440×900 desktop and 390×844 mobile viewports, opens only the local app with `?demo=1`, waits for fictional data, and uses `page.screenshot({ fullPage: false })`. Raw captures and crop metadata are written under `evidence/` for inspection. The processing script creates tightly framed article images and optimized workflow copies.

Inspect every regenerated image before sharing it. Remove `evidence/.capture-tmp/` after acceptance; it is disposable and is not part of the committed evidence.

## Audit documentation links

Run the automated checker over the generated Markdown, relative paths and anchors, local images, GitHub targets, and external HTTP/CDN URLs:

```bash
python3 scripts/audit-links.py --output evidence/verification/link-audit.json
```

To include the unpublished Hashnode draft, retrieve its current body and pass it to the checker:

```bash
hashnode -p 6a9439bd520526685ca0ce83 --json draft get 6ae62b9522949cf8d9ef1cb0 > /tmp/spec-kit-link-audit-draft.json
python3 scripts/audit-links.py \
  --draft /tmp/spec-kit-link-audit-draft.json \
  --output evidence/verification/link-audit-final.json
```

The checker exits nonzero on a real broken destination and identifies reserved example URLs separately. [link-audit.md](./evidence/verification/link-audit.md) records the initial failures, exact replacements, and final zero-broken-link result. These read-only checks do not publish or change the draft.

## Limitations and intended use

This is a small tutorial application for one person in one browser. It is not a hosted service, accounting system, or secure finance backend. It uses USD only, has no accounts or synchronization, and stores unencrypted data in localStorage. Only Chromium was exercised; no cross-browser matrix, timed usability study, numerical latency benchmark, or screen-reader verification is claimed.

Specifications and generated artifacts are inspection examples, not a guarantee that another model run will make the same decisions. The screenshots and demo records are fictional and were created in this experiment. External tools should be reviewed for their own licenses, terms, and privacy implications before use with sensitive code.

## Attribution

- [GitHub Spec Kit](https://github.com/github/spec-kit) and its Copilot skills and Bug Triage Workflow;
- [GitHub Copilot Chat in VS Code](https://code.visualstudio.com/docs/copilot/chat/copilot-chat);
- [React](https://react.dev/), [TypeScript](https://www.typescriptlang.org/), and [Vite](https://vite.dev/);
- [Vitest](https://vitest.dev/), [Testing Library](https://testing-library.com/), and [Playwright](https://playwright.dev/);
- [MDN](https://developer.mozilla.org/) and the [WAI-ARIA Authoring Practices modal dialog pattern](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/), cited in `research.md`;
- [Pillow](https://python-pillow.org/) for image cropping and optimization.

No stock photography, external UI artwork, external datasets, or third-party demo records were used. The cover combines the actual final dashboard with a workflow diagram generated for this experiment.
