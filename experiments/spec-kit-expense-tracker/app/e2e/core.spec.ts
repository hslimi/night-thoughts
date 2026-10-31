import { expect, test, type Page } from '@playwright/test';

const categories = ['food', 'transport', 'housing', 'entertainment', 'other'] as const;

async function addExpense(
  page: Page,
  values: { amount: string; category?: string; date: string; note?: string },
) {
  await page.getByLabel('Amount (USD)', { exact: true }).fill(values.amount);
  await page.getByLabel('Category', { exact: true }).selectOption(values.category ?? 'food');
  await page.getByLabel('Date', { exact: true }).fill(values.date);
  await page.getByLabel('Note (optional)', { exact: true }).fill(values.note ?? '');
  const submit = page.getByRole('button', { name: 'Add expense', exact: true });
  await submit.focus();
  await submit.press('Enter');
}

async function selectMonth(page: Page, month: string) {
  const control = page.getByLabel('Month', { exact: true });
  await control.fill(month);
  await control.press('Tab');
}

async function verifyFixedFormatting(page: Page) {
  await addExpense(page, { amount: '1234.56', date: '2026-10-15', note: 'Grouped amount' });
  await addExpense(page, { amount: '0.01', date: '2026-10-16' });
  await addExpense(page, { amount: '0.10', date: '2026-10-17' });
  await addExpense(page, { amount: '0.99', date: '2026-10-18' });

  await expect(page.getByLabel('Monthly total', { exact: true })).toHaveText('$1,235.66');
  await expect(page.getByLabel('Food total', { exact: true })).toHaveText('$1,235.66');
  await expect(page.getByLabel('Transport total', { exact: true })).toHaveText('$0.00');
  const items = page.getByRole('list', { name: 'Transactions' }).getByRole('listitem');
  await expect(items).toHaveCount(4);
  await expect(items.nth(0)).toContainText('$0.99');
  await expect(items.nth(1)).toContainText('$0.10');
  await expect(items.nth(2)).toContainText('$0.01');
  await expect(items.nth(3)).toContainText('$1,234.56');
}

test.use({ timezoneId: 'America/Los_Angeles' });

test.beforeEach(async ({ page }) => {
  await page.clock.install({ time: new Date('2026-10-31T12:00:00-07:00') });
  await page.goto('/');
});

test('CORE-001/004 and MONEY-001: add by keyboard and show exact zero/nonzero totals', async ({ page }) => {
  await expect(page.getByRole('heading', { name: 'Personal Expense Tracker' })).toBeVisible();
  await expect(page.getByLabel('Month', { exact: true })).toHaveValue('2026-10');
  await expect(page.getByLabel('Monthly total', { exact: true })).toHaveText('$0.00');
  for (const category of categories) {
    const label = `${category[0]!.toUpperCase()}${category.slice(1)} total`;
    await expect(page.getByLabel(label, { exact: true })).toHaveText('$0.00');
  }

  await addExpense(page, { amount: '25.50', date: '2026-10-15', note: '  Exact note  ' });
  await expect(page.getByLabel('Monthly total', { exact: true })).toHaveText('$25.50');
  await expect(page.getByLabel('Food total', { exact: true })).toHaveText('$25.50');
  await expect(page.getByLabel('Transport total', { exact: true })).toHaveText('$0.00');
  const item = page.getByRole('list', { name: 'Transactions' }).getByRole('listitem');
  await expect(item).toHaveCount(1);
  await expect(item).toContainText('$25.50');
  await expect(item).toContainText('2026-10-15');
  await expect(item).toContainText('Exact note');
  await expect(page.getByRole('status', { name: 'Expense status' })).toContainText('Expense added.');
});

test('CORE-002/003: fixed local current month and all five categories', async ({ page }) => {
  await expect(page.getByLabel('Month', { exact: true })).toHaveValue('2026-10');
  for (const [index, category] of categories.entries()) {
    await addExpense(page, {
      amount: String(index + 1),
      category,
      date: '2026-10-15',
    });
  }
  await expect(page.getByLabel('Monthly total', { exact: true })).toHaveText('$15.00');
  await expect(page.getByRole('list', { name: 'Transactions' }).getByRole('listitem')).toHaveCount(5);
});

test('CORE-002: clearing native Month preserves the last valid dashboard', async ({ page }) => {
  const pageErrors: string[] = [];
  page.on('pageerror', (error) => pageErrors.push(error.message));
  await addExpense(page, { amount: '99.99', date: '2026-09-30' });
  await addExpense(page, { amount: '1.00', date: '2026-10-01' });
  await addExpense(page, { amount: '2.00', category: 'transport', date: '2026-10-31' });
  await addExpense(page, { amount: '8.88', date: '2026-11-01', note: 'November record' });
  await selectMonth(page, '2026-11');

  const month = page.getByLabel('Month', { exact: true });
  const items = page.getByRole('list', { name: 'Transactions' }).getByRole('listitem');
  await expect(month).toHaveValue('2026-11');
  await expect(page.getByLabel('Monthly total', { exact: true })).toHaveText('$8.88');
  await expect(items).toHaveCount(1);
  await expect(items.nth(0)).toContainText('November record');

  await month.fill('');

  await expect(month).toHaveValue('2026-11');
  await expect(page.getByRole('heading', { name: 'Personal Expense Tracker' })).toBeVisible();
  await expect(page.getByLabel('Monthly total', { exact: true })).toHaveText('$8.88');
  await expect(items).toHaveCount(1);
  await expect(items.nth(0)).toContainText('November record');
  expect(pageErrors).toEqual([]);
});

test('CORE-001 and DATE-001/004: local first/last-day membership and month selection', async ({ page }) => {
  await addExpense(page, { amount: '99.99', date: '2026-09-30' });
  await addExpense(page, { amount: '1.00', date: '2026-10-01' });
  await addExpense(page, { amount: '2.00', category: 'transport', date: '2026-10-31' });
  await addExpense(page, { amount: '88.88', date: '2026-11-01' });

  await selectMonth(page, '2026-10');
  const items = page.getByRole('list', { name: 'Transactions' }).getByRole('listitem');
  await expect(items).toHaveCount(2);
  await expect(items.nth(0)).toContainText('2026-10-31');
  await expect(items.nth(1)).toContainText('2026-10-01');
  await expect(page.getByLabel('Monthly total', { exact: true })).toHaveText('$3.00');

  await selectMonth(page, '2026-09');
  await expect(items).toHaveCount(1);
  await expect(page.getByLabel('Monthly total', { exact: true })).toHaveText('$99.99');
});

test('DATE-002: leap-day acceptance and impossible-date rejection', async ({ page }) => {
  await addExpense(page, { amount: '2.50', date: '2024-02-29' });
  await selectMonth(page, '2024-02');
  await expect(page.getByLabel('Monthly total', { exact: true })).toHaveText('$2.50');

  await page.getByLabel('Amount (USD)', { exact: true }).fill('3.00');
  const invalidDate = page.getByLabel('Date', { exact: true });
  await invalidDate.evaluate((element) => {
    (element as HTMLInputElement).type = 'text';
  });
  await invalidDate.fill('2023-02-29');
  const submit = page.getByRole('button', { name: 'Add expense', exact: true });
  await submit.focus();
  await submit.press('Enter');
  await expect(page.getByLabel('Date', { exact: true })).toBeFocused();
  await expect(page.getByLabel('Date', { exact: true })).toHaveAttribute('aria-invalid', 'true');
  await expect(page.getByRole('alert')).toContainText('Enter a real local calendar date in YYYY-MM-DD format.');
  await expect(page.getByLabel('Monthly total', { exact: true })).toHaveText('$2.50');
});

test('DATE-003/004: future expense remains isolated until its local month is selected', async ({ page }) => {
  await addExpense(page, { amount: '12.34', date: '2027-01-15' });
  await expect(page.getByLabel('Month', { exact: true })).toHaveValue('2026-10');
  await expect(page.getByLabel('Monthly total', { exact: true })).toHaveText('$0.00');
  await selectMonth(page, '2027-01');
  await expect(page.getByLabel('Monthly total', { exact: true })).toHaveText('$12.34');
  await expect(page.getByRole('list', { name: 'Transactions' }).getByRole('listitem')).toHaveCount(1);
});

test('MONEY-002/003: exact fixed en-US USD transaction and summary output', async ({ page }) => {
  await verifyFixedFormatting(page);
});

test.describe('de-DE browser locale', () => {
  test.use({ locale: 'de-DE' });

  test('MONEY-001/003: output is identical under de-DE', async ({ page }) => {
    await expect(page.getByLabel('Monthly total', { exact: true })).toHaveText('$0.00');
    await verifyFixedFormatting(page);
  });
});

test('responsive baseline: controls meet 24px targets without horizontal reflow', async ({ page }) => {
  await addExpense(page, { amount: '25.50', date: '2026-10-15' });
  const dimensions = await page.evaluate(() => ({
    viewport: window.innerWidth,
    content: document.documentElement.scrollWidth,
    targets: [...document.querySelectorAll<HTMLElement>('button, input, select, textarea')]
      .filter((element) => element.getBoundingClientRect().width > 0)
      .map((element) => ({
        label: element.getAttribute('aria-label') ?? element.id ?? element.tagName,
        width: element.getBoundingClientRect().width,
        height: element.getBoundingClientRect().height,
      })),
  }));
  expect(dimensions.content).toBeLessThanOrEqual(dimensions.viewport);
  for (const target of dimensions.targets) {
    expect(target.width, `${target.label} width`).toBeGreaterThanOrEqual(24);
    expect(target.height, `${target.label} height`).toBeGreaterThanOrEqual(24);
  }
});
