const { test, expect } = require('@playwright/test');
const path = require('path');

const APP_URL = 'file://' + path.join(__dirname, '..', 'index.html');

test.describe('Diagnostics tab', () => {
  test('heteroscedastic preset flags the Breusch-Pagan test as significant', async ({ page }) => {
    await page.goto(APP_URL);
    await page.click('[data-testid=preset-heteroscedastic]');
    await page.click('[data-testid=tab-diagnostics]');
    const banner = await page.textContent('[data-testid=verdict-banner]');
    expect(banner).toContain("isn't constant");
    const bp = await page.textContent('[data-testid=test-bp]');
    expect(bp).toContain('SIGNIFICANT');
  });

  test('non-linear preset flags the RESET test as significant', async ({ page }) => {
    await page.goto(APP_URL);
    await page.click('[data-testid=preset-non-linear]');
    await page.click('[data-testid=tab-diagnostics]');
    const reset = await page.textContent('[data-testid=test-reset]');
    expect(reset).toContain('SIGNIFICANT');
    const banner = await page.textContent('[data-testid=verdict-banner]');
    expect(banner).toContain("isn't linear");
  });

  test('outlier preset names the dominant influential point', async ({ page }) => {
    await page.goto(APP_URL);
    await page.click('[data-testid=preset-outlier]');
    await page.click('[data-testid=tab-diagnostics]');
    const banner = await page.textContent('[data-testid=verdict-banner]');
    expect(banner).toContain('high-leverage outlier');
  });

  test('well-behaved preset does not raise any warning banner', async ({ page }) => {
    await page.goto(APP_URL); // default is well-behaved
    await page.click('[data-testid=tab-diagnostics]');
    const banner = await page.locator('[data-testid=verdict-banner]');
    await expect(banner).toHaveText(/looks sound/);
  });

  test('too few points shows a guidance message instead of crashing', async ({ page }) => {
    await page.goto(APP_URL);
    await page.click('[data-testid=preset-custom]');
    const canvas = page.locator('[data-testid=scatter-canvas]');
    const box = await canvas.boundingBox();
    await page.mouse.click(box.x + 100, box.y + 100);
    await page.mouse.click(box.x + 200, box.y + 200);
    await page.click('[data-testid=tab-diagnostics]');
    const banner = await page.textContent('[data-testid=verdict-banner]');
    expect(banner).toContain('Add at least');
  });

  test('explain button with no API key falls back to the deterministic template with zero network calls', async ({ page }) => {
    const requests = [];
    page.on('request', (req) => {
      if (req.url().includes('anthropic.com')) requests.push(req.url());
    });
    await page.goto(APP_URL);
    await page.click('[data-testid=preset-heteroscedastic]');
    await page.click('[data-testid=tab-diagnostics]');
    await page.click('[data-testid=explain-btn]');
    await expect(page.locator('[data-testid=ai-source]')).toContainText('Deterministic template');
    const explanation = await page.textContent('[data-testid=ai-explanation]');
    expect(explanation.length).toBeGreaterThan(20);
    expect(requests.length).toBe(0);
  });
});
