const { test, expect } = require('@playwright/test');
const path = require('path');

const APP_URL = 'file://' + path.join(__dirname, '..', 'index.html');

test.describe('Scatterplot & Fit tab', () => {
  test('loads with the well-behaved preset and a computed fit', async ({ page }) => {
    await page.goto(APP_URL);
    await expect(page.locator('[data-testid=stat-n]')).toHaveText('16');
    const eq = await page.textContent('[data-testid=equation-display]');
    expect(eq).toMatch(/^ŷ = -?\d+\.\d+ [+-] \d+\.\d+·x$/);
  });

  test('switching presets updates point count and stats', async ({ page }) => {
    await page.goto(APP_URL);
    await page.click('[data-testid=preset-outlier]');
    await expect(page.locator('[data-testid=stat-n]')).toHaveText('15');
    await page.click('[data-testid=preset-non-linear]');
    await expect(page.locator('[data-testid=stat-n]')).toHaveText('17');
  });

  test('custom preset starts empty and clicking adds a point', async ({ page }) => {
    await page.goto(APP_URL);
    await page.click('[data-testid=preset-custom]');
    await expect(page.locator('[data-testid=stat-n]')).toHaveText('0');
    const canvas = page.locator('[data-testid=scatter-canvas]');
    const box = await canvas.boundingBox();
    await page.mouse.click(box.x + 200, box.y + 200);
    await expect(page.locator('[data-testid=stat-n]')).toHaveText('1');
  });

  test('clicking empty canvas does NOT add a point outside custom mode', async ({ page }) => {
    await page.goto(APP_URL); // well-behaved, n=16
    const canvas = page.locator('[data-testid=scatter-canvas]');
    const box = await canvas.boundingBox();
    await page.mouse.click(box.x + 10, box.y + 10); // corner, unlikely to hit an existing point
    await expect(page.locator('[data-testid=stat-n]')).toHaveText('16');
  });

  test('dragging an existing point moves it and live-updates the fit', async ({ page }) => {
    await page.goto(APP_URL);
    await page.click('[data-testid=preset-custom]');
    const canvas = page.locator('[data-testid=scatter-canvas]');
    const box = await canvas.boundingBox();
    await page.mouse.click(box.x + 150, box.y + 300);
    await page.mouse.click(box.x + 300, box.y + 200);
    await page.mouse.click(box.x + 450, box.y + 100);

    const before = await page.evaluate(() => window.__testHooks.getPoints());
    const pixel = await page.evaluate(() => {
      const pts = window.__testHooks.getPoints();
      const canvasEl = document.getElementById('scatter-canvas');
      const bounds = window.__testHooks.getBounds();
      const t = window.__testHooks.makeTransforms(bounds, canvasEl);
      return t.toPx(pts[0].x, pts[0].y);
    });
    const freshBox = await canvas.boundingBox();
    const scaleX = freshBox.width / 640, scaleY = freshBox.height / 440;
    const sx = freshBox.x + pixel.x * scaleX, sy = freshBox.y + pixel.y * scaleY;

    await page.mouse.move(sx, sy);
    await page.mouse.down();
    await page.mouse.move(sx + 40, sy - 40, { steps: 5 });
    await page.mouse.up();

    const after = await page.evaluate(() => window.__testHooks.getPoints());
    expect(after.length).toBe(before.length);
    expect(after[0]).not.toEqual(before[0]);
  });

  test('double-clicking a point removes it', async ({ page }) => {
    await page.goto(APP_URL);
    await page.click('[data-testid=preset-outlier]');
    await expect(page.locator('[data-testid=stat-n]')).toHaveText('15');

    const pixel = await page.evaluate(() => {
      const pts = window.__testHooks.getPoints();
      const canvasEl = document.getElementById('scatter-canvas');
      const bounds = window.__testHooks.getBounds();
      const t = window.__testHooks.makeTransforms(bounds, canvasEl);
      return t.toPx(pts[0].x, pts[0].y);
    });
    const canvas = page.locator('[data-testid=scatter-canvas]');
    const box = await canvas.boundingBox();
    const scaleX = box.width / 640, scaleY = box.height / 440;
    const sx = box.x + pixel.x * scaleX, sy = box.y + pixel.y * scaleY;
    await page.mouse.dblclick(sx, sy);
    await expect(page.locator('[data-testid=stat-n]')).toHaveText('14');
  });

  test('with fewer than 3 points, the equation shows a helpful message instead of NaN', async ({ page }) => {
    await page.goto(APP_URL);
    await page.click('[data-testid=preset-custom]');
    const canvas = page.locator('[data-testid=scatter-canvas]');
    const box = await canvas.boundingBox();
    await page.mouse.click(box.x + 200, box.y + 200);
    const eq = await page.textContent('[data-testid=equation-display]');
    expect(eq).toContain('need at least');
    expect(eq).not.toContain('NaN');
  });
});

test.describe('Tab navigation', () => {
  test('all four tabs are reachable and show their own panel', async ({ page }) => {
    await page.goto(APP_URL);
    for (const tab of ['fit', 'diagnostics', 'multicollinearity', 'quiz']) {
      await page.click(`[data-testid=tab-${tab}]`);
      await expect(page.locator(`#panel-${tab}`)).toBeVisible();
    }
  });
});
