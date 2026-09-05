const { test, expect } = require('@playwright/test');
const path = require('path');

const INDEX_URL = 'file://' + path.join(__dirname, '..', 'index.html');

// Fixture: same 15-row X/Z/Y dataset independently hand-computed via a
// from-scratch pure-Python Gauss-Jordan reference implementation during the
// design phase of this build (see BUILD_LOG.md), including the Johnson-Neyman
// roots re-verified by plugging each root back into the slope/SE formula and
// confirming |t| equals t_crit exactly. Ground truth, not derived from this
// build's own JS engine.
const FIXTURE = {
  X: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 3, 5, 7, 2, 9],
  Z: [5, 3, 8, 2, 7, 6, 1, 9, 4, 10, 6, 2, 8, 5, 3],
  Y: [5.510666666666666, 8.530666666666667, 5.4706666666666655, 8.050666666666666,
      10.690666666666665, 11.470666666666665, 4.710666666666667, 21.630666666666663,
      10.770666666666667, 32.17066666666666, 6.750666666666666, 7.590666666666667,
      16.930666666666667, 6.050666666666666, 7.710666666666668],
};

test.beforeEach(async ({ page }) => {
  await page.goto(INDEX_URL);
});

test.describe('moderation-engine.js', () => {
  test('regression coefficients match hand-computed reference values', async ({ page }) => {
    const result = await page.evaluate((fixture) => analyzeModeration(fixture, 0.05), FIXTURE);
    expect(result.beta[0]).toBeCloseTo(10.035270724890479, 5);
    expect(result.beta[1]).toBeCloseTo(1.2076187802311653, 5);
    expect(result.beta[2]).toBeCloseTo(0.8238704155315291, 5);
    expect(result.beta[3]).toBeCloseTo(0.5773905609676386, 5);
    expect(result.se[1]).toBeCloseTo(0.018316758113552756, 5);
    expect(result.se[3]).toBeCloseTo(0.007776292638102513, 5);
    expect(result.dof).toBe(11);
  });

  test('SD of the moderator and simple slopes at -1/0/+1 SD match reference values', async ({ page }) => {
    const result = await page.evaluate((fixture) => analyzeModeration(fixture, 0.05), FIXTURE);
    expect(result.sdZ).toBeCloseTo(2.76371041140262, 5);
    expect(result.simpleSlopes[0].zVal).toBeCloseTo(-2.76371041140262, 4);
    expect(result.simpleSlopes[0].slope).toBeCloseTo(-0.3881256813123, 3);
    expect(result.simpleSlopes[1].slope).toBeCloseTo(1.2076187802311653, 5);
    expect(result.simpleSlopes[2].slope).toBeCloseTo(2.8034, 3);
  });

  test('Johnson-Neyman roots match independently hand-computed and self-verified reference values', async ({ page }) => {
    const result = await page.evaluate((fixture) => analyzeModeration(fixture, 0.05), FIXTURE);
    expect(result.jnRoots).not.toBeNull();
    expect(result.jnRoots[0]).toBeCloseTo(-2.19090829611953, 3);
    expect(result.jnRoots[1]).toBeCloseTo(-1.996152224371137, 3);
  });

  test('plugging a Johnson-Neyman root back into the slope/SE formula reproduces exactly +/- t_crit', async ({ page }) => {
    const result = await page.evaluate((fixture) => {
      const stats = analyzeModeration(fixture, 0.05);
      const varB1 = stats.cov[1][1], varB3 = stats.cov[3][3], covB1B3 = stats.cov[1][3];
      const tsAtRoots = stats.jnRoots.map((z) => {
        const slope = stats.beta[1] + stats.beta[3] * z;
        const se = Math.sqrt(varB1 + z * z * varB3 + 2 * z * covB1B3);
        return Math.abs(slope / se);
      });
      return { tCrit: stats.tCrit, tsAtRoots };
    }, FIXTURE);
    result.tsAtRoots.forEach((t) => expect(t).toBeCloseTo(result.tCrit, 4));
  });

  test('solveJohnsonNeyman returns null when the discriminant is negative (no boundary)', async ({ page }) => {
    const hasRoots = await page.evaluate(() => {
      // b3 tiny relative to its variance and tCrit large -> A<0, C<0, likely
      // no real crossing within a realistic range for a deliberately flat interaction.
      const roots = solveJohnsonNeyman(0.01, 0.001, 0.5, 0.5, 0.0, 50);
      return roots;
    });
    expect(hasRoots).toBeNull();
  });

  test('same seed reproduces bit-for-bit identical sample and regression results (determinism)', async ({ page }) => {
    const results = await page.evaluate(() => {
      function run() {
        const sample = generateModerationSample({ trueB1: 1.0, trueB2: 0.4, trueB3: 0.5, noiseSD: 1.5, n: 35, seed: 555 });
        const stats = analyzeModeration(sample, 0.05);
        return { X: sample.X, Z: sample.Z, Y: sample.Y, beta: stats.beta, jnRoots: stats.jnRoots };
      }
      return [run(), run()];
    });
    expect(results[0]).toEqual(results[1]);
  });

  test('a strong interaction (large true b3, low noise) produces a significant interaction term', async ({ page }) => {
    const result = await page.evaluate(() => {
      const sample = generateModerationSample({ trueB1: 1.0, trueB2: 0.5, trueB3: 1.2, noiseSD: 0.3, n: 50, seed: 21 });
      return analyzeModeration(sample, 0.05);
    });
    expect(result.interactionSignificant).toBe(true);
  });

  test('a near-zero true interaction (high noise) is not significant', async ({ page }) => {
    const result = await page.evaluate(() => {
      const sample = generateModerationSample({ trueB1: 1.0, trueB2: 0.5, trueB3: 0.0, noiseSD: 5.0, n: 40, seed: 8 });
      return analyzeModeration(sample, 0.05);
    });
    expect(result.interactionSignificant).toBe(false);
  });
});
