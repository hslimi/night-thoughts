import { expect, test, type Locator, type Page } from '@playwright/test';

const storageKey = 'personal-expense-tracker:expenses:v1';
const realRaw = JSON.stringify({
  version: 1,
  expenses: [{
    id: 'real-expense', amountCents: 123456, category: 'food',
    date: '2026-10-30', note: 'Known real expense',
  }],
});

const octoberRecords = [
  { id: 'demo-008', amount: '$32.40', category: 'transport', date: '2026-10-21', note: 'Airport train' },
  { id: 'demo-007', amount: '$67.20', category: 'food', date: '2026-10-18', note: 'Dinner with friends' },
  { id: 'demo-006', amount: '$85.00', category: 'other', date: '2026-10-15', note: 'Household supplies' },
  { id: 'demo-005', amount: '$12.80', category: 'food', date: '2026-10-12', note: 'Coffee and pastry' },
  { id: 'demo-004', amount: '$24.00', category: 'entertainment', date: '2026-10-08', note: 'Cinema tickets' },
  { id: 'demo-003', amount: '$18.50', category: 'transport', date: '2026-10-05', note: 'Metro card top-up' },
  { id: 'demo-002', amount: '$42.75', category: 'food', date: '2026-10-03', note: 'Groceries at Green Market' },
  { id: 'demo-001', amount: '$1,450.00', category: 'housing', date: '2026-10-01', note: 'October rent' },
] as const;

const summaries = {
  'Monthly total': '$1,732.65',
  'Food total': '$122.75',
  'Transport total': '$50.90',
  'Housing total': '$1,450.00',
  'Entertainment total': '$24.00',
  'Other total': '$85.00',
} as const;

type Precondition = 'populated' | 'missing' | 'malformed' | 'unreadable';

function transactions(page: Page) {
  return page.getByRole('list', { name: 'Transactions' }).getByRole('listitem');
}

function transaction(page: Page, id: string) {
  return page.locator(`li[data-expense-id="${id}"]`);
}

async function chooseOption(control: Locator, value: string) {
  await control.selectOption(value);
  await expect(control).toHaveValue(value);
}

async function expectBaseline(page: Page) {
  await expect(page.getByRole('status', { name: 'Demo mode', exact: true })).toContainText(/fictional demo data/i);
  await expect(page.getByLabel('Month', { exact: true })).toHaveValue('2026-10');
  await expect(page.getByLabel('Category filter', { exact: true })).toHaveValue('all');
  await expect(page.getByLabel('Sort by', { exact: true })).toHaveValue('date');
  await expect(page.getByLabel('Sort direction', { exact: true })).toHaveValue('desc');
  await expect(transactions(page)).toHaveCount(8, { timeout: 2000 });
  for (const [index, record] of octoberRecords.entries()) {
    const item = transactions(page).nth(index);
    await expect(item).toHaveAttribute('data-expense-id', record.id);
    await expect(item.locator('.transaction__amount')).toHaveText(record.amount);
    await expect(item.locator('.category-tag')).toHaveText(record.category);
    await expect(item.locator('time')).toHaveText(record.date);
    await expect(item.locator('.transaction-note')).toHaveText(record.note);
  }
  for (const [label, value] of Object.entries(summaries)) {
    await expect(page.getByLabel(label, { exact: true })).toHaveText(value);
  }
  await expect(page.getByText('Previous month lunch', { exact: true })).toHaveCount(0);
  await expect(page.getByText('Future concert deposit', { exact: true })).toHaveCount(0);
}

async function instrumentStorage(page: Page, precondition: Precondition) {
  await page.addInitScript(
    ({ key, populatedRaw, condition }) => {
      const counts = { reads: 0, writes: 0, listeners: 0 };
      Object.defineProperty(window, '__demoStorageCounts', { value: counts });
      const prototype = window.Storage.prototype;
      const originalGet = prototype.getItem;
      const originalSet = prototype.setItem;
      const originalRemove = prototype.removeItem;
      const originalClear = prototype.clear;
      prototype.getItem = function getItem(keyName: string) {
        counts.reads += 1;
        if (condition === 'unreadable') {
          throw new DOMException('Injected unreadable storage', 'SecurityError');
        }
        return originalGet.call(this, keyName);
      };
      prototype.setItem = function setItem(keyName: string, value: string) {
        counts.writes += 1;
        return originalSet.call(this, keyName, value);
      };
      prototype.removeItem = function removeItem(keyName: string) {
        counts.writes += 1;
        return originalRemove.call(this, keyName);
      };
      prototype.clear = function clear() {
        counts.writes += 1;
        return originalClear.call(this);
      };

      if (condition === 'missing') {
        originalRemove.call(window.localStorage, key);
      } else {
        originalSet.call(window.localStorage, key, condition === 'malformed' ? '{not-json' : populatedRaw);
      }

      const originalAddEventListener = window.addEventListener;
      window.addEventListener = function addEventListener(
        type: string,
        listener: EventListenerOrEventListenerObject | null,
        options?: boolean | AddEventListenerOptions,
      ) {
        if (type === 'storage') {
          counts.listeners += 1;
        }
        return originalAddEventListener.call(this, type, listener, options);
      } as typeof window.addEventListener;
      let assignedStorageHandler: ((this: Window, event: StorageEvent) => unknown) | null = null;
      Object.defineProperty(window, 'onstorage', {
        configurable: true,
        get: () => assignedStorageHandler,
        set: (handler) => {
          counts.listeners += 1;
          assignedStorageHandler = handler;
        },
      });
    },
    { key: storageKey, populatedRaw: realRaw, condition: precondition },
  );
}

async function storageCounts(page: Page) {
  return page.evaluate(() => {
    const counts = (window as unknown as {
      __demoStorageCounts: { reads: number; writes: number; listeners: number };
    }).__demoStorageCounts;
    return { ...counts };
  });
}

async function expectZeroStorage(page: Page) {
  expect(await storageCounts(page)).toEqual({ reads: 0, writes: 0, listeners: 0 });
}

async function exerciseDemoInteractions(page: Page) {
  const amount = page.getByLabel('Amount (USD)', { exact: true });
  await amount.fill('0');
  await page.getByLabel('Date', { exact: true }).fill('2026-10-22');
  await page.getByRole('button', { name: 'Add expense', exact: true }).click();
  await expect(amount).toBeFocused();
  await expect(page.getByRole('alert')).toContainText(/valid USD amount/i);
  await expect(page.getByLabel('Monthly total', { exact: true })).toHaveText('$1,732.65');

  await amount.fill('10.01');
  await page.getByLabel('Note (optional)', { exact: true }).fill('Demo addition');
  await page.getByRole('button', { name: 'Add expense', exact: true }).click();
  await expect(page.getByText('Demo addition', { exact: true })).toBeVisible({ timeout: 2000 });
  await expect(page.getByLabel('Monthly total', { exact: true })).toHaveText('$1,742.66');

  await transaction(page, 'demo-008').getByRole('button', { name: 'Edit expense', exact: true }).click();
  await amount.fill('40.00');
  await chooseOption(page.getByLabel('Category', { exact: true }), 'other');
  await page.getByRole('button', { name: 'Save changes', exact: true }).click();
  await expect(transaction(page, 'demo-008').locator('.transaction__amount')).toHaveText('$40.00', { timeout: 2000 });

  await transaction(page, 'demo-007').getByRole('button', { name: 'Delete expense', exact: true }).click();
  const dialog = page.getByRole('dialog', { name: 'Delete expense?', exact: true });
  await expect(dialog).toContainText('$67.20');
  await dialog.getByRole('button', { name: 'Confirm deletion', exact: true }).click();
  await expect(page.getByText('Dinner with friends', { exact: true })).toHaveCount(0);

  await page.getByLabel('Month', { exact: true }).fill('2026-09');
  await expect(transactions(page)).toHaveCount(1);
  await expect(transaction(page, 'demo-009')).toContainText('Previous month lunch');
  await expect(page.getByLabel('Monthly total', { exact: true })).toHaveText('$20.00');
  await page.getByLabel('Month', { exact: true }).fill('2026-11');
  await expect(transaction(page, 'demo-010')).toContainText('Future concert deposit');
  await expect(page.getByLabel('Monthly total', { exact: true })).toHaveText('$30.00');
  await page.getByLabel('Month', { exact: true }).fill('2026-10');

  await chooseOption(page.getByLabel('Category filter', { exact: true }), 'food');
  await expect(transactions(page)).toHaveCount(3);
  await expect(transactions(page).nth(1)).toHaveAttribute('data-expense-id', 'demo-005');
  await expect(transactions(page).nth(2)).toHaveAttribute('data-expense-id', 'demo-002');
  await expect(page.getByLabel('Monthly total', { exact: true })).toHaveText('$1,683.06');
  await chooseOption(page.getByLabel('Category filter', { exact: true }), 'all');
  await chooseOption(page.getByLabel('Sort by', { exact: true }), 'amount');
  await chooseOption(page.getByLabel('Sort direction', { exact: true }), 'asc');
  await expect(transactions(page).first()).toContainText('Demo addition');
  await expect(page.getByRole('alert', { name: 'Persistence status', exact: true })).toHaveCount(0);
  await expect(page.getByText(/durably saved|saved successfully/i)).toHaveCount(0);
}

test.use({ timezoneId: 'America/Los_Angeles' });

test.beforeEach(async ({ page }) => {
  await page.clock.install({ time: new Date('2026-10-31T12:00:00-07:00') });
});

test('DEMO-001: only an exact first demo=1 value activates demo', async ({ page }) => {
  for (const [query, active] of [
    ['?demo=1', true], ['?source=x&demo=1', true], ['?demo=1&demo=0', true],
    ['?demo=0&demo=1', false], ['?demo=01', false], ['?demo=true', false],
    ['?Demo=1', false], ['', false],
  ] as const) {
    await page.goto(`/${query}`);
    await expect(page.getByRole('heading', { name: 'Personal Expense Tracker' })).toBeVisible();
    await expect(page.getByRole('status', { name: 'Demo mode', exact: true })).toHaveCount(active ? 1 : 0);
    if (active) {
      await expectBaseline(page);
    } else {
      await expect(page.getByText('Airport train', { exact: true })).toHaveCount(0);
    }
  }
});

for (const locale of ['en-US', 'de-DE']) {
  test.describe(`demo locale ${locale}`, () => {
    test.use({ locale });
    test(`DEMO-002 and MONEY-003: exact fixed en-US USD baseline and deletion dialog in ${locale}`, async ({ page }) => {
      await page.goto('/?demo=1');
      await expectBaseline(page);
      expect(await page.evaluate(() => navigator.language)).toBe(locale);

      await transaction(page, 'demo-008').getByRole('button', { name: 'Delete expense', exact: true }).click();
      const dialog = page.getByRole('dialog', { name: 'Delete expense?', exact: true });
      await expect(dialog).toContainText('$32.40 transport expense dated 2026-10-21');
      await dialog.getByRole('button', { name: 'Cancel', exact: true }).click();
      await expectBaseline(page);
    });
  });
}

test('DEMO-003: reload restores the exact baseline and default view after every interaction', async ({ page }) => {
  await instrumentStorage(page, 'populated');
  await page.goto('/?demo=1');
  await expectBaseline(page);
  await exerciseDemoInteractions(page);
  await expectZeroStorage(page);

  await page.reload();
  await expectBaseline(page);
  await expect(page.getByLabel('Note (optional)', { exact: true })).toHaveValue('');
  await expect(page.getByRole('status', { name: 'Expense status', exact: true })).toHaveCount(0);
  await expectZeroStorage(page);
});

for (const precondition of ['populated', 'missing', 'malformed', 'unreadable'] as const) {
  test(`DEMO-005: ${precondition} real storage has zero reads, writes, and listeners through all interactions`, async ({ page }) => {
    await instrumentStorage(page, precondition);
    await page.goto('/?demo=1');
    await expectBaseline(page);
    await exerciseDemoInteractions(page);
    await expectZeroStorage(page);
    await page.reload();
    await expectBaseline(page);
    await expectZeroStorage(page);
  });
}

test('DEMO-004/007: URL, reload, back, and forward create fresh isolated destination state', async ({ page }) => {
  await page.goto('/');
  await page.evaluate(({ key, raw }) => window.localStorage.setItem(key, raw), { key: storageKey, raw: realRaw });
  await page.reload();
  await expect(page.getByText('Known real expense', { exact: true })).toBeVisible();

  await page.goto('/?demo=1');
  await expectBaseline(page);
  await chooseOption(page.getByLabel('Category filter', { exact: true }), 'housing');
  await page.getByLabel('Note (optional)', { exact: true }).fill('Demo form must not leak');
  await transaction(page, 'demo-001').getByRole('button', { name: 'Delete expense', exact: true }).click();
  await expect(page.getByRole('dialog', { name: 'Delete expense?', exact: true })).toBeVisible();

  await page.goto('/');
  await expect(page.getByRole('status', { name: 'Demo mode', exact: true })).toHaveCount(0);
  await expect(page.getByText('Known real expense', { exact: true })).toBeVisible();
  await expect(page.getByText('October rent', { exact: true })).toHaveCount(0);
  await expect(page.getByLabel('Note (optional)', { exact: true })).toHaveValue('');
  await expect(page.getByRole('dialog')).toHaveCount(0);
  expect(await page.evaluate((key) => window.localStorage.getItem(key), storageKey)).toBe(realRaw);

  await page.goBack();
  await expectBaseline(page);
  await expect(page.getByLabel('Note (optional)', { exact: true })).toHaveValue('');
  await expect(page.getByRole('dialog')).toHaveCount(0);

  await page.goForward();
  await expect(page.getByRole('status', { name: 'Demo mode', exact: true })).toHaveCount(0);
  await expect(page.getByText('Known real expense', { exact: true })).toBeVisible();
  await expect(page.getByLabel('Category filter', { exact: true })).toHaveValue('all');
  expect(await page.evaluate((key) => window.localStorage.getItem(key), storageKey)).toBe(realRaw);
});

test('DEMO-006/007: a concurrent normal tab remains untouched and receives no demo storage activity', async ({ page, context }) => {
  const normal = await context.newPage();
  await normal.goto('/');
  await normal.evaluate(({ key, raw }) => window.localStorage.setItem(key, raw), { key: storageKey, raw: realRaw });
  await normal.reload();
  await expect(normal.getByText('Known real expense', { exact: true })).toBeVisible();

  await instrumentStorage(page, 'populated');
  await page.goto('/?demo=1');
  await expectBaseline(page);
  await exerciseDemoInteractions(page);
  await expectZeroStorage(page);

  await normal.bringToFront();
  await normal.reload();
  await expect(normal.getByText('Known real expense', { exact: true })).toBeVisible();
  await expect(normal.getByRole('status', { name: 'Demo mode', exact: true })).toHaveCount(0);
  expect(await normal.evaluate((key) => window.localStorage.getItem(key), storageKey)).toBe(realRaw);
  await expectZeroStorage(page);
});
