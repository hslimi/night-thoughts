import {
  CATEGORIES,
  type Category,
  type CategoryFilter,
  type Expense,
  type SortDirection,
  type SortField,
} from "./model";

const MAX_EXPENSE_CENTS = 10_000_000;
const MAX_SAFE_CENTS = BigInt(Number.MAX_SAFE_INTEGER);

export interface MonthlySummary {
  totalCents: number | null;
  categoryTotals: Record<Category, number | null>;
}

export function parseAmountToCents(input: string): number | null {
  const match = /^(\d+)(?:\.(\d{1,2}))?$/.exec(input);
  if (!match) {
    return null;
  }

  const wholePart = match[1].replace(/^0+/, "") || "0";
  if (wholePart.length > 6) {
    return null;
  }

  const amountCents =
    Number(wholePart) * 100 + Number((match[2] ?? "").padEnd(2, "0"));
  if (amountCents <= 0 || amountCents > MAX_EXPENSE_CENTS) {
    return null;
  }

  return amountCents;
}

export function isCategory(value: unknown): value is Category {
  return typeof value === "string" && CATEGORIES.some((category) => category === value);
}

export function isValidDate(value: string): boolean {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  if (!match) {
    return false;
  }

  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  if (year < 1 || month < 1 || month > 12 || day < 1) {
    return false;
  }

  const leapYear = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
  const daysInMonth = [
    31,
    leapYear ? 29 : 28,
    31,
    30,
    31,
    30,
    31,
    31,
    30,
    31,
    30,
    31,
  ];
  return day <= daysInMonth[month - 1];
}

export function normalizeNote(value?: string): string | undefined {
  const note = value?.trim();
  return note ? note : undefined;
}

export function isExpense(value: unknown): value is Expense {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    return false;
  }

  const record = value as Record<string, unknown>;
  const amountCents = record.amountCents;
  return (
    typeof record.id === "string" &&
    record.id.length > 0 &&
    typeof amountCents === "number" &&
    Number.isSafeInteger(amountCents) &&
    amountCents > 0 &&
    amountCents <= MAX_EXPENSE_CENTS &&
    isCategory(record.category) &&
    typeof record.date === "string" &&
    isValidDate(record.date) &&
    (record.note === undefined ||
      (typeof record.note === "string" &&
        record.note.length > 0 &&
        record.note === record.note.trim()))
  );
}

export function currentLocalMonth(date = new Date()): string {
  const year = String(date.getFullYear()).padStart(4, "0");
  const month = String(date.getMonth() + 1).padStart(2, "0");
  return `${year}-${month}`;
}

function sumSafeCents(expenses: Expense[]): number | null {
  let total = 0n;
  for (const expense of expenses) {
    if (!Number.isSafeInteger(expense.amountCents) || expense.amountCents < 0) {
      return null;
    }
    total += BigInt(expense.amountCents);
    if (total > MAX_SAFE_CENTS) {
      return null;
    }
  }
  return Number(total);
}

export function calculateMonthlySummary(
  expenses: Expense[],
  month: string,
): MonthlySummary {
  const monthlyExpenses = expenses.filter((expense) => expense.date.slice(0, 7) === month);
  const categoryTotals = Object.fromEntries(
    CATEGORIES.map((category) => [
      category,
      sumSafeCents(monthlyExpenses.filter((expense) => expense.category === category)),
    ]),
  ) as Record<Category, number | null>;

  return {
    totalCents: sumSafeCents(monthlyExpenses),
    categoryTotals,
  };
}

export function selectMonthlyExpenses(
  expenses: Expense[],
  month: string,
  categoryFilter: CategoryFilter,
  sortField: SortField,
  sortDirection: SortDirection,
): Expense[] {
  return expenses
    .map((expense, index) => ({ expense, index }))
    .filter(
      ({ expense }) =>
        expense.date.slice(0, 7) === month &&
        (categoryFilter === "all" || expense.category === categoryFilter),
    )
    .sort((left, right) => {
      const comparison =
        sortField === "date"
          ? left.expense.date.localeCompare(right.expense.date)
          : left.expense.amountCents - right.expense.amountCents;
      if (comparison === 0) {
        return left.index - right.index;
      }
      return sortDirection === "ascending" ? comparison : -comparison;
    })
    .map(({ expense }) => expense);
}
