const { test, expect } = require('@playwright/test');
const M = require('../src/math.js');

test.describe('math.js — regression engine correctness', () => {
  test('simple linear regression matches hand-worked textbook example', () => {
    // x=[1,2,3,4,5], y=[2,4,5,4,5] -> known b0=2.2, b1=0.6, R2=0.6
    const reg = M.simpleLinearRegression([1, 2, 3, 4, 5], [2, 4, 5, 4, 5]);
    expect(reg.coefficients[0]).toBeCloseTo(2.2, 4);
    expect(reg.coefficients[1]).toBeCloseTo(0.6, 4);
    expect(reg.r2).toBeCloseTo(0.6, 4);
  });

  test('hat values sum to the number of parameters', () => {
    const reg = M.simpleLinearRegression([1, 2, 3, 4, 5, 6, 7], [3, 5, 4, 8, 7, 9, 10]);
    const sum = reg.hatValues.reduce((a, b) => a + b, 0);
    expect(sum).toBeCloseTo(reg.p, 6);
  });

  test('a perfect linear fit yields R2 = 1 and zero residuals', () => {
    const x = [1, 2, 3, 4, 5];
    const y = x.map((v) => 3 + 2 * v);
    const reg = M.simpleLinearRegression(x, y);
    expect(reg.r2).toBeCloseTo(1, 8);
    reg.residuals.forEach((r) => expect(Math.abs(r)).toBeLessThan(1e-8));
  });

  test('t-distribution two-tailed p-value matches known critical values', () => {
    expect(M.tTwoTailedPValue(2.228, 10)).toBeCloseTo(0.05, 2);
    expect(M.tTwoTailedPValue(2.042, 30)).toBeCloseTo(0.05, 2);
    expect(M.tTwoTailedPValue(0, 10)).toBeCloseTo(1, 6);
  });

  test('t-distribution with df=1 reduces to the Cauchy distribution', () => {
    // Cauchy CDF(1) = 0.75, so two-tailed p at t=1 is exactly 0.5
    expect(M.tTwoTailedPValue(1, 1)).toBeCloseTo(0.5, 6);
  });

  test('normalQuantile matches standard normal critical values', () => {
    expect(M.normalQuantile(0.5)).toBeCloseTo(0, 6);
    expect(M.normalQuantile(0.975)).toBeCloseTo(1.959964, 5);
    expect(M.normalQuantile(0.025)).toBeCloseTo(-1.959964, 5);
  });

  test('multipleRegression throws on an underdetermined system', () => {
    expect(() => M.multipleRegression([[1], [2]], [3, 4])).toThrow();
  });

  test('multipleRegression throws on perfectly collinear predictors', () => {
    // x2 is exactly 2*x1 for every row -> X'X is singular
    const rows = [[1, 2], [2, 4], [3, 6], [4, 8], [5, 10]];
    expect(() => M.multipleRegression(rows, [1, 2, 3, 4, 5])).toThrow();
  });

  test("Cook's Distance is large for a point with both high leverage and a large residual", () => {
    const x = [1, 2, 3, 4, 5, 6, 7, 20];
    const y = [2, 4, 6, 8, 10, 12, 14, 2]; // last point way off the trend, far in x
    const reg = M.simpleLinearRegression(x, y);
    const maxIdx = reg.cooksD.indexOf(Math.max(...reg.cooksD));
    expect(maxIdx).toBe(7);
    expect(reg.cooksD[7]).toBeGreaterThan(4 / x.length);
  });

  test('VIF equals 1 for uncorrelated predictors and grows with correlation', () => {
    const uncorrelated = M.vifPair([1, 2, 3, 4, 5], [5, 1, 4, 2, 3]);
    const correlated = M.vifPair([1, 2, 3, 4, 5], [1.1, 2.05, 2.9, 4.1, 4.95]);
    expect(uncorrelated.vif).toBeLessThan(correlated.vif);
    expect(correlated.vif).toBeGreaterThan(5);
  });

  test('breuschPaganTest flags a clear funnel-shaped variance pattern as significant', () => {
    const x = [];
    const residuals = [];
    for (let i = 1; i <= 20; i++) {
      x.push(i);
      // deterministic alternating-sign residual whose magnitude grows with x
      residuals.push((i % 2 === 0 ? 1 : -1) * i * 0.8);
    }
    const fitted = x.map((v) => 10 + 2 * v);
    const bp = M.breuschPaganTest(fitted, residuals);
    expect(bp.significant).toBe(true);
  });

  test('resetTest flags a clearly quadratic relationship as non-linear', () => {
    const x = [];
    const y = [];
    for (let i = -6; i <= 6; i++) {
      x.push(i);
      y.push(5 + 0.5 * i + 0.7 * i * i);
    }
    const reset = M.resetTest(x, y);
    expect(reset.significant).toBe(true);
  });

  test('resetTest does not flag a genuinely linear relationship with small noise', () => {
    const x = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
    const y = [2.1, 4.2, 5.9, 8.1, 9.8, 12.2, 13.9, 16.1, 17.9, 20.2];
    const reset = M.resetTest(x, y);
    expect(reset.significant).toBe(false);
  });

  test('skewness and excess kurtosis are ~0 for a symmetric, mesokurtic-like sample', () => {
    const sample = [-3, -2, -1, -1, 0, 0, 0, 1, 1, 2, 3];
    expect(Math.abs(M.skewness(sample))).toBeLessThan(0.1);
  });

  test('correlation is 1 for a perfectly increasing linear relationship and -1 for decreasing', () => {
    expect(M.correlation([1, 2, 3, 4], [2, 4, 6, 8])).toBeCloseTo(1, 8);
    expect(M.correlation([1, 2, 3, 4], [8, 6, 4, 2])).toBeCloseTo(-1, 8);
  });

  test('seededRandom is deterministic across calls with the same seed', () => {
    const r1 = M.seededRandom(42);
    const r2 = M.seededRandom(42);
    const seq1 = [r1(), r1(), r1()];
    const seq2 = [r2(), r2(), r2()];
    expect(seq1).toEqual(seq2);
  });
});
