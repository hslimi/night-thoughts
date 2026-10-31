import {
  filterAndSortExpenses,
  type CentsResult,
  type MonthlySummary,
  type TransactionPreferences,
} from '../domain/dashboard';
import type { MonthString } from '../domain/dates';
import { CATEGORIES, type Category } from '../domain/expense';
import { formatUSD } from '../domain/money';
import type {
  PersistenceIssue,
  RecoveryKind,
} from '../state/useExpenseStore';
import StatusMessage from './StatusMessage';
import TransactionList from './TransactionList';

interface DashboardProps {
  selectedMonth: MonthString;
  onMonthChange: (month: MonthString) => void;
  summary: MonthlySummary;
  visibleExpenses?: MonthlySummary['monthExpenses'];
  transactionPreferences?: TransactionPreferences;
  onTransactionPreferencesChange?: (preferences: TransactionPreferences) => void;
  onAddFromEmpty?: () => void;
  persistenceStatus?: {
    recovery: RecoveryKind | null;
    issue: PersistenceIssue;
  } | null;
  onStartFresh?: () => void;
  onEdit?: (expense: MonthlySummary['monthExpenses'][number]) => void;
  onDelete?: (expense: MonthlySummary['monthExpenses'][number]) => void;
}

const defaultTransactionPreferences: TransactionPreferences = {
  category: 'all',
  sortField: 'date',
  sortDirection: 'desc',
};

function displayCents(result: CentsResult): string {
  return result.ok ? formatUSD(result.cents) : 'Unavailable';
}

function categoryLabel(category: Category): string {
  return `${category[0]!.toUpperCase()}${category.slice(1)}`;
}

function persistenceMessage(status: NonNullable<DashboardProps['persistenceStatus']>) {
  if (status.issue === 'unsaved-add') {
    return 'Add expense: the latest work is not durably saved. Your current changes remain only in memory.';
  }
  if (status.issue === 'unsaved-edit') {
    return 'Edit expense: the latest work is not durably saved. Your current changes remain only in memory.';
  }
  if (status.issue === 'unsaved-delete') {
    return 'Delete expense: the latest work is not durably saved. Your current changes remain only in memory.';
  }
  if (status.issue === 'replacement-failed') {
    return 'Replacement failed; current work is not durably saved. Saved information still cannot currently be used, the visible collection is temporary, and replacement requires confirmation.';
  }
  if (status.recovery === 'unreadable') {
    return 'Saved information cannot currently be used because browser storage is unreadable. The visible collection is temporary. Replacing saved information requires confirmation.';
  }
  return 'Saved information cannot currently be used because its contents are invalid. The visible collection is temporary. Replacing saved information requires confirmation.';
}

export default function Dashboard({
  selectedMonth,
  onMonthChange,
  summary,
  visibleExpenses: providedVisibleExpenses,
  transactionPreferences = defaultTransactionPreferences,
  onTransactionPreferencesChange = () => {},
  onAddFromEmpty = () => document.getElementById('expense-amount')?.focus(),
  persistenceStatus = null,
  onStartFresh,
  onEdit = () => {},
  onDelete = () => {},
}: DashboardProps) {
  const hasCalculationError =
    !summary.total.ok ||
    Object.values(summary.categoryTotals).some((result) => !result.ok);
  const visibleExpenses =
    providedVisibleExpenses ??
    filterAndSortExpenses(summary.monthExpenses, transactionPreferences);

  return (
    <div className="dashboard">
      {persistenceStatus && (
        <section className="panel persistence-panel" aria-label="Persistence">
          <StatusMessage
            tone="warning"
            label="Persistence status"
            message={persistenceMessage(persistenceStatus)}
          />
          {persistenceStatus.recovery !== null && onStartFresh && (
            <button type="button" onClick={onStartFresh}>
              Start fresh
            </button>
          )}
        </section>
      )}
      <section className="panel summary-panel" aria-labelledby="monthly-summary-heading">
        <div className="dashboard-topline">
          <div className="section-heading">
            <p className="eyebrow">Monthly overview</p>
            <h2 id="monthly-summary-heading">Spending summary</h2>
          </div>
          <div className="field month-field">
            <label htmlFor="selected-month">Month</label>
            <input
              id="selected-month"
              name="month"
              type="month"
              value={selectedMonth}
              onChange={(event) => onMonthChange(event.target.value)}
            />
          </div>
        </div>

        <div className="monthly-total">
          <span>Total spending</span>
          <output aria-label="Monthly total">{displayCents(summary.total)}</output>
        </div>

        <ul className="category-totals" aria-label="Category totals">
          {CATEGORIES.map((category) => (
            <li key={category}>
              <span>{categoryLabel(category)}</span>
              <output aria-label={`${categoryLabel(category)} total`}>
                {displayCents(summary.categoryTotals[category])}
              </output>
            </li>
          ))}
        </ul>

        {hasCalculationError && (
          <StatusMessage
            tone="error"
            message="Some totals cannot be calculated exactly. Your expenses are unchanged."
          />
        )}
      </section>

      <section className="panel transactions-panel">
        <TransactionList
          expenses={visibleExpenses}
          monthExpenseCount={summary.monthExpenses.length}
          preferences={transactionPreferences}
          onPreferencesChange={onTransactionPreferencesChange}
          onAddFromEmpty={onAddFromEmpty}
          onEdit={onEdit}
          onDelete={onDelete}
        />
      </section>
    </div>
  );
}
