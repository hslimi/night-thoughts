# AI Agent Engineering Feedback Loops

A deliberately small TypeScript experiment showing a requirement interview, shared domain language, test-driven development, and an architecture review around one subscription-reminder policy.

The companion article is [Your AI Agent Writes Code Fast. Here’s How to Stop It Building a Ball of Mud](article.md).

## Agreed behavior

`sendTrialEndingReminder` sends one reminder only when:

- the subscription is `trialing`;
- `trialEndsAt` is strictly in the future;
- `trialEndsAt` is at most 72 hours away;
- no trial-ending reminder is already recorded.

Exactly 72 hours is eligible. Expired trials, cancelled subscriptions, and worker retries after a successful send do not produce email. Comparisons use absolute UTC instants.

The complete decisions are in the [behavior contract](docs/behavior-contract.md), [GLOSSARY.md](GLOSSARY.md), and [ADR 0001](docs/adr/0001-trial-ending-reminder-policy.md).

## Reproduce the final verification

From the repository root, enter the experiment:

```bash
cd experiments/ai-agent-engineering-feedback-loops
```

Install the exact lockfile versions:

```bash
npm ci
```

Run TypeScript checking:

```bash
npm run typecheck
```

Run all tests:

```bash
npm test
```

Expected final result: TypeScript exits successfully and Vitest reports one passed test file with ten passed tests.

Verified with Node.js 22.23.3, npm 10.9.9, TypeScript 7.0.2, and Vitest 5.0.5. Node.js 22 or later is required by `package.json`. Only TypeScript and Vitest are direct development dependencies; both are pinned and the lockfile is committed. No formatter or linter is configured.

## Test-first evidence

The tests were created before `src/trial-ending-reminders.ts` existed.

- [RED output](evidence/red-tests.txt): one failed suite, no tests run, because the implementation module did not exist.
- [Initial GREEN output](evidence/green-tests.txt): ten tests passed after the smallest implementation.
- [Final verification](evidence/final-verification.txt): TypeScript checking and all ten tests passed after the architecture-review rename.

The saved terminal commands normalized the absolute workspace root to `.` with `sed`; no test status, error, or result was edited. The screenshots show the exact commands used.

## Project layout

```text
src/trial-ending-reminders.ts          Public reminder seam and policy
tests/trial-ending-reminders.test.ts   Behavior, boundary, UTC, and retry tests
docs/requirement-interview.md          Questions and confirmed decisions
docs/behavior-contract.md              Executable behavior in prose
docs/architecture-review.md            Selected candidate and decision
docs/adr/0001-*.md                     Architecture and scope decision
evidence/                              Genuine sanitized terminal output
assets/screenshots/                    Original VS Code window captures
article.md                             Canonical article with local images
hashnode-draft.md                      Hashnode article with CDN images
```

## Screenshots

The eight PNG files are direct macOS captures of the VS Code window for this experiment, not illustrations. They show:

1. the vague request and genuine Copilot requirement interview;
2. the resulting behavior contract;
3. tests before implementation, with Copilot's test review;
4. the genuine RED integrated-terminal run;
5. the focused implementation and Copilot response;
6. the genuine GREEN run;
7. the architecture review and selected candidate;
8. final TypeScript and test verification.

## Skill attribution and what actually ran

The workflow references [mattpocock/skills](https://github.com/mattpocock/skills) at commit `a496f5513d4a4cf889bc48e189e579f4b0bdf6aa`.

The three selected skills were inspected and installed into scratch directories with `skills@latest`. In the captured workflow, their interview, TDD, and architecture-survey instructions were applied manually through GitHub Copilot Chat Ask mode. No upstream slash command ran. Copilot returned interview questions, a test review, an implementation, and an architecture candidate; file edits were reviewed and applied separately. Ask mode did not modify the workspace.

The installer found 38 skills and installed the three selected copies. It also skipped an unrelated in-progress `software-factory` skill after a YAML parse warning; that did not prevent the selected installs.

## Limitations

This is a policy module with in-memory test adapters, not a production subscription system. It deliberately excludes real email, persistent storage, distributed queues, HTTP, billing, concurrent-worker claims, and delivery-failure recovery. The check–send–record sequence prevents sequential worker retries after success; it does not claim atomicity across concurrent workers or failures between sending and recording.
