# Research: Personal Expense Tracker

## Decision: Frontend stack and project shape

- **Decision**: Build one frontend-only React application with TypeScript and Vite. Use React and ReactDOM as the only runtime dependencies; use semantic HTML and handcrafted CSS rather than a component, CSS, or state-management framework.
- **Rationale**: The requested stack supports a small typed module structure and fast local development. Native controls and CSS are sufficient for a polished responsive single-page application and keep the dependency surface minimal. No backend, router, remote API, or global state library is needed.
- **Alternatives considered**: A larger component/state stack was rejected as unnecessary; vanilla TypeScript was rejected because React is explicitly requested.

## Decision: Exact money handling

- **Decision**: Trim amount strings and parse the exact accepted decimal grammar directly into positive integer cents, rejecting prohibited syntax, excess precision, zero, and values above 999999999.99 without floating-point input conversion. Persist `amountCents`, calculate summaries with checked safe-integer addition, expose aggregate overflow as an error, and format only at the UI boundary with fixed `Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' })` applied to `cents / 100`.
- **Rationale**: Integer cents satisfy exact arithmetic and two-decimal USD presentation. String-based parsing rejects excess precision before conversion. Safe-integer checks prevent individual or aggregate values that JavaScript cannot represent exactly; fixed locale options make output independent of browser locale.
- **Alternatives considered**: Floating-point dollars were rejected because they accumulate rounding errors; silent rounding/clamping was rejected because it misstates money; a decimal or bigint library was rejected because bounded integer cents and checked sums are sufficient and require no dependency.

## Decision: Local calendar dates and months

- **Decision**: Treat dates as validated `YYYY-MM-DD` strings and months as `YYYY-MM` strings. Validate year, month, and day with calendar arithmetic, derive month membership with the date's first seven characters, and use lexical date comparison. Use local `Date` getters only to obtain the initial current month, never UTC date conversion.
- **Rationale**: String-based domain operations avoid timezone shifts and naturally include whole local month boundaries. Native date and month inputs provide the same string shapes at the UI boundary.
- **Alternatives considered**: ISO timestamps and UTC parsing were rejected because they can move a record into another local day or month; a date library was rejected because the required calendar operations are small and pure.

## Decision: Module boundaries and state ownership

- **Decision**: Keep pure types, validation, money/date operations, calculations, filtering, and sorting in `src/domain`; isolate every real localStorage operation in `src/persistence`; coordinate in-memory state and persistence outcomes in one React store hook; keep components limited to rendering and interaction.
- **Rationale**: Explicit boundaries make business rules testable without React or browser APIs and prevent storage failures from leaking into calculations. Derived summaries and visible transactions are recomputed from the expense collection rather than stored independently.
- **Alternatives considered**: Putting storage calls in components or calculations was rejected as a constitution violation; introducing a global state library was rejected because local React state and derived values are sufficient.

## Decision: Persistence and recovery protocol

- **Decision**: Store one versioned JSON envelope under a namespaced localStorage key and validate the complete collection all-or-nothing. Return discriminated outcomes for missing, valid, readable malformed, unreadable, write-failed, and saved states. Missing data is ready/empty. Readable malformed or unreadable storage starts empty guarded memory and performs no write until accessible informed confirmation. Only readable malformed raw data can be compared for preservation; unreadable data is preserved solely by not writing. Start fresh writes an empty envelope after confirmation; a first replacement save writes the complete current collection after confirmation. Ordinary quota, serialization, and mid-session write failures retain changed work only in memory; reload restores the last durable collection and a later success saves all current work and clears the warning.
- **Rationale**: A schema envelope and explicit state outcomes make persistence behavior testable. Non-destructive guarded recovery avoids overwriting unreadable or malformed user data, while optimistic in-memory updates preserve current work without claiming durability.
- **Alternatives considered**: Automatically resetting malformed data or writing before confirmation was rejected as destructive; inspecting or claiming preservation of an unreadable raw value was rejected as impossible; salvaging valid records from an invalid collection was rejected as inconsistent; rolling back every failed change was rejected because it discards valid current work. Concurrent normal-tab synchronization is excluded, but demo isolation remains mandatory.

## Decision: Accessible destructive actions and feedback

- **Decision**: Use native HTML `<dialog>` with `showModal()` for deletion and both replacement paths. Associate visible title/description text, focus Cancel on entry, allow Escape/cancel without mutation, contain focus, and explicitly restore it. Validation focuses the first invalid field; associated errors and task/status messages are announced and use text/icon meaning rather than color alone. Cross-month edits and empty-state actions have explicit focus destinations.
- **Rationale**: Native dialog semantics provide modality and focus behavior with minimal code, while applying identical rules to both destructive flows removes inconsistent recovery behavior. Explicit feedback rules cover the whole task rather than visual presentation alone.
- **Alternatives considered**: A custom overlay was rejected because it requires reimplementing modality and focus containment; `window.confirm` was rejected because its focus and presentation cannot meet the contract; color-only or unassociated errors were rejected as inaccessible.

## Decision: Deterministic isolated demo mode

- **Decision**: At fresh document initialization, activate demo only when the first case-sensitive `demo` query value is exactly case-sensitive `1`; allow unrelated parameters. Initialize the exact data-model baseline and 2026-10 before any real-storage path. Support add/edit/delete and all view interactions only in demo memory, with no real-storage reads, writes, or storage-event listeners. Mode transitions require navigation/reload/history-driven fresh state, and every fresh demo activation resets the baseline.
- **Rationale**: First-value activation is deterministic, a separate initialization path provides strong isolation, and fresh transitions prevent records or view state from leaking. Fixed records, totals, and ordering make screenshots objectively repeatable.
- **Alternatives considered**: Truthy/case-insensitive or any-duplicate activation was rejected as ambiguous; seeding localStorage or mixing demo records into normal state was rejected because it risks user data; in-place mode switching was rejected because it can leak state; random or current-date-relative data was rejected because it is not deterministic.

## Decision: Verification strategy

- **Decision**: Use the named quickstart case sets and requirement traceability matrix. Run Vitest with jsdom/React Testing Library for domain, persistence, and observable UI behavior; use Playwright reference Chromium for native dialogs, reload/failure behavior, exact demo activation and transitions, storage instrumentation, timing, and responsive checks. Verify demo reads, writes, and listener registrations independently with pre-initialization spies. Combine automated WCAG 2.2 AA checks with manual keyboard and VoiceOver-with-Chromium review; require zero known AA violations. Other browsers remain unverified.
- **Rationale**: Reproducible boundary/failure cases and fixed data make coverage measurable. Real-browser tests cover behavior jsdom cannot prove, especially native modality, reload, storage isolation, and timing. Raw-value equality alone cannot prove that no read occurred, and automated accessibility scanning alone cannot prove keyboard or assistive-technology operation.
- **Alternatives considered**: Browser-only testing was rejected because pure edge-case suites would be slower and less focused; jsdom-only testing was rejected because it cannot verify native dialog or reload behavior; multi-browser acceptance was excluded to keep the stated reference scope honest; critical-only accessibility acceptance was rejected because it conflicts with the AA completion target.

## Resolved technical context

No `NEEDS CLARIFICATION` items remain. The user supplied the language, framework, build tool, storage boundary, test runners, browser target, dialog implementation, demo mechanism, and frontend-only constraint. Existing project files contain specification tooling only, so implementation will establish a new Vite application at the repository root without migrating existing source code.
