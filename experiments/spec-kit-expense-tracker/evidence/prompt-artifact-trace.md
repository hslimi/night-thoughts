# Prompt → Artifact Trace

Genuine prompt and generated-artifact excerpts from this experiment. This is an editor-based trace, not a chat-UI capture.

## 1. Actual implementation prompt

> Build a personal expense tracker for a single user.
>
> Users can add, edit, and delete expenses. Each expense contains an amount, category, date, and optional note. Categories include food, transport, housing, entertainment, and other.
>
> The dashboard shows total spending for the selected month, spending by category, and a list of transactions. Users can filter transactions by category and sort them by date or amount.
>
> Reject zero, negative, and invalid amounts. Preserve data after a browser reload and provide a confirmation before deleting a transaction.

## 2. Generated specification response

The generated specification created four initial user stories:

1. Record Expenses and Review Monthly Spending — P1
2. Retain Expenses Across Browser Sessions — P1
3. Correct and Safely Remove Transactions — P2
4. Focus and Order the Transaction List — P3

Its first acceptance scenario required a valid food expense of 25.50 to appear in the transaction list, monthly total, and food total. Other scenarios required invalid amounts to leave the dashboard unchanged and deletion to remain pending until explicit confirmation.

## 3. Actual clarification exchange

**Question:** Which currency and display format should monetary values use?

**Accepted answer:** USD only, using en-US formatting with an explicit dollar symbol and exactly two decimal places.

**Question:** How should malformed persisted data be handled?

**Accepted answer:** Show a visible non-technical warning, preserve the original raw value, do not overwrite it automatically, and start with an empty in-memory collection. Any replacement requires confirmation.

**Question:** How should deterministic fictional data be provided for screenshots?

**Accepted answer:** Provide an explicitly opt-in demo mode with deterministic in-memory data that cannot change normal application behavior or persisted user data.

## 4. Resulting requirements

- **FR-014:** Amounts are persisted and calculated as exact integer cents, with no silent rounding. Every transaction, summary, confirmation, and demo value uses fixed en-US USD formatting with exactly two decimals.
- **FR-022:** Recovery-required state performs no write until explicit informed confirmation. Cancellation retains current memory and the recovery warning.
- **FR-028:** Demo mode initializes exact fixed records, integer-cent values, selected month 2026-10, expected totals, and default ordering.
- **FR-029:** Demo interactions never read, write, clear, or replace real storage and never register storage-event listeners.

The complete generated documents are `app/specs/001-expense-tracker/spec.md`, `plan.md`, `tasks.md`, and the analysis reports in `evidence/`.
