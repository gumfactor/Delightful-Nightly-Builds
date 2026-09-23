/*
 * Pooling Lab — app wiring. Connects the controls to src/stats.js,
 * src/render.js, src/quiz.js, and src/explain.js.
 */
(function () {
  'use strict';

  const PROFILES = {
    equal: { groupCount: 6, groupSizes: [15, 15, 15, 15, 15, 15] },
    'one-small': { groupCount: 6, groupSizes: [3, 30, 30, 30, 30, 30] },
    'one-large': { groupCount: 6, groupSizes: [60, 8, 8, 8, 8, 8] },
  };

  const els = {
    seed: document.getElementById('seed-input'),
    profile: document.getElementById('profile-select'),
    tauSlider: document.getElementById('tau-slider'),
    tauValue: document.getElementById('tau-value'),
    sigmaSlider: document.getElementById('sigma-slider'),
    sigmaValue: document.getElementById('sigma-value'),
    regenerateBtn: document.getElementById('regenerate-btn'),
    trueIcc: document.getElementById('true-icc'),
    empiricalIcc: document.getElementById('empirical-icc'),
    grandMean: document.getElementById('grand-mean'),
    chartCanvas: document.getElementById('chart-canvas'),
    tableBody: document.getElementById('group-table-body'),
    apiKeyInput: document.getElementById('api-key-input'),
    explainBtn: document.getElementById('explain-btn'),
    explainOutput: document.getElementById('explain-output'),
    quizContainer: document.getElementById('quiz-container'),
    quizScore: document.getElementById('quiz-score'),
    quizTotal: document.getElementById('quiz-total'),
  };

  let dataset = null;
  let score = 0;

  function currentTau() {
    return parseFloat(els.tauSlider.value);
  }

  function currentSigma() {
    return parseFloat(els.sigmaSlider.value);
  }

  function currentSummary() {
    const overridden = Object.assign({}, dataset, {
      tau2: Math.pow(currentTau(), 2),
      sigma2: Math.pow(currentSigma(), 2),
    });
    return window.PoolingStats.computePoolingSummary(overridden);
  }

  function regenerate() {
    const profile = PROFILES[els.profile.value] || PROFILES.equal;
    const seed = parseInt(els.seed.value, 10) || 0;
    dataset = window.PoolingStats.generateNestedData({
      seed,
      groupCount: profile.groupCount,
      groupSizes: profile.groupSizes,
      tau2: Math.pow(currentTau(), 2),
      sigma2: Math.pow(currentSigma(), 2),
    });
    renderAll();
    buildQuiz();
  }

  function renderAll() {
    const summary = currentSummary();

    els.tauValue.textContent = currentTau().toFixed(1);
    els.sigmaValue.textContent = currentSigma().toFixed(1);
    els.trueIcc.textContent = summary.trueICC.toFixed(3);
    els.empiricalIcc.textContent =
      summary.empiricalICC === null ? 'n/a' : summary.empiricalICC.toFixed(3);
    els.grandMean.textContent = summary.grandMean.toFixed(2);

    window.PoolingRender.drawChart(els.chartCanvas, summary);

    els.tableBody.innerHTML = '';
    summary.perGroup.forEach((g) => {
      const tr = document.createElement('tr');
      [
        'Group ' + g.id,
        String(g.n),
        g.noPooling.toFixed(2),
        g.shrinkageWeight.toFixed(2),
        g.partialPooling.toFixed(2),
      ].forEach((text) => {
        const td = document.createElement('td');
        td.textContent = text;
        tr.appendChild(td);
      });
      els.tableBody.appendChild(tr);
    });
  }

  function buildQuiz() {
    const summary = currentSummary();
    const bank = window.PoolingQuiz.buildQuestionBank(summary);
    score = 0;
    els.quizContainer.innerHTML = '';
    els.quizScore.textContent = '0';
    els.quizTotal.textContent = String(bank.length);

    bank.forEach((question, qIndex) => {
      const wrap = document.createElement('div');
      wrap.className = 'quiz-question';
      wrap.setAttribute('data-testid', 'quiz-question-' + qIndex);

      const qText = document.createElement('div');
      qText.textContent = question.text;
      wrap.appendChild(qText);

      const choicesWrap = document.createElement('div');
      choicesWrap.className = 'quiz-choices';

      question.choices.forEach((choiceText, cIndex) => {
        const btn = document.createElement('button');
        btn.textContent = choiceText;
        btn.setAttribute('data-testid', 'quiz-choice-' + qIndex + '-' + cIndex);
        btn.addEventListener('click', function () {
          const isCorrect = window.PoolingQuiz.checkAnswer(question, cIndex);
          Array.from(choicesWrap.children).forEach((b, i) => {
            b.disabled = true;
            if (i === question.correctIndex) b.classList.add('correct');
            else if (i === cIndex) b.classList.add('incorrect');
          });
          if (isCorrect) {
            score += 1;
            els.quizScore.textContent = String(score);
          }
        });
        choicesWrap.appendChild(btn);
      });

      wrap.appendChild(choicesWrap);
      els.quizContainer.appendChild(wrap);
    });
  }

  els.tauSlider.addEventListener('input', renderAll);
  els.sigmaSlider.addEventListener('input', renderAll);
  els.regenerateBtn.addEventListener('click', regenerate);
  els.explainBtn.addEventListener('click', function () {
    const apiKey = els.apiKeyInput.value.trim();
    window.PoolingExplain.requestExplanation(apiKey, currentSummary(), els.explainOutput);
  });

  window.addEventListener('resize', renderAll);

  // Initial load.
  regenerate();
})();
