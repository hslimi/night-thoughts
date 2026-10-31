# Requirement Interview

## Initial prompt

> Build a personal expense tracker for a single user. Users can add, edit, and delete expenses. Each expense contains an amount, category, date, and optional note. Categories include food, transport, housing, entertainment, and other. The dashboard shows total spending for the selected month, spending by category, and a list of transactions. Users can filter transactions by category and sort them by date or amount. Reject zero, negative, and invalid amounts. Preserve data after a browser reload and provide a confirmation before deleting a transaction.

The prompt records desired behavior but leaves currency, date boundaries, future expenses, deletion recovery, damaged storage, empty states, and evidence data unresolved.

## Clarification session

These decisions were supplied during clarification and integrated into `app/specs/001-expense-tracker/spec.md`.

| Question | Accepted answer |
| --- | --- |
| Which currency and display format? | USD only, `en-US`, explicit `$`, exactly two decimals. |
| How are dates and month boundaries interpreted? | Local `YYYY-MM-DD` calendar dates; inclusive whole-day months; no UTC conversion. |
| Are future expenses allowed? | Yes, only in their own future month. |
| What does deletion mean? | Permanent, no undo; confirmation required; Cancel gets initial focus. |
| What happens when stored data is malformed? | Warn visibly, preserve the raw value, start empty in memory, and require confirmation before replacement. |
| How do empty states differ? | Empty month offers Add expense; empty filter offers Clear filter. |
| How are screenshots made reproducible? | Explicit `?demo=1`, fixed fictional in-memory data, and no reads or writes of real storage. |

## Result

The clarification stage added or refined acceptance scenarios, FR-004, FR-009 through FR-014, FR-021 through FR-029, and SC-002 through SC-010. The complete behavior contract is the generated specification, not a substitute document.
