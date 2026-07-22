// Beta-Binomial Bayesian inference math, plus a frequentist contrast panel.
// Pure functions only — no DOM access — so they can be exercised directly in tests.
// Algorithms: log-gamma (Lanczos), regularized incomplete beta (Numerical Recipes
// continued-fraction method), and a bisection-based quantile inversion. Cross-checked
// against an independent stdlib-only Python implementation before this file was written
// (see BUILD_LOG.md).

(function (global) {
  'use strict';

  const LANCZOS_G = 7;
  const LANCZOS_COEFFICIENTS = [
    0.99999999999980993,
    676.5203681218851,
    -1259.1392167224028,
    771.32342877765313,
    -176.61502916214059,
    12.507343278686905,
    -0.13857109526572012,
    9.9843695780195716e-6,
    1.5056327351493116e-7,
  ];

  function logGamma(x) {
    if (x < 0.5) {
      // Reflection formula for accuracy on small x.
      return Math.log(Math.PI / Math.sin(Math.PI * x)) - logGamma(1 - x);
    }
    x -= 1;
    let a = LANCZOS_COEFFICIENTS[0];
    const t = x + LANCZOS_G + 0.5;
    for (let i = 1; i < LANCZOS_G + 2; i++) {
      a += LANCZOS_COEFFICIENTS[i] / (x + i);
    }
    return 0.5 * Math.log(2 * Math.PI) + (x + 0.5) * Math.log(t) - t + Math.log(a);
  }

  function betacf(x, a, b) {
    const MAXIT = 200;
    const EPS = 3e-14;
    const FPMIN = 1e-300;
    const qab = a + b;
    const qap = a + 1.0;
    const qam = a - 1.0;
    let c = 1.0;
    let d = 1.0 - (qab * x) / qap;
    if (Math.abs(d) < FPMIN) d = FPMIN;
    d = 1.0 / d;
    let h = d;
    for (let m = 1; m <= MAXIT; m++) {
      const m2 = 2 * m;
      let aa = (m * (b - m) * x) / ((qam + m2) * (a + m2));
      d = 1.0 + aa * d;
      if (Math.abs(d) < FPMIN) d = FPMIN;
      c = 1.0 + aa / c;
      if (Math.abs(c) < FPMIN) c = FPMIN;
      d = 1.0 / d;
      h *= d * c;
      aa = (-(a + m) * (qab + m) * x) / ((a + m2) * (qap + m2));
      d = 1.0 + aa * d;
      if (Math.abs(d) < FPMIN) d = FPMIN;
      c = 1.0 + aa / c;
      if (Math.abs(c) < FPMIN) c = FPMIN;
      d = 1.0 / d;
      const de = d * c;
      h *= de;
      if (Math.abs(de - 1.0) < EPS) break;
    }
    return h;
  }

  // Regularized incomplete beta function I_x(a, b) — the Beta(a,b) CDF at x.
  function regularizedIncompleteBeta(x, a, b) {
    if (x <= 0) return 0.0;
    if (x >= 1) return 1.0;
    const lbeta = logGamma(a) + logGamma(b) - logGamma(a + b);
    const front = Math.exp(a * Math.log(x) + b * Math.log(1 - x) - lbeta) / a;
    if (x < (a + 1) / (a + b + 2)) {
      return front * betacf(x, a, b);
    }
    return 1.0 - (Math.exp(b * Math.log(1 - x) + a * Math.log(x) - lbeta) / b) * betacf(1 - x, b, a);
  }

  function betaCdf(x, a, b) {
    return regularizedIncompleteBeta(x, a, b);
  }

  function betaPdf(x, a, b) {
    if (x <= 0 || x >= 1) return 0.0;
    const lbeta = logGamma(a) + logGamma(b) - logGamma(a + b);
    return Math.exp((a - 1) * Math.log(x) + (b - 1) * Math.log(1 - x) - lbeta);
  }

  // Inverts the Beta CDF via bisection. Simple and numerically robust; no
  // derivative required, which keeps this easy to verify against reference values.
  function betaQuantile(p, a, b, tol, maxIter) {
    tol = tol === undefined ? 1e-10 : tol;
    maxIter = maxIter === undefined ? 200 : maxIter;
    if (p <= 0) return 0.0;
    if (p >= 1) return 1.0;
    let lo = 0.0;
    let hi = 1.0;
    for (let i = 0; i < maxIter; i++) {
      const mid = (lo + hi) / 2;
      if (betaCdf(mid, a, b) < p) {
        lo = mid;
      } else {
        hi = mid;
      }
      if (hi - lo < tol) break;
    }
    return (lo + hi) / 2;
  }

  function betaMean(a, b) {
    return a / (a + b);
  }

  function betaMode(a, b) {
    if (a > 1 && b > 1) return (a - 1) / (a + b - 2);
    return null; // undefined/at a boundary for a<=1 or b<=1
  }

  function betaVariance(a, b) {
    const s = a + b;
    return (a * b) / (s * s * (s + 1));
  }

  function credibleInterval(a, b, level) {
    level = level === undefined ? 0.95 : level;
    const tail = (1 - level) / 2;
    return {
      lower: betaQuantile(tail, a, b),
      upper: betaQuantile(1 - tail, a, b),
    };
  }

  function posteriorProbGreaterThan(a, b, threshold) {
    return 1 - betaCdf(threshold, a, b);
  }

  // Savage-Dickey density ratio Bayes factor at a point null p0.
  // BF01 = posterior density at p0 / prior density at p0 (evidence for the null).
  // BF10 = 1 / BF01 (evidence for the alternative/effect).
  function savageDickeyBayesFactor(priorAlpha, priorBeta, postAlpha, postBeta, p0) {
    const priorDensity = betaPdf(p0, priorAlpha, priorBeta);
    const postDensity = betaPdf(p0, postAlpha, postBeta);
    const bf01 = postDensity / priorDensity;
    const bf10 = 1 / bf01;
    return { bf01, bf10 };
  }

  // Jeffreys / Lee & Wagenmakers (2013) verbal strength-of-evidence scale.
  function bayesFactorStrengthLabel(bf10) {
    const x = bf10 >= 1 ? bf10 : 1 / bf10;
    const direction = bf10 >= 1 ? 'the effect (H1) over the null' : 'the null (H0) over the effect';
    let strength;
    if (x < 1) strength = 'no evidence either way';
    else if (x < 3) strength = 'anecdotal evidence for';
    else if (x < 10) strength = 'moderate evidence for';
    else if (x < 30) strength = 'strong evidence for';
    else if (x < 100) strength = 'very strong evidence for';
    else strength = 'extreme evidence for';
    return `${strength} ${direction}`;
  }

  function wilsonScoreInterval(successes, n, confidenceLevel) {
    confidenceLevel = confidenceLevel === undefined ? 0.95 : confidenceLevel;
    if (n === 0) return { lower: 0, upper: 1 };
    const z = normalQuantile(1 - (1 - confidenceLevel) / 2);
    const phat = successes / n;
    const denom = 1 + (z * z) / n;
    const center = phat + (z * z) / (2 * n);
    const adjust = z * Math.sqrt((phat * (1 - phat)) / n + (z * z) / (4 * n * n));
    return {
      lower: Math.max(0, (center - adjust) / denom),
      upper: Math.min(1, (center + adjust) / denom),
    };
  }

  // Acklam's algorithm for the standard normal quantile (inverse CDF).
  // Accurate to ~1.15e-9 relative error, more than sufficient for a Wilson interval.
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
    const pLow = 0.02425;
    const pHigh = 1 - pLow;
    let q, r;
    if (p < pLow) {
      q = Math.sqrt(-2 * Math.log(p));
      return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) /
        ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1);
    }
    if (p <= pHigh) {
      q = p - 0.5;
      r = q * q;
      return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q /
        (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1);
    }
    q = Math.sqrt(-2 * Math.log(1 - p));
    return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) /
      ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1);
  }

  function logBinomialCoefficient(n, k) {
    return logGamma(n + 1) - logGamma(k + 1) - logGamma(n - k + 1);
  }

  function binomialPmf(k, n, p) {
    if (p <= 0) return k === 0 ? 1.0 : 0.0;
    if (p >= 1) return k === n ? 1.0 : 0.0;
    const logC = logBinomialCoefficient(n, k);
    return Math.exp(logC + k * Math.log(p) + (n - k) * Math.log(1 - p));
  }

  // Exact two-sided binomial test p-value (point-probability-threshold method,
  // matching R's binom.test): sums the probability of every outcome no more
  // likely than the observed one, under the null p0.
  function exactBinomialTestPValue(k, n, p0) {
    if (n === 0) return 1.0;
    const pObserved = binomialPmf(k, n, p0);
    const eps = 1e-10;
    let total = 0;
    for (let i = 0; i <= n; i++) {
      const pi = binomialPmf(i, n, p0);
      if (pi <= pObserved * (1 + eps)) total += pi;
    }
    return Math.min(total, 1.0);
  }

  const BetaMath = {
    logGamma,
    betaPdf,
    betaCdf,
    betaQuantile,
    betaMean,
    betaMode,
    betaVariance,
    credibleInterval,
    posteriorProbGreaterThan,
    savageDickeyBayesFactor,
    bayesFactorStrengthLabel,
    wilsonScoreInterval,
    normalQuantile,
    binomialPmf,
    exactBinomialTestPValue,
  };

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = BetaMath;
  } else {
    global.BetaMath = BetaMath;
  }
})(typeof window !== 'undefined' ? window : globalThis);
