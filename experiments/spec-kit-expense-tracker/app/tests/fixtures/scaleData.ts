import { CATEGORIES, type Expense } from '../../src/domain/expense';

interface ScaleEnvelope {
  version: 1;
  expenses: Expense[];
}

export function buildScaleEnvelope(): ScaleEnvelope {
  const expenses: Expense[] = [];

  for (let i = 1; i <= 1000; i += 1) {
    const month = ((i - 1) % 10) + 1;
    const day = ((i - 1) % 28) + 1;
    expenses.push({
      id: `scale-${String(i).padStart(4, '0')}`,
      amountCents: ((i * 7919) % 100000) + 1,
      category: CATEGORIES[(i - 1) % 5]!,
      date: `2026-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`,
      note: `Scale expense ${i}`,
    });
  }

  return { version: 1, expenses };
}
