import { describe, expect, it, vi } from 'vitest';
import {
  buildValidExpense,
  buildVersion1Envelope,
} from '../fixtures/expenses';
import { parseAmount } from '../../src/domain/money';
import {
  EXPENSES_STORAGE_KEY,
  loadExpenses,
  saveExpenses,
} from '../../src/persistence/expenseStorage';

function createStorage(initialRaw: string | null = null) {
  let raw = initialRaw;
  let nextWriteError: unknown;

  return {
    getItem: vi.fn((_key: string) => raw),
    setItem: vi.fn((_key: string, value: string) => {
      if (nextWriteError !== undefined) {
        const error = nextWriteError;
        nextWriteError = undefined;
        throw error;
      }
      raw = value;
    }),
    failNextWrite(error: unknown) {
      nextWriteError = error;
    },
    readRaw: () => raw,
  };
}

const acceptedAmounts = [
  ['AMOUNT-001', '1'],
  ['AMOUNT-001', '1.2'],
  ['AMOUNT-001', '1.23'],
  ['AMOUNT-002', '  001.2  '],
  ['AMOUNT-002', '000.50'],
  ['AMOUNT-002', '.50'],
  ['AMOUNT-003', '0.01'],
  ['AMOUNT-003', '999999999.99'],
] as const;

describe('expense storage writes', () => {
  it('PERSIST-002/013: saves the complete current collection in one version-1 envelope', () => {
    const previousExpenses = [buildValidExpense({ id: 'previous-expense' })];
    const previousRaw = JSON.stringify(buildVersion1Envelope(previousExpenses));
    const storage = createStorage(previousRaw);
    const currentExpenses = [
      buildValidExpense({ id: 'current-a', amountCents: 100 }),
      buildValidExpense({
        id: 'current-b',
        amountCents: 234,
        category: 'transport',
      }),
      buildValidExpense({
        id: 'current-c',
        amountCents: 99999999999,
        category: 'other',
      }),
    ] as const;
    const snapshot = currentExpenses.map((expense) => ({ ...expense }));

    expect(saveExpenses(currentExpenses, storage)).toEqual({ status: 'saved' });
    expect(storage.setItem).toHaveBeenCalledExactlyOnceWith(
      EXPENSES_STORAGE_KEY,
      JSON.stringify(buildVersion1Envelope([...currentExpenses])),
    );
    expect(storage.getItem).not.toHaveBeenCalled();
    expect(JSON.parse(storage.readRaw() ?? 'null')).toEqual(
      buildVersion1Envelope([...currentExpenses]),
    );
    expect(currentExpenses).toEqual(snapshot);
  });

  it('PERSIST-008: reports quota failure without changing the input or last durable value', () => {
    const durableExpenses = [buildValidExpense({ id: 'durable-expense' })];
    const durableRaw = JSON.stringify(buildVersion1Envelope(durableExpenses));
    const storage = createStorage(durableRaw);
    const error = new DOMException('Quota exceeded', 'QuotaExceededError');
    storage.failNextWrite(error);
    const changedExpenses = [
      ...durableExpenses,
      buildValidExpense({ id: 'retained-add', amountCents: 500 }),
    ];
    const snapshot = changedExpenses.map((expense) => ({ ...expense }));

    expect(saveExpenses(changedExpenses, storage)).toEqual({
      status: 'write-failed',
      error,
    });
    expect(storage.setItem).toHaveBeenCalledExactlyOnceWith(
      EXPENSES_STORAGE_KEY,
      JSON.stringify(buildVersion1Envelope(changedExpenses)),
    );
    expect(storage.getItem).not.toHaveBeenCalled();
    expect(storage.readRaw()).toBe(durableRaw);
    expect(changedExpenses).toEqual(snapshot);
    expect(loadExpenses(storage)).toEqual({
      status: 'valid',
      expenses: durableExpenses,
    });
  });

  it('PERSIST-011: reports serialization failure without writing or using a destructive fallback', () => {
    const durableRaw = JSON.stringify(buildVersion1Envelope());
    const storage = createStorage(durableRaw);
    const expense = buildValidExpense({ id: 'cyclic-expense' }) as ReturnType<
      typeof buildValidExpense
    > & { self?: unknown };
    expense.self = expense;
    const expenses = [expense];

    const result = saveExpenses(expenses, storage);
    expect(result.status).toBe('write-failed');
    if (result.status === 'write-failed') {
      expect(result.error).toBeInstanceOf(TypeError);
    }
    expect(storage.setItem).not.toHaveBeenCalled();
    expect(storage.getItem).not.toHaveBeenCalled();
    expect(storage.readRaw()).toBe(durableRaw);
    expect(expense.self).toBe(expense);
  });

  it('PERSIST-012: reports a mid-session storage access failure without fallback or mutation', () => {
    const durableExpenses = [buildValidExpense({ id: 'durable-expense' })];
    const durableRaw = JSON.stringify(buildVersion1Envelope(durableExpenses));
    const storage = createStorage(durableRaw);
    const error = new DOMException('Storage became unavailable', 'SecurityError');
    storage.failNextWrite(error);
    const changedExpenses = [
      buildValidExpense({ id: 'replacement', amountCents: 7654 }),
    ];
    const snapshot = changedExpenses.map((expense) => ({ ...expense }));

    expect(saveExpenses(changedExpenses, storage)).toEqual({
      status: 'write-failed',
      error,
    });
    expect(storage.setItem).toHaveBeenCalledTimes(1);
    expect(storage.getItem).not.toHaveBeenCalled();
    expect(storage.readRaw()).toBe(durableRaw);
    expect(changedExpenses).toEqual(snapshot);
  });

  it('PERSIST-013: a later successful save persists every retained record and reloads exactly', () => {
    const durableExpenses = [buildValidExpense({ id: 'durable-expense' })];
    const durableRaw = JSON.stringify(buildVersion1Envelope(durableExpenses));
    const storage = createStorage(durableRaw);
    const retainedExpenses = [
      ...durableExpenses,
      buildValidExpense({ id: 'retained-add', amountCents: 120 }),
    ];
    const currentExpenses = [
      ...retainedExpenses,
      buildValidExpense({ id: 'later-add', amountCents: 50 }),
    ];
    const quotaError = new DOMException('Quota exceeded', 'QuotaExceededError');
    storage.failNextWrite(quotaError);

    expect(saveExpenses(retainedExpenses, storage)).toEqual({
      status: 'write-failed',
      error: quotaError,
    });
    expect(storage.readRaw()).toBe(durableRaw);

    expect(saveExpenses(currentExpenses, storage)).toEqual({ status: 'saved' });
    expect(storage.setItem).toHaveBeenCalledTimes(2);
    expect(storage.setItem).toHaveBeenLastCalledWith(
      EXPENSES_STORAGE_KEY,
      JSON.stringify(buildVersion1Envelope(currentExpenses)),
    );
    expect(JSON.parse(storage.readRaw() ?? 'null')).toEqual(
      buildVersion1Envelope(currentExpenses),
    );
    expect(loadExpenses(storage)).toEqual({
      status: 'valid',
      expenses: currentExpenses,
    });
  });

  it.each(acceptedAmounts)(
    '%s and MONEY-004: round-trips %j as independently parsed exact integer cents',
    (_caseId, input) => {
      const parsed = parseAmount(input);
      expect(parsed.ok).toBe(true);
      if (!parsed.ok) {
        throw new Error(`Accepted fixture was rejected: ${input}`);
      }

      const expense = buildValidExpense({
        id: 'amount-roundtrip',
        amountCents: parsed.amountCents,
        note: `Original amount input: ${input}`,
      });
      const storage = createStorage();

      expect(saveExpenses([expense], storage)).toEqual({ status: 'saved' });
      const raw = storage.readRaw();
      expect(raw).not.toBeNull();
      const envelope = JSON.parse(raw ?? 'null') as {
        version: unknown;
        expenses: Array<{ amountCents: unknown }>;
      };
      expect(envelope.version).toBe(1);
      expect(envelope.expenses).toHaveLength(1);
      const storedExpense = envelope.expenses[0];
      expect(storedExpense).toBeDefined();
      if (!storedExpense) {
        throw new Error('Missing stored expense');
      }
      expect(typeof storedExpense.amountCents).toBe('number');
      if (typeof storedExpense.amountCents !== 'number') {
        throw new Error('Stored amountCents is not a JSON number');
      }
      expect(Number.isSafeInteger(storedExpense.amountCents)).toBe(true);
      expect(storedExpense.amountCents).toBe(parsed.amountCents);

      const loaded = loadExpenses(storage);
      expect(loaded).toEqual({ status: 'valid', expenses: [expense] });
      if (loaded.status === 'valid') {
        const loadedAmount = loaded.expenses[0]?.amountCents;
        expect(loadedAmount).toBe(parsed.amountCents);
        expect(typeof loadedAmount).toBe('number');
        if (typeof loadedAmount !== 'number') {
          throw new Error('Reloaded amountCents is not a number');
        }
        expect(Number.isSafeInteger(loadedAmount)).toBe(true);
      }
    },
  );
});
