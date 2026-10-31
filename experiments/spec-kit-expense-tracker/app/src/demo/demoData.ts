import type { MonthString } from '../domain/dates';
import type { Expense } from '../domain/expense';

export const DEMO_SELECTED_MONTH: MonthString = '2026-10';

export const DEMO_EXPENSES: readonly Readonly<Expense>[] = Object.freeze([
  Object.freeze({ id: 'demo-001', amountCents: 145000, category: 'housing', date: '2026-10-01', note: 'October rent' }),
  Object.freeze({ id: 'demo-002', amountCents: 4275, category: 'food', date: '2026-10-03', note: 'Groceries at Green Market' }),
  Object.freeze({ id: 'demo-003', amountCents: 1850, category: 'transport', date: '2026-10-05', note: 'Metro card top-up' }),
  Object.freeze({ id: 'demo-004', amountCents: 2400, category: 'entertainment', date: '2026-10-08', note: 'Cinema tickets' }),
  Object.freeze({ id: 'demo-005', amountCents: 1280, category: 'food', date: '2026-10-12', note: 'Coffee and pastry' }),
  Object.freeze({ id: 'demo-006', amountCents: 8500, category: 'other', date: '2026-10-15', note: 'Household supplies' }),
  Object.freeze({ id: 'demo-007', amountCents: 6720, category: 'food', date: '2026-10-18', note: 'Dinner with friends' }),
  Object.freeze({ id: 'demo-008', amountCents: 3240, category: 'transport', date: '2026-10-21', note: 'Airport train' }),
  Object.freeze({ id: 'demo-009', amountCents: 2000, category: 'food', date: '2026-09-30', note: 'Previous month lunch' }),
  Object.freeze({ id: 'demo-010', amountCents: 3000, category: 'entertainment', date: '2026-11-02', note: 'Future concert deposit' }),
] satisfies Readonly<Expense>[]);

export function isDemoMode(search: string): boolean {
  return new URLSearchParams(search).get('demo') === '1';
}
