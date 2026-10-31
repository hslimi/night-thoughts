import { isLocalDate, monthForDate, type LocalDateString, type MonthString } from './dates';
import { MAX_AMOUNT_CENTS, parseAmount } from './money';

export const CATEGORIES = [
  'food',
  'transport',
  'housing',
  'entertainment',
  'other',
] as const;

export type Category = (typeof CATEGORIES)[number];
export type { LocalDateString, MonthString };

export interface Expense {
  id: string;
  amountCents: number;
  category: Category;
  date: LocalDateString;
  note?: string;
}

export interface ExpenseDraft {
  amount: string;
  category: string;
  date: string;
  note: string;
}

export type ExpenseField = 'amount' | 'category' | 'date';
export type ExpenseDraftErrors = Partial<Record<ExpenseField, string>>;

export type ExpenseDraftResult =
  | { ok: true; value: Omit<Expense, 'id'> }
  | { ok: false; errors: ExpenseDraftErrors };

export type CreateExpenseResult =
  | { ok: true; expense: Expense }
  | { ok: false; errors: ExpenseDraftErrors };

function isCategory(value: unknown): value is Category {
  return typeof value === 'string' && CATEGORIES.includes(value as Category);
}

function normalizeNote(note: string): string | undefined {
  return note.trim() === '' ? undefined : note;
}

export function validateExpenseDraft(draft: ExpenseDraft): ExpenseDraftResult {
  const errors: ExpenseDraftErrors = {};
  const amount = parseAmount(draft.amount);
  if (!amount.ok) {
    errors.amount =
      'Enter a valid USD amount greater than zero with no more than two decimal places.';
  }
  if (!isCategory(draft.category)) {
    errors.category = 'Choose a valid category.';
  }
  if (!isLocalDate(draft.date)) {
    errors.date = 'Enter a real local calendar date in YYYY-MM-DD format.';
  }
  if (Object.keys(errors).length > 0 || !amount.ok) {
    return { ok: false, errors };
  }

  const value: Omit<Expense, 'id'> = {
    amountCents: amount.amountCents,
    category: draft.category as Category,
    date: draft.date,
  };
  const note = normalizeNote(draft.note);
  if (note !== undefined) {
    value.note = note;
  }
  return { ok: true, value };
}

export function createExpense(
  id: string,
  draft: ExpenseDraft,
): CreateExpenseResult {
  if (id.trim() === '') {
    throw new Error('Expense must have a nonempty id');
  }
  const result = validateExpenseDraft(draft);
  if (!result.ok) {
    return result;
  }
  return { ok: true, expense: { id, ...result.value } };
}

export function validateExpenseRecord(value: unknown): value is Expense {
  if (typeof value !== 'object' || value === null || Array.isArray(value)) {
    return false;
  }
  const record = value as Record<string, unknown>;
  return (
    typeof record.id === 'string' &&
    record.id.trim() !== '' &&
    typeof record.amountCents === 'number' &&
    Number.isSafeInteger(record.amountCents) &&
    record.amountCents >= 1 &&
    record.amountCents <= MAX_AMOUNT_CENTS &&
    isCategory(record.category) &&
    isLocalDate(record.date) &&
    monthForDate(record.date) === record.date.slice(0, 7) &&
    (record.note === undefined || typeof record.note === 'string')
  );
}

export function validateExpenseCollection(value: unknown): value is Expense[] {
  if (!Array.isArray(value) || !value.every(validateExpenseRecord)) {
    return false;
  }
  const ids = value.map((expense) => expense.id);
  return new Set(ids).size === ids.length;
}
