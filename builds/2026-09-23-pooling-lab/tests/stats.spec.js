const { test, expect } = require('@playwright/test');
const path = require('path');

// Unit-style tests against the pure stats engine. We load stats.js into a
// blank page via addScriptTag so the exact same code the app uses is what
// gets tested — no reimplementation, no drift.
test.beforeEach(async ({ page }) => {
  await page.goto('about:blank');
  await page.addScriptTag({ path: path.join(__dirname, '..', 'src', 'stats.js') });
});

test('computeTrueICC returns tau2/(tau2+sigma2) for typical values', async ({ page }) => {
  const icc = await page.evaluate(() => window.PoolingStats.computeTrueICC(4, 9));
  expect(icc).toBeCloseTo(4 / 13, 6);
});

test('computeTrueICC returns 0 when tau2 is 0', async ({ page }) => {
  const icc = await page.evaluate(() => window.PoolingStats.computeTrueICC(0, 9));
  expect(icc).toBe(0);
});

test('computeTrueICC returns 1 when sigma2 is 0', async ({ page }) => {
  const icc = await page.evaluate(() => window.PoolingStats.computeTrueICC(4, 0));
  expect(icc).toBe(1);
});

test('generateNestedData is deterministic for a fixed seed', async ({ page }) => {
  const result = await page.evaluate(() => {
    const params = { seed: 42, groupCount: 4, groupSizes: [5, 10, 5, 10], tau2: 4, sigma2: 9 };
    const a = window.PoolingStats.generateNestedData(params);
    const b = window.PoolingStats.generateNestedData(params);
    return JSON.stringify(a) === JSON.stringify(b);
  });
  expect(result).toBe(true);
});

test('generateNestedData produces different data for different seeds', async ({ page }) => {
  const result = await page.evaluate(() => {
    const base = { groupCount: 4, groupSizes: [5, 10, 5, 10], tau2: 4, sigma2: 9 };
    const a = window.PoolingStats.generateNestedData(Object.assign({ seed: 1 }, base));
    const b = window.PoolingStats.generateNestedData(Object.assign({ seed: 2 }, base));
    return JSON.stringify(a) !== JSON.stringify(b);
  });
  expect(result).toBe(true);
});

test('generateNestedData honors requested per-group sample sizes exactly', async ({ page }) => {
  const sizes = await page.evaluate(() => {
    const data = window.PoolingStats.generateNestedData({
      seed: 7,
      groupCount: 3,
      groupSizes: [2, 7, 13],
      tau2: 3,
      sigma2: 5,
    });
    return data.groups.map((g) => g.observations.length);
  });
  expect(sizes).toEqual([2, 7, 13]);
});

test('computeGrandMean is the size-weighted average across unequal group sizes', async ({ page }) => {
  const result = await page.evaluate(() => {
    // Construct a dataset by hand (no randomness) to check weighting exactly.
    const dataset = {
      groups: [
        { id: 0, n: 1, observations: [0] },
        { id: 1, n: 3, observations: [10, 10, 10] },
      ],
    };
    const grand = window.PoolingStats.computeGrandMean(dataset);
    // (0 + 10 + 10 + 10) / 4 = 7.5, NOT (0 + 10) / 2 = 5
    return grand;
  });
  expect(result).toBeCloseTo(7.5, 6);
});

test('partial-pooling collapses to the grand mean when tau2 is 0', async ({ page }) => {
  const result = await page.evaluate(() => {
    const data = window.PoolingStats.generateNestedData({
      seed: 5,
      groupCount: 4,
      groupSizes: [3, 6, 9, 12],
      tau2: 0,
      sigma2: 9,
    });
    const summary = window.PoolingStats.computePoolingSummary(data);
    return summary.perGroup.every((g) => Math.abs(g.partialPooling - summary.grandMean) < 1e-9);
  });
  expect(result).toBe(true);
});

test('partial-pooling collapses to the raw group mean when sigma2 is 0', async ({ page }) => {
  const result = await page.evaluate(() => {
    const data = window.PoolingStats.generateNestedData({
      seed: 5,
      groupCount: 4,
      groupSizes: [3, 6, 9, 12],
      tau2: 4,
      sigma2: 0,
    });
    const summary = window.PoolingStats.computePoolingSummary(data);
    return summary.perGroup.every((g) => Math.abs(g.partialPooling - g.noPooling) < 1e-9);
  });
  expect(result).toBe(true);
});

test('partial-pooling estimate always lies between no-pooling and complete-pooling', async ({ page }) => {
  const result = await page.evaluate(() => {
    const data = window.PoolingStats.generateNestedData({
      seed: 123,
      groupCount: 6,
      groupSizes: [3, 30, 8, 15, 1, 50],
      tau2: 4,
      sigma2: 9,
    });
    const summary = window.PoolingStats.computePoolingSummary(data);
    return summary.perGroup.every((g) => {
      const lo = Math.min(g.noPooling, g.completePooling);
      const hi = Math.max(g.noPooling, g.completePooling);
      return g.partialPooling >= lo - 1e-9 && g.partialPooling <= hi + 1e-9;
    });
  });
  expect(result).toBe(true);
});

test('a group with more observations shrinks less than a group with fewer, same tau/sigma', async ({ page }) => {
  const weights = await page.evaluate(() => ({
    small: window.PoolingStats.computeShrinkageWeight(4, 9, 3),
    large: window.PoolingStats.computeShrinkageWeight(4, 9, 100),
  }));
  expect(weights.large).toBeGreaterThan(weights.small);
});

test('shrinkage weight approaches 1 as sample size grows very large', async ({ page }) => {
  const weight = await page.evaluate(() => window.PoolingStats.computeShrinkageWeight(4, 9, 100000));
  expect(weight).toBeGreaterThan(0.999);
});

test('empirical ICC recovers the true ICC within tolerance on a large sample', async ({ page }) => {
  const result = await page.evaluate(() => {
    const data = window.PoolingStats.generateNestedData({
      seed: 99,
      groupCount: 60,
      groupSizes: Array(60).fill(200),
      tau2: 4,
      sigma2: 9,
    });
    const empirical = window.PoolingStats.computeEmpiricalICC(data);
    const truth = window.PoolingStats.computeTrueICC(4, 9);
    return { empirical, truth };
  });
  expect(Math.abs(result.empirical - result.truth)).toBeLessThan(0.05);
});

test('a single-group dataset reports empirical ICC as not computable rather than NaN', async ({ page }) => {
  const result = await page.evaluate(() => {
    const data = window.PoolingStats.generateNestedData({
      seed: 1,
      groupCount: 1,
      groupSizes: [10],
      tau2: 4,
      sigma2: 9,
    });
    return window.PoolingStats.computeEmpiricalICC(data);
  });
  expect(result).toBeNull();
});

test('generateNestedData throws a clear error when groupSizes length mismatches groupCount', async ({ page }) => {
  const threw = await page.evaluate(() => {
    try {
      window.PoolingStats.generateNestedData({ seed: 1, groupCount: 3, groupSizes: [1, 2], tau2: 1, sigma2: 1 });
      return false;
    } catch (e) {
      return true;
    }
  });
  expect(threw).toBe(true);
});
