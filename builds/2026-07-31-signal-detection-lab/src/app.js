(function () {
  'use strict';

  const M = window.SdtMath;
  const SCENARIOS = window.SDT_SCENARIOS;
  const AI = window.AiScenario;

  const QUIZ_STORAGE_KEY = 'sdtLabQuizState';

  function clampRate(r) {
    return Math.max(1e-6, Math.min(1 - 1e-6, r));
  }

  function fmt(x, digits) {
    if (!isFinite(x)) return x > 0 ? '∞' : '-∞';
    return x.toFixed(digits === undefined ? 3 : digits);
  }

  // ---------- Tab switching ----------

  function initTabs() {
    const buttons = document.querySelectorAll('.tab-button');
    buttons.forEach((btn) => {
      btn.addEventListener('click', () => {
        buttons.forEach((b) => b.setAttribute('aria-selected', 'false'));
        btn.setAttribute('aria-selected', 'true');
        document.querySelectorAll('.tab-panel').forEach((panel) => panel.classList.add('hidden'));
        const target = document.getElementById('tab-' + btn.dataset.tab);
        target.classList.remove('hidden');
        if (btn.dataset.tab === 'roc') renderRoc();
        if (btn.dataset.tab === 'explainer') renderExplainer();
      });
    });
  }

  // ---------- Explainer tab ----------

  const explainerState = {
    dPrime: 1.5,
    criterion: 0,
    dragging: false,
  };

  function domainForExplainer() {
    return { xMin: -4, xMax: explainerState.dPrime + 4 };
  }

  function xToPixel(x, xMin, xMax, width, pad) {
    return pad + ((x - xMin) / (xMax - xMin)) * (width - 2 * pad);
  }

  function pixelToX(px, xMin, xMax, width, pad) {
    return xMin + ((px - pad) / (width - 2 * pad)) * (xMax - xMin);
  }

  function yToPixel(y, yMax, height, pad) {
    return height - pad - (y / yMax) * (height - 2 * pad);
  }

  function renderExplainer() {
    const canvas = document.getElementById('explainer-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    const pad = 20;
    const { xMin, xMax } = domainForExplainer();
    const yMax = 0.45;

    ctx.clearRect(0, 0, width, height);

    const criterionPx = xToPixel(explainerState.criterion, xMin, xMax, width, pad);

    // Shaded "respond yes" regions (right of criterion) under each curve.
    ctx.beginPath();
    ctx.moveTo(criterionPx, height - pad);
    for (let px = criterionPx; px <= width - pad; px++) {
      const x = pixelToX(px, xMin, xMax, width, pad);
      const y = M.normalPdf(x - explainerState.dPrime);
      ctx.lineTo(px, yToPixel(y, yMax, height, pad));
    }
    ctx.lineTo(width - pad, height - pad);
    ctx.closePath();
    ctx.fillStyle = 'rgba(76, 175, 125, 0.28)';
    ctx.fill();

    ctx.beginPath();
    ctx.moveTo(criterionPx, height - pad);
    for (let px = criterionPx; px <= width - pad; px++) {
      const x = pixelToX(px, xMin, xMax, width, pad);
      const y = M.normalPdf(x);
      ctx.lineTo(px, yToPixel(y, yMax, height, pad));
    }
    ctx.lineTo(width - pad, height - pad);
    ctx.closePath();
    ctx.fillStyle = 'rgba(224, 108, 108, 0.28)';
    ctx.fill();

    // Noise curve.
    ctx.beginPath();
    for (let px = pad; px <= width - pad; px++) {
      const x = pixelToX(px, xMin, xMax, width, pad);
      const y = M.normalPdf(x);
      const py = yToPixel(y, yMax, height, pad);
      if (px === pad) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    }
    ctx.strokeStyle = getComputedStyle(document.documentElement).getPropertyValue('--noise-color').trim() || '#5ec8ff';
    ctx.lineWidth = 2;
    ctx.stroke();

    // Signal curve.
    ctx.beginPath();
    for (let px = pad; px <= width - pad; px++) {
      const x = pixelToX(px, xMin, xMax, width, pad);
      const y = M.normalPdf(x - explainerState.dPrime);
      const py = yToPixel(y, yMax, height, pad);
      if (px === pad) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    }
    ctx.strokeStyle = getComputedStyle(document.documentElement).getPropertyValue('--signal-color').trim() || '#ff9f5e';
    ctx.lineWidth = 2;
    ctx.stroke();

    // Criterion line.
    ctx.beginPath();
    ctx.moveTo(criterionPx, pad);
    ctx.lineTo(criterionPx, height - pad);
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 2;
    ctx.setLineDash([5, 4]);
    ctx.stroke();
    ctx.setLineDash([]);

    updateExplainerStats();
  }

  function updateExplainerStats() {
    const hitRate = clampRate(1 - M.normalCdf(explainerState.criterion - explainerState.dPrime));
    const faRate = clampRate(1 - M.normalCdf(explainerState.criterion));
    const dPrimeVal = M.dPrime(hitRate, faRate);
    const cVal = M.criterionC(hitRate, faRate);
    const betaVal = M.likelihoodRatioBeta(hitRate, faRate);

    document.getElementById('explainer-dprime').textContent = fmt(dPrimeVal);
    document.getElementById('explainer-c').textContent = fmt(cVal);
    document.getElementById('explainer-beta').textContent = fmt(betaVal);
    document.getElementById('explainer-hitrate').textContent = (hitRate * 100).toFixed(1) + '%';
    document.getElementById('explainer-farate').textContent = (faRate * 100).toFixed(1) + '%';
    document.getElementById('explainer-bias-label').textContent = M.criterionLabel(cVal);
  }

  function initExplainerControls() {
    const canvas = document.getElementById('explainer-canvas');
    const slider = document.getElementById('dprime-slider');
    const sliderValue = document.getElementById('dprime-slider-value');

    slider.addEventListener('input', () => {
      explainerState.dPrime = parseFloat(slider.value);
      sliderValue.textContent = explainerState.dPrime.toFixed(2);
      const { xMin, xMax } = domainForExplainer();
      explainerState.criterion = Math.max(xMin + 0.1, Math.min(xMax - 0.1, explainerState.criterion));
      renderExplainer();
    });

    function updateCriterionFromEvent(evt) {
      const rect = canvas.getBoundingClientRect();
      const scaleX = canvas.width / rect.width;
      const px = (evt.clientX - rect.left) * scaleX;
      const { xMin, xMax } = domainForExplainer();
      const pad = 20;
      let x = pixelToX(px, xMin, xMax, canvas.width, pad);
      x = Math.max(xMin + 0.05, Math.min(xMax - 0.05, x));
      explainerState.criterion = x;
      renderExplainer();
    }

    canvas.addEventListener('mousedown', (evt) => {
      explainerState.dragging = true;
      updateCriterionFromEvent(evt);
    });
    canvas.addEventListener('mousemove', (evt) => {
      if (explainerState.dragging) updateCriterionFromEvent(evt);
    });
    window.addEventListener('mouseup', () => {
      explainerState.dragging = false;
    });
  }

  // ---------- ROC tab ----------

  function renderRoc() {
    const canvas = document.getElementById('roc-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    const pad = 30;

    ctx.clearRect(0, 0, width, height);

    // Axes.
    ctx.strokeStyle = '#2c3550';
    ctx.lineWidth = 1;
    ctx.strokeRect(pad, pad, width - 2 * pad, height - 2 * pad);

    // Chance diagonal.
    ctx.beginPath();
    ctx.moveTo(pad, height - pad);
    ctx.lineTo(width - pad, pad);
    ctx.strokeStyle = '#4a5578';
    ctx.setLineDash([4, 4]);
    ctx.stroke();
    ctx.setLineDash([]);

    const points = M.rocCurve(explainerState.dPrime, 101);
    ctx.beginPath();
    points.forEach((p, i) => {
      const px = pad + p.fa * (width - 2 * pad);
      const py = height - pad - p.hit * (height - 2 * pad);
      if (i === 0) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    });
    ctx.strokeStyle = '#5eb1ff';
    ctx.lineWidth = 2.5;
    ctx.stroke();

    // Current criterion's operating point.
    const hitRate = clampRate(1 - M.normalCdf(explainerState.criterion - explainerState.dPrime));
    const faRate = clampRate(1 - M.normalCdf(explainerState.criterion));
    const opPx = pad + faRate * (width - 2 * pad);
    const opPy = height - pad - hitRate * (height - 2 * pad);
    ctx.beginPath();
    ctx.arc(opPx, opPy, 5, 0, 2 * Math.PI);
    ctx.fillStyle = '#ffffff';
    ctx.fill();

    const auc = M.rocAuc(explainerState.dPrime);
    document.getElementById('roc-dprime').textContent = fmt(explainerState.dPrime, 2);
    document.getElementById('roc-auc').textContent = fmt(auc);
  }

  // ---------- Calculator tab ----------

  function initCalculator() {
    const form = document.getElementById('calculator-form');
    form.addEventListener('submit', (evt) => {
      evt.preventDefault();
      const hits = parseInt(document.getElementById('calc-hits').value, 10) || 0;
      const misses = parseInt(document.getElementById('calc-misses').value, 10) || 0;
      const fa = parseInt(document.getElementById('calc-fa').value, 10) || 0;
      const cr = parseInt(document.getElementById('calc-cr').value, 10) || 0;
      const useCorrection = document.getElementById('calc-correction').checked;

      const outIds = ['calc-out-hitrate', 'calc-out-farate', 'calc-out-dprime', 'calc-out-c', 'calc-out-beta', 'calc-out-aprime', 'calc-out-bdouble'];

      try {
        const { hitRate, faRate } = M.ratesFromCounts(hits, misses, fa, cr, {
          correction: useCorrection ? 'loglinear' : 'none',
        });
        const dPrimeVal = M.dPrime(hitRate, faRate);
        const cVal = M.criterionC(hitRate, faRate);
        const betaVal = M.likelihoodRatioBeta(hitRate, faRate);
        const aPrimeVal = M.aPrime(hitRate, faRate);
        const bDoubleVal = M.bDoublePrime(hitRate, faRate);

        document.getElementById('calc-out-hitrate').textContent = (hitRate * 100).toFixed(1) + '%';
        document.getElementById('calc-out-farate').textContent = (faRate * 100).toFixed(1) + '%';
        document.getElementById('calc-out-dprime').textContent = fmt(dPrimeVal);
        document.getElementById('calc-out-c').textContent = fmt(cVal);
        document.getElementById('calc-out-beta').textContent = fmt(betaVal);
        document.getElementById('calc-out-aprime').textContent = fmt(aPrimeVal);
        document.getElementById('calc-out-bdouble').textContent = fmt(bDoubleVal);
      } catch (err) {
        outIds.forEach((id) => {
          document.getElementById(id).textContent = 'Error';
        });
        // eslint-disable-next-line no-console
        console.error(err.message);
      }
    });
  }

  // ---------- Quiz tab ----------

  function loadQuizState() {
    try {
      const raw = window.localStorage.getItem(QUIZ_STORAGE_KEY);
      if (!raw) return { overall: { attempts: 0, correct: 0 }, byScenario: {} };
      const parsed = JSON.parse(raw);
      if (!parsed || typeof parsed !== 'object' || !parsed.overall) {
        return { overall: { attempts: 0, correct: 0 }, byScenario: {} };
      }
      return parsed;
    } catch (err) {
      return { overall: { attempts: 0, correct: 0 }, byScenario: {} };
    }
  }

  function saveQuizState(state) {
    window.localStorage.setItem(QUIZ_STORAGE_KEY, JSON.stringify(state));
  }

  let quizState = loadQuizState();
  let currentScenario = SCENARIOS[0];
  let lastScenarioIndex = 0;

  function groundTruthFor(scenario) {
    const { hitRate, faRate } = M.ratesFromCounts(
      scenario.hits, scenario.misses, scenario.falseAlarms, scenario.correctRejections
    );
    const dPrimeVal = M.dPrime(hitRate, faRate);
    const cVal = M.criterionC(hitRate, faRate);
    return {
      dPrimeVal,
      cVal,
      bucket: M.dPrimeBucket(dPrimeVal),
      biasLabel: M.criterionLabel(cVal),
    };
  }

  function renderQuizScenario(scenario) {
    currentScenario = scenario;
    document.getElementById('quiz-title').textContent = scenario.title;
    document.getElementById('quiz-domain').textContent = scenario.domain;
    document.getElementById('quiz-description').textContent = scenario.description;
    document.getElementById('quiz-hits').textContent = scenario.hits;
    document.getElementById('quiz-fa').textContent = scenario.falseAlarms;
    document.getElementById('quiz-misses').textContent = scenario.misses;
    document.getElementById('quiz-cr').textContent = scenario.correctRejections;

    document.querySelectorAll('input[name="quiz-bucket"]').forEach((el) => { el.checked = false; });
    document.querySelectorAll('input[name="quiz-bias"]').forEach((el) => { el.checked = false; });

    const feedback = document.getElementById('quiz-feedback');
    feedback.classList.add('hidden');
    feedback.textContent = '';
  }

  function updateQuizScoreDisplay() {
    document.getElementById('quiz-score').textContent = quizState.overall.correct + ' / ' + quizState.overall.attempts;
  }

  function initQuiz() {
    renderQuizScenario(SCENARIOS[0]);
    updateQuizScoreDisplay();

    document.getElementById('quiz-next').addEventListener('click', () => {
      let nextIndex = lastScenarioIndex;
      if (SCENARIOS.length > 1) {
        while (nextIndex === lastScenarioIndex) {
          nextIndex = Math.floor(Math.random() * SCENARIOS.length);
        }
      }
      lastScenarioIndex = nextIndex;
      renderQuizScenario(SCENARIOS[nextIndex]);
    });

    document.getElementById('quiz-form').addEventListener('submit', (evt) => {
      evt.preventDefault();
      const bucketChoice = document.querySelector('input[name="quiz-bucket"]:checked');
      const biasChoice = document.querySelector('input[name="quiz-bias"]:checked');
      const feedback = document.getElementById('quiz-feedback');

      if (!bucketChoice || !biasChoice) {
        feedback.textContent = 'Select both a sensitivity bucket and a bias before checking.';
        feedback.className = 'quiz-feedback incorrect';
        feedback.classList.remove('hidden');
        return;
      }

      const truth = groundTruthFor(currentScenario);
      const bucketCorrect = bucketChoice.value === truth.bucket;
      const biasCorrect = biasChoice.value === truth.biasLabel;
      const allCorrect = bucketCorrect && biasCorrect;

      quizState.overall.attempts += 1;
      if (allCorrect) quizState.overall.correct += 1;
      const scenarioStats = quizState.byScenario[currentScenario.id] || { attempts: 0, correct: 0 };
      scenarioStats.attempts += 1;
      if (allCorrect) scenarioStats.correct += 1;
      quizState.byScenario[currentScenario.id] = scenarioStats;
      saveQuizState(quizState);
      updateQuizScoreDisplay();

      feedback.textContent =
        (allCorrect ? 'Correct. ' : 'Not quite. ') +
        'd′ = ' + fmt(truth.dPrimeVal, 2) + ' (' + truth.bucket + '), ' +
        'criterion c = ' + fmt(truth.cVal, 2) + ' (' + truth.biasLabel + ').';
      feedback.className = 'quiz-feedback ' + (allCorrect ? 'correct' : 'incorrect');
      feedback.classList.remove('hidden');
    });
  }

  // ---------- AI scenario generation ----------

  function initAiScenarioForm() {
    const form = document.getElementById('ai-scenario-form');
    const status = document.getElementById('ai-status');

    form.addEventListener('submit', async (evt) => {
      evt.preventDefault();
      const context = document.getElementById('ai-context').value;
      const apiKey = document.getElementById('ai-key').value;

      status.textContent = apiKey ? 'Contacting Claude…' : 'Generating scenario (no key supplied, using deterministic generator)…';

      const result = await AI.generateScenario(context, apiKey || null);
      renderQuizScenario(result.scenario);

      if (result.source === 'ai') {
        status.textContent = 'Scenario generated by Claude.';
      } else if (result.source === 'template-fallback') {
        status.textContent = 'AI request failed (' + result.error + ') — used the deterministic generator instead.';
      } else {
        status.textContent = 'Used the deterministic generator (no API key supplied). Zero network requests made.';
      }

      document.getElementById('ai-key').value = '';
    });
  }

  // ---------- Init ----------

  document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initExplainerControls();
    initCalculator();
    initQuiz();
    initAiScenarioForm();
    renderExplainer();
  });
})();
