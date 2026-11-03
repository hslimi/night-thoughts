import { chromium, expect } from "@playwright/test";
import { mkdir, writeFile } from "node:fs/promises";

const baseURL = process.env.APP_URL ?? "http://127.0.0.1:4173";
const outputDirectory = "evidence/.capture-tmp";
await mkdir(outputDirectory, { recursive: true });
const browser = await chromium.launch({ headless: true });
const captures = [];

async function capture({ name, viewport, selector, prepare }) {
  const context = await browser.newContext({ viewport, deviceScaleFactor: 1 });
  const page = await context.newPage();
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error") {
      errors.push(message.text());
    }
  });

  await page.goto(`${baseURL}/?demo=1`);
  await expect(page.getByRole("heading", { name: "Expense Tracker" })).toBeVisible();
  await expect(page.getByText(/demo mode/i)).toBeVisible();
  await expect(page.getByRole("list", { name: "Expenses" }).getByRole("listitem")).toHaveCount(2);
  if (prepare) {
    await prepare(page);
  }

  const path = `${outputDirectory}/${name}.png`;
  await page.screenshot({ path, fullPage: false });
  let crop = null;
  if (selector) {
    const box = await page.locator(selector).boundingBox();
    if (!box) {
      throw new Error(`No capture bounds for ${selector}`);
    }
    const margin = 20;
    crop = {
      x: Math.max(0, Math.floor(box.x - margin)),
      y: Math.max(0, Math.floor(box.y - margin)),
      width: Math.min(viewport.width - Math.max(0, Math.floor(box.x - margin)), Math.ceil(box.width + margin * 2)),
      height: Math.min(viewport.height - Math.max(0, Math.floor(box.y - margin)), Math.ceil(box.height + margin * 2)),
    };
  }
  captures.push({ name, viewport, crop, fictionalDemoData: true, consoleErrors: errors });
  expect(errors).toEqual([]);
  await context.close();
}

try {
  await capture({
    name: "10-desktop-dashboard",
    viewport: { width: 1440, height: 900 },
    prepare: async (page) => {
      await page.evaluate(() => window.scrollTo(0, 80));
    },
  });
  await capture({
    name: "11-expense-form",
    viewport: { width: 1440, height: 900 },
    selector: ".form-panel",
    prepare: async (page) => {
      await page.getByLabel("Amount", { exact: true }).fill("16.80");
      await page.getByLabel("Category", { exact: true }).selectOption("food");
      await page.getByLabel(/note/i).fill("Team lunch");
    },
  });
  await capture({
    name: "12-category-filtering",
    viewport: { width: 1440, height: 900 },
    selector: ".transactions-panel",
    prepare: async (page) => {
      await page.getByLabel("Filter by category").selectOption("food");
      await expect(page.getByRole("list", { name: "Expenses" }).getByRole("listitem")).toHaveCount(1);
      await expect(page.getByText("Coffee", { exact: true })).toBeVisible();
      await page.locator(".transactions-panel").scrollIntoViewIfNeeded();
    },
  });
  await capture({
    name: "13-amount-validation",
    viewport: { width: 1440, height: 900 },
    selector: ".form-panel",
    prepare: async (page) => {
      await page.getByLabel("Amount", { exact: true }).fill("-25.00");
      await page.getByRole("button", { name: "Add expense", exact: true }).click();
      await expect(page.getByRole("alert")).toContainText("amount");
    },
  });
  await capture({
    name: "14-deletion-confirmation",
    viewport: { width: 1440, height: 900 },
    selector: "dialog",
    prepare: async (page) => {
      await page.getByRole("button", { name: "Delete Transit pass" }).click();
      const dialog = page.getByRole("dialog", { name: /delete expense/i });
      await expect(dialog).toBeVisible();
      await expect(dialog.getByRole("button", { name: "Cancel" })).toBeFocused();
    },
  });
  await capture({
    name: "15-mobile-dashboard",
    viewport: { width: 390, height: 844 },
  });
  await writeFile(
    "evidence/verification/ui-captures.json",
    JSON.stringify({ applicationURL: `${baseURL}/?demo=1`, captures }, null, 2) + "\n",
  );
  console.log("Captured six independent application states with no console errors.");
} finally {
  await browser.close();
}
