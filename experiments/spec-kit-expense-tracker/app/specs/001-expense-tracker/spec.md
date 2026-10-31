# Feature Specification: Personal Expense Tracker

**Feature Branch**: `001-expense-tracker`

**Created**: 2026-10-31

**Status**: Draft

**Input**: User description: "Build a personal expense tracker for a single user. Users can add, edit, and delete expenses. Each expense contains an amount, category, date, and optional note. Categories include food, transport, housing, entertainment, and other. The dashboard shows total spending for the selected month, spending by category, and a list of transactions. Users can filter transactions by category and sort them by date or amount. Reject zero, negative, and invalid amounts. Preserve data after a browser reload and provide a confirmation before deleting a transaction."

## Clarifications

### Session 2026-10-31

- Q: Which currency and display format should monetary values use? → A: USD only, using locale-independent en-US formatting with an explicit dollar symbol and exactly two decimal places.
- Q: How are expense dates and month boundaries interpreted? → A: Dates are local calendar dates in YYYY-MM-DD form; months comprise whole local days, include both first and last days, and use no UTC conversion.
- Q: Are future-dated expenses allowed, and when do they affect totals? → A: They are allowed and included only in their own calendar month.
- Q: What deletion recovery and confirmation behavior is required? → A: Deletion has no undo in this release; confirmation is required, and cancel receives the safe initial focus. A failed durable save leaves the deletion only in memory, so reload restores the last durable record.
- Q: How should malformed or unreadable persisted data be handled? → A: Show a visible non-technical warning, start with an empty in-memory collection, and perform no write until informed replacement confirmation. Readable malformed raw values remain inspectable and unchanged; unreadable raw values cannot be inspected and are preserved solely by not writing.
- Q: How should empty months and empty filter results differ? → A: Use distinct messages and provide a useful next action for each.
- Q: How should deterministic fictional data be provided for screenshots? → A: Provide an explicitly opt-in demo mode with deterministic in-memory data that cannot read, change, or listen to normal persisted data.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Record Expenses and Review Monthly Spending (Priority: P1)

As the sole user, I can record an expense with its amount, category, date, and optional note, then see it reflected in an accurate dashboard for the month I am reviewing.

**Why this priority**: Recording expenses and understanding monthly spending are the core value of the tracker. Without these capabilities, the product has no useful purpose.

**Independent Test**: Add expenses on different dates and in different categories, select each affected month, and verify the transaction list, monthly total, and category totals without relying on editing, deletion, filtering, or sorting.

**Acceptance Scenarios**:

1. **Given** the dashboard has no expenses for the current month, **When** the user adds a valid food expense for 25.50 dated in the current month, **Then** the transaction appears in the list, and the monthly total and food spending are both displayed as $25.50.
2. **Given** expenses exist in two different months, **When** the user selects one of those months, **Then** only that month's transactions appear and the monthly and category totals include only those transactions.
3. **Given** the user is adding or editing an expense, **When** the amount is blank, non-numeric, zero, negative, above 999999999.99, or uses prohibited syntax or excess precision, **Then** the expense is not created or changed, focus moves to the first invalid field, and an associated, announced message identifies the problem without relying on color.
4. **Given** the user submits surrounding whitespace, leading zeros, one or two fractional digits, or `.50`, **When** the resulting value is positive and within the maximum, **Then** the accepted value is converted exactly to integer cents.
5. **Given** the user leaves the optional note blank, **When** all required expense fields are valid and the expense is saved, **Then** the expense is accepted without a note.
6. **Given** a valid expense dated after the current month, **When** the user saves it, **Then** it appears only in its own future month and does not affect the current month's transactions or totals.

---

### User Story 2 - Retain Expenses Across Browser Sessions (Priority: P1)

As the sole user, I can reload the browser and continue reviewing the expenses I previously saved, with clear notice if saved information cannot be read or new changes cannot be retained.

**Why this priority**: An expense tracker that loses financial records after a reload fails a fundamental user expectation and cannot be trusted.

**Independent Test**: Add a representative set of expenses, reload the browser, and compare every transaction and monthly summary with its pre-reload state. Separately simulate unavailable, malformed, and failed persistence to verify visible, non-destructive handling.

**Acceptance Scenarios**:

1. **Given** valid expenses were saved, **When** the browser reloads, **Then** all saved transactions and their monthly summaries are restored without duplication or alteration.
2. **Given** no expenses have ever been saved, **When** the tracker opens, **Then** it presents a defined empty state rather than an error.
3. **Given** a normal add, edit, or delete cannot be saved, **When** the mutation is attempted, **Then** the changed collection remains visible only in memory, an associated announced warning says it is not durable, and reload restores the last durable collection.
4. **Given** an earlier mutation failed and later work succeeds, **When** the later save completes, **Then** the complete current collection, including all still-present unsaved work, is durable and the unsaved-changes warning clears.
5. **Given** readable saved information is malformed, **When** the tracker opens, **Then** it shows a visible non-technical recovery warning, starts with an empty in-memory collection, and leaves the exact raw value unchanged until confirmed replacement.
6. **Given** saved information is unreadable, **When** the tracker opens, **Then** it does not claim to have inspected or compared the raw value, starts empty with a recovery warning, and performs no write before confirmed replacement.
7. **Given** the replacement confirmation is visible, **When** the user cancels, **Then** no write occurs and current in-memory work and the recovery warning remain; **When** replacement fails after confirmation, **Then** the same guarded state and current work remain visible without a durability claim.

---

### User Story 3 - Correct and Safely Remove Transactions (Priority: P2)

As the sole user, I can correct any expense field and permanently remove an expense only after reviewing an explicit confirmation.

**Why this priority**: Real-world records need correction and removal, but accidental deletion must not cause irreversible loss.

**Independent Test**: Edit each field of existing expenses and verify dashboard recalculation. Attempt deletion using both cancellation and confirmation, checking that only confirmation removes the intended transaction and that no undo is offered.

**Acceptance Scenarios**:

1. **Given** an expense exists, **When** the user edits its amount, category, date, or note with valid values and saves, **Then** the transaction and all affected monthly totals reflect the changes.
2. **Given** an expense is being edited, **When** the user supplies an invalid amount, **Then** the changes are not saved, the original expense remains intact, and the first invalid field receives focus.
3. **Given** an expense exists, **When** the user requests deletion, **Then** a confirmation identifies that expense by formatted amount, category, and date, explains that confirmed deletion has no undo once durable, and places initial focus on the cancellation action.
4. **Given** the deletion confirmation is open, **When** the user cancels, **Then** no data changes and focus returns to the requester; **When** the user explicitly confirms, **Then** only the identified expense is removed from memory and its month's dashboard is recalculated.
5. **Given** the confirmed deletion's durable write fails, **When** the warning appears, **Then** the deletion remains visible only in memory and a reload restores that expense from the last durable collection.
6. **Given** an expense is edited without changing its month, **When** its edit requester remains visible, **Then** focus returns to that requester; **When** an active category filter hides the edited expense, **Then** the result is announced and focus moves to the category filter.
7. **Given** an expense is deleted, **When** focus is restored, **Then** it moves to the next visible transaction edit requester in the current filtered and sorted list, else the previous visible edit requester, else Clear filter when a category filter is active, else Add expense.

---

### User Story 4 - Focus and Order the Transaction List (Priority: P3)

As the sole user, I can show only one category and order the selected month's transactions by date or amount so I can find and compare expenses.

**Why this priority**: Filtering and sorting make a growing transaction history easier to analyze, but the tracker already delivers basic value without them.

**Independent Test**: With a multi-category, multi-date set of expenses in one month, apply each category filter and each date and amount ordering, then verify list membership and order independently of add, edit, and delete flows.

**Acceptance Scenarios**:

1. **Given** the selected month contains expenses in several categories, **When** the user filters by food, **Then** only food expenses from that month appear in the transaction list while the monthly and category summaries remain based on all expenses for the month.
2. **Given** the selected month contains expenses with different dates and amounts, **When** the user sorts by date or exact cent amount and chooses a direction, **Then** the visible transactions appear in the requested order and every primary-value tie uses ID ascending in both directions.
3. **Given** a category filter matches no transactions in the selected month, **When** the filter is applied, **Then** the list shows a no-matches message and an action to clear the filter without changing any expense or summary.
4. **Given** the selected month has no expenses, **When** no category filter is hiding transactions, **Then** the dashboard shows a no-expenses-for-this-month message and an action to add an expense, distinct from the no-matches filter state.

---

### User Story 5 - Capture Fictional Demo Evidence (Priority: P3)

As a person preparing product screenshots, I can explicitly open a deterministic fictional demo so I can capture populated views without exposing or changing real saved expenses.

**Why this priority**: Repeatable demo evidence is useful for review, but it must never put real records at risk or change the normal product experience.

**Independent Test**: Save a known real expense, open the normal tracker and the explicitly activated demo separately, compare repeated demo sessions, and verify with storage instrumentation that demo initialization and interactions perform no reads, writes, or storage-event listener registration.

**Acceptance Scenarios**:

1. **Given** the first `demo` query value is absent or is anything other than case-sensitive `1`, **When** the tracker opens, **Then** it shows only normal data and behavior; unrelated query parameters do not prevent otherwise valid activation.
2. **Given** demo mode is active, **When** the tracker is opened more than once, **Then** each initial view contains the fixed baseline, selected month 2026-10, expected totals, and newest-first ordering, and is visibly labeled as fictional demo data.
3. **Given** real expenses are populated, missing, malformed, or unreadable, **When** the user initializes demo mode or adds, edits, deletes, filters, sorts, or selects months, **Then** demo uses only its own memory and performs no real-storage read, write, or storage-event listener registration.
4. **Given** a normal or demo session has changed work and view state, **When** the user navigates, reloads, or uses browser history to enter the other mode, **Then** fresh state for the destination mode is initialized without carrying records, preferences, forms, dialogs, or status messages across modes.

### Edge Cases

- Expenses dated on the first or last day of a local calendar month belong to that month; expenses on adjacent days do not leak into its totals, and no UTC conversion changes their date or month.
- Month selection handles different month lengths and leap-year February correctly.
- A future-dated expense affects only its own month, regardless of how far ahead it is dated.
- A month with no expenses and a filter with no matches produce distinct empty states with a useful next action, rather than misleading totals or an error.
- Editing an expense into a different month removes it from the current month's calculations and includes it in the destination month.
- Transactions tied on date or exact cent amount use ID ascending in both sort directions.
- Monetary calculations use exact integer cents. An aggregate that cannot be represented as a safe integer produces a visible announced error instead of a rounded, clamped, or apparently valid total.
- A note containing only whitespace is treated as an empty optional note; other notes are preserved as entered.
- Any invalid record or duplicate identity invalidates the entire persisted collection; valid records are not salvaged from that collection.
- Missing storage starts empty; readable malformed storage and unreadable storage both start with empty guarded memory and a warning, but only readable malformed storage can be checked for byte-for-byte raw preservation.
- Quota exhaustion, serialization failure, and storage becoming unavailable during a session are visible write failures with the same in-memory retention and reload rules as other failed saves.
- Demo mode never falls back to, reads, writes, or listens to real saved data, including when no real data exists, that data is malformed, or normal and demo tabs are open concurrently.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Users MUST be able to add an expense by supplying an amount, category, and date, with an optional note.
- **FR-002**: Each expense MUST use exactly one of these categories: food, transport, housing, entertainment, or other.
- **FR-003**: After trimming surrounding whitespace, amount input MUST contain either digits with an optional decimal point followed by one or two digits, or a decimal point followed by one or two digits. Leading zeros and `.50` are valid syntax. Blank, zero, negative, trailing-decimal, grouping, currency-symbol, explicit-plus, exponent, non-finite, excess-precision, and above-999999999.99 values MUST be rejected without creating or modifying an expense. Add and edit MUST focus the first invalid field and expose each error through its control association, assistive-technology announcement, and text/icon meaning rather than color alone.
- **FR-004**: Expense dates MUST use the YYYY-MM-DD local calendar-date form and represent whole local days without UTC conversion; missing or impossible dates MUST be rejected, while valid past, present, and future dates are allowed.
- **FR-005**: Users MUST be able to add a valid expense with no note, and notes consisting only of whitespace MUST be treated as empty.
- **FR-006**: Amount validation rules MUST apply identically when adding and editing expenses.
- **FR-007**: Users MUST be able to edit an existing expense's amount, category, date, and note, with invalid edits leaving the original expense unchanged.
- **FR-008**: Users MUST be able to request deletion of an expense, and the system MUST NOT delete it until the user explicitly confirms.
- **FR-009**: Deletion confirmation MUST identify the affected expense by formatted amount, category, and date, state that confirmed deletion has no undo once durable, and place initial focus on the safe cancellation action rather than the destructive action.
- **FR-010**: Cancelling deletion MUST leave all data unchanged; confirming deletion MUST remove only the identified expense from memory, with no undo after durable deletion. If the write fails, the removal is only in memory and reload MUST restore the last durable collection, including that expense.
- **FR-011**: The dashboard MUST allow selection of a local calendar month and MUST default to the current local calendar month when normal mode opens.
- **FR-012**: For the selected month, the dashboard MUST show total spending, spending for each of the five categories, and the matching transactions.
- **FR-013**: Monthly and category totals MUST include every saved expense whose local calendar date falls within the selected month, including its first and last whole days and future-dated expenses in their own month, and exclude expenses from every other month.
- **FR-014**: Amounts MUST be persisted and calculated as exact integer cents, with no silent rounding at input, persistence, calculation, or display. An individual amount MUST NOT exceed 999999999.99 USD. If a monthly or category sum exceeds the exactly representable integer-cent range, the affected total MUST be rejected and shown as a visible, announced, non-technical calculation error rather than rounded or presented as valid. Every rendered transaction, monthly/category total, deletion confirmation, and demo monetary value MUST use locale-independent en-US USD formatting with exactly two decimals, including `$0.00` and `$1,234.56`.
- **FR-015**: Adding, editing, or deleting an expense MUST update every affected monthly total, category total, and transaction-list result so the update is visible within 2 seconds in the reference Chromium browser; month selection, filtering, and sorting MUST meet the same limit.
- **FR-016**: Users MUST be able to filter the selected month's transaction list by any one category or view all categories.
- **FR-017**: Category filtering MUST affect only the transaction list; monthly and category summaries MUST continue to represent all expenses in the selected month.
- **FR-018**: Users MUST be able to sort the visible transaction list by date or exact integer-cent amount in either ascending or descending order; the default MUST be newest date first, and every primary-value tie MUST use ID ascending regardless of direction.
- **FR-019**: Sorting or filtering MUST NOT alter any saved expense or the values used in monthly summaries.
- **FR-020**: Every saved expense MUST be preserved across a browser reload without loss, duplication, or alteration.
- **FR-021**: Missing saved data MUST produce a normal empty state. A readable value with malformed JSON, an invalid envelope or record, an unsupported version, or duplicate identity MUST produce recovery-required state with a visible non-technical warning and an empty in-memory collection, rejecting the collection all-or-nothing. A storage read/access exception MUST produce unreadable recovery-required state with the same empty collection and no claim that its raw value was inspected.
- **FR-022**: Recovery-required state MUST perform no write until explicit informed confirmation. Start fresh MUST propose replacing saved information with an empty collection; the first replacement save MUST propose replacing it with the complete current in-memory collection. Both dialogs MUST explain irreversible replacement, use the same focus, containment, cancellation, and restoration rules as deletion, and perform no write on cancellation. Cancellation retains current memory and the recovery warning. Confirmed success enters ready state and clears that warning; failed replacement retains current memory and recovery-required state with a visible write failure.
- **FR-023**: Quota exhaustion, serialization failure, storage access failure, and storage becoming unavailable mid-session MUST be visible write failures. A failed normal add, edit, or delete MUST keep the complete changed collection visible only in memory and announce an unsaved-changes warning associated with the attempted task without color-only meaning. Reload MUST restore the last durable collection. A later successful mutation MUST save the complete current collection, including all retained work, and clear the unsaved-changes warning only after durable success.
- **FR-024**: A selected month with no expenses MUST show a distinct empty-month message with an action to add an expense; a filter with no matches MUST show a distinct no-matches message with an action to clear the filter; neither state MUST be presented as an error. Activating either action MUST place focus at the first meaningful control of the resulting task or refreshed list.
- **FR-025**: The complete core-flow inventory in the UI contract MUST be keyboard operable and satisfy WCAG 2.2 Level AA, including applicable criteria for keyboard access, structure, labels/instructions, error identification/suggestion, status messages, contrast, use of color, focus order/visibility/obscuring, dialog semantics, 200% text resize, 320-CSS-pixel reflow, and minimum 24-by-24-CSS-pixel pointer targets. Validation MUST focus the first invalid field; errors and persistence/calculation feedback MUST be associated with the relevant control or task, announced, and meaningful without color. Completion requires zero known WCAG 2.2 AA violations.
- **FR-026**: Deletion and replacement confirmations MUST have accessible names/descriptions, safe Cancel initial focus, keyboard containment while open, Escape/Cancel behavior without mutation, and explicit focus restoration to the requester on cancellation. After a same-month edit, focus MUST return to that expense's edit requester if it remains visible; if an active category filter hides it, the result MUST be announced and focus MUST move to the category filter. After deletion, focus MUST move to the next visible transaction edit requester in the current filtered and sorted order, else the previous visible edit requester, else Clear filter when a category filter is active, else Add expense.
- **FR-027**: Demo activation MUST compare the first URL query value named case-sensitive `demo` with case-sensitive exact value `1`; unrelated parameters are allowed. Duplicate `demo` parameters use only the first value. All other names or values select normal mode. Mode changes MUST require navigation or reload with fresh destination state, including browser-history transitions; records and view state MUST NOT transfer between modes.
- **FR-028**: Demo mode MUST initialize the exact records, integer-cent values, selected month 2026-10, expected totals, and default ordering fixed in the data-model demo baseline, independently of the current date. It MUST visibly identify the data as fictional and reproduce that initial dashboard on every activation.
- **FR-029**: Demo mode MUST support add as well as edit, delete, validation, month selection, calculations, filtering, and sorting against only its separate in-memory collection. Throughout initialization, mutations, recovery paths, and status handling, it MUST NOT read, write, clear, or replace real storage and MUST NOT register storage-event listeners, even with normal tabs open. Demo changes MUST NOT create real-data recovery warnings or persistence success claims and MUST reset on fresh activation.

### Key Entities

- **Expense**: One spending record belonging to the single user, with a positive USD amount of at most 999999999.99 persisted as integer cents, one category, a local calendar date in YYYY-MM-DD form, and an optional note. Each expense has a stable identity so editing and deletion affect only the intended record.
- **Monthly Summary**: A derived view for one selected local calendar month, containing exactly calculated total spending and spending by category or a visible error for an unsafe aggregate. It is recalculated from expenses and is not an independently editable record.
- **Transaction View Preferences**: The selected category filter, sort field, and sort direction used to shape the visible transaction list without changing expenses or monthly summaries.
- **Demo Dataset**: The exact fixed fictional baseline and selected month 2026-10 in the data model, used only in explicitly activated demo mode and reset on each fresh activation.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: At least 90% of first-time users can successfully add a valid expense and locate it in the monthly transaction list within 30 seconds.
- **SC-002**: All cases in the quickstart CORE, DATE, MONEY, and OVERFLOW sets produce their exact expected integer-cent and formatted results, including month/leap/future boundaries, category combinations, `$0.00`, `$1,234.56`, and visible rejection of unsafe aggregates.
- **SC-003**: Every case in the quickstart AMOUNT set is accepted or rejected as specified in both add and edit, with first-invalid-field focus, associated announced errors, and no change to records or summaries on rejection.
- **SC-004**: Every record and summary in the deterministic 1,000-record SCALE set matches after reload, and every measured add/edit/delete, month-selection, filter, and sort update is visible within 2 seconds in reference Chromium.
- **SC-005**: Every deletion case in the quickstart DELETE set preserves data before confirmation, initially focuses Cancel, contains focus, cancels without mutation, removes exactly the identified record on confirmation, restores focus using the specified next-visible/previous-visible/Clear filter/Add expense order, and restores that record after a failed-write reload without offering undo.
- **SC-006**: Every FILTER and SORT case produces the specified membership and ordering, including ID-ascending amount and date ties in both directions, without changing summaries.
- **SC-007**: Every enumerated core flow passes the quickstart manual keyboard and assistive-technology review and automated WCAG 2.2 AA checks at required zoom, reflow, and target sizes, with zero known WCAG 2.2 AA violations at completion.
- **SC-008**: Every PERSIST and RECOVERY case produces the specified visible status, all-or-nothing load, no-write-before-confirmation behavior, in-memory retention, later full-collection save, warning lifecycle, failed-replacement behavior, and post-failure reload result. Readable malformed raw values remain byte-for-byte unchanged before confirmed replacement; unreadable cases instead assert no attempted write.
- **SC-009**: Every EMPTY case shows the correct distinct message and action, and the add or clear action moves focus as specified.
- **SC-010**: Every DEMO case reproduces the exact baseline and activation rules, resets view state across navigation/reload/history, and proves zero real-storage reads, writes, and storage-event listener registrations with populated, missing, malformed, and unreadable real-data preconditions; normal mode contains no demo content.

## Assumptions

- The initial release serves one user in one browser profile on one device, with no sign-in, profiles, sharing, or cross-device synchronization.
- Concurrent normal-tab synchronization and conflict resolution are excluded. Normal tabs are not required to reconcile each other's changes; demo isolation from any open normal tab remains mandatory.
- All expenses and summaries use USD with fixed en-US formatting independent of browser locale; multi-currency support and exchange-rate conversion are outside the initial scope.
- Expenses are stored locally and remain available after an ordinary reload or browser restart when the same browser profile and saved data remain available. Clearing browser data or using a different browser or device is not expected to preserve them.
- Dates are local calendar dates, not timestamps; month assignment never depends on UTC conversion.
- The selected month initially defaults to the current local month in normal mode; dashboard controls are not required to survive a reload, but expense data is.
- Category filtering applies to the transaction list only, not to the monthly totals shown on the dashboard.
- Both sort directions are available for date and amount, with newest-first date ordering and ID-ascending tie-breaking as the default.
- Deletion has no undo, trash, or recovery after durable success. A failed deletion save is not durable and reload restores the last durable record.
- The fictional demo dataset is review evidence, not user data, and is excluded from normal dashboards and persistence.
- Reference acceptance uses Playwright Chromium only. Other browsers, including Firefox and WebKit/Safari, remain unverified and are neither acceptance targets nor claimed supported browsers for this release.
- No recurring expenses, budgets, income tracking, attachments, import/export, or remote backup are included in the initial scope.
