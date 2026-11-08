import { expect, test } from "@playwright/test";

declare global {
  interface Window {
    __expenseStorageCalls: {
      reads: number;
      writes: number;
      storageListeners: number;
    };
  }
}

async function createExpenseWithKeyboard(
  page: import("@playwright/test").Page,
  amountText: string,
  note: string,
) {
  await page.getByLabel("Amount").focus();
  await page.keyboard.type(amountText);
  await page.getByLabel(/note/i).focus();
  await page.keyboard.type(note);
  await page.keyboard.press("Tab");
  await page.keyboard.press("Enter");
}

test.beforeEach(async ({ page }) => {
  await page.goto("/");
  await page.evaluate(() => window.localStorage.clear());
  await page.reload();
});

test("creates an expense with the keyboard and restores it after reload", async ({ page }) => {
  await createExpenseWithKeyboard(page, "18.75", "Bookstore");

  await expect(page.getByText("Bookstore")).toBeVisible();
  await expect(
    page.getByRole("list", { name: /expenses/i }).getByText("$18.75"),
  ).toBeVisible();
  await page.reload();
  await expect(page.getByText("Bookstore")).toBeVisible();
  await expect(
    page.getByRole("list", { name: /expenses/i }).getByText("$18.75"),
  ).toBeVisible();
});

test("announces invalid amount input without adding an expense", async ({ page }) => {
  await page.getByLabel("Amount").fill("100000.01");
  await page.getByRole("button", { name: /add expense/i }).click();

  await expect(page.getByRole("alert")).toContainText(/amount/i);
  await expect(page.getByText("$100,000.01")).toHaveCount(0);
});

test("exact demo mode is isolated and reload restores its deterministic records", async ({
  page,
}) => {
  await page.goto("/?demo=1");
  await expect(page.getByText(/demo mode/i)).toBeVisible();
  const expenses = page.getByRole("list", { name: /expenses/i });
  const initialCount = await expenses.getByRole("listitem").count();

  await createExpenseWithKeyboard(page, "4.50", "Temporary demo expense");
  await expect(expenses.getByText("Temporary demo expense")).toBeVisible();
  expect(await page.evaluate(() => window.localStorage.length)).toBe(0);

  await page.reload();
  await expect(page.getByText(/demo mode/i)).toBeVisible();
  await expect(page.getByRole("list", { name: /expenses/i }).getByRole("listitem")).toHaveCount(
    initialCount,
  );
  await expect(page.getByText("Temporary demo expense")).toHaveCount(0);
});

test("an additional query parameter does not activate demo mode", async ({ page }) => {
  await page.goto("/?demo=1&other=value");

  await expect(page.getByText(/demo mode/i)).toHaveCount(0);
});

test("filters and stably sorts monthly expenses with the keyboard", async ({ page }) => {
  const expenses = await page.evaluate(() => {
    const now = new Date();
    const month = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
    const records = [
      {
        id: "food-a",
        amountCents: 1200,
        category: "food",
        date: `${month}-02`,
        note: "Food A",
      },
      {
        id: "transport",
        amountCents: 3300,
        category: "transport",
        date: `${month}-03`,
        note: "Transport",
      },
      {
        id: "food-b",
        amountCents: 1200,
        category: "food",
        date: `${month}-03`,
        note: "Food B",
      },
    ];
    window.localStorage.setItem(
      "expense-tracker:expenses",
      JSON.stringify({ version: 1, expenses: records }),
    );
    return { month };
  });
  await page.reload();

  const expenseList = page.getByRole("list", { name: /expenses/i });
  const filter = page.getByLabel("Filter by category");
  await filter.focus();
  await page.keyboard.press("f");
  await page.keyboard.press("Enter");
  await expect(expenseList.getByRole("listitem")).toHaveCount(2);
  await expect(page.getByText("$57.00")).toBeVisible();

  await page.reload();
  const allExpenses = page.getByRole("list", { name: /expenses/i });
  const sortBy = page.getByLabel("Sort by");
  await sortBy.focus();
  await page.keyboard.press("a");
  await page.keyboard.press("Enter");
  const listText = () => allExpenses.locator("li").allTextContents();
  let sortedText = await listText();
  expect(sortedText[0]).toContain("Transport");
  expect(sortedText[1]).toContain("Food A");
  expect(sortedText[2]).toContain("Food B");

  const direction = page.getByLabel("Sort direction");
  await direction.focus();
  await page.keyboard.press("a");
  await page.keyboard.press("Enter");
  sortedText = await listText();
  expect(sortedText[0]).toContain("Food A");
  expect(sortedText[1]).toContain("Food B");
  expect(sortedText[2]).toContain("Transport");

  const monthPicker = page.getByRole("textbox", { name: "Month" });
  await monthPicker.fill("2001-01");
  await expect(page.getByText(/no expenses for this month/i)).toBeVisible();
  expect(expenses.month).not.toBe("2001-01");
});

test("edits an expense with the keyboard and updates its selected month", async ({ page }) => {
  const months = await page.evaluate(() => {
    const now = new Date();
    const month = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
    window.localStorage.setItem(
      "expense-tracker:expenses",
      JSON.stringify({
        version: 1,
        expenses: [
          {
            id: "edit-me",
            amountCents: 1200,
            category: "food",
            date: `${month}-02`,
            note: "Lunch",
          },
        ],
      }),
    );
    const next = new Date(now.getFullYear(), now.getMonth() + 1, 5);
    return {
      month: `${next.getFullYear()}-${String(next.getMonth() + 1).padStart(2, "0")}`,
      date: `${next.getFullYear()}-${String(next.getMonth() + 1).padStart(2, "0")}-05`,
    };
  });
  await page.reload();

  const editButton = page.getByRole("button", { name: "Edit Lunch" });
  await editButton.focus();
  await page.keyboard.press("Enter");
  await page.getByLabel("Amount").fill("15.00");
  await page.getByLabel("Category", { exact: true }).selectOption("transport");
  await page.getByLabel("Date").fill(months.date);
  await page.getByLabel(/note/i).fill("Train");
  const saveButton = page.getByRole("button", { name: "Save changes" });
  await saveButton.focus();
  await page.keyboard.press("Enter");

  await expect(page.getByText(/no expenses for this month/i)).toBeVisible();
  await page.getByRole("textbox", { name: "Month" }).fill(months.month);
  await expect(page.getByText("Train")).toBeVisible();
  await expect(page.getByRole("list", { name: /category totals/i })).toContainText(
    "$15.00",
  );
});

test("native delete dialog contains focus and cancellation restores the invoker", async ({
  page,
}) => {
  await page.evaluate(() => {
    const now = new Date();
    const month = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
    window.localStorage.setItem(
      "expense-tracker:expenses",
      JSON.stringify({
        version: 1,
        expenses: [
          {
            id: "delete-one",
            amountCents: 1800,
            category: "food",
            date: `${month}-02`,
            note: "Snack",
          },
        ],
      }),
    );
  });
  await page.reload();

  const invoker = page.getByRole("button", { name: "Delete Snack" });
  await invoker.focus();
  await page.keyboard.press("Enter");
  const dialog = page.getByRole("dialog", { name: /delete expense/i });
  const cancel = dialog.getByRole("button", { name: "Cancel" });
  const confirm = dialog.getByRole("button", { name: "Delete" });
  await expect(cancel).toBeFocused();
  await page.keyboard.press("Tab");
  await expect(confirm).toBeFocused();
  await page.keyboard.press("Tab");
  await expect(cancel).toBeFocused();
  await page.keyboard.press("Escape");

  await expect(dialog).toBeHidden();
  await expect(invoker).toBeFocused();
  await expect(page.getByRole("list", { name: /expenses/i }).getByRole("listitem")).toHaveCount(
    1,
  );
  await invoker.click();
  await dialog.getByRole("button", { name: "Cancel" }).click();
  await expect(invoker).toBeFocused();
});

test("confirmed deletion follows visible order and falls back to Add expense", async ({
  page,
}) => {
  await page.evaluate(() => {
    const now = new Date();
    const month = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
    window.localStorage.setItem(
      "expense-tracker:expenses",
      JSON.stringify({
        version: 1,
        expenses: [
          {
            id: "newest",
            amountCents: 3000,
            category: "food",
            date: `${month}-03`,
            note: "Newest",
          },
          {
            id: "middle",
            amountCents: 2000,
            category: "food",
            date: `${month}-02`,
            note: "Middle",
          },
          {
            id: "oldest",
            amountCents: 1000,
            category: "food",
            date: `${month}-01`,
            note: "Oldest",
          },
        ],
      }),
    );
  });
  await page.reload();

  const filter = page.getByLabel("Filter by category");
  await filter.focus();
  await page.keyboard.press("f");
  await page.keyboard.press("Enter");
  await page.getByRole("button", { name: "Delete Middle" }).click();
  let dialog = page.getByRole("dialog", { name: /delete expense/i });
  await dialog.getByRole("button", { name: "Delete" }).click();
  await expect(page.getByRole("button", { name: "Edit Oldest" })).toBeFocused();

  await page.getByRole("button", { name: "Delete Oldest" }).click();
  dialog = page.getByRole("dialog", { name: /delete expense/i });
  await dialog.getByRole("button", { name: "Delete" }).click();
  await expect(page.getByRole("button", { name: "Edit Newest" })).toBeFocused();

  await page.getByRole("button", { name: "Delete Newest" }).click();
  dialog = page.getByRole("dialog", { name: /delete expense/i });
  await dialog.getByRole("button", { name: "Delete" }).click();
  await expect(page.getByRole("button", { name: "Add expense" })).toBeFocused();
});

test("deleting the expense being edited clears the draft and returns focus to Add expense", async ({
  page,
}) => {
  await page.evaluate(() => {
    const now = new Date();
    const month = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
    window.localStorage.setItem(
      "expense-tracker:expenses",
      JSON.stringify({
        version: 1,
        expenses: [
          {
            id: "being-edited",
            amountCents: 3000,
            category: "food",
            date: `${month}-02`,
            note: "Being edited",
          },
        ],
      }),
    );
  });
  await page.reload();

  await page.getByRole("button", { name: "Edit Being edited" }).click();
  await page.getByLabel("Amount").fill("99.99");
  await page.getByRole("button", { name: "Delete Being edited" }).click();
  const dialog = page.getByRole("dialog", { name: /delete expense/i });
  await dialog.getByRole("button", { name: "Delete" }).click();

  await expect(page.getByRole("heading", { name: "Add expense" })).toBeVisible();
  await expect(page.getByLabel("Amount")).toHaveValue("");
  await expect(page.getByRole("button", { name: "Add expense" })).toBeFocused();
  await expect(page.getByRole("list", { name: /expenses/i }).getByRole("listitem")).toHaveCount(
    0,
  );
});

test("deleting another record cancels the active edit before Add expense fallback", async ({
  page,
}) => {
  await page.evaluate(() => {
    const now = new Date();
    const month = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
    window.localStorage.setItem(
      "expense-tracker:expenses",
      JSON.stringify({
        version: 1,
        expenses: [
          {
            id: "being-edited",
            amountCents: 1200,
            category: "transport",
            date: `${month}-03`,
            note: "Keep editing",
          },
          {
            id: "delete-visible",
            amountCents: 1800,
            category: "food",
            date: `${month}-02`,
            note: "Delete visible",
          },
        ],
      }),
    );
  });
  await page.reload();

  await page.getByRole("button", { name: "Edit Keep editing" }).click();
  await page.getByLabel("Amount").fill("99.99");
  await page.getByLabel("Filter by category").selectOption("food");
  await page.getByRole("button", { name: "Delete Delete visible" }).click();
  const dialog = page.getByRole("dialog", { name: /delete expense/i });
  await dialog.getByRole("button", { name: "Delete" }).click();

  await expect(page.getByRole("heading", { name: "Add expense" })).toBeVisible();
  await expect(page.getByLabel("Amount")).toHaveValue("");
  await expect(page.getByRole("button", { name: "Add expense" })).toBeFocused();

  await page.getByLabel("Filter by category").selectOption("all");
  await expect(page.getByText("Keep editing")).toBeVisible();
  await expect(page.getByRole("list", { name: /expenses/i })).toContainText("$12.00");
  await expect(page.getByRole("list", { name: /expenses/i })).not.toContainText("$99.99");
});

test("reports a storage read failure and retries without showing an empty fallback", async ({
  page,
}) => {
  await page.addInitScript(() => {
    const originalGetItem = Storage.prototype.getItem;
    let shouldFail = true;
    Storage.prototype.getItem = function (key: string) {
      if (key === "expense-tracker:expenses" && shouldFail) {
        shouldFail = false;
        throw new Error("storage unavailable");
      }
      return originalGetItem.call(this, key);
    };
  });
  await page.reload();

  await expect(page.getByRole("alert")).toContainText(/could not load expenses/i);
  await expect(page.getByRole("button", { name: "Retry loading" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Add expense" })).toHaveCount(0);
  await page.getByRole("button", { name: "Retry loading" }).click();
  await expect(page.getByRole("heading", { name: "Your expenses" })).toBeVisible();
});

test("retains failed-write work in memory and reload restores durable data", async ({ page }) => {
  await page.evaluate(() => {
    const now = new Date();
    const month = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
    window.localStorage.setItem(
      "expense-tracker:expenses",
      JSON.stringify({
        version: 1,
        expenses: [
          {
            id: "durable",
            amountCents: 500,
            category: "food",
            date: `${month}-02`,
            note: "Durable",
          },
        ],
      }),
    );
  });
  await page.reload();
  const durableValue = await page.evaluate(() =>
    window.localStorage.getItem("expense-tracker:expenses"),
  );
  await page.evaluate(() => {
    const originalSetItem = Storage.prototype.setItem;
    let shouldFail = true;
    Storage.prototype.setItem = function (key: string, value: string) {
      if (key === "expense-tracker:expenses" && shouldFail) {
        shouldFail = false;
        throw new Error("quota exceeded");
      }
      return originalSetItem.call(this, key, value);
    };
  });

  await page.getByLabel("Amount").fill("3.25");
  await page.getByLabel(/note/i).fill("Unsaved");
  await page.getByRole("button", { name: "Add expense" }).click();
  await expect(page.getByRole("status")).toContainText(/not saved.*lost if you reload/i);
  await expect(page.getByText("Unsaved")).toBeVisible();
  expect(await page.evaluate(() => window.localStorage.getItem("expense-tracker:expenses"))).toBe(
    durableValue,
  );

  await page.reload();
  await expect(page.getByText("Durable")).toBeVisible();
  await expect(page.getByText("Unsaved")).toHaveCount(0);
});

test("the next successful write persists the complete in-memory collection", async ({ page }) => {
  await page.evaluate(() => {
    const now = new Date();
    const month = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
    window.localStorage.setItem(
      "expense-tracker:expenses",
      JSON.stringify({
        version: 1,
        expenses: [
          {
            id: "durable",
            amountCents: 500,
            category: "food",
            date: `${month}-02`,
            note: "Durable",
          },
        ],
      }),
    );
  });
  await page.reload();
  await page.evaluate(() => {
    const originalSetItem = Storage.prototype.setItem;
    let shouldFail = true;
    Storage.prototype.setItem = function (key: string, value: string) {
      if (key === "expense-tracker:expenses" && shouldFail) {
        shouldFail = false;
        throw new Error("quota exceeded");
      }
      return originalSetItem.call(this, key, value);
    };
  });

  await page.getByLabel("Amount").fill("3.25");
  await page.getByLabel(/note/i).fill("First unsaved");
  await page.getByRole("button", { name: "Add expense" }).click();
  await expect(page.getByRole("status")).toContainText(/not saved/i);
  await page.getByLabel("Amount").fill("4.25");
  await page.getByLabel(/note/i).fill("Second expense");
  await page.getByRole("button", { name: "Add expense" }).click();

  await expect(page.getByRole("status")).toContainText(/expense saved/i);
  const persisted = await page.evaluate(() =>
    JSON.parse(window.localStorage.getItem("expense-tracker:expenses") ?? "null"),
  );
  expect(persisted.expenses.map((expense: { note: string }) => expense.note)).toEqual([
    "Second expense",
    "First unsaved",
    "Durable",
  ]);
  await page.reload();
  await expect(page.getByText("First unsaved")).toBeVisible();
  await expect(page.getByText("Second expense")).toBeVisible();
});

test("informed start fresh replaces malformed storage with an empty versioned envelope", async ({
  page,
}) => {
  await page.evaluate(() => {
    window.localStorage.setItem("expense-tracker:expenses", "{malformed");
  });
  await page.reload();

  await expect(page.getByRole("alert")).toContainText(/malformed/i);
  const dialogPromise = page.waitForEvent("dialog");
  const clickPromise = page.getByRole("button", { name: "Start fresh" }).click();
  const confirmation = await dialogPromise;
  expect(confirmation.message()).toMatch(/replace.*malformed.*clear.*current/i);
  await confirmation.accept();
  await clickPromise;

  await expect(page.getByRole("heading", { name: "Your expenses" })).toBeVisible();
  expect(
    await page.evaluate(() =>
      window.localStorage.getItem("expense-tracker:expenses"),
    ),
  ).toBe(JSON.stringify({ version: 1, expenses: [] }));
});

test("failed start fresh preserves malformed storage and keeps the warning visible", async ({
  page,
}) => {
  await page.evaluate(() => {
    window.localStorage.setItem("expense-tracker:expenses", "{malformed");
  });
  await page.addInitScript(() => {
    const originalSetItem = Storage.prototype.setItem;
    Storage.prototype.setItem = function (key: string, value: string) {
      if (key === "expense-tracker:expenses") {
        throw new Error("storage unavailable");
      }
      return originalSetItem.call(this, key, value);
    };
  });
  await page.reload();

  const dialogPromise = page.waitForEvent("dialog");
  const clickPromise = page.getByRole("button", { name: "Start fresh" }).click();
  await (await dialogPromise).accept();
  await clickPromise;
  await expect(page.getByRole("alert")).toContainText(/malformed/i);
  await expect(page.getByRole("status")).toContainText(/could not start fresh/i);
  expect(
    await page.evaluate(() =>
      window.localStorage.getItem("expense-tracker:expenses"),
    ),
  ).toBe("{malformed");
});

test("exact demo mode makes no expense storage calls or storage listener registrations", async ({
  page,
}) => {
  await page.addInitScript(() => {
    window.__expenseStorageCalls = {
      reads: 0,
      writes: 0,
      storageListeners: 0,
    };
    const originalGetItem = Storage.prototype.getItem;
    Storage.prototype.getItem = new Proxy(originalGetItem, {
      apply(target, thisArg, args: [string]) {
        window.__expenseStorageCalls.reads += 1;
        return Reflect.apply(target, thisArg, args);
      },
    });
    const originalSetItem = Storage.prototype.setItem;
    Storage.prototype.setItem = new Proxy(originalSetItem, {
      apply(target, thisArg, args: [string, string]) {
        window.__expenseStorageCalls.writes += 1;
        return Reflect.apply(target, thisArg, args);
      },
    });
    window.addEventListener = new Proxy(window.addEventListener, {
      apply(target, thisArg, args: [string, EventListenerOrEventListenerObject]) {
        if (args[0] === "storage") {
          window.__expenseStorageCalls.storageListeners += 1;
        }
        return Reflect.apply(target, thisArg, args);
      },
    });
  });
  await page.goto("/?demo=1");
  await createExpenseWithKeyboard(page, "4.50", "Demo only");

  expect(
    await page.evaluate(() => window.__expenseStorageCalls),
  ).toEqual({ reads: 0, writes: 0, storageListeners: 0 });
  expect(await page.evaluate(() => window.localStorage.length)).toBe(0);
});

test("dashboard has no page-level horizontal overflow at phone, tablet, and desktop sizes", async ({
  page,
}) => {
  await page.goto("/?demo=1");

  for (const viewport of [
    { width: 390, height: 844 },
    { width: 768, height: 1024 },
    { width: 1440, height: 900 },
  ]) {
    await page.setViewportSize(viewport);
    const dimensions = await page.evaluate(() => ({
      clientWidth: document.documentElement.clientWidth,
      scrollWidth: document.documentElement.scrollWidth,
    }));
    expect(dimensions.scrollWidth).toBeLessThanOrEqual(dimensions.clientWidth);
    await expect(page.getByRole("heading", { name: "Expense Tracker" })).toBeVisible();
  }
});
