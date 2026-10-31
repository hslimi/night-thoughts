import type {
  CategoryFilter,
  SortDirection,
  TransactionPreferences,
  TransactionSortField,
} from '../domain/dashboard';
import { CATEGORIES, type Expense } from '../domain/expense';
import { formatUSD } from '../domain/money';
import StatusMessage from './StatusMessage';

interface TransactionListProps {
  expenses: Expense[];
  monthExpenseCount: number;
  preferences: TransactionPreferences;
  onPreferencesChange: (preferences: TransactionPreferences) => void;
  onAddFromEmpty: () => void;
  onEdit: (expense: Expense) => void;
  onDelete: (expense: Expense) => void;
}

export default function TransactionList({
  expenses,
  monthExpenseCount,
  preferences,
  onPreferencesChange,
  onAddFromEmpty,
  onEdit,
  onDelete,
}: TransactionListProps) {
  const resultMessage = `${expenses.length} ${expenses.length === 1 ? 'expense' : 'expenses'} shown${preferences.category === 'all' ? '' : ` for ${preferences.category}`}, sorted by ${preferences.sortField} ${preferences.sortDirection === 'asc' ? 'ascending' : 'descending'}.`;

  function clearFilter() {
    onPreferencesChange({ ...preferences, category: 'all' });
    document.getElementById('category-filter')?.focus();
  }

  return (
    <section className="transactions" aria-labelledby="transactions-heading">
      <div className="section-heading section-heading--row">
        <div>
          <p className="eyebrow">Activity</p>
          <h2 id="transactions-heading">Transactions</h2>
        </div>
        <span className="transaction-count">
          {expenses.length} {expenses.length === 1 ? 'item' : 'items'}
        </span>
      </div>
      <div className="transaction-preferences">
        <div className="field">
          <label htmlFor="category-filter">Category filter</label>
          <select
            id="category-filter"
            value={preferences.category}
            onChange={(event) =>
              onPreferencesChange({
                ...preferences,
                category: event.target.value as CategoryFilter,
              })
            }
          >
            <option value="all">All categories</option>
            {CATEGORIES.map((category) => (
              <option key={category} value={category}>{category}</option>
            ))}
          </select>
        </div>
        <div className="field">
          <label htmlFor="transaction-sort-field">Sort by</label>
          <select
            id="transaction-sort-field"
            value={preferences.sortField}
            onChange={(event) =>
              onPreferencesChange({
                ...preferences,
                sortField: event.target.value as TransactionSortField,
              })
            }
          >
            <option value="date">Date</option>
            <option value="amount">Amount</option>
          </select>
        </div>
        <div className="field">
          <label htmlFor="transaction-sort-direction">Sort direction</label>
          <select
            id="transaction-sort-direction"
            value={preferences.sortDirection}
            onChange={(event) =>
              onPreferencesChange({
                ...preferences,
                sortDirection: event.target.value as SortDirection,
              })
            }
          >
            <option value="desc">Descending</option>
            <option value="asc">Ascending</option>
          </select>
        </div>
      </div>
      <StatusMessage
        label="Transaction results"
        message={resultMessage}
      />
      {expenses.length === 0 && monthExpenseCount === 0 && (
        <div className="empty-state" role="status" aria-label="Empty month">
          <p>No expenses for this month. Add an expense to get started.</p>
          <button type="button" onClick={onAddFromEmpty}>
            Add expense for this month
          </button>
        </div>
      )}
      {expenses.length === 0 && monthExpenseCount > 0 && (
        <div className="empty-state" role="status" aria-label="No matching expenses">
          <p>No expenses match the selected category. Clear the filter to see this month&apos;s expenses.</p>
          <button id="clear-filter" type="button" onClick={clearFilter}>
            Clear filter
          </button>
        </div>
      )}
      <ul className="transaction-list" aria-labelledby="transactions-heading">
        {expenses.map((expense) => (
          <li key={expense.id} data-expense-id={expense.id}>
            <article className="transaction">
              <div className="transaction__details">
                <span className={`category-tag category-tag--${expense.category}`}>
                  {expense.category}
                </span>
                <time dateTime={expense.date}>{expense.date}</time>
              </div>
              <strong className="transaction__amount">
                {formatUSD(expense.amountCents)}
              </strong>
              {expense.note && (
                <p className="transaction-note">{expense.note}</p>
              )}
              <div className="transaction__actions">
                <button
                  id={`edit-expense-${expense.id}`}
                  type="button"
                  aria-label="Edit expense"
                  onClick={() => onEdit(expense)}
                >
                  Edit
                </button>
                <button
                  type="button"
                  aria-label="Delete expense"
                  onClick={() => onDelete(expense)}
                >
                  Delete
                </button>
              </div>
            </article>
          </li>
        ))}
      </ul>
    </section>
  );
}
