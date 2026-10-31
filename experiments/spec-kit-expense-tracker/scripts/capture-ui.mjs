import { chromium } from '../app/node_modules/@playwright/test/index.mjs';
import { mkdir, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const output = path.join(root, 'assets', 'screenshots');
const baseURL = process.env.EXPENSE_TRACKER_URL ?? 'http://127.0.0.1:4173';
await mkdir(output, { recursive: true });

const browser = await chromium.launch({ headless: true });
const errors = [];

async function captureState({ viewport, mobile = false, filename, prepare }) {
  const context = await browser.newContext({
    locale: 'en-US',
    timezoneId: 'America/New_York',
    isMobile: mobile,
    hasTouch: mobile,
  });
  try {
    const page = await context.newPage();
    page.on('pageerror', (error) => errors.push(error.message));
    page.on('console', (message) => {
      if (message.type() === 'error') errors.push(message.text());
    });
    await page.setViewportSize(viewport);
    await page.goto(`${baseURL}/?demo=1`, { waitUntil: 'networkidle' });
    await page.getByRole('heading', { name: 'Personal Expense Tracker' }).waitFor();
    await page.getByText('Fictional demo data.', { exact: false }).waitFor();
    await page.locator('[data-expense-id]').first().waitFor();
    await page.getByText('8 expenses shown', { exact: false }).waitFor();
    if (prepare) await prepare(page);
    const image = await page.screenshot({ fullPage: false, animations: 'disabled' });
    const width = image.readUInt32BE(16);
    const height = image.readUInt32BE(20);
    if (width !== viewport.width || height !== viewport.height) {
      throw new Error(`${filename}: rejected ${width}x${height} capture, expected ${viewport.width}x${viewport.height}`);
    }
    await writeFile(path.join(output, filename), image);
    console.log(`PASS: ${filename} is a genuine ${width}x${height} application viewport.`);
  } finally {
    await context.close();
  }
}

async function showDashboard(page) {
  await page.locator('.dashboard').evaluate((element) => element.scrollIntoView());
}

await captureState({
  viewport: { width: 1440, height: 900 },
  filename: '10-desktop-dashboard.png',
  prepare: showDashboard,
});

await captureState({
  viewport: { width: 1440, height: 900 },
  filename: '11-expense-creation.png',
  prepare: async (page) => {
    await page.getByLabel('Amount (USD)').fill('16.40');
    await page.getByLabel('Category', { exact: true }).selectOption('food');
    await page.getByLabel('Date', { exact: true }).fill('2026-10-22');
    await page.getByLabel('Note (optional)').fill('Team lunch');
  },
});

await captureState({
  viewport: { width: 1440, height: 900 },
  filename: '12-category-filtering.png',
  prepare: async (page) => {
    await page.getByLabel('Category filter').selectOption('food');
    await page.getByText('3 expenses shown for food', { exact: false }).waitFor();
    await showDashboard(page);
  },
});

await captureState({
  viewport: { width: 1440, height: 900 },
  filename: '13-invalid-amount-validation.png',
  prepare: async (page) => {
    await page.getByLabel('Amount (USD)').fill('-1');
    await page.locator('#expense-form-submit').click();
    await page.locator('#expense-amount-error').waitFor();
  },
});

await captureState({
  viewport: { width: 1440, height: 900 },
  filename: '14-deletion-confirmation.png',
  prepare: async (page) => {
    await page.locator('[data-expense-id="demo-008"]').getByRole('button', { name: 'Delete expense' }).click();
    await page.getByRole('dialog', { name: 'Delete expense?' }).waitFor();
    await page.getByRole('button', { name: 'Cancel' }).waitFor();
  },
});

await captureState({
  viewport: { width: 390, height: 844 },
  mobile: true,
  filename: '15-mobile-dashboard.png',
  prepare: showDashboard,
});

await browser.close();
if (errors.length > 0) throw new Error(`Browser console errors: ${errors.join(' | ')}`);
console.log('Captured six states using six fresh Playwright contexts. Browser console errors: 0.');
