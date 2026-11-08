# Data Model: Expense Tracker

## Expense

A user's spending record.

| Field | Type | Rules |
|---|---|---|
| `id` | string | Unique and stable for the record. |
| `amountCents` | number | Positive safe integer no greater than 10,000,000 cents (USD 100,000.00); represents exact USD cents. |
| `category` | `food \| transport \| housing \| entertainment \| other` | Exactly one allowed category. |
| `date` | string | A real local calendar date in `YYYY-MM-DD` form; not a timestamp. |
| `note` | string, optional | Trim surrounding whitespace; omit when empty. |

Amounts are entered as base-10 digits with an optional decimal point followed by one or two digits; reject signs, grouping separators, currency symbols, exponent notation, and surrounding whitespace. Validate before conversion to cents and format only for display. A derived aggregate is displayable only when its integer-cent sum is exactly representable and no greater than 9,007,199,254,740,991 cents; otherwise show an announced error instead of rounding or displaying a total. Amount, category, date, and note may be edited with the same validation as creation.

## Expense collection and persistence

- Normal-mode state is an ordered collection of `Expense` records.
- Persist the collection in a versioned JSON envelope at one application-owned localStorage key. The version-1 shape is `{ "version": 1, "expenses": [...] }`.
- Validate the JSON shape and every record before accepting the collection.
- A load failure is announced and offers retry; it is not treated as an empty durable collection. Malformed JSON or invalid records retain the original raw string, show a warning, and block persistence until the user confirms an informed start-fresh action.
- A failed normal-mode write leaves the last durable value unchanged and retains current work in memory only. Reload restores the last durable collection. On the next successful write, persist the complete current in-memory collection, including prior unsaved work.
- Start fresh confirms that malformed saved data and current in-memory work will be replaced by an empty collection. Success writes a version-1 envelope with an empty `expenses` array; failure preserves the original raw value and current work and keeps the warning visible.

## Dashboard view state

| Value | Type | Rules |
|---|---|---|
| `selectedMonth` | string (`YYYY-MM`) | Defaults to the current local calendar month. |
| `categoryFilter` | category or `all` | Applies only to the transaction list. |
| `sortField` | `date \| amount` | Determines the transaction sort key. |
| `sortDirection` | `ascending \| descending` | Date initially sorts newest first; amount initially sorts largest first. |

Monthly totals and each category total are derived from all expenses whose local date falls in the selected month, independently of the transaction category filter. Category breakdown always includes all five categories, using zero where there are no expenses. Filtered and sorted transactions are derived from that month’s expenses; equal sort keys preserve source order.

The empty-month state (zero total, add action, month-specific message) is distinct from a non-empty month whose active category filter has no matches (filter-specific message and clear/change-filter action).

## Demo-data mode

- Activated only when the query string is exactly `?demo=1`; additional or alternate query strings use normal mode.
- Starts from a deterministic collection of fictional `Expense` records.
- Uses in-memory state only; it never reads, writes, or listens for changes to the normal persisted collection.
- Repeated page loads recreate the same initial records. Demo-mode status is visible to the user.

## State transitions

- **Create/edit**: validate draft → create/update record → persist the full current collection in normal mode → on success, mark durable; on failure, retain the work in memory and announce that it is unsaved. In demo mode, update only in-memory state.
- **Delete**: request → native confirmation → cancel without change, or confirm → remove and persist in normal mode → on success update durable state; on failure retain current work in memory and report it as unsaved. After confirmed deletion, focus the next visible Edit control, else the previous visible Edit control, else Add expense. Demo-mode deletion affects only in-memory state.
- **Malformed persistence**: load raw value → show warning and block persistence → informed start-fresh confirmation → write an empty version-1 envelope → on success initialize an empty normal collection. If the write fails, preserve the blocked state, raw value, and current work and report the failure.
