import { expect, test } from "@playwright/test";
import { PARTICIPATION_GOALS, STORAGE_KEY } from "../app/src/content";

async function beginPractice(
  page: import("@playwright/test").Page,
): Promise<void> {
  await page.goto("/");
  await page.getByLabel(/I understand this is a synthetic prototype/).check();
  await page
    .getByRole("button", { name: "Pre-session confidence 3 out of 5" })
    .click();
  await page.getByRole("button", { name: /Begin private practice/ }).click();
}

test("complete private practice scenario and delete local data", async ({
  page,
}) => {
  const externalRequests: string[] = [];
  page.on("request", (request) => {
    const url = new URL(request.url());
    if (!["127.0.0.1", "localhost"].includes(url.hostname))
      externalRequests.push(url.href);
  });

  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "My First Seminar Contribution" }),
  ).toBeVisible();
  await expect(
    page.getByText("Dessa is a disabled future provider"),
  ).toBeVisible();
  await expect(page.getByText("No recording", { exact: true })).toBeVisible();
  await beginPractice(page);

  await expect(
    page.getByText("Sam · simulated seminar partner").first(),
  ).toBeVisible();
  await expect(page.locator("[data-timer]")).toHaveText(/05:00|04:59/);
  await page.getByRole("button", { name: /Next partner prompt/ }).click();
  await expect(
    page.getByText(/What makes that idea important to you/),
  ).toBeVisible();

  for (const goal of PARTICIPATION_GOALS) {
    await page.getByRole("button", { name: new RegExp(goal.title) }).click();
  }
  await expect(page.locator("[data-goal-count]")).toHaveText("5");
  await page.getByRole("button", { name: /End session/ }).click();

  await expect(
    page.getByRole("heading", { name: "You made room for your voice." }),
  ).toBeVisible();
  await expect(page.locator("blockquote")).not.toBeEmpty();
  await expect(page.locator(".feedback-source")).toHaveText(
    /SCRIPTED PROTOTYPE|LOCAL oMLX/,
  );
  await page
    .getByRole("button", { name: "Post-session confidence 4 out of 5" })
    .click();
  await expect(
    page.getByRole("button", { name: "Post-session confidence 4 out of 5" }),
  ).toHaveAttribute("aria-pressed", "true");

  const stored = await page.evaluate(
    (key) => localStorage.getItem(key),
    STORAGE_KEY,
  );
  expect(stored).not.toContain("transcript");
  expect(stored).not.toContain("recording");
  expect(stored).not.toContain("server-only-test-secret");
  await page.getByRole("button", { name: "Delete local data" }).click();
  await expect(
    page.getByText("Local practice data deleted from this browser."),
  ).toBeVisible();
  expect(
    await page.evaluate((key) => localStorage.getItem(key), STORAGE_KEY),
  ).toBeNull();
  expect(externalRequests).toEqual([]);
});

test("five-minute timer ends the session and privacy controls open", async ({
  page,
}) => {
  await page.clock.install();
  await beginPractice(page);
  await page.clock.fastForward(300_000);
  await expect(
    page.getByRole("heading", { name: "You made room for your voice." }),
  ).toBeVisible();
  await expect(page.locator(".feedback-metrics")).toContainText("05:00");
  await page.getByRole("button", { name: "Review privacy controls" }).click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await expect(
    page.getByText(/creates no recordings or transcripts/),
  ).toBeVisible();
});

test("browser responses never contain the server credential", async ({
  page,
}) => {
  await page.goto("/");
  const body = await page.locator("body").innerText();
  expect(body).not.toContain("server-only-test-secret");
  const health = await page.evaluate(async () =>
    fetch("/api/health").then((response) => response.text()),
  );
  expect(health).not.toContain("server-only-test-secret");
});
