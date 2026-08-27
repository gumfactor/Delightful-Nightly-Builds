/**
 * Regression Lab — deterministic preset datasets.
 * Every preset is generated from a fixed-seed PRNG (see src/math.js) so the
 * exact same points appear on every load and in every test run — nothing
 * here depends on Math.random().
 */

(function (root) {
  const M = typeof module !== 'undefined' && module.exports
    ? require('./math.js')
    : root.RegressionMath;

  function round2(v) {
    return Math.round(v * 100) / 100;
  }

  function generateWellBehaved() {
    const rand = M.seededRandom(101);
    const points = [];
    for (let i = 0; i < 16; i++) {
      const x = 1 + i * 0.9;
      const noise = M.gaussianFromUniform(rand) * 1.9;
      points.push({ x: round2(x), y: round2(3 + 1.6 * x + noise) });
    }
    return points;
  }

  function generateHeteroscedastic() {
    const rand = M.seededRandom(202);
    const points = [];
    for (let i = 0; i < 18; i++) {
      const x = 1 + i * 0.85;
      const noiseScale = 0.5 + x * 0.6;
      const noise = M.gaussianFromUniform(rand) * noiseScale;
      points.push({ x: round2(x), y: round2(4 + 1.2 * x + noise) });
    }
    return points;
  }

  function generateNonLinear() {
    const rand = M.seededRandom(303);
    const points = [];
    for (let i = 0; i < 17; i++) {
      const x = -4 + i * 0.6;
      const noise = M.gaussianFromUniform(rand) * 1.4;
      points.push({ x: round2(x), y: round2(12 + 0.3 * x + 0.8 * x * x + noise) });
    }
    return points;
  }

  function generateOutlier() {
    const rand = M.seededRandom(404);
    const points = [];
    for (let i = 0; i < 14; i++) {
      const x = 1 + i * 0.9;
      const noise = M.gaussianFromUniform(rand) * 1.5;
      points.push({ x: round2(x), y: round2(5 + 1.4 * x + noise) });
    }
    points.push({ x: 22, y: 8 });
    return points;
  }

  /**
   * Two correlated predictors for the Multicollinearity Lab, plus a
   * dependent variable built from both. `corr` (0..0.99) controls how
   * strongly x2 tracks x1; the underlying noise draws are fixed so only
   * the correlation itself changes between calls.
   */
  function buildMulticollinearData(corr, n) {
    n = n || 20;
    const c = Math.max(0, Math.min(0.99, corr));
    const randX1 = M.seededRandom(555);
    const randNoise = M.seededRandom(777);
    const randY = M.seededRandom(888);
    const x1 = [], x2 = [], y = [];
    for (let i = 0; i < n; i++) {
      const v1 = M.gaussianFromUniform(randX1) * 3 + 10;
      const noise = M.gaussianFromUniform(randNoise) * 3 + 10;
      const v2 = c * v1 + Math.sqrt(Math.max(0, 1 - c * c)) * noise;
      const yNoise = M.gaussianFromUniform(randY) * 2;
      x1.push(round2(v1));
      x2.push(round2(v2));
      y.push(round2(5 + 1.2 * v1 + 0.8 * v2 + yNoise));
    }
    return { x1, x2, y };
  }

  const PRESETS = {
    'well-behaved': {
      label: 'Well-Behaved',
      description: 'A clean linear relationship with roughly constant scatter around the line.',
      points: generateWellBehaved(),
    },
    heteroscedastic: {
      label: 'Heteroscedastic',
      description: 'The scatter around the line fans out as x increases — non-constant variance.',
      points: generateHeteroscedastic(),
    },
    'non-linear': {
      label: 'Non-Linear',
      description: 'The true relationship curves — a straight line systematically misses the middle.',
      points: generateNonLinear(),
    },
    outlier: {
      label: 'Outlier / High Leverage',
      description: 'One extreme point far from the rest can dominate the fit.',
      points: generateOutlier(),
    },
    custom: {
      label: 'Custom (Free Draw)',
      description: 'Click the canvas to add your own points; drag any point to move it.',
      points: [],
    },
  };

  const PRESET_ORDER = ['well-behaved', 'heteroscedastic', 'non-linear', 'outlier', 'custom'];

  const RegressionDatasets = { PRESETS, PRESET_ORDER, buildMulticollinearData };

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = RegressionDatasets;
  }
  if (typeof root !== 'undefined') {
    root.RegressionDatasets = RegressionDatasets;
  }
})(typeof window !== 'undefined' ? window : global);
