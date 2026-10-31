import { expect, test, type Locator, type Page } from '@playwright/test';

const storageKey = 'personal-expense-tracker:expenses:v1';
const seedMarker = 'transaction-list-spec:seeded';

type Expense = {
  id: string;
  amountCents: number;
  category: 'food' | 'transport' | 'housing' | 'entertainment' | 'other';
  date: string;
  note?: string;
};

const records: Expense[] = [
  { id: 'tie-a', amountCents: 200, category: 'food', date: '2026-10-10', note: 'Tie A' },
  { id: 'tie-c', amountCents: 100, category: 'transport', date: '2026-10-10', note: 'Tie C' },
  { id: 'tie-b', amountCents: 200, category: 'housing', date: '2026-10-10', note: 'Tie B' },
  { id: 'older', amountCents: 50, category: 'entertainment', date: '2026-10-01', note: 'Older' },
  { id: 'newer', amountCents: 150, category: 'other', date: '2026-10-31', note: 'Newer' },
  { id: 'september', amountCents: 999, category: 'food', date: '2026-09-30', note: 'Adjacent month' },
];

function envelope(expenses: Expense[]) {
  return JSON.stringify({ version: 1, expenses });
}

async function openTracker(page: Page, initialRecords = records) {
  await page.addInitScript(
    ({ key, marker, raw }) => {
      if (window.sessionStorage.getItem(marker) !== 'yes') {
        window.localStorage.setItem(key, raw);
        window.sessionStorage.setItem(marker, 'yes');
      }
    },
    { key: storageKey, marker: seedMarker, raw: envelope(initialRecords) },
  );
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Personal Expense Tracker' })).toBeVisible();
}

async function chooseOption(control: Locator, value: string) {
  const options = await control.locator('option').evaluateAll((elements) =>
    elements.map((element) => (element as HTMLOptionElement).value),
  );
  expect(options).toContain(value);
  await control.focus();
  await control.press(value[0]!);
  await control.press('Tab');
  await expect(control).toHaveValue(value);
}

function transactions(page: Page) {
  return page.getByRole('list', { name: 'Transactions' }).getByRole('listitem');
}

function transaction(page: Page, id: string) {
  return page.locator(`li[data-expense-id="${id}"]`);
}

async function expectIds(page: Page, ids: string[]) {
  await expect(transactions(page)).toHaveCount(ids.length, { timeout: 2000 });
  for (const [index, id] of ids.entries()) {
    await expect(transactions(page).nth(index)).toHaveAttribute('data-expense-id', id);
  }
}

async function readRaw(page: Page) {
  return page.evaluate((key) => window.localStorage.getItem(key), storageKey);
}

async function openEdit(page: Page, id: string) {
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

async function requestDeletion(page: Page, id: string) {
  const requester = transaction(page, id).getByRole('button', { name: 'Delete expense', exact: true });
  await requester.focus();
  await requester.press('Enter');
  const dialog = page.getByRole('dialog', { name: 'Delete expense?', exact: true });
  await expect(dialog).toBeVisible();
  return dialog;
}

async function confirmDeletion(page: Page, id: string) {
  const dialog = await requestDeletion(page, id);
  const confirm = dialog.getByRole('button', { name: 'Confirm deletion', exact: true });
  await confirm.focus();
  await confirm.press('Enter');
}

async function expectFocusedAndVisible(locator: Locator) {
  await expect(locator).toBeFocused({ timeout: 2000 });
  await expect(locator).toBeVisible();
}

test.use({ timezoneId: 'America/Los_Angeles' });

test.beforeEach(async ({ page }) => {
  await page.clock.install({ time: new Date('2026-10-31T12:00:00-07:00') });
});

test('FILTER-001/002: every category is exact, summaries/raw data stay stable, and all restores results', async ({ page }) => {
  await openTracker(page);
  const raw = await readRaw(page);
  const filter = page.getByLabel('Category filter', { exact: true });
  await expect(filter).toHaveValue('all');
  await expect(page.getByLabel('Sort by', { exact: true })).toHaveValue('date');
  await expect(page.getByLabel('Sort direction', { exact: true })).toHaveValue('desc');

  for (const [category, id] of [
    ['food', 'tie-a'],
    ['transport', 'tie-c'],
    ['housing', 'tie-b'],
    ['entertainment', 'older'],
    ['other', 'newer'],
  ] as const) {
    await chooseOption(filter, category);
    await expectIds(page, [id]);
    await expect(page.getByRole('status', { name: 'Transaction results', exact: true })).toContainText(`1 expense shown for ${category}`, { timeout: 2000 });
    await expect(page.getByLabel('Monthly total', { exact: true })).toHaveText('$7.00');
    expect(await readRaw(page)).toBe(raw);
  }

  await chooseOption(filter, 'all');
  await expectIds(page, ['newer', 'tie-a', 'tie-b', 'tie-c', 'older']);
  await expect(page.getByRole('status', { name: 'Transaction results', exact: true })).toContainText('5 expenses shown');
  expect(await readRaw(page)).toBe(raw);
});

for (const scenario of [
  { field: 'date', direction: 'asc', ids: ['older', 'tie-a', 'tie-b', 'tie-c', 'newer'] },
  { field: 'date', direction: 'desc', ids: ['newer', 'tie-a', 'tie-b', 'tie-c', 'older'] },
  { field: 'amount', direction: 'asc', ids: ['older', 'tie-c', 'newer', 'tie-a', 'tie-b'] },
  { field: 'amount', direction: 'desc', ids: ['tie-a', 'tie-b', 'newer', 'tie-c', 'older'] },
] as const) {
  test(`SORT-001/002: ${scenario.field} ${scenario.direction} has ID-ascending ties and no summary/raw mutation`, async ({ page }) => {
    await openTracker(page);
    const raw = await readRaw(page);
    await chooseOption(page.getByLabel('Sort by', { exact: true }), scenario.field);
    await chooseOption(page.getByLabel('Sort direction', { exact: true }), scenario.direction);
    await expectIds(page, scenario.ids);
    await expect(page.getByLabel('Monthly total', { exact: true })).toHaveText('$7.00');
    expect(await readRaw(page)).toBe(raw);
  });
}

test('EMPTY-001/002 and FILTER-002: distinct non-error actions focus Amount and Category filter', async ({ page }) => {
  const onlyFood = [records[0]!, records[3]!];
  await openTracker(page, onlyFood);
  await chooseOption(page.getByLabel('Category filter', { exact: true }), 'transport');
  const noMatches = page.getByRole('status', { name: 'No matching expenses', exact: true });
  await expect(noMatches).toContainText('No expenses match the selected category');
  await expect(page.getByRole('alert', { name: 'No matching expenses', exact: true })).toHaveCount(0);
  const clear = noMatches.getByRole('button', { name: 'Clear filter', exact: true });
  await clear.focus();
  await clear.press('Enter');
  await expectIds(page, ['tie-a', 'older']);
  await expectFocusedAndVisible(page.getByLabel('Category filter', { exact: true }));
  await expect(page.getByRole('status', { name: 'Transaction results', exact: true })).toContainText('2 expenses shown');

  const month = page.getByLabel('Month', { exact: true });
  await month.fill('2026-11');
  await month.press('Tab');
  const emptyMonth = page.getByRole('status', { name: 'Empty month', exact: true });
  await expect(emptyMonth).toContainText('No expenses for this month');
  await expect(page.getByRole('status', { name: 'No matching expenses', exact: true })).toHaveCount(0);
  const add = emptyMonth.getByRole('button', { name: 'Add expense for this month', exact: true });
  await add.focus();
  await add.press('Enter');
  await expectFocusedAndVisible(page.getByLabel('Amount (USD)', { exact: true }));
});

test('CORE-006: same-month edit out of the active filter announces membership and focuses Category filter', async ({ page }) => {
  await openTracker(page, [records[0]!, records[1]!]);
  const filter = page.getByLabel('Category filter', { exact: true });
  await chooseOption(filter, 'food');
  await openEdit(page, 'tie-a');
  await chooseOption(page.getByLabel('Category', { exact: true }), 'housing');
  await saveEdit(page);

  await expectIds(page, []);
  await expectFocusedAndVisible(filter);
  await expect(page.getByRole('status', { name: 'Expense status', exact: true })).toContainText(/updated.*no longer matches.*category filter/i, { timeout: 2000 });
  await expect(page.getByRole('status', { name: 'No matching expenses', exact: true })).toBeVisible();
  await expect(page.getByLabel('Monthly total', { exact: true })).toHaveText('$3.00');
  await expect(page.getByLabel('Housing total', { exact: true })).toHaveText('$2.00');
  const saved = JSON.parse((await readRaw(page))!) as { expenses: Expense[] };
  expect(saved.expenses.find((expense) => expense.id === 'tie-a')?.category).toBe('housing');
});

test('CORE-006: visible same-month edit restores the requester after amount resorting', async ({ page }) => {
  await openTracker(page);
  await chooseOption(page.getByLabel('Sort by', { exact: true }), 'amount');
  await chooseOption(page.getByLabel('Sort direction', { exact: true }), 'asc');
  await openEdit(page, 'tie-c');
  await page.getByLabel('Amount (USD)', { exact: true }).fill('4.00');
  await saveEdit(page);

  await expectIds(page, ['older', 'newer', 'tie-a', 'tie-b', 'tie-c']);
  await expectFocusedAndVisible(transaction(page, 'tie-c').getByRole('button', { name: 'Edit expense', exact: true }));
});

test('DELETE-005: last filtered deletion announces no matches and focuses Clear filter with hidden month data intact', async ({ page }) => {
  await openTracker(page, [records[0]!, records[1]!]);
  await chooseOption(page.getByLabel('Category filter', { exact: true }), 'food');
  await confirmDeletion(page, 'tie-a');

  await expectIds(page, []);
  await expectFocusedAndVisible(page.getByRole('button', { name: 'Clear filter', exact: true }));
  await expect(page.getByRole('status', { name: 'No matching expenses', exact: true })).toBeVisible({ timeout: 2000 });
  await expect(page.getByLabel('Monthly total', { exact: true })).toHaveText('$1.00');
  expect(JSON.parse((await readRaw(page))!).expenses.map((expense: Expense) => expense.id)).toEqual(['tie-c']);
});

test('DELETE-003: filtered and amount-sorted deletion focuses the next visible requester', async ({ page }) => {
  const filtered = [
    { ...records[0]!, id: 'filter-a', amountCents: 300 },
    { ...records[0]!, id: 'filter-b', amountCents: 200 },
    { ...records[0]!, id: 'filter-c', amountCents: 100 },
    records[1]!,
  ];
  await openTracker(page, filtered);
  await chooseOption(page.getByLabel('Category filter', { exact: true }), 'food');
  await chooseOption(page.getByLabel('Sort by', { exact: true }), 'amount');
  await chooseOption(page.getByLabel('Sort direction', { exact: true }), 'desc');
  await confirmDeletion(page, 'filter-b');
  await expectIds(page, ['filter-a', 'filter-c']);
  await expectFocusedAndVisible(transaction(page, 'filter-c').getByRole('button', { name: 'Edit expense', exact: true }));
});

test('DELETE-003: filtered and amount-sorted deletion focuses the previous visible requester when no next remains', async ({ page }) => {
  const filtered = [
    { ...records[0]!, id: 'filter-a', amountCents: 300 },
    { ...records[0]!, id: 'filter-b', amountCents: 200 },
    records[1]!,
  ];
  await openTracker(page, filtered);
  await chooseOption(page.getByLabel('Category filter', { exact: true }), 'food');
  await chooseOption(page.getByLabel('Sort by', { exact: true }), 'amount');
  await chooseOption(page.getByLabel('Sort direction', { exact: true }), 'asc');
  await confirmDeletion(page, 'filter-b');
  await expectIds(page, ['filter-a']);
  await expectFocusedAndVisible(transaction(page, 'filter-a').getByRole('button', { name: 'Edit expense', exact: true }));
});

test('DELETE-003: deleting the only unfiltered result focuses the visible Add expense submit', async ({ page }) => {
  await openTracker(page, [records[0]!]);
  await confirmDeletion(page, 'tie-a');
  await expectIds(page, []);
  await expectFocusedAndVisible(page.getByRole('button', { name: 'Add expense', exact: true }));
});
