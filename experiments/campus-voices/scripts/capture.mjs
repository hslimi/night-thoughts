import { mkdir } from "node:fs/promises";
import path from "node:path";
import { chromium } from "@playwright/test";

const baseURL = process.argv[2] || "http://127.0.0.1:3000";
const outputDirectory = path.resolve("docs/screenshots");
await mkdir(outputDirectory, { recursive: true });

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({
  viewport: { width: 1440, height: 1000 },
  deviceScaleFactor: 1,
  reducedMotion: "reduce",
});
const page = await context.newPage();
await page.clock.install();

async function capture(name) {
  await page.screenshot({
    path: path.join(outputDirectory, name),
    animations: "disabled",
    fullPage: false,
  });
  console.log(`Captured ${name}`);
}

try {
  await page.goto(baseURL, { waitUntil: "networkidle" });
  if (baseURL.includes("campusvoices.nightthoughts.dev")) {
    await capture("05-public-application.png");
  } else {
    await capture("01-local-prototype.png");
    await page.getByLabel(/I understand this is a synthetic prototype/).check();
    await page
      .getByRole("button", { name: "Pre-session confidence 3 out of 5" })
      .click();
    await page.getByRole("button", { name: /Begin private practice/ }).click();
    await page.getByRole("button", { name: /Next partner prompt/ }).click();
    await capture("02-seminar-session.png");

    for (const name of [
      "Make an opening contribution",
      "Explain your reasoning",
      "Ask a clarifying question",
    ]) {
      await page.getByRole("button", { name: new RegExp(name) }).click();
    }
    await page.clock.fastForward(180_000);
    await page.getByRole("button", { name: /End session/ }).click();
    await page
      .getByRole("heading", { name: "You made room for your voice." })
      .waitFor();
    await page.locator("blockquote").waitFor();
    await page
      .getByRole("button", { name: "Post-session confidence 4 out of 5" })
      .click();
    await capture("03-private-feedback.png");

    await page.getByRole("button", { name: "Review privacy controls" }).click();
    await page.getByRole("dialog").waitFor();
    await capture("06-local-data-controls.png");
  }
} finally {
  await browser.close();
}
