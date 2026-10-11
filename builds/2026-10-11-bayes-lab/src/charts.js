/* SVG chart helpers. Only numbers and static labels are interpolated into markup. */
(function (root) {
  'use strict';

  const W = 640;
  const H = 280;
  const PAD = { l: 14, r: 14, t: 14, b: 34 };
  const Y_CAP = 25;

  const fmt = (v) => (Number.isFinite(v) ? v.toFixed(2) : '0');

  /**
   * series: [{ ys: number[], cls: 's0'|'s1'|'s2'|'s3', fill?: boolean }]
   * opts: { xmin, xmax, ticks: number[], bands?: [{lo,hi,cls}], vlines?: [{x,cls}], label }
   */
  function curveChart(series, opts) {
    const { xmin, xmax, ticks } = opts;
    const plotW = W - PAD.l - PAD.r;
    const plotH = H - PAD.t - PAD.b;
    let ymax = 0;
    series.forEach((s) => s.ys.forEach((y) => { if (Number.isFinite(y)) ymax = Math.max(ymax, Math.min(y, Y_CAP)); }));
    if (ymax <= 0) ymax = 1;
    ymax *= 1.08;
    const sx = (x) => PAD.l + ((x - xmin) / (xmax - xmin)) * plotW;
    const sy = (y) => PAD.t + plotH - (Math.min(Math.max(y, 0), ymax) / ymax) * plotH;
    const parts = [`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${opts.label}" class="chart">`];
    (opts.bands || []).forEach((band) => {
      const x0 = sx(Math.max(xmin, band.lo));
      const x1 = sx(Math.min(xmax, band.hi));
      parts.push(`<rect class="band ${band.cls}" x="${fmt(x0)}" y="${PAD.t}" width="${fmt(Math.max(0, x1 - x0))}" height="${plotH}"/>`);
    });
    parts.push(`<line class="axis" x1="${PAD.l}" y1="${PAD.t + plotH}" x2="${W - PAD.r}" y2="${PAD.t + plotH}"/>`);
    ticks.forEach((t) => {
      parts.push(`<line class="tick" x1="${fmt(sx(t))}" y1="${PAD.t + plotH}" x2="${fmt(sx(t))}" y2="${PAD.t + plotH + 5}"/>`);
      parts.push(`<text class="ticklabel" x="${fmt(sx(t))}" y="${H - 12}" text-anchor="middle">${t}</text>`);
    });
    series.forEach((s) => {
      const n = s.ys.length;
      const pts = s.ys.map((y, i) => `${fmt(sx(xmin + ((xmax - xmin) * i) / (n - 1)))},${fmt(sy(y))}`);
      if (s.fill) {
        parts.push(`<polygon class="area ${s.cls}" points="${fmt(sx(xmin))},${fmt(sy(0))} ${pts.join(' ')} ${fmt(sx(xmax))},${fmt(sy(0))}"/>`);
      }
      parts.push(`<polyline class="line ${s.cls}" points="${pts.join(' ')}"/>`);
    });
    (opts.vlines || []).forEach((v) => {
      parts.push(`<line class="vline ${v.cls}" x1="${fmt(sx(v.x))}" y1="${PAD.t}" x2="${fmt(sx(v.x))}" y2="${PAD.t + plotH}"/>`);
    });
    parts.push('</svg>');
    return parts.join('');
  }

  /** Sample a function on n evenly spaced points. */
  function sample(fn, xmin, xmax, n = 241) {
    const out = [];
    for (let i = 0; i < n; i++) out.push(fn(xmin + ((xmax - xmin) * i) / (n - 1)));
    return out;
  }

  /** Scale an array so its maximum becomes `max` (used to draw the likelihood next to densities). */
  function scaleTo(ys, max) {
    const peak = Math.max(...ys.filter(Number.isFinite));
    return peak > 0 ? ys.map((y) => (y / peak) * max) : ys;
  }

  /** 1000-dot natural-frequency grid. counts: {tp,fn,fp,tn} */
  function dotGrid(counts, cols = 40) {
    const order = [['tp', counts.tp], ['fp', counts.fp], ['fn', counts.fn], ['tn', counts.tn]];
    const total = counts.tp + counts.fn + counts.fp + counts.tn;
    const rows = Math.ceil(total / cols);
    const cell = 14;
    const parts = [`<svg viewBox="0 0 ${cols * cell} ${rows * cell}" role="img" aria-label="Population grid" class="dots">`];
    let i = 0;
    order.forEach(([kind, count]) => {
      for (let c = 0; c < count; c++, i++) {
        const cx = (i % cols) * cell + cell / 2;
        const cy = Math.floor(i / cols) * cell + cell / 2;
        parts.push(`<circle class="dot ${kind}" cx="${cx}" cy="${cy}" r="4.5"/>`);
      }
    });
    parts.push('</svg>');
    return parts.join('');
  }

  root.Charts = { curveChart, sample, scaleTo, dotGrid };
  if (typeof module !== 'undefined' && module.exports) module.exports = root.Charts;
})(typeof window !== 'undefined' ? window : globalThis);
