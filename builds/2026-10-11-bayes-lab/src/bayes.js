/* Bayes Lab numeric core. Exposes window.Bayes (and module.exports under Node). */
(function (root) {
  'use strict';

  const LANCZOS = [
    676.5203681218851, -1259.1392167224028, 771.32342877765313,
    -176.61502916214059, 12.507343278686905, -0.13857109526572012,
    9.9843695780195716e-6, 1.5056327351493116e-7,
  ];

  function logGamma(x) {
    if (!(x > 0)) return NaN;
    if (x < 0.5) return Math.log(Math.PI / Math.sin(Math.PI * x)) - logGamma(1 - x);
    const z = x - 1;
    let sum = 0.99999999999980993;
    for (let i = 0; i < LANCZOS.length; i++) sum += LANCZOS[i] / (z + i + 1);
    const t = z + LANCZOS.length - 0.5;
    return 0.5 * Math.log(2 * Math.PI) + (z + 0.5) * Math.log(t) - t + Math.log(sum);
  }

  function logBeta(a, b) { return logGamma(a) + logGamma(b) - logGamma(a + b); }

  function logChoose(n, k) {
    return logGamma(n + 1) - logGamma(k + 1) - logGamma(n - k + 1);
  }

  function betaPdf(x, a, b) {
    if (x < 0 || x > 1) return 0;
    if (x === 0) return a < 1 ? Infinity : a === 1 ? b : 0;
    if (x === 1) return b < 1 ? Infinity : b === 1 ? a : 0;
    return Math.exp((a - 1) * Math.log(x) + (b - 1) * Math.log(1 - x) - logBeta(a, b));
  }

  function betaCF(x, a, b) {
    const TINY = 1e-300;
    let c = 1;
    let d = 1 - ((a + b) * x) / (a + 1);
    if (Math.abs(d) < TINY) d = TINY;
    d = 1 / d;
    let h = d;
    for (let m = 1; m <= 500; m++) {
      const m2 = 2 * m;
      let aa = (m * (b - m) * x) / ((a + m2 - 1) * (a + m2));
      d = 1 + aa * d; if (Math.abs(d) < TINY) d = TINY;
      c = 1 + aa / c; if (Math.abs(c) < TINY) c = TINY;
      d = 1 / d; h *= d * c;
      aa = (-(a + m) * (a + b + m) * x) / ((a + m2) * (a + m2 + 1));
      d = 1 + aa * d; if (Math.abs(d) < TINY) d = TINY;
      c = 1 + aa / c; if (Math.abs(c) < TINY) c = TINY;
      d = 1 / d;
      const delta = d * c;
      h *= delta;
      if (Math.abs(delta - 1) < 1e-14) break;
    }
    return h;
  }

  /** Regularized incomplete beta = Beta(a,b) CDF. */
  function betaCdf(x, a, b) {
    if (x <= 0) return 0;
    if (x >= 1) return 1;
    const front = Math.exp(a * Math.log(x) + b * Math.log(1 - x) - logBeta(a, b));
    if (x < (a + 1) / (a + b + 2)) return (front * betaCF(x, a, b)) / a;
    return 1 - (front * betaCF(1 - x, b, a)) / b;
  }

  function betaQuantile(p, a, b) {
    if (p <= 0) return 0;
    if (p >= 1) return 1;
    let lo = 0;
    let hi = 1;
    for (let i = 0; i < 100; i++) {
      const mid = (lo + hi) / 2;
      if (betaCdf(mid, a, b) < p) lo = mid; else hi = mid;
    }
    return (lo + hi) / 2;
  }

  const betaMean = (a, b) => a / (a + b);
  const betaSd = (a, b) => Math.sqrt((a * b) / ((a + b) * (a + b) * (a + b + 1)));

  /** Highest-density interval of a Beta(a,b). Falls back to equal-tailed when U-shaped. */
  function betaHDI(a, b, mass = 0.95) {
    const tail = 1 - mass;
    if (a > 1 && b > 1) {
      let lo = 0;
      let hi = tail;
      const width = (p) => betaQuantile(p + mass, a, b) - betaQuantile(p, a, b);
      for (let i = 0; i < 80; i++) {
        const m1 = lo + (hi - lo) / 3;
        const m2 = hi - (hi - lo) / 3;
        if (width(m1) < width(m2)) hi = m2; else lo = m1;
      }
      const p = (lo + hi) / 2;
      return [betaQuantile(p, a, b), betaQuantile(p + mass, a, b)];
    }
    if (a <= 1 && b > 1) return [0, betaQuantile(mass, a, b)];
    if (b <= 1 && a > 1) return [betaQuantile(tail, a, b), 1];
    return [betaQuantile(tail / 2, a, b), betaQuantile(1 - tail / 2, a, b)];
  }

  /** Conjugate update: k successes in n trials. */
  function betaBinomialUpdate(a, b, k, n) {
    return { a: a + k, b: b + (n - k) };
  }

  /** P(lo < theta < hi) under Beta(a,b), e.g. a region of practical equivalence. */
  function ropeProbability(a, b, lo, hi) {
    return betaCdf(Math.max(lo, hi), a, b) - betaCdf(Math.min(lo, hi), a, b);
  }

  function logBinomPmf(k, n, p) {
    if (p <= 0) return k === 0 ? 0 : -Infinity;
    if (p >= 1) return k === n ? 0 : -Infinity;
    return logChoose(n, k) + k * Math.log(p) + (n - k) * Math.log(1 - p);
  }

  /** Beta-binomial pmf: probability of m successes in M future trials under Beta(a,b). */
  function predictivePmf(a, b, M) {
    const out = [];
    for (let m = 0; m <= M; m++) {
      out.push(Math.exp(logChoose(M, m) + logBeta(m + a, M - m + b) - logBeta(a, b)));
    }
    return out;
  }

  /** Exact two-sided binomial p-value (sum of outcomes no more likely than observed). */
  function binomialPValue(k, n, p0 = 0.5) {
    if (n === 0) return 1;
    const observed = logBinomPmf(k, n, p0);
    let total = 0;
    for (let i = 0; i <= n; i++) {
      const lp = logBinomPmf(i, n, p0);
      if (lp <= observed + 1e-9) total += Math.exp(lp);
    }
    return Math.min(1, total);
  }

  /** BF10 for H1: theta ~ Beta(a,b) against point null H0: theta = theta0. */
  function bayesFactor10(k, n, a, b, theta0 = 0.5) {
    const logMarginal = logChoose(n, k) + logBeta(k + a, n - k + b) - logBeta(a, b);
    return Math.exp(logMarginal - logBinomPmf(k, n, theta0));
  }

  /** Same quantity via Savage-Dickey: BF01 = posterior density / prior density at theta0. */
  function bayesFactor01SavageDickey(k, n, a, b, theta0 = 0.5) {
    return betaPdf(theta0, a + k, b + n - k) / betaPdf(theta0, a, b);
  }

  /** Lee & Wagenmakers (2013) verbal labels for BF10. */
  function bayesFactorLabel(bf10) {
    const strength = bf10 >= 1 ? bf10 : 1 / bf10;
    const side = bf10 >= 1 ? 'the alternative' : 'the null';
    if (strength < 1.0001 || strength < 1.5) return 'Anecdotal / no real preference';
    let word;
    if (strength < 3) word = 'Anecdotal';
    else if (strength < 10) word = 'Moderate';
    else if (strength < 30) word = 'Strong';
    else if (strength < 100) word = 'Very strong';
    else word = 'Extreme';
    return `${word} evidence for ${side}`;
  }

  /** Diagnostic Bayes: P(condition | positive) and friends. */
  function diagnostic(prevalence, sensitivity, specificity) {
    const tp = prevalence * sensitivity;
    const fn = prevalence * (1 - sensitivity);
    const fp = (1 - prevalence) * (1 - specificity);
    const tn = (1 - prevalence) * specificity;
    const positive = tp + fp;
    const negative = fn + tn;
    return {
      ppv: positive > 0 ? tp / positive : NaN,
      npv: negative > 0 ? tn / negative : NaN,
      pPositive: positive,
    };
  }

  /** Natural-frequency counts for a population; rounding remainder goes to true negatives. */
  function naturalFrequencies(prevalence, sensitivity, specificity, population = 1000) {
    const diseased = Math.round(population * prevalence);
    const tp = Math.round(diseased * sensitivity);
    const fn = diseased - tp;
    const healthy = population - diseased;
    const fp = Math.round(healthy * (1 - specificity));
    const tn = healthy - fp;
    return { tp, fn, fp, tn };
  }

  /** Normal-normal conjugate update with known standard error of the estimate. */
  function normalUpdate(priorMean, priorSd, estimate, se) {
    const priorPrecision = 1 / (priorSd * priorSd);
    const dataPrecision = 1 / (se * se);
    const total = priorPrecision + dataPrecision;
    return {
      mean: (priorMean * priorPrecision + estimate * dataPrecision) / total,
      sd: Math.sqrt(1 / total),
      dataWeight: dataPrecision / total,
    };
  }

  const normalPdf = (x, mean, sd) =>
    Math.exp(-0.5 * ((x - mean) / sd) ** 2) / (sd * Math.sqrt(2 * Math.PI));

  /** Brier score for [{p, outcome}] where p is probability assigned to "true". */
  function brierScore(items) {
    if (!items.length) return NaN;
    return items.reduce((sum, it) => sum + (it.p - (it.outcome ? 1 : 0)) ** 2, 0) / items.length;
  }

  const api = {
    logGamma, logBeta, logChoose, betaPdf, betaCdf, betaQuantile, betaMean, betaSd, betaHDI,
    betaBinomialUpdate, ropeProbability, predictivePmf, binomialPValue, bayesFactor10,
    bayesFactor01SavageDickey, bayesFactorLabel, diagnostic, naturalFrequencies, normalUpdate,
    normalPdf, brierScore,
  };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  root.Bayes = api;
})(typeof window !== 'undefined' ? window : globalThis);
