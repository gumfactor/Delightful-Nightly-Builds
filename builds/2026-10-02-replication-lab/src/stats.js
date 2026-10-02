/* Statistics core for Replication Lab. Pure functions, seeded RNG, no DOM.
   Loads as a plain <script> (window.Stats) or via require() in Node tests. */
(function (root) {
  'use strict';

  // ---------- RNG ----------
  function makeRng(seed) {
    let state = (seed >>> 0) || 1;
    function uniform() {
      state = (state + 0x6d2b79f5) >>> 0;
      let t = state;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    }
    let spare = null;
    function normal() {
      if (spare !== null) {
        const value = spare;
        spare = null;
        return value;
      }
      let u = 0;
      while (u === 0) u = uniform();
      const v = uniform();
      const radius = Math.sqrt(-2 * Math.log(u));
      spare = radius * Math.sin(2 * Math.PI * v);
      return radius * Math.cos(2 * Math.PI * v);
    }
    return { uniform, normal };
  }

  // ---------- Special functions ----------
  const LANCZOS = [
    676.5203681218851, -1259.1392167224028, 771.32342877765313,
    -176.61502916214059, 12.507343278686905, -0.13857109526572012,
    9.9843695780195716e-6, 1.5056327351493116e-7,
  ];

  function lgamma(x) {
    if (x < 0.5) return Math.log(Math.PI / Math.abs(Math.sin(Math.PI * x))) - lgamma(1 - x);
    const shifted = x - 1;
    let sum = 0.99999999999980993;
    for (let i = 0; i < LANCZOS.length; i++) sum += LANCZOS[i] / (shifted + i + 1);
    const t = shifted + LANCZOS.length - 0.5;
    return 0.5 * Math.log(2 * Math.PI) + (shifted + 0.5) * Math.log(t) - t + Math.log(sum);
  }

  function betaContinuedFraction(a, b, x) {
    const tiny = 1e-30;
    let c = 1;
    let d = 1 - ((a + b) * x) / (a + 1);
    if (Math.abs(d) < tiny) d = tiny;
    d = 1 / d;
    let h = d;
    for (let m = 1; m <= 300; m++) {
      const m2 = 2 * m;
      let aa = (m * (b - m) * x) / ((a + m2 - 1) * (a + m2));
      d = 1 + aa * d;
      if (Math.abs(d) < tiny) d = tiny;
      c = 1 + aa / c;
      if (Math.abs(c) < tiny) c = tiny;
      d = 1 / d;
      h *= d * c;
      aa = (-(a + m) * (a + b + m) * x) / ((a + m2) * (a + m2 + 1));
      d = 1 + aa * d;
      if (Math.abs(d) < tiny) d = tiny;
      c = 1 + aa / c;
      if (Math.abs(c) < tiny) c = tiny;
      d = 1 / d;
      const delta = d * c;
      h *= delta;
      if (Math.abs(delta - 1) < 1e-14) break;
    }
    return h;
  }

  /** Regularised incomplete beta I_x(a, b). */
  function betaInc(a, b, x) {
    if (x <= 0) return 0;
    if (x >= 1) return 1;
    const front = Math.exp(lgamma(a + b) - lgamma(a) - lgamma(b) + a * Math.log(x) + b * Math.log(1 - x));
    if (x < (a + 1) / (a + b + 2)) return (front * betaContinuedFraction(a, b, x)) / a;
    return 1 - (front * betaContinuedFraction(b, a, 1 - x)) / b;
  }

  function normCdf(z) {
    // Chebyshev erfc fit (Numerical Recipes erfcc), fractional error below 1.2e-7.
    const x = Math.abs(z) / Math.SQRT2;
    const t = 1 / (1 + 0.5 * x);
    const tau = t * Math.exp(
      -x * x - 1.26551223 + t * (1.00002368 + t * (0.37409196 + t * (0.09678418 + t * (-0.18628806 +
      t * (0.27886807 + t * (-1.13520398 + t * (1.48851587 + t * (-0.82215223 + t * 0.17087277)))))))));
    const erfc = tau;
    return z >= 0 ? 1 - 0.5 * erfc : 0.5 * erfc;
  }

  function tCdf(t, df) {
    const tail = 0.5 * betaInc(df / 2, 0.5, df / (df + t * t));
    return t > 0 ? 1 - tail : tail;
  }

  function twoSidedP(t, df) {
    return betaInc(df / 2, 0.5, df / (df + t * t));
  }

  /** Critical |t| so that the two-sided p equals alpha. */
  function tCritical(alpha, df) {
    let lo = 0;
    let hi = 1000;
    for (let i = 0; i < 80; i++) {
      const mid = (lo + hi) / 2;
      if (twoSidedP(mid, df) > alpha) lo = mid; else hi = mid;
    }
    return (lo + hi) / 2;
  }

  function normInv(p) {
    if (p <= 0 || p >= 1) throw new RangeError('p must be in (0, 1)');
    let lo = -10;
    let hi = 10;
    for (let i = 0; i < 80; i++) {
      const mid = (lo + hi) / 2;
      if (normCdf(mid) < p) lo = mid; else hi = mid;
    }
    return (lo + hi) / 2;
  }

  // ---------- Two-sample t-test ----------
  function meanOf(values) {
    let sum = 0;
    for (let i = 0; i < values.length; i++) sum += values[i];
    return sum / values.length;
  }

  function varianceOf(values, mean) {
    let sum = 0;
    for (let i = 0; i < values.length; i++) sum += (values[i] - mean) * (values[i] - mean);
    return sum / (values.length - 1);
  }

  /** Pooled-variance two-sample t-test. Returns t, df, two-sided p and Cohen's d (treatment - control). */
  function tTest(control, treatment) {
    if (control.length < 2 || treatment.length < 2) throw new RangeError('Each group needs at least 2 observations');
    const meanC = meanOf(control);
    const meanT = meanOf(treatment);
    const varC = varianceOf(control, meanC);
    const varT = varianceOf(treatment, meanT);
    const df = control.length + treatment.length - 2;
    const pooled = ((control.length - 1) * varC + (treatment.length - 1) * varT) / df;
    const sd = Math.sqrt(pooled);
    if (sd === 0) return { t: 0, df, p: 1, d: 0 };
    const se = sd * Math.sqrt(1 / control.length + 1 / treatment.length);
    const t = (meanT - meanC) / se;
    return { t, df, p: twoSidedP(t, df), d: (meanT - meanC) / sd };
  }

  // ---------- Power ----------
  /** Normal-approximation power for a two-sample, two-sided test with n per group. */
  function analyticPower(d, n, alpha) {
    const df = 2 * n - 2;
    const crit = tCritical(alpha, df);
    const shift = d * Math.sqrt(n / 2);
    return 1 - normCdf(crit - shift) + normCdf(-crit - shift);
  }

  /** Smallest n per group whose analytic power reaches the target (null when above maxN). */
  function requiredN(d, alpha, targetPower, maxN) {
    const limit = maxN || 5000;
    if (!(d > 0)) return null;
    for (let n = 2; n <= limit; n++) {
      if (analyticPower(d, n, alpha) >= targetPower) return n;
    }
    return null;
  }

  /** Positive predictive value of a significant result given prior odds a hypothesis is true. */
  function ppv(prior, power, alpha) {
    const truePositives = power * prior;
    const falsePositives = alpha * (1 - prior);
    return truePositives + falsePositives === 0 ? 0 : truePositives / (truePositives + falsePositives);
  }

  function drawGroup(rng, n, mean) {
    const out = new Array(n);
    for (let i = 0; i < n; i++) out[i] = mean + rng.normal();
    return out;
  }

  function validate(name, value, min, max) {
    if (!Number.isFinite(value) || value < min || value > max) {
      throw new RangeError(name + ' must be between ' + min + ' and ' + max);
    }
  }

  /** Monte Carlo replication of a two-group experiment. */
  function simulateStudies(opts) {
    const { d, n, alpha, reps, seed } = opts;
    validate('n', n, 2, 5000);
    validate('alpha', alpha, 0.0001, 0.5);
    validate('reps', reps, 1, 50000);
    const rng = makeRng(seed);
    const pValues = new Array(reps);
    const effects = new Array(reps);
    let significant = 0;
    let significantPositive = 0;
    let sumSigPositive = 0;
    let sumAll = 0;
    for (let i = 0; i < reps; i++) {
      const result = tTest(drawGroup(rng, n, 0), drawGroup(rng, n, d));
      pValues[i] = result.p;
      effects[i] = result.d;
      sumAll += result.d;
      if (result.p < alpha) {
        significant++;
        if (result.d > 0) {
          significantPositive++;
          sumSigPositive += result.d;
        }
      }
    }
    return {
      pValues,
      effects,
      power: significant / reps,
      meanEffectAll: sumAll / reps,
      meanEffectSignificant: significantPositive > 0 ? sumSigPositive / significantPositive : null,
      significantCount: significant,
    };
  }

  // ---------- Optional stopping ----------
  /** Add participants in batches, testing after each batch; stop at the first p < alpha. */
  function simulatePeeking(opts) {
    const { d, nStart, step, nMax, alpha, reps, seed } = opts;
    validate('nStart', nStart, 3, 1000);
    validate('step', step, 1, 1000);
    validate('nMax', nMax, nStart, 5000);
    validate('reps', reps, 1, 50000);
    const rng = makeRng(seed);
    const looks = [];
    for (let n = nStart; n <= nMax; n += step) looks.push(n);
    const critical = looks.map((n) => tCritical(alpha, 2 * n - 2));
    const rejectedAtLook = new Array(looks.length).fill(0);
    let everRejected = 0;
    let rejectedAtFinal = 0;
    for (let rep = 0; rep < reps; rep++) {
      const control = drawGroup(rng, nMax, 0);
      const treatment = drawGroup(rng, nMax, d);
      let sumC = 0, sumT = 0, sumSqC = 0, sumSqT = 0, filled = 0;
      let rejected = false;
      let rejectedFinal = false;
      for (let li = 0; li < looks.length; li++) {
        const n = looks[li];
        for (; filled < n; filled++) {
          sumC += control[filled]; sumSqC += control[filled] * control[filled];
          sumT += treatment[filled]; sumSqT += treatment[filled] * treatment[filled];
        }
        const varC = (sumSqC - (sumC * sumC) / n) / (n - 1);
        const varT = (sumSqT - (sumT * sumT) / n) / (n - 1);
        const pooled = (varC + varT) / 2;
        const se = Math.sqrt((2 * pooled) / n);
        const t = se > 0 ? (sumT / n - sumC / n) / se : 0;
        const hit = Math.abs(t) > critical[li];
        if (hit) rejected = true;
        if (rejected) rejectedAtLook[li]++;
        if (li === looks.length - 1) rejectedFinal = hit;
      }
      if (rejected) everRejected++;
      if (rejectedFinal) rejectedAtFinal++;
    }
    return {
      looks,
      falsePositiveRate: everRejected / reps,
      fixedDesignRate: rejectedAtFinal / reps,
      cumulativeRate: rejectedAtLook.map((count) => count / reps),
    };
  }

  // ---------- Multiple outcomes ----------
  function adjustPValues(pValues, method) {
    const count = pValues.length;
    if (method === 'bonferroni') return pValues.map((p) => Math.min(1, p * count));
    if (method === 'holm') {
      const order = pValues.map((p, index) => ({ p, index })).sort((a, b) => a.p - b.p);
      const adjusted = new Array(count);
      let running = 0;
      order.forEach((entry, rank) => {
        running = Math.max(running, Math.min(1, entry.p * (count - rank)));
        adjusted[entry.index] = running;
      });
      return adjusted;
    }
    return pValues.slice();
  }

  /** k outcomes per participant (inter-correlated by rho), no true effect; report if any is significant. */
  function simulateForking(opts) {
    const { k, rho, n, alpha, reps, seed, correction } = opts;
    validate('k', k, 1, 100);
    validate('rho', rho, 0, 0.95);
    validate('n', n, 2, 1000);
    validate('reps', reps, 1, 20000);
    const rng = makeRng(seed);
    const loading = Math.sqrt(rho);
    const unique = Math.sqrt(1 - rho);
    let familywise = 0;
    let singleOutcome = 0;
    let smallestP = 0;
    for (let rep = 0; rep < reps; rep++) {
      const shared = [drawGroup(rng, n, 0), drawGroup(rng, n, 0)];
      const pValues = new Array(k);
      for (let outcome = 0; outcome < k; outcome++) {
        const groups = [0, 1].map((group) => {
          const scores = new Array(n);
          for (let i = 0; i < n; i++) scores[i] = loading * shared[group][i] + unique * rng.normal();
          return scores;
        });
        pValues[outcome] = tTest(groups[0], groups[1]).p;
      }
      if (pValues[0] < alpha) singleOutcome++;
      const adjusted = adjustPValues(pValues, correction || 'none');
      let best = 1;
      for (let i = 0; i < adjusted.length; i++) if (adjusted[i] < best) best = adjusted[i];
      smallestP += Math.min(...pValues);
      if (best < alpha) familywise++;
    }
    return {
      familywiseRate: familywise / reps,
      singleOutcomeRate: singleOutcome / reps,
      independentExpectation: 1 - Math.pow(1 - alpha, k),
      meanSmallestP: smallestP / reps,
    };
  }

  // ---------- Bayesian updating (beta-binomial) ----------
  function betaQuantile(a, b, q) {
    let lo = 0;
    let hi = 1;
    for (let i = 0; i < 70; i++) {
      const mid = (lo + hi) / 2;
      if (betaInc(a, b, mid) < q) lo = mid; else hi = mid;
    }
    return (lo + hi) / 2;
  }

  function betaPdf(a, b, x) {
    if (x <= 0 || x >= 1) return 0;
    return Math.exp(lgamma(a + b) - lgamma(a) - lgamma(b) + (a - 1) * Math.log(x) + (b - 1) * Math.log(1 - x));
  }

  /** Posterior for a success rate after k successes in n trials with a Beta(priorA, priorB) prior. */
  function betaPosterior(priorA, priorB, k, n, ropeLow, ropeHigh, credMass) {
    validate('n', n, 0, 1e6);
    if (k < 0 || k > n) throw new RangeError('k must be between 0 and n');
    const mass = credMass || 0.95;
    const a = priorA + k;
    const b = priorB + n - k;
    const tail = (1 - mass) / 2;
    const pRope = ropeLow === undefined ? null : betaInc(a, b, ropeHigh) - betaInc(a, b, ropeLow);
    return {
      a,
      b,
      mean: a / (a + b),
      interval: [betaQuantile(a, b, tail), betaQuantile(a, b, 1 - tail)],
      pRope,
    };
  }

  /** Bayes factor for H0: theta = 0.5 against H1: theta ~ Uniform(0, 1). Returns BF10. */
  function bayesFactor10(k, n) {
    const logChoose = lgamma(n + 1) - lgamma(k + 1) - lgamma(n - k + 1);
    const logBf01 = Math.log(n + 1) + logChoose + n * Math.log(0.5);
    return Math.exp(-logBf01);
  }

  function histogram(values, binCount, min, max) {
    const counts = new Array(binCount).fill(0);
    const width = (max - min) / binCount;
    for (let i = 0; i < values.length; i++) {
      const index = Math.min(binCount - 1, Math.max(0, Math.floor((values[i] - min) / width)));
      counts[index]++;
    }
    return { counts, min, max, width };
  }

  const api = {
    makeRng, lgamma, betaInc, normCdf, normInv, tCdf, twoSidedP, tCritical, tTest,
    analyticPower, requiredN, ppv, simulateStudies, simulatePeeking, simulateForking,
    adjustPValues, betaQuantile, betaPdf, betaPosterior, bayesFactor10, histogram,
  };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.Stats = api;
})(typeof window !== 'undefined' ? window : globalThis);
