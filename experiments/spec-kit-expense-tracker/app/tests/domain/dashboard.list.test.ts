import { describe, expect, it } from 'vitest';
import {
  filterAndSortExpenses,
  summarizeMonth,
  type TransactionPreferences,
} from '../../src/domain/dashboard';
import {
  CATEGORIES,
  buildValidExpense,
  type Category,
} from '../fixtures/expenses';

const records = [
  buildValidExpense({ id: 'tie-a', amountCents: 200, category: 'food', date: '2026-10-10' }),
  buildValidExpense({ id: 'tie-c', amountCents: 100, category: 'transport', date: '2026-10-10' }),
  buildValidExpense({ id: 'tie-b', amountCents: 200, category: 'housing', date: '2026-10-10' }),
  buildValidExpense({ id: 'older', amountCents: 50, category: 'entertainment', date: '2026-10-01' }),
  buildValidExpense({ id: 'newer', amountCents: 150, category: 'other', date: '2026-10-31' }),
  buildValidExpense({ id: 'september', amountCents: 999, category: 'food', date: '2026-09-30' }),
];

function preferences(
  category: Category | 'all' = 'all',
  sortField: TransactionPreferences['sortField'] = 'date',
  sortDirection: TransactionPreferences['sortDirection'] = 'desc',
): TransactionPreferences {
  return { category, sortField, sortDirection };
}

function ids(preferencesValue: TransactionPreferences) {
  const monthExpenses = summarizeMonth(records, '2026-10').monthExpenses;
  return filterAndSortExpenses(monthExpenses, preferencesValue).map((expense) => expense.id);
}

describe('transaction list filtering', () => {
  it.each(CATEGORIES)('FILTER-001: selects only exact %s membership', (category) => {
    const expected = records.find(
      (record) => record.date.startsWith('2026-10-') && record.category === category,
    )!;
    expect(ids(preferences(category))).toEqual([expected.id]);
  });

  it('FILTER-001/002: all restores every month record and an absent category has no matches', () => {
    expect(ids(preferences())).toEqual(['newer', 'tie-a', 'tie-b', 'tie-c', 'older']);
    expect(ids(preferences('food'))).toEqual(['tie-a']);
    expect(
      filterAndSortExpenses(
        [records[0]!],
        preferences('transport'),
      ),
    ).toEqual([]);
  });
});

describe('transaction list sorting', () => {
  it.each([
    ['asc', ['older', 'tie-a', 'tie-b', 'tie-c', 'newer']],
    ['desc', ['newer', 'tie-a', 'tie-b', 'tie-c', 'older']],
  ] as const)('SORT-001: date %s keeps same-date IDs ascending', (sortDirection, expected) => {
    expect(ids(preferences('all', 'date', sortDirection))).toEqual(expected);
  });

  it.each([
    ['asc', ['older', 'tie-c', 'newer', 'tie-a', 'tie-b']],
    ['desc', ['tie-a', 'tie-b', 'newer', 'tie-c', 'older']],
  ] as const)('SORT-002: exact-cent amount %s keeps amount-tie IDs ascending', (sortDirection, expected) => {
    expect(ids(preferences('all', 'amount', sortDirection))).toEqual(expected);
  });

  it('FILTER-001 and SORT-001/002: do not mutate source order or unfiltered summaries', () => {
    const before = records.map((record) => ({ ...record }));
    const summary = summarizeMonth(records, '2026-10');

    expect(filterAndSortExpenses(summary.monthExpenses, preferences('all', 'amount', 'asc')).map((record) => record.id)).toEqual([
      'older', 'tie-c', 'newer', 'tie-a', 'tie-b',
    ]);
    expect(records).toEqual(before);
    expect(summary.monthExpenses.map((record) => record.id)).toEqual([
      'tie-a', 'tie-c', 'tie-b', 'older', 'newer',
    ]);
    expect(summary.total).toEqual({ ok: true, cents: 700 });
    expect(summary.categoryTotals).toEqual({
      food: { ok: true, cents: 200 },
      transport: { ok: true, cents: 100 },
      housing: { ok: true, cents: 200 },
      entertainment: { ok: true, cents: 50 },
      other: { ok: true, cents: 150 },
    });
  });
});
