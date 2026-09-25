// Agent Relay — Canvas dependency-graph renderer. Pure layout math is
// dual-exported for testability; renderGraph itself needs a real <canvas>
// and only runs in the browser.

function computeLayout(tasks) {
  var taskById = {};
  tasks.forEach(function (t) {
    taskById[t.id] = t;
  });
  var layer = {};
  function getLayer(id) {
    if (layer.hasOwnProperty(id)) return layer[id];
    var t = taskById[id];
    var l = 0;
    t.deps.forEach(function (d) {
      var dl = getLayer(d);
      if (dl + 1 > l) l = dl + 1;
    });
    layer[id] = l;
    return l;
  }
  tasks.forEach(function (t) {
    getLayer(t.id);
  });

  var byLayer = {};
  tasks.forEach(function (t) {
    var l = layer[t.id];
    if (!byLayer[l]) byLayer[l] = [];
    byLayer[l].push(t.id);
  });

  var layerKeys = Object.keys(byLayer).map(Number);
  var numLayers = layerKeys.length ? Math.max.apply(null, layerKeys) + 1 : 0;
  var maxInLayer = 0;
  layerKeys.forEach(function (l) {
    if (byLayer[l].length > maxInLayer) maxInLayer = byLayer[l].length;
  });

  var positions = {};
  layerKeys.forEach(function (l) {
    var ids = byLayer[l];
    ids.forEach(function (id, idx) {
      positions[id] = { layer: l, indexInLayer: idx, countInLayer: ids.length };
    });
  });

  return { layer: layer, positions: positions, numLayers: numLayers, maxInLayer: maxInLayer };
}

var BOX_W = 136;
var BOX_H = 48;
var SPACING_X = 172;
var SPACING_Y = 66;
var PAD_X = 24;
var PAD_Y = 24;

function nodeCenter(layout, id, canvasHeight) {
  var pos = layout.positions[id];
  var cx = PAD_X + pos.layer * SPACING_X + BOX_W / 2;
  var layerBlockHeight = layout.maxInLayer * SPACING_Y;
  var thisLayerHeight = pos.countInLayer * SPACING_Y;
  var layerOffsetY = (layerBlockHeight - thisLayerHeight) / 2;
  var cy = PAD_Y + layerOffsetY + pos.indexInLayer * SPACING_Y + BOX_H / 2;
  return { x: cx, y: cy };
}

function canvasDimensions(layout) {
  var width = Math.max(200, PAD_X * 2 + Math.max(layout.numLayers, 1) * SPACING_X - (SPACING_X - BOX_W));
  var height = Math.max(120, PAD_Y * 2 + Math.max(layout.maxInLayer, 1) * SPACING_Y - (SPACING_Y - BOX_H));
  return { width: width, height: height };
}

var STATE_COLORS = {
  locked: { fill: "#2a2f3a", stroke: "#454c5c", text: "#8b93a5" },
  ready: { fill: "#1d3a52", stroke: "#4fa3e0", text: "#e8f2fc" },
  placed: { fill: "#1c3a2c", stroke: "#4caf7d", text: "#e3f7ec" }
};

function drawArrow(ctx, x1, y1, x2, y2, color) {
  ctx.strokeStyle = color;
  ctx.fillStyle = color;
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.moveTo(x1, y1);
  ctx.lineTo(x2, y2);
  ctx.stroke();

  var angle = Math.atan2(y2 - y1, x2 - x1);
  var headLen = 7;
  ctx.beginPath();
  ctx.moveTo(x2, y2);
  ctx.lineTo(x2 - headLen * Math.cos(angle - Math.PI / 6), y2 - headLen * Math.sin(angle - Math.PI / 6));
  ctx.lineTo(x2 - headLen * Math.cos(angle + Math.PI / 6), y2 - headLen * Math.sin(angle + Math.PI / 6));
  ctx.closePath();
  ctx.fill();
}

function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}

function truncateToWidth(ctx, text, maxWidth) {
  if (ctx.measureText(text).width <= maxWidth) return text;
  var truncated = text;
  while (truncated.length > 1 && ctx.measureText(truncated + "…").width > maxWidth) {
    truncated = truncated.slice(0, -1);
  }
  return truncated + "…";
}

// taskStateFn(taskId) -> "locked" | "ready" | "placed"
function renderGraph(canvas, tasks, taskStateFn) {
  var layout = computeLayout(tasks);
  var dims = canvasDimensions(layout);
  var dpr = (typeof window !== "undefined" && window.devicePixelRatio) || 1;

  canvas.width = Math.round(dims.width * dpr);
  canvas.height = Math.round(dims.height * dpr);
  canvas.style.width = dims.width + "px";
  canvas.style.height = dims.height + "px";

  var ctx = canvas.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, dims.width, dims.height);

  // Edges first, so node boxes sit on top of the arrows.
  tasks.forEach(function (t) {
    var to = nodeCenter(layout, t.id, dims.height);
    t.deps.forEach(function (depId) {
      var from = nodeCenter(layout, depId, dims.height);
      var color = taskStateFn(t.id) === "locked" ? "#454c5c" : "#6b93b5";
      drawArrow(ctx, from.x + BOX_W / 2, from.y, to.x - BOX_W / 2, to.y, color);
    });
  });

  tasks.forEach(function (t) {
    var c = nodeCenter(layout, t.id, dims.height);
    var state = taskStateFn(t.id);
    var colors = STATE_COLORS[state] || STATE_COLORS.locked;
    var x = c.x - BOX_W / 2;
    var y = c.y - BOX_H / 2;

    ctx.fillStyle = colors.fill;
    ctx.strokeStyle = colors.stroke;
    ctx.lineWidth = state === "ready" ? 2.5 : 1.5;
    roundRect(ctx, x, y, BOX_W, BOX_H, 8);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = colors.text;
    ctx.font = "12px system-ui, sans-serif";
    ctx.textBaseline = "middle";
    ctx.textAlign = "center";
    var nameLine = truncateToWidth(ctx, t.name, BOX_W - 12);
    ctx.fillText(nameLine, c.x, c.y - 8);
    ctx.font = "11px system-ui, sans-serif";
    ctx.fillText(t.duration + "m", c.x, c.y + 10);
  });
}

var Graph = {
  computeLayout: computeLayout,
  nodeCenter: nodeCenter,
  canvasDimensions: canvasDimensions,
  renderGraph: renderGraph
};

if (typeof module !== "undefined" && module.exports) {
  module.exports = Graph;
} else {
  window.Graph = Graph;
}
