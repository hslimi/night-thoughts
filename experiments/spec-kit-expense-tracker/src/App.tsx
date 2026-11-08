import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
  type FormEvent,
} from "react";
import {
  calculateMonthlySummary,
  currentLocalMonth,
  isCategory,
  isValidDate,
  normalizeNote,
  parseAmountToCents,
  selectMonthlyExpenses,
} from "./expenses/domain";
import { DEMO_EXPENSES } from "./expenses/demo";
import {
  CATEGORIES,
  type Category,
  type CategoryFilter,
  type Expense,
  type SortDirection,
  type SortField,
} from "./expenses/model";
import { createExpensePersistence } from "./expenses/persistence";

interface ExpenseDraft {
  amount: string;
  category: Category;
  date: string;
  note: string;
}

type FieldErrors = Partial<Record<"amount" | "category" | "date", string>>;
type LoadState = "loading" | "ready" | "error" | "malformed";

function localDateString(date: Date): string {
  const year = String(date.getFullYear()).padStart(4, "0");
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function formatCurrency(amountCents: number): string {
  const formatter = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  const cents = BigInt(amountCents);
  const dollars = cents / 100n;
  const fraction = String(cents % 100n).padStart(2, "0");
  return formatter
    .formatToParts(dollars)
    .map((part) => (part.type === "fraction" ? fraction : part.value))
    .join("");
}

function createExpenseId(): string {
  if (typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

function categoryName(category: Category): string {
  return category.charAt(0).toUpperCase() + category.slice(1);
}

function amountInputValue(amountCents: number): string {
  const dollars = Math.floor(amountCents / 100);
  const cents = String(amountCents % 100).padStart(2, "0");
  return `${dollars}.${cents}`;
}

export default function App() {
  const demoMode = window.location.search === "?demo=1";
  const persistence = useRef<ReturnType<typeof createExpensePersistence> | null>(
    null,
  );
  if (!demoMode && persistence.current === null) {
    persistence.current = createExpensePersistence();
  }

  const [expenses, setExpenses] = useState<Expense[]>(() =>
    demoMode ? DEMO_EXPENSES.map((expense) => ({ ...expense })) : [],
  );
  const [loadState, setLoadState] = useState<LoadState>(
    demoMode ? "ready" : "loading",
  );
  const [notice, setNotice] = useState("");
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [editingId, setEditingId] = useState<string | null>(null);
  const [selectedMonth, setSelectedMonth] = useState(() => currentLocalMonth());
  const [categoryFilter, setCategoryFilter] = useState<CategoryFilter>("all");
  const [sortField, setSortField] = useState<SortField>("date");
  const [sortDirection, setSortDirection] =
    useState<SortDirection>("descending");
  const amountInput = useRef<HTMLInputElement>(null);
  const submitButton = useRef<HTMLButtonElement>(null);
  const deleteDialog = useRef<HTMLDialogElement>(null);
  const cancelDeleteButton = useRef<HTMLButtonElement>(null);
  const confirmDeleteButton = useRef<HTMLButtonElement>(null);
  const deleteInvoker = useRef<HTMLButtonElement | null>(null);
  const editButtons = useRef(new Map<string, HTMLButtonElement>());
  const deleteFocusTarget = useRef<string | null>(null);
  const [focusAfterDelete, setFocusAfterDelete] =
    useState<string | null | undefined>(undefined);
  const [deletingExpense, setDeletingExpense] = useState<Expense | null>(null);
  const [draft, setDraft] = useState<ExpenseDraft>(() => ({
    amount: "",
    category: "food",
    date: localDateString(new Date()),
    note: "",
  }));
  const monthlySummary = calculateMonthlySummary(expenses, selectedMonth);
  const monthlyExpenses = expenses.filter(
    (expense) => expense.date.slice(0, 7) === selectedMonth,
  );
  const visibleExpenses = selectMonthlyExpenses(
    expenses,
    selectedMonth,
    categoryFilter,
    sortField,
    sortDirection,
  );

  const loadExpenses = useCallback(() => {
    if (demoMode) {
      return;
    }

    setLoadState("loading");
    const result = persistence.current?.load();
    if (!result) {
      setLoadState("error");
      setNotice("Could not load expenses. Retry loading to try again.");
      return;
    }
    if (result.kind === "loaded") {
      setExpenses(result.expenses);
      setLoadState("ready");
      setNotice("");
    } else if (result.kind === "malformed") {
      setLoadState("malformed");
      setNotice("");
    } else {
      setLoadState("error");
      setNotice("Could not load expenses. Retry loading to try again.");
    }
  }, [demoMode]);

  useEffect(() => {
    if (!demoMode) {
      loadExpenses();
    }
  }, [demoMode, loadExpenses]);

  useEffect(() => {
    if (deletingExpense && deleteDialog.current && !deleteDialog.current.open) {
      deleteDialog.current.showModal();
      cancelDeleteButton.current?.focus();
    }
  }, [deletingExpense]);

  useLayoutEffect(() => {
    if (focusAfterDelete === undefined) {
      return;
    }

    if (focusAfterDelete !== null) {
      const target = editButtons.current.get(focusAfterDelete);
      if (target) {
        target.focus();
        setFocusAfterDelete(undefined);
        return;
      }
    }
    if (submitButton.current) {
      submitButton.current.focus();
    } else {
      amountInput.current?.focus();
    }
    setFocusAfterDelete(undefined);
  }, [focusAfterDelete, visibleExpenses]);

  function commitExpenses(nextExpenses: Expense[], successMessage: string) {
    setExpenses(nextExpenses);
    if (demoMode) {
      setNotice(`${successMessage} Demo changes reset when you reload.`);
      return;
    }

    const result = persistence.current?.save(nextExpenses);
    if (result?.kind === "saved") {
      setNotice(successMessage);
    } else {
      setNotice(
        "Changes are not saved and may be lost if you reload. Your current work remains on this page.",
      );
    }
  }

  function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const errors: FieldErrors = {};
    const amountCents = parseAmountToCents(draft.amount);
    if (amountCents === null) {
      errors.amount = "Enter an amount from $0.01 to $100,000.00.";
    }
    if (!isCategory(draft.category)) {
      errors.category = "Choose one of the listed categories.";
    }
    if (!isValidDate(draft.date)) {
      errors.date = "Enter a real calendar date.";
    }
    setFieldErrors(errors);
    if (Object.keys(errors).length > 0 || amountCents === null) {
      return;
    }

    const updatedExpense: Expense = {
      id: editingId ?? createExpenseId(),
      amountCents,
      category: draft.category,
      date: draft.date,
      ...(normalizeNote(draft.note) ? { note: normalizeNote(draft.note) } : {}),
    };
    const nextExpenses = editingId
      ? expenses.map((expense) =>
          expense.id === editingId ? updatedExpense : expense,
        )
      : [updatedExpense, ...expenses];
    commitExpenses(
      nextExpenses,
      editingId ? "Expense updated." : "Expense saved.",
    );
    setEditingId(null);
    setDraft({
      amount: "",
      category: "food",
      date: localDateString(new Date()),
      note: "",
    });
  }

  function handleStartEdit(expense: Expense) {
    setEditingId(expense.id);
    setFieldErrors({});
    setNotice("");
    setDraft({
      amount: amountInputValue(expense.amountCents),
      category: expense.category,
      date: expense.date,
      note: expense.note ?? "",
    });
    amountInput.current?.focus();
  }

  function handleCancelEdit() {
    setEditingId(null);
    setFieldErrors({});
    setDraft({
      amount: "",
      category: "food",
      date: localDateString(new Date()),
      note: "",
    });
    amountInput.current?.focus();
  }

  function handleRequestDelete(expense: Expense, invoker: HTMLButtonElement) {
    const index = visibleExpenses.findIndex((visible) => visible.id === expense.id);
    deleteFocusTarget.current =
      visibleExpenses[index + 1]?.id ?? visibleExpenses[index - 1]?.id ?? null;
    deleteInvoker.current = invoker;
    setDeletingExpense(expense);
  }

  function handleCancelDelete() {
    if (deleteDialog.current?.open) {
      deleteDialog.current.close();
    }
    setDeletingExpense(null);
    deleteFocusTarget.current = null;
    const invoker = deleteInvoker.current;
    deleteInvoker.current = null;
    invoker?.focus();
  }

  function handleConfirmDelete() {
    if (!deletingExpense) {
      return;
    }

    const nextExpenses = expenses.filter(
      (expense) => expense.id !== deletingExpense.id,
    );
    const target = deleteFocusTarget.current;
    if (deleteDialog.current?.open) {
      deleteDialog.current.close();
    }
    setDeletingExpense(null);
    deleteInvoker.current = null;
    setEditingId(null);
    setFieldErrors({});
    setDraft({
      amount: "",
      category: "food",
      date: localDateString(new Date()),
      note: "",
    });
    commitExpenses(nextExpenses, "Expense deleted.");
    setFocusAfterDelete(target);
  }

  function handleStartFresh() {
    const confirmed = window.confirm(
      "Starting fresh will replace the malformed saved expense data and clear any current in-memory work. Continue?",
    );
    if (!confirmed) {
      return;
    }

    const result = persistence.current?.startFresh();
    if (result?.kind === "saved") {
      setExpenses([]);
      setLoadState("ready");
      setNotice("Saved data cleared. You can start adding expenses.");
    } else {
      setNotice(
        "Could not start fresh. The original saved data and current work were preserved.",
      );
    }
  }

  if (loadState === "loading") {
    return <main className="app-shell"><p role="status">Loading expenses...</p></main>;
  }

  if (loadState === "error") {
    return (
      <main className="app-shell">
        <h1>Expense Tracker</h1>
        <div className="notice notice-error" role="alert">
          <p>Could not load expenses. Your saved data has not been replaced.</p>
          <button type="button" onClick={loadExpenses}>Retry loading</button>
        </div>
      </main>
    );
  }

  if (loadState === "malformed") {
    return (
      <main className="app-shell">
        <h1>Expense Tracker</h1>
        <div className="notice notice-warning" role="alert">
          <p>
            Saved expense data appears malformed. It is preserved, and saving is
            blocked until you choose to start fresh.
          </p>
          <button type="button" onClick={handleStartFresh}>Start fresh</button>
          {notice && <p role="status">{notice}</p>}
        </div>
      </main>
    );
  }

  return (
    <main className="app-shell">
      <header className="page-header">
        <div>
          <p className="eyebrow">PERSONAL FINANCE</p>
          <h1>Expense Tracker</h1>
          <p className="intro">A clear view of where your money goes.</p>
        </div>
        {demoMode && (
          <p className="demo-badge" role="status">
            Demo mode · fictional data · resets on reload
          </p>
        )}
      </header>

      <section
        className="panel monthly-summary"
        aria-label="Monthly summary"
      >
        <div className="summary-header">
          <div className="monthly-total">
            <p className="eyebrow">MONTHLY TOTAL</p>
            {monthlySummary.totalCents === null ? (
              <p className="aggregate-error" role="alert">
                Monthly total cannot be displayed exactly.
              </p>
            ) : (
              <strong>{formatCurrency(monthlySummary.totalCents)}</strong>
            )}
          </div>
          <div className="month-picker">
            <label htmlFor="month-picker">Month</label>
            <input
              id="month-picker"
              type="month"
              value={selectedMonth}
              onChange={(event) => setSelectedMonth(event.currentTarget.value)}
            />
          </div>
        </div>
        <ul className="category-totals" aria-label="Category totals">
          {CATEGORIES.map((category) => {
            const total = monthlySummary.categoryTotals[category];
            return (
              <li key={category}>
                <span>{categoryName(category)}</span>
                {total === null ? (
                  <strong className="aggregate-error" role="alert">
                    Cannot be displayed exactly
                  </strong>
                ) : (
                  <strong>{formatCurrency(total)}</strong>
                )}
              </li>
            );
          })}
        </ul>
      </section>

      <section className="panel form-panel" aria-labelledby="add-expense-heading">
        <div className="section-heading">
          <div>
            <p className="eyebrow">{editingId ? "UPDATE TRANSACTION" : "NEW TRANSACTION"}</p>
            <h2 id="add-expense-heading">
              {editingId ? "Edit expense" : "Add expense"}
            </h2>
          </div>
        </div>
        <form className="expense-form" onSubmit={handleCreate} noValidate>
          <div className="field">
            <label htmlFor="amount">Amount</label>
            <div className="amount-input">
              <span aria-hidden="true">$</span>
              <input
                autoComplete="off"
                id="amount"
                inputMode="decimal"
                ref={amountInput}
                type="text"
                value={draft.amount}
                aria-invalid={Boolean(fieldErrors.amount)}
                aria-describedby={fieldErrors.amount ? "amount-error" : undefined}
                onChange={(event) => {
                  setDraft({ ...draft, amount: event.currentTarget.value });
                  setFieldErrors({ ...fieldErrors, amount: undefined });
                }}
              />
            </div>
            {fieldErrors.amount && (
              <span className="field-error" id="amount-error" role="alert">
                {fieldErrors.amount}
              </span>
            )}
          </div>

          <div className="field">
            <label htmlFor="category">Category</label>
            <select
              id="category"
              value={draft.category}
              aria-invalid={Boolean(fieldErrors.category)}
              aria-describedby={fieldErrors.category ? "category-error" : undefined}
              onChange={(event) => {
                const category = event.currentTarget.value;
                if (isCategory(category)) {
                  setDraft({ ...draft, category });
                  setFieldErrors({ ...fieldErrors, category: undefined });
                }
              }}
            >
              {CATEGORIES.map((category) => (
                <option key={category} value={category}>
                  {categoryName(category)}
                </option>
              ))}
            </select>
            {fieldErrors.category && (
              <span className="field-error" id="category-error" role="alert">
                {fieldErrors.category}
              </span>
            )}
          </div>

          <div className="field">
            <label htmlFor="date">Date</label>
            <input
              id="date"
              type="date"
              value={draft.date}
              aria-invalid={Boolean(fieldErrors.date)}
              aria-describedby={fieldErrors.date ? "date-error" : undefined}
              onChange={(event) => {
                setDraft({ ...draft, date: event.currentTarget.value });
                setFieldErrors({ ...fieldErrors, date: undefined });
              }}
            />
            {fieldErrors.date && (
              <span className="field-error" id="date-error" role="alert">
                {fieldErrors.date}
              </span>
            )}
          </div>

          <div className="field">
            <label htmlFor="note">Note <span className="optional">(optional)</span></label>
            <input
              id="note"
              type="text"
              value={draft.note}
              onChange={(event) =>
                setDraft({ ...draft, note: event.currentTarget.value })
              }
            />
          </div>

          <div className="form-actions">
            {editingId && (
              <button
                className="text-button"
                type="button"
                onClick={handleCancelEdit}
              >
                Cancel edit
              </button>
            )}
            <button
              className="primary-button submit-button"
              ref={submitButton}
              type="submit"
            >
              {editingId ? "Save changes" : "Add expense"}
            </button>
          </div>
        </form>
      </section>

      {notice && (
        <p className="save-notice" role="status" aria-live="polite">
          {notice}
        </p>
      )}

      <section className="panel transactions-panel" aria-labelledby="expenses-heading">
        <div className="section-heading">
          <div>
            <p className="eyebrow">TRANSACTIONS</p>
            <h2 id="expenses-heading">Your expenses</h2>
          </div>
          <span className="count-pill">{monthlyExpenses.length} this month</span>
        </div>
        <div className="transaction-controls">
          <div className="field">
            <label htmlFor="category-filter">Filter by category</label>
            <select
              id="category-filter"
              value={categoryFilter}
              onChange={(event) => {
                const value = event.currentTarget.value;
                setCategoryFilter(value === "all" || isCategory(value) ? value : "all");
              }}
            >
              <option value="all">All categories</option>
              {CATEGORIES.map((category) => (
                <option key={category} value={category}>
                  {categoryName(category)}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label htmlFor="sort-field">Sort by</label>
            <select
              id="sort-field"
              value={sortField}
              onChange={(event) => {
                const value = event.currentTarget.value;
                if (value === "date" || value === "amount") {
                  setSortField(value);
                }
              }}
            >
              <option value="date">Date</option>
              <option value="amount">Amount</option>
            </select>
          </div>
          <div className="field">
            <label htmlFor="sort-direction">Sort direction</label>
            <select
              id="sort-direction"
              value={sortDirection}
              onChange={(event) => {
                const value = event.currentTarget.value;
                if (value === "ascending" || value === "descending") {
                  setSortDirection(value);
                }
              }}
            >
              <option value="descending">Descending</option>
              <option value="ascending">Ascending</option>
            </select>
          </div>
        </div>
        {monthlyExpenses.length === 0 ? (
          <div className="empty-state">
            <span className="empty-icon" aria-hidden="true">$</span>
            <p>No expenses for this month.</p>
            <button
              className="text-button"
              type="button"
              onClick={() => amountInput.current?.focus()}
            >
              Add an expense
            </button>
          </div>
        ) : visibleExpenses.length === 0 ? (
          <div className="empty-state">
            <span className="empty-icon" aria-hidden="true">⌕</span>
            <p>No expenses match this category.</p>
            <button
              className="text-button"
              type="button"
              onClick={() => setCategoryFilter("all")}
            >
              Clear category filter
            </button>
          </div>
        ) : (
          <ul className="expense-list" aria-label="Expenses">
            {visibleExpenses.map((expense) => (
              <li className="expense-item" key={expense.id}>
                <div className="expense-category-icon" aria-hidden="true">
                  {categoryName(expense.category).slice(0, 1)}
                </div>
                <div className="expense-description">
                  <strong>{expense.note || categoryName(expense.category)}</strong>
                  <span>{categoryName(expense.category)}</span>
                </div>
                <time dateTime={expense.date}>{expense.date}</time>
                <strong className="expense-amount">
                  {formatCurrency(expense.amountCents)}
                </strong>
                <div className="expense-actions">
                  <button
                    className="text-button"
                    type="button"
                    aria-label={`Edit ${expense.note || categoryName(expense.category)}`}
                    ref={(element) => {
                      if (element) {
                        editButtons.current.set(expense.id, element);
                      } else {
                        editButtons.current.delete(expense.id);
                      }
                    }}
                    onClick={() => handleStartEdit(expense)}
                  >
                    Edit
                  </button>
                  <button
                    className="text-button danger-button"
                    type="button"
                    aria-label={`Delete ${expense.note || categoryName(expense.category)}`}
                    onClick={(event) =>
                      handleRequestDelete(expense, event.currentTarget)
                    }
                  >
                    Delete
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <dialog
        className="delete-dialog"
        ref={deleteDialog}
        aria-labelledby="delete-expense-title"
        aria-describedby="delete-expense-description"
        onKeyDown={(event) => {
          if (
            event.key === "Tab" &&
            !event.shiftKey &&
            document.activeElement === confirmDeleteButton.current
          ) {
            event.preventDefault();
            cancelDeleteButton.current?.focus();
          } else if (
            event.key === "Tab" &&
            event.shiftKey &&
            document.activeElement === cancelDeleteButton.current
          ) {
            event.preventDefault();
            confirmDeleteButton.current?.focus();
          }
        }}
        onCancel={(event) => {
          event.preventDefault();
          handleCancelDelete();
        }}
      >
        <div className="dialog-content">
          <p className="eyebrow">CONFIRM DELETION</p>
          <h2 id="delete-expense-title">Delete expense?</h2>
          <p id="delete-expense-description">
            {deletingExpense
              ? `Permanently delete ${deletingExpense.note || categoryName(deletingExpense.category)}? This cannot be undone.`
              : "This action cannot be undone."}
          </p>
          <div className="dialog-actions">
            <button
              className="secondary-button"
              ref={cancelDeleteButton}
              type="button"
              onClick={handleCancelDelete}
            >
              Cancel
            </button>
            <button
              className="danger-action"
              ref={confirmDeleteButton}
              type="button"
              onClick={handleConfirmDelete}
            >
              Delete
            </button>
          </div>
        </div>
      </dialog>
    </main>
  );
}
