import { useEffect, useState } from 'react';
import ConfirmDialog from './components/ConfirmDialog';
import Dashboard from './components/Dashboard';
import ExpenseForm from './components/ExpenseForm';
import StatusMessage from './components/StatusMessage';
import type { Expense, ExpenseDraft } from './domain/expense';
import { formatUSD } from './domain/money';
import type { StorageLike } from './persistence/expenseStorage';
import { useExpenseStore } from './state/useExpenseStore';

interface AppProps {
  initialExpenses?: Expense[];
  storage?: StorageLike;
  demo?: boolean;
}

type FocusRequest =
  | { kind: 'edit'; id: string }
  | { kind: 'month' }
  | { kind: 'add' }
  | { kind: 'amount' }
  | { kind: 'filter' }
  | { kind: 'clear-filter' };

export default function App({ initialExpenses, storage, demo = false }: AppProps) {
  const store = useExpenseStore(initialExpenses, storage, demo);
  const [editingExpense, setEditingExpense] = useState<Expense | null>(null);
  const [deletion, setDeletion] = useState<Expense | null>(null);
  const [editStatus, setEditStatus] = useState('');
  const [focusRequest, setFocusRequest] = useState<FocusRequest | null>(null);
  const persistenceStatus =
    !demo && (store.recovery !== null || store.persistenceIssue !== null)
      ? { recovery: store.recovery, issue: store.persistenceIssue }
      : null;

  useEffect(() => {
    if (focusRequest === null) {
      return;
    }
    let target: HTMLElement | null;
    if (focusRequest.kind === 'edit') {
      target = document.getElementById(`edit-expense-${focusRequest.id}`);
    } else {
      const targetIds = {
        month: 'selected-month',
        add: 'expense-form-submit',
        amount: 'expense-amount',
        filter: 'category-filter',
        'clear-filter': 'clear-filter',
      } as const;
      target = document.getElementById(targetIds[focusRequest.kind]);
    }
    target?.focus();
    setFocusRequest(null);
  }, [focusRequest]);

  function startEdit(expense: Expense) {
    setEditStatus('');
    setEditingExpense(expense);
  }

  function cancelEdit() {
    if (editingExpense) {
      setFocusRequest({ kind: 'edit', id: editingExpense.id });
    }
    setEditingExpense(null);
  }

  function startAdd() {
    setEditStatus('');
    setEditingExpense(null);
    setFocusRequest({ kind: 'amount' });
  }

  function addExpense(draft: ExpenseDraft) {
    setEditStatus('');
    return store.addExpense(draft);
  }

  function editExpense(id: string, draft: ExpenseDraft) {
    const result = store.editExpense(id, draft);
    if (!result.ok) {
      return result;
    }

    const destinationMonth = result.expense.date.slice(0, 7);
    setEditingExpense(null);
    if (destinationMonth !== store.selectedMonth) {
      setEditStatus(`Expense moved to ${destinationMonth}.`);
      setFocusRequest({ kind: 'month' });
    } else if (
      store.transactionPreferences.category !== 'all' &&
      result.expense.category !== store.transactionPreferences.category
    ) {
      setEditStatus(
        'Expense updated. It no longer matches the active category filter.',
      );
      setFocusRequest({ kind: 'filter' });
    } else {
      setEditStatus('Expense updated.');
      setFocusRequest({ kind: 'edit', id });
    }
    return result;
  }

  function confirmDeletion() {
    if (!deletion) {
      return;
    }
    const orderedExpenses = store.visibleExpenses;
    const deletedIndex = orderedExpenses.findIndex(
      (expense) => expense.id === deletion.id,
    );
    const focusExpense =
      orderedExpenses[deletedIndex + 1] ?? orderedExpenses[deletedIndex - 1];

    store.deleteExpense(deletion.id);
    setDeletion(null);
    setEditingExpense((current) =>
      current?.id === deletion.id ? null : current,
    );
    setFocusRequest(
      focusExpense
        ? { kind: 'edit', id: focusExpense.id }
        : store.transactionPreferences.category === 'all'
          ? { kind: 'add' }
          : { kind: 'clear-filter' },
    );
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <p className="brand-mark" aria-hidden="true">PT</p>
          <p className="eyebrow">Personal finance, made simple</p>
          <h1>Personal Expense Tracker</h1>
          <p className="app-intro">
            Capture everyday spending and understand each month at a glance.
          </p>
          {demo && (
            <StatusMessage
              label="Demo mode"
              message="Fictional demo data. Changes are temporary and never use real saved expenses."
            />
          )}
        </div>
      </header>
      <main className="app-layout">
        {editStatus && (
          <div className="app-feedback">
            <StatusMessage message={editStatus} tone="success" label="Expense status" />
          </div>
        )}
        <ExpenseForm
          editingExpense={editingExpense}
          onAdd={addExpense}
          onEdit={editExpense}
          onCancelEdit={cancelEdit}
        />
        <Dashboard
          selectedMonth={store.selectedMonth}
          onMonthChange={store.setSelectedMonth}
          summary={store.summary}
          visibleExpenses={store.visibleExpenses}
          transactionPreferences={store.transactionPreferences}
          onTransactionPreferencesChange={store.setTransactionPreferences}
          onAddFromEmpty={startAdd}
          persistenceStatus={persistenceStatus}
          onStartFresh={store.requestStartFresh}
          onEdit={startEdit}
          onDelete={setDeletion}
        />
      </main>
      <ConfirmDialog
        open={store.replacement !== null}
        title="Replace saved information?"
        description={
          store.replacement === 'start-fresh'
            ? 'This will irreversibly replace all existing saved information with an empty collection. The replaced information cannot be recovered afterward.'
            : 'This will irreversibly replace all existing saved information with the complete current in-memory collection. The replaced information cannot be recovered afterward.'
        }
        confirmLabel="Confirm replacement"
        onCancel={store.cancelReplacement}
        onConfirm={store.confirmReplacement}
      />
      <ConfirmDialog
        open={deletion !== null}
        title="Delete expense?"
        description={
          deletion
            ? `Delete ${formatUSD(deletion.amountCents)} ${deletion.category} expense dated ${deletion.date}? Confirmed deletion cannot be undone once durable; there is no undo.`
            : ''
        }
        confirmLabel="Confirm deletion"
        onCancel={() => setDeletion(null)}
        onConfirm={confirmDeletion}
      />
    </div>
  );
}
