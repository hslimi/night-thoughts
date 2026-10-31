# Data Model: Personal Expense Tracker

## Expense

The single durable user record.

| Field | Type | Rules |
|---|---|---|
| `id` | `string` | Nonempty stable unique identity, generated when an expense is added; retained across edits and reloads. |
| `amountCents` | `number` | Positive safe integer representing USD cents, from `1` through `99999999999`; never a floating-point dollar value. |
| `category` | `Category` | Exactly one of `food`, `transport`, `housing`, `entertainment`, `other`. |
| `date` | `LocalDateString` | Valid local calendar date in exact `YYYY-MM-DD` form; past, present, and future dates are valid. |
| `note` | `string` (optional) | Omitted or empty when the submitted note is blank or whitespace-only; otherwise preserved exactly as entered. |

`Category` is a typed constant union shared by validation, calculations, forms, and filters. An `ExpenseDraft` keeps the form's amount as a string until validation succeeds; only a valid draft becomes an `Expense`.

## Validation and conversion rules

- Trim surrounding whitespace from amount input, then accept only `(?:\d+(?:\.\d{1,2})?|\.\d{1,2})`. Thus `1`, `001.2`, `000.50`, and `.50` are valid syntax; `1.`, `1,000`, `$1`, `+1`, `-1`, `1e2`, `NaN`, and `Infinity` are not.
- Reject a syntactically valid amount when its value is zero or exceeds `999999999.99` USD. Reject blank input and every invalid value without creating or changing an expense. Never round excess precision or an out-of-range value into an accepted amount.
- Convert accepted dollars and fractional digits directly to positive integer cents, without binary floating-point input conversion. The maximum persisted value is `99999999999` cents. Add and edit use the same validation function; an invalid edit leaves the original record unchanged.
- Persisted `amountCents` values must already be positive safe integers within the same maximum. A fractional, negative, zero, unsafe, or above-maximum persisted amount invalidates the entire collection.
- Date validation checks the exact string shape and real calendar day, including leap-year February. It does not construct a UTC timestamp. The domain derives `month = date.slice(0, 7)` after validation; lexical date ordering is chronological because the representation is zero-padded.
- Display formatting converts integer cents to USD only at the presentation boundary, always using fixed `en-US` USD formatting independent of browser locale, with grouping and exactly two decimals. Zero renders as `$0.00`; `123456` cents renders as `$1,234.56`.

## Monthly Summary

A derived, non-persisted value for a selected `YYYY-MM` month.

| Field | Type | Derivation |
|---|---|---|
| `month` | `MonthString` | The dashboard's selected local month. |
| `totalCents` | `number` | Exact safe-integer sum of every expense in the selected month, or an aggregate-error result. |
| `categoryTotals` | `Record<Category, number>` | Exact safe-integer sum for each of the five categories, including explicit zero values, or an aggregate-error result for an affected category. |
| `monthExpenses` | `Expense[]` | All expenses in the selected month before list filtering or sorting. |

Adding, editing, deleting, or changing the selected month recomputes this value. Editing a record into another month removes it from the source summary and includes it in the destination summary. Future expenses affect only their own month.

Every addition checks that the result remains a safe integer. If a monthly or category aggregate exceeds that range, reject that aggregate: expose a visible, announced, non-technical calculation error and no apparently valid numeric total for the affected value. Never round, clamp, wrap, or silently approximate it. This error does not alter the underlying expense records.

## Transaction View Preferences

Ephemeral UI state; not persisted and not carried between normal and demo modes.

| Field | Type | Default / behavior |
|---|---|---|
| `selectedMonth` | `MonthString` | Current local month in normal mode; `2026-10` in demo mode. |
| `categoryFilter` | `Category \| 'all'` | `all`; filters only the visible transaction list. |
| `sortField` | `'date' \| 'amount'` | `date`. |
| `sortDirection` | `'asc' \| 'desc'` | `desc`, producing newest date first. |

The visible list is derived from `monthExpenses`, then filtered and sorted. Summaries always use the unfiltered month collection. Amount comparison uses exact `amountCents`; date comparison uses the validated local date string. Primary-value ties use `id` ascending as a deterministic secondary order in both ascending and descending directions. Sorting and filtering never mutate the expense collection.

## Persistence Envelope

Real expenses use one versioned JSON value under the namespaced localStorage key `personal-expense-tracker:expenses:v1`.

| Field | Type | Rules |
|---|---|---|
| `version` | `1` | Any other supported-looking or unknown version is malformed for this release. |
| `expenses` | `Expense[]` | Every entry and unique ID is strictly validated using the same domain invariants. |

The envelope is all-or-nothing: malformed JSON, an invalid envelope, an unsupported version, any invalid record, or duplicate IDs make the complete persisted collection recovery-required. No valid subset is loaded or merged. Missing storage is the only absent-data state that loads as a normal empty collection.

## Persistence and recovery states

| State / failure | Required outcome |
|---|---|
| **Missing** | Enter ready/empty state with no warning. The first ordinary save writes the complete collection without replacement confirmation. |
| **Valid** | Restore the complete collection without derived summaries or preferences. Successful mutations save the complete next collection. |
| **Readable malformed** | Includes malformed JSON/schema, unsupported version, any invalid record, and duplicate IDs. Enter recovery-required state with empty memory and a visible announced warning. Preserve the exact raw value by performing no write until confirmation; never salvage valid-looking records. |
| **Unreadable** | A storage read/access exception enters recovery-required state with empty memory and a visible announced warning. The raw value cannot be inspected, compared, or claimed unchanged; preserve it solely by performing no write until confirmation. |
| **Unsaved changes** | Quota exhaustion, serialization failure, or a mid-session write/access failure retains the complete changed collection only in memory and announces a task-associated warning that the latest work is not durable. Reload restores the last successfully durable collection. |
| **Later save succeeds** | Save the complete current collection, including every retained add/edit/delete, then clear the unsaved-changes warning. A subsequent failure leaves or restores that warning; editing alone does not clear it. |
| **Demo** | Initialize the fixed baseline without real-storage reads, writes, or storage-event listeners. Add, edit, and delete change only demo memory; no recovery or persistence-success status is derived from real data. |

### Replacement protocol

- **Start fresh**: The action opens confirmation without changing memory or storage. The dialog explains that existing saved information will be irreversibly replaced by an empty version-1 envelope. Cancel/Escape performs no write, retains current memory, and leaves the recovery warning. Confirm writes `{ "version": 1, "expenses": [] }`; success enters ready/empty state and clears the recovery warning.
- **First replacement save**: When guarded work is committed, confirmation explains that the complete current in-memory collection will irreversibly replace existing saved information. Cancel/Escape performs no write and retains that work in memory with the warning. Confirm attempts to serialize and write that complete collection; success enters ready state and clears the recovery warning.
- **Failed replacement**: A serialization, quota, access, or other write failure retains current in-memory work, recovery-required state, and a visible write-failure warning. It makes no success claim and performs no automatic retry or destructive fallback.
- All replacement writes occur only after explicit confirmation. Both replacement dialogs use the same accessible naming, safe initial focus, containment, cancellation, and focus-restoration rules as deletion.

## Demo Dataset

The normative baseline is a built-in readonly array with these exact fictional records. Notes are the final text in each row.

| ID | `amountCents` | Amount | Category | Date | Note |
|---|---:|---:|---|---|---|
| `demo-001` | 145000 | $1,450.00 | housing | 2026-10-01 | October rent |
| `demo-002` | 4275 | $42.75 | food | 2026-10-03 | Groceries at Green Market |
| `demo-003` | 1850 | $18.50 | transport | 2026-10-05 | Metro card top-up |
| `demo-004` | 2400 | $24.00 | entertainment | 2026-10-08 | Cinema tickets |
| `demo-005` | 1280 | $12.80 | food | 2026-10-12 | Coffee and pastry |
| `demo-006` | 8500 | $85.00 | other | 2026-10-15 | Household supplies |
| `demo-007` | 6720 | $67.20 | food | 2026-10-18 | Dinner with friends |
| `demo-008` | 3240 | $32.40 | transport | 2026-10-21 | Airport train |
| `demo-009` | 2000 | $20.00 | food | 2026-09-30 | Previous month lunch |
| `demo-010` | 3000 | $30.00 | entertainment | 2026-11-02 | Future concert deposit |

The fixed `selectedMonth` is `2026-10`. Its exact expected monthly total is `173265` cents ($1,732.65), with category totals food `12275` ($122.75), transport `5090` ($50.90), housing `145000` ($1,450.00), entertainment `2400` ($24.00), and other `8500` ($85.00). Records `demo-009` and `demo-010` are excluded from October and appear only in their own months.

Default preferences are all categories, date descending, and ID ascending for ties. The exact initial October ID order is `demo-008`, `demo-007`, `demo-006`, `demo-005`, `demo-004`, `demo-003`, `demo-002`, `demo-001`. Demo adds use the same validation and stable unique-ID rules as normal adds, but every fresh activation discards them and restores this baseline.
