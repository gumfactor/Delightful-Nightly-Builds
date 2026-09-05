// Mediation model: X -> M -> Y. Classic script, depends on rng.js and stats.js
// having already been loaded (uses their global functions directly).

// Draws a fresh synthetic sample from a data-generating process controlled by
// the caller's chosen "true" path values, using a seeded RNG so the same seed
// always reproduces the exact same sample.
function generateMediationSample(params) {
  const { trueA, trueB, trueCPrime, noiseSD, n, seed } = params;
  const rng = createRng(seed);
  const X = [], M = [], Y = [];
  for (let i = 0; i < n; i++) {
    const x = 10 + 3 * nextGaussian(rng);
    const m = 5 + trueA * x + noiseSD * nextGaussian(rng);
    const y = 2 + trueCPrime * x + trueB * m + noiseSD * nextGaussian(rng);
    X.push(x); M.push(m); Y.push(y);
  }
  return { X, M, Y, rng };
}

// Runs the full mediation analysis (paths a, b, c, c', Sobel test, and a
// bootstrap percentile CI for the indirect effect a*b) on an already-drawn
// sample. `rng` continues the same seeded stream so bootstrap resampling is
// reproducible for a given seed.
function analyzeMediation(sample, rng, bootstrapReps) {
  bootstrapReps = bootstrapReps || 2000;
  const { X, M, Y } = sample;
  const n = X.length;

  const rA = ols(X.map(x => [x]), M);
  const a = rA.beta[1], aSE = rA.se[1];

  const rBC = ols(X.map((x, i) => [x, M[i]]), Y);
  const cPrime = rBC.beta[1], cPrimeSE = rBC.se[1];
  const b = rBC.beta[2], bSE = rBC.se[2];

  const rC = ols(X.map(x => [x]), Y);
  const c = rC.beta[1], cSE = rC.se[1];

  const indirect = a * b;

  const sobelSE = Math.sqrt(b * b * aSE * aSE + a * a * bSE * bSE);
  const sobelZ = sobelSE > 0 ? indirect / sobelSE : NaN;
  const sobelP = 2 * (1 - normalCDF(Math.abs(sobelZ)));

  const bootDist = new Array(bootstrapReps);
  for (let r = 0; r < bootstrapReps; r++) {
    const idx = new Array(n);
    for (let i = 0; i < n; i++) idx[i] = Math.floor(rng() * n);
    const Xb = idx.map(i => X[i]), Mb = idx.map(i => M[i]), Yb = idx.map(i => Y[i]);
    let ab;
    try {
      const ra = ols(Xb.map(x => [x]), Mb);
      const rbc = ols(Xb.map((x, i) => [x, Mb[i]]), Yb);
      ab = ra.beta[1] * rbc.beta[2];
    } catch (e) {
      ab = NaN;
    }
    bootDist[r] = ab;
  }
  const validBoot = bootDist.filter(v => !Number.isNaN(v)).sort((x, y) => x - y);
  const bootstrapCI = validBoot.length > 0
    ? [quantile(validBoot, 0.025), quantile(validBoot, 0.975)]
    : [NaN, NaN];

  return {
    a, aSE, b, bSE, cPrime, cPrimeSE, c, cSE, indirect,
    identityCheck: c - (cPrime + indirect),
    sobelSE, sobelZ, sobelP,
    bootstrapCI, bootstrapReps: validBoot.length,
    ciExcludesZero: bootstrapCI[0] > 0 || bootstrapCI[1] < 0,
  };
}
