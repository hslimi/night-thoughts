import { useCallback, useMemo, useState } from 'react';
import {
  filterAndSortExpenses,
  summarizeMonth,
  type TransactionPreferences,
} from '../domain/dashboard';
import { getCurrentLocalMonth, isMonth, type MonthString } from '../domain/dates';
import { DEMO_EXPENSES, DEMO_SELECTED_MONTH } from '../demo/demoData';
import {
  createExpense,
  type CreateExpenseResult,
  type Expense,
  type ExpenseDraft,
} from '../domain/expense';
import {
  loadExpenses,
  saveExpenses,
  type StorageLike,
} from '../persistence/expenseStorage';

let fallbackIdCounter = 0;

export type RecoveryKind = 'readable-malformed' | 'unreadable';
export type PersistenceIssue =
  | 'unsaved-add'
  | 'unsaved-edit'
  | 'unsaved-delete'
  | 'replacement-failed'
  | null;
export type ReplacementKind = 'start-fresh' | 'first-replacement';

interface InitialStoreState {
  expenses: Expense[];
  recovery: RecoveryKind | null;
}

function nextId(expenses: Expense[]): string {
  const existingIds = new Set(expenses.map((expense) => expense.id));
  let id = '';
  do {
    if (typeof globalThis.crypto?.randomUUID === 'function') {
      id = `expense-${globalThis.crypto.randomUUID()}`;
    } else {
      fallbackIdCounter += 1;
      id = `expense-${Date.now().toString(36)}-${fallbackIdCounter.toString(36)}`;
    }
  } while (id.trim() === '' || existingIds.has(id));
  return id;
}

function initializeStore(
  initialExpenses: Expense[] | undefined,
  storage: StorageLike | undefined,
  demo: boolean,
): InitialStoreState {
  if (demo) {
    return {
      expenses: DEMO_EXPENSES.map((expense) => ({ ...expense })),
      recovery: null,
    };
  }
  if (initialExpenses !== undefined) {
    return {
      expenses: initialExpenses.map((expense) => ({ ...expense })),
      recovery: null,
    };
  }

  const result = loadExpenses(storage);
  if (result.status === 'valid') {
    return {
      expenses: result.expenses.map((expense) => ({ ...expense })),
      recovery: null,
    };
  }
  if (result.status === 'readable-malformed' || result.status === 'unreadable') {
    return { expenses: [], recovery: result.status };
  }
  return { expenses: [], recovery: null };
}

export function useExpenseStore(
  initialExpenses?: Expense[],
  storage?: StorageLike,
  demo = false,
) {
  const [initial] = useState(() => initializeStore(initialExpenses, storage, demo));
  const [expenses, setExpenses] = useState<Expense[]>(initial.expenses);
  const [selectedMonth, setSelectedMonth] = useState<MonthString>(() =>
    demo ? DEMO_SELECTED_MONTH : getCurrentLocalMonth(),
  );
  const [recovery, setRecovery] = useState<RecoveryKind | null>(initial.recovery);
  const [persistenceIssue, setPersistenceIssue] =
    useState<PersistenceIssue>(null);
  const [replacement, setReplacement] = useState<ReplacementKind | null>(null);
  const [transactionPreferences, setTransactionPreferences] =
    useState<TransactionPreferences>({
      category: 'all',
      sortField: 'date',
      sortDirection: 'desc',
    });

  const selectMonth = useCallback((month: MonthString) => {
    if (isMonth(month)) {
      setSelectedMonth(month);
    }
  }, []);

  const persistMutation = useCallback(
    (
      nextExpenses: Expense[],
      failureIssue: Exclude<PersistenceIssue, 'replacement-failed' | null>,
    ) => {
      setExpenses(nextExpenses);
      if (demo) {
        setPersistenceIssue(null);
        return;
      }
      if (recovery !== null) {
        setReplacement('first-replacement');
        return;
      }

      const saveResult = saveExpenses(nextExpenses, storage);
      setPersistenceIssue(saveResult.status === 'saved' ? null : failureIssue);
    },
    [demo, recovery, storage],
  );

  const addExpense = useCallback(
    (draft: ExpenseDraft): CreateExpenseResult => {
      const result = createExpense(nextId(expenses), draft);
      if (!result.ok) {
        return result;
      }

      persistMutation([...expenses, result.expense], 'unsaved-add');
      return result;
    },
    [expenses, persistMutation],
  );

  const editExpense = useCallback(
    (id: string, draft: ExpenseDraft): CreateExpenseResult => {
      const result = createExpense(id, draft);
      if (!result.ok) {
        return result;
      }

      const nextExpenses = expenses.map((expense) =>
        expense.id === id ? result.expense : expense,
      );
      persistMutation(nextExpenses, 'unsaved-edit');
      return result;
    },
    [expenses, persistMutation],
  );

  const deleteExpense = useCallback(
    (id: string) => {
      const nextExpenses = expenses.filter((expense) => expense.id !== id);
      if (nextExpenses.length === expenses.length) {
        return;
      }
      persistMutation(nextExpenses, 'unsaved-delete');
    },
    [expenses, persistMutation],
  );

  const requestStartFresh = useCallback(() => {
    if (!demo) {
      setReplacement('start-fresh');
    }
  }, [demo]);

  const cancelReplacement = useCallback(() => {
    setReplacement(null);
  }, []);

  const confirmReplacement = useCallback(() => {
    if (demo) {
      setReplacement(null);
      return;
    }
    if (replacement === null) {
      return;
    }
    const nextExpenses = replacement === 'start-fresh' ? [] : expenses;
    const result = saveExpenses(nextExpenses, storage);
    if (result.status === 'saved') {
      if (replacement === 'start-fresh') {
        setExpenses([]);
      }
      setRecovery(null);
      setPersistenceIssue(null);
    } else {
      setPersistenceIssue('replacement-failed');
    }
    setReplacement(null);
  }, [demo, expenses, replacement, storage]);

  const summary = useMemo(
    () => summarizeMonth(expenses, selectedMonth),
    [expenses, selectedMonth],
  );
  const visibleExpenses = useMemo(
    () => filterAndSortExpenses(summary.monthExpenses, transactionPreferences),
    [summary.monthExpenses, transactionPreferences],
  );

  return {
    expenses,
    selectedMonth,
    setSelectedMonth: selectMonth,
    addExpense,
    editExpense,
    deleteExpense,
    summary,
    transactionPreferences,
    setTransactionPreferences,
    visibleExpenses,
    recovery,
    persistenceIssue,
    replacement,
    requestStartFresh,
    cancelReplacement,
    confirmReplacement,
  };
}
