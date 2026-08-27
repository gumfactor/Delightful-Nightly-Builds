/**
 * Regression Lab — core statistics engine.
 * Classic script: attaches to `window` in the browser, exports via
 * module.exports under Node so Playwright tests can require() the exact
 * file the browser loads.
 */

// ---------- Matrix algebra ----------

function transpose(M) {
  const rows = M.length, cols = M[0].length;
  const T = [];
  for (let j = 0; j < cols; j++) {
    T.push(new Array(rows));
    for (let i = 0; i < rows; i++) T[j][i] = M[i][j];
  }
  return T;
}

function matMul(A, B) {
  const rowsA = A.length, colsA = A[0].length, colsB = B[0].length;
  const C = [];
  for (let i = 0; i < rowsA; i++) {
    C.push(new Array(colsB).fill(0));
    for (let k = 0; k < colsA; k++) {
      const a = A[i][k];
      if (a === 0) continue;
      for (let j = 0; j < colsB; j++) {
        C[i][j] += a * B[k][j];
      }
    }
  }
  return C;
}

// Gauss-Jordan elimination with partial pivoting.
function invertMatrix(M) {
  const n = M.length;
  const A = M.map((row) => row.slice());
  const I = [];
  for (let i = 0; i < n; i++) {
    I.push(new Array(n).fill(0));
    I[i][i] = 1;
  }
  for (let col = 0; col < n; col++) {
    let pivotRow = col;
    let maxAbs = Math.abs(A[col][col]);
    for (let r = col + 1; r < n; r++) {
      if (Math.abs(A[r][col]) > maxAbs) {
        maxAbs = Math.abs(A[r][col]);
        pivotRow = r;
      }
    }
    if (maxAbs < 1e-10) {
      throw new Error('Matrix is singular or near-singular — predictors may be perfectly collinear');
    }
    if (pivotRow !== col) {
      [A[col], A[pivotRow]] = [A[pivotRow], A[col]];
      [I[col], I[pivotRow]] = [I[pivotRow], I[col]];
    }
    const pivot = A[col][col];
    for (let j = 0; j < n; j++) {
      A[col][j] /= pivot;
      I[col][j] /= pivot;
    }
    for (let r = 0; r < n; r++) {
      if (r === col) continue;
      const factor = A[r][col];
      if (factor === 0) continue;
      for (let j = 0; j < n; j++) {
        A[r][j] -= factor * A[col][j];
        I[r][j] -= factor * I[col][j];
      }
    }
  }
  return I;
}

// ---------- Special functions (Lanczos log-gamma, incomplete beta) ----------

function logGamma(x) {
  const g = 7;
  const c = [
    0.99999999999980993, 676.5203681218851, -1259.1392167224028,
    771.32342877765313, -176.61502916214059, 12.507343278686905,
    -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7,
  ];
  if (x < 0.5) {
    return Math.log(Math.PI / Math.sin(Math.PI * x)) - logGamma(1 - x);
  }
  x -= 1;
  let a = c[0];
  const t = x + g + 0.5;
  for (let i = 1; i < g + 2; i++) {
    a += c[i] / (x + i);
  }
  return 0.5 * Math.log(2 * Math.PI) + (x + 0.5) * Math.log(t) - t + Math.log(a);
}

function betacf(x, a, b) {
  const MAXIT = 200, EPS = 3e-14, FPMIN = 1e-300;
  const qab = a + b, qap = a + 1, qam = a - 1;
  let c = 1;
  let d = 1 - (qab * x) / qap;
  if (Math.abs(d) < FPMIN) d = FPMIN;
  d = 1 / d;
  let h = d;
  for (let m = 1; m <= MAXIT; m++) {
    const m2 = 2 * m;
    let aa = (m * (b - m) * x) / ((qam + m2) * (a + m2));
    d = 1 + aa * d;
    if (Math.abs(d) < FPMIN) d = FPMIN;
    c = 1 + aa / c;
    if (Math.abs(c) < FPMIN) c = FPMIN;
    d = 1 / d;
    h *= d * c;
    aa = (-(a + m) * (qab + m) * x) / ((a + m2) * (qap + m2));
    d = 1 + aa * d;
    if (Math.abs(d) < FPMIN) d = FPMIN;
    c = 1 + aa / c;
    if (Math.abs(c) < FPMIN) c = FPMIN;
    d = 1 / d;
    const del = d * c;
    h *= del;
    if (Math.abs(del - 1) < EPS) break;
  }
  return h;
}

// Regularized incomplete beta function I_x(a, b).
function regularizedIncompleteBeta(x, a, b) {
  if (x <= 0) return 0;
  if (x >= 1) return 1;
  const bt = Math.exp(
    logGamma(a + b) - logGamma(a) - logGamma(b) + a * Math.log(x) + b * Math.log(1 - x)
  );
  if (x < (a + 1) / (a + b + 2)) {
    return (bt * betacf(x, a, b)) / a;
  }
  return 1 - (bt * betacf(1 - x, b, a)) / b;
}

// Two-tailed Student's t CDF / p-value.
function tCDF(t, df) {
  const x = df / (df + t * t);
  const ib = regularizedIncompleteBeta(x, df / 2, 0.5);
  return t > 0 ? 1 - 0.5 * ib : 0.5 * ib;
}

function tTwoTailedPValue(t, df) {
  if (!Number.isFinite(t) || df <= 0) return NaN;
  return 2 * (1 - tCDF(Math.abs(t), df));
}

// Inverse standard normal CDF (Acklam's algorithm).
function normalQuantile(p) {
  if (p <= 0) return -Infinity;
  if (p >= 1) return Infinity;
  const a = [
    -3.969683028665376e1, 2.209460984245205e2, -2.759285104469687e2,
    1.383577518672690e2, -3.066479806614716e1, 2.506628277459239e0,
  ];
  const b = [
    -5.447609879822406e1, 1.615858368580409e2, -1.556989798598866e2,
    6.680131188771972e1, -1.328068155288572e1,
  ];
  const c = [
    -7.784894002430293e-3, -3.223964580411365e-1, -2.400758277161838e0,
    -2.549732539343734e0, 4.374664141464968e0, 2.938163982698783e0,
  ];
  const d = [
    7.784695709041462e-3, 3.224671290700398e-1, 2.445134137142996e0,
    3.754408661907416e0,
  ];
  const plow = 0.02425;
  const phigh = 1 - plow;
  let q, r;
  if (p < plow) {
    q = Math.sqrt(-2 * Math.log(p));
    return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) /
      ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1);
  }
  if (p <= phigh) {
    q = p - 0.5;
    r = q * q;
    return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q /
      (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1);
  }
  q = Math.sqrt(-2 * Math.log(1 - p));
  return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) /
    ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1);
}

// ---------- Descriptive stats ----------

function mean(arr) {
  return arr.reduce((s, v) => s + v, 0) / arr.length;
}

function skewness(arr) {
  const n = arr.length;
  const m = mean(arr);
  const sd = Math.sqrt(arr.reduce((s, v) => s + (v - m) ** 2, 0) / n);
  if (sd === 0) return 0;
  const m3 = arr.reduce((s, v) => s + (v - m) ** 3, 0) / n;
  return m3 / sd ** 3;
}

function excessKurtosis(arr) {
  const n = arr.length;
  const m = mean(arr);
  const sd = Math.sqrt(arr.reduce((s, v) => s + (v - m) ** 2, 0) / n);
  if (sd === 0) return 0;
  const m4 = arr.reduce((s, v) => s + (v - m) ** 4, 0) / n;
  return m4 / sd ** 4 - 3;
}

function correlation(x, y) {
  const n = x.length;
  const mx = mean(x), my = mean(y);
  let sxy = 0, sxx = 0, syy = 0;
  for (let i = 0; i < n; i++) {
    const dx = x[i] - mx, dy = y[i] - my;
    sxy += dx * dy;
    sxx += dx * dx;
    syy += dy * dy;
  }
  if (sxx === 0 || syy === 0) return 0;
  return sxy / Math.sqrt(sxx * syy);
}

// ---------- Regression engine ----------

/**
 * Ordinary least squares via the normal equations, solved through a
 * Gauss-Jordan matrix inverse. predictorRows: array of n rows, each an
 * array of k predictor values (no intercept column — it is added here).
 */
function multipleRegression(predictorRows, y) {
  const n = predictorRows.length;
  if (n === 0) throw new Error('Need at least one data point');
  const k = predictorRows[0].length;
  const p = k + 1;
  if (n <= p) {
    throw new Error(`Need at least ${p + 1} points for ${k} predictor(s); have ${n}`);
  }
  const X = predictorRows.map((row) => [1, ...row]);
  const Xt = transpose(X);
  const XtX = matMul(Xt, X);
  const XtXinv = invertMatrix(XtX);
  const XtY = matMul(Xt, y.map((v) => [v]));
  const betaCol = matMul(XtXinv, XtY);
  const coefficients = betaCol.map((r) => r[0]);

  const fitted = X.map((row) => row.reduce((s, v, j) => s + v * coefficients[j], 0));
  const residuals = y.map((v, i) => v - fitted[i]);
  const yMean = mean(y);
  const sst = y.reduce((s, v) => s + (v - yMean) ** 2, 0);
  const sse = residuals.reduce((s, e) => s + e * e, 0);
  const ssr = sst - sse;
  const r2 = sst === 0 ? 1 : 1 - sse / sst;
  const df = n - p;
  const mse = sse / df;
  const adjR2 = df > 0 ? 1 - (1 - r2) * (n - 1) / df : NaN;

  const hatValues = X.map((row) => {
    let h = 0;
    for (let a = 0; a < p; a++) {
      let s = 0;
      for (let b = 0; b < p; b++) s += XtXinv[a][b] * row[b];
      h += row[a] * s;
    }
    return h;
  });

  const se = coefficients.map((_, i) => Math.sqrt(Math.max(mse * XtXinv[i][i], 0)));
  const tStats = coefficients.map((b, i) => (se[i] > 0 ? b / se[i] : NaN));
  const pValues = tStats.map((t) => tTwoTailedPValue(t, df));

  const stdResiduals = residuals.map((e, i) => {
    const denom = Math.sqrt(mse * (1 - hatValues[i]));
    return denom > 1e-9 ? e / denom : 0;
  });

  const cooksD = stdResiduals.map((r, i) => {
    const h = hatValues[i];
    if (h >= 1) return Infinity;
    return (r * r * h) / (p * (1 - h));
  });

  return {
    n, p, k, coefficients, se, tStats, pValues, fitted, residuals,
    hatValues, stdResiduals, cooksD, r2, adjR2, sse, sst, ssr, mse, df,
  };
}

function simpleLinearRegression(x, y) {
  return multipleRegression(x.map((v) => [v]), y);
}

/**
 * Ramsey RESET-style linearity test: adds x^2 to the model and tests
 * whether its coefficient is significantly different from zero.
 */
function resetTest(x, y) {
  const reg = multipleRegression(x.map((v) => [v, v * v]), y);
  return {
    b2: reg.coefficients[2],
    se: reg.se[2],
    tStat: reg.tStats[2],
    pValue: reg.pValues[2],
    significant: reg.pValues[2] < 0.05,
    df: reg.df,
  };
}

/**
 * Simplified Breusch-Pagan heteroscedasticity test: regresses squared
 * residuals on the fitted values and tests whether that slope is
 * significantly different from zero.
 *
 * When the fitted values are (near-)constant — e.g. the primary fit has an
 * exactly-zero slope — the auxiliary regression's design matrix is
 * singular (the fitted-value column carries no information), so the test
 * simply isn't applicable rather than being a computation to attempt.
 */
function breuschPaganTest(fitted, residuals) {
  const fittedMean = mean(fitted);
  const fittedVariance = fitted.reduce((s, v) => s + (v - fittedMean) ** 2, 0);
  if (fittedVariance < 1e-9) {
    return {
      slope: 0, se: NaN, tStat: NaN, pValue: NaN, significant: false, df: NaN, applicable: false,
    };
  }
  const sq = residuals.map((e) => e * e);
  const reg = simpleLinearRegression(fitted, sq);
  return {
    slope: reg.coefficients[1],
    se: reg.se[1],
    tStat: reg.tStats[1],
    pValue: reg.pValues[1],
    significant: reg.pValues[1] < 0.05,
    df: reg.df,
    applicable: true,
  };
}

/** Variance Inflation Factor between two predictors. */
function vifPair(x1, x2) {
  const r = correlation(x1, x2);
  const r2 = r * r;
  const vif = r2 >= 1 ? Infinity : 1 / (1 - r2);
  return { correlation: r, r2, vif };
}

// ---------- Seeded PRNG (deterministic presets) ----------

function seededRandom(seed) {
  let s = seed >>> 0;
  return function () {
    s |= 0;
    s = (s + 0x6d2b79f5) | 0;
    let t = Math.imul(s ^ (s >>> 15), 1 | s);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function gaussianFromUniform(rand) {
  const u1 = Math.max(rand(), 1e-12);
  const u2 = rand();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

const RegressionMath = {
  transpose, matMul, invertMatrix,
  logGamma, regularizedIncompleteBeta, tCDF, tTwoTailedPValue, normalQuantile,
  mean, skewness, excessKurtosis, correlation,
  multipleRegression, simpleLinearRegression, resetTest, breuschPaganTest, vifPair,
  seededRandom, gaussianFromUniform,
};

if (typeof module !== 'undefined' && module.exports) {
  module.exports = RegressionMath;
}
if (typeof window !== 'undefined') {
  window.RegressionMath = RegressionMath;
}
