/* Voxel Lab — core statistics, numerically verified against hand-worked
 * reference values in tests/stats.spec.js. No external dependencies. */

/** Deterministic PRNG (mulberry32). Same seed -> same sequence, used so
 *  Monte Carlo runs and quiz distractor generation are testable. */
function mulberry32(seed) {
  let a = seed >>> 0;
  return function rng() {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** Box-Muller transform: one standard-normal draw from a uniform RNG. */
function gaussianRandom(rng) {
  let u1 = 0;
  while (u1 === 0) u1 = rng();
  const u2 = rng();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

/** Abramowitz-Stegun 7.1.26 erf approximation, max error ~1.5e-7. */
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
  const y = 1 - ((((a5 * t + a4) * t + a3) * t + a2) * t + a1) * t * Math.exp(-x * x);
  return sign * y;
}

function normalCdf(z) {
  return 0.5 * (1 + erf(z / Math.SQRT2));
}

/** Two-tailed p-value for a standard-normal test statistic z. */
function pValueFromZ(z) {
  return 2 * (1 - normalCdf(Math.abs(z)));
}

function bonferroniThreshold(alpha, n) {
  return alpha / n;
}

function bonferroniSignificant(pValues, alpha) {
  const threshold = bonferroniThreshold(alpha, pValues.length);
  return pValues.map((p) => p < threshold);
}

/** Benjamini-Hochberg step-up FDR procedure.
 *  Returns a boolean array (original order) of which p-values are significant. */
function benjaminiHochberg(pValues, alpha) {
  const n = pValues.length;
  const indexed = pValues.map((p, i) => ({ p, i })).sort((a, b) => a.p - b.p);
  let cutoffRank = -1;
  for (let k = n; k >= 1; k--) {
    const critical = (k / n) * alpha;
    if (indexed[k - 1].p <= critical) {
      cutoffRank = k;
      break;
    }
  }
  const significant = new Array(n).fill(false);
  if (cutoffRank > 0) {
    for (let k = 0; k < cutoffRank; k++) {
      significant[indexed[k].i] = true;
    }
  }
  return significant;
}

/** 4-connected flood-fill cluster labeling over a binary mask laid out as a
 *  flat array with the given width/height. Returns { labels, sizes } where
 *  labels[i] is the 1-indexed cluster id (0 = not in mask) and sizes[id] is
 *  that cluster's voxel count. */
function labelClusters(mask, width, height) {
  const labels = new Array(mask.length).fill(0);
  const sizes = [0];
  let nextLabel = 1;

  for (let start = 0; start < mask.length; start++) {
    if (!mask[start] || labels[start] !== 0) continue;
    const stack = [start];
    labels[start] = nextLabel;
    let size = 0;
    while (stack.length) {
      const idx = stack.pop();
      size++;
      const x = idx % width;
      const y = Math.floor(idx / width);
      const neighbors = [
        [x - 1, y],
        [x + 1, y],
        [x, y - 1],
        [x, y + 1],
      ];
      for (const [nx, ny] of neighbors) {
        if (nx < 0 || nx >= width || ny < 0 || ny >= height) continue;
        const nIdx = ny * width + nx;
        if (mask[nIdx] && labels[nIdx] === 0) {
          labels[nIdx] = nextLabel;
          stack.push(nIdx);
        }
      }
    }
    sizes[nextLabel] = size;
    nextLabel++;
  }
  return { labels, sizes };
}

/** Cluster-extent correction: keep only mask voxels belonging to a cluster
 *  whose size is >= minClusterSize. Returns a new boolean mask. */
function clusterExtentThreshold(mask, width, height, minClusterSize) {
  const { labels, sizes } = labelClusters(mask, width, height);
  return mask.map((_, i) => {
    const label = labels[i];
    return label > 0 && sizes[label] >= minClusterSize;
  });
}

/** Canonical double-gamma HRF (Glover 1999 parameterization), each gamma
 *  term normalized so its own peak height is exactly 1 at t = n*tau. */
function rawHRF(t, n1 = 6, tau1 = 0.9, n2 = 12, tau2 = 0.9, a = 0.35) {
  if (t <= 0) return 0;
  const term1 = Math.pow(t / (n1 * tau1), n1) * Math.exp(n1 - t / tau1);
  const term2 = Math.pow(t / (n2 * tau2), n2) * Math.exp(n2 - t / tau2);
  return term1 - a * term2;
}

/** Peak height/time of the raw HRF, found by dense sampling once. */
function findHRFPeak() {
  let peakTime = 0;
  let peakValue = -Infinity;
  for (let t = 0; t <= 30; t += 0.01) {
    const v = rawHRF(t);
    if (v > peakValue) {
      peakValue = v;
      peakTime = t;
    }
  }
  return { peakTime, peakValue };
}

const HRF_PEAK = findHRFPeak();

/** Normalized HRF: peak value is exactly 1.0. */
function doubleGammaHRF(t) {
  return rawHRF(t) / HRF_PEAK.peakValue;
}

/** Full linear discrete convolution, trimmed to the input signal's length
 *  (i.e. "same"-mode convolution anchored at the signal's start). */
function convolve(signal, kernel) {
  const out = new Array(signal.length).fill(0);
  for (let i = 0; i < signal.length; i++) {
    let sum = 0;
    for (let k = 0; k < kernel.length; k++) {
      const j = i - k;
      if (j >= 0 && j < signal.length) sum += signal[j] * kernel[k];
    }
    out[i] = sum;
  }
  return out;
}

/** Solve a small linear system Ax=b via Gauss-Jordan elimination with
 *  partial pivoting. A is an array of rows, b is a column array. */
function solveLinearSystem(A, b) {
  const n = A.length;
  const M = A.map((row, i) => [...row, b[i]]);
  for (let col = 0; col < n; col++) {
    let pivotRow = col;
    for (let r = col + 1; r < n; r++) {
      if (Math.abs(M[r][col]) > Math.abs(M[pivotRow][col])) pivotRow = r;
    }
    [M[col], M[pivotRow]] = [M[pivotRow], M[col]];
    const pivot = M[col][col];
    if (Math.abs(pivot) < 1e-12) continue;
    for (let c = col; c <= n; c++) M[col][c] /= pivot;
    for (let r = 0; r < n; r++) {
      if (r === col) continue;
      const factor = M[r][col];
      for (let c = col; c <= n; c++) M[r][c] -= factor * M[col][c];
    }
  }
  return M.map((row) => row[n]);
}

/** Ordinary least squares: designMatrix is an array of rows (one per
 *  observation), y is the observed values. Returns the beta coefficient
 *  vector, solved via the normal equations (X^T X) beta = X^T y. */
function leastSquaresBeta(designMatrix, y) {
  const nObs = designMatrix.length;
  const nCoef = designMatrix[0].length;
  const XtX = Array.from({ length: nCoef }, () => new Array(nCoef).fill(0));
  const Xty = new Array(nCoef).fill(0);
  for (let i = 0; i < nObs; i++) {
    for (let a = 0; a < nCoef; a++) {
      Xty[a] += designMatrix[i][a] * y[i];
      for (let bcol = 0; bcol < nCoef; bcol++) {
        XtX[a][bcol] += designMatrix[i][a] * designMatrix[i][bcol];
      }
    }
  }
  return solveLinearSystem(XtX, Xty);
}

// Exposed for both classic-script browser use and Playwright page.evaluate.
if (typeof window !== 'undefined') {
  window.VoxelStats = {
    mulberry32,
    gaussianRandom,
    erf,
    normalCdf,
    pValueFromZ,
    bonferroniThreshold,
    bonferroniSignificant,
    benjaminiHochberg,
    labelClusters,
    clusterExtentThreshold,
    doubleGammaHRF,
    HRF_PEAK,
    convolve,
    solveLinearSystem,
    leastSquaresBeta,
  };
}
