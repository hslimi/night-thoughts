import { fireEvent, render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import App from '../../src/App';
import { buildFixedLocalClock } from '../fixtures/expenses';

const acceptedAmounts = [
  ['AMOUNT-001', '1', '$1.00'],
  ['AMOUNT-001', '1.2', '$1.20'],
  ['AMOUNT-001', '1.23', '$1.23'],
  ['AMOUNT-002', '  001.2  ', '$1.20'],
  ['AMOUNT-002', '000.50', '$0.50'],
  ['AMOUNT-002', '.50', '$0.50'],
  ['AMOUNT-003', '0.01', '$0.01'],
  ['AMOUNT-003', '999999999.99', '$999,999,999.99'],
] as const;

const rejectedAmounts = [
  ['AMOUNT-004', ''],
  ['AMOUNT-004', '   '],
  ['AMOUNT-004', '0'],
  ['AMOUNT-004', '0.00'],
  ['AMOUNT-004', '000'],
  ['AMOUNT-004', '-1'],
  ['AMOUNT-005', '.'],
  ['AMOUNT-005', '1.'],
  ['AMOUNT-005', '1.234'],
  ['AMOUNT-006', '1,000'],
  ['AMOUNT-006', '$1'],
  ['AMOUNT-006', '+1'],
  ['AMOUNT-006', '1e2'],
  ['AMOUNT-007', 'abc'],
  ['AMOUNT-007', 'NaN'],
  ['AMOUNT-007', 'Infinity'],
  ['AMOUNT-008', '1000000000.00'],
  ['AMOUNT-008', '1000000000'],
] as const;

async function submitDraft(
  user: ReturnType<typeof userEvent.setup>,
  overrides: { amount?: string; category?: string; date?: string; note?: string } = {},
) {
  const values = {
    amount: '25.50',
    category: 'food',
    date: '2026-10-15',
    note: '  Keep this note exactly  ',
    ...overrides,
  };
  const amount = screen.getByLabelText('Amount (USD)');
  await user.clear(amount);
  if (values.amount) {
    await user.type(amount, values.amount);
  }
  await user.selectOptions(screen.getByLabelText('Category'), values.category);
  fireEvent.change(screen.getByLabelText('Date'), {
    target: { value: values.date },
  });
  const note = screen.getByLabelText('Note (optional)');
  await user.clear(note);
  if (values.note) {
    await user.type(note, values.note);
  }
  await user.click(screen.getByRole('button', { name: 'Add expense' }));
}

beforeEach(() => {
  vi.useFakeTimers({ now: buildFixedLocalClock(), toFake: ['Date'] });
  render(<App />);
  fireEvent.change(screen.getByLabelText('Month'), {
    target: { value: '2026-10' },
  });
});

afterEach(() => {
  vi.useRealTimers();
});

describe('add expense amount validation', () => {
  it.each(acceptedAmounts)(
    '%s: accepts %j and renders exact USD',
    async (_caseId, amount, expected) => {
      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      await submitDraft(user, { amount });

      expect(screen.getByLabelText('Monthly total')).toHaveTextContent(expected);
      expect(screen.getByLabelText('Food total')).toHaveTextContent(expected);
      expect(
        within(screen.getByRole('list', { name: 'Transactions' })).getAllByRole(
          'listitem',
        ),
      ).toHaveLength(1);
      expect(
        screen.getByRole('status', { name: 'Expense status' }),
      ).toHaveTextContent('Expense added.');
    },
  );

  it.each(rejectedAmounts)(
    '%s: rejects %j with focus, associated announced error, and no mutation',
    async (_caseId, amount) => {
      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      const validNote = '  Preserve this valid note  ';
      await submitDraft(user, { amount, note: validNote });

      const amountControl = screen.getByLabelText('Amount (USD)');
      expect(amountControl).toHaveFocus();
      expect(amountControl).toHaveAttribute('aria-invalid', 'true');
      const describedBy = amountControl.getAttribute('aria-describedby');
      expect(describedBy).toBeTruthy();
      const error = document.getElementById(describedBy!);
      expect(error).toHaveAttribute('role', 'alert');
      expect(error).toHaveTextContent(
        'Enter a valid USD amount greater than zero with no more than two decimal places.',
      );
      expect(error).toHaveTextContent('!');
      expect(screen.getByLabelText('Note (optional)')).toHaveValue(validNote);
      expect(screen.getByLabelText('Monthly total')).toHaveTextContent('$0.00');
      expect(
        within(screen.getByRole('list', { name: 'Transactions' })).queryAllByRole(
          'listitem',
        ),
      ).toHaveLength(0);
    },
  );
});

describe('add expense core behavior', () => {
  it('CORE-002: opens on the fixed current local month', () => {
    expect(screen.getByLabelText('Month')).toHaveValue('2026-10');
  });

  it('CORE-003: adds every category and calculates each total independently', async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    const categories = ['food', 'transport', 'housing', 'entertainment', 'other'];
    for (const [index, category] of categories.entries()) {
      await submitDraft(user, {
        amount: String(index + 1),
        category,
        note: '',
      });
    }

    for (const [index, category] of categories.entries()) {
      const label = `${category[0]!.toUpperCase()}${category.slice(1)} total`;
      expect(screen.getByLabelText(label)).toHaveTextContent(
        `$${index + 1}.00`,
      );
    }
    expect(screen.getByLabelText('Monthly total')).toHaveTextContent('$15.00');
    const ids = within(screen.getByRole('list', { name: 'Transactions' }))
      .getAllByRole('listitem')
      .map((item) => item.getAttribute('data-expense-id'));
    expect(ids.every((id) => id && id.trim().length > 0)).toBe(true);
    expect(new Set(ids).size).toBe(5);
  });

  it('CORE-004: accepts an omitted note and preserves exact nonblank note text', async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    const exactNote = '  Keep  this note exactly  ';
    await submitDraft(user, { note: '' });
    await submitDraft(user, { amount: '2.00', note: exactNote });

    const items = within(screen.getByRole('list', { name: 'Transactions' }))
      .getAllByRole('listitem');
    expect(items).toHaveLength(2);
    expect(items.some((item) => item.textContent?.includes(exactNote))).toBe(true);
    expect(
      items.filter((item) => item.querySelector('.transaction-note')),
    ).toHaveLength(1);
  });

  it('CORE-001/004: focuses amount before date when both are invalid', async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    await submitDraft(user, { amount: '0', date: '2023-02-29', note: 'Valid note' });
    expect(screen.getByLabelText('Amount (USD)')).toHaveFocus();
    expect(screen.getByLabelText('Date')).toHaveAttribute('aria-invalid', 'true');
    expect(screen.getByLabelText('Note (optional)')).toHaveValue('Valid note');
  });
});
