import { expect, test, type Page } from '@playwright/test';

const storageKey = 'personal-expense-tracker:expenses:v1';
const seedMarker = 'persistence-spec:seeded';

type Expense = {
  id: string;
  amountCents: number;
  category: 'food' | 'transport' | 'housing' | 'entertainment' | 'other';
  date: string;
  note?: string;
};

type WriteFailure = 'quota' | 'access' | null;

type PersistenceProbe = {
  writes: number;
  writeValues: string[];
  serializationFailures: number;
  writeFailure: WriteFailure;
  failNextStringify: boolean;
};

declare global {
  interface Window {
    __persistenceSpec: PersistenceProbe;
  }
}

const durableExpense: Expense = {
  id: 'durable-001',
  amountCents: 1250,
  category: 'food',
  date: '2026-10-10',
  note: 'Durable lunch',
};

const completeCollection: Expense[] = [
  {
    id: 'expense-b',
    amountCents: 2550,
    category: 'food',
    date: '2026-10-15',
    note: 'Exact note',
  },
  {
    id: 'expense-a',
    amountCents: 100,
    category: 'transport',
    date: '2026-10-01',
  },
  {
    id: 'expense-c',
    amountCents: 99999999999,
    category: 'other',
    date: '2026-09-30',
    note: 'Large previous-month expense',
  },
];

function envelope(expenses: Expense[]) {
  return JSON.stringify({ version: 1, expenses });
}

async function openTracker(page: Page, options: { raw?: string; unreadable?: boolean } = {}) {
  await page.addInitScript(
    ({ key, marker, raw, unreadable }) => {
      const storage = window.localStorage;
      if (window.sessionStorage.getItem(marker) !== 'yes') {
        if (raw === null) storage.removeItem(key);
        else storage.setItem(key, raw);
        window.sessionStorage.setItem(marker, 'yes');
      }

      const probe: PersistenceProbe = {
        writes: 0,
        writeValues: [],
        serializationFailures: 0,
        writeFailure: null,
        failNextStringify: false,
      };
      window.__persistenceSpec = probe;

      const originalGetItem = Storage.prototype.getItem;
      Storage.prototype.getItem = function (itemKey) {
        if (this === storage && unreadable && itemKey === key) {
          throw new DOMException('Injected storage read failure', 'SecurityError');
        }
        return originalGetItem.call(this, itemKey);
      };

      const originalSetItem = Storage.prototype.setItem;
      Storage.prototype.setItem = function (itemKey, value) {
        if (this === storage) {
          probe.writes += 1;
          probe.writeValues.push(String(value));
          if (itemKey === key && probe.writeFailure) {
            const name = probe.writeFailure === 'quota' ? 'QuotaExceededError' : 'SecurityError';
            throw new DOMException('Injected storage write failure', name);
          }
        }
        return originalSetItem.call(this, itemKey, value);
      };

      const originalStringify = JSON.stringify;
      JSON.stringify = ((value: unknown, ...rest: unknown[]) => {
        if (
          probe.failNextStringify &&
          value !== null &&
          typeof value === 'object' &&
          (value as { version?: unknown }).version === 1 &&
          Array.isArray((value as { expenses?: unknown }).expenses)
        ) {
          probe.failNextStringify = false;
          probe.serializationFailures += 1;
          throw new TypeError('Injected envelope serialization failure');
        }
        return Reflect.apply(originalStringify, JSON, [value, ...rest]);
      }) as typeof JSON.stringify;
    },
    {
      key: storageKey,
      marker: seedMarker,
      raw: options.raw ?? null,
      unreadable: options.unreadable ?? false,
    },
  );
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Personal Expense Tracker' })).toBeVisible();
}

async function readRaw(page: Page) {
  return page.evaluate((key) => window.localStorage.getItem(key), storageKey);
}

async function readProbe(page: Page) {
  return page.evaluate(() => ({
    writes: window.__persistenceSpec.writes,
    writeValues: [...window.__persistenceSpec.writeValues],
    serializationFailures: window.__persistenceSpec.serializationFailures,
  }));
}

async function setWriteFailure(page: Page, failure: WriteFailure) {
  await page.evaluate((value) => {
    window.__persistenceSpec.writeFailure = value;
  }, failure);
}

async function failNextSerialization(page: Page) {
  await page.evaluate(() => {
    window.__persistenceSpec.failNextStringify = true;
  });
}

async function addExpense(
  page: Page,
  values: { amount: string; category?: Expense['category']; date: string; note?: string },
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

function transactions(page: Page) {
  return page.getByRole('list', { name: 'Transactions' }).getByRole('listitem');
}

function recoveryWarning(page: Page) {
  return page.getByRole('alert', { name: 'Persistence status', exact: true });
}

async function expectRecoveryWarning(page: Page, options: { unreadable?: boolean } = {}) {
  const warning = recoveryWarning(page);
  await expect(warning).toBeVisible();
  await expect(warning).toContainText(/saved information/i);
  await expect(warning).toContainText(/temporary/i);
  await expect(warning).toContainText(/confirm/i);
  if (options.unreadable) {
    await expect(warning).not.toContainText(/raw|byte|unchanged|inspect|compar|pars(?:e|ed|ing)|JSON/i);
  }
  return warning;
}

async function expectWriteWarning(page: Page) {
  const warning = recoveryWarning(page);
  await expect(warning).toBeVisible();
  await expect(warning).toContainText(/not (?:durably )?saved|could not save|couldn't save|unable to save/i);
  await expect(warning).toContainText(/expense|work|latest|add/i);
  return warning;
}

async function expectNoPersistenceSuccess(page: Page) {
  const status = page.getByRole('status', { name: 'Expense status' });
  if (await status.count()) {
    await expect(status).not.toContainText(
      /saved successfully|successfully saved|replacement complete|started fresh/i,
    );
  }
}

async function expectReplacementDialog(page: Page) {
  const dialog = page.getByRole('dialog', { name: /replace saved information/i });
  await expect(dialog).toBeVisible();
  await expect(dialog).toContainText(/irreversibly|cannot be recovered|can't be recovered/i);
  const cancel = dialog.getByRole('button', { name: 'Cancel', exact: true });
  const confirm = dialog.getByRole('button', { name: 'Confirm replacement', exact: true });
  await expect(cancel).toBeFocused();
  await cancel.press('Shift+Tab');
  await expect(confirm).toBeFocused();
  await confirm.press('Tab');
  await expect(cancel).toBeFocused();
  return { dialog, cancel, confirm };
}

async function expectGuardedAddDialog(page: Page, note: string, expectedWrites = 0) {
  await expect(transactions(page).filter({ hasText: note })).toHaveCount(1);
  const dialog = await expectReplacementDialog(page);
  expect((await readProbe(page)).writes).toBe(expectedWrites);
  return dialog;
}

test.use({ timezoneId: 'America/Los_Angeles' });

test.beforeEach(async ({ page }) => {
  await page.clock.install({ time: new Date('2026-10-31T12:00:00-07:00') });
});

test('PERSIST-001: missing storage opens a normal empty dashboard without recovery UI', async ({ page }) => {
  await openTracker(page);

  await expect(page.getByLabel('Month', { exact: true })).toHaveValue('2026-10');
  await expect(page.getByLabel('Monthly total', { exact: true })).toHaveText('$0.00');
  await expect(transactions(page)).toHaveCount(0);
  await expect(recoveryWarning(page)).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Start fresh', exact: true })).toHaveCount(0);
  expect((await readProbe(page)).writes).toBe(0);
});

test('PERSIST-002: a valid envelope reloads the exact complete collection without alteration', async ({ page }) => {
  const raw = envelope(completeCollection);
  await openTracker(page, { raw });

  await expect(recoveryWarning(page)).toHaveCount(0);
  await expect(transactions(page)).toHaveCount(2);
  await expect(transactions(page).nth(0)).toContainText('2026-10-15');
  await expect(transactions(page).nth(0)).toContainText('$25.50');
  await expect(transactions(page).nth(0)).toContainText('Exact note');
  await expect(transactions(page).nth(1)).toContainText('2026-10-01');
  await expect(transactions(page).nth(1)).toContainText('$1.00');
  await expect(page.getByLabel('Monthly total', { exact: true })).toHaveText('$26.50');
  await selectMonth(page, '2026-09');
  await expect(transactions(page)).toHaveCount(1);
  await expect(transactions(page)).toContainText('$999,999,999.99');
  await expect(transactions(page)).toContainText('Large previous-month expense');
  expect(await readRaw(page)).toBe(raw);

  await page.reload();
  await expect(page.getByLabel('Month', { exact: true })).toHaveValue('2026-10');
  await expect(transactions(page)).toHaveCount(2);
  await expect(page.getByLabel('Monthly total', { exact: true })).toHaveText('$26.50');
  expect(await readRaw(page)).toBe(raw);
  expect((await readProbe(page)).writes).toBe(0);
});

test('PERSIST-003: malformed JSON rejects everything and cancellation preserves exact raw bytes', async ({ page }) => {
  const raw = '{"version":1,"expenses":[ broken Café\n  ';
  await openTracker(page, { raw });

  await expectRecoveryWarning(page);
  await expect(transactions(page)).toHaveCount(0);
  await expect(page.getByLabel('Monthly total', { exact: true })).toHaveText('$0.00');
  expect(await readRaw(page)).toBe(raw);
  expect((await readProbe(page)).writes).toBe(0);

  await page.getByRole('button', { name: 'Start fresh', exact: true }).click();
  const { dialog, cancel } = await expectReplacementDialog(page);
  await cancel.click();
  await expect(dialog).toHaveCount(0);
  await expectRecoveryWarning(page);
  await expect(transactions(page)).toHaveCount(0);
  expect(await readRaw(page)).toBe(raw);
  expect((await readProbe(page)).writes).toBe(0);
});

for (const [classification, raw] of [
  ['unsupported version', envelope([]).replace('"version":1', '"version":2')],
  ['invalid envelope shape', JSON.stringify({ version: 1, expenses: { 0: durableExpense } })],
] as const) {
  test(`PERSIST-004: ${classification} requires all-or-nothing recovery without a write`, async ({ page }) => {
    await openTracker(page, { raw });

    await expectRecoveryWarning(page);
    await expect(transactions(page)).toHaveCount(0);
    expect(await readRaw(page)).toBe(raw);
    await page.getByRole('button', { name: 'Start fresh', exact: true }).click();
    const { cancel } = await expectReplacementDialog(page);
    await cancel.click();
    expect(await readRaw(page)).toBe(raw);
    expect((await readProbe(page)).writes).toBe(0);
  });
}

test('PERSIST-005: one invalid record rejects the entire otherwise-valid collection', async ({ page }) => {
  const invalid = { ...durableExpense, id: 'invalid-record', amountCents: 12.5 };
  const raw = JSON.stringify({ version: 1, expenses: [durableExpense, invalid] });
  await openTracker(page, { raw });

  await expectRecoveryWarning(page);
  await expect(transactions(page)).toHaveCount(0);
  await expect(page.getByText('Durable lunch', { exact: true })).toHaveCount(0);
  await expect(page.getByLabel('Monthly total', { exact: true })).toHaveText('$0.00');
  await page.getByRole('button', { name: 'Start fresh', exact: true }).click();
  const { cancel } = await expectReplacementDialog(page);
  await cancel.click();
  expect(await readRaw(page)).toBe(raw);
  expect((await readProbe(page)).writes).toBe(0);
});

test('PERSIST-006: duplicate IDs reject the complete collection', async ({ page }) => {
  const duplicate = { ...durableExpense, amountCents: 999, note: 'Duplicate identity' };
  const raw = envelope([durableExpense, duplicate]);
  await openTracker(page, { raw });

  await expectRecoveryWarning(page);
  await expect(transactions(page)).toHaveCount(0);
  await expect(page.getByText('Durable lunch', { exact: true })).toHaveCount(0);
  await page.getByRole('button', { name: 'Start fresh', exact: true }).click();
  const { cancel } = await expectReplacementDialog(page);
  await cancel.click();
  expect(await readRaw(page)).toBe(raw);
  expect((await readProbe(page)).writes).toBe(0);
});

test('PERSIST-007: unreadable storage performs zero writes before or after cancellation', async ({ page }) => {
  await openTracker(page, { unreadable: true });

  await expectRecoveryWarning(page, { unreadable: true });
  await expect(transactions(page)).toHaveCount(0);
  expect((await readProbe(page)).writes).toBe(0);

  await page.getByRole('button', { name: 'Start fresh', exact: true }).click();
  const { dialog, cancel } = await expectReplacementDialog(page);
  await cancel.click();
  await expect(dialog).toHaveCount(0);
  await expectRecoveryWarning(page, { unreadable: true });
  await expect(transactions(page)).toHaveCount(0);
  expect((await readProbe(page)).writes).toBe(0);
});

test('PERSIST-008: a quota-failed add stays visible with a warning and is omitted after reload', async ({ page }) => {
  const raw = envelope([durableExpense]);
  await openTracker(page, { raw });
  await setWriteFailure(page, 'quota');

  await addExpense(page, { amount: '23.45', date: '2026-10-20', note: 'Quota-only memory' });
  await expect(transactions(page)).toHaveCount(2);
  await expect(transactions(page).filter({ hasText: 'Quota-only memory' })).toContainText('$23.45');
  await expectWriteWarning(page);
  await expectNoPersistenceSuccess(page);
  expect((await readProbe(page)).writes).toBe(1);
  expect(await readRaw(page)).toBe(raw);

  await page.reload();
  await expect(recoveryWarning(page)).toHaveCount(0);
  await expect(transactions(page)).toHaveCount(1);
  await expect(page.getByText('Quota-only memory', { exact: true })).toHaveCount(0);
  await expect(page.getByText('Durable lunch', { exact: true })).toBeVisible();
  expect(await readRaw(page)).toBe(raw);
});

test('PERSIST-011: envelope serialization failure retains work without writes or destructive fallback', async ({ page }) => {
  const raw = envelope([durableExpense]);
  await openTracker(page, { raw });
  await failNextSerialization(page);

  await addExpense(page, { amount: '10.01', date: '2026-10-21', note: 'Serialization-only memory' });
  await expect(transactions(page)).toHaveCount(2);
  await expect(page.getByText('Serialization-only memory', { exact: true })).toBeVisible();
  await expectWriteWarning(page);
  await expectNoPersistenceSuccess(page);
  const probe = await readProbe(page);
  expect(probe.serializationFailures).toBe(1);
  expect(probe.writes).toBe(0);
  expect(await readRaw(page)).toBe(raw);
});

test('PERSIST-012: a mid-session storage access failure retains the complete add only in memory', async ({ page }) => {
  const raw = envelope([durableExpense]);
  await openTracker(page, { raw });
  expect(await readRaw(page)).toBe(raw);
  await setWriteFailure(page, 'access');

  await addExpense(page, { amount: '19.99', date: '2026-10-22', note: 'Access-failure memory' });
  await expect(transactions(page)).toHaveCount(2);
  await expect(page.getByText('Access-failure memory', { exact: true })).toBeVisible();
  await expectWriteWarning(page);
  expect((await readProbe(page)).writes).toBe(1);
  expect(await readRaw(page)).toBe(raw);

  await page.reload();
  await expect(transactions(page)).toHaveCount(1);
  await expect(page.getByText('Access-failure memory', { exact: true })).toHaveCount(0);
  await expect(page.getByText('Durable lunch', { exact: true })).toBeVisible();
});

test('PERSIST-013: a later save writes every retained change, clears warning, and survives reload', async ({ page }) => {
  await openTracker(page, { raw: envelope([durableExpense]) });
  await setWriteFailure(page, 'quota');
  await addExpense(page, { amount: '2.25', category: 'transport', date: '2026-10-11', note: 'Retained first add' });
  await expectWriteWarning(page);
  expect(await readRaw(page)).toBe(envelope([durableExpense]));

  await setWriteFailure(page, null);
  await expectWriteWarning(page);
  await addExpense(page, { amount: '3.75', category: 'other', date: '2026-10-12', note: 'Successful later add' });
  await expect(recoveryWarning(page)).toHaveCount(0);
  await expect(transactions(page)).toHaveCount(3);

  const saved = JSON.parse((await readProbe(page)).writeValues.at(-1)!) as {
    version: number;
    expenses: Expense[];
  };
  expect(saved.version).toBe(1);
  expect(saved.expenses).toHaveLength(3);
  expect(saved.expenses).toEqual(
    expect.arrayContaining([
      durableExpense,
      expect.objectContaining({ amountCents: 225, category: 'transport', date: '2026-10-11', note: 'Retained first add' }),
      expect.objectContaining({ amountCents: 375, category: 'other', date: '2026-10-12', note: 'Successful later add' }),
    ]),
  );
  expect(new Set(saved.expenses.map((expense) => expense.id)).size).toBe(3);
  expect(await readRaw(page)).toBe(JSON.stringify(saved));

  await page.reload();
  await expect(recoveryWarning(page)).toHaveCount(0);
  await expect(transactions(page)).toHaveCount(3);
  await expect(page.getByText('Retained first add', { exact: true })).toBeVisible();
  await expect(page.getByText('Successful later add', { exact: true })).toBeVisible();
  await expect(page.getByLabel('Monthly total', { exact: true })).toHaveText('$18.50');
});

test('RECOVERY-001: start-fresh Cancel and Escape retain empty guarded memory and exact raw data', async ({ page }) => {
  const raw = '{ definitely not an envelope }';
  await openTracker(page, { raw });
  const startFresh = page.getByRole('button', { name: 'Start fresh', exact: true });

  for (const cancellation of ['cancel', 'escape'] as const) {
    await startFresh.click();
    const { dialog, cancel } = await expectReplacementDialog(page);
    if (cancellation === 'cancel') await cancel.click();
    else await page.keyboard.press('Escape');
    await expect(dialog).toHaveCount(0);
    await expect(startFresh).toBeFocused();
    await expectRecoveryWarning(page);
    await expect(transactions(page)).toHaveCount(0);
    expect(await readRaw(page)).toBe(raw);
    expect((await readProbe(page)).writes).toBe(0);
  }
});

test('RECOVERY-002: confirmed start fresh writes one empty version-1 envelope and clears recovery', async ({ page }) => {
  await openTracker(page, { raw: '{broken' });
  await expectRecoveryWarning(page);

  await page.getByRole('button', { name: 'Start fresh', exact: true }).click();
  const { dialog, confirm } = await expectReplacementDialog(page);
  expect(await readRaw(page)).toBe('{broken');
  await confirm.click();
  await expect(dialog).toHaveCount(0);
  await expect(recoveryWarning(page)).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Start fresh', exact: true })).toHaveCount(0);
  await expect(transactions(page)).toHaveCount(0);
  const probe = await readProbe(page);
  expect(probe.writes).toBe(1);
  expect(JSON.parse(probe.writeValues[0]!)).toEqual({ version: 1, expenses: [] });
  expect(await readRaw(page)).toBe(envelope([]));

  await page.reload();
  await expect(recoveryWarning(page)).toHaveCount(0);
  await expect(transactions(page)).toHaveCount(0);
  expect(await readRaw(page)).toBe(envelope([]));
});

test('RECOVERY-003: failed start fresh makes no success claim and never automatically retries', async ({ page }) => {
  const raw = '{broken start fresh}';
  await openTracker(page, { raw });
  await setWriteFailure(page, 'quota');

  await page.getByRole('button', { name: 'Start fresh', exact: true }).click();
  const { confirm } = await expectReplacementDialog(page);
  await confirm.click();
  await expectWriteWarning(page);
  await expectRecoveryWarning(page);
  await expectNoPersistenceSuccess(page);
  await expect(transactions(page)).toHaveCount(0);
  expect(await readRaw(page)).toBe(raw);
  await page.waitForTimeout(100);
  expect((await readProbe(page)).writes).toBe(1);
});

test('RECOVERY-004: guarded work survives first-save Cancel and Escape with no write', async ({ page }) => {
  const raw = '{"version":1,"expenses":[';
  await openTracker(page, { raw });

  await addExpense(page, { amount: '4.25', date: '2026-10-16', note: 'Guarded cancel work' });
  let dialog = await expectGuardedAddDialog(page, 'Guarded cancel work');
  expect(await readRaw(page)).toBe(raw);
  await dialog.cancel.click();
  await expect(dialog.dialog).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Add expense', exact: true })).toBeFocused();
  await expectRecoveryWarning(page);
  await expect(page.getByText('Guarded cancel work', { exact: true })).toBeVisible();

  await addExpense(page, { amount: '5.75', date: '2026-10-17', note: 'Guarded Escape work' });
  dialog = await expectGuardedAddDialog(page, 'Guarded Escape work');
  await page.keyboard.press('Escape');
  await expect(dialog.dialog).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Add expense', exact: true })).toBeFocused();
  await expectRecoveryWarning(page);
  await expect(transactions(page)).toHaveCount(2);
  expect(await readRaw(page)).toBe(raw);
  expect((await readProbe(page)).writes).toBe(0);
});

test('RECOVERY-005: confirmed first replacement saves the complete guarded collection and reloads it', async ({ page }) => {
  const raw = 'old malformed value that must not be salvaged';
  await openTracker(page, { raw });

  await addExpense(page, { amount: '7.10', date: '2026-10-18', note: 'First guarded record' });
  const cancelled = await expectGuardedAddDialog(page, 'First guarded record');
  await cancelled.cancel.click();
  await addExpense(page, { amount: '8.20', category: 'transport', date: '2026-10-19', note: 'Second guarded record' });
  const confirmed = await expectGuardedAddDialog(page, 'Second guarded record');
  expect(await readRaw(page)).toBe(raw);
  await confirmed.confirm.click();

  await expect(confirmed.dialog).toHaveCount(0);
  await expect(recoveryWarning(page)).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Start fresh', exact: true })).toHaveCount(0);
  await expect(transactions(page)).toHaveCount(2);
  const probe = await readProbe(page);
  expect(probe.writes).toBe(1);
  const saved = JSON.parse(probe.writeValues[0]!) as { version: number; expenses: Expense[] };
  expect(saved.version).toBe(1);
  expect(saved.expenses).toHaveLength(2);
  expect(saved.expenses).toEqual(
    expect.arrayContaining([
      expect.objectContaining({ amountCents: 710, category: 'food', date: '2026-10-18', note: 'First guarded record' }),
      expect.objectContaining({ amountCents: 820, category: 'transport', date: '2026-10-19', note: 'Second guarded record' }),
    ]),
  );
  expect(saved.expenses.every((expense) => expense.id.length > 0)).toBe(true);

  await page.reload();
  await expect(recoveryWarning(page)).toHaveCount(0);
  await expect(transactions(page)).toHaveCount(2);
  await expect(page.getByText('First guarded record', { exact: true })).toBeVisible();
  await expect(page.getByText('Second guarded record', { exact: true })).toBeVisible();
  await expect(page.getByLabel('Monthly total', { exact: true })).toHaveText('$15.30');
  expect(await readRaw(page)).toBe(JSON.stringify(saved));
});

for (const failure of ['serialization', 'quota', 'access'] as const) {
  test(`RECOVERY-006: ${failure} failure retains guarded work and recovery without retry`, async ({ page }) => {
    const raw = `{broken ${failure}}`;
    await openTracker(page, { raw });
    await addExpense(page, { amount: '11.11', date: '2026-10-20', note: `Retained ${failure} work` });
    const { confirm } = await expectGuardedAddDialog(page, `Retained ${failure} work`);
    if (failure === 'serialization') await failNextSerialization(page);
    else await setWriteFailure(page, failure);

    await confirm.click();
    await expectWriteWarning(page);
    await expectRecoveryWarning(page);
    await expectNoPersistenceSuccess(page);
    await expect(page.getByText(`Retained ${failure} work`, { exact: true })).toBeVisible();
    expect(await readRaw(page)).toBe(raw);
    await page.waitForTimeout(100);
    const probe = await readProbe(page);
    expect(probe.writes).toBe(failure === 'serialization' ? 0 : 1);
    expect(probe.serializationFailures).toBe(failure === 'serialization' ? 1 : 0);
  });
}

test('RECOVERY-007: unreadable cancellation, failure, and success write only after explicit confirmation', async ({ page }) => {
  await openTracker(page, { unreadable: true });
  await expectRecoveryWarning(page, { unreadable: true });

  await addExpense(page, { amount: '1.25', date: '2026-10-21', note: 'Unreadable cancelled work' });
  let dialog = await expectGuardedAddDialog(page, 'Unreadable cancelled work');
  await dialog.cancel.click();
  await expectRecoveryWarning(page, { unreadable: true });
  await expect(page.getByText('Unreadable cancelled work', { exact: true })).toBeVisible();
  expect((await readProbe(page)).writes).toBe(0);

  await addExpense(page, { amount: '2.50', date: '2026-10-22', note: 'Unreadable failed work' });
  dialog = await expectGuardedAddDialog(page, 'Unreadable failed work');
  await setWriteFailure(page, 'access');
  await dialog.confirm.click();
  await expect(dialog.dialog).toHaveCount(0);
  await expectWriteWarning(page);
  await expectRecoveryWarning(page, { unreadable: true });
  await expectNoPersistenceSuccess(page);
  await expect(transactions(page)).toHaveCount(2);
  await page.waitForTimeout(100);
  expect((await readProbe(page)).writes).toBe(1);

  await setWriteFailure(page, null);
  await addExpense(page, { amount: '3.75', date: '2026-10-23', note: 'Unreadable successful work' });
  dialog = await expectGuardedAddDialog(page, 'Unreadable successful work', 1);
  expect((await readProbe(page)).writes).toBe(1);
  await dialog.confirm.click();
  await expect(dialog.dialog).toHaveCount(0);
  await expect(recoveryWarning(page)).toHaveCount(0);
  await expect(transactions(page)).toHaveCount(3);

  const probe = await readProbe(page);
  expect(probe.writes).toBe(2);
  const saved = JSON.parse(probe.writeValues.at(-1)!) as { version: number; expenses: Expense[] };
  expect(saved.version).toBe(1);
  expect(saved.expenses).toHaveLength(3);
  expect(saved.expenses).toEqual(
    expect.arrayContaining([
      expect.objectContaining({ amountCents: 125, note: 'Unreadable cancelled work' }),
      expect.objectContaining({ amountCents: 250, note: 'Unreadable failed work' }),
      expect.objectContaining({ amountCents: 375, note: 'Unreadable successful work' }),
    ]),
  );
});
