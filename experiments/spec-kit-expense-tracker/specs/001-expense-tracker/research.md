# Research: Expense Tracker

Research was scoped to the feature requirements in [spec.md](./spec.md) and current official guidance for the selected browser stack.

## Application structure and testing

**Decision**: Use one React + TypeScript + Vite application. Keep domain rules, persistence, demo fixtures, and UI in small separate modules. Use Vitest with jsdom and React Testing Library for business logic and important user interactions; use Playwright Chromium for a small number of full-browser checks.

**Rationale**: Derived totals, category breakdowns, and transaction views can be computed from the expense records rather than duplicated in UI state. Unit/component tests make validation and calculations quick to exercise; Chromium verifies real native-dialog keyboard/focus behavior, reload persistence, and responsive layouts.

**Alternatives considered**: A global state library, routing, layered repositories/services, or placing every test in Playwright add infrastructure without a requirement. jsdom-only testing would not verify real browser dialog behavior.

Sources: [React: Thinking in React](https://react.dev/learn/thinking-in-react), [Vitest environments](https://vitest.dev/config/environment), [Testing Library guiding principles](https://testing-library.com/docs/guiding-principles/), [user-event](https://testing-library.com/docs/user-event/intro/), [Playwright introduction](https://playwright.dev/docs/intro), [Playwright emulation](https://playwright.dev/docs/emulation).

## Exact money and local calendar dates

**Decision**: Keep amounts as positive integer cents, accept base-10 digits with an optional decimal point followed by one or two digits, reject signs/separators/currency symbols/exponents/whitespace, and cap each expense at USD 100,000.00. Keep expense dates as validated `YYYY-MM-DD` strings and selected months as `YYYY-MM`; compare their year/month portions directly, without UTC conversion. Use local date components for the default current month and format amounts at the presentation boundary with explicit `en-US` USD options and exactly two fraction digits. If an aggregate cannot be represented exactly as a safe integer number of cents (maximum 9,007,199,254,740,991 cents), announce an error instead of rounding or showing a misleading total.

**Rationale**: Integer arithmetic preserves cents. Date-only strings represent calendar dates rather than instants, avoiding timezone shifts at month boundaries. The native date input already exposes normalized date strings. Future dates remain valid, as required.

**Alternatives considered**: Floating-point dollar values and timestamp conversions can introduce rounding or timezone boundary errors. A date library is unnecessary for validated date-only strings and month comparisons in this scope.

Sources: [MDN: Intl.NumberFormat](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl/NumberFormat), [MDN: date input](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/input/date), [MDN: Date.parse](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Date/parse).

## Persistence and malformed data

**Decision**: Put localStorage reads, writes, JSON parsing, and record validation behind one typed adapter. Store a version-1 envelope `{ "version": 1, "expenses": [...] }`. A read failure is announced with a retry-loading action and is not treated as an empty durable collection. After a write failure, retain current work in memory only, leave the last durable value unchanged, and announce that work may be lost on reload; reload restores durable data, and the next successful save writes the complete current collection. Malformed JSON or records retain the original raw value and block persistence until an informed start-fresh confirmation that explains it will replace malformed data and clear current in-memory work; success writes an empty version-1 envelope, while failure preserves the raw value and current work with a visible warning.

**Rationale**: Storage access and writes can fail, and syntactically valid JSON may still violate the expense schema. Failing closed avoids replacing data that could not be read or validated and avoids showing an unsaved mutation as saved.

**Alternatives considered**: Silently substituting an empty list can later overwrite unreadable data. Automatically clearing malformed data violates the preservation requirement. A session-only fallback adds state and UX complexity and is not required.

Sources: [MDN: localStorage](https://developer.mozilla.org/en-US/docs/Web/API/Window/localStorage), [MDN: Storage.setItem](https://developer.mozilla.org/en-US/docs/Web/API/Storage/setItem), [MDN: JSON.parse](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/JSON/parse).

## Deterministic demo mode

**Decision**: Enable fictional data only when the query string is exactly `?demo=1`. Keep fixed fixture records in a separate in-memory state source; in demo mode do not read, write, or listen for changes to persisted user expenses. Demo supports the same in-memory interactions and reload recreates the initial fixture set. Show a clear demo-mode indicator; every other query string uses normal mode.

**Rationale**: The query parameter makes screenshot setup repeatable and explicitly opted in. A separate data source prevents demo records or demo mutations from contaminating persistent user data; a reload recreates the same fixture set.

**Alternatives considered**: Seeding localStorage can mix fictional and user data. An automatic or implicit demo mode can change normal behavior unexpectedly.

Source: [Demo-data requirements](./spec.md#requirements-mandatory).

## Accessible dialog and responsive verification

**Decision**: Use `<dialog>.showModal()` for deletion confirmation, with a visible accessible title, Cancel as the initial focused control, and native modal keyboard containment. Escape and Cancel leave data untouched and restore focus to the invoker. After confirmed deletion, focus the next visible transaction's Edit control, otherwise the previous visible transaction's Edit control, otherwise Add expense. Verify accessible names, keyboard flows, announcements, and focus behavior in Playwright Chromium. Check representative narrow phone, tablet, and desktop viewports.

**Rationale**: Native modal dialog behavior avoids implementing a custom focus trap. Browser-level verification covers focus behavior that a simulated DOM cannot establish. A few representative viewport sizes are proportionate to a responsive single-page demo.

**Alternatives considered**: A custom ARIA modal or toggling the `open` attribute requires more focus/inertness machinery. A large device matrix adds little value beyond representative layouts.

Sources: [MDN: dialog](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/dialog), [WAI-ARIA APG: modal dialog](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/), [Playwright emulation](https://playwright.dev/docs/emulation).
