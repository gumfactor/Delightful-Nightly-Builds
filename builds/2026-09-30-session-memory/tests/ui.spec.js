const { test, expect } = require("playwright/test");

test("lists projects and opens a resume brief", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("stats")).toContainText("5 sessions");
  await page.getByTestId("project-item").filter({ hasText: "canada-list" }).click();
  await expect(page.getByTestId("brief")).toContainText("canada-list: resume brief");
  await expect(page.getByTestId("brief")).toContainText("Open items");
});

test("search highlights matches and opens the session at the hit", async ({ page }) => {
  await page.goto("/");
  await page.getByTestId("search-input").fill("postal");
  await expect(page.getByTestId("hit").first()).toBeVisible();
  await expect(page.getByTestId("hit").first().locator("mark").first()).toHaveText(/postal/i);
  await page.getByTestId("hit").first().click();
  await expect(page.getByTestId("transcript")).toContainText("postal");
  await expect(page.locator(".msg.hit")).toHaveCount(1);
});

test("source filter narrows results and empty search shows a message", async ({ page }) => {
  await page.goto("/");
  await page.getByTestId("source-filter").selectOption("chatgpt");
  await expect(page.getByTestId("session-item")).toHaveCount(1);
  await page.getByTestId("search-input").fill("zzzzqqqq");
  await expect(page.getByTestId("no-results")).toBeVisible();
});

test("session view shows offline summary and AI button reports missing key", async ({ page }) => {
  await page.goto("/");
  await page.getByTestId("session-item").first().click();
  await expect(page.getByTestId("summary-kind")).toHaveText("offline summary");
  await page.getByTestId("ai-summary").click();
  await expect(page.getByTestId("error")).toContainText("ANTHROPIC_API_KEY");
});

test("transcript text is rendered as text, never as HTML", async ({ page }) => {
  await page.goto("/");
  await page.getByTestId("search-input").fill("cortisol");
  await page.getByTestId("hit").first().click();
  await expect(page.locator("#detail script, #detail img")).toHaveCount(0);
});
