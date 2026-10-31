import { useLayoutEffect, useRef, useState, type FormEvent } from 'react';
import { getCurrentLocalDate } from '../domain/dates';
import {
  CATEGORIES,
  type CreateExpenseResult,
  type Expense,
  type ExpenseDraft,
  type ExpenseDraftErrors,
  type ExpenseField,
} from '../domain/expense';
import StatusMessage from './StatusMessage';

interface ExpenseFormProps {
  editingExpense: Expense | null;
  onAdd: (draft: ExpenseDraft) => CreateExpenseResult;
  onEdit: (id: string, draft: ExpenseDraft) => CreateExpenseResult;
  onCancelEdit: () => void;
}

function initialDraft(): ExpenseDraft {
  return {
    amount: '',
    category: 'food',
    date: getCurrentLocalDate(),
    note: '',
  };
}

function amountInputValue(amountCents: number): string {
  return `${Math.floor(amountCents / 100)}.${String(amountCents % 100).padStart(2, '0')}`;
}

export default function ExpenseForm({
  editingExpense,
  onAdd,
  onEdit,
  onCancelEdit,
}: ExpenseFormProps) {
  const [draft, setDraft] = useState<ExpenseDraft>(initialDraft);
  const [errors, setErrors] = useState<ExpenseDraftErrors>({});
  const [status, setStatus] = useState('');
  const amountRef = useRef<HTMLInputElement>(null);
  const categoryRef = useRef<HTMLSelectElement>(null);
  const dateRef = useRef<HTMLInputElement>(null);

  useLayoutEffect(() => {
    setErrors({});
    setStatus('');
    if (editingExpense) {
      setDraft({
        amount: amountInputValue(editingExpense.amountCents),
        category: editingExpense.category,
        date: editingExpense.date,
        note: editingExpense.note ?? '',
      });
      amountRef.current?.focus();
    } else {
      setDraft(initialDraft());
    }
  }, [editingExpense]);

  function updateField<Field extends keyof ExpenseDraft>(
    field: Field,
    value: ExpenseDraft[Field],
  ) {
    setDraft((current) => ({ ...current, [field]: value }));
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setStatus('');
    const result = editingExpense
      ? onEdit(editingExpense.id, draft)
      : onAdd(draft);
    if (!result.ok) {
      setErrors(result.errors);
      const firstInvalid = (['amount', 'category', 'date'] as const).find(
        (field) => result.errors[field],
      );
      const refs: Record<ExpenseField, HTMLElement | null> = {
        amount: amountRef.current,
        category: categoryRef.current,
        date: dateRef.current,
      };
      if (firstInvalid) {
        refs[firstInvalid]?.focus();
      }
      return;
    }

    setErrors({});
    if (editingExpense) {
      return;
    }
    setDraft((current) => ({ ...current, amount: '', note: '' }));
    setStatus('Expense added.');
  }

  return (
    <section className="panel expense-form-panel" aria-labelledby="add-expense-heading">
      <div className="section-heading">
        <p className="eyebrow">{editingExpense ? 'Correct transaction' : 'New transaction'}</p>
        <h2 id="add-expense-heading">{editingExpense ? 'Edit expense' : 'Add expense'}</h2>
        <p>
          {editingExpense
            ? 'Update this purchase using the same validation as a new expense.'
            : 'Record a purchase using its local calendar date.'}
        </p>
      </div>
      <form noValidate onSubmit={handleSubmit}>
        <div className="field">
          <label htmlFor="expense-amount">Amount (USD)</label>
          <input
            ref={amountRef}
            id="expense-amount"
            name="amount"
            type="text"
            inputMode="decimal"
            autoComplete="off"
            placeholder="0.00"
            value={draft.amount}
            onChange={(event) => updateField('amount', event.target.value)}
            aria-invalid={errors.amount ? true : undefined}
            aria-describedby={errors.amount ? 'expense-amount-error' : undefined}
          />
          {errors.amount && (
            <span className="field-error" id="expense-amount-error" role="alert">
              <span aria-hidden="true">! </span>
              {errors.amount}
            </span>
          )}
        </div>

        <div className="field-row">
          <div className="field">
            <label htmlFor="expense-category">Category</label>
            <select
              ref={categoryRef}
              id="expense-category"
              name="category"
              value={draft.category}
              onChange={(event) => updateField('category', event.target.value)}
              aria-invalid={errors.category ? true : undefined}
              aria-describedby={errors.category ? 'expense-category-error' : undefined}
            >
              {CATEGORIES.map((category) => (
                <option key={category} value={category}>
                  {category}
                </option>
              ))}
            </select>
            {errors.category && (
              <span className="field-error" id="expense-category-error" role="alert">
                <span aria-hidden="true">! </span>
                {errors.category}
              </span>
            )}
          </div>

          <div className="field">
            <label htmlFor="expense-date">Date</label>
            <input
              ref={dateRef}
              id="expense-date"
              name="date"
              type="date"
              value={draft.date}
              onChange={(event) => updateField('date', event.target.value)}
              aria-invalid={errors.date ? true : undefined}
              aria-describedby={errors.date ? 'expense-date-error' : undefined}
            />
            {errors.date && (
              <span className="field-error" id="expense-date-error" role="alert">
                <span aria-hidden="true">! </span>
                {errors.date}
              </span>
            )}
          </div>
        </div>

        <div className="field">
          <label htmlFor="expense-note">Note (optional)</label>
          <textarea
            id="expense-note"
            name="note"
            rows={3}
            value={draft.note}
            onChange={(event) => updateField('note', event.target.value)}
            placeholder="What was this expense for?"
          />
        </div>

        <div className="expense-form__actions">
          <button id="expense-form-submit" className="primary-button" type="submit">
            {editingExpense ? 'Save changes' : 'Add expense'}
          </button>
          {editingExpense && (
            <button type="button" onClick={onCancelEdit}>
              Cancel edit
            </button>
          )}
        </div>
        {status && (
          <StatusMessage message={status} tone="success" label="Expense status" />
        )}
      </form>
    </section>
  );
}
