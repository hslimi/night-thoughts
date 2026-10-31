# UI Contract: Personal Expense Tracker

This frontend-only application exposes a browser UI and one explicit demo URL switch. It exposes no HTTP API, backend endpoint, authentication flow, or remote data contract.

## Entry points and mode transitions

| URL query | Contract |
|---|---|
| First case-sensitive `demo` query value is exactly case-sensitive `1` | Demo mode. Unrelated parameters are allowed. |
| Missing `demo`, any other first value, or only differently cased names such as `Demo` | Normal mode. |

Only the first `demo` value controls activation: `?demo=1&demo=0` activates demo, while `?demo=0&demo=1` does not. Examples of valid demo URLs include `/?demo=1` and `/?source=review&demo=1`; `/?demo=01`, `/?demo=true`, and `/?Demo=1` are normal mode. URL parsing supplies query values, and the first parsed value must equal the literal string `1`.

Normal mode loads only real persisted expenses and initially selects the current local month. Demo mode initializes the exact data-model baseline and 2026-10, shows a persistent fictional-demo label, and never accesses real storage. There is no in-place mode switch. Entering another mode requires navigation or reload with fresh application state. Address-bar navigation, reload, and back/forward history entry activation initialize the destination mode without carrying records, selected month, filter, sort, forms, dialogs, or status messages from the other mode. Fresh demo activation resets the baseline; fresh normal activation reloads durable data and default preferences.

## Core-flow inventory

“All core flows” means every flow below, not only add/edit/delete:

1. Normal initialization with valid, missing, readable malformed, and unreadable saved data.
2. Month selection, including adjacent-month and leap-year boundaries.
3. Valid and invalid add, including add from the empty-month action.
4. Valid and invalid edit, including edits that move a record into or out of the selected month and a same-month category edit that leaves the active filter.
5. Deletion request, Cancel/Escape, confirmation, deterministic next/previous/Clear filter/Add expense focus restoration, deletion of the last visible filtered result, and failed durable deletion.
6. Category selection, all-categories selection, no-match empty state, and clear-filter action.
7. Date and amount sorting in both directions, including deterministic ties.
8. Failed add/edit/delete saves, retained work, later successful full-collection save, warning clearance, and post-failure reload.
9. Start-fresh and first-replacement-save confirmation, cancellation, success, and failed replacement.
10. Exact demo activation, demo add/edit/delete/month/filter/sort interactions, fresh reset, and navigation/reload/history transitions between modes.

Every flow is included in keyboard, focus, feedback, responsive, and WCAG 2.2 AA acceptance review.

## Dashboard contract

- A labeled month control selects any local `YYYY-MM` month. Normal mode initially selects the current local month; demo initially selects 2026-10.
- The monthly summary displays total USD spending and all five category totals for the entire selected month, including zero-valued categories. Filtering does not change these totals.
- An unsafe monthly or category aggregate displays an associated, announced, non-technical calculation error instead of a rounded or apparently valid numeric total. Underlying records remain unchanged.
- The transaction list shows only the selected month, optionally narrowed to one category. Controls provide exact-cent amount and date sorting in both directions; primary-value ties always use ID ascending. Initial order is newest date first.
- An empty month shows a non-error message and an add-expense action. Activating it opens/focuses the add task with focus on the amount input. A nonempty month with no filter matches shows a different message and a clear-filter action; clearing restores the unfiltered list, announces the result, and places focus on the category-filter control.
- Desktop and mobile layouts preserve the same content, control labels, validation, and operation results.

## Add and edit contract

Inputs are amount, category, local date, and optional note. Both operations share validation.

- After surrounding whitespace is trimmed, accepted amount syntax is digits with an optional one/two-digit fraction or a leading decimal point with one/two digits. Leading zeros and `.50` are accepted. Zero, negatives, trailing decimal points, grouping, currency symbols, plus signs, exponent notation, non-finite values, excess precision, and values above 999999999.99 are rejected without rounding.
- Invalid submission creates or changes nothing. Focus moves to the first invalid field in form order. Each message is programmatically associated with its field and announced to assistive technology; text and/or iconography communicates the error, never color alone. Already valid nonblank note input is preserved.
- Valid add creates one stable-ID expense and recalculates affected summaries and list results without automatically changing the selected month. The update is visible within 2 seconds in reference Chromium.
- Valid edit updates every field of the same expense. Moving its date to another month removes it from the current view and calculations. Because the edit requester may disappear, a cross-month edit closes the edit task, announces that the record moved, and places focus on the selected-month control. After a same-month edit, focus returns to the same expense's edit requester if it remains visible, including when sorting changes its position. If an active category filter hides the edited expense, the resulting list membership is announced and focus moves to the category-filter control.
- Blank and whitespace-only notes are accepted as absent. Other notes are preserved as entered.
- Rendered transactions, monthly/category totals, deletion confirmations, and demo values use fixed en-US USD formatting independent of browser locale, including `$0.00` and `$1,234.56`.

## Deletion dialog contract

Requesting deletion opens a native modal dialog before any deletion occurs.

- The dialog identifies the expense by formatted amount, category, and local date and states that confirmed deletion has no undo once durable.
- The dialog has an accessible name and description. Cancel receives initial focus, keyboard focus remains inside while open, and Escape/Cancel closes without mutation and restores focus to the requester.
- Confirm removes only the identified expense from memory and recalculates the dashboard within 2 seconds. Focus moves to the next visible transaction edit requester in the current filtered and sorted order after deletion; if none exists, it moves to the previous visible edit requester; if no visible requester remains, it moves to Clear filter when a category filter is active, otherwise to Add expense. No undo is offered after durable deletion.
- If the write fails, the removal stays visible only in memory with the unsaved-changes warning; reload restores the deleted record from the last durable collection.

## Persistence status and replacement contract

- Missing data opens a normal empty dashboard. Valid data is restored after reload without duplication or alteration. Any malformed record or duplicate ID rejects the entire collection; no valid subset is shown.
- Readable malformed data opens an empty guarded dashboard with a visible, announced, non-technical recovery warning and leaves the exact raw value unwritten. Unreadable data opens the same guarded state, but messaging must not claim that its raw value was inspected or compared; no write occurs before confirmation in either state.
- Recovery-warning text explains that saved information cannot currently be used, the visible collection is temporary, and replacement requires confirmation. It remains visible while recovery is required and clears only after confirmed successful replacement.
- Start fresh proposes an empty replacement collection. A first save of guarded work proposes the complete current in-memory collection. Both open a native modal dialog explaining that existing saved information will be irreversibly replaced and cannot be recovered afterward.
- Replacement dialogs have the same focus rules as deletion: accessible name/description, Cancel initial focus, containment, Escape/Cancel without mutation or write, and restoration to the requester. Cancellation retains current in-memory work and the recovery warning.
- Confirmed replacement success clears the recovery warning. Failed replacement retains current memory, recovery-required state, and a visible announced write-failure warning without a durability claim or automatic retry.
- A failed normal add, edit, or delete keeps the complete changed collection visible only in memory. Its warning identifies the latest work as not durably saved, is associated with the attempted task, is announced, and does not rely on color. Reload restores the last durable collection: a failed add disappears, a failed edit reverts, and a failed delete reappears.
- A later successful mutation saves all current work and clears the unsaved-changes warning only after durable success. Quota exhaustion, serialization failure, and mid-session storage failure follow this same contract.
- Concurrent normal-tab synchronization is excluded. This exclusion does not permit demo reads, writes, or storage listeners.

## Demo interaction contract

Demo mode supports the same add, edit, delete, validation, month selection, calculations, filtering, sorting, empty states, and dialogs against its own in-memory collection. The exact initial records, 2026-10 totals, and newest-first IDs are defined in [data-model.md](../data-model.md#demo-dataset). Fresh activation discards demo changes and restores that baseline.

Demo initialization and every interaction must perform zero real-storage reads, zero writes/clears/removals, and zero storage-event listener registrations, including `addEventListener('storage', ...)` and `onstorage` assignment. This applies with populated, missing, malformed, or unreadable real data and while normal tabs are open. Demo never triggers real-data recovery handling, persistence warnings, or persistence success claims.

## Accessibility and feedback contract

All core flows target and complete with zero known WCAG 2.2 Level AA violations. Requirements map to the following applicable success criteria, without excluding other applicable AA criteria:

- **Keyboard and semantics**: 1.3.1, 2.1.1, 2.1.2, and 4.1.2 for structure, operability, no keyboard trap, and control/dialog names, roles, states, and properties.
- **Forms and errors**: 1.3.5, 3.3.1, 3.3.2, and 3.3.3 for identified purpose where applicable, labels/instructions, error identification, and correction suggestions. Errors are associated with controls and announced; failed submission focuses the first invalid field.
- **Status and meaning**: 1.4.1 and 4.1.3 for non-color meaning and programmatically determinable status/warning messages. Validation, persistence, recovery, calculation, empty-state, and demo feedback use text and/or iconography as well as any color.
- **Visual presentation**: 1.4.3 and 1.4.11 for text and non-text contrast; 1.4.4 for 200% text resizing without loss of content or function.
- **Zoom and reflow**: At 200% browser zoom and at a 320-CSS-pixel-wide viewport, content and every core flow remain available without two-dimensional scrolling or overlap, satisfying 1.4.10. Required feedback is not hidden at desktop or mobile widths.
- **Focus**: 2.4.3, 2.4.7, and 2.4.11 for logical order, visible focus, and focus not obscured. Both dialog types contain focus, start on Cancel, and restore focus; validation, same-month and cross-month edits, the deterministic post-deletion fallback order, and empty-state actions follow their explicit focus rules above.
- **Targets**: Every pointer target at desktop and mobile widths has a minimum size of 24 by 24 CSS pixels, meeting 2.5.8 without relying on a smaller-target spacing exception.

Completion uses manual keyboard and assistive-technology review plus automated accessibility checks over forms, errors, warnings, both dialogs, empty states, transaction results, and responsive layouts. Reference acceptance is Chromium only; all other browsers remain unverified.
