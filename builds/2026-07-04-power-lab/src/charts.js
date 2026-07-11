// Native Canvas 2D rendering for the Power Explorer tab -- no external
// charting library. This build's test environment has a sandboxed network
// policy that blocks outbound requests (confirmed while building this very
// app), so a CDN-hosted charting library cannot be relied on to load either
// in tests or, potentially, for the end user. Real math, drawn by hand.
//
// Loaded as a classic (non-module) script after stats.js, so it reads
// PowerLabStats off window rather than using ES import/export -- Chromium
// blocks type="module" scripts entirely when a page is opened via a plain
// file:// URL (no local server), which this app must support. Wrapped in an
// IIFE so top-level declarations don't collide with other classic scripts
// sharing this page's global lexical scope (see stats.js for detail).
(function () {

const { invNormalCDF } = window.PowerLabStats;

function normalPDF(x) {
  return Math.exp((-x * x) / 2) / Math.sqrt(2 * Math.PI);
}

function nFactorFor(testType) {
  return testType === 'two-sample' ? 2 : 1;
}

function criticalZ(alpha, tails) {
  const tailAlpha = tails === 'one' ? alpha : alpha / 2;
  return invNormalCDF(1 - tailAlpha);
}

const COLORS = {
  h0: '#7aa2f7',
  h1: '#f7768e',
  reject: 'rgba(247, 118, 142, 0.28)',
  grid: 'rgba(148, 163, 184, 0.18)',
  axis: 'rgba(148, 163, 184, 0.5)',
  text: '#94a3b8',
  point: '#9ece6a',
  refLine: 'rgba(148, 163, 184, 0.6)',
};

// Resizes a canvas's backing store to match its rendered CSS size at the
// current devicePixelRatio, and returns a context pre-scaled so drawing
// coordinates can be expressed in CSS pixels.
function fitCanvas(canvas) {
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  const width = Math.max(1, Math.round(rect.width));
  const height = Math.max(1, Math.round(rect.height));
  canvas.width = width * dpr;
  canvas.height = height * dpr;
  const ctx = canvas.getContext('2d');
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  return { ctx, width, height };
}

const PAD = { top: 16, right: 16, bottom: 32, left: 40 };

function scaleFns(width, height, xMin, xMax, yMin, yMax) {
  const plotW = width - PAD.left - PAD.right;
  const plotH = height - PAD.top - PAD.bottom;
  const sx = (x) => PAD.left + ((x - xMin) / (xMax - xMin)) * plotW;
  const sy = (y) => PAD.top + plotH - ((y - yMin) / (yMax - yMin)) * plotH;
  return { sx, sy, plotW, plotH };
}

function drawAxes(ctx, width, height, xTicks, yTicks, sx, sy, xLabel, yLabel) {
  ctx.clearRect(0, 0, width, height);
  ctx.strokeStyle = COLORS.grid;
  ctx.lineWidth = 1;
  ctx.fillStyle = COLORS.text;
  ctx.font = '11px -apple-system, sans-serif';

  yTicks.forEach((yt) => {
    const py = sy(yt);
    ctx.beginPath();
    ctx.moveTo(PAD.left, py);
    ctx.lineTo(width - PAD.right, py);
    ctx.stroke();
    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';
    ctx.fillText(typeof yt === 'number' ? yt.toFixed(2) : yt, PAD.left - 6, py);
  });

  ctx.textAlign = 'center';
  ctx.textBaseline = 'top';
  xTicks.forEach((xt) => {
    const px = sx(xt);
    ctx.fillText(String(xt), px, height - PAD.bottom + 6);
  });

  ctx.strokeStyle = COLORS.axis;
  ctx.beginPath();
  ctx.moveTo(PAD.left, PAD.top);
  ctx.lineTo(PAD.left, height - PAD.bottom);
  ctx.lineTo(width - PAD.right, height - PAD.bottom);
  ctx.stroke();

  ctx.fillStyle = COLORS.text;
  ctx.textAlign = 'center';
  ctx.fillText(xLabel, (width + PAD.left - PAD.right) / 2, height - 10);
  ctx.save();
  ctx.translate(12, (height + PAD.top - PAD.bottom) / 2);
  ctx.rotate(-Math.PI / 2);
  ctx.fillText(yLabel, 0, 0);
  ctx.restore();
}

function drawLegend(ctx, width, entries) {
  let x = PAD.left + 4;
  const y = PAD.top + 4;
  ctx.font = '11px -apple-system, sans-serif';
  entries.forEach(({ color, label }) => {
    ctx.fillStyle = color;
    ctx.fillRect(x, y, 10, 10);
    ctx.fillStyle = COLORS.text;
    ctx.textAlign = 'left';
    ctx.textBaseline = 'top';
    ctx.fillText(label, x + 14, y - 1);
    x += ctx.measureText(label).width + 34;
  });
}

function niceStep(range, targetTicks) {
  const raw = range / targetTicks;
  const magnitude = Math.pow(10, Math.floor(Math.log10(raw)));
  const residual = raw / magnitude;
  let step;
  if (residual > 5) step = 10 * magnitude;
  else if (residual > 2) step = 5 * magnitude;
  else if (residual > 1) step = 2 * magnitude;
  else step = magnitude;
  return step;
}

function createDistributionChart(canvas) {
  let lastParams = null;

  function draw() {
    if (!lastParams) return;
    const { d, n, alpha, testType, tails } = lastParams;
    const { ctx, width, height } = fitCanvas(canvas);

    const shift = Math.abs(d) * Math.sqrt(n / nFactorFor(testType));
    const zAlpha = criticalZ(alpha, tails);
    const xMin = Math.min(-4, shift - 4);
    const xMax = Math.max(4, shift + 4);

    const step = 0.05;
    const points = [];
    for (let x = xMin; x <= xMax + 1e-9; x += step) points.push(x);

    const h0 = points.map((x) => normalPDF(x));
    const h1 = points.map((x) => normalPDF(x - shift));
    const yMax = Math.max(...h0, ...h1) * 1.15;

    const { sx, sy } = scaleFns(width, height, xMin, xMax, 0, yMax);

    const xTickStep = niceStep(xMax - xMin, 6);
    const xTicks = [];
    for (let t = Math.ceil(xMin / xTickStep) * xTickStep; t <= xMax; t += xTickStep) {
      xTicks.push(Math.round(t * 100) / 100);
    }
    const yTicks = [0, yMax / 2, yMax];

    drawAxes(ctx, width, height, xTicks, yTicks, sx, sy, 'Standardized effect (z units)', 'Density');

    // Rejection region fill (under H0 curve, x >= zAlpha).
    ctx.beginPath();
    let started = false;
    points.forEach((x, i) => {
      if (x < zAlpha) return;
      const px = sx(x);
      const py = sy(h0[i]);
      if (!started) {
        ctx.moveTo(sx(zAlpha), sy(0));
        ctx.lineTo(px, py);
        started = true;
      } else {
        ctx.lineTo(px, py);
      }
    });
    if (started) {
      ctx.lineTo(sx(xMax), sy(0));
      ctx.closePath();
      ctx.fillStyle = COLORS.reject;
      ctx.fill();
    }

    // Critical value marker.
    ctx.strokeStyle = COLORS.refLine;
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(sx(zAlpha), sy(0));
    ctx.lineTo(sx(zAlpha), sy(yMax));
    ctx.stroke();
    ctx.setLineDash([]);

    function drawCurve(values, color) {
      ctx.beginPath();
      points.forEach((x, i) => {
        const px = sx(x);
        const py = sy(values[i]);
        if (i === 0) ctx.moveTo(px, py);
        else ctx.lineTo(px, py);
      });
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.stroke();
    }

    drawCurve(h0, COLORS.h0);
    drawCurve(h1, COLORS.h1);

    drawLegend(ctx, width, [
      { color: COLORS.h0, label: 'H0 (null)' },
      { color: COLORS.h1, label: 'H1 (true effect)' },
      { color: COLORS.reject, label: 'Rejection region' },
    ]);
  }

  function update(params) {
    lastParams = params;
    draw();
  }

  window.addEventListener('resize', draw);

  return { update };
}

function createPowerCurveChart(canvas) {
  let lastParams = null;

  function draw() {
    if (!lastParams) return;
    const { d, alpha, testType, tails, currentN, computePower } = lastParams;
    const { ctx, width, height } = fitCanvas(canvas);

    const maxN = Math.max(200, Math.ceil(currentN * 1.5));
    const nStep = Math.max(1, Math.round(maxN / 80));
    const ns = [];
    for (let n = nStep; n <= maxN; n += nStep) ns.push(n);

    const powers = ns.map((n) => computePower({ d, n, alpha, testType, tails }));
    const { sx, sy } = scaleFns(width, height, 0, maxN, 0, 1);

    const xTickStep = niceStep(maxN, 6);
    const xTicks = [];
    for (let t = 0; t <= maxN; t += xTickStep) xTicks.push(Math.round(t));
    const yTicks = [0, 0.2, 0.4, 0.6, 0.8, 1.0];

    drawAxes(ctx, width, height, xTicks, yTicks, sx, sy, 'N per group', 'Power');

    // 0.80 reference line.
    ctx.strokeStyle = COLORS.refLine;
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(sx(0), sy(0.8));
    ctx.lineTo(sx(maxN), sy(0.8));
    ctx.stroke();
    ctx.setLineDash([]);

    ctx.beginPath();
    ns.forEach((n, i) => {
      const px = sx(n);
      const py = sy(powers[i]);
      if (i === 0) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    });
    ctx.strokeStyle = COLORS.h1;
    ctx.lineWidth = 2;
    ctx.stroke();

    const currentPower = computePower({ d, n: currentN, alpha, testType, tails });
    ctx.beginPath();
    ctx.fillStyle = COLORS.point;
    ctx.arc(sx(currentN), sy(currentPower), 5, 0, Math.PI * 2);
    ctx.fill();

    drawLegend(ctx, width, [
      { color: COLORS.h1, label: 'Power vs N' },
      { color: COLORS.point, label: 'Current N' },
    ]);
  }

  function update(params) {
    lastParams = params;
    draw();
  }

  window.addEventListener('resize', draw);

  return { update };
}

window.PowerLabCharts = { createDistributionChart, createPowerCurveChart };

})();
