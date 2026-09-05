const { test, expect } = require('@playwright/test');
const path = require('path');

const INDEX_URL = 'file://' + path.join(__dirname, '..', 'index.html');

test.beforeEach(async ({ page }) => {
  await page.goto(INDEX_URL);
});

test.describe('stats.js core math', () => {
  test('OLS simple regression matches independently hand-computed reference (path a: M~X)', async ({ page }) => {
    const X = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
    const M = [4.0, 4.7, 6.7, 7.4, 9.9, 10.9, 12.8, 13.6, 16.1, 16.8];
    const result = await page.evaluate(({ X, M }) => {
      const r = ols(X.map(x => [x]), M);
      return { beta: r.beta, se: r.se };
    }, { X, M });
    // Independently hand-computed via a from-scratch pure-Python Gauss-Jordan
    // reference implementation (see BUILD_LOG.md), not derived from this JS.
    expect(result.beta[0]).toBeCloseTo(2.0666666666666487, 6);
    expect(result.beta[1]).toBeCloseTo(1.495151515151516, 6);
    expect(result.se[0]).toBeCloseTo(0.2999225489247773, 6);
    expect(result.se[1]).toBeCloseTo(0.04833689547052224, 6);
  });

  test('OLS multiple regression matches hand-computed reference (path b/c prime: Y~X+M)', async ({ page }) => {
    const X = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
    const M = [4.0, 4.7, 6.7, 7.4, 9.9, 10.9, 12.8, 13.6, 16.1, 16.8];
    const Y = [9.7, 11.3, 16.2, 17.6, 23.4, 25.5, 30.3, 32.2, 37.6, 39.8];
    const result = await page.evaluate(({ X, M, Y }) => {
      const rows = X.map((x, i) => [x, M[i]]);
      const r = ols(rows, Y);
      return { beta: r.beta, se: r.se };
    }, { X, M, Y });
    expect(result.beta[0]).toBeCloseTo(0.6160226379502092, 5);
    expect(result.beta[1]).toBeCloseTo(0.17938060053438676, 5);
    expect(result.beta[2]).toBeCloseTo(2.2116019493789736, 5);
    expect(result.se[1]).toBeCloseTo(0.24628802902149827, 5);
    expect(result.se[2]).toBeCloseTo(0.16404009026660027, 5);
  });

  test('matrix inverse throws on a singular (perfectly collinear) design matrix', async ({ page }) => {
    const threw = await page.evaluate(() => {
      try {
        // Two predictors that are identical make X'X singular.
        ols([[1, 1], [2, 2], [3, 3], [4, 4]], [5, 8, 11, 14]);
        return false;
      } catch (e) {
        return true;
      }
    });
    expect(threw).toBe(true);
  });

  test('Student t CDF reduces exactly to the closed-form Cauchy CDF at df=1', async ({ page }) => {
    const result = await page.evaluate(() => {
      const t = 1.5;
      const cdfViaStudentT = studentTCDF(t, 1);
      const cauchyClosedForm = 0.5 + Math.atan(t) / Math.PI;
      return { cdfViaStudentT, cauchyClosedForm };
    });
    expect(result.cdfViaStudentT).toBeCloseTo(result.cauchyClosedForm, 6);
  });

  test('studentTCritical(df=11, alpha=.05) matches the tabulated t-critical value', async ({ page }) => {
    const tCrit = await page.evaluate(() => studentTCritical(11, 0.05));
    // Standard tabulated two-tailed t-critical value for df=11, alpha=.05.
    expect(tCrit).toBeCloseTo(2.200985, 3);
  });

  test('normalCDF(0) is exactly 0.5 and is monotonically increasing', async ({ page }) => {
    const result = await page.evaluate(() => ({
      zero: normalCDF(0),
      neg: normalCDF(-2),
      pos: normalCDF(2),
    }));
    expect(result.zero).toBeCloseTo(0.5, 6);
    expect(result.neg).toBeLessThan(result.zero);
    expect(result.pos).toBeGreaterThan(result.zero);
    expect(result.pos).toBeCloseTo(1 - result.neg, 6);
  });

  test('quantile() interpolates correctly on a known sorted array', async ({ page }) => {
    const result = await page.evaluate(() => {
      const arr = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
      return {
        median: quantile(arr, 0.5),
        p025: quantile(arr, 0.025),
        p975: quantile(arr, 0.975),
      };
    });
    expect(result.median).toBeCloseTo(5.5, 6);
    expect(result.p025).toBeCloseTo(1.225, 3);
    expect(result.p975).toBeCloseTo(9.775, 3);
  });

  test('sampleSD matches the standard n-1 formula on a known array', async ({ page }) => {
    const sd = await page.evaluate(() => sampleSD([2, 4, 4, 4, 5, 5, 7, 9]));
    // Classic textbook array: mean=5, sum of squared deviations=32.
    // Sample SD (n-1=7 denominator) = sqrt(32/7) = 2.1380899...
    // (Population SD with an n=8 denominator would be exactly 2, but this
    // engine deliberately uses the sample formula throughout, matching the
    // moderator-SD usage in moderation-engine.js.)
    expect(sd).toBeCloseTo(Math.sqrt(32 / 7), 6);
  });
});
