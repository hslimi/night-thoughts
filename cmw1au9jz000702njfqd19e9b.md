---
title: "Beyond Vibe Coding: Building and Maintaining an Expense Tracker with GitHub Spec Kit"
seoTitle: "GitHub Spec Kit Tutorial: Build an App with Copilot"
seoDescription: "Spec-driven development end to end: spec, plan, test-first tasks, convergence and bug fixing, and the gaps it caught after green builds."
datePublished: 2026-11-03T23:08:39.234Z
cuid: cmw1au9jz000702njfqd19e9b
slug: beyond-vibe-coding-building-and-maintaining-an-expense-tracker-with-github-spec-kit
cover: https://cdn.hashnode.com/uploads/gql/6a92730f9a9aa7f72e74fdf4/8733568d-2fbf-4c01-ac0c-a86d7497a70d.png
tags: tutorial, ai, software-development, github, typescript

---

Before I build anything, I already have a strong suspicion about one category: coffee. ‘Just one more coffee’ may not be a financial strategy, but it will make a realistic test expense. ☕

An expense tracker is a useful specification exercise because the first prompt sounds complete until implementation begins. Amounts need exact arithmetic. Dates need month boundaries. Storage can be absent, malformed, or unavailable. A delete button is not enough: cancellation, confirmation, and keyboard focus all have observable behavior.

This walkthrough builds that application with GitHub Spec Kit and GitHub Copilot Chat in VS Code. It keeps the generated artifacts, test-first checkpoints, mistakes, convergence finding, and a real maintenance repair. The result is a small frontend application, not a financial service. The process is the product being examined.

## 1\. Why “build me an expense tracker” is underspecified

A prompt such as “add expenses and show monthly totals” leaves important decisions unanswered.

Should `$1.2` be accepted? What about `1e2`, `1,000`, negative values, or three decimal places? Does a date belong to a month in UTC or in the browser’s local calendar? Can an expense be dated next year? What happens when localStorage contains invalid JSON? Should malformed data be replaced automatically?

These are not edge decorations. Each choice changes code and tests. If the coding agent guesses silently, the resulting application may look coherent while implementing different intent.

Spec Kit separates those decisions into a specification, a technical plan, ordered tasks, implementation, and verification. The specification describes observable behavior. The plan chooses technology and boundaries. Tasks sequence the work. Implementation satisfies the artifacts. Verification checks the result rather than confirming that files were generated.

## 2\. What we will build

The demonstration uses React, TypeScript, and Vite. It supports:

- create, edit, and confirmed deletion;
- amount, category, local calendar date, and optional note;
- Food, Transport, Housing, Entertainment, and Other;
- monthly navigation, exact monthly totals, and five category totals;
- category filtering and stable date or amount sorting;
- visible validation and persistence errors;
- localStorage recovery and malformed-data protection;
- keyboard-operable forms and a native deletion dialog;
- desktop, tablet, and phone layouts;
- explicitly labeled, deterministic fictional demo data.

There is no backend, account system, router, global state package, or currency conversion. Money is stored as integer cents. Dates remain `YYYY-MM-DD` strings, avoiding UTC conversion at month boundaries.

The [source folder](https://github.com/hslimi/night-thoughts/tree/main/experiments/spec-kit-expense-tracker) contains the application, specifications, plans, tasks, tests, evidence, and this article.

## 3\. Prerequisites and exact versions

The experiment used the following installed tools. Exact application dependency versions are in `package-lock.json`.

| Tool | Version |
| --- | --- |
| Spec Kit CLI | 1.2.5 |
| Spec Kit integration | Copilot skills |
| VS Code | 1.144.1 |
| Copilot SDK | 1.0.103-unstable.r40031404408.gba6c003 |
| uv | 0.13.0 |
| Spec Kit Python | 3.12.15 |
| Node.js | 22.23.3 |
| npm | 10.9.9 |
| React | 19.3.1 |
| TypeScript | 7.0.2 |
| Vite | 8.3.5 |
| Vitest | 5.1.0 |
| Playwright | 1.64.1 |
| Bug Triage Workflow | 1.0.1 |

The [Spec Kit documentation](https://github.com/github/spec-kit), [Copilot integration instructions](https://github.com/github/spec-kit/blob/main/docs/integrations/copilot.md), and [bug-fixing guide](https://github.github.com/spec-kit/guides/bugfix.html) supplied the current command shapes. Installed CLI help remained authoritative for flags.

![Verified Spec Kit, Copilot, Node.js, and application dependency versions displayed in VS Code](https://cdn.hashnode.com/uploads/gql/6a92730f9a9aa7f72e74fdf4/b8b69e7e-8168-44be-82f5-134dcec9cd20.png align="center")

## 4\. Initialising Spec Kit

For a new empty directory, initialization is:

```bash
specify init . --integration copilot
```

The project records `speckit_version: 1.2.5`, `integration: copilot`, and enabled agent skills in `.specify/init-options.json`. Spec Kit creates its scripts and templates under `.specify` and the Copilot skills under `.github/skills`.

The workflow then ran in this order in GitHub Copilot Chat:

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

These are agent prompts, not terminal commands. The screenshots show the resulting artifacts in VS Code; the sanitized [Copilot stage log](https://github.com/hslimi/night-thoughts/tree/main/experiments/spec-kit-expense-tracker/evidence/workflow/copilot-stage-log.md) preserves the actual prompts and visible results.

## 5\. Establishing engineering rules with a constitution

The constitution is the project’s engineering contract. It requires:

1. exact integer-cent monetary arithmetic;
2. accessible keyboard-first forms and dialogs;
3. meaningful business-logic tests;
4. separation of UI, calculations, and persistence;
5. confirmation for destructive actions;
6. visible persistence outcomes;
7. a scope proportionate to a small demonstration.

The last constraint matters. A specification process can generate its own form of overengineering. This project did not need a backend, repository abstraction, global store, or dozens of microtasks.

The constitution also makes review criteria explicit. A visually complete dashboard would still fail if it used unrestricted floating-point dollar calculations, hid a failed save, or allowed deletion without confirmation.

![The generated constitution showing exact money, accessibility, testing, and separation-of-concerns principles](https://cdn.hashnode.com/uploads/gql/6a92730f9a9aa7f72e74fdf4/22eab54e-b21e-4ca2-ba13-1d9824fc0ac6.png align="center")

## 6\. Writing the specification

`/speckit-specify` turned the baseline prompt into user stories, acceptance scenarios, edge cases, functional requirements, and measurable outcomes. Clarification expanded the initial 13 functional requirements to 15.

The three priorities are deliberately small:

- **P1: record expenses.** Create valid records and retain successful saves after reload.
- **P2: review monthly spending.** Show totals, category breakdowns, filtering, and stable sorting.
- **P3: correct or remove expenses.** Edit records and require confirmation before permanent deletion.

Each story has an independent test. That prevents “the app renders” from becoming a substitute for behavior.

The specification does not choose React or Playwright. A later clarification removed implementation details such as browser-vendor names, storage-envelope mechanics, and numeric representation details from this document. Those choices belong in the technical artifacts.

![The generated specification with its clarification decisions and prioritized user stories](https://cdn.hashnode.com/uploads/gql/6a92730f9a9aa7f72e74fdf4/4d14b216-debb-4161-982c-467be4a92421.png align="center")

## 7\. Clarifying what the agent should not guess

The clarification pass recorded decisions directly rather than inventing a usability study or asking for unnecessary input.

| Decision | Result |
| --- | --- |
| Currency | USD, fixed `en-US`, exactly two decimals |
| Amount storage | Positive integer cents, capped at $100,000.00 per expense |
| Month boundaries | Inclusive local calendar months, no UTC conversion |
| Future expenses | Allowed only in their matching calendar month |
| Deletion | Permanent, no undo, Cancel initially focused |
| Malformed storage | Preserve the raw value and block normal writes |
| Failed writes | Retain work in memory and announce that it is unsaved |
| Demo data | Exact `?demo=1`, fictional, deterministic, in memory only |

Malformed data received a particularly strict rule. Starting fresh requires informed confirmation. Success writes an empty version-1 envelope. Failure preserves the original value and current work with a visible warning.

These choices removed ambiguity before the plan turned them into code structure. They also created acceptance tests that can fail meaningfully.

## 8\. Producing the technical plan

`/speckit-plan` selected one Vite application with three clear boundaries:

```text
src/
├── App.tsx                 # React presentation and interaction
└── expenses/
    ├── model.ts            # Expense and view types
    ├── domain.ts           # Validation and pure calculations
    ├── persistence.ts      # Typed localStorage adapter
    └── demo.ts             # Deterministic fictional records
```

The plan also produced `research.md`, `data-model.md`, `contracts/ui.md`, and `quickstart.md`. It passed the constitution gates before and after design.

The plan is not the implementation. It records decisions such as native `<dialog>.showModal()`, pure monthly selectors, local calendar strings, and Playwright verification in a real browser. Those decisions are reviewable before they become hundreds of lines of code.

![The technical plan showing the React, TypeScript, Vite, storage, and testing decisions](https://cdn.hashnode.com/uploads/gql/6a92730f9a9aa7f72e74fdf4/37273a15-4cec-43bb-a228-fd942566f621.png align="center")

## 9\. Checking requirement quality

The quality stages produced useful findings rather than ceremonial approvals.

`/speckit-checklist` created eight reviewer-owned requirement checks. A separate remediation pass corrected the artifacts and marked all eight only after review.

The first `/speckit-analyze` invocation reached a follow-up prompt without displaying its report. It was not treated as passed. The repeated invocation produced four findings:

- an unmeasurable performance goal;
- a timed usability outcome without a repeatable protocol;
- duplicated persistence language;
- missing coverage for that usability outcome.

The report measured 26/27 requirement/criterion coverage and no critical issues. Remediation replaced the usability claim with a functional browser check, declared that no numerical latency target was in scope, consolidated the persistence wording, and mapped the new criterion to existing test tasks.

![The four consistency-analysis findings and their documented resolutions](https://cdn.hashnode.com/uploads/gql/6a92730f9a9aa7f72e74fdf4/d9a9b851-6981-4b2e-a638-8e4e6369747a.png align="center")

Implementation later stopped at another gate: two built-in checklist items were unchecked because implementation details had leaked into the specification. `/speckit-clarify` moved those details back into the plan and tasks. Copilot did not proceed until both checklists genuinely passed.

![Copilot paused at the requirements checklist gate beside the test-first task breakdown](https://cdn.hashnode.com/uploads/gql/6a92730f9a9aa7f72e74fdf4/43ed912e-a0fe-4a76-9c6f-ea92ded5d5bc.png align="center")

## 10\. Generating tasks and analysing consistency

`/speckit-tasks` produced 16 dependency-ordered tasks. That is enough structure for this application; a 70-task breakdown would obscure rather than help.

The sequence begins with setup, then proves the test runner before application source exists:

```text
T001  Project manifest and build configuration
T002  Vitest, jsdom, and Playwright configuration
T003  Render test fails because src/App.tsx is missing
T004–T006  Write US1 tests
T007–T009  Implement US1
T010–T012  Test and implement the dashboard
T013–T015  Test and implement edit/delete
T016  Run complete validation
```

The T003 failure was intentional and genuine. Vitest reached the test file and failed while resolving `../src/App`. It did not fail because the toolchain was broken. The sanitized output is retained in `evidence/workflow/missing-app-test.txt`.

![The real missing-App test failure with absolute workspace paths removed](https://cdn.hashnode.com/uploads/gql/6a92730f9a9aa7f72e74fdf4/b9c165d7-b6b6-4b97-9822-51fbd16fb661.png align="center")

![Copilot executing the 16-task plan beside the test-first checkpoints](https://cdn.hashnode.com/uploads/gql/6a92730f9a9aa7f72e74fdf4/bb8127ed-c485-4d64-b788-409a13013b12.png align="center")

## 11\. Implementing the application

Traceability is easiest to see with FR-002, the amount rule. The pure domain function accepts a narrow decimal grammar and returns integer cents:

```ts
const match = /^(\d+)(?:\.(\d{1,2}))?$/.exec(input);
if (!match) return null;

const wholePart = match[1].replace(/^0+/, "") || "0";
if (wholePart.length > 6) return null;

const amountCents =
  Number(wholePart) * 100 + Number((match[2] ?? "").padEnd(2, "0"));
if (amountCents <= 0 || amountCents > 10_000_000) return null;
return amountCents;
```

Tests accept `1`, `1.2`, `1.20`, `0.01`, and `100000.00`. They reject blank, zero, negative, signed, grouped, currency-prefixed, exponent, whitespace-padded, nonnumeric, excess-precision, and over-limit inputs. The same validator runs for creation and editing.

The persistence adapter fails closed. `save()` returns `blocked` unless loading succeeded and no malformed raw value is present. A failed write leaves durable data unchanged and the current work visible. A later successful save writes the complete current collection.

Currency formatting also avoids a subtle boundary problem. It converts safe integer cents to `BigInt`, splits dollars and fractional cents, and uses `Intl.NumberFormat` only at presentation. It does not divide a large cent value into a potentially rounded dollar number.

Implementation was not flawless. The first strict build needed React and Node type packages. Native date/select controls invalidated early browser-helper assumptions. A real Chromium check showed that Tab could leave the two-button deletion dialog, so explicit Tab/Shift+Tab wrapping was added. These corrections are preserved in the [implementation notes](https://github.com/hslimi/night-thoughts/tree/main/experiments/spec-kit-expense-tracker/evidence/workflow/implementation-notes.md).

## 12\. Converging the code with the specification

The initial implementation completed with 50 Vitest tests, 15 Chromium tests, and a passing production build. `/speckit-converge` still found a HIGH-severity gap.

Deleting while an edit was active left a stale draft. If no visible transaction neighbor remained, focus could reach **Save changes** instead of **Add expense**. The task checkboxes had not revealed that interaction.

Convergence appended T017. Two component tests and two Chromium tests reproduced the problem before the fix. Confirmed deletion now exits edit mode and clears the draft, and the fallback targets the actual Add expense button. The follow-up result was 52 Vitest tests and 17 Chromium tests passing.

The second convergence run checked 40 requirement and success-criterion items, 10 edge-case groups, plan decisions, and constitution constraints. It reported:

> Converged — the implementation satisfies the spec, plan, and tasks.

It left `tasks.md` byte-for-byte unchanged. This is the useful distinction between implementation and convergence: generation says the work exists; convergence looks for observable intent that is still missing.

![The final clean convergence result with zero remaining findings and unchanged tasks](https://cdn.hashnode.com/uploads/gql/6a92730f9a9aa7f72e74fdf4/4e782f62-86ae-4a32-a07d-d9867e9fc1c5.png align="center")

## 13\. Running and inspecting the UI

The deterministic demo mode is enabled only when `window.location.search === "?demo=1"`. It never reads, writes, or listens to normal expense storage. Reload restores the same fictional records. Every other query string uses normal mode.

The desktop dashboard shows the selected month, exact total, all five category totals, entry form, and transaction controls. The badge explicitly says “Demo mode · fictional data · resets on reload.”

![The populated expense tracker dashboard at 1440×900 with clearly labeled fictional demo data](https://cdn.hashnode.com/uploads/gql/6a92730f9a9aa7f72e74fdf4/4d8c05a0-2376-4634-a39b-2fce9ee2a620.png align="center")

The form keeps amount, category, date, and note visible without decorative clutter.

![Creating a fictional $16.80 Food expense with a Team lunch note](https://cdn.hashnode.com/uploads/gql/6a92730f9a9aa7f72e74fdf4/87472eaf-321b-4401-933b-865e37e51858.png align="center")

Filtering changes the transaction list, not the monthly totals. The Food filter shows Coffee while the monthly category totals remain derived from the unfiltered month.

![Food category filtering with the matching Coffee transaction and sort controls](https://cdn.hashnode.com/uploads/gql/6a92730f9a9aa7f72e74fdf4/856982bd-d60c-41e0-84ad-f1eb27214f33.png align="center")

Invalid input produces adjacent, programmatically associated feedback and does not write a record.

![A negative amount rejected with a visible correction message](https://cdn.hashnode.com/uploads/gql/6a92730f9a9aa7f72e74fdf4/1ef2488f-61ae-4a56-8f45-22c7f2bc2fe1.png align="center")

Deletion uses a native modal dialog. Cancel receives initial focus, Tab and Shift+Tab remain within the two actions, and Escape restores the invoking control.

![The permanent deletion dialog for the fictional Transit pass with Cancel and Delete actions](https://cdn.hashnode.com/uploads/gql/6a92730f9a9aa7f72e74fdf4/d656aba4-2d54-4931-bf24-cc868aa4ca3d.png align="center")

The phone layout uses a 390×844 viewport. Content reflows without page-level horizontal overflow; checks also passed at 768×1024 and 1440×900.

![The expense tracker monthly summary and entry form at 390×844](https://cdn.hashnode.com/uploads/gql/6a92730f9a9aa7f72e74fdf4/2ac292b2-5d30-49fc-bf23-efdaaabc18b1.png align="center")

An independent production-browser script then exercised 16 checks against the built app: keyboard creation, CRUD, exact totals, persistence, invalid amounts, filtering/sorting, deletion focus, accessibility-tree names, three viewports, failed writes, malformed storage, read retry, and console errors. All 16 passed. No console errors or uncaught page errors were recorded.

## 14\. Fixing a bug through Spec Kit

The maintenance example was a genuine defect found during code review, not a planted bug. Muted text used `#74817c`, which measured 4.059:1 on white and 3.770:1 on the page background. The normal-text target was 4.5:1.

The official extension installed with:

```bash
specify extension add bug
```

The three stages then ran separately in Copilot Chat:

```text
/speckit-bug-assess ... slug=muted-text-contrast
/speckit-bug-fix slug=muted-text-contrast
/speckit-bug-test slug=muted-text-contrast
```

Assessment returned **valid**, severity **medium**, and identified the shared token and every applicable surface. Fix changed only `--muted` and added a focused Vitest regression. The test failed on all four backgrounds before the change.

![The genuine contrast assessment with reproduction steps and a scoped remediation](https://cdn.hashnode.com/uploads/gql/6a92730f9a9aa7f72e74fdf4/e4a222ef-29f4-44ff-ae3d-0594d463a96a.png align="center")

The final ratios were:

| Background | Before | After |
| --- | --: | --: |
| White | 4.059:1 | 5.367:1 |
| Page | 3.770:1 | 4.985:1 |
| Category tile | 3.803:1 | 5.029:1 |
| Gradient endpoint | 3.548:1 | 4.691:1 |

The first verification verdict was **partial**: all behavior checks passed, but an untracked experiment directory provided no Git baseline for the claimed two-file source change. A rerun inspected the recorded fix-session edit operations directly. They confirmed only the stylesheet token, the new test, and the fix report changed. The final verdict was **verified**, with no screen-reader claim.

![The final verified bug report with passing contrast, test, build, browser, and scope checks](https://cdn.hashnode.com/uploads/gql/6a92730f9a9aa7f72e74fdf4/19ff6199-4c12-4ef3-9777-c60532f7c081.png align="center")

## 15\. What worked, what did not, and when the process is worth using

The useful part was not a perfect prompt-to-code transformation. It was the number of assumptions that became reviewable before and after implementation.

| Requirement | Evidence |
| --- | --- |
| Exact amount validation | 25 domain tests; invalid-input browser checks |
| Monthly and category totals | Pure boundary and aggregation tests; production total checks |
| Filtering and stable sorting | Domain selectors, component tests, keyboard Chromium scenario |
| Persistence and failed writes | Adapter tests, recovery browser scenarios, production reload checks |
| Malformed stored data | Raw-value preservation and informed start-fresh tests |
| Edit and deletion | Invalid-edit non-mutation, native-dialog keyboard tests, T017 regressions |
| Keyboard and accessible names | Role/name assertions and Chromium accessibility-tree inspection |
| Responsive layout | No horizontal overflow at 390×844, 768×1024, and 1440×900 |
| Demo isolation | Storage/listener spies, deterministic reloads, exact-query checks |
| Contrast repair | Four source-token regressions and verified bug report |

The process also produced friction. Copilot invoked a prerequisite script from the wrong directory. Some test locators were ambiguous. Native `window.confirm` caused Playwright synchronization deadlocks. The first analysis did not display its report. The first bug verdict was partial. Those events belong in the evidence; removing them would make the workflow look more reliable than it was.

There are clear limitations. This is one user, one browser, USD only, and localStorage only. Chromium was tested, not a browser matrix. No VoiceOver review or other screen-reader verification was completed. No timed usability study or numerical latency benchmark was performed. Local browser storage is not a secure multi-device finance backend.

Spec Kit is most useful when requirements have meaningful edge cases, several people need to review intent, or maintenance must remain traceable. For a disposable prototype, the artifact overhead may exceed the benefit. For this experiment, convergence and the bug workflow justified the structure because they found real gaps after generation.

## 16\. Reproduction instructions and source code

Clone the repository and enter the experiment:

```bash
git clone https://github.com/hslimi/night-thoughts.git
cd night-thoughts/experiments/spec-kit-expense-tracker
npm ci
npx playwright install chromium
```

Run the application and verification commands:

```bash
npm run dev
npm run test
npm run test:e2e
npm run build
npx vite preview --host 127.0.0.1 --port 4173
```

With the production preview running in another terminal:

```bash
node scripts/verify-production.mjs
```

The final results are **56/56 Vitest tests**, **17/17 Playwright Chromium tests**, **16/16 independent production-browser checks**, a passing production build, clean convergence, and a verified contrast repair. The npm clean-install audit reported zero vulnerabilities.

The [experiment README](https://github.com/hslimi/night-thoughts/tree/main/experiments/spec-kit-expense-tracker/README.md) explains evidence regeneration, including screenshot processing. The key source links are:

- [application and domain modules](https://github.com/hslimi/night-thoughts/tree/main/experiments/spec-kit-expense-tracker/src/);
- [unit and component tests](https://github.com/hslimi/night-thoughts/tree/main/experiments/spec-kit-expense-tracker/tests/);
- [Chromium scenarios](https://github.com/hslimi/night-thoughts/tree/main/experiments/spec-kit-expense-tracker/e2e/expenses.spec.ts);
- [specification, plan, and tasks](https://github.com/hslimi/night-thoughts/tree/main/experiments/spec-kit-expense-tracker/specs/001-expense-tracker/);
- [test and build evidence](https://github.com/hslimi/night-thoughts/tree/main/experiments/spec-kit-expense-tracker/evidence/verification/);
- [convergence reports](https://github.com/hslimi/night-thoughts/tree/main/experiments/spec-kit-expense-tracker/evidence/workflow/convergence-final.md);
- [bug assessment, fix, and verification](https://github.com/hslimi/night-thoughts/tree/main/experiments/spec-kit-expense-tracker/.specify/bugs/muted-text-contrast/).

Spec Kit’s value is not merely generating code. It makes intent, decisions, tasks, and verification visible and reviewable. Human judgement remains responsible for the result.