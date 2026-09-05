// UI wiring: tab switching, slider handling, canvas rendering, and quiz flow.
// Classic script, runs at end of <body> so all elements already exist and
// every other src/*.js file has already attached its globals.
(function () {
  'use strict';

  const $ = (testid) => document.querySelector('[data-testid="' + testid + '"]');

  function fmt(v, d) {
    d = d === undefined ? 3 : d;
    return Number.isFinite(v) ? v.toFixed(d) : 'n/a';
  }
  function fmtP(p) {
    if (!Number.isFinite(p)) return 'n/a';
    return p < 0.001 ? '<0.001' : p.toFixed(4);
  }
  function setBadge(el, isSig, sigText, nonSigText) {
    el.textContent = isSig ? sigText : nonSigText;
    el.className = 'significance-badge ' + (isSig ? 'sig' : 'nonsig');
  }
  function clearChildren(el) {
    while (el.firstChild) el.removeChild(el.firstChild);
  }

  // ---------- Tabs ----------
  const tabButtons = document.querySelectorAll('.tab-btn');
  const panels = {
    mediation: $('panel-mediation'),
    moderation: $('panel-moderation'),
    quiz: $('panel-quiz'),
  };
  tabButtons.forEach((btn) => {
    btn.addEventListener('click', () => {
      const target = btn.getAttribute('data-tab');
      tabButtons.forEach((b) => {
        const active = b === btn;
        b.classList.toggle('active', active);
        b.setAttribute('aria-selected', String(active));
      });
      Object.keys(panels).forEach((key) => {
        panels[key].classList.toggle('hidden', key !== target);
      });
    });
  });

  // ---------- Mediation Lab ----------
  let medState = null;

  function wireSlider(sliderId, valId, decimals) {
    const slider = $(sliderId), valSpan = $(valId);
    slider.addEventListener('input', () => {
      valSpan.textContent = parseFloat(slider.value).toFixed(decimals);
    });
  }
  wireSlider('med-a', 'med-a-val', 2);
  wireSlider('med-b', 'med-b-val', 2);
  wireSlider('med-cprime', 'med-cprime-val', 2);
  wireSlider('med-noise', 'med-noise-val', 2);
  wireSlider('med-n', 'med-n-val', 0);
  wireSlider('mod-b1', 'mod-b1-val', 2);
  wireSlider('mod-b2', 'mod-b2-val', 2);
  wireSlider('mod-b3', 'mod-b3-val', 2);
  wireSlider('mod-noise', 'mod-noise-val', 2);
  wireSlider('mod-n', 'mod-n-val', 0);

  function drawMediationDiagram(stats) {
    const canvas = $('med-canvas');
    const ctx = canvas.getContext('2d');
    const w = canvas.width, h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    ctx.font = '13px sans-serif';
    ctx.textAlign = 'center';

    const nodes = {
      X: { x: 60, y: 190 },
      M: { x: 210, y: 55 },
      Y: { x: 360, y: 190 },
    };

    function drawNode(label, pos) {
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, 32, 0, Math.PI * 2);
      ctx.fillStyle = '#222937';
      ctx.fill();
      ctx.strokeStyle = '#5ab0ff';
      ctx.lineWidth = 2;
      ctx.stroke();
      ctx.fillStyle = '#e7ecf3';
      ctx.fillText(label, pos.x, pos.y + 5);
    }

    function drawArrow(from, to, label, color) {
      const dx = to.x - from.x, dy = to.y - from.y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      const ux = dx / dist, uy = dy / dist;
      const startX = from.x + ux * 34, startY = from.y + uy * 34;
      const endX = to.x - ux * 34, endY = to.y - uy * 34;
      ctx.beginPath();
      ctx.moveTo(startX, startY);
      ctx.lineTo(endX, endY);
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.stroke();
      const angle = Math.atan2(endY - startY, endX - startX);
      ctx.beginPath();
      ctx.moveTo(endX, endY);
      ctx.lineTo(endX - 8 * Math.cos(angle - 0.4), endY - 8 * Math.sin(angle - 0.4));
      ctx.lineTo(endX - 8 * Math.cos(angle + 0.4), endY - 8 * Math.sin(angle + 0.4));
      ctx.closePath();
      ctx.fillStyle = color;
      ctx.fill();
      const midX = (startX + endX) / 2, midY = (startY + endY) / 2;
      ctx.fillStyle = color;
      ctx.fillText(label, midX, midY - 8);
    }

    drawArrow(nodes.X, nodes.M, 'a=' + fmt(stats.a, 2), '#ffb454');
    drawArrow(nodes.M, nodes.Y, 'b=' + fmt(stats.b, 2), '#ffb454');
    drawArrow(nodes.X, nodes.Y, "c'=" + fmt(stats.cPrime, 2), '#5ab0ff');
    drawNode('X', nodes.X);
    drawNode('M', nodes.M);
    drawNode('Y', nodes.Y);

    ctx.fillStyle = '#9aa5b5';
    ctx.fillText('Total effect c = ' + fmt(stats.c, 3) + ' (no mediator in model)', w / 2, h - 10);
  }

  function renderMediationResults(stats) {
    $('med-a-est').textContent = fmt(stats.a, 3) + ' (SE ' + fmt(stats.aSE, 3) + ')';
    $('med-b-est').textContent = fmt(stats.b, 3) + ' (SE ' + fmt(stats.bSE, 3) + ')';
    $('med-cprime-est').textContent = fmt(stats.cPrime, 3) + ' (SE ' + fmt(stats.cPrimeSE, 3) + ')';
    $('med-c-est').textContent = fmt(stats.c, 3) + ' (SE ' + fmt(stats.cSE, 3) + ')';
    $('med-indirect').textContent = fmt(stats.indirect, 3);
    $('med-ci').textContent = '[' + fmt(stats.bootstrapCI[0], 3) + ', ' + fmt(stats.bootstrapCI[1], 3) + '] (' + stats.bootstrapReps + ' resamples)';
    $('med-identity').textContent = fmt(stats.identityCheck, 6) + ' (should be ~0)';
    $('med-sobel').textContent = fmt(stats.sobelSE, 3) + ' / ' + fmt(stats.sobelZ, 3) + ' / ' + fmtP(stats.sobelP);
    setBadge($('med-sig-badge'), stats.ciExcludesZero,
      'Indirect effect significant (95% CI excludes zero)',
      'Indirect effect not significant (95% CI includes zero)');
    $('med-explanation').textContent = '';
    $('med-results').hidden = false;
    drawMediationDiagram(stats);
  }

  $('med-generate').addEventListener('click', () => {
    const params = {
      trueA: parseFloat($('med-a').value),
      trueB: parseFloat($('med-b').value),
      trueCPrime: parseFloat($('med-cprime').value),
      noiseSD: parseFloat($('med-noise').value),
      n: parseInt($('med-n').value, 10),
      seed: hashSeed($('med-seed').value),
    };
    const sample = generateMediationSample(params);
    const stats = analyzeMediation(sample, sample.rng, 2000);
    medState = { params, sample, stats };
    renderMediationResults(stats);
  });

  $('med-explain-btn').addEventListener('click', async () => {
    if (!medState) return;
    const out = $('med-explanation');
    out.textContent = 'Thinking...';
    const apiKey = $('api-key-input').value.trim() || null;
    const result = await requestAIExplanation('mediation', medState.stats, apiKey);
    out.textContent = result.text;
  });

  // ---------- Moderation Lab ----------
  let modState = null;

  function zColor(rank) {
    // rank in [0,1]: low -> blue, high -> orange
    const r = Math.round(90 + rank * (255 - 90));
    const g = Math.round(176 - rank * 90);
    const b = Math.round(255 - rank * 200);
    return 'rgb(' + r + ',' + g + ',' + b + ')';
  }

  function drawModerationScatter(sample, stats) {
    const canvas = $('mod-canvas');
    const ctx = canvas.getContext('2d');
    const w = canvas.width, h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    const pad = 40;
    const xMin = Math.min(...sample.X), xMax = Math.max(...sample.X);
    const yMin = Math.min(...sample.Y), yMax = Math.max(...sample.Y);
    const zMin = Math.min(...sample.Z), zMax = Math.max(...sample.Z);
    const xSpan = (xMax - xMin) || 1, ySpan = (yMax - yMin) || 1, zSpan = (zMax - zMin) || 1;

    function toPx(x) { return pad + ((x - xMin) / xSpan) * (w - 2 * pad); }
    function toPy(y) { return h - pad - ((y - yMin) / ySpan) * (h - 2 * pad); }

    ctx.strokeStyle = '#2c3444';
    ctx.beginPath();
    ctx.moveTo(pad, h - pad); ctx.lineTo(w - pad, h - pad);
    ctx.moveTo(pad, pad); ctx.lineTo(pad, h - pad);
    ctx.stroke();

    sample.X.forEach((x, i) => {
      const rank = (sample.Z[i] - zMin) / zSpan;
      ctx.beginPath();
      ctx.arc(toPx(x), toPy(sample.Y[i]), 3.5, 0, Math.PI * 2);
      ctx.fillStyle = zColor(rank);
      ctx.globalAlpha = 0.85;
      ctx.fill();
      ctx.globalAlpha = 1;
    });

    const levels = [
      { k: -1, color: '#5ab0ff', label: '-1 SD' },
      { k: 0, color: '#e7ecf3', label: 'Mean' },
      { k: 1, color: '#ffb454', label: '+1 SD' },
    ];
    levels.forEach((lvl) => {
      const zVal = lvl.k * stats.sdZ;
      const yAt = (x) => stats.beta[0] + stats.beta[1] * (x - stats.xbar) + stats.beta[2] * zVal + stats.beta[3] * (x - stats.xbar) * zVal;
      ctx.beginPath();
      ctx.moveTo(toPx(xMin), toPy(yAt(xMin)));
      ctx.lineTo(toPx(xMax), toPy(yAt(xMax)));
      ctx.strokeStyle = lvl.color;
      ctx.lineWidth = 2;
      ctx.stroke();
    });

    ctx.font = '11px sans-serif';
    ctx.textAlign = 'left';
    levels.forEach((lvl, i) => {
      ctx.fillStyle = lvl.color;
      ctx.fillText('— ' + lvl.label, pad + i * 90, pad - 12);
    });
  }

  function simpleSlopeSignificantAt(zVal, stats) {
    const varB1 = stats.cov[1][1], varB3 = stats.cov[3][3], covB1B3 = stats.cov[1][3];
    const slope = stats.beta[1] + stats.beta[3] * zVal;
    const se = Math.sqrt(varB1 + zVal * zVal * varB3 + 2 * zVal * covB1B3);
    const t = slope / se;
    return studentTTwoTailedP(t, stats.dof) < 0.05;
  }

  function drawJNStrip(stats) {
    const canvas = $('mod-jn-canvas');
    const ctx = canvas.getContext('2d');
    const w = canvas.width, h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    const zLo = -3 * stats.sdZ, zHi = 3 * stats.sdZ;
    const steps = 200;
    for (let i = 0; i < steps; i++) {
      const zVal = zLo + ((zHi - zLo) * i) / steps;
      const sig = simpleSlopeSignificantAt(zVal, stats);
      ctx.fillStyle = sig ? 'rgba(82,199,143,0.55)' : 'rgba(239,106,106,0.3)';
      ctx.fillRect((w * i) / steps, 10, w / steps + 1, h - 30);
    }
    if (stats.jnRoots) {
      stats.jnRoots.forEach((z) => {
        const px = ((z - zLo) / (zHi - zLo)) * w;
        ctx.strokeStyle = '#e7ecf3';
        ctx.beginPath();
        ctx.moveTo(px, 10); ctx.lineTo(px, h - 20);
        ctx.stroke();
      });
    }
    ctx.fillStyle = '#9aa5b5';
    ctx.font = '10px sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText('Z = ' + fmt(zLo, 1), 2, h - 5);
    ctx.textAlign = 'right';
    ctx.fillText('Z = ' + fmt(zHi, 1), w - 2, h - 5);
  }

  function renderModerationResults(sample, stats) {
    $('mod-b0-est').textContent = fmt(stats.beta[0], 3) + ' (SE ' + fmt(stats.se[0], 3) + ')';
    $('mod-b1-est').textContent = fmt(stats.beta[1], 3) + ' (SE ' + fmt(stats.se[1], 3) + ')';
    $('mod-b2-est').textContent = fmt(stats.beta[2], 3) + ' (SE ' + fmt(stats.se[2], 3) + ')';
    $('mod-b3-est').textContent = fmt(stats.beta[3], 3) + ' (SE ' + fmt(stats.se[3], 3) + ', p ' + fmtP(stats.interactionP) + ')';
    $('mod-r2').textContent = fmt(stats.r2, 3);

    const tbody = $('mod-simple-slopes').querySelector('tbody');
    clearChildren(tbody);
    stats.simpleSlopes.forEach((s) => {
      const tr = document.createElement('tr');
      [s.label, fmt(s.slope, 3), fmt(s.se, 3), fmt(s.t, 3), fmtP(s.p) + (s.significant ? ' *' : '')].forEach((val) => {
        const td = document.createElement('td');
        td.textContent = val;
        tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });

    const jnEl = $('mod-jn-region');
    if (!stats.jnRoots) {
      jnEl.textContent = 'No finite boundary — the slope\'s significance does not change within a realistic range of the moderator.';
    } else if (stats.jnRoots.length === 1) {
      jnEl.textContent = 'Boundary at Z = ' + fmt(stats.jnRoots[0], 2) + ' (relative to the moderator\'s mean).';
    } else {
      jnEl.textContent = 'Significance changes outside Z = ' + fmt(stats.jnRoots[0], 2) + ' to ' + fmt(stats.jnRoots[1], 2) + ' (relative to the moderator\'s mean).';
    }

    setBadge($('mod-sig-badge'), stats.interactionSignificant,
      'Interaction significant', 'Interaction not significant');
    $('mod-explanation').textContent = '';
    $('mod-results').hidden = false;
    drawModerationScatter(sample, stats);
    drawJNStrip(stats);
  }

  $('mod-generate').addEventListener('click', () => {
    const params = {
      trueB1: parseFloat($('mod-b1').value),
      trueB2: parseFloat($('mod-b2').value),
      trueB3: parseFloat($('mod-b3').value),
      noiseSD: parseFloat($('mod-noise').value),
      n: parseInt($('mod-n').value, 10),
      seed: hashSeed($('mod-seed').value),
    };
    const sample = generateModerationSample(params);
    const stats = analyzeModeration(sample, 0.05);
    modState = { params, sample, stats };
    renderModerationResults(sample, stats);
  });

  $('mod-explain-btn').addEventListener('click', async () => {
    if (!modState) return;
    const out = $('mod-explanation');
    out.textContent = 'Thinking...';
    const apiKey = $('api-key-input').value.trim() || null;
    const result = await requestAIExplanation('moderation', modState.stats, apiKey);
    out.textContent = result.text;
  });

  // ---------- Quiz ----------
  let quiz = null;

  function startQuiz() {
    quiz = {
      questions: buildQuiz(String(Date.now()) + '-' + Math.random()),
      index: 0,
      score: 0,
      answers: [],
    };
    $('quiz-intro').hidden = true;
    $('quiz-result').hidden = true;
    $('quiz-question').hidden = false;
    renderQuestion();
  }

  function renderQuestion() {
    const q = quiz.questions[quiz.index];
    $('quiz-progress').textContent = 'Question ' + (quiz.index + 1) + ' of ' + quiz.questions.length +
      ' — ' + (q.type === 'fixed' ? 'Conceptual' : 'Live-computed');
    $('quiz-prompt').textContent = q.prompt;
    const choicesEl = $('quiz-choices');
    clearChildren(choicesEl);
    const feedback = $('quiz-feedback');
    feedback.hidden = true;
    feedback.textContent = '';
    $('quiz-next').hidden = true;

    q.choices.forEach((choiceText, idx) => {
      const btn = document.createElement('button');
      btn.className = 'quiz-choice-btn';
      btn.textContent = choiceText;
      btn.addEventListener('click', () => answerQuestion(idx));
      choicesEl.appendChild(btn);
    });
  }

  function answerQuestion(chosenIndex) {
    const q = quiz.questions[quiz.index];
    const correct = chosenIndex === q.correctIndex;
    if (correct) quiz.score++;
    quiz.answers.push({ chosenIndex, correct, question: q });

    const choicesEl = $('quiz-choices');
    Array.from(choicesEl.children).forEach((btn, idx) => {
      btn.disabled = true;
      if (idx === q.correctIndex) btn.classList.add('correct');
      else if (idx === chosenIndex) btn.classList.add('incorrect');
    });

    const feedback = $('quiz-feedback');
    feedback.hidden = false;
    feedback.textContent = (correct ? 'Correct. ' : 'Incorrect. ') + q.explanation;
    $('quiz-next').hidden = false;
  }

  $('quiz-next').addEventListener('click', () => {
    quiz.index++;
    if (quiz.index < quiz.questions.length) {
      renderQuestion();
    } else {
      finishQuiz();
    }
  });

  function finishQuiz() {
    $('quiz-question').hidden = true;
    $('quiz-result').hidden = false;
    $('quiz-score').textContent = 'Score: ' + quiz.score + ' / ' + quiz.questions.length;
    const reviewEl = $('quiz-review');
    clearChildren(reviewEl);
    quiz.answers.forEach((ans, i) => {
      const div = document.createElement('div');
      div.className = 'quiz-review-item';
      const tag = document.createElement('span');
      tag.className = 'tag';
      tag.textContent = '[' + (ans.question.type === 'fixed' ? 'Conceptual' : 'Live') + '] ';
      const promptSpan = document.createElement('strong');
      promptSpan.textContent = 'Q' + (i + 1) + ': ' + ans.question.prompt;
      const resultP = document.createElement('p');
      resultP.textContent = (ans.correct ? 'Correct — ' : 'Incorrect — ') + ans.question.explanation;
      div.appendChild(tag);
      div.appendChild(promptSpan);
      div.appendChild(resultP);
      reviewEl.appendChild(div);
    });
  }

  $('quiz-start').addEventListener('click', startQuiz);
  $('quiz-restart').addEventListener('click', startQuiz);
})();
