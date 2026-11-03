# User Interface Contract

This application exposes a single responsive dashboard; there is no backend API.

## Dashboard

- Default to the current local calendar month.
- Show monthly total, all five category totals, month selection, category filter, sort field/direction, and transactions for the selected month.
- Use en-US USD formatting with exactly two decimal places.
- Accept positive amounts through USD 100,000.00 per expense; reject any greater amount. When a monthly or category aggregate exceeds 9,007,199,254,740,991 cents or cannot be represented exactly, show an announced error instead of a rounded total.
- Month filtering compares local `YYYY-MM` calendar portions; it does not convert dates through UTC.
- Show a distinct zero-total empty-month state with an Add expense action, and a distinct no-filter-results state with a clear/change-filter action.
- On narrow screens, keep all actions, summaries, transactions, error messages, and dialogs usable without page-level horizontal overflow.
- Give every interactive control a semantic role and accessible name. Validation, persistence, and unsafe-aggregate errors must be associated with the relevant control or announced to assistive technology.
- Make all primary tasks keyboard-operable. Keep focus contained in a modal dialog; Escape and Cancel close it without mutation.

## Create and edit

- Provide labeled amount, category, date, and optional note controls.
- Accept only positive amounts up to and including USD 100,000.00 in digits with an optional decimal point and one or two fractional digits (for example, `1`, `1.2`, or `1.20`); reject signs, grouping separators, currency symbols, exponent notation, surrounding whitespace, and other forms. Also require one of the five defined categories and a real `YYYY-MM-DD` date.
- Show validation errors next to the relevant field and make them available to assistive technology; invalid submissions do not mutate saved or in-memory data.
- Clear surrounding whitespace from notes and treat a blank note as omitted.
- Future dates are valid and appear only in their local calendar month.

## Delete confirmation

- Open a native modal `<dialog>` before permanent deletion.
- Give the dialog a visible accessible title and explicit Cancel and Delete actions.
- Focus Cancel when opened. Keyboard focus remains contained while the modal is open.
- Escape and Cancel close without changing data and restore focus to the invoking control.
- Confirm permanently deletes with no undo. After deletion, focus the next visible transaction's Edit control in the current sorted/filtered order; if none exists, focus the previous visible transaction's Edit control; if neither exists, focus Add expense.

## Persistence status

- Announce load errors and provide a Retry loading action; do not treat an empty fallback as durable. Announce failed writes as unsaved, retain current work in memory only, and tell the user it may be lost on reload. Reload restores the last durable collection; the next successful save writes the complete current in-memory collection.
- For malformed persisted data, show a warning, retain the raw storage value, and block normal persistence until an informed start-fresh confirmation.
- Explain in the confirmation that starting fresh replaces the malformed saved value and clears current in-memory work. On success, write an empty version-1 envelope with an empty `expenses` array. On failure, preserve the original raw value and current work and keep the warning visible.

## Demo mode

- Only the exact query string `?demo=1` enables the deterministic fictional dataset and visible demo-mode indicator; additional query parameters do not.
- Demo mode supports the same add, edit, and delete interactions in memory, and reload restores the same fixed fictional data. Demo mode never reads or writes normal user expenses in localStorage and never registers a storage-event listener.
- Any query string other than the exact `?demo=1` uses normal persisted user data and behavior.
