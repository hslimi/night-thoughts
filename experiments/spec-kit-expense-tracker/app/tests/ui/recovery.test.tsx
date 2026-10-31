import { fireEvent, render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import App from '../../src/App';
import { EXPENSES_STORAGE_KEY, type StorageLike } from '../../src/persistence/expenseStorage';
import { buildFixedLocalClock, buildValidExpense, buildVersion1Envelope } from '../fixtures/expenses';

interface FakeStorage extends StorageLike {
  raw: string | null;
  getItem: ReturnType<typeof vi.fn<(key: string) => string | null>>;
  setItem: ReturnType<typeof vi.fn<(key: string, value: string) => void>>;
  failWrites: boolean;
}

function createStorage(raw: string | null): FakeStorage {
  const storage: FakeStorage = {
    raw,
    failWrites: false,
    getItem: vi.fn((key: string) => {
      expect(key).toBe(EXPENSES_STORAGE_KEY);
      return storage.raw;
    }),
    setItem: vi.fn((key: string, value: string) => {
      expect(key).toBe(EXPENSES_STORAGE_KEY);
      if (storage.failWrites) {
        throw new DOMException('Storage is full', 'QuotaExceededError');
      }
      storage.raw = value;
    }),
  };
  return storage;
}

async function addExpense(user: ReturnType<typeof userEvent.setup>, amount = '25.50') {
  await user.type(screen.getByLabelText('Amount (USD)'), amount);
  fireEvent.change(screen.getByLabelText('Date'), { target: { value: '2026-10-15' } });
  await user.click(screen.getByRole('button', { name: 'Add expense' }));
}

function expectDialog() {
  const dialog = screen.getByRole('dialog', { name: /replace saved information/i });
  expect(dialog).toHaveAttribute('open');
  expect(dialog).toHaveAccessibleDescription(/irreversibly replace/i);
  expect(within(dialog).getByRole('button', { name: 'Cancel' })).toHaveFocus();
  expect(within(dialog).getByRole('button', { name: 'Confirm replacement' })).toBeInTheDocument();
  return dialog;
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

describe('guarded recovery replacements', () => {
  it('PERSIST-003/RECOVERY-001: readable malformed data is not written by Cancel or Escape', async () => {
    const raw = '{ malformed\n  "version":1,"expenses":[{"id":"looks-valid"}]';
    const storage = createStorage(raw);
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    render(<App storage={storage} />);

    expect(screen.getByLabelText('Monthly total')).toHaveTextContent('$0.00');
    expect(screen.queryByText('looks-valid')).not.toBeInTheDocument();
    const warning = screen.getByRole('alert', { name: 'Persistence status' });
    expect(warning).toHaveTextContent(/temporary/i);
    expect(warning).toHaveTextContent(/requires confirmation/i);
    expect(storage.setItem).not.toHaveBeenCalled();

    const startFresh = screen.getByRole('button', { name: 'Start fresh' });
    await user.click(startFresh);
    expectDialog();
    await user.click(screen.getByRole('button', { name: 'Cancel' }));
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    expect(startFresh).toHaveFocus();
    expect(storage.raw).toBe(raw);
    expect(storage.setItem).not.toHaveBeenCalled();
    expect(screen.getByRole('alert', { name: 'Persistence status' })).toBeInTheDocument();

    await user.click(startFresh);
    fireEvent(expectDialog(), new Event('cancel', { cancelable: true }));
    expect(storage.raw).toBe(raw);
    expect(storage.setItem).not.toHaveBeenCalled();
    expect(startFresh).toHaveFocus();
  });

  it('RECOVERY-002: confirmed start fresh writes exactly an empty version-1 envelope', async () => {
    const storage = createStorage('{bad json');
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    render(<App storage={storage} />);

    await user.click(screen.getByRole('button', { name: 'Start fresh' }));
    await user.click(screen.getByRole('button', { name: 'Confirm replacement' }));

    expect(storage.setItem).toHaveBeenCalledTimes(1);
    expect(JSON.parse(storage.raw!)).toEqual({ version: 1, expenses: [] });
    expect(screen.queryByRole('alert', { name: 'Persistence status' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Start fresh' })).not.toBeInTheDocument();
    expect(screen.getByLabelText('Monthly total')).toHaveTextContent('$0.00');
  });

  it('RECOVERY-003: failed start fresh retains guarded empty memory and never retries automatically', async () => {
    const storage = createStorage('{bad json');
    storage.failWrites = true;
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    render(<App storage={storage} />);

    await user.click(screen.getByRole('button', { name: 'Start fresh' }));
    await user.click(screen.getByRole('button', { name: 'Confirm replacement' }));

    expect(storage.setItem).toHaveBeenCalledTimes(1);
    expect(storage.raw).toBe('{bad json');
    expect(screen.getByLabelText('Monthly total')).toHaveTextContent('$0.00');
    const warning = screen.getByRole('alert', { name: 'Persistence status' });
    expect(warning).toHaveTextContent(/replacement failed/i);
    expect(warning).toHaveTextContent(/not durably saved/i);
    expect(screen.queryByRole('status', { name: 'Persistence status' })).not.toBeInTheDocument();
  });

  it('RECOVERY-004: cancelling the first replacement retains guarded added work without writing', async () => {
    const raw = '{bad json';
    const storage = createStorage(raw);
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    render(<App storage={storage} />);

    await addExpense(user);
    expectDialog();
    const item = within(screen.getByRole('list', { name: 'Transactions' })).getByRole('listitem');
    expect(item).toHaveTextContent('$25.50');
    await user.click(screen.getByRole('button', { name: 'Cancel' }));
    expect(screen.getByRole('button', { name: 'Add expense' })).toHaveFocus();
    expect(item).toHaveTextContent('$25.50');
    expect(storage.raw).toBe(raw);
    expect(storage.setItem).not.toHaveBeenCalled();

    await addExpense(user, '2.00');
    fireEvent(expectDialog(), new Event('cancel', { cancelable: true }));
    expect(storage.raw).toBe(raw);
    expect(storage.setItem).not.toHaveBeenCalled();
    expect(screen.getByLabelText('Monthly total')).toHaveTextContent('$27.50');
    expect(screen.getByRole('alert', { name: 'Persistence status' })).toBeInTheDocument();
  });

  it('RECOVERY-005: confirmed first replacement saves the complete current collection and clears recovery', async () => {
    const storage = createStorage('{bad json');
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    const first = render(<App storage={storage} />);

    await addExpense(user);
    await user.click(screen.getByRole('button', { name: 'Confirm replacement' }));
    await addExpense(user, '2.00');

    const envelope = JSON.parse(storage.raw!) as ReturnType<typeof buildVersion1Envelope>;
    expect(envelope.version).toBe(1);
    expect(envelope.expenses).toHaveLength(2);
    expect(envelope.expenses.map((expense) => expense.amountCents).sort((a, b) => a - b)).toEqual([200, 2550]);
    expect(screen.queryByRole('alert', { name: 'Persistence status' })).not.toBeInTheDocument();

    first.unmount();
    render(<App storage={storage} />);
    expect(screen.getByLabelText('Monthly total')).toHaveTextContent('$27.50');
    expect(within(screen.getByRole('list', { name: 'Transactions' })).getAllByRole('listitem')).toHaveLength(2);
  });

  it.each(['quota', 'serialization'] as const)('RECOVERY-006: %s failure retains current guarded work without success or retry', async (failure) => {
    const storage = createStorage('{bad json');
    if (failure === 'quota') {
      storage.failWrites = true;
    } else {
      vi.spyOn(JSON, 'stringify').mockImplementation(() => {
        throw new Error('Serialization failed');
      });
    }
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    render(<App storage={storage} />);

    await addExpense(user);
    await user.click(screen.getByRole('button', { name: 'Confirm replacement' }));

    expect(storage.setItem).toHaveBeenCalledTimes(failure === 'quota' ? 1 : 0);
    expect(storage.raw).toBe('{bad json');
    expect(screen.getByLabelText('Monthly total')).toHaveTextContent('$25.50');
    expect(screen.getByRole('alert', { name: 'Persistence status' })).toHaveTextContent(/replacement failed/i);
    expect(screen.queryByRole('status', { name: 'Persistence status' })).not.toBeInTheDocument();
  });

  it('PERSIST-007/RECOVERY-007: unreadable storage follows cancellation, failure, and success without inspection claims', async () => {
    const storage = createStorage(null);
    storage.getItem.mockImplementation(() => {
      throw new Error('Access denied');
    });
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    render(<App storage={storage} />);

    const warning = screen.getByRole('alert', { name: 'Persistence status' });
    expect(warning).toHaveTextContent(/unreadable/i);
    expect(warning).not.toHaveTextContent(/raw|byte|unchanged|inspect|compar|pars(?:e|ed|ing)|JSON|malformed/i);

    const startFresh = screen.getByRole('button', { name: 'Start fresh' });
    await user.click(startFresh);
    await user.click(screen.getByRole('button', { name: 'Cancel' }));
    expect(storage.setItem).not.toHaveBeenCalled();
    expect(startFresh).toHaveFocus();

    storage.failWrites = true;
    await addExpense(user);
    await user.click(screen.getByRole('button', { name: 'Confirm replacement' }));
    expect(storage.setItem).toHaveBeenCalledTimes(1);
    expect(screen.getByLabelText('Monthly total')).toHaveTextContent('$25.50');
    expect(screen.getByRole('alert', { name: 'Persistence status' })).toHaveTextContent(/replacement failed/i);

    storage.failWrites = false;
    await user.click(screen.getByRole('button', { name: 'Start fresh' }));
    await user.click(screen.getByRole('button', { name: 'Confirm replacement' }));
    expect(storage.setItem).toHaveBeenCalledTimes(2);
    expect(JSON.parse(storage.raw!)).toEqual(buildVersion1Envelope([]));
    expect(screen.queryByRole('alert', { name: 'Persistence status' })).not.toBeInTheDocument();
  });

  it('PERSIST-002: restores valid records exactly once without altering their values', () => {
    const records = [
      buildValidExpense({ id: 'one', amountCents: 1, note: '  exact note  ' }),
      buildValidExpense({ id: 'two', amountCents: 99999999999, category: 'housing', date: '2026-10-31' }),
    ];
    const storage = createStorage(JSON.stringify(buildVersion1Envelope(records)));
    render(<App storage={storage} />);

    expect(storage.getItem).toHaveBeenCalledTimes(1);
    expect(screen.getByLabelText('Monthly total')).toHaveTextContent('$1,000,000,000.00');
    const items = within(screen.getByRole('list', { name: 'Transactions' })).getAllByRole('listitem');
    expect(items).toHaveLength(2);
    expect(items[0]).toHaveAttribute('data-expense-id', 'two');
    expect(items[1]?.querySelector('.transaction-note')?.textContent).toBe('  exact note  ');
    expect(screen.queryByRole('alert', { name: 'Persistence status' })).not.toBeInTheDocument();
  });
});
