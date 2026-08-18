/* Voxel Lab — multiple comparisons Monte Carlo engine.
 * Every "trial" generates pure-noise voxels (no injected true signal
 * anywhere) so any voxel marked significant is, by construction, a false
 * positive. This is what the tool uses to teach why correction matters. */

const METHODS = ['none', 'bonferroni', 'fdr', 'cluster'];

function gridWidthFor(voxelCount) {
  return Math.ceil(Math.sqrt(voxelCount));
}

/** Apply one correction method to an already-computed p-value array.
 *  Shared by simulateTrial (single method) and runComparison (all methods
 *  applied to the SAME noise draw, for a fair side-by-side comparison). */
function computeSignificance(pValues, method, alpha, width, height, minClusterSize) {
  if (method === 'none') {
    return pValues.map((p) => p < alpha);
  }
  if (method === 'bonferroni') {
    return window.VoxelStats.bonferroniSignificant(pValues, alpha);
  }
  if (method === 'fdr') {
    return window.VoxelStats.benjaminiHochberg(pValues, alpha);
  }
  if (method === 'cluster') {
    const uncorrectedMask = pValues.map((p) => p < alpha);
    // Pad the mask to a full width*height rectangle so cluster labeling
    // never reads past the array (extra cells are simply "not in mask").
    const padded = new Array(width * height).fill(false);
    for (let i = 0; i < pValues.length; i++) padded[i] = uncorrectedMask[i];
    const corrected = window.VoxelStats.clusterExtentThreshold(padded, width, height, minClusterSize);
    return corrected.slice(0, pValues.length);
  }
  throw new Error(`Unknown correction method: ${method}`);
}

function drawNoiseVoxels(voxelCount, rng) {
  const stats = window.VoxelStats;
  const width = gridWidthFor(voxelCount);
  const height = Math.ceil(voxelCount / width);
  const zValues = [];
  const pValues = [];
  for (let i = 0; i < voxelCount; i++) {
    const z = stats.gaussianRandom(rng);
    zValues.push(z);
    pValues.push(stats.pValueFromZ(z));
  }
  return { zValues, pValues, width, height };
}

/** One Monte Carlo trial: draw voxelCount independent standard-normal
 *  noise values, compute p-values, apply the chosen correction method,
 *  and report which voxels survive as "significant" (i.e. false positives). */
function simulateTrial({ voxelCount, method, alpha, rng, minClusterSize = 5 }) {
  const { zValues, pValues, width, height } = drawNoiseVoxels(voxelCount, rng);
  const significant = computeSignificance(pValues, method, alpha, width, height, minClusterSize);

  const voxels = zValues.map((z, i) => ({
    value: z,
    pValue: pValues[i],
    significant: significant[i],
    x: i % width,
    y: Math.floor(i / width),
  }));

  return {
    method,
    alpha,
    voxelCount,
    width,
    height,
    falsePositives: significant.filter(Boolean).length,
    voxels,
  };
}

/** Run `trials` independent simulateTrial calls and summarize the false
 *  positive counts (raw list + mean + population std). */
function runMonteCarlo({ voxelCount, method, alpha, trials, rng, minClusterSize = 5 }) {
  const counts = [];
  let lastTrial = null;
  for (let t = 0; t < trials; t++) {
    const trial = simulateTrial({ voxelCount, method, alpha, rng, minClusterSize });
    counts.push(trial.falsePositives);
    lastTrial = trial;
  }
  const mean = counts.reduce((a, b) => a + b, 0) / counts.length;
  const variance = counts.reduce((a, b) => a + (b - mean) ** 2, 0) / counts.length;
  return {
    method,
    alpha,
    voxelCount,
    trials,
    counts,
    mean,
    std: Math.sqrt(variance),
    lastTrial,
  };
}

/** Run `trials` trials where every method is applied to the SAME noise draw
 *  per trial (fair comparison, not independent samples per method). Returns
 *  per-method counts/mean/std plus the last trial's per-method voxel grids
 *  for a side-by-side visualization. */
function runComparison({ voxelCount, alpha, trials, rng, minClusterSize = 5 }) {
  const counts = { none: [], bonferroni: [], fdr: [], cluster: [] };
  let lastVoxelsByMethod = null;
  let width = 0;
  let height = 0;

  for (let t = 0; t < trials; t++) {
    const draw = drawNoiseVoxels(voxelCount, rng);
    width = draw.width;
    height = draw.height;
    const isLast = t === trials - 1;
    if (isLast) lastVoxelsByMethod = {};

    for (const method of METHODS) {
      const significant = computeSignificance(draw.pValues, method, alpha, draw.width, draw.height, minClusterSize);
      counts[method].push(significant.filter(Boolean).length);
      if (isLast) {
        lastVoxelsByMethod[method] = draw.zValues.map((z, i) => ({
          x: i % draw.width,
          y: Math.floor(i / draw.width),
          significant: significant[i],
        }));
      }
    }
  }

  const summary = {};
  for (const method of METHODS) {
    const c = counts[method];
    const mean = c.reduce((a, b) => a + b, 0) / c.length;
    const variance = c.reduce((a, b) => a + (b - mean) ** 2, 0) / c.length;
    summary[method] = { counts: c, mean, std: Math.sqrt(variance) };
  }

  return { voxelCount, alpha, trials, width, height, methods: summary, lastVoxelsByMethod };
}

if (typeof window !== 'undefined') {
  window.VoxelMonteCarlo = { simulateTrial, runMonteCarlo, runComparison, gridWidthFor, METHODS };
}
