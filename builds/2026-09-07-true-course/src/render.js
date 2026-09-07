/* True Course — Canvas 2D drawing helpers. No external library. */
(function (global) {
  'use strict';

  var TC = global.TC || {};

  function clear(ctx, w, h) {
    ctx.clearRect(0, 0, w, h);
  }

  function bearingPoint(cx, cy, bearingDeg, length) {
    var rad = TC.toRad(bearingDeg);
    return {
      x: cx + length * Math.sin(rad),
      y: cy - length * Math.cos(rad),
    };
  }

  function drawArrow(ctx, cx, cy, bearingDeg, length, color, width) {
    var tip = bearingPoint(cx, cy, bearingDeg, length);
    ctx.save();
    ctx.strokeStyle = color;
    ctx.fillStyle = color;
    ctx.lineWidth = width || 3;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.lineTo(tip.x, tip.y);
    ctx.stroke();

    var headLen = 10;
    var angle = Math.atan2(tip.y - cy, tip.x - cx);
    ctx.beginPath();
    ctx.moveTo(tip.x, tip.y);
    ctx.lineTo(
      tip.x - headLen * Math.cos(angle - Math.PI / 6),
      tip.y - headLen * Math.sin(angle - Math.PI / 6)
    );
    ctx.lineTo(
      tip.x - headLen * Math.cos(angle + Math.PI / 6),
      tip.y - headLen * Math.sin(angle + Math.PI / 6)
    );
    ctx.closePath();
    ctx.fill();
    ctx.restore();
    return tip;
  }

  function drawCompassRose(ctx, cx, cy, r) {
    ctx.save();
    ctx.strokeStyle = '#3a5a7a';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.arc(cx, cy, r, 0, Math.PI * 2);
    ctx.stroke();

    ctx.fillStyle = '#9fb8cc';
    ctx.font = '12px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    var labels = { 0: 'N', 90: 'E', 180: 'S', 270: 'W' };
    Object.keys(labels).forEach(function (deg) {
      var p = bearingPoint(cx, cy, Number(deg), r + 14);
      ctx.fillText(labels[deg], p.x, p.y);
    });

    ctx.strokeStyle = '#2a4560';
    for (var d = 0; d < 360; d += 30) {
      var inner = bearingPoint(cx, cy, d, r - 6);
      var outer = bearingPoint(cx, cy, d, r);
      ctx.beginPath();
      ctx.moveTo(inner.x, inner.y);
      ctx.lineTo(outer.x, outer.y);
      ctx.stroke();
    }
    ctx.restore();
  }

  function drawSetDriftDiagram(canvas, puzzle, revealed, playerHeadingDeg) {
    var ctx = canvas.getContext('2d');
    var w = canvas.width;
    var h = canvas.height;
    clear(ctx, w, h);
    var cx = w / 2;
    var cy = h / 2;
    var r = Math.min(w, h) / 2 - 30;

    drawCompassRose(ctx, cx, cy, r);
    drawArrow(ctx, cx, cy, puzzle.params.trackDeg, r * 0.85, '#5fd0ff', 3);

    if (revealed) {
      drawArrow(ctx, cx, cy, puzzle.params.setDeg, r * 0.4, '#ff8a5c', 2);
    }
    if (typeof playerHeadingDeg === 'number' && !isNaN(playerHeadingDeg)) {
      drawArrow(ctx, cx, cy, playerHeadingDeg, r * 0.7, '#ffd85c', 2);
    }
  }

  function drawVesselDiagram(canvas, puzzle) {
    var ctx = canvas.getContext('2d');
    var w = canvas.width;
    var h = canvas.height;
    clear(ctx, w, h);
    var cx = w / 2;
    var cy = h / 2;
    var r = Math.min(w, h) / 2 - 40;

    drawCompassRose(ctx, cx, cy, r);

    // "You" at center, heading arrow.
    drawArrow(ctx, cx, cy, puzzle.params.yourHeadingDeg, r * 0.5, '#5fd0ff', 3);
    ctx.save();
    ctx.fillStyle = '#5fd0ff';
    ctx.font = 'bold 12px sans-serif';
    ctx.fillText('YOU', cx + 8, cy + 16);
    ctx.restore();

    // "Other" vessel positioned along the bearing-to-other line.
    var otherPos = bearingPoint(cx, cy, puzzle.params.bearingToOtherDeg, r * 0.85);
    ctx.save();
    ctx.strokeStyle = '#5a6a7a';
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.lineTo(otherPos.x, otherPos.y);
    ctx.stroke();
    ctx.restore();

    drawArrow(
      ctx,
      otherPos.x,
      otherPos.y,
      puzzle.params.otherHeadingDeg,
      r * 0.3,
      '#ff8a5c',
      3
    );
    ctx.save();
    ctx.fillStyle = '#ff8a5c';
    ctx.font = 'bold 12px sans-serif';
    ctx.fillText('OTHER', otherPos.x + 8, otherPos.y + 16);
    ctx.restore();
  }

  function drawTideCurve(canvas, puzzle, revealed, startTime) {
    var ctx = canvas.getContext('2d');
    var w = canvas.width;
    var h = canvas.height;
    clear(ctx, w, h);

    var padL = 40;
    var padR = 20;
    var padT = 20;
    var padB = 30;
    var plotW = w - padL - padR;
    var plotH = h - padT - padB;

    var p = puzzle.params;
    var minH = Math.min(p.h0, p.h1) - 0.3;
    var maxH = Math.max(p.h0, p.h1) + 0.3;

    function xFor(t) {
      return padL + ((t - p.t0) / (p.t1 - p.t0)) * plotW;
    }
    function yFor(height) {
      return padT + plotH - ((height - minH) / (maxH - minH)) * plotH;
    }

    ctx.save();
    ctx.strokeStyle = '#3a5a7a';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(padL, padT);
    ctx.lineTo(padL, padT + plotH);
    ctx.lineTo(padL + plotW, padT + plotH);
    ctx.stroke();

    // Tide curve.
    ctx.strokeStyle = '#5fd0ff';
    ctx.lineWidth = 2;
    ctx.beginPath();
    var steps = 60;
    for (var i = 0; i <= steps; i++) {
      var t = p.t0 + (i / steps) * (p.t1 - p.t0);
      var hgt = TC.tideHeight(t, p.t0, p.h0, p.t1, p.h1);
      var x = xFor(t);
      var y = yFor(hgt);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();

    // Required-height threshold line.
    ctx.strokeStyle = '#ff8a5c';
    ctx.setLineDash([5, 4]);
    ctx.beginPath();
    ctx.moveTo(padL, yFor(p.requiredHeight));
    ctx.lineTo(padL + plotW, yFor(p.requiredHeight));
    ctx.stroke();
    ctx.setLineDash([]);

    if (revealed && typeof startTime === 'number') {
      ctx.fillStyle = 'rgba(95, 208, 255, 0.18)';
      var xStart = xFor(startTime);
      ctx.fillRect(xStart, padT, padL + plotW - xStart, plotH);
      ctx.strokeStyle = '#ffd85c';
      ctx.setLineDash([]);
      ctx.beginPath();
      ctx.moveTo(xStart, padT);
      ctx.lineTo(xStart, padT + plotH);
      ctx.stroke();
    }

    ctx.fillStyle = '#9fb8cc';
    ctx.font = '11px sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText(TC.formatClock(p.t0), padL - 4, padT + plotH + 16);
    ctx.textAlign = 'right';
    ctx.fillText(TC.formatClock(p.t1), padL + plotW, padT + plotH + 16);
    ctx.restore();
  }

  function drawBuoy(canvas, color, shape) {
    var ctx = canvas.getContext('2d');
    var w = canvas.width;
    var h = canvas.height;
    clear(ctx, w, h);
    var cx = w / 2;
    var waterline = h * 0.72;

    ctx.save();
    ctx.strokeStyle = '#2a4560';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, waterline);
    ctx.lineTo(w, waterline);
    ctx.stroke();

    var fill = color === 'red' ? '#e05252' : '#3fae5c';
    ctx.fillStyle = fill;
    ctx.strokeStyle = '#141b22';
    ctx.lineWidth = 2;

    var bodyW = 46;
    var bodyH = 60;
    var bodyTop = waterline - bodyH;

    ctx.beginPath();
    ctx.rect(cx - bodyW / 2, bodyTop, bodyW, bodyH);
    ctx.fill();
    ctx.stroke();

    ctx.beginPath();
    if (shape === 'nun') {
      ctx.moveTo(cx - bodyW / 2, bodyTop);
      ctx.lineTo(cx, bodyTop - 34);
      ctx.lineTo(cx + bodyW / 2, bodyTop);
    } else {
      ctx.moveTo(cx - bodyW / 2, bodyTop);
      ctx.lineTo(cx - bodyW / 2 + 6, bodyTop - 20);
      ctx.lineTo(cx + bodyW / 2 - 6, bodyTop - 20);
      ctx.lineTo(cx + bodyW / 2, bodyTop);
    }
    ctx.closePath();
    ctx.fill();
    ctx.stroke();
    ctx.restore();
  }

  TC.render = {
    drawArrow: drawArrow,
    drawCompassRose: drawCompassRose,
    drawSetDriftDiagram: drawSetDriftDiagram,
    drawVesselDiagram: drawVesselDiagram,
    drawTideCurve: drawTideCurve,
    drawBuoy: drawBuoy,
  };

  global.TC = TC;
})(typeof window !== 'undefined' ? window : globalThis);
