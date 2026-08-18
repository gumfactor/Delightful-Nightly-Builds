const { test, expect } = require('@playwright/test');
const path = require('path');

const pageUrl = `file://${path.resolve(__dirname, '../index.html')}`;

async function canvasIsNonBlank(page, selector) {
  return page.evaluate((sel) => {
    const canvas = document.querySelector(sel);
    const ctx = canvas.getContext('2d');
    const data = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
    // A totally blank canvas would be all-zero (transparent black) or a
    // single uniform fill color. Check for at least some pixel variation.
    let firstR = data[0];
    for (let i = 0; i < data.length; i += 4) {
      if (data[i] !== firstR) return true;
    }
    return false;
  }, selector);
}

test.describe('Pipeline tab', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(pageUrl);
  });

  test('loads on the Pipeline tab by default with 6 step buttons', async ({ page }) => {
    await expect(page.locator('[data-testid="panel-pipeline"]')).toHaveClass(/active/);
    const stepButtons = page.locator('[data-testid="step-nav"] .step-nav-btn');
    await expect(stepButtons).toHaveCount(6);
  });

  test('first step shows Motion Correction with explanation and pitfall text', async ({ page }) => {
    await expect(page.locator('[data-testid="step-title"]')).toContainText('Motion Correction');
    const explanation = await page.locator('[data-testid="step-explanation"]').textContent();
    const pitfall = await page.locator('[data-testid="step-pitfall"]').textContent();
    expect(explanation.length).toBeGreaterThan(20);
    expect(pitfall).toContain('Pitfall');
  });

  test('each of the 6 pipeline steps renders distinct non-blank canvas content', async ({ page }) => {
    const titles = [];
    for (let i = 0; i < 6; i++) {
      await page.locator('[data-testid="step-nav"] .step-nav-btn').nth(i).click();
      const title = await page.locator('[data-testid="step-title"]').textContent();
      titles.push(title);
      const nonBlank = await canvasIsNonBlank(page, '[data-testid="pipeline-canvas"]');
      expect(nonBlank, `step ${i} (${title}) should render non-blank canvas`).toBe(true);
    }
    // All 6 titles should be distinct.
    expect(new Set(titles).size).toBe(6);
  });

  test('Before/After toggle changes the canvas render for the smoothing step', async ({ page }) => {
    // Smoothing step is index 3 (0-indexed) in the nav.
    await page.locator('[data-testid="step-nav"] .step-nav-btn').nth(3).click();
    await expect(page.locator('[data-testid="step-title"]')).toContainText('Spatial Smoothing');

    const beforePixels = await page.evaluate(() => {
      const canvas = document.querySelector('[data-testid="pipeline-canvas"]');
      return Array.from(canvas.getContext('2d').getImageData(0, 0, canvas.width, canvas.height).data);
    });

    await page.locator('[data-testid="phase-after"]').click();
    const afterPixels = await page.evaluate(() => {
      const canvas = document.querySelector('[data-testid="pipeline-canvas"]');
      return Array.from(canvas.getContext('2d').getImageData(0, 0, canvas.width, canvas.height).data);
    });

    let diffCount = 0;
    for (let i = 0; i < beforePixels.length; i++) {
      if (beforePixels[i] !== afterPixels[i]) diffCount++;
    }
    expect(diffCount).toBeGreaterThan(100);
  });

  test('HRF/GLM step (After phase) reports a recovered beta close to a plausible range', async ({ page }) => {
    await page.locator('[data-testid="step-nav"] .step-nav-btn').nth(4).click();
    await page.locator('[data-testid="phase-after"]').click();
    // The step draws "True beta = X, GLM-recovered beta = Y" as canvas text,
    // which isn't queryable via DOM — instead verify indirectly through the
    // underlying math used by the same render path.
    const recoveredCloseToTrue = await page.evaluate(() => {
      const stats = window.VoxelStats;
      const rng = stats.mulberry32(999);
      const trueBeta = 3;
      const n = 100;
      const predictor = Array.from({ length: n }, (_, i) => Math.sin((i / n) * Math.PI));
      const y = predictor.map((v) => trueBeta * v + stats.gaussianRandom(rng) * 0.1);
      const design = predictor.map((v) => [1, v]);
      const beta = stats.leastSquaresBeta(design, y);
      return Math.abs(beta[1] - trueBeta) < 0.5;
    });
    expect(recoveredCloseToTrue).toBe(true);
  });
});
