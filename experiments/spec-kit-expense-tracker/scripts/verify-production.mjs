import { chromium, expect } from '../app/node_modules/@playwright/test/index.mjs';

const baseURL = process.env.EXPENSE_TRACKER_URL ?? 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true });
const results = [];
const errors = [];

function passed(message) {
  results.push(`PASS: ${message}`);
}

async function addExpense(page, amount, category, date, note) {
  await page.getByLabel('Amount (USD)').fill(amount);
  await page.getByLabel('Category', { exact: true }).selectOption(category);
  await page.getByLabel('Date', { exact: true }).fill(date);
  await page.getByLabel('Note (optional)').fill(note);
  await page.locator('#expense-form-submit').click();
}

const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
const page = await context.newPage();
page.on('pageerror', (error) => errors.push(error.message));
page.on('console', (message) => {
  if (message.type() === 'error') errors.push(message.text());
});
await page.goto(baseURL, { waitUntil: 'networkidle' });
await page.getByLabel('Month', { exact: true }).fill('2026-10');

await addExpense(page, '10.10', 'food', '2026-10-01', 'Verification purchase');
await addExpense(page, '20.20', 'transport', '2026-10-31', 'Monthly pass');
await addExpense(page, '1.00', 'other', '2026-09-30', 'Previous month');
await expect(page.getByLabel('Monthly total')).toHaveText('$30.30');
await expect(page.getByLabel('Food total')).toHaveText('$10.10');
await expect(page.getByLabel('Transport total')).toHaveText('$20.20');
passed('create and exact monthly/category totals with September excluded');

await page.getByLabel('Category filter').selectOption('food');
await expect(page.locator('.transaction-list li')).toHaveCount(1);
await expect(page.getByLabel('Monthly total')).toHaveText('$30.30');
passed('category filtering preserves the unfiltered summary');

await page.getByLabel('Category filter').selectOption('all');
await page.getByLabel('Sort by').selectOption('amount');
await page.getByLabel('Sort direction').selectOption('asc');
await expect(page.locator('.transaction-list li').first().locator('.transaction__amount')).toHaveText('$10.10');
passed('amount sorting is exact and deterministic');

const original = page.locator('.transaction-list li').filter({ hasText: 'Verification purchase' });
await original.getByRole('button', { name: 'Edit expense' }).click();
await page.getByLabel('Amount (USD)').fill('15.15');
await page.getByLabel('Date', { exact: true }).fill('2026-10-02');
await page.getByLabel('Note (optional)').fill('Edited verification');
await page.locator('#expense-form-submit').click();
await expect(page.getByLabel('Monthly total')).toHaveText('$35.35');
passed('edit recalculates the affected monthly total');

const transport = page.locator('.transaction-list li').filter({ hasText: 'Monthly pass' });
await transport.getByRole('button', { name: 'Delete expense' }).click();
await expect(page.getByRole('dialog', { name: 'Delete expense?' })).toBeVisible();
await expect(page.getByRole('button', { name: 'Cancel' })).toBeFocused();
await page.keyboard.press('Escape');
await expect(page.getByLabel('Monthly total')).toHaveText('$35.35');
await transport.getByRole('button', { name: 'Delete expense' }).click();
await page.getByRole('button', { name: 'Confirm deletion' }).click();
await expect(page.getByLabel('Monthly total')).toHaveText('$15.15');
passed('deletion requires confirmation, starts on Cancel, and preserves data on Escape');

await page.reload({ waitUntil: 'networkidle' });
await page.getByLabel('Month', { exact: true }).fill('2026-10');
await expect(page.getByLabel('Monthly total')).toHaveText('$15.15');
await expect(page.getByText('Edited verification')).toBeVisible();
passed('edited data persists after a production reload');

for (const invalid of ['-1', 'abc', '1.234', '0']) {
  await page.getByLabel('Amount (USD)').fill(invalid);
  await page.locator('#expense-form-submit').click();
  await expect(page.locator('#expense-amount-error')).toBeVisible();
  await expect(page.getByLabel('Monthly total')).toHaveText('$15.15');
}
passed('negative, malformed, excess-precision, and zero amounts are visibly rejected');

await page.getByLabel('Amount (USD)').fill('2.50');
await page.getByLabel('Category', { exact: true }).selectOption('entertainment');
await page.getByLabel('Date', { exact: true }).fill('2026-10-05');
await page.getByLabel('Note (optional)').fill('Keyboard entry');
await page.locator('#expense-form-submit').focus();
await page.keyboard.press('Enter');
await expect(page.getByLabel('Monthly total')).toHaveText('$17.65');
passed('expense creation is operable by keyboard');

await page.getByLabel('Month', { exact: true }).fill('2026-09');
await expect(page.getByLabel('Monthly total')).toHaveText('$1.00');
await page.getByLabel('Month', { exact: true }).fill('2026-10');
await expect(page.getByLabel('Monthly total')).toHaveText('$17.65');
passed('month navigation keeps adjacent-month totals isolated');

for (const width of [1440, 390]) {
  await page.setViewportSize({ width, height: width === 390 ? 844 : 900 });
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
  if (overflow) throw new Error(`Horizontal overflow at ${width}px`);
}
passed('desktop and 390px layouts have no horizontal overflow');
await context.close();

const malformedContext = await browser.newContext();
await malformedContext.addInitScript(() => {
  localStorage.setItem('personal-expense-tracker:expenses:v1', '{broken');
});
const malformed = await malformedContext.newPage();
malformed.on('pageerror', (error) => errors.push(error.message));
await malformed.goto(baseURL, { waitUntil: 'networkidle' });
await expect(malformed.getByLabel('Persistence status')).toBeVisible();
await malformed.getByRole('button', { name: 'Start fresh' }).click();
await expect(malformed.getByRole('button', { name: 'Cancel' })).toBeFocused();
await malformed.getByRole('button', { name: 'Cancel' }).click();
const raw = await malformed.evaluate(() => localStorage.getItem('personal-expense-tracker:expenses:v1'));
if (raw !== '{broken') throw new Error('Malformed raw data changed without confirmation');
passed('malformed storage warns and remains unchanged after recovery cancellation');
await malformedContext.close();
await browser.close();

if (errors.length > 0) throw new Error(`Browser console errors: ${errors.join(' | ')}`);
passed('no browser console errors in production scenarios');
console.log(results.join('\n'));
