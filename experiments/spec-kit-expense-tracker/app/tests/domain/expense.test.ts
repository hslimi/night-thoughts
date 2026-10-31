import { describe, expect, it } from 'vitest';
import {
  CATEGORIES as FIXTURE_CATEGORIES,
  buildExpenseDraft,
  buildValidExpense,
} from '../fixtures/expenses';
import {
  CATEGORIES,
  createExpense,
  validateExpenseCollection,
  validateExpenseDraft,
  validateExpenseRecord,
} from '../../src/domain/expense';
import { MAX_AMOUNT_CENTS } from '../../src/domain/money';

describe('expense drafts and records', () => {
  it('CORE-003: supports exactly the five specified categories', () => {
    expect(CATEGORIES).toEqual(FIXTURE_CATEGORIES);

    for (const category of FIXTURE_CATEGORIES) {
      const result = createExpense(
        `expense-${category}`,
        buildExpenseDraft({ category }),
      );
      expect(result).toEqual({
        ok: true,
        expense: expect.objectContaining({
          id: `expense-${category}`,
          category,
        }),
      });
    }
  });

  it('CORE-003: rejects an invalid draft category without producing a record', () => {
    const result = validateExpenseDraft(
      buildExpenseDraft({ category: 'investment' }),
    );
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.errors.category).toMatch(/choose a valid category/i);
    }
  });

  it('CORE-004: omits blank and whitespace-only notes', () => {
    for (const note of ['', '   ', '\t\n ']) {
      const result = createExpense(
        'expense-blank-note',
        buildExpenseDraft({ note }),
      );
      expect(result.ok).toBe(true);
      if (result.ok) {
        expect('note' in result.expense).toBe(false);
      }
    }
  });

  it('CORE-004: preserves a nonblank note exactly, including surrounding whitespace', () => {
    const note = '  Keep  this\nnote exactly  ';
    const result = createExpense(
      'expense-exact-note',
      buildExpenseDraft({ note }),
    );
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.expense.note).toBe(note);
      expect(result.expense.id).toBe('expense-exact-note');
    }
  });

  it('rejects a blank generated identity', () => {
    expect(() =>
      createExpense('   ', buildExpenseDraft()),
    ).toThrow(/nonempty id/i);
  });

  it('accepts a valid persisted record and preserves its stable identity', () => {
    const expense = buildValidExpense({ id: 'stable-record-id' });
    expect(validateExpenseRecord(expense)).toBe(true);
    expect(expense.id).toBe('stable-record-id');
  });

  it.each([
    null,
    undefined,
    'expense',
    [],
    buildValidExpense({ id: '' }),
    buildValidExpense({ id: '   ' }),
    buildValidExpense({ amountCents: 0 }),
    buildValidExpense({ amountCents: -1 }),
    buildValidExpense({ amountCents: 1.5 }),
    buildValidExpense({ amountCents: Number.MAX_SAFE_INTEGER + 1 }),
    buildValidExpense({ amountCents: MAX_AMOUNT_CENTS + 1 }),
    buildValidExpense({ category: 'invalid' as never }),
    buildValidExpense({ date: '2023-02-29' }),
    buildValidExpense({ date: '2026-2-09' }),
    buildValidExpense({ note: 42 as never }),
  ])('rejects invalid persisted record %#', (record) => {
    expect(validateExpenseRecord(record)).toBe(false);
  });

  it('rejects duplicate IDs across a persisted collection', () => {
    const expenses = [
      buildValidExpense({ id: 'duplicate-id' }),
      buildValidExpense({ id: 'duplicate-id' }),
    ];
    expect(validateExpenseCollection(expenses)).toBe(false);
    expect(validateExpenseCollection([])).toBe(true);
    expect(
      validateExpenseCollection([
        buildValidExpense({ id: 'unique-a' }),
        buildValidExpense({ id: 'unique-b' }),
      ]),
    ).toBe(true);
  });
});
