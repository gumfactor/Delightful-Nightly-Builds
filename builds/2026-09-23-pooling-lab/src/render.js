/*
 * Pooling Lab — chart rendering.
 *
 * Draws a per-group column chart on a native <canvas> 2D context:
 *   - a dashed horizontal line for the complete-pooling estimate (grand mean)
 *   - a hollow circle for the no-pooling (raw group mean) estimate
 *   - a filled circle for the partial-pooling (shrinkage) estimate
 *   - a connecting line between no-pooling and partial-pooling so the
 *     "pull" toward the grand mean is visually obvious
 *
 * No DOM dependency beyond the canvas element passed in, so this stays easy
 * to reason about; it is exercised indirectly through UI tests rather than
 * unit tests (unlike stats.js, drawing has no meaningful pure-function
 * assertions beyond "it ran without throwing").
 */
(function (global) {
  'use strict';

  const COLORS = {
    axis: 'var(--axis-color, #888)',
    completePooling: '#e07a5f',
    noPooling: '#81b29a',
    partialPooling: '#3d5a80',
    text: 'var(--text-color, #222)',
  };

  function drawChart(canvas, summary) {
    const ctx = canvas.getContext('2d');
    const dpr = global.devicePixelRatio || 1;
    const cssWidth = canvas.clientWidth || 600;
    const cssHeight = canvas.clientHeight || 320;
    canvas.width = Math.round(cssWidth * dpr);
    canvas.height = Math.round(cssHeight * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, cssWidth, cssHeight);

    const padding = { top: 20, right: 20, bottom: 40, left: 50 };
    const plotWidth = cssWidth - padding.left - padding.right;
    const plotHeight = cssHeight - padding.top - padding.bottom;

    const groups = summary.perGroup;
    if (groups.length === 0) return;

    const allValues = [];
    groups.forEach((g) => {
      allValues.push(g.noPooling, g.partialPooling, g.completePooling);
    });
    let min = Math.min.apply(null, allValues);
    let max = Math.max.apply(null, allValues);
    if (min === max) {
      min -= 1;
      max += 1;
    }
    const valueRange = max - min;
    const yMargin = valueRange * 0.15;
    min -= yMargin;
    max += yMargin;

    function yToPixel(v) {
      return padding.top + plotHeight * (1 - (v - min) / (max - min));
    }

    const slot = plotWidth / groups.length;

    // Resolve CSS custom properties against real computed colors so the
    // canvas (which cannot use CSS variables directly) still respects theme.
    const computed = global.getComputedStyle ? global.getComputedStyle(canvas) : null;
    const textColor = (computed && computed.color) || '#222';
    ctx.strokeStyle = textColor;
    ctx.fillStyle = textColor;
    ctx.font = '11px sans-serif';

    // Axis line
    ctx.globalAlpha = 0.4;
    ctx.beginPath();
    ctx.moveTo(padding.left, padding.top);
    ctx.lineTo(padding.left, padding.top + plotHeight);
    ctx.lineTo(padding.left + plotWidth, padding.top + plotHeight);
    ctx.stroke();
    ctx.globalAlpha = 1;

    // Complete-pooling reference line (grand mean is identical for every group).
    const grandY = yToPixel(summary.grandMean);
    ctx.save();
    ctx.setLineDash([6, 4]);
    ctx.strokeStyle = COLORS.completePooling;
    ctx.beginPath();
    ctx.moveTo(padding.left, grandY);
    ctx.lineTo(padding.left + plotWidth, grandY);
    ctx.stroke();
    ctx.restore();

    groups.forEach((g, i) => {
      const cx = padding.left + slot * (i + 0.5);
      const yNo = yToPixel(g.noPooling);
      const yPartial = yToPixel(g.partialPooling);

      // Connector between no-pooling and partial-pooling.
      ctx.strokeStyle = COLORS.partialPooling;
      ctx.globalAlpha = 0.6;
      ctx.beginPath();
      ctx.moveTo(cx, yNo);
      ctx.lineTo(cx, yPartial);
      ctx.stroke();
      ctx.globalAlpha = 1;

      // No-pooling: hollow circle.
      ctx.strokeStyle = COLORS.noPooling;
      ctx.beginPath();
      ctx.arc(cx, yNo, 5, 0, 2 * Math.PI);
      ctx.stroke();

      // Partial-pooling: filled circle.
      ctx.fillStyle = COLORS.partialPooling;
      ctx.beginPath();
      ctx.arc(cx, yPartial, 5, 0, 2 * Math.PI);
      ctx.fill();

      // Group label.
      ctx.fillStyle = textColor;
      ctx.textAlign = 'center';
      ctx.fillText('G' + g.id + ' (n=' + g.n + ')', cx, padding.top + plotHeight + 16);
    });

    ctx.textAlign = 'left';
  }

  global.PoolingRender = { drawChart };
})(typeof window !== 'undefined' ? window : globalThis);
