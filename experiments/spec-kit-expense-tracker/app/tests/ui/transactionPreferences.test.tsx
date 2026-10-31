import { fireEvent, render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import App from '../../src/App';
import type { StorageLike } from '../../src/persistence/expenseStorage';
import {
  buildFixedLocalClock,
  buildValidExpense,
  buildVersion1Envelope,
  type Expense,
} from '../fixtures/expenses';

const records = [
  buildValidExpense({ id: 'tie-a', amountCents: 200, category: 'food', date: '2026-10-10' }),
  buildValidExpense({ id: 'tie-c', amountCents: 100, category: 'transport', date: '2026-10-10' }),
  buildValidExpense({ id: 'tie-b', amountCents: 200, category: 'housing', date: '2026-10-10' }),
  buildValidExpense({ id: 'older', amountCents: 50, category: 'entertainment', date: '2026-10-01' }),
  buildValidExpense({ id: 'newer', amountCents: 150, category: 'other', date: '2026-10-31' }),
];

function createStorage(initialRecords: Expense[]) {
  const storage: StorageLike & {
    raw: string;
    setItem: ReturnType<typeof vi.fn<(key: string, value: string) => void>>;
  } = {
    raw: JSON.stringify(buildVersion1Envelope(initialRecords)),
    getItem: vi.fn(() => storage.raw),
    setItem: vi.fn((_key: string, value: string) => {
      storage.raw = value;
    }),
  };
  return storage;
}

function visibleIds() {
  return within(screen.getByRole('list', { name: 'Transactions' }))
    .queryAllByRole('listitem')
    .map((item) => item.getAttribute('data-expense-id'));
}

function transaction(id: string) {
  return within(screen.getByRole('list', { name: 'Transactions' }))
    .getAllByRole('listitem')
    .find((item) => item.getAttribute('data-expense-id') === id)!;
}

function results() {
  return screen.getByRole('status', { name: 'Transaction results' });
}

beforeEach(() => {
  vi.useFakeTimers({ now: buildFixedLocalClock(), toFake: ['Date'] });
  if (!HTMLDialogElement.prototype.showModal) {
    HTMLDialogElement.prototype.showModal = function showModal() {
      this.setAttribute('open', '');
    };
  }
  if (!HTMLDialogElement.prototype.close) {
    HTMLDialogElement.prototype.close = function close() {
      this.removeAttribute('open');
    };
  }
});

afterEach(() => {
  vi.restoreAllMocks();
  vi.useRealTimers();
});

describe('transaction filtering and sorting', () => {
  it('FILTER-001: filters only the list, announces results, and preserves summaries and durable data', async () => {
    const storage = createStorage(records);
    const raw = storage.raw;
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    render(<App initialExpenses={records} storage={storage} />);

    expect(screen.getByLabelText('Category filter')).toHaveValue('all');
    expect(screen.getByLabelText('Sort by')).toHaveValue('date');
    expect(screen.getByLabelText('Sort direction')).toHaveValue('desc');
    expect(results()).toHaveTextContent('5 expenses shown');

    for (const [category, id, total] of [
      ['food', 'tie-a', 'Food total'],
      ['transport', 'tie-c', 'Transport total'],
      ['housing', 'tie-b', 'Housing total'],
      ['entertainment', 'older', 'Entertainment total'],
      ['other', 'newer', 'Other total'],
    ] as const) {
      await user.selectOptions(screen.getByLabelText('Category filter'), category);
      expect(visibleIds()).toEqual([id]);
      expect(results()).toHaveTextContent(`1 expense shown for ${category}`);
      expect(screen.getByLabelText('Monthly total')).toHaveTextContent('$7.00');
      expect(screen.getByLabelText(total)).not.toHaveTextContent('$0.00');
    }

    await user.selectOptions(screen.getByLabelText('Category filter'), 'all');
    expect(visibleIds()).toEqual(['newer', 'tie-a', 'tie-b', 'tie-c', 'older']);
    expect(results()).toHaveTextContent('5 expenses shown');
    expect(screen.getByLabelText('Monthly total')).toHaveTextContent('$7.00');
    expect(storage.raw).toBe(raw);
    expect(storage.setItem).not.toHaveBeenCalled();
  });

  it.each([
    ['date', 'asc', ['older', 'tie-a', 'tie-b', 'tie-c', 'newer']],
    ['date', 'desc', ['newer', 'tie-a', 'tie-b', 'tie-c', 'older']],
    ['amount', 'asc', ['older', 'tie-c', 'newer', 'tie-a', 'tie-b']],
    ['amount', 'desc', ['tie-a', 'tie-b', 'newer', 'tie-c', 'older']],
  ] as const)('SORT-001/002: %s %s has deterministic ID-ascending ties', async (sortField, sortDirection, expected) => {
    const storage = createStorage(records);
    const raw = storage.raw;
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    render(<App initialExpenses={records} storage={storage} />);

    await user.selectOptions(screen.getByLabelText('Sort by'), sortField);
    await user.selectOptions(screen.getByLabelText('Sort direction'), sortDirection);

    expect(visibleIds()).toEqual(expected);
    expect(results()).toHaveTextContent(`5 expenses shown, sorted by ${sortField} ${sortDirection === 'asc' ? 'ascending' : 'descending'}`);
    expect(screen.getByLabelText('Monthly total')).toHaveTextContent('$7.00');
    expect(storage.raw).toBe(raw);
    expect(storage.setItem).not.toHaveBeenCalled();
  });
});

describe('distinct empty states', () => {
  it('EMPTY-001: an empty month has a non-error add action that focuses Amount', async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    render(<App initialExpenses={records} storage={createStorage(records)} />);
    fireEvent.change(screen.getByLabelText('Month'), { target: { value: '2026-11' } });

    const empty = screen.getByRole('status', { name: 'Empty month' });
    expect(empty).toHaveTextContent('No expenses for this month');
    expect(empty).not.toHaveAttribute('role', 'alert');
    expect(screen.queryByRole('status', { name: 'No matching expenses' })).not.toBeInTheDocument();
    await user.click(within(empty).getByRole('button', { name: 'Add expense for this month' }));
    expect(screen.getByLabelText('Amount (USD)')).toHaveFocus();
  });

  it('FILTER-002/EMPTY-002: no matches differs from empty month and Clear filter restores results and focus', async () => {
    const onlyFood = [records[0]!, records[3]!];
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    render(<App initialExpenses={onlyFood} storage={createStorage(onlyFood)} />);
    await user.selectOptions(screen.getByLabelText('Category filter'), 'transport');

    const empty = screen.getByRole('status', { name: 'No matching expenses' });
    expect(empty).toHaveTextContent('No expenses match the selected category');
    expect(screen.queryByRole('status', { name: 'Empty month' })).not.toBeInTheDocument();
    expect(screen.queryByRole('alert', { name: 'No matching expenses' })).not.toBeInTheDocument();
    expect(screen.getByLabelText('Monthly total')).toHaveTextContent('$2.50');
    await user.click(within(empty).getByRole('button', { name: 'Clear filter' }));

    expect(visibleIds()).toEqual(['tie-a', 'older']);
    expect(results()).toHaveTextContent('2 expenses shown');
    expect(screen.getByLabelText('Category filter')).toHaveFocus();
  });
});

describe('integrated edit and deletion focus', () => {
  it('CORE-006: a same-month edit leaving the filter announces the result and focuses Category filter', async () => {
    const initial = [records[0]!, records[1]!];
    const storage = createStorage(initial);
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    render(<App initialExpenses={initial} storage={storage} />);
    await user.selectOptions(screen.getByLabelText('Category filter'), 'food');
    await user.click(within(transaction('tie-a')).getByRole('button', { name: 'Edit expense' }));
    await user.selectOptions(screen.getByLabelText('Category', { exact: true }), 'housing');
    await user.click(screen.getByRole('button', { name: 'Save changes' }));

    expect(visibleIds()).toEqual([]);
    expect(screen.getByRole('status', { name: 'Expense status' })).toHaveTextContent(/updated.*no longer matches.*category filter/i);
    expect(screen.getByLabelText('Category filter')).toHaveFocus();
    expect(screen.getByLabelText('Monthly total')).toHaveTextContent('$3.00');
    expect(screen.getByLabelText('Food total')).toHaveTextContent('$0.00');
    expect(screen.getByLabelText('Housing total')).toHaveTextContent('$2.00');
    expect(screen.getByRole('status', { name: 'No matching expenses' })).toBeInTheDocument();
  });

  it('CORE-006: a visible same-month edit restores its requester after resorting', async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    render(<App initialExpenses={records} storage={createStorage(records)} />);
    await user.selectOptions(screen.getByLabelText('Sort by'), 'amount');
    await user.selectOptions(screen.getByLabelText('Sort direction'), 'asc');
    await user.click(within(transaction('tie-c')).getByRole('button', { name: 'Edit expense' }));
    const amount = screen.getByLabelText('Amount (USD)');
    await user.clear(amount);
    await user.type(amount, '4.00');
    await user.click(screen.getByRole('button', { name: 'Save changes' }));

    expect(visibleIds()).toEqual(['older', 'newer', 'tie-a', 'tie-b', 'tie-c']);
    expect(within(transaction('tie-c')).getByRole('button', { name: 'Edit expense' })).toHaveFocus();
  });

  it('DELETE-005: deleting the last filtered result focuses Clear filter while hidden month data remains', async () => {
    const initial = [records[0]!, records[1]!];
    const storage = createStorage(initial);
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    render(<App initialExpenses={initial} storage={storage} />);
    await user.selectOptions(screen.getByLabelText('Category filter'), 'food');
    await user.click(within(transaction('tie-a')).getByRole('button', { name: 'Delete expense' }));
    await user.click(screen.getByRole('button', { name: 'Confirm deletion' }));

    expect(visibleIds()).toEqual([]);
    expect(screen.getByRole('status', { name: 'No matching expenses' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Clear filter' })).toHaveFocus();
    expect(screen.getByLabelText('Monthly total')).toHaveTextContent('$1.00');
    expect(screen.getByLabelText('Food total')).toHaveTextContent('$0.00');
    expect(screen.getByLabelText('Transport total')).toHaveTextContent('$1.00');
    expect(JSON.parse(storage.raw).expenses.map((expense: Expense) => expense.id)).toEqual(['tie-c']);
  });
});
