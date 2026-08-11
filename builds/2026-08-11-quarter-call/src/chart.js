// Native Canvas 2D chart rendering. No external charting library.

function renderChart(canvas, points, opts) {
  opts = opts || {};
  const ctx = canvas.getContext('2d');
  const w = canvas.width;
  const h = canvas.height;
  ctx.clearRect(0, 0, w, h);
  if (!points || points.length === 0) return;

  const closes = points.map((p) => p.close);
  const min = Math.min(...closes);
  const max = Math.max(...closes);
  const pad = 20;
  const range = max - min || 1;
  const stepX = (w - pad * 2) / Math.max(points.length - 1, 1);
  const yFor = (close) => h - pad - ((close - min) / range) * (h - pad * 2);

  ctx.strokeStyle = opts.color || '#4fd1c5';
  ctx.lineWidth = 2;
  ctx.beginPath();
  points.forEach((p, i) => {
    const x = pad + i * stepX;
    const y = yFor(p.close);
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();
}

function renderRevealChart(canvas, trailingPoints, forwardPoints) {
  const ctx = canvas.getContext('2d');
  const w = canvas.width;
  const h = canvas.height;
  ctx.clearRect(0, 0, w, h);
  if (!trailingPoints || !forwardPoints || trailingPoints.length === 0 || forwardPoints.length === 0) return;

  const allCloses = trailingPoints.concat(forwardPoints).map((p) => p.close);
  const min = Math.min(...allCloses);
  const max = Math.max(...allCloses);
  const pad = 20;
  const range = max - min || 1;
  const totalPoints = trailingPoints.length + forwardPoints.length - 1; // shared decision point
  const stepX = (w - pad * 2) / Math.max(totalPoints, 1);
  const yFor = (close) => h - pad - ((close - min) / range) * (h - pad * 2);

  ctx.strokeStyle = '#8892a0';
  ctx.lineWidth = 2;
  ctx.beginPath();
  trailingPoints.forEach((p, i) => {
    const x = pad + i * stepX;
    const y = yFor(p.close);
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();

  const forwardUp = forwardPoints[forwardPoints.length - 1].close >= forwardPoints[0].close;
  ctx.strokeStyle = forwardUp ? '#48bb78' : '#f56565';
  ctx.beginPath();
  forwardPoints.forEach((p, i) => {
    const x = pad + (trailingPoints.length - 1 + i) * stepX;
    const y = yFor(p.close);
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();
}
