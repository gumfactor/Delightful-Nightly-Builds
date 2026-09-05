const { test, expect } = require('@playwright/test');
const path = require('path');

const INDEX_URL = 'file://' + path.join(__dirname, '..', 'index.html');

// Fixture: same 10-row X/M/Y dataset independently hand-computed via a
// from-scratch pure-Python Gauss-Jordan reference implementation during the
// design phase of this build (see BUILD_LOG.md). Ground truth, not derived
// from this build's own JS engine.
const FIXTURE = {
  X: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
  M: [4.0, 4.7, 6.7, 7.4, 9.9, 10.9, 12.8, 13.6, 16.1, 16.8],
  Y: [9.7, 11.3, 16.2, 17.6, 23.4, 25.5, 30.3, 32.2, 37.6, 39.8],
};

test.beforeEach(async ({ page }) => {
  await page.goto(INDEX_URL);
});

test.describe('mediation-engine.js', () => {
  test('path coefficients and indirect effect match hand-computed reference values', async ({ page }) => {
    const result = await page.evaluate((fixture) => {
      const rng = createRng(42);
      const stats = analyzeMediation(fixture, rng, 500);
      return stats;
    }, FIXTURE);

    expect(result.a).toBeCloseTo(1.495151515151516, 5);
    expect(result.b).toBeCloseTo(2.2116019493789736, 5);
    expect(result.cPrime).toBeCloseTo(0.17938060053438676, 5);
    expect(result.c).toBeCloseTo(3.486060606060608, 5);
    expect(result.indirect).toBeCloseTo(3.306680005526019, 5);
    expect(result.sobelSE).toBeCloseTo(0.26754971247059134, 5);
    expect(result.sobelZ).toBeCloseTo(12.359123749346148, 4);
  });

  test('the algebraic identity c = c\' + a*b holds for every generated sample', async ({ page }) => {
    const identityChecks = await page.evaluate(() => {
      const out = [];
      for (let seed = 1; seed <= 5; seed++) {
        const sample = generateMediationSample({ trueA: 0.9, trueB: 1.3, trueCPrime: 0.4, noiseSD: 1.2, n: 30, seed });
        const stats = analyzeMediation(sample, sample.rng, 200);
        out.push(stats.identityCheck);
      }
      return out;
    });
    identityChecks.forEach((diff) => expect(Math.abs(diff)).toBeLessThan(1e-6));
  });

  test('a larger sample size produces a narrower bootstrap CI, holding the true model fixed', async ({ page }) => {
    const widths = await page.evaluate(() => {
      function widthFor(n) {
        const sample = generateMediationSample({ trueA: 0.9, trueB: 1.4, trueCPrime: 0.3, noiseSD: 1.5, n, seed: 7 });
        const stats = analyzeMediation(sample, sample.rng, 1000);
        return stats.bootstrapCI[1] - stats.bootstrapCI[0];
      }
      return { small: widthFor(20), large: widthFor(400) };
    });
    expect(widths.large).toBeLessThan(widths.small);
  });

  test('same seed reproduces bit-for-bit identical sample and results (determinism)', async ({ page }) => {
    const results = await page.evaluate(() => {
      function run() {
        const sample = generateMediationSample({ trueA: 0.7, trueB: 1.1, trueCPrime: 0.2, noiseSD: 1.0, n: 40, seed: 12345 });
        const stats = analyzeMediation(sample, sample.rng, 1000);
        return { X: sample.X, M: sample.M, Y: sample.Y, indirect: stats.indirect, ci: stats.bootstrapCI };
      }
      return [run(), run()];
    });
    expect(results[0]).toEqual(results[1]);
  });

  test('a strong true mediation effect (large a, large b) yields a significant bootstrap CI', async ({ page }) => {
    const result = await page.evaluate(() => {
      const sample = generateMediationSample({ trueA: 1.5, trueB: 1.8, trueCPrime: 0.1, noiseSD: 0.5, n: 60, seed: 99 });
      return analyzeMediation(sample, sample.rng, 1000);
    });
    expect(result.ciExcludesZero).toBe(true);
    expect(result.bootstrapCI[0]).toBeGreaterThan(0);
  });

  test('a near-zero true mediation effect (a approx 0) yields a bootstrap CI including zero', async ({ page }) => {
    const result = await page.evaluate(() => {
      const sample = generateMediationSample({ trueA: 0.0, trueB: 1.5, trueCPrime: 0.5, noiseSD: 2.0, n: 60, seed: 3 });
      return analyzeMediation(sample, sample.rng, 1000);
    });
    expect(result.ciExcludesZero).toBe(false);
  });
});
