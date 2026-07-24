// Heuristic Hunt — view routing, rendering, and game logic.
// Classic script, no ES modules, all DOM built via createElement/textContent
// (no innerHTML) so there is no script-injection surface even though every
// string used here is static, author-controlled content.
window.HH = window.HH || {};

(function () {
  var CHAPTER_UNLOCK_THRESHOLD = 0.7;
  var QUESTIONS_PER_CHAPTER = 10;
  var DAILY_QUESTION_COUNT = 5;

  var state = HH.loadState();

  // Transient in-memory session (not persisted) driving the current quiz run.
  var session = null;

  function biasById(id) {
    return HH.BIASES.filter(function (b) { return b.id === id; })[0];
  }

  function vignettesForChapter(ch) {
    return HH.VIGNETTES.filter(function (v) { return v.chapter === ch; });
  }

  function el(tag, opts, children) {
    var node = document.createElement(tag);
    opts = opts || {};
    if (opts.className) node.className = opts.className;
    if (opts.testid) node.setAttribute('data-testid', opts.testid);
    if (opts.text !== undefined) node.textContent = opts.text;
    if (opts.disabled) node.disabled = true;
    if (opts.onClick) node.addEventListener('click', opts.onClick);
    (children || []).forEach(function (c) { if (c) node.appendChild(c); });
    return node;
  }

  function clearApp() {
    var app = document.getElementById('app');
    while (app.firstChild) app.removeChild(app.firstChild);
    return app;
  }

  function persist() {
    HH.saveState(state);
  }

  function recordBiasAnswer(biasId, isCorrect) {
    var m = state.biasMastery[biasId];
    if (!m) { m = { attempts: 0, correct: 0 }; state.biasMastery[biasId] = m; }
    m.attempts += 1;
    if (isCorrect) m.correct += 1;
  }

  function recordStreak(isCorrect) {
    if (isCorrect) {
      state.currentStreak += 1;
      if (state.currentStreak > state.bestStreak) state.bestStreak = state.currentStreak;
    } else {
      state.currentStreak = 0;
    }
  }

  function accuracyPct(correct, attempts) {
    if (!attempts) return 0;
    return Math.round((correct / attempts) * 100);
  }

  function masteryLevel(correct, attempts) {
    if (!attempts) return 'none';
    var pct = accuracyPct(correct, attempts);
    if (pct >= 80) return 'high';
    if (pct >= 50) return 'mid';
    return 'low';
  }

  // ---------- Views ----------

  function renderMenu() {
    var app = clearApp();
    var view = el('div', { className: 'view', testid: 'menu-view' });

    view.appendChild(el('h1', { text: 'Heuristic Hunt' }));
    view.appendChild(el('p', { className: 'subtitle', text: 'Spot the cognitive bias behind each real-world decision.' }));

    var streakLine = el('p', { className: 'streak-line', testid: 'streak-line',
      text: 'Current streak: ' + state.currentStreak + ' | Best streak: ' + state.bestStreak });
    view.appendChild(streakLine);

    var menuList = el('div', { className: 'menu-list' }, [
      el('button', { className: 'menu-btn', testid: 'btn-campaign', text: 'Play Campaign', onClick: renderChapterSelect }),
      el('button', { className: 'menu-btn', testid: 'btn-daily', text: 'Daily Challenge', onClick: renderDailyEntry }),
      el('button', { className: 'menu-btn', testid: 'btn-practice', text: 'Practice by Bias', onClick: renderPracticeSelect }),
      el('button', { className: 'menu-btn', testid: 'btn-mastery', text: 'Mastery Dashboard', onClick: renderMasteryDashboard }),
      el('button', { className: 'menu-btn menu-btn-secondary', testid: 'btn-reset', text: 'Reset Progress', onClick: renderResetConfirm })
    ]);
    view.appendChild(menuList);

    app.appendChild(view);
  }

  function renderChapterSelect() {
    var app = clearApp();
    var view = el('div', { className: 'view', testid: 'chapter-select-view' });
    view.appendChild(el('h2', { text: 'Campaign' }));
    view.appendChild(backButton(renderMenu));

    [1, 2, 3].forEach(function (ch) {
      var prog = state.chapterProgress[ch];
      var card = el('div', { className: 'chapter-card', testid: 'chapter-card-' + ch });
      card.appendChild(el('h3', { text: 'Chapter ' + ch }));
      var statusText = prog.unlocked
        ? (prog.attempted > 0 ? 'Lifetime accuracy: ' + accuracyPct(prog.correct, prog.attempted) + '%' : 'Not yet played')
        : 'Locked — reach ' + Math.round(CHAPTER_UNLOCK_THRESHOLD * 100) + '% on the previous chapter to unlock';
      card.appendChild(el('p', { text: statusText }));
      var playBtn = el('button', {
        className: 'menu-btn',
        testid: 'chapter-play-' + ch,
        text: prog.unlocked ? 'Play Chapter ' + ch : 'Locked',
        disabled: !prog.unlocked,
        onClick: prog.unlocked ? function () { startChapterSession(ch); } : null
      });
      card.appendChild(playBtn);
      view.appendChild(card);
    });

    app.appendChild(view);
  }

  function backButton(onClick) {
    return el('button', { className: 'back-btn', testid: 'btn-back', text: '← Back', onClick: onClick });
  }

  function startChapterSession(ch) {
    session = {
      mode: 'campaign',
      chapter: ch,
      questions: vignettesForChapter(ch),
      index: 0,
      correctCount: 0,
      answered: false,
      selectedId: null
    };
    renderQuestion();
  }

  function startPracticeSession(biasId) {
    var pool = biasId === 'all' ? HH.VIGNETTES : HH.VIGNETTES.filter(function (v) { return v.biasId === biasId; });
    var shuffled = pool.slice().sort(function () { return Math.random() - 0.5; });
    session = {
      mode: 'practice',
      questions: shuffled,
      index: 0,
      correctCount: 0,
      answered: false,
      selectedId: null
    };
    renderQuestion();
  }

  function startDailySession(dateString, vignettes) {
    session = {
      mode: 'daily',
      dateString: dateString,
      questions: vignettes,
      index: 0,
      correctCount: 0,
      answered: false,
      selectedId: null,
      resultSequence: []
    };
    renderQuestion();
  }

  function shuffledOptions(vignette) {
    var options = [vignette.biasId].concat(vignette.distractors);
    return options
      .map(function (id) { return { id: id, sort: Math.random() }; })
      .sort(function (a, b) { return a.sort - b.sort; })
      .map(function (o) { return o.id; });
  }

  function renderQuestion() {
    var app = clearApp();
    var v = session.questions[session.index];
    var view = el('div', { className: 'view', testid: 'question-view' });

    view.appendChild(el('p', { className: 'progress-line', testid: 'question-progress',
      text: 'Question ' + (session.index + 1) + ' of ' + session.questions.length }));
    view.appendChild(el('p', { className: 'vignette-text', testid: 'question-text', text: v.text }));

    if (!session._optionOrder || session._optionOrderFor !== v.id) {
      session._optionOrder = shuffledOptions(v);
      session._optionOrderFor = v.id;
    }

    var answersWrap = el('div', { className: 'answers-wrap' });
    session._optionOrder.forEach(function (biasId, idx) {
      var bias = biasById(biasId);
      var btn = el('button', {
        className: 'answer-btn',
        testid: 'answer-btn-' + idx,
        text: bias.name,
        disabled: session.answered,
        onClick: function () { handleAnswer(biasId); }
      });
      if (session.answered) {
        if (biasId === v.biasId) btn.classList.add('answer-correct');
        else if (biasId === session.selectedId) btn.classList.add('answer-incorrect');
      }
      answersWrap.appendChild(btn);
    });
    view.appendChild(answersWrap);

    if (session.answered) {
      var isCorrect = session.selectedId === v.biasId;
      var feedback = el('div', {
        className: 'feedback-panel ' + (isCorrect ? 'feedback-correct' : 'feedback-incorrect'),
        testid: 'feedback-panel'
      });
      feedback.setAttribute('data-result', isCorrect ? 'correct' : 'incorrect');
      feedback.appendChild(el('p', {
        className: 'feedback-headline',
        testid: isCorrect ? 'feedback-correct' : 'feedback-incorrect',
        text: isCorrect ? 'Correct!' : 'Not quite — the correct answer is ' + biasById(v.biasId).name + '.'
      }));
      feedback.appendChild(el('p', { className: 'explanation-text', testid: 'explanation-text', text: v.explanation }));
      view.appendChild(feedback);

      var isLast = session.index === session.questions.length - 1;
      view.appendChild(el('button', {
        className: 'menu-btn',
        testid: 'btn-next',
        text: isLast ? 'See Results' : 'Next Question',
        onClick: advanceQuestion
      }));
    }

    app.appendChild(view);
  }

  function handleAnswer(selectedBiasId) {
    if (session.answered) return;
    var v = session.questions[session.index];
    var isCorrect = selectedBiasId === v.biasId;
    session.answered = true;
    session.selectedId = selectedBiasId;
    if (isCorrect) session.correctCount += 1;

    recordBiasAnswer(v.biasId, isCorrect);
    recordStreak(isCorrect);

    if (session.mode === 'daily') {
      session.resultSequence.push(isCorrect);
    }
    if (session.mode === 'campaign') {
      var prog = state.chapterProgress[session.chapter];
      prog.attempted += 1;
      if (isCorrect) prog.correct += 1;
    }
    persist();
    renderQuestion();
  }

  function advanceQuestion() {
    if (session.index < session.questions.length - 1) {
      session.index += 1;
      session.answered = false;
      session.selectedId = null;
      renderQuestion();
    } else {
      finishSession();
    }
  }

  function finishSession() {
    if (session.mode === 'campaign') {
      renderChapterComplete();
    } else if (session.mode === 'daily') {
      var grid = session.resultSequence.map(function (ok) { return ok ? '🟩' : '🟥'; }).join('');
      var result = { score: session.correctCount, total: session.questions.length, grid: grid, date: session.dateString };
      state.dailyChallenge.lastPlayedDate = session.dateString;
      state.dailyChallenge.lastResult = result;
      state.dailyChallenge.history.push(result);
      persist();
      renderDailyResult(result);
    } else {
      renderPracticeComplete();
    }
  }

  function renderChapterComplete() {
    var app = clearApp();
    var ch = session.chapter;
    var accuracy = session.correctCount / session.questions.length;
    var passed = accuracy >= CHAPTER_UNLOCK_THRESHOLD;
    var unlockedNow = false;

    if (passed && ch < 3 && !state.chapterProgress[ch + 1].unlocked) {
      state.chapterProgress[ch + 1].unlocked = true;
      unlockedNow = true;
      persist();
    }

    var view = el('div', { className: 'view', testid: 'chapter-complete-view' });
    view.appendChild(el('h2', { text: 'Chapter ' + ch + ' Complete' }));
    view.appendChild(el('p', { className: 'accuracy-line', testid: 'chapter-complete-accuracy',
      text: session.correctCount + ' / ' + session.questions.length + ' correct (' + Math.round(accuracy * 100) + '%)' }));

    if (ch < 3) {
      var msg = unlockedNow
        ? 'Chapter ' + (ch + 1) + ' unlocked!'
        : (passed
          ? 'Chapter ' + (ch + 1) + ' already unlocked.'
          : 'You scored ' + Math.round(accuracy * 100) + '% — need ' + Math.round(CHAPTER_UNLOCK_THRESHOLD * 100) + '% or higher to unlock Chapter ' + (ch + 1) + '.');
      view.appendChild(el('p', { className: 'unlock-message', testid: 'chapter-complete-unlock-message', text: msg }));
    } else {
      view.appendChild(el('p', { className: 'unlock-message', testid: 'chapter-complete-unlock-message', text: 'You’ve completed the full campaign!' }));
    }

    view.appendChild(el('button', { className: 'menu-btn', testid: 'btn-back-to-chapters', text: 'Back to Chapters', onClick: renderChapterSelect }));
    view.appendChild(el('button', { className: 'menu-btn menu-btn-secondary', testid: 'btn-retry-chapter', text: 'Retry Chapter', onClick: function () { startChapterSession(ch); } }));

    app.appendChild(view);
  }

  function renderPracticeComplete() {
    var app = clearApp();
    var view = el('div', { className: 'view', testid: 'practice-complete-view' });
    view.appendChild(el('h2', { text: 'Practice Complete' }));
    view.appendChild(el('p', { className: 'accuracy-line', testid: 'practice-complete-accuracy',
      text: session.correctCount + ' / ' + session.questions.length + ' correct' }));
    view.appendChild(el('button', { className: 'menu-btn', testid: 'btn-back-to-menu', text: 'Back to Menu', onClick: renderMenu }));
    app.appendChild(view);
  }

  // ---------- Daily Challenge ----------

  function renderDailyEntry() {
    var app = clearApp();
    var today = HH.todayUTCString();
    var view = el('div', { className: 'view', testid: 'daily-view' });
    view.appendChild(el('h2', { text: 'Daily Challenge' }));
    view.appendChild(backButton(renderMenu));
    view.appendChild(el('p', { text: 'A new 5-question set every day (UTC), the same for everyone.' }));

    if (state.dailyChallenge.lastPlayedDate === today) {
      view.appendChild(el('p', { className: 'daily-locked', testid: 'daily-already-played',
        text: 'You already played today’s challenge. Come back after 00:00 UTC for a new one.' }));
      var last = state.dailyChallenge.lastResult;
      if (last) {
        view.appendChild(el('p', { className: 'daily-grid', testid: 'daily-last-grid', text: last.grid + '  ' + last.score + '/' + last.total }));
      }
    } else {
      view.appendChild(el('button', {
        className: 'menu-btn',
        testid: 'btn-start-daily',
        text: 'Start Today’s Challenge',
        onClick: function () { startDailySession(today, HH.dailyVignettes(today)); }
      }));
    }
    app.appendChild(view);
  }

  function renderDailyResult(result) {
    var app = clearApp();
    var view = el('div', { className: 'view', testid: 'daily-result-view' });
    view.appendChild(el('h2', { text: 'Daily Challenge Result' }));
    view.appendChild(el('p', { className: 'daily-grid', testid: 'daily-result-grid', text: result.grid }));
    view.appendChild(el('p', { className: 'daily-score', testid: 'daily-result-score', text: result.score + ' / ' + result.total + ' correct' }));

    var copyBtn = el('button', {
      className: 'menu-btn',
      testid: 'btn-copy-result',
      text: 'Copy Result',
      onClick: function () {
        var shareText = 'Heuristic Hunt ' + result.date + '\n' + result.grid + ' ' + result.score + '/' + result.total;
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(shareText).catch(function () {});
        }
        copyBtn.textContent = 'Copied!';
      }
    });
    view.appendChild(copyBtn);
    view.appendChild(el('button', { className: 'menu-btn menu-btn-secondary', testid: 'btn-back-to-menu', text: 'Back to Menu', onClick: renderMenu }));
    app.appendChild(view);
  }

  // ---------- Practice ----------

  function renderPracticeSelect() {
    var app = clearApp();
    var view = el('div', { className: 'view', testid: 'practice-select-view' });
    view.appendChild(el('h2', { text: 'Practice by Bias' }));
    view.appendChild(backButton(renderMenu));

    view.appendChild(el('button', {
      className: 'menu-btn',
      testid: 'practice-all-btn',
      text: 'All Biases (mixed)',
      onClick: function () { startPracticeSession('all'); }
    }));

    HH.BIASES.forEach(function (b) {
      var m = state.biasMastery[b.id];
      var pct = accuracyPct(m.correct, m.attempts);
      var row = el('div', { className: 'practice-row' });
      row.appendChild(el('button', {
        className: 'menu-btn menu-btn-list',
        testid: 'practice-bias-btn-' + b.id,
        text: b.name + (m.attempts > 0 ? ' (' + pct + '%)' : ' (not attempted)'),
        onClick: function () { startPracticeSession(b.id); }
      }));
      view.appendChild(row);
    });

    app.appendChild(view);
  }

  // ---------- Mastery Dashboard ----------

  function renderMasteryDashboard() {
    var app = clearApp();
    var view = el('div', { className: 'view', testid: 'mastery-view' });
    view.appendChild(el('h2', { text: 'Mastery Dashboard' }));
    view.appendChild(backButton(renderMenu));

    HH.BIASES.forEach(function (b) {
      var m = state.biasMastery[b.id];
      var pct = accuracyPct(m.correct, m.attempts);
      var level = masteryLevel(m.correct, m.attempts);
      var row = el('div', { className: 'mastery-row', testid: 'mastery-row-' + b.id });
      row.setAttribute('data-level', level);
      row.appendChild(el('span', { className: 'mastery-name', text: b.name }));
      var barOuter = el('div', { className: 'mastery-bar-outer' });
      var barInner = el('div', { className: 'mastery-bar-inner mastery-' + level, testid: 'mastery-bar-' + b.id });
      barInner.style.width = pct + '%';
      barOuter.appendChild(barInner);
      row.appendChild(barOuter);
      row.appendChild(el('span', { className: 'mastery-pct', testid: 'mastery-pct-' + b.id,
        text: m.attempts > 0 ? pct + '% (' + m.correct + '/' + m.attempts + ')' : 'Not attempted' }));
      view.appendChild(row);
    });

    app.appendChild(view);
  }

  // ---------- Reset ----------

  function renderResetConfirm() {
    var app = clearApp();
    var view = el('div', { className: 'view', testid: 'reset-confirm-view' });
    view.appendChild(el('h2', { text: 'Reset Progress?' }));
    view.appendChild(el('p', { text: 'This clears all chapter unlocks, mastery stats, streaks, and daily challenge history. This cannot be undone.' }));
    view.appendChild(el('button', {
      className: 'menu-btn menu-btn-danger',
      testid: 'btn-confirm-reset',
      text: 'Yes, Reset Everything',
      onClick: function () {
        state = HH.resetState();
        session = null;
        renderMenu();
      }
    }));
    view.appendChild(el('button', { className: 'menu-btn menu-btn-secondary', testid: 'btn-cancel-reset', text: 'Cancel', onClick: renderMenu }));
    app.appendChild(view);
  }

  // Expose a couple of internals for tests that want to inspect/reset state
  // without going through localStorage directly.
  HH._getState = function () { return state; };
  HH._reloadState = function () { state = HH.loadState(); };

  document.addEventListener('DOMContentLoaded', function () {
    renderMenu();
  });
})();
