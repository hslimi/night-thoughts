# Feature Specification: Expense Tracker

**Feature Branch**: `Not created`

**Created**: 2026-11-03

**Status**: Draft

**Input**: User description: "Build a personal expense tracker for a single user. Users can add, edit, and delete expenses. Each expense contains an amount, category, date, and optional note. Categories include food, transport, housing, entertainment, and other. The dashboard shows total spending for the selected month, spending by category, and a list of transactions. Users can filter transactions by category and sort them by date or amount. Reject zero, negative, and invalid amounts. Preserve data after a browser reload and provide a confirmation before deleting a transaction. Keep this a small frontend-only demonstration."

## Clarifications

### Session 2026-11-03

- Q: Which currency and display format should expenses use? → A: USD, fixed en-US formatting with exactly two decimal places.
- Q: How should the selected month include expenses? → A: Use inclusive local calendar months without shifting dates.
- Q: How should future-dated expenses be handled? → A: Allow them only in the month matching their local calendar date.
- Q: What should deletion confirmation do? → A: Deletion is permanent with no undo, and initial focus goes to Cancel.
- Q: How should malformed persisted data be handled? → A: Show a visible warning, preserve the saved data, and never overwrite it automatically.
- Q: How should empty months differ from empty filter results? → A: Show distinct messages with useful next actions.
- Q: How should screenshot demo data work? → A: Make deterministic fictional data explicitly opt-in; demo changes must not affect saved user data and must reset on reload.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Record expenses (Priority: P1)

A person records an expense with its amount, category, and date, adding a note when useful. Their entries remain available when they return to the demonstration after a browser reload.

**Why this priority**: Recording and retaining expenses is the foundation of the tracker.

**Independent Test**: Add a valid expense, reload the page, and verify that the same expense and its details remain available.

**Acceptance Scenarios**:

1. **Given** the expense form is available, **When** the user submits a positive amount, an allowed category, a valid date, and an optional note, **Then** the expense appears in the transaction list.
2. **Given** an expense has been saved, **When** the user reloads the page, **Then** the expense and all its details are still available.
3. **Given** the user enters a zero, negative, nonnumeric, or more-than-two-decimal amount, **When** they attempt to save the expense, **Then** the expense is rejected and the user is told how to correct the amount.

### User Story 2 - Review monthly spending (Priority: P2)

A person selects a month and reviews its total spending, spending by category, and transactions. They can narrow the transaction list by category and order it by date or amount.

**Why this priority**: The monthly overview turns individual records into useful spending information.

**Independent Test**: Use a set of expenses across different months and categories to verify monthly totals, category totals, filtering, and both sort choices.

**Acceptance Scenarios**:

1. **Given** expenses exist in multiple months, **When** the user selects a month, **Then** the dashboard shows only that month's total, category breakdown, and transactions.
2. **Given** the selected month has expenses in multiple categories, **When** the user chooses a category filter, **Then** only matching transactions are shown; choosing All shows every transaction for that month.
3. **Given** the transaction list is shown, **When** the user sorts by date or amount and chooses a direction, **Then** transactions appear in that order, with equal sort values retaining their relative order.
4. **Given** the selected month has no expenses, **When** the dashboard is shown, **Then** it displays a zero total, a month-empty message, and an action to add an expense.
5. **Given** the selected month has expenses but the selected category has no matches, **When** the dashboard is shown, **Then** it displays a filter-empty message and an action to clear or change the filter.
6. **Given** an expense has a future date, **When** the user views the dashboard, **Then** that expense appears only when its local calendar month is selected.

### User Story 3 - Correct or remove expenses (Priority: P3)

A person corrects an existing expense or removes one they no longer want included. The dashboard reflects the change, and a deletion takes place only after confirmation.

**Why this priority**: Corrections and confirmed removal keep recorded spending accurate without risking accidental deletion.

**Independent Test**: Edit an expense and verify the updated values and summaries; then attempt deletion, cancel it, and confirm separately that a confirmed deletion removes the expense.

**Acceptance Scenarios**:

1. **Given** an existing expense, **When** the user saves valid edits, **Then** the transaction and affected monthly and category totals reflect the edited values.
2. **Given** an existing expense, **When** the user requests deletion, **Then** a confirmation is presented before any data is permanently removed, with initial focus on Cancel and no undo after confirmation.
3. **Given** deletion confirmation is open, **When** the user cancels, **Then** the expense and all related totals remain unchanged.
4. **Given** deletion confirmation is open, **When** the user confirms, **Then** the expense is removed and the affected summaries update; focus moves to the next visible transaction's Edit control, otherwise the previous visible transaction's Edit control, otherwise Add expense.

### Edge Cases

- The selected month has no expenses, or the chosen category has no matching transactions.
- An edited expense changes category or moves to a different month; both affected summaries must remain accurate.
- An amount is blank, malformed, zero, negative, or has more than two fractional digits.
- An expense exceeds USD 100,000.00, or a displayed aggregate cannot be represented exactly.
- A date or category is missing or invalid.
- Two or more transactions have the same value for the selected sort field.
- Browser data cannot be saved or retrieved; the user must be told that persistence failed rather than seeing a false success.
- A failed save leaves current changes unsaved and at risk of loss on reload; reloading restores the last saved collection, and a later successful save includes all current changes.
- Saved data is malformed; it is preserved, a visible warning is shown, and it is not automatically overwritten.
- Starting fresh from malformed data requires informed confirmation; failure preserves both saved data and current work.
- A future-dated expense is shown only in the month matching its local calendar date.
- A note is omitted or consists only of whitespace; it remains optional.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The demonstration MUST allow one person to create an expense with an amount, one of the categories Food, Transport, Housing, Entertainment, or Other, a date, and an optional note.
- **FR-002**: The amount input MUST accept base-10 digits with an optional decimal point followed by one or two digits (for example, `1`, `1.2`, or `1.20`); it MUST reject signs, grouping separators, currency symbols, exponent notation, surrounding whitespace, and other forms. The parsed amount MUST be positive and no greater than USD 100,000.00 per expense. The demonstration MUST explain rejected values and display accepted amounts as USD using fixed en-US formatting with exactly two decimal places.
- **FR-003**: The demonstration MUST allow a person to edit an existing expense's amount, category, date, and note, applying the same validation as for a new expense.
- **FR-004**: The demonstration MUST ask for confirmation before permanently deleting an expense. The confirmation MUST initially focus Cancel; cancelling MUST leave the expense and summaries unchanged and restore focus to the invoking control. Confirmed deletion MUST have no undo and MUST focus the next visible transaction's Edit control, otherwise the previous visible transaction's Edit control, otherwise Add expense.
- **FR-005**: Successfully saved expenses and their edits or deletions MUST remain reflected after the browser is reloaded. Failed-save behavior is specified in FR-012.
- **FR-006**: The dashboard MUST allow a person to select a calendar month and show that month's total spending, spending for each of the five categories, and transaction list. Month boundaries MUST use inclusive local calendar dates without shifting expenses into adjacent dates or months.
- **FR-007**: The selected month MUST default to the current calendar month.
- **FR-008**: The transaction list MUST be filterable by any one category or by All categories.
- **FR-009**: The transaction list MUST be sortable by date or amount, in ascending or descending order. The default order MUST be newest date first; choosing amount MUST default to largest first.
- **FR-010**: The monthly total and category totals MUST include each valid expense exactly once according to its date and category, and MUST update after a successful add, edit, or deletion. If a total cannot be represented exactly, the demonstration MUST announce an error in place of that total and MUST NOT round or display a misleading value.
- **FR-011**: An empty month MUST show a zero total, a distinct message, and an action to add an expense. A category filter with no results MUST show a different message and an action to clear or change the filter. Category totals for categories without expenses MUST be shown as zero.
- **FR-012**: The demonstration MUST communicate failed data saving or retrieval clearly and MUST NOT present an unsuccessful save as successful. On a load failure, it MUST announce the error and provide a retry-loading action without treating an empty fallback as saved data. On a save failure, it MUST identify current changes as unsaved and at risk of loss on reload, preserve previously saved data, and retain current changes until reload; after a later successful save, reloading MUST restore the full current collection, including prior unsaved changes. If saved data is malformed, it MUST show a visible warning, preserve that data, and prevent normal changes from overwriting it until the person confirms an informed start-fresh action. That action MUST explain that the malformed saved data and current unsaved changes will be replaced by an empty collection. On success, the saved collection MUST be empty. On failure, saved data and current changes MUST remain unchanged and the warning MUST remain visible.
- **FR-013**: All primary tasks MUST be keyboard-operable. Interactive controls MUST have semantic roles and accessible names; field validation, persistence outcomes, and unsafe-total errors MUST be understandable and available to people using assistive technology. The deletion confirmation MUST have an accessible title, contain keyboard focus while open, close without mutation on Escape or Cancel, and follow FR-004 focus restoration rules.
- **FR-014**: Future-dated expenses MUST be allowed and included only in the month matching their local calendar date.
- **FR-015**: The demonstration MUST offer deterministic fictional demo-data mode only when the person explicitly opts in. It MUST reset to the same fixed fictional collection on reload, and demo-mode additions, edits, and deletions MUST NOT change the person's saved expense collection. Normal mode MUST remain the default.

### Key Entities

- **Expense**: A single person's spending record, including a positive USD amount, one allowed category, a local calendar date, and an optional note.
- **Selected month**: The inclusive local calendar month used to scope the dashboard total, category breakdown, and transaction list; expenses MUST NOT shift into adjacent dates or months.
- **Transaction view**: The selected month's expenses as displayed after applying the chosen category filter and sort order.
- **Demo-data mode**: An explicitly opted-in, deterministic fictional dataset that does not change saved user expenses and resets on reload.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In a browser check, create a valid expense with an amount, category, date, and note; verify that every entered detail is displayed correctly in the transaction list and remains after reload.
- **SC-002**: Validation tests accept `1`, `1.2`, `1.20`, USD 0.01, and USD 100,000.00; reject blank, zero, negative, whitespace-padded, signed, comma-separated, currency-prefixed, exponent, nonnumeric, over-precision, and USD 100,000.01 inputs.
- **SC-003**: For every tested month, monthly and category totals exactly match the sum of valid expenses. If a total cannot be represented exactly, an announced error is shown instead of a rounded or misleading value.
- **SC-004**: In every reload test, the most recently saved collection is restored: successful edits remain, unsaved changes are absent, and confirmed deletions remain absent.
- **SC-005**: In every filter and sort test, the visible transactions match the selected month, category, sort field, and direction.
- **SC-006**: In every tested deletion scenario, initial focus is on Cancel; Escape and Cancel preserve the expense and restore focus to the invoking control. Confirming permanently removes it with no undo and focuses the next visible transaction's Edit control, otherwise the previous one's, otherwise Add expense.
- **SC-007**: Empty-month and empty-filter tests show distinct messages and their respective add-expense or clear/change-filter actions.
- **SC-008**: Malformed-data checks verify the warning, unchanged saved data, and blocked normal changes before informed confirmation. The confirmation states that success replaces malformed saved data and clears current unsaved changes. Starting fresh leaves the saved collection empty; a simulated failure leaves saved data and current changes unchanged and the warning visible.
- **SC-009**: Only explicit opt-in activates demo mode. Repeated reloads show the same fictional data; add, edit, and delete work without changing saved user expenses; without opt-in, normal mode is used.
- **SC-010**: Automated accessibility checks find semantic roles and accessible names for every primary control; keyboard-only tests complete add, edit, filtering/sorting, delete-cancel, and delete-confirm flows; validation, persistence, and unsafe-aggregate outcomes are exposed through accessible descriptions or live announcements.
- **SC-011**: Boundary checks accept the inclusive per-expense maximum and reject the next cent; aggregation checks verify exact totals when representable and an announced error when they are not.
- **SC-012**: Simulated read failures show an announced error and retry-loading action without claiming data was loaded. Simulated write failures show unsaved-work guidance and leave saved data unchanged; reload restores saved data, while the next successful save includes the entire current collection.

## Assumptions

- The demonstration serves one person in one browser; accounts, sharing, synchronization across devices, and currency conversion are outside scope.
- All entries use USD, fixed en-US formatting with exactly two decimal places.
- The dashboard initially selects the current calendar month, shows all categories, and orders transactions newest first. Amount sorting initially orders largest first.
- Calendar month selection and expense dates use local calendar dates; future-dated expenses are allowed only in the month matching their date.
- A note may be left blank. A missing or invalid required date or category prevents saving.
