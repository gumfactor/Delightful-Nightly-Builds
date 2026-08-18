const { test, expect } = require('@playwright/test');
const path = require('path');

const pageUrl = `file://${path.resolve(__dirname, '../index.html')}`;

test.describe('stats.js — core math correctness', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(pageUrl);
  });

  test('Bonferroni threshold equals alpha/n exactly', async ({ page }) => {
    const results = await page.evaluate(() => {
      const s = window.VoxelStats;
      return [
        [s.bonferroniThreshold(0.05, 1000), 0.05 / 1000],
        [s.bonferroniThreshold(0.01, 20000), 0.01 / 20000],
        [s.bonferroniThreshold(0.1, 4), 0.1 / 4],
      ];
    });
    for (const [actual, expected] of results) {
      expect(actual).toBeCloseTo(expected, 12);
    }
  });

  test('Benjamini-Hochberg FDR reproduces a hand-worked textbook example', async ({ page }) => {
    // Classic worked example: 5 p-values, alpha=0.05.
    // BH critical values (k/n)*alpha = 0.01, 0.02, 0.03, 0.04, 0.05.
    // Sorted p: 0.001, 0.008, 0.039, 0.041, 0.09
    // Compare to critical: 0.001<=0.01 ok, 0.008<=0.02 ok, 0.039<=0.03 fail,
    // 0.041<=0.04 fail, 0.09<=0.05 fail -> largest passing k is 2 -> reject 2 smallest.
    const significant = await page.evaluate(() => {
      const pValues = [0.041, 0.001, 0.09, 0.008, 0.039];
      return window.VoxelStats.benjaminiHochberg(pValues, 0.05);
    });
    // Original order: [0.041, 0.001, 0.09, 0.008, 0.039]
    // Only the two smallest overall (0.001 and 0.008) should be significant.
    expect(significant).toEqual([false, true, false, true, false]);
  });

  test('Benjamini-Hochberg rejects nothing when no p-value passes its critical value', async ({ page }) => {
    const significant = await page.evaluate(() => {
      return window.VoxelStats.benjaminiHochberg([0.5, 0.6, 0.7], 0.05);
    });
    expect(significant).toEqual([false, false, false]);
  });

  test('Gaussian RNG (Box-Muller) sample mean/std approach 0/1 over a large N', async ({ page }) => {
    const { mean, std } = await page.evaluate(() => {
      const rng = window.VoxelStats.mulberry32(42);
      const n = 20000;
      const samples = [];
      for (let i = 0; i < n; i++) samples.push(window.VoxelStats.gaussianRandom(rng));
      const mean = samples.reduce((a, b) => a + b, 0) / n;
      const variance = samples.reduce((a, b) => a + (b - mean) ** 2, 0) / n;
      return { mean, std: Math.sqrt(variance) };
    });
    expect(Math.abs(mean)).toBeLessThan(0.05);
    expect(std).toBeGreaterThan(0.95);
    expect(std).toBeLessThan(1.05);
  });

  test('Double-gamma HRF peaks between 4 and 7 seconds and is normalized to 1.0', async ({ page }) => {
    const { peakTime, peakValue } = await page.evaluate(() => {
      let peakTime = 0;
      let peakValue = -Infinity;
      for (let t = 0; t <= 20; t += 0.05) {
        const v = window.VoxelStats.doubleGammaHRF(t);
        if (v > peakValue) {
          peakValue = v;
          peakTime = t;
        }
      }
      return { peakTime, peakValue };
    });
    expect(peakTime).toBeGreaterThan(4);
    expect(peakTime).toBeLessThan(7);
    expect(peakValue).toBeCloseTo(1.0, 2);
  });

  test('Double-gamma HRF is zero at and before t=0', async ({ page }) => {
    const values = await page.evaluate(() => [
      window.VoxelStats.doubleGammaHRF(0),
      window.VoxelStats.doubleGammaHRF(-5),
    ]);
    expect(values).toEqual([0, 0]);
  });

  test('Least-squares GLM recovers a known true beta from a noiseless signal', async ({ page }) => {
    const beta = await page.evaluate(() => {
      const trueBeta0 = 1.5;
      const trueBeta1 = 3.0;
      const design = [];
      const y = [];
      for (let i = 0; i < 50; i++) {
        const x = i / 10;
        design.push([1, x]);
        y.push(trueBeta0 + trueBeta1 * x);
      }
      return window.VoxelStats.leastSquaresBeta(design, y);
    });
    expect(beta[0]).toBeCloseTo(1.5, 6);
    expect(beta[1]).toBeCloseTo(3.0, 6);
  });

  test('4-connected cluster labeling finds the correct cluster count and sizes', async ({ page }) => {
    const { sizes, clusterCount } = await page.evaluate(() => {
      // 5x5 grid: one 3-voxel L-shaped cluster (top-left) and two isolated
      // single voxels (bottom-right corner and middle-right), diagonal
      // neighbors don't count under 4-connectivity.
      const width = 5;
      const height = 5;
      const mask = new Array(width * height).fill(false);
      // L-shape at (0,0),(1,0),(0,1)
      mask[0] = true; // (0,0)
      mask[1] = true; // (1,0)
      mask[width] = true; // (0,1)
      // isolated voxel at (4,4)
      mask[width * height - 1] = true;
      // isolated voxel at (4,2), diagonal-only neighbor to the L-shape (not touching)
      mask[2 * width + 4] = true;
      const { sizes } = window.VoxelStats.labelClusters(mask, width, height);
      const nonZeroSizes = sizes.slice(1).sort((a, b) => a - b);
      return { sizes: nonZeroSizes, clusterCount: nonZeroSizes.length };
    });
    expect(clusterCount).toBe(3);
    expect(sizes).toEqual([1, 1, 3]);
  });

  test('Cluster-extent correction removes clusters smaller than the minimum size', async ({ page }) => {
    const survivorCount = await page.evaluate(() => {
      const width = 5;
      const height = 5;
      const mask = new Array(width * height).fill(false);
      mask[0] = true;
      mask[1] = true;
      mask[width] = true; // 3-voxel cluster
      mask[width * height - 1] = true; // isolated voxel
      const corrected = window.VoxelStats.clusterExtentThreshold(mask, width, height, 2);
      return corrected.filter(Boolean).length;
    });
    expect(survivorCount).toBe(3);
  });

  test('convolve() produces the correct result for a simple hand-worked case', async ({ page }) => {
    const result = await page.evaluate(() => {
      // signal = [1, 0, 0, 0], kernel = [1, 2, 3] -> causal convolution
      // out[i] = sum_k signal[i-k]*kernel[k]
      return window.VoxelStats.convolve([1, 0, 0, 0], [1, 2, 3]);
    });
    expect(result).toEqual([1, 2, 3, 0]);
  });
});
