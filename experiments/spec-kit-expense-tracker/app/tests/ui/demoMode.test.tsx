import { act, fireEvent, render, renderHook, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import App from '../../src/App';
import { isDemoMode } from '../../src/demo/demoData';
import type { StorageLike } from '../../src/persistence/expenseStorage';
import { useExpenseStore } from '../../src/state/useExpenseStore';
import { buildExpenseDraft, buildFixedLocalClock, buildValidExpense } from '../fixtures/expenses';

function createStorage() {
  return {
    getItem: vi.fn(() => null),
    setItem: vi.fn(),
    removeItem: vi.fn(),
    clear: vi.fn(),
  };
}

type MockStorage = ReturnType<typeof createStorage>;

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

function expectBaseline() {
  expect(screen.getByRole('status', { name: 'Demo mode' })).toHaveTextContent(/fictional demo data/i);
  expect(screen.getByLabelText('Month')).toHaveValue('2026-10');
  expect(screen.getByLabelText('Category filter')).toHaveValue('all');
  expect(screen.getByLabelText('Sort by')).toHaveValue('date');
  expect(screen.getByLabelText('Sort direction')).toHaveValue('desc');
  expect(screen.getByLabelText('Monthly total')).toHaveTextContent('$1,732.65');
  expect(screen.getByLabelText('Food total')).toHaveTextContent('$122.75');
  expect(screen.getByLabelText('Transport total')).toHaveTextContent('$50.90');
  expect(screen.getByLabelText('Housing total')).toHaveTextContent('$1,450.00');
  expect(screen.getByLabelText('Entertainment total')).toHaveTextContent('$24.00');
  expect(screen.getByLabelText('Other total')).toHaveTextContent('$85.00');
  expect(visibleIds()).toEqual([
    'demo-008', 'demo-007', 'demo-006', 'demo-005',
    'demo-004', 'demo-003', 'demo-002', 'demo-001',
  ]);
}

function expectNoStorage(storage: MockStorage, addEventListener: ReturnType<typeof vi.spyOn>) {
  expect(storage.getItem).not.toHaveBeenCalled();
  expect(storage.setItem).not.toHaveBeenCalled();
  expect(storage.removeItem).not.toHaveBeenCalled();
  expect(storage.clear).not.toHaveBeenCalled();
  expect(addEventListener.mock.calls.some((call: unknown[]) => call[0] === 'storage')).toBe(false);
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

describe('DEMO-001/002: activation and baseline', () => {
  it.each([
    ['?demo=1', true],
    ['?source=x&demo=1', true],
    ['?demo=1&demo=0', true],
    ['?demo=0&demo=1', false],
    ['?demo=01', false],
    ['?demo=true', false],
    ['?Demo=1', false],
    ['', false],
  ])('uses only the first exact demo value for %s', (search, demo) => {
    const storage = createStorage();
    const view = render(<App demo={isDemoMode(search)} initialExpenses={[]} storage={storage} />);

    expect(screen.queryByRole('status', { name: 'Demo mode' }) !== null).toBe(demo);
    view.unmount();
  });

  it('renders the fixed labeled baseline independently of injected normal records', () => {
    const storage = createStorage();
    const listeners = vi.spyOn(window, 'addEventListener');
    render(<App demo initialExpenses={[buildValidExpense({ id: 'real-only' })]} storage={storage} />);

    expectBaseline();
    expect(screen.queryByText('Fixture expense')).not.toBeInTheDocument();
    expect(screen.queryByRole('alert', { name: 'Persistence status' })).not.toBeInTheDocument();
    expectNoStorage(storage, listeners);
  });
});

describe('DEMO-003/004: interactions and fresh activation', () => {
  it('supports validation, add, edit, confirmed deletion, months, filter, and sort only in memory', async () => {
    const storage = createStorage();
    const listeners = vi.spyOn(window, 'addEventListener');
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    render(<App demo storage={storage} />);

    await user.type(screen.getByLabelText('Amount (USD)'), '0');
    fireEvent.change(screen.getByLabelText('Date'), { target: { value: '2026-10-22' } });
    await user.click(screen.getByRole('button', { name: 'Add expense' }));
    expect(screen.getByLabelText('Amount (USD)')).toHaveFocus();
    expect(screen.getByRole('alert')).toHaveTextContent(/valid USD amount/i);
    expect(screen.getByLabelText('Monthly total')).toHaveTextContent('$1,732.65');

    const amount = screen.getByLabelText('Amount (USD)');
    await user.clear(amount);
    await user.type(amount, '10.01');
    await user.type(screen.getByLabelText('Note (optional)'), 'Demo addition');
    await user.click(screen.getByRole('button', { name: 'Add expense' }));
    expect(screen.getByLabelText('Monthly total')).toHaveTextContent('$1,742.66');
    expect(screen.getByText('Demo addition')).toBeInTheDocument();

    await user.click(within(transaction('demo-008')).getByRole('button', { name: 'Edit expense' }));
    await user.clear(amount);
    await user.type(amount, '40.00');
    await user.selectOptions(screen.getByLabelText('Category', { exact: true }), 'other');
    await user.click(screen.getByRole('button', { name: 'Save changes' }));
    expect(within(transaction('demo-008')).getByText('$40.00')).toBeInTheDocument();
    expect(screen.getByLabelText('Other total')).toHaveTextContent('$125.00');

    await user.click(within(transaction('demo-007')).getByRole('button', { name: 'Delete expense' }));
    expect(screen.getByRole('dialog', { name: 'Delete expense?' })).toHaveTextContent('$67.20');
    await user.click(screen.getByRole('button', { name: 'Confirm deletion' }));
    expect(screen.queryByText('Dinner with friends')).not.toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Month'), { target: { value: '2026-09' } });
    expect(visibleIds()).toEqual(['demo-009']);
    expect(screen.getByLabelText('Monthly total')).toHaveTextContent('$20.00');
    fireEvent.change(screen.getByLabelText('Month'), { target: { value: '2026-11' } });
    expect(visibleIds()).toEqual(['demo-010']);
    expect(screen.getByLabelText('Monthly total')).toHaveTextContent('$30.00');
    fireEvent.change(screen.getByLabelText('Month'), { target: { value: '2026-10' } });
    await user.selectOptions(screen.getByLabelText('Category filter'), 'food');
    expect(visibleIds()).toHaveLength(3);
    expect(visibleIds().slice(1)).toEqual(['demo-005', 'demo-002']);
    expect(screen.getByLabelText('Monthly total')).toHaveTextContent('$1,683.06');
    await user.selectOptions(screen.getByLabelText('Category filter'), 'all');
    await user.selectOptions(screen.getByLabelText('Sort by'), 'amount');
    await user.selectOptions(screen.getByLabelText('Sort direction'), 'asc');
    expect(screen.getByRole('list', { name: 'Transactions' }).querySelector('li')).toHaveTextContent('Demo addition');
    expect(screen.queryByRole('alert', { name: 'Persistence status' })).not.toBeInTheDocument();
    expectNoStorage(storage, listeners);
  });

  it('resets records, preferences, forms, dialogs, and status on every fresh activation and keeps normal data separate', async () => {
    const storage = createStorage();
    const listeners = vi.spyOn(window, 'addEventListener');
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    const realExpense = buildValidExpense({ id: 'real-only', note: 'Real record only' });
    const demoView = render(<App demo storage={storage} />);

    await user.selectOptions(screen.getByLabelText('Category filter'), 'housing');
    await user.selectOptions(screen.getByLabelText('Sort direction'), 'asc');
    await user.type(screen.getByLabelText('Note (optional)'), 'Unsaved demo form text');
    await user.click(within(transaction('demo-001')).getByRole('button', { name: 'Delete expense' }));
    expect(screen.getByRole('dialog', { name: 'Delete expense?' })).toBeInTheDocument();
    demoView.unmount();

    const normalView = render(<App initialExpenses={[realExpense]} storage={storage} />);
    expect(screen.queryByRole('status', { name: 'Demo mode' })).not.toBeInTheDocument();
    expect(screen.queryByText(/October rent|Airport train/)).not.toBeInTheDocument();
    expect(screen.getByText('Real record only')).toBeInTheDocument();
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    expect(screen.getByLabelText('Note (optional)')).toHaveValue('');
    normalView.unmount();

    render(<App demo storage={storage} />);
    expectBaseline();
    expect(screen.getByLabelText('Note (optional)')).toHaveValue('');
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    expect(screen.queryByRole('status', { name: 'Expense status' })).not.toBeInTheDocument();
    expectNoStorage(storage, listeners);
  });
});

describe('demo store isolation', () => {
  it('branches before loading and mutates separate memory without any storage access', () => {
    const storage = createStorage();
    const { result } = renderHook(() => useExpenseStore(undefined, storage as StorageLike, true));

    expect(result.current.expenses.map((expense) => expense.id)).toHaveLength(10);
    expect(result.current.selectedMonth).toBe('2026-10');
    act(() => {
      const added = result.current.addExpense(buildExpenseDraft({ amount: '1.01' }));
      expect(added.ok).toBe(true);
    });
    act(() => result.current.deleteExpense('demo-001'));

    expect(result.current.expenses).toHaveLength(10);
    expect(result.current.expenses.some((expense) => expense.id === 'demo-001')).toBe(false);
    expect(result.current.recovery).toBeNull();
    expect(result.current.persistenceIssue).toBeNull();
    expect(storage.getItem).not.toHaveBeenCalled();
    expect(storage.setItem).not.toHaveBeenCalled();
  });
});
