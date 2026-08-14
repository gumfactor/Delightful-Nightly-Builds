/**
 * Minimal hand-drawn Canvas 2D line-chart helper. No external charting
 * library. Used for the live rolling dB chart, a session's own mini chart,
 * and the cross-session trend chart.
 */

function clearCanvas(ctx, width, height) {
  ctx.clearRect(0, 0, width, height);
}

/**
 * Draw a line chart of {t, db} points into a canvas 2D context.
 * options: { minDb, maxDb, zoneBands: [{maxDb, color}], lineColor, padding }
 */
function drawDbLineChart(canvas, points, options) {
  const opts = options || {};
  const ctx = canvas.getContext('2d');
  const width = canvas.width;
  const height = canvas.height;
  const padding = opts.padding != null ? opts.padding : 24;
  const minDb = opts.minDb != null ? opts.minDb : 30;
  const maxDb = opts.maxDb != null ? opts.maxDb : 100;
  const lineColor = opts.lineColor || '#38bdf8';

  clearCanvas(ctx, width, height);

  const plotW = width - padding * 2;
  const plotH = height - padding * 2;

  // background zone bands (quiet/moderate/loud/hazardous), drawn behind the line
  if (opts.zoneBands) {
    let prevDb = minDb;
    for (const band of opts.zoneBands) {
      const bandTopDb = Math.min(band.maxDb, maxDb);
      const yTop = padding + plotH * (1 - (bandTopDb - minDb) / (maxDb - minDb));
      const yBottom = padding + plotH * (1 - (prevDb - minDb) / (maxDb - minDb));
      ctx.fillStyle = band.color;
      ctx.globalAlpha = 0.12;
      ctx.fillRect(padding, Math.max(padding, yTop), plotW, Math.max(0, yBottom - Math.max(padding, yTop)));
      ctx.globalAlpha = 1;
      prevDb = band.maxDb;
      if (prevDb >= maxDb) break;
    }
  }

  // axes
  ctx.strokeStyle = 'rgba(148, 163, 184, 0.4)';
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(padding, padding);
  ctx.lineTo(padding, height - padding);
  ctx.lineTo(width - padding, height - padding);
  ctx.stroke();

  if (!points || points.length === 0) return;

  const minT = points[0].t;
  const maxT = points[points.length - 1].t;
  const tRange = Math.max(maxT - minT, 1e-6);

  ctx.strokeStyle = lineColor;
  ctx.lineWidth = 2;
  ctx.beginPath();
  points.forEach((p, i) => {
    const x = padding + ((p.t - minT) / tRange) * plotW;
    const clampedDb = Math.max(minDb, Math.min(maxDb, p.db));
    const y = padding + plotH * (1 - (clampedDb - minDb) / (maxDb - minDb));
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();
}

/** Draw a simple bar/line trend of one numeric value per session, oldest to newest. */
function drawTrendChart(canvas, values, options) {
  const opts = options || {};
  const ctx = canvas.getContext('2d');
  const width = canvas.width;
  const height = canvas.height;
  const padding = opts.padding != null ? opts.padding : 24;
  const minDb = opts.minDb != null ? opts.minDb : 30;
  const maxDb = opts.maxDb != null ? opts.maxDb : 100;

  clearCanvas(ctx, width, height);

  ctx.strokeStyle = 'rgba(148, 163, 184, 0.4)';
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(padding, padding);
  ctx.lineTo(padding, height - padding);
  ctx.lineTo(width - padding, height - padding);
  ctx.stroke();

  if (!values || values.length === 0) return;

  const plotW = width - padding * 2;
  const plotH = height - padding * 2;
  const step = values.length > 1 ? plotW / (values.length - 1) : 0;

  ctx.strokeStyle = opts.lineColor || '#a78bfa';
  ctx.lineWidth = 2;
  ctx.beginPath();
  values.forEach((v, i) => {
    const x = padding + step * i;
    const clamped = Math.max(minDb, Math.min(maxDb, v));
    const y = padding + plotH * (1 - (clamped - minDb) / (maxDb - minDb));
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
    ctx.fillStyle = opts.lineColor || '#a78bfa';
    ctx.beginPath();
    ctx.arc(x, y, 3, 0, Math.PI * 2);
    ctx.fill();
  });
  ctx.stroke();
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { drawDbLineChart, drawTrendChart, clearCanvas };
}
