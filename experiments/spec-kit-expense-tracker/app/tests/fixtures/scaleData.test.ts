import { describe, expect, it } from 'vitest';
import { CATEGORIES, validateExpenseCollection } from '../../src/domain/expense';
import { buildScaleEnvelope } from './scaleData';

describe('SCALE deterministic fixture and MONEY-004', () => {
  it('contains exactly 1,000 valid ID-ordered records with exact integer formulas', () => {
    const envelope = buildScaleEnvelope();

    expect(envelope.version).toBe(1);
    expect(envelope.expenses).toHaveLength(1000);
    expect(validateExpenseCollection(envelope.expenses)).toBe(true);

    const monthCounts = new Map<string, number>();
    const categoryCounts = new Map<string, number>();

    envelope.expenses.forEach((expense, index) => {
      const i = index + 1;
      const month = ((i - 1) % 10) + 1;
      const day = ((i - 1) % 28) + 1;
      const expectedAmountCents = ((i * 7919) % 100000) + 1;

      expect(expense).toEqual({
        id: `scale-${String(i).padStart(4, '0')}`,
        amountCents: expectedAmountCents,
        category: CATEGORIES[(i - 1) % 5],
        date: `2026-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`,
        note: `Scale expense ${i}`,
      });
      expect(Number.isSafeInteger(expense.amountCents)).toBe(true);
      expect(expense.amountCents).toBe(Math.trunc(expense.amountCents));

      const monthKey = expense.date.slice(0, 7);
      monthCounts.set(monthKey, (monthCounts.get(monthKey) ?? 0) + 1);
      categoryCounts.set(
        expense.category,
        (categoryCounts.get(expense.category) ?? 0) + 1,
      );
    });

    expect(envelope.expenses[0]?.id).toBe('scale-0001');
    expect(envelope.expenses[999]?.id).toBe('scale-1000');
    expect(monthCounts.size).toBe(10);
    for (let month = 1; month <= 10; month += 1) {
      expect(monthCounts.get(`2026-${String(month).padStart(2, '0')}`)).toBe(100);
    }
    for (const category of CATEGORIES) {
      expect(categoryCounts.get(category)).toBe(200);
    }
  });

  it('matches independently calculated exact summaries for every SCALE month', () => {
    const { expenses } = buildScaleEnvelope();

    for (let month = 1; month <= 10; month += 1) {
      const monthKey = `2026-${String(month).padStart(2, '0')}`;
      let expectedTotal = 0;
      const expectedCategories = {
        food: 0,
        transport: 0,
        housing: 0,
        entertainment: 0,
        other: 0,
      };

      for (let i = 1; i <= 1000; i += 1) {
        if (((i - 1) % 10) + 1 !== month) {
          continue;
        }
        const amountCents = ((i * 7919) % 100000) + 1;
        expectedTotal += amountCents;
        expectedCategories[CATEGORIES[(i - 1) % 5]!] += amountCents;
      }

      const actualExpenses = expenses.filter((expense) =>
        expense.date.startsWith(`${monthKey}-`),
      );
      const actualTotal = actualExpenses.reduce(
        (total, expense) => total + expense.amountCents,
        0,
      );
      const actualCategories = Object.fromEntries(
        CATEGORIES.map((category) => [
          category,
          actualExpenses
            .filter((expense) => expense.category === category)
            .reduce((total, expense) => total + expense.amountCents, 0),
        ]),
      );

      expect(Number.isSafeInteger(expectedTotal)).toBe(true);
      expect(actualTotal).toBe(expectedTotal);
      expect(actualCategories).toEqual(expectedCategories);
    }
  });
});
