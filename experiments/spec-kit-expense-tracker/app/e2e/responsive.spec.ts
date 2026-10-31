import { expect, test, type Page } from '@playwright/test';
import {
  addExpense,
  coreExpenses,
  expectFocusVisibleAndUnobscured,
  openEdit,
  openNormal,
  openUnsafeTotals,
  requestDeletion,
  saveEdit,
  selectMonth,
  setFailWrites,
  transaction,
  transactions,
} from './coreFlowUtils';

async function expectResponsive(page: Page, state: string) {
  const result = await page.evaluate(() => {
    const openDialog = document.querySelector<HTMLDialogElement>('dialog[open]');
    const targets = [...document.querySelectorAll<HTMLElement>(
      'button, input, select, textarea, a[href], [role="button"]',
    )]
      .filter((element) => {
        const rect = element.getBoundingClientRect();
        return (
          rect.width > 0 &&
          rect.height > 0 &&
          getComputedStyle(element).visibility !== 'hidden' &&
          (!openDialog || openDialog.contains(element))
        );
      })
      .map((element) => {
        const rect = element.getBoundingClientRect();
        return {
          label: element.getAttribute('aria-label') ?? element.id ?? element.textContent?.trim() ?? element.tagName,
          left: rect.left,
          right: rect.right,
          top: rect.top,
          bottom: rect.bottom,
          width: rect.width,
          height: rect.height,
        };
      });
    const overlaps: Array<[string, string]> = [];
    for (let first = 0; first < targets.length; first += 1) {
      for (let second = first + 1; second < targets.length; second += 1) {
        const a = targets[first]!;
        const b = targets[second]!;
        const intersectionWidth = Math.min(a.right, b.right) - Math.max(a.left, b.left);
        const intersectionHeight = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
        if (intersectionWidth > 1 && intersectionHeight > 1) {
          overlaps.push([a.label, b.label]);
        }
      }
    }
    return {
      viewportWidth: window.innerWidth,
      contentWidth: document.documentElement.scrollWidth,
      targets,
      overlaps,
    };
  });

  expect(result.contentWidth, `${state}: no two-dimensional scrolling`).toBeLessThanOrEqual(result.viewportWidth);
  expect(result.overlaps, `${state}: controls must not overlap`).toEqual([]);
  for (const target of result.targets) {
    expect(target.width, `${state}: ${target.label} target width`).toBeGreaterThanOrEqual(24);
    expect(target.height, `${state}: ${target.label} target height`).toBeGreaterThanOrEqual(24);
    expect(target.left, `${state}: ${target.label} must not clip left`).toBeGreaterThanOrEqual(0);
    expect(target.right, `${state}: ${target.label} must not clip right`).toBeLessThanOrEqual(result.viewportWidth);
  }
}

async function doubleRenderedText(page: Page) {
  const sizes = await page.evaluate(() => {
    const elements = [...document.querySelectorAll<HTMLElement>('body *')].filter(
      (element) => getComputedStyle(element).display !== 'none',
    );
    const before = elements.map((element) => Number.parseFloat(getComputedStyle(element).fontSize));
    const headingBefore = Number.parseFloat(getComputedStyle(document.querySelector('h1')!).fontSize);
    elements.forEach((element, index) => {
      element.style.fontSize = `${before[index]! * 2}px`;
    });
    return {
      before: headingBefore,
      after: Number.parseFloat(getComputedStyle(document.querySelector('h1')!).fontSize),
    };
  });
  expect(sizes.after).toBe(sizes.before * 2);
}

test.use({ timezoneId: 'America/Los_Angeles' });

test.beforeEach(async ({ page }) => {
  await page.clock.install({ time: new Date('2026-10-31T12:00:00-07:00') });
});

test('responsive populated dashboard, invalid/valid add and edit, and month selection preserve all controls', async ({ page }) => {
  await openNormal(page);
  await expectResponsive(page, 'populated dashboard');

  const amount = page.getByLabel('Amount (USD)', { exact: true });
  await amount.fill('0');
  await page.getByLabel('Date', { exact: true }).fill('2026-10-22');
  await page.getByRole('button', { name: 'Add expense', exact: true }).press('Enter');
  await expectFocusVisibleAndUnobscured(amount);
  await expectResponsive(page, 'invalid add');

  await amount.fill('25.50');
  await page.getByLabel('Note (optional)', { exact: true }).fill('Responsive add');
  await page.getByRole('button', { name: 'Add expense', exact: true }).press('Enter');
  await expect(page.getByText('Responsive add', { exact: true })).toBeVisible();
  await expectResponsive(page, 'valid add');

  await openEdit(page);
  await amount.fill('1.234');
  await saveEdit(page);
  await expectFocusVisibleAndUnobscured(amount);
  await expectResponsive(page, 'invalid edit');
  await amount.fill('30.00');
  await saveEdit(page);
  await expectFocusVisibleAndUnobscured(
    transaction(page, 'core-target').getByRole('button', { name: 'Edit expense', exact: true }),
  );
  await expectResponsive(page, 'valid same-month edit');

  await openEdit(page);
  await page.getByLabel('Date', { exact: true }).fill('2026-11-01');
  await saveEdit(page);
  await expectFocusVisibleAndUnobscured(page.getByLabel('Month', { exact: true }));
  await expectResponsive(page, 'cross-month edit');
});

test('responsive deletion and replacement dialogs, focus fallbacks, and warning states remain usable', async ({ page }) => {
  await openNormal(page);
  const deletion = await requestDeletion(page);
  await expectFocusVisibleAndUnobscured(deletion.dialog.getByRole('button', { name: 'Cancel', exact: true }));
  await expectResponsive(page, 'deletion dialog');
  await deletion.dialog.getByRole('button', { name: 'Cancel', exact: true }).press('Enter');
  await expectFocusVisibleAndUnobscured(deletion.requester);

  await setFailWrites(page, true);
  const failedDeletion = await requestDeletion(page, 'core-oldest');
  await failedDeletion.dialog.getByRole('button', { name: 'Confirm deletion', exact: true }).press('Enter');
  await expect(page.getByRole('alert', { name: 'Persistence status', exact: true })).toContainText(/delete expense/i);
  await expectResponsive(page, 'failed deletion warning');

  await setFailWrites(page, false);
  await page.evaluate(() => window.localStorage.setItem('personal-expense-tracker:expenses:v1', '{broken'));
  await page.reload();
  await expect(page.getByRole('alert', { name: 'Persistence status', exact: true })).toContainText(/invalid/i);
  await expectResponsive(page, 'readable recovery warning');
  const startFresh = page.getByRole('button', { name: 'Start fresh', exact: true });
  await startFresh.focus();
  await startFresh.press('Enter');
  const replacement = page.getByRole('dialog', { name: 'Replace saved information?', exact: true });
  await expectFocusVisibleAndUnobscured(replacement.getByRole('button', { name: 'Cancel', exact: true }));
  await expectResponsive(page, 'start-fresh replacement dialog');
  await replacement.getByRole('button', { name: 'Cancel', exact: true }).press('Enter');
  await expectFocusVisibleAndUnobscured(startFresh);

  await addExpense(page, { amount: '7.10', date: '2026-10-18', note: 'Responsive guarded work' });
  await expect(replacement).toContainText(/complete current in-memory collection/i);
  await expectResponsive(page, 'first-replacement dialog');
  await replacement.getByRole('button', { name: 'Cancel', exact: true }).press('Enter');
  await expect(page.getByText('Responsive guarded work', { exact: true })).toBeVisible();
});

test('responsive unreadable recovery retains its warning and all controls', async ({ page }) => {
  await openNormal(page, [], { unreadable: true });
  await expect(page.getByRole('alert', { name: 'Persistence status', exact: true })).toContainText(/unreadable/i);
  await expectResponsive(page, 'unreadable recovery');
});

test('responsive empty/no-match actions, filters, and both sort directions retain functionality', async ({ page }) => {
  await openNormal(page, []);
  await expect(page.getByRole('status', { name: 'Empty month', exact: true })).toBeVisible();
  await expectResponsive(page, 'empty month');
  await page.getByRole('button', { name: 'Add expense for this month', exact: true }).press('Enter');
  await expectFocusVisibleAndUnobscured(page.getByLabel('Amount (USD)', { exact: true }));

  await page.evaluate(({ key, raw }) => window.localStorage.setItem(key, raw), {
    key: 'personal-expense-tracker:expenses:v1',
    raw: JSON.stringify({ version: 1, expenses: coreExpenses }),
  });
  await page.reload();
  await page.getByLabel('Category filter', { exact: true }).selectOption('entertainment');
  await expect(page.getByRole('status', { name: 'No matching expenses', exact: true })).toBeVisible();
  await expectResponsive(page, 'no matching expenses');
  await page.getByRole('button', { name: 'Clear filter', exact: true }).press('Enter');
  await expectFocusVisibleAndUnobscured(page.getByLabel('Category filter', { exact: true }));

  for (const field of ['date', 'amount'] as const) {
    await page.getByLabel('Sort by', { exact: true }).selectOption(field);
    for (const direction of ['asc', 'desc'] as const) {
      await page.getByLabel('Sort direction', { exact: true }).selectOption(direction);
      await expect(transactions(page)).toHaveCount(3);
      await expectResponsive(page, `${field} ${direction} results`);
    }
  }
});

test('responsive labeled demo and unsafe-total feedback do not hide content or functionality', async ({ page }) => {
  await page.goto('/?demo=1');
  await expect(page.getByRole('status', { name: 'Demo mode', exact: true })).toBeVisible();
  await expectResponsive(page, 'labeled demo');
  await page.getByLabel('Category filter', { exact: true }).selectOption('food');
  await expect(transactions(page)).toHaveCount(3);
  await page.getByLabel('Sort by', { exact: true }).selectOption('amount');
  await page.getByLabel('Sort direction', { exact: true }).selectOption('asc');
  await expectResponsive(page, 'demo filtered and sorted');

  await openUnsafeTotals(page);
  await expect(page.getByRole('alert').filter({ hasText: 'Some totals cannot be calculated exactly.' })).toBeVisible();
  await expectResponsive(page, 'unsafe totals');
});

test('200% browser zoom preserves populated, validation, and dialog flows without reflow defects', async ({ page, browserName }) => {
  test.skip(page.viewportSize()?.width === 320, 'Desktop browser-zoom scenario');
  expect(browserName).toBe('chromium');
  await openNormal(page);
  const session = await page.context().newCDPSession(page);
  await session.send('Emulation.setDeviceMetricsOverride', {
    width: 640,
    height: 360,
    screenWidth: 1280,
    screenHeight: 720,
    deviceScaleFactor: 2,
    mobile: false,
  });
  expect(await page.evaluate(() => ({ width: window.innerWidth, ratio: window.devicePixelRatio }))).toEqual({
    width: 640,
    ratio: 2,
  });
  await expectResponsive(page, '200% browser zoom populated');

  await page.getByLabel('Amount (USD)', { exact: true }).fill('0');
  await page.getByRole('button', { name: 'Add expense', exact: true }).press('Enter');
  await expectFocusVisibleAndUnobscured(page.getByLabel('Amount (USD)', { exact: true }));
  await expectResponsive(page, '200% browser zoom invalid add');

  const deletion = await requestDeletion(page);
  await expectFocusVisibleAndUnobscured(deletion.dialog.getByRole('button', { name: 'Cancel', exact: true }));
  await expectResponsive(page, '200% browser zoom deletion dialog');
  await session.send('Emulation.clearDeviceMetricsOverride');
});

test('200% text resize preserves dialog content, targets, and unobscured focus at desktop and 320px', async ({ page }) => {
  await openNormal(page);
  const deletion = await requestDeletion(page);
  await doubleRenderedText(page);
  await expectFocusVisibleAndUnobscured(deletion.dialog.getByRole('button', { name: 'Cancel', exact: true }));
  await expectResponsive(page, '200% text resize deletion dialog');
  await deletion.dialog.getByRole('button', { name: 'Cancel', exact: true }).press('Enter');
  await expectFocusVisibleAndUnobscured(deletion.requester);
});

test('200% text resize preserves invalid-edit feedback and validation focus', async ({ page }) => {
  await openNormal(page);
  await openEdit(page);
  await page.getByLabel('Amount (USD)', { exact: true }).fill('0');
  await doubleRenderedText(page);
  await saveEdit(page);
  await expectFocusVisibleAndUnobscured(page.getByLabel('Amount (USD)', { exact: true }));
  await expectResponsive(page, '200% text resize invalid edit');
});
