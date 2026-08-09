/*
 * Portfolio Lab — pure math module. No DOM access, no globals besides the
 * single PortfolioMath namespace, so it can be unit-tested directly via
 * page.evaluate() in Playwright and reused unchanged by app.js.
 *
 * Classic script (no ES module) — loaded before app.js in index.html.
 */
var PortfolioMath = (function () {
  'use strict';

  // ---- Deterministic PRNG (mulberry32) ------------------------------
  // Math.random() would make the Monte Carlo cloud and quiz rounds
  // non-reproducible, which makes both manual QA and automated tests
  // impossible to pin down. A tiny seeded PRNG keeps everything testable
  // while still looking "random" to the user (reseed via a counter for a
  // fresh cloud/quiz round on demand).
  function mulberry32(seed) {
    let a = seed >>> 0;
    return function () {
      a |= 0;
      a = (a + 0x6d2b79f5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  // ---- Small vector/matrix helpers -----------------------------------
  function vecDot(a, b) {
    let s = 0;
    for (let i = 0; i < a.length; i++) s += a[i] * b[i];
    return s;
  }

  function matVecMul(mat, vec) {
    return mat.map((row) => vecDot(row, vec));
  }

  function quadForm(vec, mat) {
    // vec^T * mat * vec
    return vecDot(vec, matVecMul(mat, vec));
  }

  // Gauss-Jordan inversion of an NxN matrix. Throws on a singular /
  // near-singular matrix rather than silently returning NaN/Infinity.
  function matInverse(matrix) {
    const n = matrix.length;
    // Augment [A | I]
    const aug = matrix.map((row, i) => {
      const identityRow = new Array(n).fill(0);
      identityRow[i] = 1;
      return row.concat(identityRow);
    });

    for (let col = 0; col < n; col++) {
      // Partial pivot: find the row with the largest absolute value in this column
      let pivotRow = col;
      let maxAbs = Math.abs(aug[col][col]);
      for (let r = col + 1; r < n; r++) {
        if (Math.abs(aug[r][col]) > maxAbs) {
          maxAbs = Math.abs(aug[r][col]);
          pivotRow = r;
        }
      }
      if (maxAbs < 1e-10) {
        throw new Error('Matrix is singular or near-singular — cannot invert.');
      }
      if (pivotRow !== col) {
        const tmp = aug[col];
        aug[col] = aug[pivotRow];
        aug[pivotRow] = tmp;
      }
      const pivotVal = aug[col][col];
      for (let c = 0; c < 2 * n; c++) aug[col][c] /= pivotVal;
      for (let r = 0; r < n; r++) {
        if (r === col) continue;
        const factor = aug[r][col];
        if (factor === 0) continue;
        for (let c = 0; c < 2 * n; c++) aug[r][c] -= factor * aug[col][c];
      }
    }
    return aug.map((row) => row.slice(n));
  }

  // ---- Portfolio statistics -------------------------------------------

  // Two-asset mix using the real covariance matrix entries directly
  // (cov[i][i] = variance of asset i, so this stays consistent with the
  // full N-asset math without re-deriving correlation separately).
  function twoAssetStats(meanA, meanB, covAA, covBB, covAB, weightA) {
    const wA = weightA;
    const wB = 1 - weightA;
    const ret = wA * meanA + wB * meanB;
    const variance = wA * wA * covAA + wB * wB * covBB + 2 * wA * wB * covAB;
    return { return: ret, volatility: Math.sqrt(Math.max(variance, 0)) };
  }

  function portfolioStats(weights, meanVec, covMatrix) {
    const ret = vecDot(weights, meanVec);
    const variance = quadForm(weights, covMatrix);
    return { return: ret, volatility: Math.sqrt(Math.max(variance, 0)) };
  }

  // Sample a random long-only weight vector (sums to 1, all >= 0) drawn
  // uniformly from the simplex via the standard exponential-normalization
  // trick: n Exp(1) draws, normalized, are uniform on the simplex.
  function randomLongOnlyWeights(n, rng) {
    const draws = [];
    let sum = 0;
    for (let i = 0; i < n; i++) {
      const u = Math.max(rng(), 1e-12);
      const e = -Math.log(u);
      draws.push(e);
      sum += e;
    }
    return draws.map((d) => d / sum);
  }

  function monteCarloCloud(meanVec, covMatrix, nSamples, rng) {
    const n = meanVec.length;
    const points = [];
    for (let i = 0; i < nSamples; i++) {
      const weights = randomLongOnlyWeights(n, rng);
      const stats = portfolioStats(weights, meanVec, covMatrix);
      points.push({ weights, return: stats.return, volatility: stats.volatility });
    }
    return points;
  }

  // Precompute the scalars used by the closed-form (unconstrained,
  // shorting-allowed) Markowitz two-fund frontier: A = 1'Σ⁻¹1,
  // B = 1'Σ⁻¹μ, C = μ'Σ⁻¹μ, D = AC - B².
  function frontierCoefficients(meanVec, covMatrix) {
    const n = meanVec.length;
    const ones = new Array(n).fill(1);
    const invCov = matInverse(covMatrix);
    const invCovOnes = matVecMul(invCov, ones);
    const invCovMean = matVecMul(invCov, meanVec);
    const A = vecDot(ones, invCovOnes);
    const B = vecDot(ones, invCovMean);
    const C = vecDot(meanVec, invCovMean);
    const D = A * C - B * B;
    if (Math.abs(D) < 1e-10) {
      throw new Error('Degenerate frontier (D ~ 0) — asset set is not diversified enough.');
    }
    return { invCov, invCovOnes, invCovMean, A, B, C, D };
  }

  // Global minimum variance portfolio: w = Σ⁻¹1 / (1'Σ⁻¹1)
  function globalMinVariancePortfolio(meanVec, covMatrix, coeffs) {
    const c = coeffs || frontierCoefficients(meanVec, covMatrix);
    const weights = c.invCovOnes.map((x) => x / c.A);
    const stats = portfolioStats(weights, meanVec, covMatrix);
    return { weights, return: stats.return, volatility: stats.volatility };
  }

  // Efficient frontier portfolio for a given target return (two-fund
  // theorem closed form). Weights may go negative (short positions) —
  // this is the standard unconstrained analytical frontier; the
  // long-only Monte Carlo cloud is a strict subset of what it dominates.
  function efficientFrontierPoint(targetReturn, meanVec, covMatrix, coeffs) {
    const c = coeffs || frontierCoefficients(meanVec, covMatrix);
    const lambda1 = (c.C - c.B * targetReturn) / c.D;
    const lambda2 = (c.A * targetReturn - c.B) / c.D;
    const n = meanVec.length;
    const weights = new Array(n);
    for (let i = 0; i < n; i++) {
      weights[i] = lambda1 * c.invCovOnes[i] + lambda2 * c.invCovMean[i];
    }
    const stats = portfolioStats(weights, meanVec, covMatrix);
    return { weights, return: stats.return, volatility: stats.volatility };
  }

  function sharpeRatio(ret, volatility, riskFreeRate) {
    if (volatility <= 0) return 0;
    return (ret - riskFreeRate) / volatility;
  }

  // Closed-form tangency portfolio (Merton 1972): the unique unconstrained
  // portfolio maximizing the Sharpe ratio for a given risk-free rate.
  //   w_tan = Σ⁻¹(μ - rf·1) / (1'Σ⁻¹(μ - rf·1))
  // Exact and range-independent — no numerical search needed.
  function tangencyPortfolio(meanVec, covMatrix, riskFreeRate, coeffs) {
    const c = coeffs || frontierCoefficients(meanVec, covMatrix);
    const excessReturns = meanVec.map((m) => m - riskFreeRate);
    const numerator = matVecMul(c.invCov, excessReturns);
    const denom = numerator.reduce((sum, x) => sum + x, 0);
    if (Math.abs(denom) < 1e-10) {
      throw new Error('Tangency portfolio is undefined at this risk-free rate.');
    }
    const weights = numerator.map((x) => x / denom);
    const stats = portfolioStats(weights, meanVec, covMatrix);
    const sharpe = sharpeRatio(stats.return, stats.volatility, riskFreeRate);
    return { weights: weights, return: stats.return, volatility: stats.volatility, sharpe: sharpe };
  }

  return {
    mulberry32,
    vecDot,
    matVecMul,
    quadForm,
    matInverse,
    twoAssetStats,
    portfolioStats,
    randomLongOnlyWeights,
    monteCarloCloud,
    frontierCoefficients,
    globalMinVariancePortfolio,
    efficientFrontierPoint,
    sharpeRatio,
    tangencyPortfolio,
  };
})();
