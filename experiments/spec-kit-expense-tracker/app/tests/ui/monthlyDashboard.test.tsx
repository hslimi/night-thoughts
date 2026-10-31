import { fireEvent, render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import App from '../../src/App';
import Dashboard from '../../src/components/Dashboard';
import type { MonthlySummary } from '../../src/domain/dashboard';
import { buildFixedLocalClock, buildValidExpense } from '../fixtures/expenses';

const boundaryRecords = [
  buildValidExpense({ id: 'sep', amountCents: 999, date: '2026-09-30' }),
  buildValidExpense({ id: 'first', amountCents: 100, category: 'food', date: '2026-10-01' }),
  buildValidExpense({ id: 'last', amountCents: 200, category: 'transport', date: '2026-10-31' }),
  buildValidExpense({ id: 'nov', amountCents: 888, date: '2026-11-01' }),
];

beforeEach(() => {
  vi.useFakeTimers({ now: buildFixedLocalClock(), toFake: ['Date'] });
});

afterEach(() => {
  vi.useRealTimers();
});

describe('monthly dashboard', () => {
  it('DATE-001/004: shows only selected-month transactions and exact totals', () => {
    render(<App initialExpenses={boundaryRecords} />);
    const list = screen.getByRole('list', { name: 'Transactions' });
    expect(within(list).getAllByRole('listitem').map((item) => item.getAttribute('data-expense-id'))).toEqual([
      'last',
      'first',
    ]);
    expect(screen.getByLabelText('Monthly total')).toHaveTextContent('$3.00');
    expect(screen.getByLabelText('Food total')).toHaveTextContent('$1.00');
    expect(screen.getByLabelText('Transport total')).toHaveTextContent('$2.00');
    expect(screen.getByLabelText('Housing total')).toHaveTextContent('$0.00');
    expect(screen.getByLabelText('Entertainment total')).toHaveTextContent('$0.00');
    expect(screen.getByLabelText('Other total')).toHaveTextContent('$0.00');

    fireEvent.change(screen.getByLabelText('Month'), {
      target: { value: '2026-11' },
    });
    expect(within(list).getAllByRole('listitem')).toHaveLength(1);
    expect(screen.getByLabelText('Monthly total')).toHaveTextContent('$8.88');
  });

  it('CORE-002: preserves the last valid month when the native control is cleared', () => {
    render(<App initialExpenses={boundaryRecords} />);
    const month = screen.getByLabelText('Month');
    expect(month).toHaveValue('2026-10');

    fireEvent.change(month, { target: { value: '' } });

    expect(month).toHaveValue('2026-10');
    expect(screen.getByLabelText('Monthly total')).toHaveTextContent('$3.00');
    expect(
      within(screen.getByRole('list', { name: 'Transactions' })).getAllByRole('listitem'),
    ).toHaveLength(2);
  });

  it('DATE-002: includes leap day and rejects an impossible date with associated focus', async () => {
    render(<App />);
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    await user.type(screen.getByLabelText('Amount (USD)'), '2.50');
    fireEvent.change(screen.getByLabelText('Date'), {
      target: { value: '2024-02-29' },
    });
    await user.click(screen.getByRole('button', { name: 'Add expense' }));
    fireEvent.change(screen.getByLabelText('Month'), {
      target: { value: '2024-02' },
    });
    expect(screen.getByLabelText('Monthly total')).toHaveTextContent('$2.50');

    await user.clear(screen.getByLabelText('Amount (USD)'));
    await user.type(screen.getByLabelText('Amount (USD)'), '3.00');
    fireEvent.change(screen.getByLabelText('Date'), {
      target: { value: '2023-02-29' },
    });
    await user.click(screen.getByRole('button', { name: 'Add expense' }));
    const date = screen.getByLabelText('Date');
    expect(date).toHaveFocus();
    expect(date).toHaveAttribute('aria-invalid', 'true');
    const error = document.getElementById(date.getAttribute('aria-describedby')!);
    expect(error).toHaveAttribute('role', 'alert');
    expect(error).toHaveTextContent('Enter a real local calendar date in YYYY-MM-DD format.');
    expect(screen.getByLabelText('Monthly total')).toHaveTextContent('$2.50');
  });

  it('DATE-003: keeps selected month unchanged after adding a future expense', async () => {
    render(<App />);
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    await user.type(screen.getByLabelText('Amount (USD)'), '12.34');
    fireEvent.change(screen.getByLabelText('Date'), {
      target: { value: '2027-01-15' },
    });
    await user.click(screen.getByRole('button', { name: 'Add expense' }));

    expect(screen.getByLabelText('Month')).toHaveValue('2026-10');
    expect(screen.getByLabelText('Monthly total')).toHaveTextContent('$0.00');
    expect(
      within(screen.getByRole('list', { name: 'Transactions' })).queryAllByRole('listitem'),
    ).toHaveLength(0);
    fireEvent.change(screen.getByLabelText('Month'), {
      target: { value: '2027-01' },
    });
    expect(screen.getByLabelText('Monthly total')).toHaveTextContent('$12.34');
    expect(screen.getByLabelText('Food total')).toHaveTextContent('$12.34');
  });

  it('OVERFLOW-001: announces calculation errors instead of unsafe numeric totals', () => {
    const summary: MonthlySummary = {
      month: '2026-10',
      total: { ok: false, error: 'unsafe-total' },
      categoryTotals: {
        food: { ok: false, error: 'unsafe-total' },
        transport: { ok: true, cents: 0 },
        housing: { ok: true, cents: 0 },
        entertainment: { ok: true, cents: 0 },
        other: { ok: true, cents: 0 },
      },
      monthExpenses: [buildValidExpense()],
    };
    render(
      <Dashboard
        selectedMonth="2026-10"
        onMonthChange={() => {}}
        summary={summary}
      />,
    );

    expect(screen.getByLabelText('Monthly total')).toHaveTextContent('Unavailable');
    expect(screen.getByLabelText('Monthly total')).not.toHaveTextContent('$');
    expect(screen.getByLabelText('Food total')).toHaveTextContent('Unavailable');
    expect(screen.getByRole('alert')).toHaveTextContent(
      'Some totals cannot be calculated exactly. Your expenses are unchanged.',
    );
    expect(screen.getByRole('alert')).toHaveTextContent('!');
    expect(screen.getByRole('list', { name: 'Transactions' })).toBeInTheDocument();
  });
});
