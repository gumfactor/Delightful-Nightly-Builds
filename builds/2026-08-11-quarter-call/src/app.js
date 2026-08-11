// DOM wiring for Quarter Call. All dynamic content is inserted via textContent /
// createElement — never innerHTML — so untrusted round data can never execute.

(function () {
  'use strict';

  const state = {
    mode: 'practice',
    stats: null,
    currentRound: null,
    guessed: false,
    guess: null,
    dailyRounds: [],
    dailyIndex: 0,
    dailyResults: [],
    apiKey: '',
  };

  function $(testid) {
    return document.querySelector('[data-testid="' + testid + '"]');
  }

  function todayUTCString() {
    const now = new Date();
    const y = now.getUTCFullYear();
    const m = String(now.getUTCMonth() + 1).padStart(2, '0');
    const d = String(now.getUTCDate()).padStart(2, '0');
    return y + '-' + m + '-' + d;
  }

  function init() {
    state.stats = loadStats();

    const hasData = typeof ROUNDS_DATA !== 'undefined' && ROUNDS_DATA && ROUNDS_DATA.length > 0;
    if (!hasData) {
      $('no-data-banner').hidden = false;
      $('app').hidden = true;
      return;
    }

    wireEvents();
    updateStatsPanel();
    startPractice();
  }

  function wireEvents() {
    $('tab-practice').addEventListener('click', function () {
      state.mode = 'practice';
      setActiveTab();
      startPractice();
    });
    $('tab-daily').addEventListener('click', function () {
      state.mode = 'daily';
      setActiveTab();
      startDaily();
    });
    $('guess-up').addEventListener('click', function () {
      submitGuess('up');
    });
    $('guess-down').addEventListener('click', function () {
      submitGuess('down');
    });
    $('guess-flat').addEventListener('click', function () {
      submitGuess('flat');
    });
    $('next-round-btn').addEventListener('click', nextRound);

    const apiKeyInput = $('api-key-input');
    if (apiKeyInput) {
      apiKeyInput.addEventListener('input', function (e) {
        state.apiKey = e.target.value;
      });
    }
  }

  function setActiveTab() {
    $('tab-practice').setAttribute('aria-selected', String(state.mode === 'practice'));
    $('tab-daily').setAttribute('aria-selected', String(state.mode === 'daily'));
  }

  function startPractice() {
    state.dailyRounds = [];
    const round = getNextPracticeRound(state.stats, ROUNDS_DATA);
    saveStats(state.stats);
    showRound(round);
  }

  function startDaily() {
    const dateStr = todayUTCString();
    if (hasDailyCompleted(state.stats, dateStr)) {
      showDailyCompleteSummary(dateStr);
      return;
    }
    state.dailyRounds = dailyChallengeRounds(dateStr, ROUNDS_DATA, 5);
    state.dailyIndex = 0;
    state.dailyResults = [];
    showRound(state.dailyRounds[0]);
  }

  function showRound(round) {
    state.currentRound = round;
    state.guessed = false;
    state.guess = null;

    $('ticker').textContent = round.ticker;
    $('company').textContent = round.company;
    $('sector-badge').textContent = round.sector;
    $('industry-badge').textContent = round.industry;
    $('decision-date').textContent = 'As of ' + round.decisionDate;
    const returnSign = round.metrics.trailingReturnPct > 0 ? '+' : '';
    $('metric-return').textContent = '6-mo return: ' + returnSign + round.metrics.trailingReturnPct + '%';
    $('metric-vol').textContent = 'Annualized volatility: ' + round.metrics.annualizedVolatilityPct + '%';

    if (state.mode === 'daily') {
      $('progress-indicator').textContent = 'Round ' + (state.dailyIndex + 1) + ' of ' + state.dailyRounds.length;
      $('progress-indicator').hidden = false;
    } else {
      $('progress-indicator').hidden = true;
    }

    renderChart($('chart-canvas'), round.chart, {});

    $('reveal-panel').hidden = true;
    $('guess-buttons').hidden = false;
    $('daily-complete-banner').hidden = true;
    $('share-result').hidden = true;
  }

  function submitGuess(guess) {
    if (state.guessed || !state.currentRound) return;
    state.guessed = true;
    state.guess = guess;
    const round = state.currentRound;
    const correct = evaluateGuess(guess, round.forward.outcome);

    recordResult(state.stats, round, correct);
    if (state.mode === 'daily') {
      state.dailyResults.push(correct ? 'correct' : 'wrong');
    }
    saveStats(state.stats);

    renderReveal(round, correct);
    updateStatsPanel();
  }

  function renderReveal(round, correct) {
    $('guess-buttons').hidden = true;
    $('reveal-panel').hidden = false;
    $('reveal-result').textContent = correct
      ? 'Correct — ' + round.ticker + ' was ' + round.forward.outcome + '.'
      : 'Not this time — ' + round.ticker + ' was actually ' + round.forward.outcome + '.';
    $('reveal-result').dataset.outcome = correct ? 'correct' : 'wrong';
    const pctSign = round.forward.pctChange > 0 ? '+' : '';
    $('reveal-pct').textContent = pctSign + round.forward.pctChange + '% by ' + round.forward.endDate;

    renderRevealChart($('reveal-canvas'), round.chart, round.forward.chart);

    const noteEl = $('ai-note');
    noteEl.textContent = 'Loading note…';
    getAiOrFallbackNote(state.apiKey, round).then(function (note) {
      noteEl.textContent = note;
    });
  }

  function updateStatsPanel() {
    const s = state.stats;
    $('stat-streak').textContent = 'Streak: ' + s.streak;
    $('stat-best-streak').textContent = 'Best streak: ' + s.bestStreak;
    $('stat-accuracy').textContent = 'Accuracy: ' + accuracyPct(s) + '% (' + s.totalCorrect + '/' + s.totalPlayed + ')';

    const sectorEl = $('sector-stats');
    sectorEl.textContent = '';
    Object.keys(s.sectorStats)
      .sort()
      .forEach(function (sector) {
        const rec = s.sectorStats[sector];
        const row = document.createElement('div');
        row.dataset.testid = 'sector-stat-row';
        row.textContent = sector + ': ' + rec.correct + '/' + rec.played;
        sectorEl.appendChild(row);
      });
  }

  function nextRound() {
    if (state.mode === 'daily') {
      state.dailyIndex += 1;
      if (state.dailyIndex >= state.dailyRounds.length) {
        finishDaily();
        return;
      }
      showRound(state.dailyRounds[state.dailyIndex]);
    } else {
      startPractice();
    }
  }

  function finishDaily() {
    const dateStr = todayUTCString();
    recordDailyCompletion(state.stats, dateStr, state.dailyResults);
    saveStats(state.stats);
    showDailyCompleteSummary(dateStr);
  }

  function showDailyCompleteSummary(dateStr) {
    $('reveal-panel').hidden = true;
    $('guess-buttons').hidden = true;
    $('progress-indicator').hidden = true;

    const banner = $('daily-complete-banner');
    banner.hidden = false;
    banner.textContent = "Today's Daily Challenge is complete. Come back tomorrow for a new one.";

    const history = state.stats.dailyHistory[dateStr];
    const results = history ? history.results : [];
    const shareEl = $('share-result');
    shareEl.hidden = false;
    shareEl.textContent = 'Quarter Call ' + dateStr + '\n' + shareString(results);

    updateStatsPanel();
  }

  document.addEventListener('DOMContentLoaded', init);
})();
