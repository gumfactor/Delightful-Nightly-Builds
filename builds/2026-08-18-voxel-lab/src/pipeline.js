/* Voxel Lab — six canonical fMRI preprocessing/analysis pipeline steps.
 * Every visual is generated from synthetic data computed at render time —
 * never real scan data — using the shared math in stats.js/mc-sim.js. */

(function () {
  const stats = () => window.VoxelStats;
  const mc = () => window.VoxelMonteCarlo;

  function clear(ctx, w, h) {
    ctx.fillStyle = '#0b0f14';
    ctx.fillRect(0, 0, w, h);
  }

  function drawBrainOutline(ctx, cx, cy, rx, ry, color, dashed) {
    ctx.save();
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    if (dashed) ctx.setLineDash([6, 4]);
    ctx.beginPath();
    ctx.ellipse(cx, cy, rx, ry, 0, 0, Math.PI * 2);
    ctx.stroke();
    ctx.restore();
  }

  // 1. Motion correction ----------------------------------------------------
  function renderMotionCorrection(ctx, w, h, phase, rng) {
    clear(ctx, w, h);
    const cx = w / 2;
    const cy = h / 2;
    const r = Math.min(w, h) * 0.22;
    const frames = 5;
    for (let f = 0; f < frames; f++) {
      let ox = 0;
      let oy = 0;
      if (phase === 'before') {
        ox = (rng() - 0.5) * w * 0.18;
        oy = (rng() - 0.5) * h * 0.18;
      }
      ctx.globalAlpha = 0.35;
      ctx.fillStyle = `hsl(${190 + f * 10}, 80%, 60%)`;
      ctx.beginPath();
      ctx.ellipse(cx + ox, cy + oy, r, r * 0.8, 0, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.globalAlpha = 1;
    ctx.fillStyle = '#e6edf3';
    ctx.font = '13px sans-serif';
    ctx.fillText(phase === 'before' ? '5 frames, uncorrected head motion' : '5 frames, realigned to a reference', 10, h - 12);
  }

  // 2. Slice timing correction ----------------------------------------------
  function renderSliceTiming(ctx, w, h, phase, rng) {
    clear(ctx, w, h);
    const rows = 10;
    const rowHeight = h / (rows + 1);
    for (let i = 0; i < rows; i++) {
      const y = rowHeight * (i + 1);
      const acquisitionOffset = phase === 'before' ? (i / rows) * 0.4 : 0;
      const phaseShift = acquisitionOffset * Math.PI;
      ctx.strokeStyle = '#30363d';
      ctx.beginPath();
      ctx.moveTo(10, y);
      ctx.lineTo(w - 10, y);
      ctx.stroke();
      const bandX = 10 + ((w - 20) * (0.5 + 0.4 * Math.sin(phaseShift)));
      ctx.fillStyle = '#58a6ff';
      ctx.beginPath();
      ctx.arc(bandX, y, 5, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.fillStyle = '#e6edf3';
    ctx.font = '13px sans-serif';
    ctx.fillText(
      phase === 'before' ? 'Slices acquired at staggered times — diagonal shear' : 'Resampled to a common reference time',
      10,
      16
    );
    void rng;
  }

  // 3. Spatial normalization --------------------------------------------------
  function renderNormalization(ctx, w, h, phase, rng) {
    clear(ctx, w, h);
    const cx = w / 2;
    const cy = h / 2;
    const templateRx = Math.min(w, h) * 0.24;
    const templateRy = templateRx * 0.85;
    drawBrainOutline(ctx, cx, cy, templateRx, templateRy, '#3fb950', true);

    if (phase === 'before') {
      const subjRx = templateRx * (0.7 + rng() * 0.5);
      const subjRy = templateRy * (0.7 + rng() * 0.5);
      const dx = (rng() - 0.5) * w * 0.15;
      const dy = (rng() - 0.5) * h * 0.15;
      drawBrainOutline(ctx, cx + dx, cy + dy, subjRx, subjRy, '#f0883e', false);
    } else {
      drawBrainOutline(ctx, cx, cy, templateRx, templateRy, '#f0883e', false);
    }
    ctx.fillStyle = '#e6edf3';
    ctx.font = '13px sans-serif';
    ctx.fillText(phase === 'before' ? 'Subject anatomy (orange) vs. template (green)' : 'Warped into template space — outlines coincide', 10, h - 12);
  }

  // 4. Spatial smoothing ---------------------------------------------------
  function boxBlur(field, w, h, radius) {
    const out = new Float64Array(field.length);
    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        let sum = 0;
        let count = 0;
        for (let dy = -radius; dy <= radius; dy++) {
          for (let dx = -radius; dx <= radius; dx++) {
            const nx = x + dx;
            const ny = y + dy;
            if (nx >= 0 && nx < w && ny >= 0 && ny < h) {
              sum += field[ny * w + nx];
              count++;
            }
          }
        }
        out[y * w + x] = sum / count;
      }
    }
    return out;
  }

  function renderSmoothing(ctx, w, h, phase, rng) {
    const gridW = 40;
    const gridH = 28;
    const field = new Float64Array(gridW * gridH);
    for (let i = 0; i < field.length; i++) field[i] = stats().gaussianRandom(rng);

    const display = phase === 'before' ? field : boxBlur(field, gridW, gridH, 2);
    const cellW = w / gridW;
    const cellH = h / gridH;
    let min = Infinity;
    let max = -Infinity;
    for (const v of display) {
      if (v < min) min = v;
      if (v > max) max = v;
    }
    for (let y = 0; y < gridH; y++) {
      for (let x = 0; x < gridW; x++) {
        const v = display[y * gridW + x];
        const t = max > min ? (v - min) / (max - min) : 0.5;
        const gray = Math.round(t * 255);
        ctx.fillStyle = `rgb(${gray},${gray},${gray})`;
        ctx.fillRect(x * cellW, y * cellH, cellW + 1, cellH + 1);
      }
    }
    ctx.fillStyle = '#f0f6fc';
    ctx.font = '13px sans-serif';
    ctx.fillText(phase === 'before' ? 'Raw voxel-wise noise' : 'After a real 5x5 box-blur kernel', 10, 16);
  }

  // 5. HRF convolution & GLM -------------------------------------------------
  function renderHRFGLM(ctx, w, h, phase, rng) {
    clear(ctx, w, h);
    const durationSec = 60;
    const dt = 0.5;
    const nSamples = Math.round(durationSec / dt);
    const boxcar = new Array(nSamples).fill(0);
    for (let i = 0; i < nSamples; i++) {
      const t = i * dt;
      boxcar[i] = Math.floor(t / 15) % 2 === 0 ? 1 : 0;
    }

    const marginL = 40;
    const marginB = 24;
    const plotW = w - marginL - 10;
    const plotH = h - marginB - 10;

    function plotSeries(series, color, baselineY, scale) {
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.beginPath();
      for (let i = 0; i < series.length; i++) {
        const x = marginL + (i / (series.length - 1)) * plotW;
        const y = baselineY - series[i] * scale;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();
    }

    ctx.strokeStyle = '#30363d';
    ctx.beginPath();
    ctx.moveTo(marginL, 10);
    ctx.lineTo(marginL, h - marginB);
    ctx.lineTo(w - 10, h - marginB);
    ctx.stroke();

    if (phase === 'before') {
      plotSeries(boxcar, '#58a6ff', h - marginB - 5, plotH * 0.7);
      ctx.fillStyle = '#e6edf3';
      ctx.font = '13px sans-serif';
      ctx.fillText('Task design (boxcar): stimulus on/off', marginL, 16);
    } else {
      const kernel = [];
      for (let t = 0; t <= 30; t += dt) kernel.push(stats().doubleGammaHRF(t));
      const predicted = stats().convolve(boxcar, kernel);
      const maxPred = Math.max(...predicted, 1e-6);
      const normPredicted = predicted.map((v) => v / maxPred);

      const trueBeta = 2 + Math.floor(rng() * 3); // 2..4
      const noisy = normPredicted.map((v) => trueBeta * v + stats().gaussianRandom(rng) * 0.3);

      const design = normPredicted.map((v) => [1, v]);
      const beta = stats().leastSquaresBeta(design, noisy);

      plotSeries(normPredicted, '#3fb950', h - marginB - 5, plotH * 0.6);

      ctx.fillStyle = '#f0883e';
      for (let i = 0; i < noisy.length; i += 2) {
        const x = marginL + (i / (noisy.length - 1)) * plotW;
        const y = h - marginB - 5 - (noisy[i] / (trueBeta + 1)) * plotH * 0.5;
        ctx.beginPath();
        ctx.arc(x, y, 1.5, 0, Math.PI * 2);
        ctx.fill();
      }

      ctx.fillStyle = '#e6edf3';
      ctx.font = '13px sans-serif';
      ctx.fillText(`Predicted response (green) fit to noisy signal (orange dots)`, marginL, 16);
      ctx.fillText(`True beta = ${trueBeta.toFixed(1)}, GLM-recovered beta = ${beta[1].toFixed(2)}`, marginL, 30);
    }
  }

  // 6. Statistical thresholding ----------------------------------------------
  function renderThresholding(ctx, w, h, phase, rng) {
    clear(ctx, w, h);
    const voxelCount = 900;
    const method = phase === 'before' ? 'none' : 'bonferroni';
    const trial = mc().simulateTrial({ voxelCount, method, alpha: 0.05, rng });
    const cellSize = Math.min(w / trial.width, h / trial.height);
    const gridPixelW = trial.width * cellSize;
    const offsetX = (w - gridPixelW) / 2;
    for (const v of trial.voxels) {
      ctx.fillStyle = v.significant ? '#f85149' : '#1c2733';
      ctx.fillRect(offsetX + v.x * cellSize, v.y * cellSize, cellSize - 1, cellSize - 1);
    }
    ctx.fillStyle = '#f0f6fc';
    ctx.font = '13px sans-serif';
    const label = phase === 'before' ? `Uncorrected p<0.05: ${trial.falsePositives} false positives` : `Bonferroni-corrected: ${trial.falsePositives} false positives`;
    ctx.fillText(label, 10, h - 12);
  }

  const PIPELINE_STEPS = [
    {
      id: 'motion-correction',
      title: 'Motion Correction',
      explanation:
        'Even small head movements between (or within) volumes shift where each voxel actually samples the brain. Motion correction rigidly realigns every volume to a reference frame before anything else happens.',
      pitfall: 'Skip this and apparent "activation" can just be the edge of the brain sliding in and out of a voxel as the head moves — a classic motion artifact mistaken for a real effect.',
      render: renderMotionCorrection,
    },
    {
      id: 'slice-timing',
      title: 'Slice Timing Correction',
      explanation:
        'A single fMRI volume is usually acquired one 2D slice at a time, so different slices reflect slightly different moments. Slice timing correction interpolates each voxel\'s time series to a common reference time.',
      pitfall: 'Uncorrected staggered acquisition biases event-related timing estimates and can look like a "shear" across slices for anything with a fast time course.',
      render: renderSliceTiming,
    },
    {
      id: 'normalization',
      title: 'Spatial Normalization',
      explanation:
        'Every brain has a different size and shape. Normalization warps each subject\'s anatomy into a shared template (e.g. MNI space) so the same voxel coordinate means the same anatomical location across subjects.',
      pitfall: 'Without it, group analysis is comparing different anatomy at the same coordinates across subjects — any group-level map is meaningless.',
      render: renderNormalization,
    },
    {
      id: 'smoothing',
      title: 'Spatial Smoothing',
      explanation:
        'Applying a Gaussian (here approximated with a real box-blur kernel) spatial filter increases signal-to-noise ratio and helps satisfy the Gaussian random field assumptions used later for cluster-based statistics.',
      pitfall: 'Too much smoothing blurs away genuinely small, spatially precise effects; too little leaves data noisy and violates the smoothness assumptions correction methods rely on.',
      render: renderSmoothing,
    },
    {
      id: 'hrf-glm',
      title: 'HRF Convolution & GLM',
      explanation:
        'The BOLD signal doesn\'t track a stimulus instantly — it rises and falls over ~15-20 seconds. Convolving the task design with a canonical hemodynamic response function (HRF) produces the predicted signal shape that a General Linear Model fits against the real (noisy) data to estimate a beta weight per condition.',
      pitfall: 'Fitting a raw boxcar directly against BOLD data (skipping HRF convolution) systematically underestimates the true response and misses its delayed peak.',
      render: renderHRFGLM,
    },
    {
      id: 'thresholding',
      title: 'Statistical Thresholding',
      explanation:
        'A whole-brain analysis tests tens of thousands of voxels at once. An uncorrected p<0.05 threshold guarantees a large number of false positives purely by chance — this is exactly what the Multiple Comparisons Lab tab lets you explore in depth.',
      pitfall: 'This is the "dead salmon" problem: testing enough voxels without correction will produce apparently "significant" clusters even in a dead fish with no brain activity at all.',
      render: renderThresholding,
    },
  ];

  window.VoxelPipeline = { PIPELINE_STEPS };
})();
