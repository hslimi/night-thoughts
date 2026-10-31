import { fireEvent, render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import App from '../../src/App';
import type { StorageLike } from '../../src/persistence/expenseStorage';
import {
  buildFixedLocalClock,
  buildValidExpense,
  buildVersion1Envelope,
} from '../fixtures/expenses';

const records = [
  buildValidExpense({ id: 'newest', amountCents: 100, category: 'food', date: '2026-10-20', note: 'Newest record' }),
  buildValidExpense({ id: 'target', amountCents: 123456, category: 'transport', date: '2026-10-15', note: 'Delete target' }),
  buildValidExpense({ id: 'oldest', amountCents: 300, category: 'housing', date: '2026-10-10', note: 'Oldest record' }),
];

function createStorage(initialRecords = records) {
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

function transaction(id: string) {
  return within(screen.getByRole('list', { name: 'Transactions' }))
    .getAllByRole('listitem')
    .find((item) => item.getAttribute('data-expense-id') === id)!;
}

function visibleIds() {
  return within(screen.getByRole('list', { name: 'Transactions' }))
    .queryAllByRole('listitem')
    .map((item) => item.getAttribute('data-expense-id'));
}

async function requestDeletion(user: ReturnType<typeof userEvent.setup>, id = 'target') {
  const requester = within(transaction(id)).getByRole('button', { name: 'Delete expense' });
  await user.click(requester);
  const dialog = screen.getByRole('dialog', { name: 'Delete expense?' });
  expect(dialog).toHaveAttribute('open');
  return { dialog, requester };
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

describe('delete confirmation', () => {
  it('DELETE-001/MONEY-003: identifies exact fixed-locale values and starts contained focus on Cancel', async () => {
    const storage = createStorage();
    const raw = storage.raw;
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    render(<App initialExpenses={records} storage={storage} />);

    const { dialog } = await requestDeletion(user);
    expect(dialog).toHaveAccessibleDescription(/\$1,234\.56/);
    expect(dialog).toHaveAccessibleDescription(/transport/);
    expect(dialog).toHaveAccessibleDescription(/2026-10-15/);
    expect(dialog).toHaveAccessibleDescription(/no undo|cannot be undone/i);
    const cancel = within(dialog).getByRole('button', { name: 'Cancel' });
    const confirm = within(dialog).getByRole('button', { name: 'Confirm deletion' });
    expect(cancel).toHaveFocus();
    await user.tab({ shift: true });
    expect(confirm).toHaveFocus();
    await user.tab();
    expect(cancel).toHaveFocus();
    expect(visibleIds()).toEqual(['newest', 'target', 'oldest']);
    expect(storage.raw).toBe(raw);
    expect(storage.setItem).not.toHaveBeenCalled();
  });

  it.each(['Cancel', 'Escape'] as const)('DELETE-002: %s makes no mutation or write and restores the requester', async (method) => {
    const storage = createStorage();
    const raw = storage.raw;
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    render(<App initialExpenses={records} storage={storage} />);
    const { dialog, requester } = await requestDeletion(user);

    if (method === 'Cancel') await user.click(within(dialog).getByRole('button', { name: 'Cancel' }));
    else fireEvent(dialog, new Event('cancel', { cancelable: true }));

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    expect(requester).toHaveFocus();
    expect(visibleIds()).toEqual(['newest', 'target', 'oldest']);
    expect(screen.getByLabelText('Monthly total')).toHaveTextContent('$1,238.56');
    expect(storage.raw).toBe(raw);
    expect(storage.setItem).not.toHaveBeenCalled();
  });

  it('DELETE-003: confirms only the target, recalculates, and focuses the next visible edit requester', async () => {
    const storage = createStorage();
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    render(<App initialExpenses={records} storage={storage} />);
    const { dialog } = await requestDeletion(user);
    await user.click(within(dialog).getByRole('button', { name: 'Confirm deletion' }));

    expect(visibleIds()).toEqual(['newest', 'oldest']);
    expect(screen.getByLabelText('Monthly total')).toHaveTextContent('$4.00');
    expect(screen.getByLabelText('Transport total')).toHaveTextContent('$0.00');
    expect(within(transaction('oldest')).getByRole('button', { name: 'Edit expense' })).toHaveFocus();
    expect(JSON.parse(storage.raw).expenses.map((expense: { id: string }) => expense.id)).toEqual(['newest', 'oldest']);
    expect(screen.queryByRole('button', { name: /undo/i })).not.toBeInTheDocument();
  });

  it('DELETE-003: focuses the previous visible edit requester when no following result remains', async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    render(<App initialExpenses={records} storage={createStorage()} />);
    const { dialog } = await requestDeletion(user, 'oldest');
    await user.click(within(dialog).getByRole('button', { name: 'Confirm deletion' }));

    expect(visibleIds()).toEqual(['newest', 'target']);
    expect(within(transaction('target')).getByRole('button', { name: 'Edit expense' })).toHaveFocus();
  });

  it('DELETE-003: focuses Add expense when no unfiltered result remains', async () => {
    const only = [records[1]!];
    const storage = createStorage(only);
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    render(<App initialExpenses={only} storage={storage} />);
    const { dialog } = await requestDeletion(user);
    await user.click(within(dialog).getByRole('button', { name: 'Confirm deletion' }));

    expect(visibleIds()).toEqual([]);
    expect(screen.getByLabelText('Monthly total')).toHaveTextContent('$0.00');
    expect(screen.getByRole('button', { name: 'Add expense' })).toHaveFocus();
    expect(JSON.parse(storage.raw)).toEqual({ version: 1, expenses: [] });
    expect(screen.queryByRole('button', { name: /undo/i })).not.toBeInTheDocument();
  });
});
