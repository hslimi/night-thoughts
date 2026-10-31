import { expect, type Locator, type Page } from '@playwright/test';

export const storageKey = 'personal-expense-tracker:expenses:v1';

export type TestExpense = {
  id: string;
  amountCents: number;
  category: 'food' | 'transport' | 'housing' | 'entertainment' | 'other';
  date: string;
  note?: string;
};

export const coreExpenses: TestExpense[] = [
  { id: 'core-newest', amountCents: 100, category: 'food', date: '2026-10-20', note: 'Newest record' },
  { id: 'core-target', amountCents: 123456, category: 'transport', date: '2026-10-15', note: 'Target record' },
  { id: 'core-oldest', amountCents: 300, category: 'housing', date: '2026-10-10', note: 'Oldest record' },
];

type OpenOptions = {
  raw?: string;
  unreadable?: boolean;
};

declare global {
  interface Window {
    __coreFlowSpec: {
      failWrites: boolean;
      writes: number;
    };
  }
}

export function envelope(expenses: TestExpense[]): string {
  return JSON.stringify({ version: 1, expenses });
}

export async function openNormal(
  page: Page,
  records: TestExpense[] = coreExpenses,
  options: OpenOptions = {},
) {
  await page.addInitScript(
    ({ key, raw, unreadable }) => {
      const storage = window.localStorage;
      if (window.sessionStorage.getItem('core-flow:seeded') !== 'yes') {
        storage.setItem(key, raw);
        window.sessionStorage.setItem('core-flow:seeded', 'yes');
      }
      window.__coreFlowSpec = { failWrites: false, writes: 0 };
      const originalGetItem = Storage.prototype.getItem;
      Storage.prototype.getItem = function getItem(itemKey) {
        if (this === storage && unreadable && itemKey === key) {
          throw new DOMException('Injected unreadable storage', 'SecurityError');
        }
        return originalGetItem.call(this, itemKey);
      };
      const originalSetItem = Storage.prototype.setItem;
      Storage.prototype.setItem = function setItem(itemKey, value) {
        if (this === storage && itemKey === key) {
          window.__coreFlowSpec.writes += 1;
          if (window.__coreFlowSpec.failWrites) {
            throw new DOMException('Injected write failure', 'QuotaExceededError');
          }
        }
        return originalSetItem.call(this, itemKey, value);
      };
    },
    {
      key: storageKey,
      raw: options.raw ?? envelope(records),
      unreadable: options.unreadable ?? false,
    },
  );
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Personal Expense Tracker' })).toBeVisible();
}

export async function resetNormal(page: Page, records: TestExpense[] = coreExpenses) {
  await page.evaluate(
    ({ key, raw }) => window.localStorage.setItem(key, raw),
    { key: storageKey, raw: envelope(records) },
  );
  await page.reload();
  await expect(page.getByRole('heading', { name: 'Personal Expense Tracker' })).toBeVisible();
}

export async function setFailWrites(page: Page, failWrites: boolean) {
  await page.evaluate((value) => {
    window.__coreFlowSpec.failWrites = value;
  }, failWrites);
}

export function transactions(page: Page) {
  return page.getByRole('list', { name: 'Transactions' }).getByRole('listitem');
}

export function transaction(page: Page, id: string) {
  return page.locator(`li[data-expense-id="${id}"]`);
}

export async function selectMonth(page: Page, month: string) {
  const control = page.getByLabel('Month', { exact: true });
  await control.fill(month);
  await control.press('Tab');
  await expect(control).toHaveValue(month);
}

export async function addExpense(
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

export async function openEdit(page: Page, id = 'core-target') {
  const requester = transaction(page, id).getByRole('button', { name: 'Edit expense', exact: true });
  await requester.focus();
  await requester.press('Enter');
  await expect(page.getByRole('heading', { name: 'Edit expense', exact: true })).toBeVisible();
}

export async function saveEdit(page: Page) {
  const submit = page.getByRole('button', { name: 'Save changes', exact: true });
  await submit.focus();
  await submit.press('Enter');
}

export async function requestDeletion(page: Page, id = 'core-target') {
  const requester = transaction(page, id).getByRole('button', { name: 'Delete expense', exact: true });
  await requester.focus();
  await requester.press('Enter');
  const dialog = page.getByRole('dialog', { name: 'Delete expense?', exact: true });
  await expect(dialog).toBeVisible();
  return { dialog, requester };
}

export async function openUnsafeTotals(page: Page) {
  await page.addInitScript((key) => {
    const records = [
      { id: 'overflow-transport', amountCents: 100, category: 'transport', date: '2026-10-01' },
      ...Array.from({ length: 90072 }, (_, index) => ({
        id: `overflow-${String(index + 1).padStart(5, '0')}`,
        amountCents: 99999999999,
        category: 'food',
        date: '2026-10-15',
      })),
    ];
    const raw = JSON.stringify({ version: 1, expenses: records });
    const originalGetItem = Storage.prototype.getItem;
    Storage.prototype.getItem = function getItem(itemKey) {
      if (this === window.localStorage && itemKey === key) {
        return raw;
      }
      return originalGetItem.call(this, itemKey);
    };
  }, storageKey);
  await page.goto('/');
  await expect(page.getByLabel('Monthly total', { exact: true })).toHaveText('Unavailable', { timeout: 60000 });
  await page.getByLabel('Category filter', { exact: true }).selectOption('transport');
  await expect(transactions(page)).toHaveCount(1, { timeout: 10000 });
}

export async function expectFocusVisibleAndUnobscured(locator: Locator) {
  await expect(locator).toBeFocused({ timeout: 2000 });
  await expect(locator).toBeVisible();
  const result = await locator.evaluate((element) => {
    const rect = element.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    const hit = document.elementFromPoint(centerX, centerY);
    const style = getComputedStyle(element);
    return {
      insideViewport:
        rect.left >= 0 &&
        rect.top >= 0 &&
        rect.right <= window.innerWidth &&
        rect.bottom <= window.innerHeight,
      unobscured: hit === element || element.contains(hit),
      outlineWidth: Number.parseFloat(style.outlineWidth),
      outlineStyle: style.outlineStyle,
    };
  });
  expect(result.insideViewport, 'focused control must be inside the viewport').toBe(true);
  expect(result.unobscured, 'focused control must not be obscured').toBe(true);
  expect(result.outlineStyle, 'focused control must have a visible outline').not.toBe('none');
  expect(result.outlineWidth, 'focused control outline width').toBeGreaterThanOrEqual(2);
}
