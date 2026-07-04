const { test, expect } = require('@playwright/test');
const path = require('path');

// Loads stats.js as a real ES module in the page and exposes its exports on
// window.PowerLabStats (stats.js does this itself when window is defined),
// so we exercise the exact same code the app uses -- no reimplementation.
async function gotoStatsPage(page) {
  const filePath = path.join(__dirname, '..', 'index.html');
  await page.goto(`file://${filePath}`);
  await page.waitForFunction(() => window.PowerLabStats !== undefined);
}

test.describe('stats.js core math', () => {
  test('normalCDF at known reference points', async ({ page }) => {
    await gotoStatsPage(page);
    const results = await page.evaluate(() => {
      const { normalCDF } = window.PowerLabStats;
      return {
        zero: normalCDF(0),
        z196: normalCDF(1.959964),
        negZ196: normalCDF(-1.959964),
      };
    });
    expect(results.zero).toBeCloseTo(0.5, 3);
    expect(results.z196).toBeCloseTo(0.975, 3);
    expect(results.negZ196).toBeCloseTo(0.025, 3);
  });

  test('invNormalCDF round-trips normalCDF', async ({ page }) => {
    await gotoStatsPage(page);
    const results = await page.evaluate(() => {
      const { normalCDF, invNormalCDF } = window.PowerLabStats;
      return [0.1, 0.5, 0.8, 0.975, 0.999].map((p) => {
        const z = invNormalCDF(p);
        return normalCDF(z);
      });
    });
    for (let i = 0; i < results.length; i++) {
      const expected = [0.1, 0.5, 0.8, 0.975, 0.999][i];
      expect(results[i]).toBeCloseTo(expected, 3);
    }
  });

  test('invNormalCDF rejects out-of-range probabilities', async ({ page }) => {
    await gotoStatsPage(page);
    const threw = await page.evaluate(() => {
      const { invNormalCDF } = window.PowerLabStats;
      try {
        invNormalCDF(0);
        return false;
      } catch {
        return true;
      }
    });
    expect(threw).toBe(true);
  });

  test('computePower matches the classic textbook benchmark (d=0.5, n=64/group, alpha=.05 two-sided)', async ({ page }) => {
    await gotoStatsPage(page);
    const power = await page.evaluate(() => {
      const { computePower } = window.PowerLabStats;
      return computePower({ d: 0.5, n: 64, alpha: 0.05, testType: 'two-sample', tails: 'two' });
    });
    expect(power).toBeGreaterThan(0.75);
    expect(power).toBeLessThan(0.85);
  });

  test('power increases monotonically with sample size', async ({ page }) => {
    await gotoStatsPage(page);
    const powers = await page.evaluate(() => {
      const { computePower } = window.PowerLabStats;
      return [20, 40, 64, 100, 200].map((n) =>
        computePower({ d: 0.5, n, alpha: 0.05, testType: 'two-sample', tails: 'two' })
      );
    });
    for (let i = 1; i < powers.length; i++) {
      expect(powers[i]).toBeGreaterThan(powers[i - 1]);
    }
  });

  test('power increases monotonically with effect size', async ({ page }) => {
    await gotoStatsPage(page);
    const powers = await page.evaluate(() => {
      const { computePower } = window.PowerLabStats;
      return [0.1, 0.2, 0.5, 0.8, 1.2].map((d) =>
        computePower({ d, n: 40, alpha: 0.05, testType: 'two-sample', tails: 'two' })
      );
    });
    for (let i = 1; i < powers.length; i++) {
      expect(powers[i]).toBeGreaterThan(powers[i - 1]);
    }
  });

  test('one-sample design reaches higher power than two-sample for the same n and d', async ({ page }) => {
    await gotoStatsPage(page);
    const { oneSample, twoSample } = await page.evaluate(() => {
      const { computePower } = window.PowerLabStats;
      return {
        oneSample: computePower({ d: 0.5, n: 40, alpha: 0.05, testType: 'one-sample', tails: 'two' }),
        twoSample: computePower({ d: 0.5, n: 40, alpha: 0.05, testType: 'two-sample', tails: 'two' }),
      };
    });
    expect(oneSample).toBeGreaterThan(twoSample);
  });

  test('d=0 yields power approximately equal to alpha (two-sided)', async ({ page }) => {
    await gotoStatsPage(page);
    const power = await page.evaluate(() => {
      const { computePower } = window.PowerLabStats;
      return computePower({ d: 0, n: 50, alpha: 0.05, testType: 'two-sample', tails: 'two' });
    });
    expect(power).toBeCloseTo(0.05, 2);
  });

  test('computeRequiredN round-trips computePower: the returned N achieves at least the target power', async ({ page }) => {
    await gotoStatsPage(page);
    const results = await page.evaluate(() => {
      const { computeRequiredN, computePower } = window.PowerLabStats;
      return [0.2, 0.5, 0.8].map((d) => {
        const n = computeRequiredN({ d, power: 0.8, alpha: 0.05, testType: 'two-sample', tails: 'two' });
        const achievedPower = computePower({ d, n, alpha: 0.05, testType: 'two-sample', tails: 'two' });
        return achievedPower;
      });
    });
    results.forEach((p) => expect(p).toBeGreaterThanOrEqual(0.8));
  });

  test('computeRequiredN rejects d=0 and out-of-range power', async ({ page }) => {
    await gotoStatsPage(page);
    const results = await page.evaluate(() => {
      const { computeRequiredN } = window.PowerLabStats;
      const attempts = [];
      try { computeRequiredN({ d: 0, power: 0.8, alpha: 0.05, testType: 'two-sample', tails: 'two' }); attempts.push('no-throw-d0'); }
      catch { attempts.push('threw-d0'); }
      try { computeRequiredN({ d: 0.5, power: 1.2, alpha: 0.05, testType: 'two-sample', tails: 'two' }); attempts.push('no-throw-power'); }
      catch { attempts.push('threw-power'); }
      return attempts;
    });
    expect(results).toEqual(['threw-d0', 'threw-power']);
  });

  test('dToR and rToD round-trip within tolerance', async ({ page }) => {
    await gotoStatsPage(page);
    const results = await page.evaluate(() => {
      const { dToR, rToD } = window.PowerLabStats;
      return [0.2, 0.5, 0.8, 1.2].map((d) => rToD(dToR(d)));
    });
    [0.2, 0.5, 0.8, 1.2].forEach((d, i) => expect(results[i]).toBeCloseTo(d, 3));
  });

  test('dToR matches a hand-computed value at d=0.5', async ({ page }) => {
    await gotoStatsPage(page);
    const r = await page.evaluate(() => window.PowerLabStats.dToR(0.5));
    // r = 0.5 / sqrt(0.25 + 4) = 0.5 / sqrt(4.25) = 0.24254...
    expect(r).toBeCloseTo(0.24254, 4);
  });

  test('tToD matches hand-computed values for two-sample and one-sample designs', async ({ page }) => {
    await gotoStatsPage(page);
    const results = await page.evaluate(() => {
      const { tToD } = window.PowerLabStats;
      return {
        twoSample: tToD({ t: 2.0, n: 30, testType: 'two-sample' }), // 2 * sqrt(2/30)
        oneSample: tToD({ t: 2.0, n: 30, testType: 'one-sample' }), // 2 * sqrt(1/30)
      };
    });
    expect(results.twoSample).toBeCloseTo(2 * Math.sqrt(2 / 30), 6);
    expect(results.oneSample).toBeCloseTo(2 * Math.sqrt(1 / 30), 6);
  });

  test('powerLabel and effectSizeLabel return the expected qualitative bands', async ({ page }) => {
    await gotoStatsPage(page);
    const results = await page.evaluate(() => {
      const { powerLabel, effectSizeLabel } = window.PowerLabStats;
      return {
        low: powerLabel(0.3),
        mid: powerLabel(0.6),
        high: powerLabel(0.95),
        smallEffect: effectSizeLabel(0.3),
        largeEffect: effectSizeLabel(0.9),
      };
    });
    expect(results.low).toBe('severely underpowered');
    expect(results.mid).toBe('underpowered');
    expect(results.high).toBe('well-powered');
    expect(results.smallEffect).toBe('small');
    expect(results.largeEffect).toBe('large');
  });
});
