import { expect, test, type Page } from '@playwright/test';

const storageKey = 'personal-expense-tracker:expenses:v1';
const seedMarker = 'edit-delete-spec:seeded';

type Expense = {
  id: string;
  amountCents: number;
  category: 'food' | 'transport' | 'housing' | 'entertainment' | 'other';
  date: string;
  note?: string;
};

declare global {
  interface Window {
    __editDeleteSpec: {
      failWrites: boolean;
      writes: number;
      writeValues: string[];
    };
  }
}

const records: Expense[] = [
  { id: 'newest', amountCents: 100, category: 'food', date: '2026-10-20', note: 'Newest record' },
  { id: 'target', amountCents: 123456, category: 'transport', date: '2026-10-15', note: 'Edit or delete target' },
  { id: 'oldest', amountCents: 300, category: 'housing', date: '2026-10-10', note: 'Oldest record' },
];

function envelope(expenses: Expense[]) {
  return JSON.stringify({ version: 1, expenses });
}

async function openTracker(page: Page, initialRecords = records) {
  await page.addInitScript(
    ({ key, marker, raw }) => {
      const storage = window.localStorage;
      if (window.sessionStorage.getItem(marker) !== 'yes') {
        storage.setItem(key, raw);
        window.sessionStorage.setItem(marker, 'yes');
      }
      const probe = { failWrites: false, writes: 0, writeValues: [] as string[] };
      window.__editDeleteSpec = probe;
      const originalSetItem = Storage.prototype.setItem;
      Storage.prototype.setItem = function (itemKey, value) {
        if (this === storage && itemKey === key) {
          probe.writes += 1;
          probe.writeValues.push(String(value));
          if (probe.failWrites) throw new DOMException('Injected write failure', 'QuotaExceededError');
        }
        return originalSetItem.call(this, itemKey, value);
      };
    },
    { key: storageKey, marker: seedMarker, raw: envelope(initialRecords) },
  );
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Personal Expense Tracker' })).toBeVisible();
}

function transaction(page: Page, id: string) {
  return page.locator(`li[data-expense-id="${id}"]`);
}

function transactions(page: Page) {
  return page.getByRole('list', { name: 'Transactions' }).getByRole('listitem');
}

async function openEdit(page: Page, id = 'target') {
  const requester = transaction(page, id).getByRole('button', { name: 'Edit expense', exact: true });
  await requester.focus();
  await requester.press('Enter');
  await expect(page.getByRole('heading', { name: 'Edit expense', exact: true })).toBeVisible();
}

async function saveEdit(page: Page) {
  const submit = page.getByRole('button', { name: 'Save changes', exact: true });
  await submit.focus();
  await submit.press('Enter');
}

async function requestDeletion(page: Page, id = 'target') {
  const requester = transaction(page, id).getByRole('button', { name: 'Delete expense', exact: true });
  await requester.focus();
  await requester.press('Enter');
  const dialog = page.getByRole('dialog', { name: 'Delete expense?', exact: true });
  await expect(dialog).toBeVisible();
  return { dialog, requester };
}

async function selectMonth(page: Page, month: string) {
  const monthControl = page.getByLabel('Month', { exact: true });
  await monthControl.fill(month);
  await monthControl.press('Tab');
}

async function readRaw(page: Page) {
  return page.evaluate((key) => window.localStorage.getItem(key), storageKey);
}

async function setWriteFailure(page: Page, failWrites: boolean) {
  await page.evaluate((value) => {
    window.__editDeleteSpec.failWrites = value;
  }, failWrites);
}

test.use({ timezoneId: 'America/Los_Angeles' });

test.beforeEach(async ({ page }) => {
  await page.clock.install({ time: new Date('2026-10-31T12:00:00-07:00') });
});

test('CORE-005: edits every field with the same ID, exact recalculation, durable save, and requester focus', async ({ page }) => {
  await openTracker(page);
  await openEdit(page);
  await expect(page.getByLabel('Amount (USD)', { exact: true })).toHaveValue('1234.56');
  await expect(page.getByLabel('Category', { exact: true })).toHaveValue('transport');
  await expect(page.getByLabel('Date', { exact: true })).toHaveValue('2026-10-15');
  await expect(page.getByLabel('Note (optional)', { exact: true })).toHaveValue('Edit or delete target');

  await page.getByLabel('Amount (USD)', { exact: true }).fill('25.50');
  await page.getByLabel('Category', { exact: true }).selectOption('other');
  await page.getByLabel('Date', { exact: true }).fill('2026-10-21');
  await page.getByLabel('Note (optional)', { exact: true }).fill('  Exact edited note  ');
  await saveEdit(page);

  const item = transaction(page, 'target');
  await expect(item).toContainText('Exact edited note', { timeout: 2000 });
  await expect(item).toContainText('$25.50');
  await expect(item).toContainText('other');
  await expect(item).toContainText('2026-10-21');
  await expect(page.getByLabel('Monthly total', { exact: true })).toHaveText('$29.50');
  await expect(page.getByLabel('Transport total', { exact: true })).toHaveText('$0.00');
  await expect(page.getByLabel('Other total', { exact: true })).toHaveText('$25.50');
  await expect(item.getByRole('button', { name: 'Edit expense', exact: true })).toBeFocused();
  await expect(page.getByLabel('Month', { exact: true })).toHaveValue('2026-10');
  const saved = JSON.parse((await readRaw(page))!) as { expenses: Expense[] };
  expect(saved.expenses).toHaveLength(3);
  expect(saved.expenses.find((expense) => expense.id === 'target')).toEqual({
    id: 'target', amountCents: 2550, category: 'other', date: '2026-10-21', note: '  Exact edited note  ',
  });
});

for (const scenario of [
  { name: 'September into October', initialMonth: '2026-09', initialDate: '2026-09-30', editedDate: '2026-10-01', destinationMonth: '2026-10' },
  { name: 'October into November', initialMonth: '2026-10', initialDate: '2026-10-31', editedDate: '2026-11-01', destinationMonth: '2026-11' },
] as const) {
  test(`CORE-005: moves ${scenario.name}, announces the move, and focuses Month`, async ({ page }) => {
    const record = { ...records[1]!, date: scenario.initialDate };
    await openTracker(page, [record]);
    await selectMonth(page, scenario.initialMonth);
    await openEdit(page);
    await page.getByLabel('Date', { exact: true }).fill(scenario.editedDate);
    await saveEdit(page);

    const monthControl = page.getByLabel('Month', { exact: true });
    await expect(monthControl).toBeFocused({ timeout: 2000 });
    await expect(monthControl).toHaveValue(scenario.initialMonth);
    await expect(page.getByRole('status', { name: 'Expense status', exact: true })).toContainText(new RegExp(`moved.*${scenario.destinationMonth}`, 'i'));
    await expect(transactions(page)).toHaveCount(0);
    await expect(page.getByLabel('Monthly total', { exact: true })).toHaveText('$0.00');
    await selectMonth(page, scenario.destinationMonth);
    await expect(transaction(page, 'target')).toContainText(scenario.editedDate);
    await expect(page.getByLabel('Monthly total', { exact: true })).toHaveText('$1,234.56');
  });
}

test('DELETE-001/MONEY-003: native dialog has exact identity, no-undo text, and contained keyboard focus', async ({ page }) => {
  await openTracker(page);
  const { dialog } = await requestDeletion(page);
  await expect(dialog).toContainText('$1,234.56');
  await expect(dialog).toContainText('transport');
  await expect(dialog).toContainText('2026-10-15');
  await expect(dialog).toContainText(/no undo|cannot be undone/i);
  const cancel = dialog.getByRole('button', { name: 'Cancel', exact: true });
  const confirm = dialog.getByRole('button', { name: 'Confirm deletion', exact: true });
  await expect(cancel).toBeFocused();
  await cancel.press('Tab');
  await expect(confirm).toBeFocused();
  await confirm.press('Tab');
  await expect(cancel).toBeFocused();
  await cancel.press('Shift+Tab');
  await expect(confirm).toBeFocused();
  await confirm.press('Shift+Tab');
  await expect(cancel).toBeFocused();
  await expect(transactions(page)).toHaveCount(3);
});

for (const method of ['Cancel', 'Escape'] as const) {
  test(`DELETE-002: ${method} performs no mutation or write and restores the requester`, async ({ page }) => {
    await openTracker(page);
    const raw = await readRaw(page);
    const { dialog, requester } = await requestDeletion(page);
    if (method === 'Cancel') await dialog.getByRole('button', { name: 'Cancel', exact: true }).press('Enter');
    else await page.keyboard.press('Escape');
    await expect(dialog).toHaveCount(0);
    await expect(requester).toBeFocused();
    await expect(transactions(page)).toHaveCount(3);
    expect(await readRaw(page)).toBe(raw);
    expect(await page.evaluate(() => window.__editDeleteSpec.writes)).toBe(0);
  });
}

test('DELETE-003: confirmation removes only the target and focuses the next visible edit requester', async ({ page }) => {
  await openTracker(page);
  const { dialog } = await requestDeletion(page);
  await dialog.getByRole('button', { name: 'Confirm deletion', exact: true }).press('Enter');
  await expect(transactions(page)).toHaveCount(2, { timeout: 2000 });
  await expect(transaction(page, 'target')).toHaveCount(0);
  await expect(page.getByLabel('Monthly total', { exact: true })).toHaveText('$4.00');
  await expect(transaction(page, 'oldest').getByRole('button', { name: 'Edit expense', exact: true })).toBeFocused();
  await expect(page.getByRole('button', { name: /undo/i })).toHaveCount(0);
  expect(JSON.parse((await readRaw(page))!).expenses.map((expense: Expense) => expense.id)).toEqual(['newest', 'oldest']);
});

test('DELETE-003: deletes the last result and focuses the previous visible edit requester', async ({ page }) => {
  await openTracker(page);
  const { dialog } = await requestDeletion(page, 'oldest');
  await dialog.getByRole('button', { name: 'Confirm deletion', exact: true }).press('Enter');
  await expect(transaction(page, 'oldest')).toHaveCount(0, { timeout: 2000 });
  await expect(transaction(page, 'target').getByRole('button', { name: 'Edit expense', exact: true })).toBeFocused();
});

test('DELETE-003: deleting the only unfiltered result focuses Add expense', async ({ page }) => {
  await openTracker(page, [records[1]!]);
  const { dialog } = await requestDeletion(page);
  await dialog.getByRole('button', { name: 'Confirm deletion', exact: true }).press('Enter');
  await expect(transactions(page)).toHaveCount(0, { timeout: 2000 });
  await expect(page.getByRole('button', { name: 'Add expense', exact: true })).toBeFocused();
  expect(await readRaw(page)).toBe(envelope([]));
});

test('PERSIST-009: failed edit remains only in memory and reload restores original fields', async ({ page }) => {
  await openTracker(page);
  const raw = await readRaw(page);
  await setWriteFailure(page, true);
  await openEdit(page);
  await page.getByLabel('Amount (USD)', { exact: true }).fill('99.99');
  await page.getByLabel('Note (optional)', { exact: true }).fill('Failed edit memory only');
  await saveEdit(page);

  await expect(transaction(page, 'target')).toContainText('Failed edit memory only', { timeout: 2000 });
  await expect(transaction(page, 'target')).toContainText('$99.99');
  const warning = page.getByRole('alert', { name: 'Persistence status', exact: true });
  await expect(warning).toContainText(/edit expense/i);
  await expect(warning).toContainText(/not durably saved/i);
  await expect(warning).toContainText(/only in memory/i);
  expect(await readRaw(page)).toBe(raw);

  await page.reload();
  await expect(transaction(page, 'target')).toContainText('$1,234.56');
  await expect(transaction(page, 'target')).toContainText('Edit or delete target');
  await expect(page.getByText('Failed edit memory only', { exact: true })).toHaveCount(0);
  await expect(page.getByRole('alert', { name: 'Persistence status', exact: true })).toHaveCount(0);
});

test('DELETE-004/PERSIST-010: failed deletion remains only in memory and reload restores the target', async ({ page }) => {
  await openTracker(page);
  const raw = await readRaw(page);
  await setWriteFailure(page, true);
  const { dialog } = await requestDeletion(page);
  await dialog.getByRole('button', { name: 'Confirm deletion', exact: true }).press('Enter');

  await expect(transaction(page, 'target')).toHaveCount(0, { timeout: 2000 });
  const warning = page.getByRole('alert', { name: 'Persistence status', exact: true });
  await expect(warning).toContainText(/delete expense/i);
  await expect(warning).toContainText(/not durably saved/i);
  await expect(warning).toContainText(/only in memory/i);
  expect(await readRaw(page)).toBe(raw);

  await page.reload();
  await expect(transaction(page, 'target')).toBeVisible();
  await expect(transaction(page, 'target')).toContainText('$1,234.56');
  await expect(page.getByRole('alert', { name: 'Persistence status', exact: true })).toHaveCount(0);
  expect(await readRaw(page)).toBe(raw);
});

test.describe('de-DE deletion formatting', () => {
  test.use({ locale: 'de-DE' });

  test('MONEY-003: deletion identity remains fixed en-US USD', async ({ page }) => {
    await openTracker(page);
    const { dialog } = await requestDeletion(page);
    await expect(dialog).toContainText('$1,234.56');
    await expect(dialog).not.toContainText('1.234,56');
  });
});
