import { CATEGORIES, type Category, type Expense, type MonthString } from './expense';
import { isMonth, monthForDate } from './dates';

export type CentsResult =
  | { ok: true; cents: number }
  | { ok: false; error: 'unsafe-total' };

export interface MonthlySummary {
  month: MonthString;
  total: CentsResult;
  categoryTotals: Record<Category, CentsResult>;
  monthExpenses: Expense[];
}

export type CategoryFilter = Category | 'all';
export type TransactionSortField = 'date' | 'amount';
export type SortDirection = 'asc' | 'desc';

export interface TransactionPreferences {
  category: CategoryFilter;
  sortField: TransactionSortField;
  sortDirection: SortDirection;
}

export function filterAndSortExpenses(
  expenses: Expense[],
  preferences: TransactionPreferences,
): Expense[] {
  const direction = preferences.sortDirection === 'asc' ? 1 : -1;
  return expenses
    .filter(
      (expense) =>
        preferences.category === 'all' || expense.category === preferences.category,
    )
    .sort((first, second) => {
      const primaryOrder =
        preferences.sortField === 'date'
          ? first.date.localeCompare(second.date)
          : first.amountCents - second.amountCents;
      return primaryOrder * direction || first.id.localeCompare(second.id);
    });
}

function addCents(total: number, amountCents: number): CentsResult {
  const next = total + amountCents;
  return Number.isSafeInteger(next)
    ? { ok: true, cents: next }
    : { ok: false, error: 'unsafe-total' };
}

export function summarizeMonth(
  expenses: Expense[],
  month: MonthString,
): MonthlySummary {
  if (!isMonth(month)) {
    throw new Error('Expected a valid local month');
  }
  const monthExpenses = expenses.filter(
    (expense) => monthForDate(expense.date) === month,
  );
  const categoryTotals = Object.fromEntries(
    CATEGORIES.map((category) => [category, { ok: true, cents: 0 }]),
  ) as Record<Category, CentsResult>;
  let total = 0;
  let totalOverflow = false;

  for (const expense of monthExpenses) {
    if (!totalOverflow) {
      const nextTotal = addCents(total, expense.amountCents);
      if (nextTotal.ok) {
        total = nextTotal.cents;
      } else {
        totalOverflow = true;
      }
    }

    const categoryTotal = categoryTotals[expense.category];
    if (categoryTotal.ok) {
      categoryTotals[expense.category] = addCents(
        categoryTotal.cents,
        expense.amountCents,
      );
    }
  }

  return {
    month,
    total: totalOverflow
      ? { ok: false, error: 'unsafe-total' }
      : { ok: true, cents: total },
    categoryTotals,
    monthExpenses,
  };
}
