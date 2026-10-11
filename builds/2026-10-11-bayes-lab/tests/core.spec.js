const { test, expect } = require('@playwright/test');
const path = require('path');
const { pathToFileURL } = require('url');

const URL = pathToFileURL(path.join(__dirname, '..', 'index.html')).href;
const close = (actual, expected, tol = 1e-6) => expect(Math.abs(actual - expected)).toBeLessThan(tol);

test.beforeEach(async ({ page }) => { await page.goto(URL); });

const run = (page, fn, arg) => page.evaluate(fn, arg);

test('logGamma matches factorials and Gamma(1/2)=sqrt(pi)', async ({ page }) => {
  const [g5, gHalf] = await run(page, () => [Math.exp(Bayes.logGamma(5)), Math.exp(Bayes.logGamma(0.5))]);
  close(g5, 24, 1e-9);
  close(gHalf, Math.sqrt(Math.PI), 1e-9);
});

test('beta CDF and quantile are exact for symmetric and uniform cases and invert each other', async ({ page }) => {
  const r = await run(page, () => ({
    half: Bayes.betaCdf(0.5, 2, 2), uni: Bayes.betaCdf(0.3, 1, 1),
    q: Bayes.betaQuantile(0.5, 3, 3), roundTrip: Bayes.betaCdf(Bayes.betaQuantile(0.9, 2.5, 7), 2.5, 7),
    below: Bayes.betaCdf(0, 2, 2), above: Bayes.betaCdf(1, 2, 2),
  }));
  close(r.half, 0.5); close(r.uni, 0.3); close(r.q, 0.5); close(r.roundTrip, 0.9);
  expect(r.below).toBe(0); expect(r.above).toBe(1);
});

test('beta pdf integrates to ~1 and handles boundary shapes without NaN', async ({ page }) => {
  const r = await run(page, () => {
    let area = 0;
    const steps = 20000;
    for (let i = 0; i < steps; i++) area += Bayes.betaPdf((i + 0.5) / steps, 3, 5) / steps;
    return { area, u: Bayes.betaPdf(0, 0.5, 2), flat0: Bayes.betaPdf(0, 1, 1), outside: Bayes.betaPdf(1.5, 2, 2) };
  });
  close(r.area, 1, 1e-6);
  expect(r.u).toBe(Infinity);
  expect(r.flat0).toBe(1);
  expect(r.outside).toBe(0);
});

test('conjugate update: flat prior with 3/3 successes gives Beta(4,1), mean 0.8; k=0 and n=0 are valid', async ({ page }) => {
  const r = await run(page, () => ({
    u: Bayes.betaBinomialUpdate(1, 1, 3, 3), none: Bayes.betaBinomialUpdate(2, 3, 0, 0), zero: Bayes.betaBinomialUpdate(1, 1, 0, 5),
    mean: Bayes.betaMean(4, 1),
  }));
  expect(r.u).toEqual({ a: 4, b: 1 });
  expect(r.none).toEqual({ a: 2, b: 3 });
  expect(r.zero).toEqual({ a: 1, b: 6 });
  close(r.mean, 0.8);
});

test('HDI: symmetric Beta(5,5) is centred, mass is 95%, and skewed HDI is narrower than the equal-tailed interval', async ({ page }) => {
  const r = await run(page, () => {
    const sym = Bayes.betaHDI(5, 5, 0.95);
    const skew = Bayes.betaHDI(8, 2, 0.95);
    const et = [Bayes.betaQuantile(0.025, 8, 2), Bayes.betaQuantile(0.975, 8, 2)];
    return { sym, mass: Bayes.betaCdf(skew[1], 8, 2) - Bayes.betaCdf(skew[0], 8, 2), skewWidth: skew[1] - skew[0], etWidth: et[1] - et[0], mono: Bayes.betaHDI(1, 5, 0.9) };
  });
  close(r.sym[0] + r.sym[1], 1, 1e-6);
  close(r.mass, 0.95, 1e-6);
  expect(r.skewWidth).toBeLessThan(r.etWidth);
  expect(r.mono[0]).toBe(0);
});

test('ROPE probability equals CDF difference and is order-insensitive', async ({ page }) => {
  const r = await run(page, () => [Bayes.ropeProbability(1, 1, 0.45, 0.55), Bayes.ropeProbability(1, 1, 0.55, 0.45)]);
  close(r[0], 0.1); close(r[1], 0.1);
});

test('posterior predictive is a pmf summing to 1 with the right mean', async ({ page }) => {
  const r = await run(page, () => {
    const pmf = Bayes.predictivePmf(4, 1, 10);
    return { sum: pmf.reduce((s, v) => s + v, 0), mean: pmf.reduce((s, v, m) => s + m * v, 0) };
  });
  close(r.sum, 1, 1e-9);
  close(r.mean, 8, 1e-9);
});

test('exact binomial p-value: 7/10 vs 0.5 is 0.34375; 5/10 is 1; n=0 is 1', async ({ page }) => {
  const r = await run(page, () => [Bayes.binomialPValue(7, 10), Bayes.binomialPValue(5, 10), Bayes.binomialPValue(0, 0)]);
  close(r[0], 0.34375, 1e-9); close(r[1], 1, 1e-9); expect(r[2]).toBe(1);
});

test('Bayes factor: closed form for 7/10 uniform prior; Savage-Dickey equals marginal-likelihood BF01', async ({ page }) => {
  const r = await run(page, () => ({
    bf10: Bayes.bayesFactor10(7, 10, 1, 1, 0.5),
    viaMarginal: 1 / Bayes.bayesFactor10(5100, 10000, 1, 1, 0.5),
    viaSD: Bayes.bayesFactor01SavageDickey(5100, 10000, 1, 1, 0.5),
    jeff: [Bayes.bayesFactor10(30, 100, 0.5, 0.5, 0.4), 1 / Bayes.bayesFactor01SavageDickey(30, 100, 0.5, 0.5, 0.4)],
  }));
  close(r.bf10, (1 / 11) / (120 / 1024), 1e-9);
  close(r.viaMarginal, r.viaSD, 1e-8 * r.viaSD);
  close(r.jeff[0], r.jeff[1], 1e-6 * r.jeff[0]);
});

test("Lindley's paradox: p < .05 while the Bayes factor favours the null", async ({ page }) => {
  const r = await run(page, () => ({ p: Bayes.binomialPValue(5100, 10000), bf01: 1 / Bayes.bayesFactor10(5100, 10000, 1, 1) }));
  expect(r.p).toBeLessThan(0.05);
  expect(r.bf01).toBeGreaterThan(5);
});

test('Bayes factor labels follow Lee & Wagenmakers bands in both directions', async ({ page }) => {
  const r = await run(page, () => [Bayes.bayesFactorLabel(1), Bayes.bayesFactorLabel(5), Bayes.bayesFactorLabel(1 / 50), Bayes.bayesFactorLabel(500), Bayes.bayesFactorLabel(2)]);
  expect(r[0]).toMatch(/no real preference/);
  expect(r[1]).toBe('Moderate evidence for the alternative');
  expect(r[2]).toBe('Very strong evidence for the null');
  expect(r[3]).toBe('Extreme evidence for the alternative');
  expect(r[4]).toBe('Anecdotal evidence for the alternative');
});

test('diagnostic: 1% prevalence, 90/90 gives PPV 1/12 and NPV ~99.89%; degenerate test returns NaN PPV', async ({ page }) => {
  const r = await run(page, () => ({ d: Bayes.diagnostic(0.01, 0.9, 0.9), none: Bayes.diagnostic(0.2, 0, 1) }));
  close(r.d.ppv, 1 / 12, 1e-9);
  close(r.d.npv, 0.891 / 0.892, 1e-9);
  expect(Number.isNaN(r.none.ppv)).toBe(true);
});

test('natural frequencies always add up to the population', async ({ page }) => {
  const r = await run(page, () => {
    const out = [];
    for (const [p, se, sp] of [[0.01, 0.9, 0.9], [0.001, 0.77, 0.63], [0.6, 1, 1], [0.5, 0.5, 0.5]]) {
      const f = Bayes.naturalFrequencies(p, se, sp, 1000);
      out.push(f.tp + f.fn + f.fp + f.tn);
    }
    return { totals: out, f: Bayes.naturalFrequencies(0.01, 0.9, 0.9, 1000) };
  });
  expect(r.totals).toEqual([1000, 1000, 1000, 1000]);
  expect(r.f).toEqual({ tp: 9, fn: 1, fp: 99, tn: 891 });
});

test('normal update: equal precision averages, precise data dominates, weights sum correctly', async ({ page }) => {
  const r = await run(page, () => ({ eq: Bayes.normalUpdate(0, 1, 2, 1), dom: Bayes.normalUpdate(0, 1, 2, 0.01) }));
  close(r.eq.mean, 1); close(r.eq.sd, Math.SQRT1_2); close(r.eq.dataWeight, 0.5);
  expect(r.dom.mean).toBeGreaterThan(1.99);
  expect(r.dom.dataWeight).toBeGreaterThan(0.999);
});

test('Brier score: perfect 0, always-50% 0.25, confident-wrong 1, empty is NaN', async ({ page }) => {
  const r = await run(page, () => ({
    perfect: Bayes.brierScore([{ p: 1, outcome: true }, { p: 0, outcome: false }]),
    coin: Bayes.brierScore([{ p: 0.5, outcome: true }, { p: 0.5, outcome: false }]),
    wrong: Bayes.brierScore([{ p: 1, outcome: false }]),
    empty: Bayes.brierScore([]),
  }));
  expect(r.perfect).toBe(0); close(r.coin, 0.25); expect(r.wrong).toBe(1); expect(Number.isNaN(r.empty)).toBe(true);
});

test('samplesToAgree: skeptic and enthusiast need data to converge; returns a finite n', async ({ page }) => {
  const r = await run(page, () => ({ n: LessonInternals.samplesToAgree(0.6), zero: LessonInternals.samplesToAgree(0.5, 0.7) }));
  expect(r.n).toBeGreaterThan(20);
  expect(r.n).toBeLessThan(200);
  expect(r.zero).toBe(0);
});
