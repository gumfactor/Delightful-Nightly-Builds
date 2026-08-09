/*
 * Portfolio Lab — UI wiring. Depends on math.js (PortfolioMath) and
 * data.js (window.PORTFOLIO_DATA) being loaded first. Classic script,
 * no ES modules, so it works when index.html is opened via file://.
 */
(function () {
  'use strict';

  var DATA = window.PORTFOLIO_DATA;
  var STORAGE_KEY = 'portfolioLabState';
  var QUIZ_RISK_FREE = 0.02;

  var rngSeed = (typeof window.__TEST_SEED__ !== 'undefined')
    ? window.__TEST_SEED__
    : Math.floor(Math.random() * 4294967295);
  var cloudRng = PortfolioMath.mulberry32(rngSeed >>> 0);
  var quizRng = PortfolioMath.mulberry32((rngSeed ^ 0x9e3779b9) >>> 0);

  var els = {};
  var meanVec = null;
  var frontierCoeffs = null;
  var frontierReturnRange = null;
  var gmv = null;
  var currentCloud = [];
  var quizRound = null; // { portfolios: [{tickerA, tickerB, weightA, return, volatility, sharpe}, ...], correctIndex }

  function $(id) { return document.getElementById(id); }

  function objectToVec(obj, tickers) {
    return tickers.map(function (t) { return obj[t]; });
  }

  function formatPct(x, decimals) {
    if (x === null || x === undefined || isNaN(x)) return '—';
    return (x * 100).toFixed(decimals === undefined ? 1 : decimals) + '%';
  }

  function formatNum(x, decimals) {
    if (x === null || x === undefined || isNaN(x)) return '—';
    return x.toFixed(decimals === undefined ? 2 : decimals);
  }

  // ---- localStorage state -------------------------------------------
  function defaultState() {
    return { quiz: { attempts: 0, correct: 0, streak: 0, bestStreak: 0 }, lastPair: null };
  }

  function loadState() {
    try {
      var raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return defaultState();
      var parsed = JSON.parse(raw);
      var merged = defaultState();
      if (parsed && parsed.quiz) merged.quiz = Object.assign(merged.quiz, parsed.quiz);
      if (parsed && parsed.lastPair) merged.lastPair = parsed.lastPair;
      return merged;
    } catch (e) {
      return defaultState();
    }
  }

  function saveState() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch (e) {
      // localStorage unavailable (private mode, quota, etc.) — degrade silently
    }
  }

  var state = loadState();

  // ---- Init -------------------------------------------------------------
  document.addEventListener('DOMContentLoaded', init);

  function init() {
    cacheEls();
    if (!DATA || !DATA.tickers || DATA.tickers.length < 2) {
      showOnboarding();
      return;
    }
    showApp();

    meanVec = objectToVec(DATA.mean_return, DATA.tickers);
    try {
      frontierCoeffs = PortfolioMath.frontierCoefficients(meanVec, DATA.cov_matrix);
      gmv = PortfolioMath.globalMinVariancePortfolio(meanVec, DATA.cov_matrix, frontierCoeffs);
      computeFrontierReturnRange();
    } catch (err) {
      showFrontierError(err);
      return;
    }

    renderDataMeta();
    setupTabs();
    setupExplainer();
    setupFrontier();
    setupSharpe();
    setupCorrelation();
    setupQuiz();
  }

  function cacheEls() {
    [
      'onboarding', 'app', 'data-meta',
      'asset-a', 'asset-b', 'mix-weight', 'mix-weight-value', 'mixer-canvas',
      'mixer-corr', 'mixer-return', 'mixer-vol', 'mixer-naive-vol',
      'explain-mixer', 'explain-mixer-output',
      'resample-cloud', 'frontier-canvas', 'gmv-return', 'gmv-vol',
      'explain-frontier', 'explain-frontier-output',
      'riskfree-slider', 'riskfree-value', 'sharpe-canvas',
      'tangency-return', 'tangency-vol', 'tangency-sharpe', 'gmv-sharpe',
      'corr-heatmap',
      'quiz-option-0', 'quiz-option-1', 'quiz-feedback', 'quiz-next',
      'quiz-attempts', 'quiz-correct', 'quiz-streak', 'quiz-best-streak',
      'api-key-input', 'footer-note',
    ].forEach(function (id) {
      els[id] = $(id);
    });
  }

  function showOnboarding() {
    els.onboarding.hidden = false;
    els.app.hidden = true;
  }

  function showApp() {
    els.onboarding.hidden = true;
    els.app.hidden = false;
  }

  function showFrontierError(err) {
    els.app.hidden = true;
    els.onboarding.hidden = false;
    els.onboarding.querySelector('.onboard-card').innerHTML = '';
    var h2 = document.createElement('h2');
    h2.textContent = 'Data problem';
    var p = document.createElement('p');
    p.textContent = 'The fetched dataset could not be used: ' + err.message + ' Try re-running fetch_data.py.';
    els.onboarding.querySelector('.onboard-card').appendChild(h2);
    els.onboarding.querySelector('.onboard-card').appendChild(p);
  }

  function renderDataMeta() {
    els['data-meta'].textContent =
      'Real data as of ' + DATA.generated_at + ' · ' + DATA.years + ' year(s) · ' + DATA.tickers.length + ' assets';
    els['footer-note'].textContent = 'with ' + DATA.tickers.length + ' real assets, refreshed ' + DATA.generated_at;
  }

  function computeFrontierReturnRange() {
    var maxMean = Math.max.apply(null, meanVec);
    var span = Math.max(maxMean - gmv.return, 0.05);
    frontierReturnRange = { min: gmv.return, max: gmv.return + span * 1.5 };
  }

  // ---- Tabs ---------------------------------------------------------
  function setupTabs() {
    var buttons = els.app.querySelectorAll('.tab-btn');
    buttons.forEach(function (btn) {
      btn.addEventListener('click', function () {
        activateTab(btn.getAttribute('data-tab'));
      });
    });
  }

  function activateTab(name) {
    els.app.querySelectorAll('.tab-btn').forEach(function (btn) {
      var active = btn.getAttribute('data-tab') === name;
      btn.setAttribute('aria-selected', active ? 'true' : 'false');
    });
    els.app.querySelectorAll('.tab-panel').forEach(function (panel) {
      panel.hidden = panel.id !== 'panel-' + name;
    });
  }

  // ---- Explainer tab --------------------------------------------------
  function setupExplainer() {
    DATA.tickers.forEach(function (t) {
      els['asset-a'].appendChild(makeOption(t));
      els['asset-b'].appendChild(makeOption(t));
    });

    var defaultA = DATA.tickers[0];
    var defaultB = DATA.tickers[1];
    if (state.lastPair && DATA.tickers.indexOf(state.lastPair[0]) !== -1 && DATA.tickers.indexOf(state.lastPair[1]) !== -1) {
      defaultA = state.lastPair[0];
      defaultB = state.lastPair[1];
    }
    els['asset-a'].value = defaultA;
    els['asset-b'].value = defaultB !== defaultA ? defaultB : DATA.tickers[1];

    els['asset-a'].addEventListener('change', onMixerInputsChanged);
    els['asset-b'].addEventListener('change', onMixerInputsChanged);
    els['mix-weight'].addEventListener('input', renderMixer);
    els['explain-mixer'].addEventListener('click', explainMixer);

    renderMixer();
  }

  function makeOption(ticker) {
    var opt = document.createElement('option');
    opt.value = ticker;
    var meta = DATA.meta && DATA.meta[ticker];
    opt.textContent = meta ? ticker + ' — ' + meta.name : ticker;
    return opt;
  }

  function onMixerInputsChanged() {
    state.lastPair = [els['asset-a'].value, els['asset-b'].value];
    saveState();
    renderMixer();
  }

  function currentMixerSelection() {
    var tickerA = els['asset-a'].value;
    var tickerB = els['asset-b'].value;
    var iA = DATA.tickers.indexOf(tickerA);
    var iB = DATA.tickers.indexOf(tickerB);
    var weightA = Number(els['mix-weight'].value) / 100;
    return { tickerA: tickerA, tickerB: tickerB, iA: iA, iB: iB, weightA: weightA };
  }

  function renderMixer() {
    var sel = currentMixerSelection();
    els['mix-weight-value'].textContent = Math.round(sel.weightA * 100) + '%';

    if (sel.iA === sel.iB) {
      els['mixer-corr'].textContent = 'n/a (same asset)';
      els['mixer-return'].textContent = formatPct(DATA.mean_return[sel.tickerA]);
      els['mixer-vol'].textContent = formatPct(DATA.volatility[sel.tickerA]);
      els['mixer-naive-vol'].textContent = formatPct(DATA.volatility[sel.tickerA]);
      drawMixerCurve(sel);
      return;
    }

    var meanA = DATA.mean_return[sel.tickerA];
    var meanB = DATA.mean_return[sel.tickerB];
    var covAA = DATA.cov_matrix[sel.iA][sel.iA];
    var covBB = DATA.cov_matrix[sel.iB][sel.iB];
    var covAB = DATA.cov_matrix[sel.iA][sel.iB];
    var corr = DATA.corr_matrix[sel.iA][sel.iB];

    var stats = PortfolioMath.twoAssetStats(meanA, meanB, covAA, covBB, covAB, sel.weightA);
    var volA = DATA.volatility[sel.tickerA];
    var volB = DATA.volatility[sel.tickerB];
    var naiveVol = sel.weightA * volA + (1 - sel.weightA) * volB;

    els['mixer-corr'].textContent = formatNum(corr, 2);
    els['mixer-return'].textContent = formatPct(stats.return);
    els['mixer-vol'].textContent = formatPct(stats.volatility);
    els['mixer-naive-vol'].textContent = formatPct(naiveVol);

    drawMixerCurve(sel);
  }

  function drawMixerCurve(sel) {
    var canvas = els['mixer-canvas'];
    var ctx = canvas.getContext('2d');
    var w = canvas.width;
    var h = canvas.height;
    ctx.clearRect(0, 0, w, h);

    var meanA = DATA.mean_return[sel.tickerA];
    var meanB = DATA.mean_return[sel.tickerB];
    var covAA = DATA.cov_matrix[sel.iA][sel.iA];
    var covBB = DATA.cov_matrix[sel.iB][sel.iB];
    var covAB = sel.iA === sel.iB ? covAA : DATA.cov_matrix[sel.iA][sel.iB];

    var points = [];
    for (var i = 0; i <= 50; i++) {
      var wA = i / 50;
      points.push(PortfolioMath.twoAssetStats(meanA, meanB, covAA, covBB, covAB, wA));
    }

    var margin = 46;
    var vols = points.map(function (p) { return p.volatility; });
    var rets = points.map(function (p) { return p.return; });
    var volMin = Math.min.apply(null, vols) * 0.9;
    var volMax = Math.max.apply(null, vols) * 1.1 || 0.01;
    var retMin = Math.min.apply(null, rets);
    var retMax = Math.max.apply(null, rets);
    var retPad = Math.max((retMax - retMin) * 0.15, 0.005);
    retMin -= retPad;
    retMax += retPad;

    function xOf(vol) { return margin + ((vol - volMin) / (volMax - volMin)) * (w - margin - 16); }
    function yOf(ret) { return h - margin - ((ret - retMin) / (retMax - retMin)) * (h - margin - 16); }

    drawAxes(ctx, w, h, margin, 'Volatility →', 'Return →');

    ctx.strokeStyle = '#5b9dff';
    ctx.lineWidth = 2;
    ctx.beginPath();
    points.forEach(function (p, idx) {
      var x = xOf(p.volatility);
      var y = yOf(p.return);
      if (idx === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();

    var current = PortfolioMath.twoAssetStats(meanA, meanB, covAA, covBB, covAB, sel.weightA);
    ctx.fillStyle = '#4fd1a5';
    ctx.beginPath();
    ctx.arc(xOf(current.volatility), yOf(current.return), 6, 0, Math.PI * 2);
    ctx.fill();
  }

  function drawAxes(ctx, w, h, margin, xLabel, yLabel) {
    ctx.strokeStyle = '#2c3650';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(margin, 10);
    ctx.lineTo(margin, h - margin);
    ctx.lineTo(w - 10, h - margin);
    ctx.stroke();

    ctx.fillStyle = '#9aa5bd';
    ctx.font = '11px sans-serif';
    ctx.fillText(xLabel, w - 90, h - margin + 24);
    ctx.save();
    ctx.translate(14, margin + 10);
    ctx.rotate(-Math.PI / 2);
    ctx.fillText(yLabel, 0, 0);
    ctx.restore();
  }

  // ---- AI explain (shared) -------------------------------------------
  function explainWithAI(promptText, fallbackText, outputEl) {
    var key = els['api-key-input'].value.trim();
    outputEl.textContent = 'Thinking…';

    if (!key) {
      outputEl.textContent = fallbackText;
      return;
    }

    fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
        'x-api-key': key,
        'anthropic-version': '2023-06-01',
        'anthropic-dangerous-direct-browser-access': 'true',
      },
      body: JSON.stringify({
        model: 'claude-haiku-4-5-20251001',
        max_tokens: 300,
        messages: [{ role: 'user', content: promptText }],
      }),
    })
      .then(function (res) {
        if (!res.ok) throw new Error('API error ' + res.status);
        return res.json();
      })
      .then(function (data) {
        var text = data && data.content && data.content[0] && data.content[0].text;
        outputEl.textContent = text || fallbackText;
      })
      .catch(function () {
        outputEl.textContent = fallbackText;
      });
  }

  function explainMixer() {
    var sel = currentMixerSelection();
    if (sel.iA === sel.iB) {
      els['explain-mixer-output'].textContent = 'Pick two different assets to compare.';
      return;
    }
    var meanA = DATA.mean_return[sel.tickerA];
    var meanB = DATA.mean_return[sel.tickerB];
    var covAA = DATA.cov_matrix[sel.iA][sel.iA];
    var covBB = DATA.cov_matrix[sel.iB][sel.iB];
    var covAB = DATA.cov_matrix[sel.iA][sel.iB];
    var corr = DATA.corr_matrix[sel.iA][sel.iB];
    var stats = PortfolioMath.twoAssetStats(meanA, meanB, covAA, covBB, covAB, sel.weightA);
    var volA = DATA.volatility[sel.tickerA];
    var volB = DATA.volatility[sel.tickerB];
    var naiveVol = sel.weightA * volA + (1 - sel.weightA) * volB;
    var saved = naiveVol - stats.volatility;

    var fallback = sel.tickerA + ' and ' + sel.tickerB + ' have a real historical correlation of ' + formatNum(corr, 2) + '. ' +
      'At ' + Math.round(sel.weightA * 100) + '%/' + Math.round((1 - sel.weightA) * 100) + '%, the blended portfolio has an expected ' +
      'volatility of ' + formatPct(stats.volatility) + ' — versus ' + formatPct(naiveVol) + ' if you naively averaged their individual volatilities. ' +
      (saved > 0
        ? 'That ' + formatPct(saved) + ' of risk simply disappeared because the two assets do not move in perfect lockstep.'
        : 'Because the correlation here is high, there is little to no diversification benefit from this pair at this mix.');

    var prompt = 'In two short sentences, explain to a research-savvy but non-finance-expert reader why blending ' +
      sel.tickerA + ' (' + Math.round(sel.weightA * 100) + '%) and ' + sel.tickerB + ' (' + Math.round((1 - sel.weightA) * 100) + '%) ' +
      'gives a portfolio volatility of ' + formatPct(stats.volatility) + ' when the naive weighted-average volatility would be ' +
      formatPct(naiveVol) + ', given their historical correlation is ' + formatNum(corr, 2) + '. Be concrete and reference the actual numbers.';

    explainWithAI(prompt, fallback, els['explain-mixer-output']);
  }

  // ---- Efficient Frontier tab -----------------------------------------
  function setupFrontier() {
    els['resample-cloud'].addEventListener('click', function () {
      renderFrontier();
    });
    els['explain-frontier'].addEventListener('click', explainFrontier);
    renderFrontier();
  }

  function renderFrontier() {
    currentCloud = PortfolioMath.monteCarloCloud(meanVec, DATA.cov_matrix, 600, cloudRng);
    els['gmv-return'].textContent = formatPct(gmv.return);
    els['gmv-vol'].textContent = formatPct(gmv.volatility);
    drawFrontierChart(els['frontier-canvas'], null);
  }

  function frontierCurvePoints(steps) {
    var n = steps || 60;
    var pts = [];
    for (var i = 0; i <= n; i++) {
      var target = frontierReturnRange.min + ((frontierReturnRange.max - frontierReturnRange.min) * i) / n;
      pts.push(PortfolioMath.efficientFrontierPoint(target, meanVec, DATA.cov_matrix, frontierCoeffs));
    }
    return pts;
  }

  function drawFrontierChart(canvas, overlay) {
    var ctx = canvas.getContext('2d');
    var w = canvas.width;
    var h = canvas.height;
    ctx.clearRect(0, 0, w, h);

    var curve = frontierCurvePoints(60);
    var allVols = currentCloud.map(function (p) { return p.volatility; }).concat(curve.map(function (p) { return p.volatility; }));
    var allRets = currentCloud.map(function (p) { return p.return; }).concat(curve.map(function (p) { return p.return; }));

    var margin = 46;
    var volMin = 0;
    var volMax = Math.max.apply(null, allVols) * 1.08;
    var retMin = Math.min.apply(null, allRets);
    var retMax = Math.max.apply(null, allRets);
    var retPad = Math.max((retMax - retMin) * 0.1, 0.005);
    retMin -= retPad;
    retMax += retPad;

    function xOf(vol) { return margin + ((vol - volMin) / (volMax - volMin)) * (w - margin - 16); }
    function yOf(ret) { return h - margin - ((ret - retMin) / (retMax - retMin)) * (h - margin - 16); }

    drawAxes(ctx, w, h, margin, 'Volatility →', 'Return →');

    ctx.fillStyle = 'rgba(154, 165, 189, 0.5)';
    currentCloud.forEach(function (p) {
      ctx.beginPath();
      ctx.arc(xOf(p.volatility), yOf(p.return), 2.5, 0, Math.PI * 2);
      ctx.fill();
    });

    ctx.strokeStyle = '#5b9dff';
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    curve.forEach(function (p, idx) {
      var x = xOf(p.volatility);
      var y = yOf(p.return);
      if (idx === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();

    ctx.fillStyle = '#4fd1a5';
    ctx.beginPath();
    ctx.arc(xOf(gmv.volatility), yOf(gmv.return), 6, 0, Math.PI * 2);
    ctx.fill();

    if (overlay && overlay.tangency) {
      var t = overlay.tangency;
      // Capital Market Line from (0, riskFreeRate) through the tangency point
      ctx.strokeStyle = '#ffb454';
      ctx.lineWidth = 1.5;
      ctx.setLineDash([5, 4]);
      ctx.beginPath();
      ctx.moveTo(xOf(0), yOf(overlay.riskFreeRate));
      var slope = (t.return - overlay.riskFreeRate) / t.volatility;
      var endVol = volMax;
      ctx.lineTo(xOf(endVol), yOf(overlay.riskFreeRate + slope * endVol));
      ctx.stroke();
      ctx.setLineDash([]);

      ctx.fillStyle = '#ffb454';
      ctx.beginPath();
      ctx.arc(xOf(t.volatility), yOf(t.return), 6, 0, Math.PI * 2);
      ctx.fill();
    }

    return { xOf: xOf, yOf: yOf, volMax: volMax };
  }

  function explainFrontier() {
    var avgVol = DATA.tickers.reduce(function (sum, t) { return sum + DATA.volatility[t]; }, 0) / DATA.tickers.length;
    var reduction = avgVol - gmv.volatility;
    var fallback = 'The global minimum-variance portfolio has a volatility of ' + formatPct(gmv.volatility) +
      ', compared with an average individual-asset volatility of ' + formatPct(avgVol) + ' across all ' + DATA.tickers.length +
      ' assets. Spreading the ' + formatPct(reduction) + ' gap between them is the entire point of diversification: combining ' +
      'imperfectly-correlated assets can produce a portfolio less volatile than any single asset in it.';
    var prompt = 'In two short sentences, explain why a diversified portfolio\'s minimum-variance volatility (' +
      formatPct(gmv.volatility) + ') can be lower than the average individual asset volatility (' + formatPct(avgVol) +
      ') among the ' + DATA.tickers.length + ' assets it is built from. Reference the actual numbers.';
    explainWithAI(prompt, fallback, els['explain-frontier-output']);
  }

  // ---- Sharpe & Risk-Free tab -------------------------------------------
  function setupSharpe() {
    els['riskfree-slider'].addEventListener('input', renderSharpe);
    renderSharpe();
  }

  function renderSharpe() {
    var riskFree = Number(els['riskfree-slider'].value) / 100;
    els['riskfree-value'].textContent = formatPct(riskFree, 1);

    var tangency = PortfolioMath.tangencyPortfolio(meanVec, DATA.cov_matrix, riskFree, frontierCoeffs);
    var gmvSharpe = PortfolioMath.sharpeRatio(gmv.return, gmv.volatility, riskFree);

    els['tangency-return'].textContent = formatPct(tangency.return);
    els['tangency-vol'].textContent = formatPct(tangency.volatility);
    els['tangency-sharpe'].textContent = formatNum(tangency.sharpe, 3);
    els['gmv-sharpe'].textContent = formatNum(gmvSharpe, 3);

    // Keep the drawn curve wide enough that the tangency marker never
    // falls outside the visible frontier segment, however the risk-free
    // slider moves it.
    if (tangency.return > frontierReturnRange.max) {
      frontierReturnRange.max = tangency.return * 1.1;
    }

    if (!currentCloud.length) currentCloud = PortfolioMath.monteCarloCloud(meanVec, DATA.cov_matrix, 600, cloudRng);
    drawFrontierChart(els['sharpe-canvas'], { tangency: tangency, riskFreeRate: riskFree });
  }

  // ---- Correlation Matrix tab -------------------------------------------
  function corrToColor(corr) {
    var c = Math.max(-1, Math.min(1, corr));
    if (c >= 0) {
      var t = c; // 0..1 -> white..blue
      var r = Math.round(255 - t * (255 - 91));
      var g = Math.round(255 - t * (255 - 157));
      var b = Math.round(255 - t * (255 - 255));
      return 'rgb(' + r + ',' + g + ',' + b + ')';
    } else {
      var t2 = -c; // 0..1 -> white..red
      var r2 = Math.round(255 - t2 * (255 - 255));
      var g2 = Math.round(255 - t2 * (255 - 123));
      var b2 = Math.round(255 - t2 * (255 - 123));
      return 'rgb(' + r2 + ',' + g2 + ',' + b2 + ')';
    }
  }

  function setupCorrelation() {
    var grid = els['corr-heatmap'];
    grid.innerHTML = '';
    var n = DATA.tickers.length;
    grid.style.gridTemplateColumns = 'repeat(' + (n + 1) + ', minmax(46px, 1fr))';

    var corner = document.createElement('div');
    corner.className = 'heatmap-cell heatmap-header';
    grid.appendChild(corner);

    DATA.tickers.forEach(function (t) {
      var head = document.createElement('div');
      head.className = 'heatmap-cell heatmap-header';
      head.textContent = t;
      grid.appendChild(head);
    });

    DATA.tickers.forEach(function (rowTicker, i) {
      var rowHead = document.createElement('div');
      rowHead.className = 'heatmap-cell heatmap-header';
      rowHead.textContent = rowTicker;
      grid.appendChild(rowHead);

      DATA.tickers.forEach(function (colTicker, j) {
        var corr = DATA.corr_matrix[i][j];
        var cell = document.createElement('button');
        cell.className = 'heatmap-cell';
        cell.setAttribute('data-testid', 'corr-cell-' + rowTicker + '-' + colTicker);
        cell.style.background = corrToColor(corr);
        cell.style.color = '#0a0e17';
        cell.style.border = 'none';
        cell.textContent = formatNum(corr, 2);
        cell.addEventListener('click', function () {
          els['asset-a'].value = rowTicker;
          els['asset-b'].value = colTicker === rowTicker ? (DATA.tickers[(j + 1) % n]) : colTicker;
          onMixerInputsChanged();
          activateTab('explainer');
        });
        grid.appendChild(cell);
      });
    });
  }

  // ---- Quiz tab -----------------------------------------------------
  function setupQuiz() {
    els['quiz-option-0'].addEventListener('click', function () { answerQuiz(0); });
    els['quiz-option-1'].addEventListener('click', function () { answerQuiz(1); });
    els['quiz-next'].addEventListener('click', newQuizRound);
    renderQuizStats();
    newQuizRound();
  }

  function randomQuizPortfolio() {
    var iA = Math.floor(quizRng() * DATA.tickers.length);
    var iB = Math.floor(quizRng() * DATA.tickers.length);
    if (iB === iA) iB = (iA + 1) % DATA.tickers.length;
    var weightA = 0.15 + quizRng() * 0.7; // keep away from the 0/100% edges for a more interesting mix
    var tickerA = DATA.tickers[iA];
    var tickerB = DATA.tickers[iB];
    var stats = PortfolioMath.twoAssetStats(
      DATA.mean_return[tickerA], DATA.mean_return[tickerB],
      DATA.cov_matrix[iA][iA], DATA.cov_matrix[iB][iB], DATA.cov_matrix[iA][iB],
      weightA
    );
    var sharpe = PortfolioMath.sharpeRatio(stats.return, stats.volatility, QUIZ_RISK_FREE);
    return {
      tickerA: tickerA, tickerB: tickerB, weightA: weightA,
      return: stats.return, volatility: stats.volatility, sharpe: sharpe,
    };
  }

  function newQuizRound() {
    var a = randomQuizPortfolio();
    var b = randomQuizPortfolio();
    var correctIndex = a.sharpe >= b.sharpe ? 0 : 1;
    quizRound = { portfolios: [a, b], correctIndex: correctIndex, answered: false };
    renderQuizRound();
  }

  function describePortfolio(p) {
    return Math.round(p.weightA * 100) + '% ' + p.tickerA + ' / ' + Math.round((1 - p.weightA) * 100) + '% ' + p.tickerB +
      '\nExpected return: ' + formatPct(p.return) + '  ·  Volatility: ' + formatPct(p.volatility);
  }

  function renderQuizRound() {
    [0, 1].forEach(function (i) {
      var btn = els['quiz-option-' + i];
      btn.textContent = describePortfolio(quizRound.portfolios[i]);
      btn.classList.remove('correct', 'incorrect');
      btn.disabled = false;
    });
    els['quiz-feedback'].textContent = '';
    els['quiz-next'].hidden = true;
  }

  function answerQuiz(chosenIndex) {
    if (quizRound.answered) return;
    quizRound.answered = true;

    var correct = chosenIndex === quizRound.correctIndex;
    [0, 1].forEach(function (i) {
      var btn = els['quiz-option-' + i];
      btn.disabled = true;
      if (i === quizRound.correctIndex) btn.classList.add('correct');
      else if (i === chosenIndex) btn.classList.add('incorrect');
    });

    els['quiz-feedback'].textContent = (correct ? 'Correct. ' : 'Not quite. ') +
      'Sharpe ratios: option 1 = ' + formatNum(quizRound.portfolios[0].sharpe, 3) +
      ', option 2 = ' + formatNum(quizRound.portfolios[1].sharpe, 3) + '.';

    state.quiz.attempts += 1;
    if (correct) {
      state.quiz.correct += 1;
      state.quiz.streak += 1;
      state.quiz.bestStreak = Math.max(state.quiz.bestStreak, state.quiz.streak);
    } else {
      state.quiz.streak = 0;
    }
    saveState();
    renderQuizStats();

    els['quiz-next'].hidden = false;
  }

  function renderQuizStats() {
    els['quiz-attempts'].textContent = String(state.quiz.attempts);
    els['quiz-correct'].textContent = String(state.quiz.correct);
    els['quiz-streak'].textContent = String(state.quiz.streak);
    els['quiz-best-streak'].textContent = String(state.quiz.bestStreak);
  }

  // Expose a few internals for Playwright tests to call directly without
  // relying purely on UI timing.
  window.__portfolioLabTestHooks = {
    getState: function () { return state; },
    getQuizRound: function () { return quizRound; },
  };
})();
