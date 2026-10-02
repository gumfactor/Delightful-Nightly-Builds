const { test, expect } = require('@playwright/test');
const S = require('../src/stats.js');

test.describe('special functions', () => {
  test('normCdf matches known values', () => {
    expect(S.normCdf(0)).toBeCloseTo(0.5, 6);
    expect(S.normCdf(1.96)).toBeCloseTo(0.975, 3);
    expect(S.normCdf(-1.96)).toBeCloseTo(0.025, 3);
  });

  test('normInv inverts normCdf', () => {
    expect(S.normInv(0.975)).toBeCloseTo(1.96, 2);
    expect(() => S.normInv(1)).toThrow(RangeError);
  });

  test('two-sided t p-value matches tables (t=2.228, df=10 -> .05)', () => {
    expect(S.twoSidedP(2.228, 10)).toBeCloseTo(0.05, 3);
    expect(S.twoSidedP(0, 20)).toBeCloseTo(1, 10);
  });

  test('tCritical gives 2.086 for df=20 and approaches 1.96 for large df', () => {
    expect(S.tCritical(0.05, 20)).toBeCloseTo(2.086, 3);
    expect(S.tCritical(0.05, 5000)).toBeCloseTo(1.96, 2);
  });

  test('betaInc is symmetric: I_x(a,b) = 1 - I_(1-x)(b,a)', () => {
    expect(S.betaInc(2, 5, 0.3)).toBeCloseTo(1 - S.betaInc(5, 2, 0.7), 10);
    expect(S.betaInc(1, 1, 0.37)).toBeCloseTo(0.37, 10);
  });
});

test.describe('t-test', () => {
  test('known small example', () => {
    const result = S.tTest([1, 2, 3, 4, 5], [3, 4, 5, 6, 7]);
    expect(result.df).toBe(8);
    expect(result.t).toBeCloseTo(2, 6);
    expect(result.p).toBeCloseTo(0.0805, 3);
    expect(result.d).toBeCloseTo(1.265, 3);
  });

  test('identical constant groups return p = 1 instead of NaN', () => {
    expect(S.tTest([2, 2, 2], [2, 2, 2]).p).toBe(1);
  });

  test('rejects groups with fewer than two observations', () => {
    expect(() => S.tTest([1], [1, 2])).toThrow(RangeError);
  });
});

test.describe('rng', () => {
  test('same seed gives the same stream, different seed differs', () => {
    const a = S.makeRng(7), b = S.makeRng(7), c = S.makeRng(8);
    expect(a.normal()).toBe(b.normal());
    expect(a.uniform()).toBe(b.uniform());
    expect(S.makeRng(7).normal()).not.toBe(c.normal());
  });

  test('normal draws have mean ~0 and sd ~1', () => {
    const rng = S.makeRng(1);
    const draws = Array.from({ length: 20000 }, () => rng.normal());
    const mean = draws.reduce((s, v) => s + v, 0) / draws.length;
    const variance = draws.reduce((s, v) => s + (v - mean) ** 2, 0) / draws.length;
    expect(Math.abs(mean)).toBeLessThan(0.03);
    expect(variance).toBeCloseTo(1, 1);
  });
});

test.describe('power', () => {
  test('analytic power at d=0.5, n=64 per group is about 0.80', () => {
    expect(S.analyticPower(0.5, 64, 0.05)).toBeGreaterThan(0.78);
    expect(S.analyticPower(0.5, 64, 0.05)).toBeLessThan(0.83);
  });

  test('requiredN reproduces the textbook 64-ish per group for d=0.5', () => {
    const n = S.requiredN(0.5, 0.05, 0.8);
    expect(n).toBeGreaterThanOrEqual(63);
    expect(n).toBeLessThanOrEqual(66);
  });

  test('requiredN returns null for a zero effect or an unreachable target', () => {
    expect(S.requiredN(0, 0.05, 0.8)).toBeNull();
    expect(S.requiredN(0.01, 0.05, 0.8, 100)).toBeNull();
  });

  test('simulated power agrees with analytic power', () => {
    const sim = S.simulateStudies({ d: 0.5, n: 30, alpha: 0.05, reps: 3000, seed: 11 });
    expect(Math.abs(sim.power - S.analyticPower(0.5, 30, 0.05))).toBeLessThan(0.035);
  });

  test('under the null, about alpha of studies are significant and p is uniform', () => {
    const sim = S.simulateStudies({ d: 0, n: 20, alpha: 0.05, reps: 4000, seed: 3 });
    expect(Math.abs(sim.power - 0.05)).toBeLessThan(0.017);
    const below = sim.pValues.filter((p) => p < 0.5).length / sim.pValues.length;
    expect(Math.abs(below - 0.5)).toBeLessThan(0.03);
  });

  test('winner\'s curse: significant studies overstate a true small effect at low power', () => {
    const sim = S.simulateStudies({ d: 0.3, n: 20, alpha: 0.05, reps: 4000, seed: 5 });
    expect(Math.abs(sim.meanEffectAll - 0.3)).toBeLessThan(0.03);
    expect(sim.meanEffectSignificant).toBeGreaterThan(0.6);
  });

  test('simulation rejects out-of-range inputs', () => {
    expect(() => S.simulateStudies({ d: 0, n: 1, alpha: 0.05, reps: 10, seed: 1 })).toThrow(RangeError);
    expect(() => S.simulateStudies({ d: 0, n: 10, alpha: 0.05, reps: 0, seed: 1 })).toThrow(RangeError);
  });

  test('PPV falls as prior probability falls', () => {
    expect(S.ppv(0.5, 0.8, 0.05)).toBeCloseTo(0.9412, 3);
    expect(S.ppv(0.1, 0.35, 0.05)).toBeLessThan(0.45);
    expect(S.ppv(0, 0.8, 0.05)).toBe(0);
  });
});

test.describe('optional stopping', () => {
  test('peeking inflates false positives well above alpha', () => {
    const result = S.simulatePeeking({ d: 0, nStart: 10, step: 5, nMax: 100, alpha: 0.05, reps: 1500, seed: 2 });
    expect(result.falsePositiveRate).toBeGreaterThan(0.2);
    expect(result.fixedDesignRate).toBeLessThan(0.09);
  });

  test('a single look keeps the false positive rate near alpha', () => {
    const result = S.simulatePeeking({ d: 0, nStart: 50, step: 50, nMax: 50, alpha: 0.05, reps: 3000, seed: 4 });
    expect(result.looks).toEqual([50]);
    expect(Math.abs(result.falsePositiveRate - 0.05)).toBeLessThan(0.017);
  });

  test('cumulative rejection curve never decreases', () => {
    const result = S.simulatePeeking({ d: 0, nStart: 10, step: 10, nMax: 60, alpha: 0.05, reps: 500, seed: 9 });
    for (let i = 1; i < result.cumulativeRate.length; i++) {
      expect(result.cumulativeRate[i]).toBeGreaterThanOrEqual(result.cumulativeRate[i - 1]);
    }
  });
});

test.describe('multiple outcomes', () => {
  test('uncorrected familywise rate matches 1-(1-a)^k for independent outcomes', () => {
    const result = S.simulateForking({ k: 10, rho: 0, n: 20, alpha: 0.05, reps: 1500, seed: 6, correction: 'none' });
    expect(Math.abs(result.familywiseRate - result.independentExpectation)).toBeLessThan(0.04);
  });

  test('correlated outcomes inflate less than independent ones', () => {
    const independent = S.simulateForking({ k: 10, rho: 0, n: 20, alpha: 0.05, reps: 1200, seed: 6, correction: 'none' });
    const correlated = S.simulateForking({ k: 10, rho: 0.8, n: 20, alpha: 0.05, reps: 1200, seed: 6, correction: 'none' });
    expect(correlated.familywiseRate).toBeLessThan(independent.familywiseRate);
  });

  test('Bonferroni and Holm hold the familywise rate near alpha', () => {
    for (const correction of ['bonferroni', 'holm']) {
      const result = S.simulateForking({ k: 10, rho: 0, n: 20, alpha: 0.05, reps: 1500, seed: 8, correction });
      expect(result.familywiseRate).toBeLessThan(0.075);
    }
  });

  test('Holm adjustment is monotone and never exceeds 1', () => {
    const adjusted = S.adjustPValues([0.01, 0.04, 0.03, 0.5], 'holm');
    expect(adjusted[0]).toBeCloseTo(0.04, 10);
    expect(adjusted[2]).toBeCloseTo(0.09, 10);
    expect(adjusted[1]).toBeCloseTo(0.09, 10);
    expect(adjusted[3]).toBe(0.5);
    expect(S.adjustPValues([0.6, 0.7], 'bonferroni')).toEqual([1, 1]);
  });
});

test.describe('bayesian updating', () => {
  test('uniform prior with 7/10 gives Beta(8,4) with mean 2/3', () => {
    const post = S.betaPosterior(1, 1, 7, 10);
    expect(post.a).toBe(8);
    expect(post.b).toBe(4);
    expect(post.mean).toBeCloseTo(2 / 3, 10);
    expect(post.interval[0]).toBeLessThan(post.mean);
    expect(post.interval[1]).toBeGreaterThan(post.mean);
  });

  test('credible interval has the requested mass', () => {
    const post = S.betaPosterior(2, 2, 30, 50);
    const mass = S.betaInc(post.a, post.b, post.interval[1]) - S.betaInc(post.a, post.b, post.interval[0]);
    expect(mass).toBeCloseTo(0.95, 6);
  });

  test('ROPE probability is between 0 and 1 and shrinks as data accumulate away from it', () => {
    const early = S.betaPosterior(1, 1, 6, 10, 0.45, 0.55).pRope;
    const late = S.betaPosterior(1, 1, 600, 1000, 0.45, 0.55).pRope;
    expect(early).toBeGreaterThan(late);
    expect(late).toBeGreaterThanOrEqual(0);
  });

  test('Bayes factor: 5/10 favours the null, 90/100 favours the alternative', () => {
    expect(S.bayesFactor10(5, 10)).toBeLessThan(1 / 2);
    expect(S.bayesFactor10(90, 100)).toBeGreaterThan(1e10);
  });

  test('invalid counts are rejected', () => {
    expect(() => S.betaPosterior(1, 1, 11, 10)).toThrow(RangeError);
  });

  test('histogram bins everything, clamping values outside the range', () => {
    const hist = S.histogram([0, 0.1, 0.99, 1, 2, -1], 10, 0, 1);
    expect(hist.counts.reduce((s, v) => s + v, 0)).toBe(6);
    expect(hist.counts[9]).toBe(3);
  });
});
