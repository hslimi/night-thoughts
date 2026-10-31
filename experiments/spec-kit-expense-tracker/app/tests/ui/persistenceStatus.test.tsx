import { fireEvent, render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import App from '../../src/App';
import type { StorageLike } from '../../src/persistence/expenseStorage';
import { buildFixedLocalClock, buildValidExpense, buildVersion1Envelope } from '../fixtures/expenses';

function createStorage(expenses = [buildValidExpense()]) {
  const storage: StorageLike & {
    raw: string;
    failWrites: boolean;
    getItem: ReturnType<typeof vi.fn<() => string>>;
    setItem: ReturnType<typeof vi.fn<(key: string, value: string) => void>>;
  } = {
    raw: JSON.stringify(buildVersion1Envelope(expenses)),
    failWrites: false,
    getItem: vi.fn(() => storage.raw),
    setItem: vi.fn((_key: string, value: string) => {
      if (storage.failWrites) {
        throw new Error('Storage became unavailable');
      }
      storage.raw = value;
    }),
  };
  return storage;
}

async function addExpense(user: ReturnType<typeof userEvent.setup>, amount: string, note: string) {
  const amountControl = screen.getByLabelText('Amount (USD)');
  await user.clear(amountControl);
  await user.type(amountControl, amount);
  fireEvent.change(screen.getByLabelText('Date'), { target: { value: '2026-10-15' } });
  const noteControl = screen.getByLabelText('Note (optional)');
  await user.clear(noteControl);
  await user.type(noteControl, note);
  await user.click(screen.getByRole('button', { name: 'Add expense' }));
}

beforeEach(() => {
  vi.useFakeTimers({ now: buildFixedLocalClock(), toFake: ['Date'] });
});

afterEach(() => {
  vi.restoreAllMocks();
  vi.useRealTimers();
});

describe('ordinary persistence status', () => {
  it('PERSIST-001: missing data starts ready and empty without recovery or unsaved warnings', () => {
    const storage = createStorage();
    storage.raw = null as unknown as string;
    render(<App storage={storage} />);

    expect(screen.getByLabelText('Monthly total')).toHaveTextContent('$0.00');
    expect(screen.queryByRole('alert', { name: 'Persistence status' })).not.toBeInTheDocument();
    expect(screen.queryByRole('status', { name: 'Persistence status' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Start fresh' })).not.toBeInTheDocument();
  });

  it('PERSIST-008/013: failed add stays visibly unsaved and a later save persists all retained work before clearing the warning', async () => {
    const storage = createStorage();
    storage.failWrites = true;
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    const first = render(<App storage={storage} />);

    await addExpense(user, '2.00', 'Retained after failure');
    expect(screen.getByLabelText('Monthly total')).toHaveTextContent('$27.50');
    const warning = screen.getByRole('alert', { name: 'Persistence status' });
    expect(warning).toHaveTextContent(/add expense/i);
    expect(warning).toHaveTextContent(/not durably saved/i);
    expect(warning).toHaveTextContent(/only in memory/i);
    expect(warning).toHaveTextContent('!');
    expect(JSON.parse(storage.raw).expenses).toHaveLength(1);

    storage.failWrites = false;
    await addExpense(user, '3.00', 'Later successful save');
    expect(screen.queryByRole('alert', { name: 'Persistence status' })).not.toBeInTheDocument();
    const saved = JSON.parse(storage.raw) as ReturnType<typeof buildVersion1Envelope>;
    expect(saved.expenses).toHaveLength(3);
    expect(saved.expenses.map((expense) => expense.note)).toEqual(
      expect.arrayContaining(['Fixture expense', 'Retained after failure', 'Later successful save']),
    );

    first.unmount();
    render(<App storage={storage} />);
    expect(screen.getByLabelText('Monthly total')).toHaveTextContent('$30.50');
    expect(within(screen.getByRole('list', { name: 'Transactions' })).getAllByRole('listitem')).toHaveLength(3);
    expect(screen.queryByRole('alert', { name: 'Persistence status' })).not.toBeInTheDocument();
  });

  it('PERSIST-011: serialization failure retains optimistic work without a durable-success claim or fallback write', async () => {
    const storage = createStorage();
    const stringify = vi.spyOn(JSON, 'stringify').mockImplementation(() => {
      throw new Error('Cannot serialize');
    });
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    render(<App storage={storage} />);
    stringify.mockImplementation(() => {
      throw new Error('Cannot serialize');
    });

    await addExpense(user, '4.00', 'Serialization failure');
    expect(screen.getByLabelText('Monthly total')).toHaveTextContent('$29.50');
    expect(storage.setItem).not.toHaveBeenCalled();
    const warning = screen.getByRole('alert', { name: 'Persistence status' });
    expect(warning).toHaveTextContent(/not durably saved/i);
    expect(warning).not.toHaveTextContent(/saved successfully|all changes are durable/i);
  });

  it('PERSIST-012: a mid-session access exception retains changes and a subsequent failure leaves the warning visible', async () => {
    const storage = createStorage();
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    render(<App storage={storage} />);
    storage.failWrites = true;

    await addExpense(user, '1.25', 'First failure');
    const warning = screen.getByRole('alert', { name: 'Persistence status' });
    expect(warning).toHaveTextContent(/not durably saved/i);
    await addExpense(user, '2.25', 'Second failure');

    expect(screen.getByLabelText('Monthly total')).toHaveTextContent('$29.00');
    expect(screen.getByRole('alert', { name: 'Persistence status' })).toHaveTextContent(/not durably saved/i);
    expect(storage.setItem).toHaveBeenCalledTimes(2);
    expect(JSON.parse(storage.raw).expenses).toHaveLength(1);
  });
});
