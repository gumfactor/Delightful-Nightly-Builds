// Signal Detection Theory math, equal-variance Gaussian model.
// Pure functions only — no DOM access — so they can be exercised directly in tests
// and shared identically between every UI tab.
//
// References: Green & Swets (1966) Signal Detection Theory and Psychophysics;
// Hautus (1995) loglinear correction for extreme rates; Pollack & Norman (1964)
// and Donaldson (1992) for the nonparametric A'/B'' measures. normalQuantile uses
// Peter Acklam's rational approximation plus one Halley refinement step.

(function (global) {
  'use strict';

  // ---------- Standard normal distribution ----------

  // Abramowitz & Stegun 7.1.26 approximation to erf. Max absolute error ~1.5e-7.
  function erf(x) {
    const sign = x < 0 ? -1 : 1;
    x = Math.abs(x);
    const a1 = 0.254829592;
    const a2 = -0.284496736;
    const a3 = 1.421413741;
    const a4 = -1.453152027;
    const a5 = 1.061405429;
    const p = 0.3275911;
    const t = 1 / (1 + p * x);
    const y = 1 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * Math.exp(-x * x);
    return sign * y;
  }

  function normalPdf(z) {
    return Math.exp(-0.5 * z * z) / Math.sqrt(2 * Math.PI);
  }

  function normalCdf(z) {
    return 0.5 * (1 + erf(z / Math.SQRT2));
  }

  // Inverse standard normal CDF (probit function). Peter Acklam's algorithm,
  // refined with one step of Halley's rational method.
  function normalQuantile(p) {
    if (!(p > 0) || !(p < 1)) {
      if (p === 0) return -Infinity;
      if (p === 1) return Infinity;
      throw new RangeError('normalQuantile: p must be in (0, 1), got ' + p);
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
      7.784695709041462e-3, 3.224671290700398e-1, 2.445134137142996e0, 3.754408661907416e0,
    ];

    const pLow = 0.02425;
    const pHigh = 1 - pLow;
    let x;

    if (p < pLow) {
      const q = Math.sqrt(-2 * Math.log(p));
      x = (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) /
          ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1);
    } else if (p <= pHigh) {
      const q = p - 0.5;
      const r = q * q;
      x = (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q /
          (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1);
    } else {
      const q = Math.sqrt(-2 * Math.log(1 - p));
      x = -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) /
          ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1);
    }

    // One step of Halley's method to refine against our own normalCdf/normalPdf.
    const e = normalCdf(x) - p;
    const u = e * Math.sqrt(2 * Math.PI) * Math.exp((x * x) / 2);
    x = x - u / (1 + (x * u) / 2);
    return x;
  }

  // ---------- Rate handling ----------

  function clamp(x, lo, hi) {
    return Math.max(lo, Math.min(hi, x));
  }

  // Converts raw hit/miss/false-alarm/correct-rejection counts into rates.
  // With correction 'loglinear' (default, per Hautus 1995): adds 0.5 to hits and
  // false alarms, 1 to each N — avoids undefined z-scores at 0% or 100% rates.
  // With correction 'none': rates are computed directly and clamped away from
  // the exact 0/1 boundary only enough to keep normalQuantile finite.
  function ratesFromCounts(hits, misses, falseAlarms, correctRejections, options) {
    const correction = (options && options.correction) || 'loglinear';
    const nSignal = hits + misses;
    const nNoise = falseAlarms + correctRejections;
    if (nSignal <= 0 || nNoise <= 0) {
      throw new RangeError('ratesFromCounts: signal and noise trial counts must both be > 0');
    }

    let hitRate;
    let faRate;
    if (correction === 'loglinear') {
      hitRate = (hits + 0.5) / (nSignal + 1);
      faRate = (falseAlarms + 0.5) / (nNoise + 1);
    } else {
      const eps = 1e-6;
      hitRate = clamp(hits / nSignal, eps, 1 - eps);
      faRate = clamp(falseAlarms / nNoise, eps, 1 - eps);
    }
    return { hitRate, faRate, nSignal, nNoise };
  }

  // ---------- Core SDT measures ----------

  function dPrime(hitRate, faRate) {
    return normalQuantile(hitRate) - normalQuantile(faRate);
  }

  function criterionC(hitRate, faRate) {
    return -0.5 * (normalQuantile(hitRate) + normalQuantile(faRate));
  }

  // Likelihood-ratio criterion measure beta = f_signal(k) / f_noise(k) at the
  // observed criterion. exp((zFA^2 - zH^2) / 2) is the closed form under the
  // equal-variance Gaussian model.
  function likelihoodRatioBeta(hitRate, faRate) {
    const zH = normalQuantile(hitRate);
    const zFA = normalQuantile(faRate);
    return Math.exp((zFA * zFA - zH * zH) / 2);
  }

  // Nonparametric sensitivity (Pollack & Norman, 1964 / Grier, 1971 form).
  function aPrime(hitRate, faRate) {
    if (hitRate >= faRate) {
      return 0.5 + ((hitRate - faRate) * (1 + hitRate - faRate)) / (4 * hitRate * (1 - faRate));
    }
    return 0.5 - ((faRate - hitRate) * (1 + faRate - hitRate)) / (4 * faRate * (1 - hitRate));
  }

  // Nonparametric bias (Donaldson, 1992). Positive = conservative, negative = liberal,
  // 0 at the unbiased point (hitRate + faRate == 1).
  function bDoublePrime(hitRate, faRate) {
    const hTerm = hitRate * (1 - hitRate);
    const fTerm = faRate * (1 - faRate);
    if (hitRate >= faRate) {
      return (hTerm - fTerm) / (hTerm + fTerm || 1e-12);
    }
    return (fTerm - hTerm) / (hTerm + fTerm || 1e-12);
  }

  // ---------- ROC curve ----------

  // Traces the ROC curve for a fixed d' by sweeping the decision criterion k.
  // Under the equal-variance model with noise ~ N(0,1) and signal ~ N(d',1):
  //   hitRate(k) = 1 - Phi(k - d'),  faRate(k) = 1 - Phi(k)
  // Returns points sorted by ascending false-alarm rate, including exact (0,0)
  // and (1,1) endpoints.
  function rocCurve(dPrimeValue, numPoints) {
    const n = numPoints || 41;
    const points = [{ fa: 0, hit: 0 }];
    for (let i = 1; i < n - 1; i++) {
      const k = 4 - (8 * i) / (n - 1); // sweep k from ~4 down to ~-4
      const fa = 1 - normalCdf(k);
      const hit = 1 - normalCdf(k - dPrimeValue);
      points.push({ fa: clamp(fa, 0, 1), hit: clamp(hit, 0, 1) });
    }
    points.push({ fa: 1, hit: 1 });
    points.sort((p, q) => p.fa - q.fa);
    return points;
  }

  // Closed-form area under the equal-variance Gaussian ROC curve.
  function rocAuc(dPrimeValue) {
    return normalCdf(dPrimeValue / Math.SQRT2);
  }

  // Trapezoidal numeric integration of a rocCurve — used as an independent
  // cross-check against the closed-form rocAuc in tests.
  function rocAucNumeric(points) {
    let area = 0;
    for (let i = 1; i < points.length; i++) {
      const dx = points[i].fa - points[i - 1].fa;
      const avgY = (points[i].hit + points[i - 1].hit) / 2;
      area += dx * avgY;
    }
    return area;
  }

  // ---------- Interpretation helpers ----------

  const D_PRIME_BUCKETS = [
    { max: 0.5, label: 'poor' },
    { max: 1.0, label: 'weak' },
    { max: 2.0, label: 'moderate' },
    { max: 3.0, label: 'good' },
    { max: Infinity, label: 'excellent' },
  ];

  function dPrimeBucket(dPrimeValue) {
    const magnitude = Math.abs(dPrimeValue);
    for (const bucket of D_PRIME_BUCKETS) {
      if (magnitude < bucket.max) return bucket.label;
    }
    return 'excellent';
  }

  const CRITERION_TOLERANCE = 0.15;

  function criterionLabel(c) {
    if (c > CRITERION_TOLERANCE) return 'conservative';
    if (c < -CRITERION_TOLERANCE) return 'liberal';
    return 'neutral';
  }

  const SdtMath = {
    erf,
    normalPdf,
    normalCdf,
    normalQuantile,
    ratesFromCounts,
    dPrime,
    criterionC,
    likelihoodRatioBeta,
    aPrime,
    bDoublePrime,
    rocCurve,
    rocAuc,
    rocAucNumeric,
    dPrimeBucket,
    criterionLabel,
    D_PRIME_BUCKETS,
    CRITERION_TOLERANCE,
  };

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = SdtMath;
  } else {
    global.SdtMath = SdtMath;
  }
})(typeof window !== 'undefined' ? window : globalThis);
