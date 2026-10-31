import { expect, test, type Locator, type Page } from '@playwright/test';
import { buildScaleEnvelope } from '../tests/fixtures/scaleData';

const storageKey = 'personal-expense-tracker:expenses:v1';
const seedMarker = 'scale-spec:seeded';
const categories = ['food', 'transport', 'housing', 'entertainment', 'other'] as const;

type Category = (typeof categories)[number];
type SortField = 'date' | 'amount';
type SortDirection = 'asc' | 'desc';

type ExpectedExpense = {
  id: string;
  amountCents: number;
  category: Category;
  date: string;
  note: string;
};

type PersistedEnvelope = {
  version: number;
  expenses: ExpectedExpense[];
};

const rawScaleEnvelope = JSON.stringify(buildScaleEnvelope());

function expectedExpense(i: number): ExpectedExpense {
  return {
    id: `scale-${String(i).padStart(4, '0')}`,
    amountCents: ((i * 7919) % 100000) + 1,
    category: categories[(i - 1) % 5]!,
    date: `2026-${String(((i - 1) % 10) + 1).padStart(2, '0')}-${String(((i - 1) % 28) + 1).padStart(2, '0')}`,
    note: `Scale expense ${i}`,
  };
}

const expectedExpenses = Array.from({ length: 1000 }, (_, index) => expectedExpense(index + 1));

function compareText(first: string, second: string) {
  return first < second ? -1 : first > second ? 1 : 0;
}

function expectedVisibleExpenses(
  expenses: ExpectedExpense[],
  month: string,
  category: Category | 'all' = 'all',
  sortField: SortField = 'date',
  sortDirection: SortDirection = 'desc',
) {
  const direction = sortDirection === 'asc' ? 1 : -1;
  return expenses
    .filter((expense) =>
      expense.date.startsWith(`${month}-`) && (category === 'all' || expense.category === category))
    .sort((first, second) => {
      const primary = sortField === 'date'
        ? compareText(first.date, second.date)
        : first.amountCents - second.amountCents;
      return primary * direction || compareText(first.id, second.id);
    });
}

function formatCents(cents: number) {
  const dollars = String(Math.floor(cents / 100)).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
  return `$${dollars}.${String(cents % 100).padStart(2, '0')}`;
}

function expectedRendered(expenses: ExpectedExpense[]) {
  return expenses.map((expense) => ({
    id: expense.id,
    category: expense.category,
    date: expense.date,
    dateText: expense.date,
    amount: formatCents(expense.amountCents),
    note: expense.note,
  }));
}

async function readRendered(page: Page) {
  return page.locator('li[data-expense-id]').evaluateAll((items) =>
    items.map((item) => {
      const time = item.querySelector('time');
      return {
        id: item.getAttribute('data-expense-id'),
        category: item.querySelector('.category-tag')?.textContent ?? null,
        date: time?.getAttribute('datetime') ?? null,
        dateText: time?.textContent ?? null,
        amount: item.querySelector('.transaction__amount')?.textContent ?? null,
        note: item.querySelector('.transaction-note')?.textContent ?? null,
      };
    }),
  );
}

async function readPersisted(page: Page): Promise<PersistedEnvelope> {
  const raw = await page.evaluate((key) => window.localStorage.getItem(key), storageKey);
  expect(raw).not.toBeNull();
  return JSON.parse(raw!) as PersistedEnvelope;
}

async function expectMonthView(
  page: Page,
  expenses: ExpectedExpense[],
  month: string,
  category: Category | 'all' = 'all',
  sortField: SortField = 'date',
  sortDirection: SortDirection = 'desc',
) {
  const monthExpenses = expenses.filter((expense) => expense.date.startsWith(`${month}-`));
  const expectedTotal = monthExpenses.reduce((total, expense) => total + expense.amountCents, 0);
  await expect(page.getByLabel('Month', { exact: true })).toHaveValue(month);
  await expect(page.getByLabel('Monthly total', { exact: true })).toHaveText(formatCents(expectedTotal));
  for (const summaryCategory of categories) {
    const expectedCategoryTotal = monthExpenses
      .filter((expense) => expense.category === summaryCategory)
      .reduce((total, expense) => total + expense.amountCents, 0);
    const label = `${summaryCategory[0]!.toUpperCase()}${summaryCategory.slice(1)} total`;
    await expect(page.getByLabel(label, { exact: true })).toHaveText(formatCents(expectedCategoryTotal));
  }
  const visible = expectedVisibleExpenses(expenses, month, category, sortField, sortDirection);
  await expect.poll(() => readRendered(page)).toEqual(expectedRendered(visible));
}

async function openScale(page: Page) {
  await page.addInitScript(
    ({ key, marker, raw }) => {
      if (window.sessionStorage.getItem(marker) !== 'yes') {
        window.localStorage.setItem(key, raw);
        window.sessionStorage.setItem(marker, 'yes');
      }
    },
    { key: storageKey, marker: seedMarker, raw: rawScaleEnvelope },
  );
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Personal Expense Tracker' })).toBeVisible();
  await expect(page.locator('li[data-expense-id]')).toHaveCount(100);
}

async function resetScale(page: Page) {
  await page.evaluate(
    ({ key, raw }) => window.localStorage.setItem(key, raw),
    { key: storageKey, raw: rawScaleEnvelope },
  );
  await page.reload();
  await expect(page.getByLabel('Month', { exact: true })).toHaveValue('2026-10');
  await expect(page.locator('li[data-expense-id]')).toHaveCount(100);
}

async function selectMonth(page: Page, month: string) {
  const control = page.getByLabel('Month', { exact: true });
  await control.fill(month);
  await control.press('Tab');
}

async function setSelect(control: Locator, value: string) {
  await control.selectOption(value);
  await expect(control).toHaveValue(value);
}

async function fillExpense(
  page: Page,
  values: { amount: string; category: Category; date: string; note: string },
) {
  await page.getByLabel('Amount (USD)', { exact: true }).fill(values.amount);
  await setSelect(page.getByLabel('Category', { exact: true }), values.category);
  await page.getByLabel('Date', { exact: true }).fill(values.date);
  await page.getByLabel('Note (optional)', { exact: true }).fill(values.note);
}

async function openEdit(page: Page, id: string) {
  const requester = page.locator(`li[data-expense-id="${id}"]`)
    .getByRole('button', { name: 'Edit expense', exact: true });
  await requester.focus();
  await requester.press('Enter');
  await expect(page.getByRole('heading', { name: 'Edit expense', exact: true })).toBeVisible();
}

async function openDelete(page: Page, id: string) {
  const requester = page.locator(`li[data-expense-id="${id}"]`)
    .getByRole('button', { name: 'Delete expense', exact: true });
  await requester.focus();
  await requester.press('Enter');
  const dialog = page.getByRole('dialog', { name: 'Delete expense?', exact: true });
  await expect(dialog).toBeVisible();
  return dialog;
}

async function timed(
  label: string,
  activate: () => Promise<void>,
  expectExactVisibleResult: () => Promise<void>,
) {
  const startedAt = performance.now();
  await activate();
  await expectExactVisibleResult();
  const elapsedMilliseconds = performance.now() - startedAt;
  test.info().annotations.push({
    type: 'SCALE-002 timing',
    description: `${label}: ${elapsedMilliseconds.toFixed(1)} ms`,
  });
  expect(
    elapsedMilliseconds,
    `${label} took ${elapsedMilliseconds.toFixed(1)} ms from committed activation to the exact visible result`,
  ).toBeLessThan(2000);
}

test.describe.configure({ mode: 'serial' });
test.use({ timezoneId: 'America/Los_Angeles' });

test.beforeEach(async ({ page }) => {
  await page.clock.install({ time: new Date('2026-10-31T12:00:00-07:00') });
});

test('SCALE-001: all 1,000 persisted records and January-October views match independent expectations', async ({ page }) => {
  test.setTimeout(180_000);
  await openScale(page);
  await page.reload();

  const persisted = await readPersisted(page);
  expect(persisted.version).toBe(1);
  expect(persisted.expenses).toHaveLength(1000);
  expect(persisted.expenses.map((expense) => expense.amountCents))
    .toEqual(expectedExpenses.map((expense) => expense.amountCents));
  expect(persisted.expenses.every((expense) => Number.isSafeInteger(expense.amountCents))).toBe(true);
  expect(persisted.expenses).toEqual(expectedExpenses);

  for (let monthNumber = 1; monthNumber <= 10; monthNumber += 1) {
    const month = `2026-${String(monthNumber).padStart(2, '0')}`;
    await selectMonth(page, month);
    await expectMonthView(page, expectedExpenses, month);
  }
});

test('SCALE-002: three exact sub-two-second repetitions of every scale interaction', async ({ page }) => {
  test.setTimeout(600_000);
  await openScale(page);

  for (let repetition = 1; repetition <= 3; repetition += 1) {
    await resetScale(page);
    await fillExpense(page, {
      amount: '543.21',
      category: 'entertainment',
      date: '2026-10-31',
      note: 'Scale timed add',
    });
    const submit = page.getByRole('button', { name: 'Add expense', exact: true });
    await submit.focus();
    await timed(`add repetition ${repetition}`, () => submit.press('Enter'), async () => {
      const saved = await readPersisted(page);
      const added = saved.expenses.find((expense) => expense.note === 'Scale timed add');
      expect(added).toBeDefined();
      const expectedCollection = [...expectedExpenses, {
        id: added!.id,
        amountCents: 54321,
        category: 'entertainment',
        date: '2026-10-31',
        note: 'Scale timed add',
      }];
      await expectMonthView(page, expectedCollection, '2026-10');
      expect(saved).toEqual({ version: 1, expenses: expectedCollection });
    });
  }

  const sameMonthEdit: ExpectedExpense = {
    ...expectedExpense(10),
    amountCents: 123456,
    category: 'transport',
    date: '2026-10-31',
    note: 'Scale same-month edit',
  };
  const sameMonthCollection = expectedExpenses.map((expense) =>
    expense.id === sameMonthEdit.id ? sameMonthEdit : expense);
  for (let repetition = 1; repetition <= 3; repetition += 1) {
    await resetScale(page);
    await openEdit(page, sameMonthEdit.id);
    await fillExpense(page, {
      amount: '1234.56',
      category: 'transport',
      date: '2026-10-31',
      note: 'Scale same-month edit',
    });
    const save = page.getByRole('button', { name: 'Save changes', exact: true });
    await save.focus();
    await timed(`same-month edit repetition ${repetition}`, () => save.press('Enter'), async () => {
      await expectMonthView(page, sameMonthCollection, '2026-10');
      expect(await readPersisted(page)).toEqual({ version: 1, expenses: sameMonthCollection });
    });
  }

  const crossMonthEdit: ExpectedExpense = {
    ...expectedExpense(10),
    amountCents: 24680,
    category: 'housing',
    date: '2026-09-30',
    note: 'Scale cross-month edit',
  };
  const crossMonthCollection = expectedExpenses.map((expense) =>
    expense.id === crossMonthEdit.id ? crossMonthEdit : expense);
  for (let repetition = 1; repetition <= 3; repetition += 1) {
    await resetScale(page);
    await openEdit(page, crossMonthEdit.id);
    await fillExpense(page, {
      amount: '246.80',
      category: 'housing',
      date: '2026-09-30',
      note: 'Scale cross-month edit',
    });
    const save = page.getByRole('button', { name: 'Save changes', exact: true });
    await save.focus();
    await timed(`cross-month edit repetition ${repetition}`, () => save.press('Enter'), async () => {
      await expectMonthView(page, crossMonthCollection, '2026-10');
      await expect(page.getByRole('status', { name: 'Expense status', exact: true }))
        .toContainText('Expense moved to 2026-09.');
      expect(await readPersisted(page)).toEqual({ version: 1, expenses: crossMonthCollection });
    });
    await selectMonth(page, '2026-09');
    await expectMonthView(page, crossMonthCollection, '2026-09');
  }

  const deletedId = expectedExpense(10).id;
  const deletionCollection = expectedExpenses.filter((expense) => expense.id !== deletedId);
  for (let repetition = 1; repetition <= 3; repetition += 1) {
    await resetScale(page);
    const dialog = await openDelete(page, deletedId);
    const confirm = dialog.getByRole('button', { name: 'Confirm deletion', exact: true });
    await confirm.focus();
    await timed(`delete repetition ${repetition}`, () => confirm.press('Enter'), async () => {
      await expectMonthView(page, deletionCollection, '2026-10');
      expect(await readPersisted(page)).toEqual({ version: 1, expenses: deletionCollection });
    });
  }

  for (let repetition = 1; repetition <= 3; repetition += 1) {
    await resetScale(page);
    const month = page.getByLabel('Month', { exact: true });
    await month.focus();
    await timed(`month selection repetition ${repetition}`, () => month.fill('2026-09'), async () => {
      await expectMonthView(page, expectedExpenses, '2026-09');
    });
  }

  for (const category of categories) {
    for (let repetition = 1; repetition <= 3; repetition += 1) {
      await resetScale(page);
      const filter = page.getByLabel('Category filter', { exact: true });
      await filter.focus();
      await timed(`${category} filter repetition ${repetition}`, () => setSelect(filter, category), async () => {
        await expectMonthView(page, expectedExpenses, '2026-10', category);
      });
    }
  }

  for (const scenario of [
    { field: 'date', direction: 'asc' },
    { field: 'date', direction: 'desc' },
    { field: 'amount', direction: 'asc' },
    { field: 'amount', direction: 'desc' },
  ] as const) {
    for (let repetition = 1; repetition <= 3; repetition += 1) {
      await resetScale(page);
      if (scenario.field === 'amount') {
        await setSelect(page.getByLabel('Sort by', { exact: true }), 'amount');
      }
      const direction = page.getByLabel('Sort direction', { exact: true });
      await setSelect(direction, scenario.direction === 'asc' ? 'desc' : 'asc');
      await direction.focus();
      await timed(
        `${scenario.field} ${scenario.direction} sort repetition ${repetition}`,
        () => setSelect(direction, scenario.direction),
        () => expectMonthView(
          page,
          expectedExpenses,
          '2026-10',
          'all',
          scenario.field,
          scenario.direction,
        ),
      );
    }
  }
});
