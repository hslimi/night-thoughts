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

const original = buildValidExpense({
  id: 'same-record-id',
  amountCents: 2550,
  category: 'food',
  date: '2026-10-15',
  note: 'Original note',
});

function createStorage() {
  const storage: StorageLike & {
    raw: string;
    setItem: ReturnType<typeof vi.fn<(key: string, value: string) => void>>;
  } = {
    raw: JSON.stringify(buildVersion1Envelope([original])),
    getItem: vi.fn(() => storage.raw),
    setItem: vi.fn((_key: string, value: string) => {
      storage.raw = value;
    }),
  };
  return storage;
}

function transaction(id = original.id) {
  return within(screen.getByRole('list', { name: 'Transactions' }))
    .getAllByRole('listitem')
    .find((item) => item.getAttribute('data-expense-id') === id)!;
}

async function openEdit(user: ReturnType<typeof userEvent.setup>) {
  await user.click(within(transaction()).getByRole('button', { name: 'Edit expense' }));
  expect(screen.getByRole('heading', { name: 'Edit expense' })).toBeInTheDocument();
  expect(screen.getByLabelText('Amount (USD)')).toHaveValue('25.50');
  expect(screen.getByLabelText('Category')).toHaveValue('food');
  expect(screen.getByLabelText('Date')).toHaveValue('2026-10-15');
  expect(screen.getByLabelText('Note (optional)')).toHaveValue('Original note');
}

async function replaceAmount(user: ReturnType<typeof userEvent.setup>, amount: string) {
  const control = screen.getByLabelText('Amount (USD)');
  await user.clear(control);
  if (amount) await user.type(control, amount);
}

beforeEach(() => {
  vi.useFakeTimers({ now: buildFixedLocalClock(), toFake: ['Date'] });
});

afterEach(() => {
  vi.restoreAllMocks();
  vi.useRealTimers();
});

describe('edit amount validation', () => {
  it.each(acceptedAmounts)('%s: accepts %j using the add parser and preserves identity', async (_caseId, amount, expected) => {
    const storage = createStorage();
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    render(<App initialExpenses={[original]} storage={storage} />);
    await openEdit(user);

    await replaceAmount(user, amount);
    await user.click(screen.getByRole('button', { name: 'Save changes' }));

    expect(transaction()).toHaveTextContent(expected);
    expect(screen.getByLabelText('Monthly total')).toHaveTextContent(expected);
    expect(within(transaction()).getByRole('button', { name: 'Edit expense' })).toHaveFocus();
    expect(JSON.parse(storage.raw).expenses).toHaveLength(1);
    expect(JSON.parse(storage.raw).expenses[0].id).toBe(original.id);
  });

  it.each(rejectedAmounts)('%s: rejects %j without changing the record or durable collection', async (_caseId, amount) => {
    const storage = createStorage();
    const raw = storage.raw;
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    render(<App initialExpenses={[original]} storage={storage} />);
    await openEdit(user);
    const exactNote = '  Preserve this valid edit note  ';
    const note = screen.getByLabelText('Note (optional)');
    await user.clear(note);
    await user.type(note, exactNote);

    await replaceAmount(user, amount);
    await user.click(screen.getByRole('button', { name: 'Save changes' }));

    const amountControl = screen.getByLabelText('Amount (USD)');
    expect(amountControl).toHaveFocus();
    expect(amountControl).toHaveAttribute('aria-invalid', 'true');
    const error = document.getElementById(amountControl.getAttribute('aria-describedby')!);
    expect(error).toHaveAttribute('role', 'alert');
    expect(error).toHaveTextContent('Enter a valid USD amount greater than zero with no more than two decimal places.');
    expect(note).toHaveValue(exactNote);
    expect(transaction()).toHaveTextContent('$25.50');
    expect(transaction()).toHaveTextContent('Original note');
    expect(screen.getByLabelText('Monthly total')).toHaveTextContent('$25.50');
    expect(storage.setItem).not.toHaveBeenCalled();
    expect(storage.raw).toBe(raw);
  });
});

describe('edit core behavior', () => {
  it('CORE-004/005: updates every field on the same ID and restores the visible requester', async () => {
    const storage = createStorage();
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    render(<App initialExpenses={[original]} storage={storage} />);
    await openEdit(user);

    await replaceAmount(user, '1234.56');
    await user.selectOptions(screen.getByLabelText('Category'), 'transport');
    fireEvent.change(screen.getByLabelText('Date'), { target: { value: '2026-10-20' } });
    const exactNote = '  Exact  edited note  ';
    const note = screen.getByLabelText('Note (optional)');
    await user.clear(note);
    await user.type(note, exactNote);
    await user.click(screen.getByRole('button', { name: 'Save changes' }));

    expect(transaction()).toHaveAttribute('data-expense-id', original.id);
    expect(transaction()).toHaveTextContent('$1,234.56');
    expect(transaction()).toHaveTextContent('transport');
    expect(transaction()).toHaveTextContent('2026-10-20');
    expect(transaction().querySelector('.transaction-note')?.textContent).toBe(exactNote);
    expect(screen.getByLabelText('Monthly total')).toHaveTextContent('$1,234.56');
    expect(screen.getByLabelText('Food total')).toHaveTextContent('$0.00');
    expect(screen.getByLabelText('Transport total')).toHaveTextContent('$1,234.56');
    expect(screen.getByLabelText('Month')).toHaveValue('2026-10');
    expect(within(transaction()).getByRole('button', { name: 'Edit expense' })).toHaveFocus();
    expect(JSON.parse(storage.raw).expenses).toEqual([
      {
        id: original.id,
        amountCents: 123456,
        category: 'transport',
        date: '2026-10-20',
        note: exactNote,
      },
    ]);
  });

  it.each([
    ['blank', '', null],
    ['whitespace-only', '   ', null],
    ['nonblank', '  Keep exactly  ', '  Keep exactly  '],
  ] as const)('CORE-004: edit accepts a %s note', async (_label, value, expected) => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    render(<App initialExpenses={[original]} storage={createStorage()} />);
    await openEdit(user);
    const note = screen.getByLabelText('Note (optional)');
    await user.clear(note);
    if (value) await user.type(note, value);
    await user.click(screen.getByRole('button', { name: 'Save changes' }));

    if (expected === null) expect(transaction().querySelector('.transaction-note')).toBeNull();
    else expect(transaction().querySelector('.transaction-note')?.textContent).toBe(expected);
    expect(transaction()).toHaveAttribute('data-expense-id', original.id);
  });

  it('CORE-005: invalid category and date retain the original and focus the first invalid field', async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    render(<App initialExpenses={[original]} storage={createStorage()} />);
    await openEdit(user);
    fireEvent.change(screen.getByLabelText('Category'), { target: { value: 'invalid' } });
    fireEvent.change(screen.getByLabelText('Date'), { target: { value: '2023-02-29' } });
    await user.click(screen.getByRole('button', { name: 'Save changes' }));

    expect(screen.getByLabelText('Category')).toHaveFocus();
    expect(screen.getByLabelText('Category')).toHaveAttribute('aria-invalid', 'true');
    expect(screen.getByLabelText('Date')).toHaveAttribute('aria-invalid', 'true');
    expect(transaction()).toHaveTextContent('$25.50');
    expect(transaction()).toHaveTextContent('2026-10-15');
    expect(screen.getByLabelText('Monthly total')).toHaveTextContent('$25.50');
  });

  it.each([
    ['September into October', '2026-09', '2026-09-30', '2026-10-01', '2026-10'],
    ['October into November', '2026-10', '2026-10-31', '2026-11-01', '2026-11'],
  ] as const)('CORE-005: moves a record from %s without changing the selected month', async (_label, initialMonth, initialDate, editedDate, destinationMonth) => {
    const record = { ...original, date: initialDate };
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    render(<App initialExpenses={[record]} storage={createStorage()} />);
    fireEvent.change(screen.getByLabelText('Month'), { target: { value: initialMonth } });
    await user.click(within(transaction()).getByRole('button', { name: 'Edit expense' }));
    fireEvent.change(screen.getByLabelText('Date'), { target: { value: editedDate } });
    await user.click(screen.getByRole('button', { name: 'Save changes' }));

    expect(screen.getByLabelText('Month')).toHaveValue(initialMonth);
    expect(screen.getByLabelText('Month')).toHaveFocus();
    expect(screen.getByRole('status', { name: 'Expense status' })).toHaveTextContent(new RegExp(`moved.*${destinationMonth}`, 'i'));
    expect(screen.getByLabelText('Monthly total')).toHaveTextContent('$0.00');
    expect(within(screen.getByRole('list', { name: 'Transactions' })).queryAllByRole('listitem')).toHaveLength(0);

    fireEvent.change(screen.getByLabelText('Month'), { target: { value: destinationMonth } });
    expect(screen.getByLabelText('Monthly total')).toHaveTextContent('$25.50');
    expect(transaction()).toHaveAttribute('data-expense-id', original.id);
    expect(transaction()).toHaveTextContent(editedDate);
  });
});
