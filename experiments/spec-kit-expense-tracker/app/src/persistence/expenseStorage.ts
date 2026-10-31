import {
  validateExpenseCollection,
  type Expense,
} from '../domain/expense';

export const EXPENSES_STORAGE_KEY = 'personal-expense-tracker:expenses:v1';

export interface StorageLike {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
}

export type LoadExpensesResult =
  | { status: 'missing' }
  | { status: 'valid'; expenses: Expense[] }
  | { status: 'readable-malformed'; raw: string }
  | { status: 'unreadable'; error: unknown };

export type SaveExpensesResult =
  | { status: 'saved' }
  | { status: 'write-failed'; error: unknown };

interface Version1Envelope {
  version: 1;
  expenses: Expense[];
}

function browserStorage(): StorageLike {
  return globalThis.localStorage;
}

export function loadExpenses(storage?: StorageLike): LoadExpensesResult {
  let raw: string | null;
  try {
    raw = (storage ?? browserStorage()).getItem(EXPENSES_STORAGE_KEY);
  } catch (error) {
    return { status: 'unreadable', error };
  }

  if (raw === null) {
    return { status: 'missing' };
  }

  let envelope: unknown;
  try {
    envelope = JSON.parse(raw);
  } catch {
    return { status: 'readable-malformed', raw };
  }

  if (typeof envelope !== 'object' || envelope === null || Array.isArray(envelope)) {
    return { status: 'readable-malformed', raw };
  }
  const candidate = envelope as Record<string, unknown>;
  if (candidate.version !== 1 || !validateExpenseCollection(candidate.expenses)) {
    return { status: 'readable-malformed', raw };
  }

  return { status: 'valid', expenses: candidate.expenses };
}

export function saveExpenses(
  expenses: readonly Expense[],
  storage?: StorageLike,
): SaveExpensesResult {
  try {
    const envelope: Version1Envelope = {
      version: 1,
      expenses: expenses.map((expense) => ({ ...expense })),
    };
    const raw = JSON.stringify(envelope);
    (storage ?? browserStorage()).setItem(EXPENSES_STORAGE_KEY, raw);
    return { status: 'saved' };
  } catch (error) {
    return { status: 'write-failed', error };
  }
}
