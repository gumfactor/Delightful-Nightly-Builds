const { test, expect } = require('@playwright/test');
const { pageUrl, gotoFresh } = require('./helpers');

test.describe('deterministic daily puzzle selection', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(pageUrl());
  });

  test('anchor date 2026-07-06 maps to puzzle index 0', async ({ page }) => {
    const index = await page.evaluate(() => getPuzzleIndexForDate('2026-07-06'));
    expect(index).toBe(0);
  });

  test('consecutive UTC days map to consecutive indexes', async ({ page }) => {
    const a = await page.evaluate(() => getPuzzleIndexForDate('2026-07-06'));
    const b = await page.evaluate(() => getPuzzleIndexForDate('2026-07-07'));
    expect(b).toBe(a + 1);
  });

  test('the index wraps around (modulo) after a full bank cycle', async ({ page }) => {
    // 2026-08-05 is exactly 30 days after the 2026-07-06 anchor for a 30-puzzle bank.
    const anchorIndex = await page.evaluate(() => getPuzzleIndexForDate('2026-07-06'));
    const futureIndex = await page.evaluate(() => getPuzzleIndexForDate('2026-08-05'));
    expect(futureIndex).toBe(anchorIndex);
  });

  test('the same date string always yields the same puzzle (deterministic)', async ({ page }) => {
    const first = await page.evaluate(() => getPuzzleForDate('2026-07-15').id);
    const second = await page.evaluate(() => getPuzzleForDate('2026-07-15').id);
    expect(first).toBe(second);
  });

  test('a date before the anchor still resolves to a valid, non-negative index', async ({ page }) => {
    const index = await page.evaluate(() => getPuzzleIndexForDate('2025-01-01'));
    const length = await page.evaluate(() => PUZZLES.length);
    expect(index).toBeGreaterThanOrEqual(0);
    expect(index).toBeLessThan(length);
  });

  test("the displayed puzzle title matches getPuzzleForDate for today's date", async ({ page }) => {
    await gotoFresh(page);
    const expectedTitle = await page.evaluate(
      () => getPuzzleForDate(new Date().toISOString().slice(0, 10)).title
    );
    await expect(page.locator('#puzzle-title')).toHaveText(expectedTitle);
  });
});
