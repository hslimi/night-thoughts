export const CATEGORIES = [
  'food',
  'transport',
  'housing',
  'entertainment',
  'other',
] as const;

export type Category = (typeof CATEGORIES)[number];

export interface Expense {
  id: string;
  amountCents: number;
  category: Category;
  date: string;
  note?: string;
}

export interface ExpenseDraft {
  amount: string;
  category: string;
  date: string;
  note: string;
}

export interface Version1Envelope {
  version: 1;
  expenses: Expense[];
}

export interface ExpectedMonthlySummary {
  month: string;
  totalCents: number;
  categoryTotals: Record<Category, number>;
  monthExpenses: Expense[];
}

export function buildValidExpense(
  overrides: Partial<Expense> = {},
): Expense {
  return {
    id: 'expense-001',
    amountCents: 2550,
    category: 'food',
    date: '2026-10-15',
    note: 'Fixture expense',
    ...overrides,
  };
}

export function buildExpenseDraft(
  overrides: Partial<ExpenseDraft> = {},
): ExpenseDraft {
  return {
    amount: '25.50',
    category: 'food',
    date: '2026-10-15',
    note: 'Fixture expense',
    ...overrides,
  };
}

export function buildVersion1Envelope(
  expenses: Expense[] = [buildValidExpense()],
): Version1Envelope {
  return {
    version: 1,
    expenses: expenses.map((expense) => ({ ...expense })),
  };
}

export function buildFixedLocalClock(
  year = 2026,
  month = 10,
  day = 31,
): Date {
  return new Date(year, month - 1, day, 12, 0, 0, 0);
}

function addExactCents(total: number, amountCents: number): number {
  const next = total + amountCents;
  if (!Number.isSafeInteger(next)) {
    throw new RangeError('Fixture summary exceeds safe integer cents');
  }
  return next;
}

export function buildExpectedMonthlySummary(
  expenses: Expense[],
  month: string,
): ExpectedMonthlySummary {
  const monthExpenses = expenses.filter((expense) =>
    expense.date.startsWith(`${month}-`),
  );
  const categoryTotals: Record<Category, number> = {
    food: 0,
    transport: 0,
    housing: 0,
    entertainment: 0,
    other: 0,
  };
  let totalCents = 0;

  for (const expense of monthExpenses) {
    totalCents = addExactCents(totalCents, expense.amountCents);
    categoryTotals[expense.category] = addExactCents(
      categoryTotals[expense.category],
      expense.amountCents,
    );
  }

  return { month, totalCents, categoryTotals, monthExpenses };
}
