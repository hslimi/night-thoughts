import { isExpense } from "./domain";
import type { Expense } from "./model";

export const EXPENSES_STORAGE_KEY = "expense-tracker:expenses";

type ExpenseStorage = Pick<Storage, "getItem" | "setItem">;

const browserStorage: ExpenseStorage = {
  getItem: (key) => window.localStorage.getItem(key),
  setItem: (key, value) => window.localStorage.setItem(key, value),
};

export type LoadResult =
  | { kind: "loaded"; expenses: Expense[] }
  | { kind: "malformed"; raw: string }
  | { kind: "error"; error: unknown };

export type WriteResult =
  | { kind: "saved" }
  | { kind: "blocked" }
  | { kind: "error"; error: unknown };

interface ExpenseEnvelope {
  version: 1;
  expenses: Expense[];
}

function isEnvelope(value: unknown): value is ExpenseEnvelope {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    return false;
  }

  const record = value as Record<string, unknown>;
  if (record.version !== 1 || !Array.isArray(record.expenses)) {
    return false;
  }

  const expenses = record.expenses;
  const ids = new Set<string>();
  return expenses.every((expense) => {
    if (!isExpense(expense) || ids.has(expense.id)) {
      return false;
    }
    ids.add(expense.id);
    return true;
  });
}

export function createExpensePersistence(
  storage: ExpenseStorage = browserStorage,
) {
  let state: "unloaded" | "ready" | "malformed" = "unloaded";
  let malformedRaw: string | undefined;

  function load(): LoadResult {
    let raw: string | null;
    try {
      raw = storage.getItem(EXPENSES_STORAGE_KEY);
    } catch (error) {
      state = "unloaded";
      malformedRaw = undefined;
      return { kind: "error", error };
    }

    if (raw === null) {
      state = "ready";
      malformedRaw = undefined;
      return { kind: "loaded", expenses: [] };
    }

    let parsed: unknown;
    try {
      parsed = JSON.parse(raw);
    } catch {
      state = "malformed";
      malformedRaw = raw;
      return { kind: "malformed", raw };
    }

    if (!isEnvelope(parsed)) {
      state = "malformed";
      malformedRaw = raw;
      return { kind: "malformed", raw };
    }

    state = "ready";
    malformedRaw = undefined;
    return { kind: "loaded", expenses: parsed.expenses };
  }

  function save(expenses: Expense[]): WriteResult {
    if (state !== "ready" || malformedRaw !== undefined) {
      return { kind: "blocked" };
    }

    try {
      const envelope: ExpenseEnvelope = { version: 1, expenses };
      storage.setItem(EXPENSES_STORAGE_KEY, JSON.stringify(envelope));
      return { kind: "saved" };
    } catch (error) {
      return { kind: "error", error };
    }
  }

  function startFresh(): WriteResult {
    if (state !== "malformed" || malformedRaw === undefined) {
      return { kind: "blocked" };
    }

    try {
      const envelope: ExpenseEnvelope = { version: 1, expenses: [] };
      storage.setItem(EXPENSES_STORAGE_KEY, JSON.stringify(envelope));
      state = "ready";
      malformedRaw = undefined;
      return { kind: "saved" };
    } catch (error) {
      return { kind: "error", error };
    }
  }

  return { load, save, startFresh };
}
