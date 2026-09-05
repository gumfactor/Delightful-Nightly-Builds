// Core statistics engine: matrix algebra, OLS regression, and probability
// distributions, all from scratch (no library). Classic script — attaches
// functions to window (no ES module exports) so index.html can load it with
// a plain <script> tag and open directly via file://.

function transpose(A) {
  const rows = A.length, cols = A[0].length;
  const T = [];
  for (let j = 0; j < cols; j++) {
    const row = new Array(rows);
    for (let i = 0; i < rows; i++) row[i] = A[i][j];
    T.push(row);
  }
  return T;
}

function matmul(A, B) {
  const n = A.length, m = A[0].length, p = B[0].length;
  const R = [];
  for (let i = 0; i < n; i++) {
    const row = new Array(p).fill(0);
    for (let k = 0; k < m; k++) {
      const aik = A[i][k];
      if (aik === 0) continue;
      for (let j = 0; j < p; j++) row[j] += aik * B[k][j];
    }
    R.push(row);
  }
  return R;
}

function matvec(A, v) {
  return A.map(row => row.reduce((sum, a, k) => sum + a * v[k], 0));
}

// Gauss-Jordan matrix inversion with partial pivoting (row with the largest
// absolute pivot-column value is swapped to the top before elimination).
// Throws if the matrix is singular to within a small tolerance.
function inverse(A) {
  const n = A.length;
  const M = A.map((row, i) => {
    const identity = new Array(n).fill(0);
    identity[i] = 1;
    return row.concat(identity);
  });
  for (let col = 0; col < n; col++) {
    let pivotRow = col;
    let maxAbs = Math.abs(M[col][col]);
    for (let r = col + 1; r < n; r++) {
      if (Math.abs(M[r][col]) > maxAbs) {
        maxAbs = Math.abs(M[r][col]);
        pivotRow = r;
      }
    }
    if (pivotRow !== col) {
      const tmp = M[col]; M[col] = M[pivotRow]; M[pivotRow] = tmp;
    }
    const pv = M[col][col];
    if (Math.abs(pv) < 1e-10) {
      throw new Error('singular matrix — predictors are perfectly collinear');
    }
    for (let k = 0; k < 2 * n; k++) M[col][k] /= pv;
    for (let r = 0; r < n; r++) {
      if (r === col) continue;
      const factor = M[r][col];
      if (factor === 0) continue;
      for (let k = 0; k < 2 * n; k++) M[r][k] -= factor * M[col][k];
    }
  }
  return M.map(row => row.slice(n));
}

// Ordinary least squares. featureRows: array of feature arrays WITHOUT an
// intercept column (one is added automatically). Returns coefficients
// (intercept first), standard errors, the full coefficient covariance
// matrix, residuals, residual variance, residual degrees of freedom, and R².
function ols(featureRows, y) {
  const n = featureRows.length;
  const design = featureRows.map(row => [1].concat(row));
  const k = design[0].length;
  const Xt = transpose(design);
  const XtX = matmul(Xt, design);
  const XtXInv = inverse(XtX);
  const Xty = Xt.map(row => row.reduce((s, x, i) => s + x * y[i], 0));
  const beta = matvec(XtXInv, Xty);
  const yhat = design.map(row => row.reduce((s, x, i) => s + x * beta[i], 0));
  const resid = y.map((yi, i) => yi - yhat[i]);
  const dof = n - k;
  const sse = resid.reduce((s, r) => s + r * r, 0);
  const sigma2 = dof > 0 ? sse / dof : NaN;
  const cov = XtXInv.map(row => row.map(v => v * sigma2));
  const se = cov.map((row, i) => Math.sqrt(row[i]));
  const ybar = y.reduce((s, v) => s + v, 0) / n;
  const sst = y.reduce((s, v) => s + (v - ybar) * (v - ybar), 0);
  const r2 = sst > 0 ? 1 - sse / sst : NaN;
  return { beta, se, cov, resid, sigma2, dof, sse, r2, n, k };
}

function mean(arr) {
  return arr.reduce((s, v) => s + v, 0) / arr.length;
}

function sampleSD(arr) {
  const m = mean(arr);
  const n = arr.length;
  const ss = arr.reduce((s, v) => s + (v - m) * (v - m), 0);
  return Math.sqrt(ss / (n - 1));
}

function quantile(sortedArr, p) {
  const n = sortedArr.length;
  const idx = p * (n - 1);
  const lo = Math.floor(idx), hi = Math.ceil(idx);
  if (lo === hi) return sortedArr[lo];
  const frac = idx - lo;
  return sortedArr[lo] * (1 - frac) + sortedArr[hi] * frac;
}

// Log-gamma via the Lanczos approximation (standard 9-term g=7 coefficient set).
const LANCZOS_G = 7;
const LANCZOS_COEF = [
  0.99999999999980993, 676.5203681218851, -1259.1392167224028,
  771.32342877765313, -176.61502916214059, 12.507343278686905,
  -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7,
];

function logGamma(x) {
  if (x < 0.5) {
    return Math.log(Math.PI / Math.sin(Math.PI * x)) - logGamma(1 - x);
  }
  x -= 1;
  let a = LANCZOS_COEF[0];
  const t = x + LANCZOS_G + 0.5;
  for (let i = 1; i < LANCZOS_G + 2; i++) a += LANCZOS_COEF[i] / (x + i);
  return 0.5 * Math.log(2 * Math.PI) + (x + 0.5) * Math.log(t) - t + Math.log(a);
}

// Regularized incomplete beta function I_x(a,b) via a continued-fraction
// expansion (Numerical Recipes' betacf), with the standard symmetry
// transformation for numerical stability when x > (a+1)/(a+b+2).
function betacf(x, a, b) {
  const MAXIT = 200, EPS = 3e-9, FPMIN = 1e-30;
  const qab = a + b, qap = a + 1, qam = a - 1;
  let c = 1, d = 1 - (qab * x) / qap;
  if (Math.abs(d) < FPMIN) d = FPMIN;
  d = 1 / d;
  let h = d;
  for (let m = 1; m <= MAXIT; m++) {
    const m2 = 2 * m;
    let aa = (m * (b - m) * x) / ((qam + m2) * (a + m2));
    d = 1 + aa * d; if (Math.abs(d) < FPMIN) d = FPMIN;
    c = 1 + aa / c; if (Math.abs(c) < FPMIN) c = FPMIN;
    d = 1 / d;
    h *= d * c;
    aa = (-(a + m) * (qab + m) * x) / ((a + m2) * (qap + m2));
    d = 1 + aa * d; if (Math.abs(d) < FPMIN) d = FPMIN;
    c = 1 + aa / c; if (Math.abs(c) < FPMIN) c = FPMIN;
    d = 1 / d;
    const del = d * c;
    h *= del;
    if (Math.abs(del - 1) < EPS) break;
  }
  return h;
}

function regularizedIncompleteBeta(x, a, b) {
  if (x <= 0) return 0;
  if (x >= 1) return 1;
  const bt = Math.exp(
    logGamma(a + b) - logGamma(a) - logGamma(b) +
    a * Math.log(x) + b * Math.log(1 - x)
  );
  if (x < (a + 1) / (a + b + 2)) {
    return (bt * betacf(x, a, b)) / a;
  }
  return 1 - (bt * betacf(1 - x, b, a)) / b;
}

// Two-tailed Student's t CDF-derived p-value is computed by callers as
// 2 * (1 - studentTCDF(|t|, df)). studentTCDF itself is the one-sided CDF.
function studentTCDF(t, df) {
  const x = df / (df + t * t);
  const ib = regularizedIncompleteBeta(x, df / 2, 0.5);
  return t >= 0 ? 1 - 0.5 * ib : 0.5 * ib;
}

function studentTTwoTailedP(t, df) {
  return 2 * (1 - studentTCDF(Math.abs(t), df));
}

// Inverse of the two-sided critical value: find t such that
// studentTTwoTailedP(t, df) == alpha, via bisection (studentTCDF is smooth
// and monotonic in t for t >= 0, so bisection is robust and needs no
// closed form).
function studentTCritical(df, alpha) {
  let lo = 0, hi = 1000;
  for (let i = 0; i < 200; i++) {
    const mid = (lo + hi) / 2;
    const p = studentTTwoTailedP(mid, df);
    if (p > alpha) lo = mid; else hi = mid;
  }
  return (lo + hi) / 2;
}

function normalCDF(z) {
  return 0.5 * (1 + erf(z / Math.SQRT2));
}

// Abramowitz & Stegun 7.1.26 approximation, max error 1.5e-7.
function erf(x) {
  const sign = x < 0 ? -1 : 1;
  x = Math.abs(x);
  const a1 = 0.254829592, a2 = -0.284496736, a3 = 1.421413741;
  const a4 = -1.453152027, a5 = 1.061405429, p = 0.3275911;
  const t = 1 / (1 + p * x);
  const y = 1 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * Math.exp(-x * x);
  return sign * y;
}
