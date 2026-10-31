import AxeBuilder from '@axe-core/playwright';
import { expect, test, type Page } from '@playwright/test';
import {
  addExpense,
  coreExpenses,
  expectFocusVisibleAndUnobscured,
  openEdit,
  openNormal,
  openUnsafeTotals,
  requestDeletion,
  resetNormal,
  saveEdit,
  selectMonth,
  setFailWrites,
  transaction,
  transactions,
} from './coreFlowUtils';

async function expectWCAG22AA(page: Page) {
  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
    .analyze();
  expect(
    results.violations.map((violation) => ({
      id: violation.id,
      impact: violation.impact,
      description: violation.description,
      nodes: violation.nodes.map((node) => ({ target: node.target, failure: node.failureSummary })),
    })),
  ).toEqual([]);
}

test.use({ timezoneId: 'America/Los_Angeles' });

test.beforeEach(async ({ page }) => {
  await page.clock.install({ time: new Date('2026-10-31T12:00:00-07:00') });
});

test('A11Y initial missing/valid dashboard, transaction results, and empty-month action', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('status', { name: 'Empty month', exact: true })).toBeVisible();
  await expect(page.getByRole('status', { name: 'Transaction results', exact: true })).toContainText('0 expenses shown');
  await expectWCAG22AA(page);

  await openNormal(page);
  await expect(transactions(page)).toHaveCount(3);
  await expect(page.getByRole('status', { name: 'Transaction results', exact: true })).toContainText('3 expenses shown, sorted by date descending.');
  await expectWCAG22AA(page);

  await selectMonth(page, '2026-11');
  const empty = page.getByRole('status', { name: 'Empty month', exact: true });
  await expect(empty).toContainText('No expenses for this month');
  await expectWCAG22AA(page);
  await empty.getByRole('button', { name: 'Add expense for this month', exact: true }).press('Enter');
  await expectFocusVisibleAndUnobscured(page.getByLabel('Amount (USD)', { exact: true }));
});

test('A11Y invalid and valid add expose associated feedback and preserve valid input', async ({ page }) => {
  await openNormal(page);
  const amount = page.getByLabel('Amount (USD)', { exact: true });
  await amount.fill('0');
  await page.getByLabel('Date', { exact: true }).fill('2026-10-22');
  await page.getByLabel('Note (optional)', { exact: true }).fill('Keep this valid note');
  await page.getByRole('button', { name: 'Add expense', exact: true }).press('Enter');

  await expectFocusVisibleAndUnobscured(amount);
  await expect(amount).toHaveAttribute('aria-invalid', 'true');
  const errorId = await amount.getAttribute('aria-describedby');
  expect(errorId).toBeTruthy();
  const error = page.locator(`#${errorId}`);
  await expect(error).toHaveRole('alert');
  await expect(error).toContainText(/valid USD amount/i);
  await expect(error).toContainText('!');
  await expect(page.getByLabel('Note (optional)', { exact: true })).toHaveValue('Keep this valid note');
  await expectWCAG22AA(page);

  await amount.fill('25.50');
  await page.getByRole('button', { name: 'Add expense', exact: true }).press('Enter');
  await expect(page.getByRole('status', { name: 'Expense status', exact: true })).toContainText('Expense added.');
  await expect(page.getByText('Keep this valid note', { exact: true })).toBeVisible();
  await expect(page.getByLabel('Monthly total', { exact: true })).toHaveText('$1,264.06');
  await expectWCAG22AA(page);
});

test('A11Y invalid, same-month, and cross-month edit states preserve semantics and focus', async ({ page }) => {
  await openNormal(page);
  await openEdit(page);
  const amount = page.getByLabel('Amount (USD)', { exact: true });
  await amount.fill('1.234');
  await saveEdit(page);
  await expectFocusVisibleAndUnobscured(amount);
  await expect(amount).toHaveAttribute('aria-invalid', 'true');
  await expect(page.locator(`#${await amount.getAttribute('aria-describedby')}`)).toHaveRole('alert');
  await expect(transaction(page, 'core-target')).toContainText('$1,234.56');
  await expectWCAG22AA(page);

  await amount.fill('25.50');
  await saveEdit(page);
  await expectFocusVisibleAndUnobscured(
    transaction(page, 'core-target').getByRole('button', { name: 'Edit expense', exact: true }),
  );
  await expect(page.getByRole('status', { name: 'Expense status', exact: true })).toContainText('Expense updated.');
  await expect(page.getByLabel('Monthly total', { exact: true })).toHaveText('$29.50');
  await expectWCAG22AA(page);

  await openEdit(page);
  await page.getByLabel('Date', { exact: true }).fill('2026-11-01');
  await saveEdit(page);
  await expectFocusVisibleAndUnobscured(page.getByLabel('Month', { exact: true }));
  await expect(page.getByRole('status', { name: 'Expense status', exact: true })).toContainText('Expense moved to 2026-11.');
  await expect(page.getByLabel('Monthly total', { exact: true })).toHaveText('$4.00');
  await expectWCAG22AA(page);
});

test('A11Y deletion dialog, cancellation, and deterministic post-deletion focus', async ({ page }) => {
  await openNormal(page);
  let deletion = await requestDeletion(page);
  await expect(deletion.dialog).toContainText('$1,234.56 transport expense dated 2026-10-15');
  await expect(deletion.dialog).toContainText(/no undo/i);
  await expectFocusVisibleAndUnobscured(
    deletion.dialog.getByRole('button', { name: 'Cancel', exact: true }),
  );
  await expectWCAG22AA(page);
  await deletion.dialog.getByRole('button', { name: 'Cancel', exact: true }).press('Enter');
  await expectFocusVisibleAndUnobscured(deletion.requester);

  deletion = await requestDeletion(page);
  await deletion.dialog.getByRole('button', { name: 'Confirm deletion', exact: true }).press('Enter');
  await expect(transaction(page, 'core-target')).toHaveCount(0);
  await expectFocusVisibleAndUnobscured(
    transaction(page, 'core-oldest').getByRole('button', { name: 'Edit expense', exact: true }),
  );
  await expectWCAG22AA(page);

  await resetNormal(page, [coreExpenses[0]!, coreExpenses[1]!]);
  await page.getByLabel('Category filter', { exact: true }).selectOption('food');
  deletion = await requestDeletion(page, 'core-newest');
  await deletion.dialog.getByRole('button', { name: 'Confirm deletion', exact: true }).press('Enter');
  await expect(page.getByRole('status', { name: 'No matching expenses', exact: true })).toBeVisible();
  await expectFocusVisibleAndUnobscured(page.getByRole('button', { name: 'Clear filter', exact: true }));
  await expectWCAG22AA(page);
});

test('A11Y category no-match, clear, filtered edit, and exact sort result states', async ({ page }) => {
  await openNormal(page);
  const filter = page.getByLabel('Category filter', { exact: true });
  await filter.selectOption('entertainment');
  await expect(page.getByRole('status', { name: 'No matching expenses', exact: true })).toBeVisible();
  await expectWCAG22AA(page);
  await page.getByRole('button', { name: 'Clear filter', exact: true }).press('Enter');
  await expectFocusVisibleAndUnobscured(filter);
  await expect(transactions(page)).toHaveCount(3);

  await filter.selectOption('food');
  await openEdit(page, 'core-newest');
  await page.getByLabel('Category', { exact: true }).selectOption('other');
  await saveEdit(page);
  await expectFocusVisibleAndUnobscured(filter);
  await expect(page.getByRole('status', { name: 'Expense status', exact: true })).toContainText(/no longer matches/i);
  await expectWCAG22AA(page);

  await filter.selectOption('all');
  await page.getByLabel('Sort by', { exact: true }).selectOption('amount');
  await page.getByLabel('Sort direction', { exact: true }).selectOption('asc');
  await expect(transactions(page).nth(0)).toHaveAttribute('data-expense-id', 'core-newest');
  await expect(transactions(page).nth(1)).toHaveAttribute('data-expense-id', 'core-oldest');
  await expect(transactions(page).nth(2)).toHaveAttribute('data-expense-id', 'core-target');
  await expect(page.getByRole('status', { name: 'Transaction results', exact: true })).toContainText('sorted by amount ascending.');
  await expectWCAG22AA(page);
});

test('A11Y readable recovery, replacement dialog, failure, and successful start fresh', async ({ page }) => {
  await openNormal(page, [], { raw: '{broken readable data' });
  const warning = page.getByRole('alert', { name: 'Persistence status', exact: true });
  await expect(warning).toContainText(/invalid/i);
  await expect(warning).toContainText(/temporary/i);
  await expect(warning).toContainText('!');
  await expectWCAG22AA(page);

  const startFresh = page.getByRole('button', { name: 'Start fresh', exact: true });
  await startFresh.focus();
  await startFresh.press('Enter');
  let dialog = page.getByRole('dialog', { name: 'Replace saved information?', exact: true });
  await expect(dialog).toContainText(/irreversibly replace/i);
  await expectFocusVisibleAndUnobscured(dialog.getByRole('button', { name: 'Cancel', exact: true }));
  await expectWCAG22AA(page);
  await dialog.getByRole('button', { name: 'Cancel', exact: true }).press('Enter');
  await expectFocusVisibleAndUnobscured(startFresh);

  await setFailWrites(page, true);
  await startFresh.press('Enter');
  await dialog.getByRole('button', { name: 'Confirm replacement', exact: true }).press('Enter');
  await expect(warning).toContainText(/replacement failed/i);
  await expect(warning).toContainText(/not durably saved/i);
  await expectWCAG22AA(page);

  await setFailWrites(page, false);
  await startFresh.press('Enter');
  await dialog.getByRole('button', { name: 'Confirm replacement', exact: true }).press('Enter');
  await expect(warning).toHaveCount(0);
  await expect(page.getByRole('status', { name: 'Empty month', exact: true })).toBeVisible();
  await expectWCAG22AA(page);
});

test('A11Y unreadable recovery and first-replacement-save dialog retain work and focus', async ({ page }) => {
  await openNormal(page, [], { unreadable: true });
  const warning = page.getByRole('alert', { name: 'Persistence status', exact: true });
  await expect(warning).toContainText(/unreadable/i);
  await expect(warning).not.toContainText(/raw|byte|inspect|compar|JSON/i);
  await expectWCAG22AA(page);

  await addExpense(page, { amount: '7.10', date: '2026-10-18', note: 'Guarded accessible work' });
  const dialog = page.getByRole('dialog', { name: 'Replace saved information?', exact: true });
  await expect(dialog).toContainText(/complete current in-memory collection/i);
  await expectFocusVisibleAndUnobscured(dialog.getByRole('button', { name: 'Cancel', exact: true }));
  await expectWCAG22AA(page);
  await dialog.getByRole('button', { name: 'Cancel', exact: true }).press('Enter');
  await expectFocusVisibleAndUnobscured(page.getByRole('button', { name: 'Add expense', exact: true }));
  await expect(page.getByText('Guarded accessible work', { exact: true })).toBeVisible();

  await addExpense(page, { amount: '2.50', date: '2026-10-19', note: 'Second guarded work' });
  await dialog.getByRole('button', { name: 'Confirm replacement', exact: true }).press('Enter');
  await expect(warning).toHaveCount(0);
  await expect(transactions(page)).toHaveCount(2);
  await expectWCAG22AA(page);
});

test('A11Y failed add, edit, and delete saves announce task-associated non-color warnings', async ({ page }) => {
  await openNormal(page);
  await setFailWrites(page, true);
  const warning = page.getByRole('alert', { name: 'Persistence status', exact: true });

  await addExpense(page, { amount: '10.01', date: '2026-10-21', note: 'Unsaved accessible add' });
  await expect(warning).toContainText(/add expense/i);
  await expect(warning).toContainText(/not durably saved/i);
  await expect(warning).toContainText('!');
  await expectWCAG22AA(page);

  await openEdit(page);
  await page.getByLabel('Amount (USD)', { exact: true }).fill('99.99');
  await saveEdit(page);
  await expect(warning).toContainText(/edit expense/i);
  await expectWCAG22AA(page);

  const deletion = await requestDeletion(page, 'core-oldest');
  await deletion.dialog.getByRole('button', { name: 'Confirm deletion', exact: true }).press('Enter');
  await expect(warning).toContainText(/delete expense/i);
  await expect(page.getByText('Unsaved accessible add', { exact: true })).toBeVisible();
  await expectWCAG22AA(page);
});

test('A11Y unsafe monthly/category totals remain announced and operable', async ({ page }) => {
  test.setTimeout(180000);
  await openUnsafeTotals(page);
  await expect(page.getByLabel('Monthly total', { exact: true })).toHaveText('Unavailable');
  await expect(page.getByLabel('Food total', { exact: true })).toHaveText('Unavailable');
  await expect(page.getByLabel('Transport total', { exact: true })).toHaveText('$1.00');
  const calculationError = page.getByRole('alert').filter({ hasText: 'Some totals cannot be calculated exactly.' });
  await expect(calculationError).toBeVisible();
  await expect(calculationError).toContainText('Your expenses are unchanged.');
  await expect(calculationError).toContainText('!');
  await expectWCAG22AA(page);
});

test('A11Y labeled demo supports validation, edit, deletion, month, filter, and sort states', async ({ page }) => {
  await page.goto('/?demo=1');
  await expect(page.getByRole('status', { name: 'Demo mode', exact: true })).toContainText(/fictional demo data/i);
  await expect(page.getByRole('alert', { name: 'Persistence status', exact: true })).toHaveCount(0);
  await expectWCAG22AA(page);

  await page.getByLabel('Amount (USD)', { exact: true }).fill('0');
  await page.getByRole('button', { name: 'Add expense', exact: true }).press('Enter');
  await expectFocusVisibleAndUnobscured(page.getByLabel('Amount (USD)', { exact: true }));
  await expectWCAG22AA(page);

  await transaction(page, 'demo-008').getByRole('button', { name: 'Edit expense', exact: true }).press('Enter');
  await page.getByLabel('Amount (USD)', { exact: true }).fill('40.00');
  await saveEdit(page);
  await expect(transaction(page, 'demo-008')).toContainText('$40.00');
  await expectWCAG22AA(page);

  await transaction(page, 'demo-007').getByRole('button', { name: 'Delete expense', exact: true }).press('Enter');
  const dialog = page.getByRole('dialog', { name: 'Delete expense?', exact: true });
  await expectFocusVisibleAndUnobscured(dialog.getByRole('button', { name: 'Cancel', exact: true }));
  await expectWCAG22AA(page);
  await dialog.getByRole('button', { name: 'Confirm deletion', exact: true }).press('Enter');

  await selectMonth(page, '2026-09');
  await expect(transaction(page, 'demo-009')).toBeVisible();
  await selectMonth(page, '2026-10');
  await page.getByLabel('Category filter', { exact: true }).selectOption('food');
  await expect(transactions(page)).toHaveCount(2);
  await page.getByLabel('Category filter', { exact: true }).selectOption('all');
  await page.getByLabel('Sort by', { exact: true }).selectOption('amount');
  await page.getByLabel('Sort direction', { exact: true }).selectOption('asc');
  await expect(page.getByRole('status', { name: 'Transaction results', exact: true })).toContainText('sorted by amount ascending.');
  await expectWCAG22AA(page);
});
