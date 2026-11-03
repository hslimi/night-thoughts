# Quickstart: Expense Tracker Validation

Run these checks from the project root after implementation.

## Prerequisites

- Node.js and npm supported by the installed Vite release.
- Chromium installed for Playwright.

## Install and run

```sh
npm install
npx playwright install chromium
npm run dev
```

Open the local URL printed by Vite. Verify the default month, dashboard totals, category filter, sort controls, and responsive layout. To verify the deterministic fictional dataset, open the same URL with exactly `?demo=1`; the page should show the demo indicator and must not read, write, or listen to normal expense storage. Verify that `?demo=1&other=value` uses normal mode.

## Automated validation

```sh
npm run test
npm run test:e2e
npm run build
```

The Vitest suite should cover exact amount-text syntax and date/category validation, inclusive USD 100,000.00 expense limit, cent-exact monthly and category calculations, announced errors for aggregates above 9,007,199,254,740,991 cents, filtering and stable sorting, empty states, persistence errors, malformed-data protection, and accessible names, validation announcements, and keyboard interactions. The Playwright Chromium suite should verify save/reload; failed-write memory retention and restoration of durable data on reload; complete-collection persistence after a later successful save; read-failure retry; edit; delete cancel/confirm and focus fallback order; informed start-fresh confirmation and both successful and failed empty-envelope writes; exact-query demo isolation, in-memory interactions, and reload determinism. Require keyboard-driven completion of create, edit, filter, sort, and delete flows. At each viewport size—390x844, 768x1024, and 1440x900—verify the layout and confirm there is no page-level horizontal overflow (the document's scroll width does not exceed its client width). The production build must complete without type or bundling errors.

For malformed-data validation, seed the application storage key with invalid JSON and with invalid expense records. Confirm the warning is announced, the original raw value remains unchanged, and normal persistence stays blocked until the user confirms an informed start-fresh action that explains it will replace malformed data and clear current work. Verify success replaces it with a version-1 envelope whose `expenses` array is empty; a failed write leaves the raw value, current work, and warning unchanged. For storage failures, use a test storage implementation that throws on reads or writes. Verify read failure exposes retry without presenting an empty collection as durable; failed writes retain work only in memory, leave the durable value unchanged, and announce the risk of reload. Verify reload restores durable data and that the next successful write stores the entire current collection.

For demo isolation, spy on real expense storage reads, writes, and storage-event listener registration. Verify zero calls in exact-query demo mode, same in-memory interactions as normal mode, fixed fictional records after reload, and normal mode for every non-exact query string. For accessibility and deletion focus, test keyboard completion of primary flows, accessible control names and error announcements, focus containment and Escape/Cancel behavior, then confirm focus moves to the next visible Edit control, previous visible Edit control, or Add expense in that order.

See [data-model.md](./data-model.md) for record and state rules and [contracts/ui.md](./contracts/ui.md) for user-visible behavior.
