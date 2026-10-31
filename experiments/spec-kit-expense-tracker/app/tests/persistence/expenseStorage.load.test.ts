import { describe, expect, it, vi } from 'vitest';
import {
  buildValidExpense,
  buildVersion1Envelope,
} from '../fixtures/expenses';
import {
  EXPENSES_STORAGE_KEY,
  loadExpenses,
} from '../../src/persistence/expenseStorage';

function createStorage(initialRaw: string | null) {
  let raw = initialRaw;

  return {
    getItem: vi.fn((_key: string) => raw),
    setItem: vi.fn((_key: string, value: string) => {
      raw = value;
    }),
    readRaw: () => raw,
  };
}

describe('expense storage loading', () => {
  it('uses the namespaced version-1 storage key', () => {
    expect(EXPENSES_STORAGE_KEY).toBe('personal-expense-tracker:expenses:v1');
  });

  it('PERSIST-001: classifies a missing key without writing', () => {
    const storage = createStorage(null);

    expect(loadExpenses(storage)).toEqual({ status: 'missing' });
    expect(storage.getItem).toHaveBeenCalledExactlyOnceWith(
      EXPENSES_STORAGE_KEY,
    );
    expect(storage.setItem).not.toHaveBeenCalled();
    expect(storage.readRaw()).toBeNull();
  });

  it('PERSIST-002: restores the exact complete valid collection without duplication or alteration', () => {
    const expenses = [
      buildValidExpense({
        id: 'expense-a',
        amountCents: 1,
        category: 'food',
        date: '2024-02-29',
        note: '  Keep  this\nnote exactly  ',
      }),
      buildValidExpense({
        id: 'expense-b',
        amountCents: 99999999999,
        category: 'housing',
        date: '2027-01-01',
      }),
    ];
    const raw = JSON.stringify(buildVersion1Envelope(expenses));
    const storage = createStorage(raw);

    expect(loadExpenses(storage)).toEqual({ status: 'valid', expenses });
    expect(storage.getItem).toHaveBeenCalledExactlyOnceWith(
      EXPENSES_STORAGE_KEY,
    );
    expect(storage.setItem).not.toHaveBeenCalled();
    expect(storage.readRaw()).toBe(raw);
  });

  it('PERSIST-003: returns readable malformed JSON with its exact raw value and performs no write', () => {
    const raw = '{"version":1,"expenses":[  broken\n';
    const storage = createStorage(raw);

    expect(loadExpenses(storage)).toEqual({
      status: 'readable-malformed',
      raw,
    });
    expect(storage.setItem).not.toHaveBeenCalled();
    expect(storage.readRaw()).toBe(raw);
  });

  it.each([
    ['null', null],
    ['an array', []],
    ['an empty object', {}],
    ['a missing expenses collection', { version: 1 }],
    ['a non-array expenses collection', { version: 1, expenses: {} }],
    ['an unsupported older version', { version: 0, expenses: [] }],
    ['an unsupported future version', { version: 2, expenses: [] }],
    ['a non-numeric version', { version: '1', expenses: [] }],
  ])(
    'PERSIST-004: rejects %s as an invalid version-1 envelope all-or-nothing',
    (_label, envelope) => {
      const raw = JSON.stringify(envelope);
      const storage = createStorage(raw);

      expect(loadExpenses(storage)).toEqual({
        status: 'readable-malformed',
        raw,
      });
      expect(storage.setItem).not.toHaveBeenCalled();
      expect(storage.readRaw()).toBe(raw);
    },
  );

  it.each([
    ['a fractional amount', buildValidExpense({ amountCents: 12.5 })],
    ['a zero amount', buildValidExpense({ amountCents: 0 })],
    ['an invalid category', buildValidExpense({ category: 'invalid' as never })],
    ['an impossible date', buildValidExpense({ date: '2023-02-29' })],
    ['a non-string note', buildValidExpense({ note: 42 as never })],
  ])(
    'PERSIST-005: rejects the entire collection when one record has %s',
    (_label, invalidExpense) => {
      const validExpense = buildValidExpense({
        id: 'valid-looking-record',
        amountCents: 2550,
      });
      const raw = JSON.stringify(
        buildVersion1Envelope([validExpense, invalidExpense]),
      );
      const storage = createStorage(raw);

      expect(loadExpenses(storage)).toEqual({
        status: 'readable-malformed',
        raw,
      });
      expect(storage.setItem).not.toHaveBeenCalled();
      expect(storage.readRaw()).toBe(raw);
    },
  );

  it('PERSIST-006: rejects duplicate IDs without loading any otherwise valid records', () => {
    const expenses = [
      buildValidExpense({ id: 'duplicate-id', amountCents: 100 }),
      buildValidExpense({ id: 'unique-id', amountCents: 200 }),
      buildValidExpense({ id: 'duplicate-id', amountCents: 300 }),
    ];
    const raw = JSON.stringify(buildVersion1Envelope(expenses));
    const storage = createStorage(raw);

    expect(loadExpenses(storage)).toEqual({
      status: 'readable-malformed',
      raw,
    });
    expect(storage.setItem).not.toHaveBeenCalled();
    expect(storage.readRaw()).toBe(raw);
  });

  it('PERSIST-007: classifies storage read exceptions as unreadable and never writes', () => {
    const error = new DOMException('Storage access denied', 'SecurityError');
    const storage = {
      getItem: vi.fn((_key: string): string | null => {
        throw error;
      }),
      setItem: vi.fn((_key: string, _value: string) => {}),
    };

    expect(loadExpenses(storage)).toEqual({ status: 'unreadable', error });
    expect(storage.getItem).toHaveBeenCalledExactlyOnceWith(
      EXPENSES_STORAGE_KEY,
    );
    expect(storage.setItem).not.toHaveBeenCalled();
  });
});
