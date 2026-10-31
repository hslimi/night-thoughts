import { describe, expect, it } from 'vitest';
import {
  CATEGORIES,
  buildExpectedMonthlySummary,
  buildValidExpense,
} from '../fixtures/expenses';
import { summarizeMonth } from '../../src/domain/dashboard';
import { MAX_AMOUNT_CENTS } from '../../src/domain/money';

const monthRecords = [
  buildValidExpense({ id: 'september', amountCents: 9999, date: '2026-09-30' }),
  buildValidExpense({ id: 'october-first', amountCents: 100, category: 'food', date: '2026-10-01' }),
  buildValidExpense({ id: 'october-last', amountCents: 200, category: 'transport', date: '2026-10-31' }),
  buildValidExpense({ id: 'november', amountCents: 8888, date: '2026-11-01' }),
];

describe('monthly dashboard calculations', () => {
  it('CORE-001/003 and DATE-001: includes exact first/last-day and all-category totals', () => {
    const records = [
      ...monthRecords,
      buildValidExpense({ id: 'housing', amountCents: 300, category: 'housing', date: '2026-10-15' }),
      buildValidExpense({ id: 'entertainment', amountCents: 400, category: 'entertainment', date: '2026-10-15' }),
      buildValidExpense({ id: 'other', amountCents: 500, category: 'other', date: '2026-10-15' }),
    ];
    const expected = buildExpectedMonthlySummary(records, '2026-10');
    const summary = summarizeMonth(records, '2026-10');

    expect(summary.month).toBe('2026-10');
    expect(summary.total).toEqual({ ok: true, cents: expected.totalCents });
    expect(summary.total).toEqual({ ok: true, cents: 1500 });
    expect(summary.monthExpenses.map((expense) => expense.id)).toEqual([
      'october-first',
      'october-last',
      'housing',
      'entertainment',
      'other',
    ]);

    for (const category of CATEGORIES) {
      expect(summary.categoryTotals[category]).toEqual({
        ok: true,
        cents: expected.categoryTotals[category],
      });
    }
  });

  it('MONEY-001: returns explicit zero totals for every category', () => {
    const summary = summarizeMonth(monthRecords, '2027-01');
    expect(summary.total).toEqual({ ok: true, cents: 0 });
    expect(summary.monthExpenses).toEqual([]);
    for (const category of CATEGORIES) {
      expect(summary.categoryTotals[category]).toEqual({
        ok: true,
        cents: 0,
      });
    }
  });

  it('DATE-003: isolates future records in their own month', () => {
    expect(summarizeMonth(monthRecords, '2026-10').monthExpenses).toHaveLength(2);
    const future = summarizeMonth(monthRecords, '2026-11');
    expect(future.total).toEqual({ ok: true, cents: 8888 });
    expect(future.monthExpenses.map((expense) => expense.id)).toEqual(['november']);
  });

  it('OVERFLOW-001: rejects unsafe aggregates without changing source records', () => {
    const records = Array.from({ length: 90072 }, (_, index) =>
      buildValidExpense({
        id: `overflow-${index + 1}`,
        amountCents: MAX_AMOUNT_CENTS,
        category: 'food',
        date: '2026-10-15',
      }),
    );
    const before = records.map((record) => ({ ...record }));
    const summary = summarizeMonth(records, '2026-10');

    expect(summary.total).toEqual({ ok: false, error: 'unsafe-total' });
    expect(summary.categoryTotals.food).toEqual({
      ok: false,
      error: 'unsafe-total',
    });
    expect(summary.categoryTotals.transport).toEqual({ ok: true, cents: 0 });
    expect(summary.monthExpenses).toHaveLength(90072);
    expect(records).toEqual(before);
  });
});
