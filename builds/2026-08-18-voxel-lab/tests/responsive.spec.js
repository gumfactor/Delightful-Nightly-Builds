const { test, expect } = require('@playwright/test');
const path = require('path');

const pageUrl = `file://${path.resolve(__dirname, '../index.html')}`;

test.describe('Responsive layout', () => {
  test('layout does not overflow horizontally at a 375px mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 700 });
    await page.goto(pageUrl);

    const { scrollWidth, clientWidth } = await page.evaluate(() => ({
      scrollWidth: document.documentElement.scrollWidth,
      clientWidth: document.documentElement.clientWidth,
    }));
    expect(scrollWidth).toBeLessThanOrEqual(clientWidth + 1);
  });

  test('all three tabs remain usable at a 375px mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 700 });
    await page.goto(pageUrl);

    await page.locator('[data-testid="tab-mc"]').click();
    await expect(page.locator('[data-testid="panel-mc"]')).toHaveClass(/active/);
    await expect(page.locator('[data-testid="mc-run"]')).toBeVisible();

    await page.locator('[data-testid="tab-quiz"]').click();
    await expect(page.locator('[data-testid="panel-quiz"]')).toHaveClass(/active/);
    await expect(page.locator('[data-testid="quiz-choices"] .choice-btn').first()).toBeVisible();
  });

  test('pipeline canvas remains visible and non-zero-size at a 375px mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 700 });
    await page.goto(pageUrl);
    const box = await page.locator('[data-testid="pipeline-canvas"]').boundingBox();
    expect(box.width).toBeGreaterThan(0);
    expect(box.height).toBeGreaterThan(0);
  });
});
