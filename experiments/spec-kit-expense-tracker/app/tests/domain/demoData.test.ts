import { describe, expect, it } from 'vitest';
import { filterAndSortExpenses, summarizeMonth } from '../../src/domain/dashboard';
import {
  DEMO_EXPENSES,
  DEMO_SELECTED_MONTH,
  isDemoMode,
} from '../../src/demo/demoData';

const expectedRecords = [
  { id: 'demo-001', amountCents: 145000, category: 'housing', date: '2026-10-01', note: 'October rent' },
  { id: 'demo-002', amountCents: 4275, category: 'food', date: '2026-10-03', note: 'Groceries at Green Market' },
  { id: 'demo-003', amountCents: 1850, category: 'transport', date: '2026-10-05', note: 'Metro card top-up' },
  { id: 'demo-004', amountCents: 2400, category: 'entertainment', date: '2026-10-08', note: 'Cinema tickets' },
  { id: 'demo-005', amountCents: 1280, category: 'food', date: '2026-10-12', note: 'Coffee and pastry' },
  { id: 'demo-006', amountCents: 8500, category: 'other', date: '2026-10-15', note: 'Household supplies' },
  { id: 'demo-007', amountCents: 6720, category: 'food', date: '2026-10-18', note: 'Dinner with friends' },
  { id: 'demo-008', amountCents: 3240, category: 'transport', date: '2026-10-21', note: 'Airport train' },
  { id: 'demo-009', amountCents: 2000, category: 'food', date: '2026-09-30', note: 'Previous month lunch' },
  { id: 'demo-010', amountCents: 3000, category: 'entertainment', date: '2026-11-02', note: 'Future concert deposit' },
] as const;

describe('DEMO-002: normative fictional baseline', () => {
  it('contains exactly ten readonly records with exact integer cents, dates, categories, and notes', () => {
    expect(DEMO_EXPENSES).toEqual(expectedRecords);
    expect(DEMO_EXPENSES).toHaveLength(10);
    expect(Object.isFrozen(DEMO_EXPENSES)).toBe(true);
    expect(DEMO_EXPENSES.every((expense) => Object.isFrozen(expense))).toBe(true);
    expect(DEMO_EXPENSES.every((expense) => Number.isSafeInteger(expense.amountCents))).toBe(true);
    expect(new Set(DEMO_EXPENSES.map((expense) => expense.id)).size).toBe(10);
  });

  it('fixes October 2026 totals and excludes both adjacent-month records', () => {
    const summary = summarizeMonth([...DEMO_EXPENSES], DEMO_SELECTED_MONTH);

    expect(DEMO_SELECTED_MONTH).toBe('2026-10');
    expect(summary.total).toEqual({ ok: true, cents: 173265 });
    expect(summary.categoryTotals).toEqual({
      food: { ok: true, cents: 12275 },
      transport: { ok: true, cents: 5090 },
      housing: { ok: true, cents: 145000 },
      entertainment: { ok: true, cents: 2400 },
      other: { ok: true, cents: 8500 },
    });
    expect(summary.monthExpenses.map((expense) => expense.id)).not.toContain('demo-009');
    expect(summary.monthExpenses.map((expense) => expense.id)).not.toContain('demo-010');
    expect(summarizeMonth([...DEMO_EXPENSES], '2026-09').monthExpenses.map((expense) => expense.id)).toEqual(['demo-009']);
    expect(summarizeMonth([...DEMO_EXPENSES], '2026-11').monthExpenses.map((expense) => expense.id)).toEqual(['demo-010']);
  });

  it('uses the specified newest-first default order', () => {
    const summary = summarizeMonth([...DEMO_EXPENSES], DEMO_SELECTED_MONTH);
    const visible = filterAndSortExpenses(summary.monthExpenses, {
      category: 'all',
      sortField: 'date',
      sortDirection: 'desc',
    });

    expect(visible.map((expense) => expense.id)).toEqual([
      'demo-008',
      'demo-007',
      'demo-006',
      'demo-005',
      'demo-004',
      'demo-003',
      'demo-002',
      'demo-001',
    ]);
  });
});

describe('DEMO-001: exact first-value activation', () => {
  it.each([
    ['?demo=1', true],
    ['?source=x&demo=1', true],
    ['?demo=1&demo=0', true],
    ['?demo=0&demo=1', false],
    ['?demo=01', false],
    ['?demo=true', false],
    ['?Demo=1', false],
    ['', false],
    ['?source=x', false],
    ['?demo=', false],
    ['?demo=1%20', false],
  ])('parses %s as demo=%s', (search, expected) => {
    expect(isDemoMode(search)).toBe(expected);
  });
});
