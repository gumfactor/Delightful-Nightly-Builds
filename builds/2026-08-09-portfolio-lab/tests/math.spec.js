// @ts-check
const { test, expect } = require('@playwright/test');
const path = require('path');

const HARNESS_URL = 'file://' + path.resolve(__dirname, 'fixtures/math-harness.html');

test.beforeEach(async ({ page }) => {
  await page.goto(HARNESS_URL);
});

test('matInverse inverts the identity matrix to itself', async ({ page }) => {
  const result = await page.evaluate(() => PortfolioMath.matInverse([[1, 0], [0, 1]]));
  expect(result).toEqual([[1, 0], [0, 1]]);
});

test('matInverse matches a hand-calculated 2x2 inverse', async ({ page }) => {
  // A = [[4,7],[2,6]], det = 10, inv = 1/10 * [[6,-7],[-2,4]]
  const result = await page.evaluate(() => PortfolioMath.matInverse([[4, 7], [2, 6]]));
  expect(result[0][0]).toBeCloseTo(0.6, 9);
  expect(result[0][1]).toBeCloseTo(-0.7, 9);
  expect(result[1][0]).toBeCloseTo(-0.2, 9);
  expect(result[1][1]).toBeCloseTo(0.4, 9);
});

test('matInverse throws on a singular matrix', async ({ page }) => {
  const threw = await page.evaluate(() => {
    try {
      PortfolioMath.matInverse([[1, 2], [2, 4]]);
      return false;
    } catch (e) {
      return true;
    }
  });
  expect(threw).toBe(true);
});

test('matInverse * original matrix is (approximately) the identity, for a 4x4', async ({ page }) => {
  const ok = await page.evaluate(() => {
    const A = [
      [0.04, 0.004, 0.036, -0.003],
      [0.004, 0.01, 0.003, -0.0025],
      [0.036, 0.003, 0.09, 0.0],
      [-0.003, -0.0025, 0.0, 0.0025],
    ];
    const inv = PortfolioMath.matInverse(A);
    // A * inv should be the identity
    for (let i = 0; i < 4; i++) {
      for (let j = 0; j < 4; j++) {
        let sum = 0;
        for (let k = 0; k < 4; k++) sum += A[i][k] * inv[k][j];
        const expected = i === j ? 1 : 0;
        if (Math.abs(sum - expected) > 1e-6) return false;
      }
    }
    return true;
  });
  expect(ok).toBe(true);
});

test('twoAssetStats at weightA=1 matches pure asset A', async ({ page }) => {
  const result = await page.evaluate(() =>
    PortfolioMath.twoAssetStats(0.10, 0.06, 0.04, 0.01, 0.004, 1.0)
  );
  expect(result.return).toBeCloseTo(0.10, 9);
  expect(result.volatility).toBeCloseTo(Math.sqrt(0.04), 9);
});

test('twoAssetStats at weightA=0 matches pure asset B', async ({ page }) => {
  const result = await page.evaluate(() =>
    PortfolioMath.twoAssetStats(0.10, 0.06, 0.04, 0.01, 0.004, 0.0)
  );
  expect(result.return).toBeCloseTo(0.06, 9);
  expect(result.volatility).toBeCloseTo(Math.sqrt(0.01), 9);
});

test('twoAssetStats volatility is lower than the naive average when correlation < 1', async ({ page }) => {
  const result = await page.evaluate(() => {
    const stats = PortfolioMath.twoAssetStats(0.10, 0.06, 0.04, 0.01, 0.004, 0.5);
    const naiveVol = 0.5 * Math.sqrt(0.04) + 0.5 * Math.sqrt(0.01);
    return { vol: stats.volatility, naiveVol };
  });
  expect(result.vol).toBeLessThan(result.naiveVol);
});

test('portfolioStats agrees with twoAssetStats for an equivalent 2-asset weight vector', async ({ page }) => {
  const result = await page.evaluate(() => {
    const meanVec = [0.10, 0.06];
    const cov = [[0.04, 0.004], [0.004, 0.01]];
    const weights = [0.3, 0.7];
    const a = PortfolioMath.portfolioStats(weights, meanVec, cov);
    const b = PortfolioMath.twoAssetStats(0.10, 0.06, 0.04, 0.01, 0.004, 0.3);
    return { a, b };
  });
  expect(result.a.return).toBeCloseTo(result.b.return, 9);
  expect(result.a.volatility).toBeCloseTo(result.b.volatility, 9);
});

test('globalMinVariancePortfolio weights sum to 1', async ({ page }) => {
  const sum = await page.evaluate(() => {
    const meanVec = [0.10, 0.06, 0.14, 0.03];
    const cov = [
      [0.04, 0.004, 0.036, -0.003],
      [0.004, 0.01, 0.003, -0.0025],
      [0.036, 0.003, 0.09, 0.0],
      [-0.003, -0.0025, 0.0, 0.0025],
    ];
    const gmv = PortfolioMath.globalMinVariancePortfolio(meanVec, cov);
    return gmv.weights.reduce((s, w) => s + w, 0);
  });
  expect(sum).toBeCloseTo(1, 9);
});

test('global minimum-variance portfolio has lower (or equal) volatility than every sampled long-only Monte Carlo portfolio', async ({ page }) => {
  const ok = await page.evaluate(() => {
    const meanVec = [0.10, 0.06, 0.14, 0.03];
    const cov = [
      [0.04, 0.004, 0.036, -0.003],
      [0.004, 0.01, 0.003, -0.0025],
      [0.036, 0.003, 0.09, 0.0],
      [-0.003, -0.0025, 0.0, 0.0025],
    ];
    const rng = PortfolioMath.mulberry32(12345);
    const gmv = PortfolioMath.globalMinVariancePortfolio(meanVec, cov);
    const cloud = PortfolioMath.monteCarloCloud(meanVec, cov, 500, rng);
    return cloud.every((p) => gmv.volatility <= p.volatility + 1e-9);
  });
  expect(ok).toBe(true);
});

test('efficient frontier point at a cloud portfolio\'s exact return has volatility <= that cloud portfolio (dominance)', async ({ page }) => {
  const ok = await page.evaluate(() => {
    const meanVec = [0.10, 0.06, 0.14, 0.03];
    const cov = [
      [0.04, 0.004, 0.036, -0.003],
      [0.004, 0.01, 0.003, -0.0025],
      [0.036, 0.003, 0.09, 0.0],
      [-0.003, -0.0025, 0.0, 0.0025],
    ];
    const rng = PortfolioMath.mulberry32(999);
    const coeffs = PortfolioMath.frontierCoefficients(meanVec, cov);
    const cloud = PortfolioMath.monteCarloCloud(meanVec, cov, 300, rng);
    return cloud.every((p) => {
      const frontierPoint = PortfolioMath.efficientFrontierPoint(p.return, meanVec, cov, coeffs);
      return frontierPoint.volatility <= p.volatility + 1e-9;
    });
  });
  expect(ok).toBe(true);
});

test('randomLongOnlyWeights always sums to 1 and has no negative entries', async ({ page }) => {
  const ok = await page.evaluate(() => {
    const rng = PortfolioMath.mulberry32(42);
    for (let trial = 0; trial < 50; trial++) {
      const w = PortfolioMath.randomLongOnlyWeights(5, rng);
      const sum = w.reduce((s, x) => s + x, 0);
      if (Math.abs(sum - 1) > 1e-9) return false;
      if (w.some((x) => x < 0)) return false;
    }
    return true;
  });
  expect(ok).toBe(true);
});

test('mulberry32 is deterministic for a fixed seed', async ({ page }) => {
  const result = await page.evaluate(() => {
    const rngA = PortfolioMath.mulberry32(777);
    const rngB = PortfolioMath.mulberry32(777);
    const seqA = [rngA(), rngA(), rngA()];
    const seqB = [rngB(), rngB(), rngB()];
    return { seqA, seqB };
  });
  expect(result.seqA).toEqual(result.seqB);
});

test('sharpeRatio is zero volatility-safe and matches the formula', async ({ page }) => {
  const result = await page.evaluate(() => ({
    normal: PortfolioMath.sharpeRatio(0.1, 0.2, 0.02),
    zeroVol: PortfolioMath.sharpeRatio(0.1, 0, 0.02),
  }));
  expect(result.normal).toBeCloseTo((0.1 - 0.02) / 0.2, 9);
  expect(result.zeroVol).toBe(0);
});

test('tangencyPortfolio has a Sharpe ratio >= the GMV Sharpe ratio', async ({ page }) => {
  const ok = await page.evaluate(() => {
    const meanVec = [0.10, 0.06, 0.14, 0.03];
    const cov = [
      [0.04, 0.004, 0.036, -0.003],
      [0.004, 0.01, 0.003, -0.0025],
      [0.036, 0.003, 0.09, 0.0],
      [-0.003, -0.0025, 0.0, 0.0025],
    ];
    const coeffs = PortfolioMath.frontierCoefficients(meanVec, cov);
    const gmv = PortfolioMath.globalMinVariancePortfolio(meanVec, cov, coeffs);
    const riskFree = 0.02;
    const gmvSharpe = PortfolioMath.sharpeRatio(gmv.return, gmv.volatility, riskFree);
    const tangency = PortfolioMath.tangencyPortfolio(meanVec, cov, riskFree, coeffs);
    return tangency.sharpe >= gmvSharpe - 1e-9;
  });
  expect(ok).toBe(true);
});

test('tangencyPortfolio is a true local (and by convexity, global) Sharpe maximum on the frontier', async ({ page }) => {
  const ok = await page.evaluate(() => {
    const meanVec = [0.10, 0.06, 0.14, 0.03];
    const cov = [
      [0.04, 0.004, 0.036, -0.003],
      [0.004, 0.01, 0.003, -0.0025],
      [0.036, 0.003, 0.09, 0.0],
      [-0.003, -0.0025, 0.0, 0.0025],
    ];
    const coeffs = PortfolioMath.frontierCoefficients(meanVec, cov);
    const riskFree = 0.02;
    const tangency = PortfolioMath.tangencyPortfolio(meanVec, cov, riskFree, coeffs);

    // Sample frontier points just above and below the tangency's target
    // return; the tangency Sharpe ratio should dominate both neighbours.
    const delta = 0.003;
    const below = PortfolioMath.efficientFrontierPoint(tangency.return - delta, meanVec, cov, coeffs);
    const above = PortfolioMath.efficientFrontierPoint(tangency.return + delta, meanVec, cov, coeffs);
    const belowSharpe = PortfolioMath.sharpeRatio(below.return, below.volatility, riskFree);
    const aboveSharpe = PortfolioMath.sharpeRatio(above.return, above.volatility, riskFree);

    return tangency.sharpe >= belowSharpe - 1e-6 && tangency.sharpe >= aboveSharpe - 1e-6;
  });
  expect(ok).toBe(true);
});
