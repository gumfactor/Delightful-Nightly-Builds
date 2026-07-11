// Core statistical power math. Pure functions, no DOM/state dependencies.
//
// Power and required-N are computed with a normal approximation to the
// noncentral-t distribution (the same approximation behind quick power
// calculators and Cohen's original tables). It is accurate to within
// roughly 1-3 percentage points of exact noncentral-t values for n >= 20
// per group -- good for planning and teaching, not a substitute for exact
// software (G*Power, R's `pwr` package) when a document requires exact
// figures.
//
// Loaded as a classic (non-module) script -- see charts.js for why -- so
// the whole file is wrapped in an IIFE. Top-level let/const in separate
// classic <script> tags on the same page share one global lexical scope,
// so without this wrapper a name declared here could collide with a same-
// named declaration in another file loaded on the same page.
(function () {

const ERF_A1 = 0.254829592;
const ERF_A2 = -0.284496736;
const ERF_A3 = 1.421413741;
const ERF_A4 = -1.453152027;
const ERF_A5 = 1.061405429;
const ERF_P = 0.3275911;

function erf(x) {
  const sign = x < 0 ? -1 : 1;
  const ax = Math.abs(x);
  const t = 1 / (1 + ERF_P * ax);
  const y =
    1 -
    ((((ERF_A5 * t + ERF_A4) * t + ERF_A3) * t + ERF_A2) * t + ERF_A1) *
      t *
      Math.exp(-ax * ax);
  return sign * y;
}

// Standard normal CDF, Phi(x).
function normalCDF(x) {
  return 0.5 * (1 + erf(x / Math.SQRT2));
}

// Standard normal quantile function (inverse CDF / probit), Acklam's
// rational approximation. Accurate to ~1.15e-9 for p in (0, 1).
function invNormalCDF(p) {
  if (!(p > 0 && p < 1)) {
    throw new RangeError('invNormalCDF: p must be strictly between 0 and 1');
  }

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

  const pLow = 0.02425;
  const pHigh = 1 - pLow;

  let q, r;
  if (p < pLow) {
    q = Math.sqrt(-2 * Math.log(p));
    return (
      (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) /
      ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    );
  } else if (p <= pHigh) {
    q = p - 0.5;
    r = q * q;
    return (
      ((((( a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) *
      q /
      (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)
    );
  } else {
    q = Math.sqrt(-2 * Math.log(1 - p));
    return (
      -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) /
      ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    );
  }
}

const TEST_TYPES = Object.freeze({
  TWO_SAMPLE: 'two-sample',
  ONE_SAMPLE: 'one-sample',
});

// Returns the divisor factor applied to n inside the sqrt term of the
// power formula: two independent equal-n groups split the variance,
// one-sample/paired designs do not.
function nFactor(testType) {
  if (testType === TEST_TYPES.TWO_SAMPLE) return 2;
  if (testType === TEST_TYPES.ONE_SAMPLE) return 1;
  throw new RangeError(`Unknown testType: ${testType}`);
}

function criticalZ(alpha, tails) {
  if (!(alpha > 0 && alpha < 1)) {
    throw new RangeError('alpha must be strictly between 0 and 1');
  }
  const tailAlpha = tails === 'one' ? alpha : alpha / 2;
  return invNormalCDF(1 - tailAlpha);
}

// computePower({ d, n, alpha, testType, tails }) -> power in [0, 1]
//
// For a two-tailed test, power is the probability of landing in *either*
// rejection tail: normalCDF(ncp - zAlpha) + normalCDF(-ncp - zAlpha). The
// second term is negligible for realistic effect sizes but matters at the
// d=0 boundary, where a correct formula must reduce to exactly alpha (both
// tails contribute alpha/2 each) rather than alpha/2 from a single tail.
function computePower({ d, n, alpha, testType, tails = 'two' }) {
  if (n <= 0) throw new RangeError('n must be positive');
  const zAlpha = criticalZ(alpha, tails);
  const ncp = d * Math.sqrt(n / nFactor(testType));
  if (tails === 'one') {
    return normalCDF(ncp - zAlpha);
  }
  return normalCDF(ncp - zAlpha) + normalCDF(-ncp - zAlpha);
}

// computeRequiredN({ d, power, alpha, testType, tails }) -> ceil(n) per group
function computeRequiredN({ d, power, alpha, testType, tails = 'two' }) {
  if (!(power > 0 && power < 1)) {
    throw new RangeError('power must be strictly between 0 and 1');
  }
  if (d === 0) {
    throw new RangeError('d must be nonzero to solve for a finite sample size');
  }
  const zAlpha = criticalZ(alpha, tails);
  const zBeta = invNormalCDF(power);
  const n = (nFactor(testType) * Math.pow(zAlpha + zBeta, 2)) / (d * d);
  return Math.ceil(n);
}

function powerLabel(power) {
  if (power < 0.5) return 'severely underpowered';
  if (power < 0.7) return 'underpowered';
  if (power < 0.9) return 'adequate';
  return 'well-powered';
}

function effectSizeLabel(d) {
  const ad = Math.abs(d);
  if (ad < 0.2) return 'negligible';
  if (ad < 0.5) return 'small';
  if (ad < 0.8) return 'medium';
  return 'large';
}

// Cohen's d <-> Pearson's r, exact for equal-n groups.
function dToR(d) {
  return d / Math.sqrt(d * d + 4);
}

function rToD(r) {
  if (Math.abs(r) >= 1) {
    throw new RangeError('r must satisfy |r| < 1');
  }
  return (2 * r) / Math.sqrt(1 - r * r);
}

// t-statistic + sample size -> Cohen's d.
// For two-sample equal-n designs, n is per group and the standard error
// factor is sqrt(2/n); for one-sample/paired designs it is sqrt(1/n).
function tToD({ t, n, testType }) {
  if (n <= 0) throw new RangeError('n must be positive');
  const factor = testType === TEST_TYPES.TWO_SAMPLE ? Math.sqrt(2 / n) : Math.sqrt(1 / n);
  return t * factor;
}

window.PowerLabStats = {
  normalCDF,
  invNormalCDF,
  computePower,
  computeRequiredN,
  powerLabel,
  effectSizeLabel,
  dToR,
  rToD,
  tToD,
  TEST_TYPES,
};

})();
