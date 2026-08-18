const { test, expect } = require('@playwright/test');
const path = require('path');

const pageUrl = `file://${path.resolve(__dirname, '../index.html')}`;

test.describe('Multiple Comparisons Lab', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(pageUrl);
    await page.locator('[data-testid="tab-mc"]').click();
  });

  test('MC tab loads with default results already rendered', async ({ page }) => {
    await expect(page.locator('[data-testid="panel-mc"]')).toHaveClass(/active/);
    const summaryText = await page.locator('[data-testid="mc-mean"]').textContent();
    expect(summaryText).toContain('Bonferroni');
    expect(summaryText).toContain('Benjamini-Hochberg');
  });

  test('running the simulation through the real UI shows uncorrected false positives substantially exceeding Bonferroni/FDR at a large voxel count', async ({ page }) => {
    await page.locator('[data-testid="mc-voxel-count"]').fill('8000');
    await page.locator('[data-testid="mc-alpha"]').fill('0.05');
    await page.locator('[data-testid="mc-trials"]').fill('60');
    await page.locator('[data-testid="mc-run"]').click();

    const result = await page.evaluate(() => window.__lastMCResult);
    expect(result.voxelCount).toBe(8000);
    expect(result.trials).toBe(60);

    const uncorrectedMean = result.methods.none.mean;
    const bonferroniMean = result.methods.bonferroni.mean;
    const fdrMean = result.methods.fdr.mean;

    // At alpha=0.05 and 8000 independent noise voxels, uncorrected false
    // positives should average close to 400 (0.05 * 8000), while Bonferroni
    // essentially never survives (threshold = 0.05/8000). This is the
    // tool's core teaching claim, verified live through the real UI.
    expect(uncorrectedMean).toBeGreaterThan(200);
    expect(bonferroniMean).toBeLessThan(uncorrectedMean / 10);
    expect(fdrMean).toBeLessThan(uncorrectedMean / 5);
  });

  test('bar chart and per-method slice canvases render after running', async ({ page }) => {
    await page.locator('[data-testid="mc-run"]').click();
    const sliceCanvases = page.locator('[data-testid="mc-slices"] canvas');
    await expect(sliceCanvases).toHaveCount(4);

    const barChartNonBlank = await page.evaluate(() => {
      const canvas = document.querySelector('[data-testid="mc-bar-chart"]');
      const data = canvas.getContext('2d').getImageData(0, 0, canvas.width, canvas.height).data;
      const first = data[0];
      for (let i = 0; i < data.length; i += 4) {
        if (data[i] !== first) return true;
      }
      return false;
    });
    expect(barChartNonBlank).toBe(true);
  });

  test('cluster-extent correction removes more false positives than uncorrected at a fixed noise draw (direct math check)', async ({ page }) => {
    const result = await page.evaluate(() => {
      const rng = window.VoxelStats.mulberry32(123);
      return window.VoxelMonteCarlo.runComparison({ voxelCount: 4000, alpha: 0.05, trials: 30, rng });
    });
    expect(result.methods.cluster.mean).toBeLessThan(result.methods.none.mean);
  });

  test('voxel count input is respected and clamped within its stated 100-20000 range in the UI', async ({ page }) => {
    await page.locator('[data-testid="mc-voxel-count"]').fill('500000');
    await page.locator('[data-testid="mc-run"]').click();
    const result = await page.evaluate(() => window.__lastMCResult);
    expect(result.voxelCount).toBeLessThanOrEqual(20000);
  });
});
