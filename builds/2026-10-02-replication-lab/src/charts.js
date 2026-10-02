/* Minimal canvas charts for Replication Lab. Colours come from CSS custom properties. */
(function (root) {
  'use strict';

  function palette() {
    const style = getComputedStyle(document.documentElement);
    const read = (name) => style.getPropertyValue(name).trim();
    return { text: read('--text'), muted: read('--muted'), line: read('--line'), accent: read('--accent'), bad: read('--bad'), good: read('--good'), warn: read('--warn') };
  }

  function prepare(canvas) {
    const ratio = window.devicePixelRatio || 1;
    const width = canvas.clientWidth || 320;
    const height = canvas.clientHeight || 240;
    canvas.width = Math.round(width * ratio);
    canvas.height = Math.round(height * ratio);
    const ctx = canvas.getContext('2d');
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    ctx.clearRect(0, 0, width, height);
    ctx.font = '12px system-ui, sans-serif';
    return { ctx, width, height, colors: palette() };
  }

  function frame(env, xMin, xMax, yMax, xLabel, yLabel, xFormat) {
    const { ctx, width, height, colors } = env;
    const box = { left: 44, right: 10, top: 12, bottom: 34 };
    const plotW = width - box.left - box.right;
    const plotH = height - box.top - box.bottom;
    const xOf = (value) => box.left + ((value - xMin) / (xMax - xMin)) * plotW;
    const yOf = (value) => box.top + plotH - (value / yMax) * plotH;
    ctx.strokeStyle = colors.line;
    ctx.fillStyle = colors.muted;
    ctx.lineWidth = 1;
    ctx.textAlign = 'right';
    for (let i = 0; i <= 4; i++) {
      const value = (yMax * i) / 4;
      ctx.beginPath(); ctx.moveTo(box.left, yOf(value)); ctx.lineTo(width - box.right, yOf(value)); ctx.stroke();
      ctx.fillText(yLabel(value), box.left - 5, yOf(value) + 4);
    }
    ctx.textAlign = 'center';
    for (let i = 0; i <= 4; i++) {
      const value = xMin + ((xMax - xMin) * i) / 4;
      ctx.fillText(xFormat ? xFormat(value) : String(Math.round(value * 100) / 100), xOf(value), height - box.bottom + 16);
    }
    ctx.fillText(xLabel, box.left + plotW / 2, height - 4);
    return { box, plotW, plotH, xOf, yOf };
  }

  function vline(env, geo, x, color, label, dash, row) {
    const { ctx } = env;
    ctx.save();
    ctx.strokeStyle = color; ctx.fillStyle = color; ctx.lineWidth = 2;
    if (dash) ctx.setLineDash([5, 4]);
    ctx.beginPath(); ctx.moveTo(geo.xOf(x), geo.box.top); ctx.lineTo(geo.xOf(x), geo.box.top + geo.plotH); ctx.stroke();
    ctx.setLineDash([]);
    ctx.textAlign = geo.xOf(x) > env.width - 90 ? 'right' : 'left';
    ctx.fillText(label, geo.xOf(x) + (ctx.textAlign === 'left' ? 4 : -4), geo.box.top + 12 + row * 14);
    ctx.restore();
  }

  function drawHistogram(canvas, hist, opts) {
    const env = prepare(canvas);
    const total = hist.counts.reduce((sum, count) => sum + count, 0) || 1;
    const shares = hist.counts.map((count) => count / total);
    const yMax = Math.max(0.05, Math.ceil(Math.max(...shares) * 20) / 20);
    const geo = frame(env, hist.min, hist.max, yMax, opts.xLabel, (v) => Math.round(v * 100) + '%', opts.xFormat);
    shares.forEach((share, index) => {
      const x0 = geo.xOf(hist.min + index * hist.width);
      const x1 = geo.xOf(hist.min + (index + 1) * hist.width);
      const highlight = opts.highlight && opts.highlight(hist.min + (index + 0.5) * hist.width);
      env.ctx.fillStyle = highlight ? env.colors.bad : env.colors.accent;
      env.ctx.globalAlpha = 0.85;
      env.ctx.fillRect(x0 + 1, geo.yOf(share), Math.max(1, x1 - x0 - 2), geo.box.top + geo.plotH - geo.yOf(share));
      env.ctx.globalAlpha = 1;
    });
    (opts.lines || []).forEach((line, row) => vline(env, geo, line.x, env.colors[line.color || 'text'] || line.color, line.label, line.dash, row));
  }

  function drawLines(canvas, spec) {
    const env = prepare(canvas);
    const xs = spec.series.flatMap((series) => series.points.map((point) => point[0]));
    const xMin = Math.min(...xs);
    const xMax = Math.max(...xs);
    const geo = frame(env, xMin, xMax, spec.yMax, spec.xLabel, (v) => Math.round(v * 100) + '%', spec.xFormat);
    spec.series.forEach((series) => {
      env.ctx.strokeStyle = env.colors[series.color]; env.ctx.lineWidth = 2.5;
      env.ctx.setLineDash(series.dash ? [6, 4] : []);
      env.ctx.beginPath();
      series.points.forEach((point, index) => {
        const px = geo.xOf(point[0]); const py = geo.yOf(Math.min(point[1], spec.yMax));
        if (index === 0) env.ctx.moveTo(px, py); else env.ctx.lineTo(px, py);
      });
      env.ctx.stroke();
      env.ctx.setLineDash([]);
    });
    spec.series.forEach((series, index) => {
      env.ctx.fillStyle = env.colors[series.color];
      env.ctx.textAlign = 'left';
      env.ctx.fillText(series.label, geo.box.left + 8, geo.box.top + 14 + index * 15);
    });
  }

  function drawBars(canvas, bars, yMax) {
    const env = prepare(canvas);
    const { ctx, colors } = env;
    const box = { left: 44, right: 10, top: 14, bottom: 52 };
    const plotW = env.width - box.left - box.right;
    const plotH = env.height - box.top - box.bottom;
    const yOf = (value) => box.top + plotH - (Math.min(value, yMax) / yMax) * plotH;
    ctx.strokeStyle = colors.line; ctx.fillStyle = colors.muted; ctx.textAlign = 'right';
    for (let i = 0; i <= 4; i++) {
      const value = (yMax * i) / 4;
      ctx.beginPath(); ctx.moveTo(box.left, yOf(value)); ctx.lineTo(env.width - box.right, yOf(value)); ctx.stroke();
      ctx.fillText(Math.round(value * 100) + '%', box.left - 5, yOf(value) + 4);
    }
    const slot = plotW / bars.length;
    bars.forEach((bar, index) => {
      const x = box.left + index * slot + slot * 0.18;
      ctx.fillStyle = colors[bar.color]; ctx.globalAlpha = 0.9;
      ctx.fillRect(x, yOf(bar.value), slot * 0.64, box.top + plotH - yOf(bar.value));
      ctx.globalAlpha = 1;
      ctx.fillStyle = colors.text; ctx.textAlign = 'center';
      ctx.fillText(Math.round(bar.value * 1000) / 10 + '%', x + slot * 0.32, yOf(bar.value) - 4);
      ctx.fillStyle = colors.muted;
      bar.label.split('\n').forEach((part, row) => ctx.fillText(part, x + slot * 0.32, env.height - box.bottom + 16 + row * 14));
    });
  }

  function drawDensities(canvas, spec) {
    const env = prepare(canvas);
    const geo = frame(env, 0, 1, spec.yMax, 'true success rate', (v) => (Math.round(v * 10) / 10).toString());
    const steps = 200;
    spec.curves.forEach((curve, index) => {
      env.ctx.strokeStyle = env.colors[curve.color]; env.ctx.lineWidth = 2.5;
      env.ctx.setLineDash(curve.dash ? [6, 4] : []);
      env.ctx.beginPath();
      for (let i = 1; i < steps; i++) {
        const x = i / steps;
        const y = Math.min(curve.pdf(x), spec.yMax);
        if (i === 1) env.ctx.moveTo(geo.xOf(x), geo.yOf(y)); else env.ctx.lineTo(geo.xOf(x), geo.yOf(y));
      }
      env.ctx.stroke(); env.ctx.setLineDash([]);
      env.ctx.fillStyle = env.colors[curve.color]; env.ctx.textAlign = 'left';
      env.ctx.fillText(curve.label, geo.box.left + 8, geo.box.top + 14 + index * 15);
    });
    (spec.shade || []).forEach((band) => {
      env.ctx.fillStyle = env.colors[band.color]; env.ctx.globalAlpha = 0.18;
      env.ctx.fillRect(geo.xOf(band.from), geo.box.top, geo.xOf(band.to) - geo.xOf(band.from), geo.plotH);
      env.ctx.globalAlpha = 1;
    });
  }

  root.Charts = { drawHistogram, drawLines, drawBars, drawDensities };
})(window);
