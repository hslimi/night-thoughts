# Architecture Review: Final Module Boundaries

The implementation preserves the constitution's separation of UI, pure business rules, and persistence.

```text
src/
├── domain/
│   ├── expense.ts       # Expense types and shared record/draft validation
│   ├── money.ts         # Decimal-string parsing into checked integer cents
│   ├── dates.ts         # Local YYYY-MM-DD and YYYY-MM calendar rules
│   └── dashboard.ts     # Exact totals, filtering, and deterministic sorting
├── persistence/
│   └── expenseStorage.ts # Sole real localStorage boundary and schema results
├── state/
│   └── useExpenseStore.ts # React state, guarded recovery, and demo memory
├── demo/
│   └── demoData.ts       # Fixed fictional records and exact demo activation
├── components/
│   ├── ExpenseForm.tsx   # Add/edit forms and field-level errors
│   ├── Dashboard.tsx     # Month and category summaries/status
│   ├── TransactionList.tsx # Filter/sort controls and transaction actions
│   ├── ConfirmDialog.tsx # Native modal focus behavior
│   └── StatusMessage.tsx # Announced text/icon feedback
├── App.tsx               # Interaction coordination and focus restoration
├── main.tsx              # Normal/demo entry selection
└── styles.css            # Responsive layout, focus, contrast, and targets
```

## Boundary checks

- Domain modules import no React components or browser storage.
- `expenseStorage.ts` is the only application module that accesses real localStorage.
- Demo initialization branches before storage loading and uses only fixed in-memory records.
- Monthly/category summaries are derived from the complete selected-month collection; filtering changes only the visible list.
- Tests mirror these boundaries: domain, persistence, React UI, and eight Playwright suites.

The month-clear guard at `useExpenseStore.ts:103` rejects invalid month values before they can reach summary calculation. `ExpenseForm.tsx:46` initializes edit drafts in `useLayoutEffect` to prevent stale values from overwriting fast user input.
