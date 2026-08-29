// Zebra Lab — DOM wiring: screens, grid rendering, localStorage-backed progress/stats.
// Depends on data.js, logic.js, ai.js being loaded first.

const ZL_STORAGE_KEYS = { progress: 'zebralab_progress', stats: 'zebralab_stats', daily: 'zebralab_daily' };
const ZL_MAX_HINTS = 2;

function zlDefaultProgress() {
  return { solvedByChapter: { 1: 0, 2: 0, 3: 0 } };
}

function zlLoadProgress() {
  try {
    const raw = localStorage.getItem(ZL_STORAGE_KEYS.progress);
    if (!raw) return zlDefaultProgress();
    const parsed = JSON.parse(raw);
    return Object.assign(zlDefaultProgress(), parsed);
  } catch (e) {
    return zlDefaultProgress();
  }
}

function zlSaveProgress(progress) {
  try {
    localStorage.setItem(ZL_STORAGE_KEYS.progress, JSON.stringify(progress));
  } catch (e) {
    // localStorage unavailable — progress just won't persist this session
  }
}

function zlIsChapterUnlocked(chapterId, progress) {
  const chapter = zlGetChapter(chapterId);
  if (!chapter.unlockRequirement) return true;
  const prevChapterId = chapterId - 1;
  return (progress.solvedByChapter[prevChapterId] || 0) >= chapter.unlockRequirement;
}

function zlDefaultStats() {
  return {
    totalSolved: 0,
    totalChecks: 0,
    totalHints: 0,
    currentStreak: 0,
    bestStreak: 0,
    lastDailyDate: null,
    fastestChecksByChapter: {},
  };
}

function zlLoadStats() {
  try {
    const raw = localStorage.getItem(ZL_STORAGE_KEYS.stats);
    if (!raw) return zlDefaultStats();
    return Object.assign(zlDefaultStats(), JSON.parse(raw));
  } catch (e) {
    return zlDefaultStats();
  }
}

function zlSaveStats(stats) {
  try {
    localStorage.setItem(ZL_STORAGE_KEYS.stats, JSON.stringify(stats));
  } catch (e) {
    // localStorage unavailable — stats just won't persist this session
  }
}

function zlLoadDaily() {
  try {
    const raw = localStorage.getItem(ZL_STORAGE_KEYS.daily);
    return raw ? JSON.parse(raw) : null;
  } catch (e) {
    return null;
  }
}

function zlSaveDaily(daily) {
  try {
    localStorage.setItem(ZL_STORAGE_KEYS.daily, JSON.stringify(daily));
  } catch (e) {
    // localStorage unavailable
  }
}

function zlIsDailyCompletedToday(dateStr) {
  const d = zlLoadDaily();
  return !!(d && d.date === dateStr && d.completed);
}

function zlUpdateStreakOnDailyComplete(stats, dateStr) {
  const prevDate = stats.lastDailyDate;
  let continued = false;
  if (prevDate) {
    const prev = new Date(prevDate + 'T00:00:00Z');
    const cur = new Date(dateStr + 'T00:00:00Z');
    const diffDays = Math.round((cur - prev) / 86400000);
    continued = diffDays === 1;
  }
  stats.currentStreak = continued ? stats.currentStreak + 1 : 1;
  stats.bestStreak = Math.max(stats.bestStreak, stats.currentStreak);
  stats.lastDailyDate = dateStr;
  return stats;
}

(function () {
  const state = {
    screen: 'home',
    mode: null,
    chapterId: null,
    dateStr: null,
    puzzle: null,
    playerAssign: null,
    checksUsed: 0,
    hintsUsed: 0,
    solved: false,
  };

  function showScreen(name) {
    state.screen = name;
    ['home', 'puzzle', 'result'].forEach(function (s) {
      const el = document.getElementById('screen-' + s);
      if (el) el.hidden = s !== name;
    });
  }

  function initPlayerAssign(puzzle) {
    const assign = {};
    puzzle.categories
      .filter(function (c) {
        return c.id !== 'position';
      })
      .forEach(function (cat) {
        assign[cat.id] = new Array(puzzle.size).fill(-1);
      });
    return assign;
  }

  function startPuzzle(mode, chapterId) {
    let puzzle;
    let dateStr = null;
    if (mode === 'daily') {
      dateStr = zlTodayUtcString();
      puzzle = zlGenerateDailyPuzzle(dateStr);
      chapterId = 2;
    } else {
      const seed = 'practice-' + chapterId + '-' + Date.now() + '-' + Math.floor(Math.random() * 1e9);
      puzzle = zlGeneratePuzzle(chapterId, seed);
    }
    state.mode = mode;
    state.chapterId = chapterId;
    state.dateStr = dateStr;
    state.puzzle = puzzle;
    state.playerAssign = initPlayerAssign(puzzle);
    state.checksUsed = 0;
    state.hintsUsed = 0;
    state.solved = false;
    renderPuzzleScreen();
    showScreen('puzzle');
  }

  function renderPuzzleScreen() {
    const puzzle = state.puzzle;
    const clueList = document.getElementById('clue-list');
    clueList.innerHTML = '';
    puzzle.clues.forEach(function (clue) {
      const li = document.createElement('li');
      li.setAttribute('data-testid', 'clue-item');
      li.textContent = zlFormatClue(clue, puzzle.categories);
      clueList.appendChild(li);
    });

    const attrCats = puzzle.categories.filter(function (c) {
      return c.id !== 'position';
    });
    const table = document.getElementById('answer-grid');
    table.innerHTML = '';
    const thead = document.createElement('thead');
    const headRow = document.createElement('tr');
    headRow.appendChild(document.createElement('th'));
    attrCats.forEach(function (cat) {
      const th = document.createElement('th');
      th.textContent = cat.label;
      headRow.appendChild(th);
    });
    thead.appendChild(headRow);
    table.appendChild(thead);

    const tbody = document.createElement('tbody');
    for (let p = 0; p < puzzle.size; p++) {
      const tr = document.createElement('tr');
      const rowHead = document.createElement('th');
      rowHead.textContent = 'Study #' + (p + 1);
      tr.appendChild(rowHead);
      attrCats.forEach(function (cat) {
        const td = document.createElement('td');
        const select = document.createElement('select');
        select.setAttribute('data-testid', 'grid-select-' + cat.id + '-' + p);
        select.setAttribute('aria-label', cat.label + ' for Study #' + (p + 1));
        const blankOpt = document.createElement('option');
        blankOpt.value = '-1';
        blankOpt.textContent = '—';
        select.appendChild(blankOpt);
        cat.values.forEach(function (v, vi) {
          const opt = document.createElement('option');
          opt.value = String(vi);
          opt.textContent = v.label;
          select.appendChild(opt);
        });
        select.value = String(state.playerAssign[cat.id][p]);
        select.addEventListener('change', function () {
          state.playerAssign[cat.id][p] = parseInt(select.value, 10);
        });
        td.appendChild(select);
        tr.appendChild(td);
      });
      tbody.appendChild(tr);
    }
    table.appendChild(tbody);

    document.getElementById('check-feedback').textContent = '';
    document.getElementById('hint-count').textContent = String(ZL_MAX_HINTS - state.hintsUsed);
    document.getElementById('checks-used').textContent = String(state.checksUsed);
    document.getElementById('puzzle-chapter-label').textContent =
      (state.mode === 'daily' ? 'Daily Challenge — ' : 'Practice — ') + puzzle.chapterName;
  }

  function handleCheck() {
    state.checksUsed++;
    const correctCount = zlCountCorrectPositions(state.puzzle, state.playerAssign);
    document.getElementById('checks-used').textContent = String(state.checksUsed);
    const feedback = document.getElementById('check-feedback');
    if (correctCount === state.puzzle.size) {
      state.solved = true;
      feedback.textContent = 'Solved! ' + correctCount + ' of ' + state.puzzle.size + ' studies fully correct.';
      onPuzzleSolved();
    } else {
      feedback.textContent = correctCount + ' of ' + state.puzzle.size + ' studies are fully correct.';
    }
  }

  function handleHint() {
    if (state.hintsUsed >= ZL_MAX_HINTS) return;
    const pos = zlPickHintPosition(state.puzzle, state.playerAssign, Math.random);
    const attrCats = state.puzzle.categories.filter(function (c) {
      return c.id !== 'position';
    });
    attrCats.forEach(function (cat) {
      state.playerAssign[cat.id][pos] = state.puzzle.solution[cat.id][pos];
      const select = document.querySelector('[data-testid="grid-select-' + cat.id + '-' + pos + '"]');
      if (select) select.value = String(state.puzzle.solution[cat.id][pos]);
    });
    state.hintsUsed++;
    document.getElementById('hint-count').textContent = String(ZL_MAX_HINTS - state.hintsUsed);
  }

  function onPuzzleSolved() {
    const progress = zlLoadProgress();
    progress.solvedByChapter[state.chapterId] = (progress.solvedByChapter[state.chapterId] || 0) + 1;
    zlSaveProgress(progress);

    const stats = zlLoadStats();
    stats.totalSolved++;
    stats.totalChecks += state.checksUsed;
    stats.totalHints += state.hintsUsed;
    const key = 'ch' + state.chapterId;
    if (!stats.fastestChecksByChapter[key] || state.checksUsed < stats.fastestChecksByChapter[key]) {
      stats.fastestChecksByChapter[key] = state.checksUsed;
    }
    if (state.mode === 'daily') {
      zlUpdateStreakOnDailyComplete(stats, state.dateStr);
      zlSaveDaily({ date: state.dateStr, completed: true, checksUsed: state.checksUsed, hintsUsed: state.hintsUsed });
    }
    zlSaveStats(stats);

    setTimeout(function () {
      renderResultScreen();
      showScreen('result');
    }, 500);
  }

  function renderResultScreen() {
    document.getElementById('result-summary').textContent =
      'Solved in ' + state.checksUsed + ' check(s) and ' + state.hintsUsed + ' hint(s).';
    const shareBtn = document.getElementById('btn-share');
    const shareRow = document.getElementById('share-row');
    const shareText = document.getElementById('share-text');
    if (state.mode === 'daily') {
      shareText.value = zlBuildShareString(state.dateStr, state.checksUsed, state.hintsUsed, true);
      shareRow.hidden = false;
    } else {
      shareText.value = '';
      shareRow.hidden = true;
    }
    void shareBtn;

    const pair = zlPickExplainerPair(state.puzzle);
    const aiPanel = document.getElementById('ai-panel');
    if (pair) {
      aiPanel.hidden = false;
      const apiKey = zlGetSessionApiKey();
      const textEl = document.getElementById('ai-explanation-text');
      textEl.textContent = 'Loading explanation…';
      zlFetchAIExplanation(pair, apiKey).then(function (res) {
        textEl.textContent = res.text;
        textEl.setAttribute('data-source', res.source);
      });
    } else {
      aiPanel.hidden = true;
    }
  }

  function renderHomeScreen() {
    const progress = zlLoadProgress();
    const stats = zlLoadStats();
    const dateStr = zlTodayUtcString();
    const dailyDone = zlIsDailyCompletedToday(dateStr);
    const dailyBtn = document.getElementById('btn-daily');
    dailyBtn.disabled = dailyDone;
    dailyBtn.textContent = dailyDone ? 'Daily Challenge — Completed Today' : 'Play Daily Challenge';

    const chapterList = document.getElementById('chapter-list');
    chapterList.innerHTML = '';
    ZL_CHAPTERS.forEach(function (chapter) {
      const unlocked = zlIsChapterUnlocked(chapter.id, progress);
      const li = document.createElement('li');
      li.setAttribute('data-testid', 'chapter-row-' + chapter.id);
      const solvedCount = progress.solvedByChapter[chapter.id] || 0;
      const label = document.createElement('span');
      label.textContent =
        'Chapter ' + chapter.id + ': ' + chapter.name + ' — solved ' + solvedCount + 'x' + (unlocked ? '' : ' (locked)');
      li.appendChild(label);
      const btn = document.createElement('button');
      btn.textContent = 'Practice';
      btn.setAttribute('data-testid', 'btn-practice-' + chapter.id);
      btn.disabled = !unlocked;
      btn.addEventListener('click', function () {
        startPuzzle('practice', chapter.id);
      });
      li.appendChild(btn);
      chapterList.appendChild(li);
    });

    document.getElementById('stats-total-solved').textContent = String(stats.totalSolved);
    document.getElementById('stats-current-streak').textContent = String(stats.currentStreak);
    document.getElementById('stats-best-streak').textContent = String(stats.bestStreak);
  }

  function init() {
    document.getElementById('btn-daily').addEventListener('click', function () {
      startPuzzle('daily', 2);
    });
    document.getElementById('btn-check').addEventListener('click', handleCheck);
    document.getElementById('btn-hint').addEventListener('click', handleHint);
    document.getElementById('btn-back-to-menu').addEventListener('click', function () {
      renderHomeScreen();
      showScreen('home');
    });
    document.getElementById('btn-result-menu').addEventListener('click', function () {
      renderHomeScreen();
      showScreen('home');
    });
    document.getElementById('btn-play-again').addEventListener('click', function () {
      if (state.mode === 'daily') {
        renderHomeScreen();
        showScreen('home');
      } else {
        startPuzzle('practice', state.chapterId);
      }
    });
    document.getElementById('btn-copy-share').addEventListener('click', function () {
      const text = document.getElementById('share-text').value;
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).catch(function () {});
      }
    });
    const apiKeyInput = document.getElementById('api-key-input');
    apiKeyInput.addEventListener('change', function (e) {
      zlSetSessionApiKey(e.target.value.trim());
    });
    apiKeyInput.value = zlGetSessionApiKey();

    renderHomeScreen();
    showScreen('home');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  window.ZebraLab = {
    state: state,
    startPuzzle: startPuzzle,
    handleCheck: handleCheck,
    handleHint: handleHint,
    renderHomeScreen: renderHomeScreen,
    renderPuzzleScreen: renderPuzzleScreen,
    renderResultScreen: renderResultScreen,
    MAX_HINTS: ZL_MAX_HINTS,
  };
})();
