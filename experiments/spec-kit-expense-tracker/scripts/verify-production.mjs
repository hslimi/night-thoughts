import { chromium, expect } from "@playwright/test";
import { writeFile } from "node:fs/promises";

const baseURL = process.env.APP_URL ?? "http://127.0.0.1:4173";
const storageKey = "expense-tracker:expenses";
const browser = await chromium.launch({ headless: true });
const checks = [];
const consoleErrors = [];

function localDate(date = new Date()) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

async function createContext(viewport = { width: 1440, height: 900 }) {
  const context = await browser.newContext({ viewport });
  const page = await context.newPage();
  page.on("pageerror", (error) => consoleErrors.push(`pageerror: ${error.message}`));
  page.on("console", (message) => {
    if (message.type() === "error") {
      consoleErrors.push(`console: ${message.text()}`);
    }
  });
  return { context, page };
}

async function openNormal(page) {
  await page.goto(baseURL);
  await page.evaluate(() => window.localStorage.clear());
  await page.reload();
  await expect(page.getByRole("heading", { name: "Expense Tracker" })).toBeVisible();
}

async function addExpense(page, amount, note, category = "food") {
  await page.getByLabel("Amount", { exact: true }).fill(amount);
  await page.getByLabel("Category", { exact: true }).selectOption(category);
  await page.getByLabel("Date", { exact: true }).fill(localDate());
  await page.getByLabel(/note/i).fill(note);
  await page.getByRole("button", { name: "Add expense", exact: true }).click();
}

try {
  const { context, page } = await createContext();
  await openNormal(page);
  const today = localDate();
  const currentMonth = today.slice(0, 7);
  await expect(page.getByLabel("Month", { exact: true })).toHaveValue(currentMonth);

  await page.getByLabel("Amount", { exact: true }).focus();
  await page.keyboard.type("12.50");
  await page.getByLabel("Date", { exact: true }).fill(today);
  await page.getByLabel(/note/i).focus();
  await page.keyboard.type("Coffee");
  await page.getByRole("button", { name: "Add expense", exact: true }).focus();
  await page.keyboard.press("Enter");
  await expect(page.getByText("Coffee", { exact: true })).toBeVisible();
  await expect(page.getByRole("region", { name: "Monthly summary" })).toContainText("$12.50");
  checks.push("keyboard create and current-month total");

  await page.reload();
  await expect(page.getByText("Coffee", { exact: true })).toBeVisible();
  const persisted = await page.evaluate((key) => JSON.parse(window.localStorage.getItem(key)), storageKey);
  expect(persisted.expenses[0].amountCents).toBe(1250);
  checks.push("integer-cent persistence after reload");

  const initialRaw = await page.evaluate((key) => window.localStorage.getItem(key), storageKey);
  for (const invalid of ["-2.50", "1.234", "0", "100000.01"]) {
    await page.getByLabel("Amount", { exact: true }).fill(invalid);
    await page.getByRole("button", { name: "Add expense", exact: true }).click();
    await expect(page.getByRole("alert")).toContainText("amount");
  }
  expect(await page.evaluate((key) => window.localStorage.getItem(key), storageKey)).toBe(initialRaw);
  checks.push("negative, malformed, zero, and over-limit amounts rejected without writes");

  await addExpense(page, "20.00", "Metro", "transport");
  const summary = page.getByRole("region", { name: "Monthly summary" });
  await expect(summary).toContainText("$32.50");
  await expect(page.getByRole("list", { name: "Category totals" }).locator("li").filter({ hasText: "Food" })).toContainText("$12.50");
  await expect(page.getByRole("list", { name: "Category totals" }).locator("li").filter({ hasText: "Transport" })).toContainText("$20.00");
  checks.push("exact monthly and category totals");

  await page.getByLabel("Filter by category").selectOption("food");
  await expect(page.getByRole("list", { name: "Expenses" }).getByRole("listitem")).toHaveCount(1);
  await expect(page.getByText("Coffee", { exact: true })).toBeVisible();
  await page.getByLabel("Filter by category").selectOption("all");
  await page.getByLabel("Sort by", { exact: true }).selectOption("amount");
  await page.getByLabel("Sort direction").selectOption("ascending");
  const notes = await page.getByRole("list", { name: "Expenses" }).locator(".expense-description strong").allTextContents();
  expect(notes).toEqual(["Coffee", "Metro"]);
  checks.push("category filtering and amount sorting");

  await page.getByRole("button", { name: "Edit Coffee" }).click();
  await page.getByLabel("Amount", { exact: true }).fill("15.00");
  await page.getByRole("button", { name: "Save changes" }).click();
  await expect(summary).toContainText("$35.00");
  await page.reload();
  await expect(page.getByRole("region", { name: "Monthly summary" })).toContainText("$35.00");
  checks.push("edit updates and persists summaries");

  const deleteInvoker = page.getByRole("button", { name: "Delete Metro" });
  await deleteInvoker.focus();
  await page.keyboard.press("Enter");
  const dialog = page.getByRole("dialog", { name: /delete expense/i });
  const cancel = dialog.getByRole("button", { name: "Cancel" });
  await expect(cancel).toBeFocused();
  await page.keyboard.press("Tab");
  await expect(dialog.getByRole("button", { name: "Delete", exact: true })).toBeFocused();
  await page.keyboard.press("Tab");
  await expect(cancel).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(dialog).toBeHidden();
  await expect(deleteInvoker).toBeFocused();
  await expect(page.getByText("Metro", { exact: true })).toBeVisible();
  checks.push("keyboard deletion cancel, focus containment, and focus restoration");

  await deleteInvoker.click();
  await dialog.getByRole("button", { name: "Delete", exact: true }).click();
  await expect(page.getByText("Metro", { exact: true })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Edit Coffee", exact: true })).toBeFocused();
  await page.reload();
  await expect(page.getByText("Metro", { exact: true })).toHaveCount(0);
  await expect(page.getByRole("region", { name: "Monthly summary" })).toContainText("$15.00");
  checks.push("confirmed permanent deletion, previous-record focus, and durable totals");

  const cdp = await context.newCDPSession(page);
  const accessibilityTree = await cdp.send("Accessibility.getFullAXTree");
  const namedControls = accessibilityTree.nodes
    .filter((node) => ["button", "textbox", "combobox"].includes(node.role?.value))
    .map((node) => ({ role: node.role.value, name: node.name?.value ?? "" }));
  expect(namedControls.some((control) => control.role === "button" && control.name === "Add expense")).toBe(true);
  expect(namedControls.every((control) => control.name.length > 0)).toBe(true);
  checks.push("Chromium accessibility tree exposes named primary controls");

  for (const viewport of [{ width: 1440, height: 900 }, { width: 768, height: 1024 }, { width: 390, height: 844 }]) {
    await page.setViewportSize(viewport);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
    expect(overflow).toBe(false);
    checks.push(`no page-level horizontal overflow at ${viewport.width}x${viewport.height}`);
  }
  await context.close();

  const failureContext = await createContext();
  const failurePage = failureContext.page;
  await failurePage.addInitScript((key) => {
    const original = Storage.prototype.setItem;
    let failOnce = true;
    Storage.prototype.setItem = function (name, value) {
      if (name === key && failOnce) {
        failOnce = false;
        throw new DOMException("Simulated quota failure", "QuotaExceededError");
      }
      return original.call(this, name, value);
    };
  }, storageKey);
  await openNormal(failurePage);
  await addExpense(failurePage, "8.75", "Unsaved lunch");
  await expect(failurePage.getByText(/not saved/i)).toBeVisible();
  await expect(failurePage.getByText("Unsaved lunch", { exact: true })).toBeVisible();
  await addExpense(failurePage, "2.00", "Recovery save");
  const recovered = await failurePage.evaluate((key) => JSON.parse(window.localStorage.getItem(key)), storageKey);
  expect(recovered.expenses.map((expense) => expense.note).sort()).toEqual(["Recovery save", "Unsaved lunch"]);
  await failurePage.reload();
  await expect(failurePage.getByText("Unsaved lunch", { exact: true })).toBeVisible();
  await expect(failurePage.getByText("Recovery save", { exact: true })).toBeVisible();
  checks.push("failed write stays visible and later success saves the complete collection");
  await failureContext.context.close();

  const malformedContext = await createContext();
  const malformedPage = malformedContext.page;
  await openNormal(malformedPage);
  await malformedPage.evaluate((key) => window.localStorage.setItem(key, "{malformed"), storageKey);
  await malformedPage.reload();
  await expect(malformedPage.getByRole("alert")).toContainText("malformed");
  malformedPage.once("dialog", (nativeDialog) => nativeDialog.dismiss());
  await malformedPage.getByRole("button", { name: "Start fresh" }).click();
  expect(await malformedPage.evaluate((key) => window.localStorage.getItem(key), storageKey)).toBe("{malformed");
  malformedPage.once("dialog", (nativeDialog) => nativeDialog.accept());
  await malformedPage.getByRole("button", { name: "Start fresh" }).click();
  await expect(malformedPage.getByText(/no expenses for this month/i)).toBeVisible();
  expect(await malformedPage.evaluate((key) => window.localStorage.getItem(key), storageKey)).toBe(JSON.stringify({ version: 1, expenses: [] }));
  checks.push("malformed storage survives cancellation and resets only after informed confirmation");
  await malformedContext.context.close();

  const readContext = await createContext();
  const readPage = readContext.page;
  await readPage.addInitScript((key) => {
    const original = Storage.prototype.getItem;
    let failOnce = true;
    Storage.prototype.getItem = function (name) {
      if (name === key && failOnce) {
        failOnce = false;
        throw new DOMException("Simulated read failure", "SecurityError");
      }
      return original.call(this, name);
    };
  }, storageKey);
  await readPage.goto(baseURL);
  await expect(readPage.getByRole("alert")).toContainText("Could not load");
  await readPage.getByRole("button", { name: "Retry loading" }).click();
  await expect(readPage.getByText(/no expenses for this month/i)).toBeVisible();
  checks.push("read failure announces the problem and retries without replacing data");
  await readContext.context.close();

  expect(consoleErrors).toEqual([]);
  checks.push("no browser console errors or uncaught page errors");

  await writeFile(
    "evidence/verification/production-browser.json",
    JSON.stringify({
      applicationURL: baseURL,
      verifiedAt: new Date().toISOString(),
      browser: "Playwright Chromium",
      checks,
      namedAccessibilityControls: namedControls,
      consoleErrors,
      screenReaderReview: "Not performed",
    }, null, 2) + "\n",
  );
  console.log(`Production browser verification passed: ${checks.length} checks`);
  for (const check of checks) {
    console.log(`PASS ${check}`);
  }
} finally {
  await browser.close();
}
