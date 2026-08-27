/**
 * Regression Lab — UI controller. Classic script (no ES modules) so the
 * page opens directly via file://. Relies on window.RegressionMath,
 * window.RegressionDatasets, window.RegressionQuiz, window.RegressionAI
 * (all attached by their own scripts, loaded before this one).
 */

(function () {
  const M = window.RegressionMath;
  const D = window.RegressionDatasets;
  const Q = window.RegressionQuiz;
  const AI = window.RegressionAI;

  const MIN_FIT_POINTS = 3;
  const MIN_DIAG_POINTS = 4;
  const HIT_RADIUS_PX = 12;

  // ---------- State ----------

  let currentPresetKey = 'well-behaved';
  let points = D.PRESETS['well-behaved'].points.map((p) => ({ x: p.x, y: p.y }));
  let dragIndex = null;

  let quizSession = [];
  let quizIndex = 0;
  let quizScore = 0;
  let quizAnswered = false;
  let quizSeed = 20260827;

  // ---------- Coordinate transforms ----------

  function computeBounds(pts) {
    if (pts.length === 0) return { minX: 0, maxX: 10, minY: 0, maxY: 10 };
    const xs = pts.map((p) => p.x), ys = pts.map((p) => p.y);
    let minX = Math.min(...xs), maxX = Math.max(...xs);
    let minY = Math.min(...ys), maxY = Math.max(...ys);
    const padX = Math.max((maxX - minX) * 0.15, 1);
    const padY = Math.max((maxY - minY) * 0.15, 1);
    return { minX: minX - padX, maxX: maxX + padX, minY: minY - padY, maxY: maxY + padY };
  }

  function makeTransforms(bounds, canvas, margin) {
    margin = margin || 36;
    const w = canvas.width, h = canvas.height;
    const spanX = bounds.maxX - bounds.minX || 1;
    const spanY = bounds.maxY - bounds.minY || 1;
    const toPx = (dataX, dataY) => ({
      x: margin + ((dataX - bounds.minX) / spanX) * (w - 2 * margin),
      y: h - margin - ((dataY - bounds.minY) / spanY) * (h - 2 * margin),
    });
    const toData = (px, py) => ({
      x: bounds.minX + ((px - margin) / (w - 2 * margin)) * spanX,
      y: bounds.minY + ((h - margin - py) / (h - 2 * margin)) * spanY,
    });
    return { toPx, toData, margin };
  }

  function canvasPointFromEvent(canvas, evt) {
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const clientX = evt.touches ? evt.touches[0].clientX : evt.clientX;
    const clientY = evt.touches ? evt.touches[0].clientY : evt.clientY;
    return { x: (clientX - rect.left) * scaleX, y: (clientY - rect.top) * scaleY };
  }

  // ---------- Generic chart primitives ----------

  function clearCanvas(ctx, canvas) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
  }

  function drawAxes(ctx, canvas, bounds, transforms, xLabel, yLabel) {
    const { toPx, margin } = transforms;
    ctx.strokeStyle = '#2b3040';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(margin, margin);
    ctx.lineTo(margin, canvas.height - margin);
    ctx.lineTo(canvas.width - margin, canvas.height - margin);
    ctx.stroke();
    ctx.fillStyle = '#9aa2b1';
    ctx.font = '11px sans-serif';
    if (xLabel) ctx.fillText(xLabel, canvas.width / 2 - 20, canvas.height - 6);
    if (yLabel) {
      ctx.save();
      ctx.translate(10, canvas.height / 2 + 20);
      ctx.rotate(-Math.PI / 2);
      ctx.fillText(yLabel, 0, 0);
      ctx.restore();
    }
  }

  function drawHorizontalLine(ctx, transforms, bounds, yVal, color, dashed) {
    const p1 = transforms.toPx(bounds.minX, yVal);
    const p2 = transforms.toPx(bounds.maxX, yVal);
    ctx.strokeStyle = color;
    ctx.lineWidth = 1;
    if (dashed) ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(p1.x, p1.y);
    ctx.lineTo(p2.x, p2.y);
    ctx.stroke();
    ctx.setLineDash([]);
  }

  function drawDots(ctx, transforms, pts, color, radius) {
    ctx.fillStyle = color;
    pts.forEach(({ x, y }) => {
      const px = transforms.toPx(x, y);
      ctx.beginPath();
      ctx.arc(px.x, px.y, radius || 5, 0, Math.PI * 2);
      ctx.fill();
    });
  }

  // ---------- Fit tab rendering ----------

  function getScatterCanvas() {
    return document.getElementById('scatter-canvas');
  }

  function currentRegression() {
    if (points.length < MIN_FIT_POINTS) return null;
    try {
      return M.simpleLinearRegression(points.map((p) => p.x), points.map((p) => p.y));
    } catch (err) {
      return null;
    }
  }

  function drawScatter() {
    const canvas = getScatterCanvas();
    const ctx = canvas.getContext('2d');
    clearCanvas(ctx, canvas);
    const bounds = computeBounds(points);
    const transforms = makeTransforms(bounds, canvas);
    drawAxes(ctx, canvas, bounds, transforms, 'x', 'y');

    const reg = currentRegression();
    if (reg) {
      const x1 = bounds.minX, x2 = bounds.maxX;
      const y1 = reg.coefficients[0] + reg.coefficients[1] * x1;
      const y2 = reg.coefficients[0] + reg.coefficients[1] * x2;
      const p1 = transforms.toPx(x1, y1);
      const p2 = transforms.toPx(x2, y2);
      ctx.strokeStyle = '#5fb3ff';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(p1.x, p1.y);
      ctx.lineTo(p2.x, p2.y);
      ctx.stroke();
    }

    drawDots(ctx, transforms, points, '#e6e9ef', 6);
  }

  function renderFitStats() {
    const reg = currentRegression();
    const eq = document.getElementById('equation-display');
    const n = document.getElementById('stat-n');
    const b0 = document.getElementById('stat-b0');
    const b1 = document.getElementById('stat-b1');
    const r2 = document.getElementById('stat-r2');
    const adjr2 = document.getElementById('stat-adjr2');
    const seb1 = document.getElementById('stat-seb1');
    const tb1 = document.getElementById('stat-tb1');
    const pb1 = document.getElementById('stat-pb1');

    n.textContent = String(points.length);

    if (!reg) {
      eq.textContent = `ŷ = — (need at least ${MIN_FIT_POINTS} points)`;
      [b0, b1, r2, adjr2, seb1, tb1, pb1].forEach((el) => (el.textContent = '—'));
      return;
    }

    const [c0, c1] = reg.coefficients;
    eq.textContent = `ŷ = ${c0.toFixed(3)} ${c1 >= 0 ? '+' : '-'} ${Math.abs(c1).toFixed(3)}·x`;
    b0.textContent = c0.toFixed(4);
    b1.textContent = c1.toFixed(4);
    r2.textContent = reg.r2.toFixed(4);
    adjr2.textContent = Number.isFinite(reg.adjR2) ? reg.adjR2.toFixed(4) : '—';
    seb1.textContent = reg.se[1].toFixed(4);
    tb1.textContent = reg.tStats[1].toFixed(3);
    pb1.textContent = Number.isFinite(reg.pValues[1]) ? reg.pValues[1].toFixed(4) : '—';
  }

  function refreshFitTab() {
    drawScatter();
    renderFitStats();
    if (isDiagnosticsVisible()) renderDiagnosticsTab();
  }

  // ---------- Diagnostics tab ----------

  function isDiagnosticsVisible() {
    const panel = document.getElementById('panel-diagnostics');
    return panel && panel.classList.contains('active');
  }

  function drawResidualPlot(canvas, reg) {
    const ctx = canvas.getContext('2d');
    clearCanvas(ctx, canvas);
    const fittedYs = reg.fitted;
    const resPts = fittedYs.map((f, i) => ({ x: f, y: reg.residuals[i] }));
    const bounds = computeBounds(resPts);
    bounds.minY = Math.min(bounds.minY, -Math.abs(bounds.maxY));
    bounds.maxY = Math.max(bounds.maxY, Math.abs(bounds.minY));
    const transforms = makeTransforms(bounds, canvas);
    drawAxes(ctx, canvas, bounds, transforms, 'fitted', 'residual');
    drawHorizontalLine(ctx, transforms, bounds, 0, '#9aa2b1', true);
    drawDots(ctx, transforms, resPts, '#5fb3ff', 4);
  }

  function drawQQPlot(canvas, reg) {
    const ctx = canvas.getContext('2d');
    clearCanvas(ctx, canvas);
    const n = reg.stdResiduals.length;
    const sorted = [...reg.stdResiduals].sort((a, b) => a - b);
    const qqPts = sorted.map((sr, i) => ({
      x: M.normalQuantile((i + 0.5) / n),
      y: sr,
    }));
    const bounds = computeBounds(qqPts);
    const span = Math.max(Math.abs(bounds.minX), Math.abs(bounds.maxX), Math.abs(bounds.minY), Math.abs(bounds.maxY));
    const symBounds = { minX: -span, maxX: span, minY: -span, maxY: span };
    const transforms = makeTransforms(symBounds, canvas);
    drawAxes(ctx, canvas, symBounds, transforms, 'theoretical', 'sample');
    const p1 = transforms.toPx(-span, -span);
    const p2 = transforms.toPx(span, span);
    ctx.strokeStyle = '#9aa2b1';
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(p1.x, p1.y);
    ctx.lineTo(p2.x, p2.y);
    ctx.stroke();
    ctx.setLineDash([]);
    drawDots(ctx, transforms, qqPts, '#5fb3ff', 4);
  }

  function drawLeveragePlot(canvas, reg, threshold) {
    const ctx = canvas.getContext('2d');
    clearCanvas(ctx, canvas);
    const levPts = reg.hatValues.map((h, i) => ({ x: h, y: reg.cooksD[i] }));
    const bounds = computeBounds(levPts);
    bounds.minY = Math.min(bounds.minY, 0);
    bounds.minX = Math.min(bounds.minX, 0);
    const transforms = makeTransforms(bounds, canvas);
    drawAxes(ctx, canvas, bounds, transforms, 'leverage', "Cook's D");
    drawHorizontalLine(ctx, transforms, bounds, threshold, '#f87171', true);
    drawDots(ctx, transforms, levPts, '#5fb3ff', 4);
  }

  function currentDiagnostics() {
    if (points.length < MIN_DIAG_POINTS) return null;
    try {
      const diag = Q.diagnoseDataset(points);
      const threshold = 4 / points.length;
      return { ...diag, threshold };
    } catch (err) {
      return null;
    }
  }

  function renderDiagnosticsTab() {
    document.getElementById('diag-source-label').textContent =
      D.PRESETS[currentPresetKey] ? D.PRESETS[currentPresetKey].label : 'Custom';

    const diag = currentDiagnostics();
    const bpEl = document.getElementById('test-bp');
    const resetEl = document.getElementById('test-reset');
    const influenceEl = document.getElementById('test-influence');
    const normEl = document.getElementById('test-normality');
    const banner = document.getElementById('verdict-banner');

    ['residual-canvas', 'qq-canvas', 'leverage-canvas'].forEach((id) => {
      const c = document.getElementById(id);
      clearCanvas(c.getContext('2d'), c);
    });

    if (!diag) {
      bpEl.textContent = resetEl.textContent = influenceEl.textContent = normEl.textContent = '—';
      banner.textContent = `Add at least ${MIN_DIAG_POINTS} points on the Scatterplot & Fit tab to run diagnostics.`;
      banner.className = 'verdict-banner';
      return;
    }

    const { reg, bp, reset, verdict, maxCooksD, threshold } = diag;

    drawResidualPlot(document.getElementById('residual-canvas'), reg);
    drawQQPlot(document.getElementById('qq-canvas'), reg);
    drawLeveragePlot(document.getElementById('leverage-canvas'), reg, threshold);

    bpEl.textContent = bp.applicable === false
      ? 'not applicable — the fitted values are constant (the fit has zero slope)'
      : `slope=${bp.slope.toFixed(4)}, t=${bp.tStat.toFixed(3)}, p=${bp.pValue.toFixed(4)} — ${bp.significant ? 'SIGNIFICANT' : 'not significant'}`;
    resetEl.textContent = `b₂=${reset.b2.toFixed(4)}, t=${reset.tStat.toFixed(3)}, p=${reset.pValue.toFixed(4)} — ${reset.significant ? 'SIGNIFICANT' : 'not significant'}`;
    const maxIdx = reg.cooksD.indexOf(maxCooksD);
    influenceEl.textContent = `point ${maxIdx + 1}: Cook's D=${maxCooksD.toFixed(3)} (rule-of-thumb threshold ${threshold.toFixed(3)})`;
    const skew = M.skewness(reg.stdResiduals);
    const kurt = M.excessKurtosis(reg.stdResiduals);
    normEl.textContent = `skew=${skew.toFixed(3)}, excess kurtosis=${kurt.toFixed(3)}`;

    const verdictText = {
      outlier: `⚠ One point dominates Cook's Distance — likely a high-leverage outlier.`,
      'non-linear': `⚠ The RESET-style test is significant — the relationship likely isn't linear.`,
      heteroscedastic: `⚠ The Breusch-Pagan test is significant — error variance likely isn't constant.`,
      'well-behaved': `✓ No test came back significant and no point dominates influence — this fit looks sound.`,
    };
    banner.textContent = verdictText[verdict];
    banner.className = `verdict-banner flag-${verdict}`;

    banner.dataset.verdict = verdict;
  }

  // ---------- AI explanation ----------

  async function handleExplainClick() {
    const diag = currentDiagnostics();
    const explanationEl = document.getElementById('ai-explanation');
    const sourceEl = document.getElementById('ai-source');
    if (!diag) {
      explanationEl.textContent = `Add at least ${MIN_DIAG_POINTS} points first.`;
      sourceEl.textContent = '';
      return;
    }
    explanationEl.textContent = 'Thinking...';
    sourceEl.textContent = '';
    const apiKey = document.getElementById('api-key-input').value.trim();
    const context = {
      verdict: diag.verdict,
      bp: diag.bp,
      reset: diag.reset,
      maxCooksD: diag.maxCooksD,
      cooksThreshold: diag.threshold,
      r2: diag.reg.r2,
    };
    const result = await AI.explainDiagnostic(context, apiKey || null);
    explanationEl.textContent = result.text;
    sourceEl.textContent = result.source === 'ai' ? 'Generated by Claude Haiku.' : 'Deterministic template (no API key set, or the request failed).';
  }

  // ---------- Scatter drag / add / remove interactions ----------

  function findNearestPointIndex(canvas, pxPoint) {
    const bounds = computeBounds(points);
    const transforms = makeTransforms(bounds, canvas);
    let nearestIdx = -1;
    let nearestDist = Infinity;
    points.forEach((pt, i) => {
      const px = transforms.toPx(pt.x, pt.y);
      const d = Math.hypot(px.x - pxPoint.x, px.y - pxPoint.y);
      if (d < nearestDist) {
        nearestDist = d;
        nearestIdx = i;
      }
    });
    return nearestDist <= HIT_RADIUS_PX ? nearestIdx : -1;
  }

  function setupScatterInteractions() {
    const canvas = getScatterCanvas();

    canvas.addEventListener('mousedown', (evt) => {
      const px = canvasPointFromEvent(canvas, evt);
      const idx = findNearestPointIndex(canvas, px);
      if (idx >= 0) {
        dragIndex = idx;
      } else if (currentPresetKey === 'custom') {
        const bounds = computeBounds(points);
        const transforms = makeTransforms(bounds, canvas);
        const data = transforms.toData(px.x, px.y);
        points.push({ x: Math.round(data.x * 100) / 100, y: Math.round(data.y * 100) / 100 });
        refreshFitTab();
      }
    });

    window.addEventListener('mousemove', (evt) => {
      if (dragIndex === null) return;
      const px = canvasPointFromEvent(canvas, evt);
      const bounds = computeBounds(points);
      const transforms = makeTransforms(bounds, canvas);
      const data = transforms.toData(px.x, px.y);
      points[dragIndex] = { x: Math.round(data.x * 100) / 100, y: Math.round(data.y * 100) / 100 };
      refreshFitTab();
    });

    window.addEventListener('mouseup', () => {
      dragIndex = null;
    });

    canvas.addEventListener('dblclick', (evt) => {
      const px = canvasPointFromEvent(canvas, evt);
      const idx = findNearestPointIndex(canvas, px);
      if (idx >= 0) {
        points.splice(idx, 1);
        refreshFitTab();
      }
    });
  }

  function selectPreset(key) {
    currentPresetKey = key;
    points = D.PRESETS[key].points.map((p) => ({ x: p.x, y: p.y }));
    document.querySelectorAll('.preset-btn').forEach((btn) => {
      btn.classList.toggle('active', btn.dataset.preset === key);
    });
    document.getElementById('preset-description').textContent = D.PRESETS[key].description;
    refreshFitTab();
  }

  function setupPresetBar() {
    document.querySelectorAll('.preset-btn').forEach((btn) => {
      btn.addEventListener('click', () => selectPreset(btn.dataset.preset));
    });
    document.getElementById('clear-points-btn').addEventListener('click', () => {
      points = [];
      currentPresetKey = 'custom';
      document.querySelectorAll('.preset-btn').forEach((btn) => {
        btn.classList.toggle('active', btn.dataset.preset === 'custom');
      });
      document.getElementById('preset-description').textContent = D.PRESETS.custom.description;
      refreshFitTab();
    });
  }

  // ---------- Tabs ----------

  function setupTabs() {
    document.querySelectorAll('.tab-btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.tab-btn').forEach((b) => {
          b.classList.remove('active');
          b.setAttribute('aria-selected', 'false');
        });
        document.querySelectorAll('.tab-panel').forEach((p) => p.classList.remove('active'));
        btn.classList.add('active');
        btn.setAttribute('aria-selected', 'true');
        const panel = document.getElementById(`panel-${btn.dataset.tab}`);
        panel.classList.add('active');
        if (btn.dataset.tab === 'diagnostics') renderDiagnosticsTab();
        if (btn.dataset.tab === 'multicollinearity') renderMulticollinearityTab();
      });
    });
  }

  // ---------- Multicollinearity Lab ----------

  function renderMulticollinearityTab() {
    const slider = document.getElementById('corr-slider');
    const corr = Number(slider.value) / 100;
    document.getElementById('corr-value').textContent = corr.toFixed(2);

    const data = D.buildMulticollinearData(corr, 20);
    const vif = M.vifPair(data.x1, data.x2);
    const joint = M.multipleRegression(data.x1.map((v, i) => [v, data.x2[i]]), data.y);

    document.getElementById('mc-corr').textContent = vif.correlation.toFixed(4);
    document.getElementById('mc-vif').textContent = Number.isFinite(vif.vif) ? vif.vif.toFixed(2) : '∞';
    document.getElementById('mc-r2').textContent = joint.r2.toFixed(4);
    document.getElementById('mc-se1').textContent = joint.se[1].toFixed(4);
    document.getElementById('mc-se2').textContent = joint.se[2].toFixed(4);

    const canvas = document.getElementById('mc-scatter-canvas');
    const ctx = canvas.getContext('2d');
    clearCanvas(ctx, canvas);
    const scatterPts = data.x1.map((v, i) => ({ x: v, y: data.x2[i] }));
    const bounds = computeBounds(scatterPts);
    const transforms = makeTransforms(bounds, canvas);
    drawAxes(ctx, canvas, bounds, transforms, 'X1', 'X2');
    drawDots(ctx, transforms, scatterPts, '#5fb3ff', 4);
  }

  function setupMulticollinearityTab() {
    document.getElementById('corr-slider').addEventListener('input', renderMulticollinearityTab);
  }

  // ---------- Quiz ----------

  function loadQuizBest() {
    try {
      const raw = localStorage.getItem('regressionLabQuizBest');
      if (!raw) return null;
      return JSON.parse(raw);
    } catch (err) {
      return null;
    }
  }

  function saveQuizBest(score, total) {
    try {
      const prev = loadQuizBest();
      if (!prev || score > prev.best) {
        localStorage.setItem(
          'regressionLabQuizBest',
          JSON.stringify({ best: score, total, playedAt: new Date().toISOString() })
        );
      }
    } catch (err) {
      /* localStorage unavailable — non-fatal */
    }
  }

  function renderQuizBest() {
    const best = loadQuizBest();
    const el = document.getElementById('quiz-best');
    el.textContent = best ? `Best score so far: ${best.best} / ${best.total}` : '';
  }

  function startQuiz() {
    quizSession = Q.buildQuizSession(quizSeed);
    quizSeed += 1;
    quizIndex = 0;
    quizScore = 0;
    document.getElementById('quiz-intro').classList.add('hidden');
    document.getElementById('quiz-results').classList.add('hidden');
    document.getElementById('quiz-active').classList.remove('hidden');
    renderQuizQuestion();
  }

  function renderQuizQuestion() {
    quizAnswered = false;
    const q = quizSession[quizIndex];
    document.getElementById('quiz-progress').textContent = `Question ${quizIndex + 1} of ${quizSession.length} — Score: ${quizScore}`;
    document.getElementById('quiz-prompt').textContent = q.prompt;
    document.getElementById('quiz-feedback').textContent = '';
    document.getElementById('quiz-next-btn').classList.add('hidden');

    const chartCard = document.getElementById('quiz-chart-card');
    if (q.type === 'diagnose') {
      chartCard.classList.remove('hidden');
      drawResidualPlot(document.getElementById('quiz-canvas'), q.reg);
    } else {
      chartCard.classList.add('hidden');
    }

    const optionsEl = document.getElementById('quiz-options');
    optionsEl.innerHTML = '';
    q.options.forEach((optText, idx) => {
      const btn = document.createElement('button');
      btn.className = 'quiz-option-btn';
      btn.textContent = optText;
      btn.dataset.testid = `quiz-option-${idx}`;
      btn.addEventListener('click', () => handleQuizAnswer(idx));
      optionsEl.appendChild(btn);
    });
  }

  function handleQuizAnswer(chosenIdx) {
    if (quizAnswered) return;
    quizAnswered = true;
    const q = quizSession[quizIndex];
    const correct = chosenIdx === q.correctIndex;
    if (correct) quizScore += 1;

    const buttons = document.querySelectorAll('#quiz-options .quiz-option-btn');
    buttons.forEach((btn, idx) => {
      btn.disabled = true;
      if (idx === q.correctIndex) btn.classList.add('correct');
      else if (idx === chosenIdx) btn.classList.add('incorrect');
    });

    let feedback = correct ? 'Correct. ' : 'Not quite. ';
    if (q.type === 'concept') {
      feedback += q.explanation;
    } else {
      const threshold = 4 / q.points.length;
      feedback += AI.deterministicExplanation({
        verdict: q.verdict,
        bp: M.breuschPaganTest(q.reg.fitted, q.reg.residuals),
        reset: M.resetTest(q.points.map((p) => p.x), q.points.map((p) => p.y)),
        maxCooksD: Math.max(...q.reg.cooksD),
        cooksThreshold: threshold,
        r2: q.reg.r2,
      });
    }
    document.getElementById('quiz-feedback').textContent = feedback;
    document.getElementById('quiz-next-btn').classList.remove('hidden');
  }

  function handleQuizNext() {
    quizIndex += 1;
    if (quizIndex >= quizSession.length) {
      finishQuiz();
    } else {
      renderQuizQuestion();
    }
  }

  function finishQuiz() {
    document.getElementById('quiz-active').classList.add('hidden');
    document.getElementById('quiz-results').classList.remove('hidden');
    document.getElementById('quiz-score').textContent = `${quizScore} / ${quizSession.length}`;
    const pct = (quizScore / quizSession.length) * 100;
    let msg;
    if (pct >= 90) msg = 'Excellent — you\'re reading these diagnostics like a reviewer.';
    else if (pct >= 70) msg = 'Solid grasp of the core diagnostics.';
    else if (pct >= 50) msg = 'Getting there — revisit the Diagnostics tab and try again.';
    else msg = 'Worth another pass through the Diagnostics tab before retrying.';
    document.getElementById('quiz-summary').textContent = msg;
    saveQuizBest(quizScore, quizSession.length);
    renderQuizBest();
  }

  function setupQuiz() {
    document.getElementById('start-quiz-btn').addEventListener('click', startQuiz);
    document.getElementById('quiz-next-btn').addEventListener('click', handleQuizNext);
    document.getElementById('quiz-retry-btn').addEventListener('click', () => {
      document.getElementById('quiz-results').classList.add('hidden');
      document.getElementById('quiz-intro').classList.remove('hidden');
    });
    renderQuizBest();
  }

  // ---------- Init ----------

  function init() {
    setupTabs();
    setupPresetBar();
    setupScatterInteractions();
    setupMulticollinearityTab();
    setupQuiz();
    document.getElementById('explain-btn').addEventListener('click', handleExplainClick);

    document.getElementById('preset-description').textContent = D.PRESETS[currentPresetKey].description;
    document.querySelectorAll('.preset-btn').forEach((btn) => {
      btn.classList.toggle('active', btn.dataset.preset === currentPresetKey);
    });
    refreshFitTab();
    renderMulticollinearityTab();

    // Exposed for Playwright tests only — read-only introspection, no
    // behavior is altered by its presence.
    window.__testHooks = {
      getPoints: () => points.map((p) => ({ ...p })),
      setPoints: (pts) => {
        points = pts.map((p) => ({ x: p.x, y: p.y }));
        refreshFitTab();
      },
      getBounds: () => computeBounds(points),
      makeTransforms: (bounds, canvas) => makeTransforms(bounds, canvas),
      getCurrentPresetKey: () => currentPresetKey,
    };
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
