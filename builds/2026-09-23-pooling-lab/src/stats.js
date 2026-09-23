/*
 * Pooling Lab — statistics engine.
 *
 * Pure, DOM-free functions. No mutation of inputs. Attaches everything to
 * window.PoolingStats so both the app and the Playwright tests can call the
 * exact same code path (tests load this file via addScriptTag).
 */
(function (global) {
  'use strict';

  // ---- Seeded PRNG (mulberry32) — deterministic, reproducible per seed ----
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

  // Box-Muller transform using the supplied uniform RNG, so every draw is
  // reproducible for a given seed.
  function makeGaussianSampler(rng) {
    let spare = null;
    return function (mean, sd) {
      if (spare !== null) {
        const z = spare;
        spare = null;
        return mean + sd * z;
      }
      let u1 = 0;
      let u2 = 0;
      // Avoid log(0).
      while (u1 <= Number.EPSILON) {
        u1 = rng();
      }
      u2 = rng();
      const r = Math.sqrt(-2 * Math.log(u1));
      const theta = 2 * Math.PI * u2;
      spare = r * Math.sin(theta);
      return mean + sd * r * Math.cos(theta);
    };
  }

  /**
   * Generate a synthetic nested dataset.
   *
   * @param {Object} params
   * @param {number} params.seed - integer seed; same seed => identical dataset.
   * @param {number} params.groupCount - number of groups G.
   * @param {number[]} params.groupSizes - length-G array of per-group sample sizes.
   * @param {number} params.tau2 - true between-group variance.
   * @param {number} params.sigma2 - true within-group (residual) variance.
   * @param {number} [params.grandMeanTrue=50] - population mean used to generate group means.
   * @returns {{seed:number, tau2:number, sigma2:number, grandMeanTrue:number, groups:Array}}
   */
  function generateNestedData(params) {
    const {
      seed,
      groupCount,
      groupSizes,
      tau2,
      sigma2,
      grandMeanTrue = 50,
    } = params;

    if (!Array.isArray(groupSizes) || groupSizes.length !== groupCount) {
      throw new Error('groupSizes must have length groupCount');
    }

    const rng = mulberry32(seed);
    const gaussian = makeGaussianSampler(rng);
    const tauSd = Math.sqrt(Math.max(tau2, 0));
    const sigmaSd = Math.sqrt(Math.max(sigma2, 0));

    const groups = [];
    for (let g = 0; g < groupCount; g++) {
      const n = groupSizes[g];
      const trueMean = tauSd === 0 ? grandMeanTrue : gaussian(grandMeanTrue, tauSd);
      const observations = [];
      for (let i = 0; i < n; i++) {
        const value = sigmaSd === 0 ? trueMean : gaussian(trueMean, sigmaSd);
        observations.push(value);
      }
      groups.push({ id: g, n, trueMean, observations });
    }

    return { seed, tau2, sigma2, grandMeanTrue, groups };
  }

  function mean(values) {
    if (values.length === 0) return NaN;
    let sum = 0;
    for (let i = 0; i < values.length; i++) sum += values[i];
    return sum / values.length;
  }

  function computeGroupMeans(dataset) {
    return dataset.groups.map((g) => ({ id: g.id, n: g.n, groupMean: mean(g.observations) }));
  }

  /** Size-weighted grand mean across all observations (the "complete pooling" estimate). */
  function computeGrandMean(dataset) {
    let total = 0;
    let count = 0;
    for (const g of dataset.groups) {
      for (const v of g.observations) {
        total += v;
        count += 1;
      }
    }
    if (count === 0) return NaN;
    return total / count;
  }

  /** True ICC from the generating parameters: tau2 / (tau2 + sigma2). */
  function computeTrueICC(tau2, sigma2) {
    if (tau2 <= 0) return 0;
    if (sigma2 <= 0) return 1;
    return tau2 / (tau2 + sigma2);
  }

  /**
   * Empirical ICC estimated from the sample via a one-way random-effects
   * ANOVA variance decomposition (the standard method-of-moments estimator).
   * Returns null when there are fewer than 2 groups (ICC is not computable).
   */
  function computeEmpiricalICC(dataset) {
    const groups = dataset.groups.filter((g) => g.n > 0);
    const k = groups.length;
    if (k < 2) return null;

    const totalN = groups.reduce((s, g) => s + g.n, 0);
    const grand = computeGrandMean(dataset);

    let ssBetween = 0;
    let ssWithin = 0;
    for (const g of groups) {
      const gMean = mean(g.observations);
      ssBetween += g.n * Math.pow(gMean - grand, 2);
      for (const v of g.observations) {
        ssWithin += Math.pow(v - gMean, 2);
      }
    }

    const dfBetween = k - 1;
    const dfWithin = totalN - k;
    if (dfWithin <= 0) return null;

    const msBetween = ssBetween / dfBetween;
    const msWithin = ssWithin / dfWithin;

    // Average group size (harmonic-mean-style correction, standard ANOVA ICC formula).
    const nBar =
      (totalN - groups.reduce((s, g) => s + g.n * g.n, 0) / totalN) / dfBetween;

    if (nBar <= 0) return null;

    const tau2Hat = Math.max((msBetween - msWithin) / nBar, 0);
    const sigma2Hat = Math.max(msWithin, 0);
    if (tau2Hat + sigma2Hat === 0) return 0;
    return tau2Hat / (tau2Hat + sigma2Hat);
  }

  /**
   * Empirical-Bayes shrinkage weight for a group: how much its own mean is
   * trusted vs. pulled toward the grand mean. weight -> 1 as n -> infinity or
   * tau2 >> sigma2; weight -> 0 as n -> 0 or tau2 -> 0.
   */
  function computeShrinkageWeight(tau2, sigma2, n) {
    if (n <= 0) return 0;
    if (tau2 <= 0) return 0;
    if (sigma2 <= 0) return 1;
    return tau2 / (tau2 + sigma2 / n);
  }

  /**
   * Full per-group summary: no-pooling, complete-pooling, and partial-pooling
   * (shrinkage) estimates, plus the shrinkage weight used.
   */
  function computePoolingSummary(dataset) {
    const grandMean = computeGrandMean(dataset);
    const trueICC = computeTrueICC(dataset.tau2, dataset.sigma2);
    const empiricalICC = computeEmpiricalICC(dataset);

    const perGroup = dataset.groups.map((g) => {
      const noPooling = mean(g.observations);
      const shrinkageWeight = computeShrinkageWeight(dataset.tau2, dataset.sigma2, g.n);
      const partialPooling = Number.isNaN(noPooling)
        ? grandMean
        : shrinkageWeight * noPooling + (1 - shrinkageWeight) * grandMean;
      return {
        id: g.id,
        n: g.n,
        noPooling,
        completePooling: grandMean,
        shrinkageWeight,
        partialPooling,
      };
    });

    return { grandMean, trueICC, empiricalICC, perGroup };
  }

  global.PoolingStats = {
    mulberry32,
    makeGaussianSampler,
    generateNestedData,
    computeGroupMeans,
    computeGrandMean,
    computeTrueICC,
    computeEmpiricalICC,
    computeShrinkageWeight,
    computePoolingSummary,
  };
})(typeof window !== 'undefined' ? window : globalThis);
