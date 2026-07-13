/* CircuitLab app wiring: mode/view switching, question flow, stats, reset.
   Depends on data.js, mastery-store.js, quiz-engine.js, brain-diagram.js. */

(function () {
  var state = {
    mastery: {},
    mode: 'explore',
    exploreView: 'lateral',
    queue: [],
    index: 0,
    results: [],
    circuitProgress: [],
    activeVignette: null,
  };

  function $(id) {
    return document.getElementById(id);
  }

  function escapeHtml(str) {
    var div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  function currentQuestion() {
    if (state.mode === 'vignette') {
      return state.activeVignette || state.queue[state.index] || null;
    }
    return state.queue[state.index] || null;
  }

  function setModePanel(mode) {
    document.querySelectorAll('.mode-panel').forEach(function (panel) {
      panel.classList.toggle('active-panel', panel.getAttribute('data-panel') === mode);
    });
    $('panel-session-summary').classList.remove('active-panel');
  }

  function setModeNav(mode) {
    document.querySelectorAll('.mode-tab').forEach(function (btn) {
      var isActive = btn.getAttribute('data-mode') === mode;
      btn.classList.toggle('active', isActive);
      btn.setAttribute('aria-selected', isActive ? 'true' : 'false');
    });
  }

  function renderStats() {
    var pct = overallMasteryPercent(state.mastery);
    $('overall-mastery').textContent = pct + '%';
    var masteredCount = 0;
    for (var id in state.mastery) {
      if (state.mastery[id] >= MASTERY_MAX) {
        masteredCount += 1;
      }
    }
    $('mastered-count').textContent = masteredCount + ' / ' + REGION_ORDER.length;
  }

  function switchMode(mode) {
    state.mode = mode;
    state.index = 0;
    state.results = [];
    state.circuitProgress = [];
    state.activeVignette = null;
    BrainDiagram.clearHighlights();
    setModeNav(mode);
    setModePanel(mode);

    if (mode === 'explore') {
      BrainDiagram.setViewMode('single');
      BrainDiagram.setActiveView(state.exploreView);
      renderExploreDetail(null);
    } else if (mode === 'label') {
      BrainDiagram.setViewMode('both');
      state.queue = buildLabelQueue();
      renderLabelQuestion();
    } else if (mode === 'function') {
      BrainDiagram.setViewMode('both');
      state.queue = buildFunctionQueue();
      renderFunctionQuestion();
    } else if (mode === 'circuit') {
      BrainDiagram.setViewMode('both');
      state.queue = buildCircuitQueue();
      renderCircuitQuestion();
    } else if (mode === 'vignette') {
      BrainDiagram.setViewMode('both');
      state.queue = buildVignetteQueue(VIGNETTES);
      $('anthropic-key-input').value = '';
      $('vignette-ai-status').textContent = '';
      updateGenerateButtonState();
      renderVignetteQuestion();
    }
  }

  /* ---------- Explore mode ---------- */

  function renderExploreDetail(regionId) {
    var el = $('explore-detail');
    if (!regionId) {
      el.innerHTML = '<p class="muted">Click any labeled region on the diagram to see what it does.</p>';
      return;
    }
    var r = REGIONS[regionId];
    el.innerHTML =
      '<h3>' + escapeHtml(r.name) + ' <span class="abbr">(' + escapeHtml(r.abbr) + ')</span></h3>' +
      '<p><strong>Function:</strong> ' + escapeHtml(r.fn) + '</p>' +
      '<p><strong>Relevance:</strong> ' + escapeHtml(r.relevance) + '</p>';
  }

  /* ---------- Label mode ---------- */

  function renderLabelQuestion() {
    BrainDiagram.clearHighlights();
    var q = currentQuestion();
    if (!q) {
      finishSession();
      return;
    }
    BrainDiagram.highlightRegion(q.regionId);
    $('label-progress').textContent = (state.index + 1) + ' / ' + state.queue.length;
    $('label-feedback').textContent = '';
    $('label-feedback').className = 'feedback';
    var choicesEl = $('label-choices');
    choicesEl.innerHTML = '';
    q.choices.forEach(function (choiceId) {
      var btn = document.createElement('button');
      btn.className = 'choice-btn';
      btn.type = 'button';
      btn.setAttribute('data-testid', 'label-choice');
      btn.setAttribute('data-choice-region', choiceId);
      btn.textContent = REGIONS[choiceId].name;
      btn.addEventListener('click', function () {
        answerLabel(choiceId);
      });
      choicesEl.appendChild(btn);
    });
    $('label-next').disabled = true;
  }

  function answerLabel(choiceId) {
    var q = currentQuestion();
    if (!q || $('label-next').disabled === false) {
      /* already answered */
    }
    var correct = choiceId === q.regionId;
    state.results.push({ correct: correct });
    state.mastery = updateMastery(state.mastery, q.regionId, correct);
    BrainDiagram.applyMastery(state.mastery);
    renderStats();
    BrainDiagram.flashResult(q.regionId, correct);
    document.querySelectorAll('#label-choices .choice-btn').forEach(function (btn) {
      btn.disabled = true;
    });
    var fb = $('label-feedback');
    if (correct) {
      fb.textContent = 'Correct — ' + REGIONS[q.regionId].name + '.';
      fb.className = 'feedback feedback-correct';
    } else {
      fb.textContent = 'Not quite. The highlighted region is ' + REGIONS[q.regionId].name + '.';
      fb.className = 'feedback feedback-incorrect';
    }
    $('label-next').disabled = false;
  }

  /* ---------- Function match mode ---------- */

  function renderFunctionQuestion() {
    BrainDiagram.clearHighlights();
    var q = currentQuestion();
    if (!q) {
      finishSession();
      return;
    }
    $('function-progress').textContent = (state.index + 1) + ' / ' + state.queue.length;
    $('function-prompt').textContent = q.prompt;
    $('function-feedback').textContent = '';
    $('function-feedback').className = 'feedback';
    $('function-next').disabled = true;
    state.awaitingFunctionAnswer = true;
  }

  function answerFunction(regionId) {
    if (state.mode !== 'function' || !state.awaitingFunctionAnswer) {
      return;
    }
    var q = currentQuestion();
    if (!q) {
      return;
    }
    state.awaitingFunctionAnswer = false;
    var correct = regionId === q.regionId;
    state.results.push({ correct: correct });
    state.mastery = updateMastery(state.mastery, q.regionId, correct);
    BrainDiagram.applyMastery(state.mastery);
    renderStats();
    BrainDiagram.flashResult(regionId, correct);
    if (!correct) {
      BrainDiagram.highlightRegion(q.regionId);
    }
    var fb = $('function-feedback');
    if (correct) {
      fb.textContent = 'Correct — that is ' + REGIONS[q.regionId].name + '.';
      fb.className = 'feedback feedback-correct';
    } else {
      fb.textContent = 'Not quite. The correct region is ' + REGIONS[q.regionId].name + ' (now highlighted).';
      fb.className = 'feedback feedback-incorrect';
    }
    $('function-next').disabled = false;
  }

  /* ---------- Circuit trace mode ---------- */

  function renderCircuitQuestion() {
    BrainDiagram.clearHighlights();
    state.circuitProgress = [];
    var q = currentQuestion();
    if (!q) {
      finishSession();
      return;
    }
    $('circuit-progress-label').textContent = (state.index + 1) + ' / ' + state.queue.length;
    $('circuit-name').textContent = CIRCUITS[q.circuitId].name;
    $('circuit-steps').textContent = '0 / ' + q.sequence.length + ' regions selected';
    $('circuit-feedback').textContent = '';
    $('circuit-feedback').className = 'feedback';
    $('circuit-next').disabled = true;
    state.awaitingCircuitAnswer = true;
  }

  function answerCircuit(regionId) {
    if (state.mode !== 'circuit' || !state.awaitingCircuitAnswer) {
      return;
    }
    var q = currentQuestion();
    if (!q) {
      return;
    }
    var result = checkCircuitClick(state.circuitProgress, q.sequence, regionId);
    if (result.status === 'incorrect') {
      state.awaitingCircuitAnswer = false;
      state.results.push({ correct: false });
      state.mastery = updateMastery(state.mastery, q.sequence[state.circuitProgress.length], false);
      BrainDiagram.applyMastery(state.mastery);
      renderStats();
      BrainDiagram.flashResult(regionId, false);
      var fb = $('circuit-feedback');
      fb.textContent = 'Not quite. Correct sequence: ' +
        q.sequence.map(function (id) { return REGIONS[id].abbr; }).join(' → ') +
        '. ' + CIRCUITS[q.circuitId].description;
      fb.className = 'feedback feedback-incorrect';
      $('circuit-next').disabled = false;
      return;
    }

    state.circuitProgress = result.progress;
    BrainDiagram.markCircuitProgress(state.circuitProgress);
    $('circuit-steps').textContent = state.circuitProgress.length + ' / ' + q.sequence.length + ' regions selected';

    if (result.status === 'correct-complete') {
      state.awaitingCircuitAnswer = false;
      state.results.push({ correct: true });
      q.sequence.forEach(function (id) {
        state.mastery = updateMastery(state.mastery, id, true);
      });
      BrainDiagram.applyMastery(state.mastery);
      renderStats();
      var fbOk = $('circuit-feedback');
      fbOk.textContent = 'Correct! ' + CIRCUITS[q.circuitId].description;
      fbOk.className = 'feedback feedback-correct';
      $('circuit-next').disabled = false;
    }
  }

  /* ---------- Vignette mode ---------- */

  function updateGenerateButtonState() {
    var key = $('anthropic-key-input').value.trim();
    $('generate-vignette-btn').disabled = key.length === 0;
  }

  function renderVignetteQuestion() {
    state.activeVignette = null;
    var q = state.queue[state.index];
    if (!q) {
      finishSession();
      return;
    }
    displayVignetteQuestion(q);
  }

  function displayVignetteQuestion(q) {
    $('vignette-progress').textContent = (state.index + 1) + ' / ' + state.queue.length;
    $('vignette-text').textContent = q.vignette.text;
    $('vignette-feedback').textContent = '';
    $('vignette-feedback').className = 'feedback';
    $('vignette-source').textContent = q.vignette.aiGenerated ? 'AI-generated' : 'Curated';
    var choicesEl = $('vignette-choices');
    choicesEl.innerHTML = '';
    q.choices.forEach(function (choiceId) {
      var btn = document.createElement('button');
      btn.className = 'choice-btn';
      btn.type = 'button';
      btn.setAttribute('data-testid', 'vignette-choice');
      btn.setAttribute('data-choice-region', choiceId);
      btn.textContent = REGIONS[choiceId].name;
      btn.addEventListener('click', function () {
        answerVignette(choiceId, q);
      });
      choicesEl.appendChild(btn);
    });
    $('vignette-next').disabled = true;
  }

  function answerVignette(choiceId, q) {
    if (document.querySelectorAll('#vignette-choices .choice-btn[disabled]').length > 0) {
      return;
    }
    var correct = choiceId === q.vignette.targetRegion;
    state.results.push({ correct: correct });
    state.mastery = updateMastery(state.mastery, q.vignette.targetRegion, correct);
    BrainDiagram.applyMastery(state.mastery);
    renderStats();
    document.querySelectorAll('#vignette-choices .choice-btn').forEach(function (btn) {
      btn.disabled = true;
    });
    var fb = $('vignette-feedback');
    fb.textContent = (correct ? 'Correct. ' : 'Not quite — ' + REGIONS[q.vignette.targetRegion].name + ' was the target. ') +
      q.vignette.explanation;
    fb.className = 'feedback ' + (correct ? 'feedback-correct' : 'feedback-incorrect');
    $('vignette-next').disabled = false;
  }

  async function handleGenerateVignette() {
    var key = $('anthropic-key-input').value.trim();
    var statusEl = $('vignette-ai-status');
    var btn = $('generate-vignette-btn');
    if (!key) {
      return;
    }
    btn.disabled = true;
    statusEl.textContent = 'Generating…';
    statusEl.className = 'ai-status';
    try {
      var vignette = await generateVignette(key);
      state.activeVignette = {
        type: 'vignette',
        vignette: vignette,
        choices: buildRegionChoices(vignette.targetRegion, 4),
      };
      statusEl.textContent = 'New vignette generated.';
      statusEl.className = 'ai-status ai-status-ok';
      displayVignetteQuestion(state.activeVignette);
    } catch (err) {
      statusEl.textContent = err.message || 'Could not generate a vignette.';
      statusEl.className = 'ai-status ai-status-error';
    } finally {
      btn.disabled = key.length === 0;
    }
  }

  /* ---------- Shared: next / finish / reset ---------- */

  function goNext() {
    state.index += 1;
    if (state.mode === 'label') {
      renderLabelQuestion();
    } else if (state.mode === 'function') {
      renderFunctionQuestion();
    } else if (state.mode === 'circuit') {
      renderCircuitQuestion();
    } else if (state.mode === 'vignette') {
      renderVignetteQuestion();
    }
  }

  function finishSession() {
    var summary = scoreSession(state.results);
    summary.mode = state.mode;
    saveLastSession(summary);
    setModePanel('__none__');
    var panel = $('panel-session-summary');
    panel.classList.add('active-panel');
    $('summary-text').textContent =
      summary.correct + ' / ' + summary.total + ' correct (' + summary.percent + '%)';
  }

  function onRegionActivate(regionId) {
    if (state.mode === 'explore') {
      renderExploreDetail(regionId);
    } else if (state.mode === 'function') {
      answerFunction(regionId);
    } else if (state.mode === 'circuit') {
      answerCircuit(regionId);
    }
    /* label and vignette modes are answered via choice buttons, not diagram clicks */
  }

  function resetProgress() {
    state.mastery = resetMastery();
    BrainDiagram.applyMastery(state.mastery);
    renderStats();
  }

  function init() {
    state.mastery = loadMastery();
    BrainDiagram.init(onRegionActivate);
    BrainDiagram.applyMastery(state.mastery);
    renderStats();

    document.querySelectorAll('.mode-tab').forEach(function (btn) {
      btn.addEventListener('click', function () {
        switchMode(btn.getAttribute('data-mode'));
      });
    });

    document.querySelectorAll('.view-tab').forEach(function (btn) {
      btn.addEventListener('click', function () {
        state.exploreView = btn.getAttribute('data-view');
        BrainDiagram.setActiveView(state.exploreView);
      });
    });

    $('label-next').addEventListener('click', goNext);
    $('function-next').addEventListener('click', goNext);
    $('circuit-next').addEventListener('click', goNext);
    $('vignette-next').addEventListener('click', goNext);

    $('reset-progress-btn').addEventListener('click', function () {
      resetProgress();
    });

    $('anthropic-key-input').addEventListener('input', updateGenerateButtonState);
    $('generate-vignette-btn').addEventListener('click', handleGenerateVignette);

    $('summary-try-again').addEventListener('click', function () {
      switchMode(state.mode);
    });
    $('summary-explore').addEventListener('click', function () {
      switchMode('explore');
    });

    switchMode('explore');
  }

  document.addEventListener('DOMContentLoaded', init);

  /* Exposed for tests: read-only introspection, no state mutation from here. */
  window.CircuitLabApp = {
    getCurrentQuestion: currentQuestion,
    getMastery: function () { return state.mastery; },
    getMode: function () { return state.mode; },
  };
})();
