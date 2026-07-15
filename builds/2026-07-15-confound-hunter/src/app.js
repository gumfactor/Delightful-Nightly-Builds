// Confound Hunter — game engine. Classic script, relies on globals from data.js.

var STORAGE_KEYS = {
  progress: 'confoundHunter_progress',
  mastery: 'confoundHunter_mastery',
  daily: 'confoundHunter_daily'
};

var CHAPTER_NAMES = { 1: 'Classic Flaws', 2: 'Level Up', 3: 'Detective Finals' };

var currentSession = null;

function qs(id) { return document.getElementById(id); }

function showScreen(id) {
  var screens = document.querySelectorAll('.screen');
  for (var i = 0; i < screens.length; i++) screens[i].classList.add('hidden');
  qs(id).classList.remove('hidden');
}

function loadJSON(key, fallback) {
  try {
    var raw = localStorage.getItem(key);
    if (!raw) return fallback;
    return JSON.parse(raw);
  } catch (e) {
    return fallback;
  }
}
function saveJSON(key, value) {
  localStorage.setItem(key, JSON.stringify(value));
}

function defaultProgress() {
  return {
    '1': { passed: false, bestAccuracy: 0 },
    '2': { passed: false, bestAccuracy: 0 },
    '3': { passed: false, bestAccuracy: 0 }
  };
}
function getProgress() { return loadJSON(STORAGE_KEYS.progress, defaultProgress()); }
function saveProgress(p) { saveJSON(STORAGE_KEYS.progress, p); }

function defaultMastery() {
  var m = {};
  FLAW_ORDER.forEach(function (f) { m[f] = { correct: 0, total: 0 }; });
  return m;
}
function getMastery() { return loadJSON(STORAGE_KEYS.mastery, defaultMastery()); }
function saveMastery(m) { saveJSON(STORAGE_KEYS.mastery, m); }

function getDaily() { return loadJSON(STORAGE_KEYS.daily, null); }
function saveDaily(d) { saveJSON(STORAGE_KEYS.daily, d); }

function recordMastery(flawId, correct) {
  var m = getMastery();
  if (!m[flawId]) m[flawId] = { correct: 0, total: 0 };
  m[flawId].total += 1;
  if (correct) m[flawId].correct += 1;
  saveMastery(m);
}

function todayUTCString(d) {
  d = d || new Date();
  var y = d.getUTCFullYear();
  var m = String(d.getUTCMonth() + 1).padStart(2, '0');
  var day = String(d.getUTCDate()).padStart(2, '0');
  return y + '-' + m + '-' + day;
}

function mulberry32(seed) {
  return function () {
    seed |= 0;
    seed = (seed + 0x6D2B79F5) | 0;
    var t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function hashString(str) {
  var h = 0;
  for (var i = 0; i < str.length; i++) {
    h = (Math.imul(31, h) + str.charCodeAt(i)) | 0;
  }
  return h;
}

function pickDailyVignetteIds(dateStr) {
  var rand = mulberry32(hashString(dateStr));
  var pool = VIGNETTES.map(function (v) { return v.id; });
  var picked = [];
  for (var i = 0; i < 5 && pool.length > 0; i++) {
    var idx = Math.floor(rand() * pool.length);
    picked.push(pool[idx]);
    pool.splice(idx, 1);
  }
  return picked;
}

function gradeFor(pct) {
  if (pct >= 90) return 'A';
  if (pct >= 80) return 'B';
  if (pct >= 70) return 'C';
  if (pct >= 60) return 'D';
  return 'F';
}

function vignetteById(id) {
  for (var i = 0; i < VIGNETTES.length; i++) {
    if (VIGNETTES[i].id === id) return VIGNETTES[i];
  }
  return null;
}

function currentVignette() {
  var id = currentSession.vignetteIds[currentSession.index];
  return vignetteById(id);
}

function startChapter(chapterNum) {
  var progress = getProgress();
  if (chapterNum > 1) {
    var prev = progress[String(chapterNum - 1)];
    if (!prev || !prev.passed) return;
  }
  var ids = VIGNETTES.filter(function (v) { return v.chapter === chapterNum; })
    .map(function (v) { return v.id; });
  currentSession = {
    mode: 'practice',
    chapter: chapterNum,
    vignetteIds: ids,
    index: 0,
    correctCount: 0,
    streak: 0,
    results: []
  };
  showScreen('screen-play');
  renderQuestion();
}

function startDaily() {
  var today = todayUTCString();
  var daily = getDaily();
  if (daily && daily.date === today) {
    renderDailyResult(daily);
    return;
  }
  var ids = pickDailyVignetteIds(today);
  currentSession = {
    mode: 'daily',
    vignetteIds: ids,
    index: 0,
    correctCount: 0,
    streak: 0,
    results: []
  };
  showScreen('screen-play');
  renderQuestion();
}

function renderQuestion() {
  var v = currentVignette();
  qs('vignette-text').textContent = v.text;
  qs('progress-display').textContent =
    (currentSession.mode === 'daily' ? 'Daily ' : 'Question ') +
    (currentSession.index + 1) + ' / ' + currentSession.vignetteIds.length;
  qs('streak-display').textContent = 'Streak: ' + currentSession.streak;

  var grid = qs('options-grid');
  while (grid.firstChild) grid.removeChild(grid.firstChild);

  v.options.forEach(function (flawId, i) {
    var btn = document.createElement('button');
    btn.className = 'option-btn';
    btn.type = 'button';
    btn.setAttribute('data-testid', 'option-btn-' + i);
    btn.setAttribute('data-flaw', flawId);
    btn.textContent = FLAW_TYPES[flawId].name;
    btn.addEventListener('click', function () { handleAnswer(flawId, btn); });
    grid.appendChild(btn);
  });

  qs('feedback-panel').classList.add('hidden');
}

function handleAnswer(selectedFlaw, btnEl) {
  var v = currentVignette();
  var correct = selectedFlaw === v.flaw;
  recordMastery(v.flaw, correct);
  currentSession.results.push(correct);
  if (correct) {
    currentSession.correctCount++;
    currentSession.streak++;
  } else {
    currentSession.streak = 0;
  }

  var buttons = qs('options-grid').querySelectorAll('.option-btn');
  buttons.forEach(function (b) {
    b.disabled = true;
    var flawId = b.getAttribute('data-flaw');
    if (flawId === v.flaw) b.classList.add('correct');
    else if (b === btnEl) b.classList.add('incorrect');
  });

  qs('feedback-verdict').textContent = correct
    ? '✅ Correct!'
    : ('❌ Not quite — the flaw was: ' + FLAW_TYPES[v.flaw].name);
  qs('feedback-explanation').textContent = v.explanation;
  qs('streak-display').textContent = 'Streak: ' + currentSession.streak;
  qs('feedback-panel').classList.remove('hidden');
}

function finishSession() {
  if (currentSession.mode === 'practice') finishChapter();
  else finishDaily();
}

function finishChapter() {
  var total = currentSession.vignetteIds.length;
  var accuracy = Math.round((currentSession.correctCount / total) * 100);
  var grade = gradeFor(accuracy);
  var passed = accuracy >= 70;

  var progress = getProgress();
  var key = String(currentSession.chapter);
  var prev = progress[key] || { passed: false, bestAccuracy: 0 };
  progress[key] = {
    passed: prev.passed || passed,
    bestAccuracy: Math.max(prev.bestAccuracy, accuracy)
  };
  saveProgress(progress);

  qs('chapter-end-grade').textContent = 'Grade: ' + grade;
  qs('chapter-end-accuracy').textContent =
    currentSession.correctCount + ' / ' + total + ' correct (' + accuracy + '%)';

  var unlockMsg;
  if (currentSession.chapter >= 3 && passed) {
    unlockMsg = 'All chapters complete!';
  } else if (passed) {
    unlockMsg = 'Chapter ' + (currentSession.chapter + 1) + ' unlocked!';
  } else {
    unlockMsg = 'Score 70% or higher to unlock the next chapter. Try again!';
  }
  qs('chapter-end-unlock').textContent = unlockMsg;
  showScreen('screen-chapter-end');
}

function buildShareText(daily) {
  var correctCount = daily.results.filter(Boolean).length;
  var grid = daily.results.map(function (r) { return r ? '✅' : '❌'; }).join('');
  return 'Confound Hunter Daily ' + daily.date + ': ' + correctCount + '/' + daily.results.length + '\n' + grid;
}

function finishDaily() {
  var today = todayUTCString();
  var daily = {
    date: today,
    vignetteIds: currentSession.vignetteIds.slice(),
    results: currentSession.results.slice()
  };
  saveDaily(daily);
  renderDailyResult(daily);
}

function renderDailyResult(daily) {
  var correctCount = daily.results.filter(Boolean).length;
  qs('daily-result-score').textContent = correctCount + ' / ' + daily.results.length + ' correct';
  qs('daily-result-text').textContent = buildShareText(daily);
  qs('daily-copy-confirm').classList.add('hidden');
  showScreen('screen-daily-result');
}

function renderChapterList() {
  var progress = getProgress();
  var list = qs('chapter-list');
  while (list.firstChild) list.removeChild(list.firstChild);

  [1, 2, 3].forEach(function (num) {
    var unlocked = num === 1 || (progress[String(num - 1)] && progress[String(num - 1)].passed);
    var card = document.createElement('div');
    card.className = 'chapter-card' + (unlocked ? '' : ' locked');
    card.setAttribute('data-testid', 'chapter-card-' + num);
    if (!unlocked) card.setAttribute('data-locked', 'true');

    var best = progress[String(num)] ? progress[String(num)].bestAccuracy : 0;

    var h3 = document.createElement('h3');
    h3.textContent = 'Chapter ' + num + ': ' + CHAPTER_NAMES[num] + (unlocked ? '' : ' 🔒');
    var p = document.createElement('p');
    p.textContent = unlocked ? ('Best: ' + best + '%') : 'Pass the previous chapter at 70%+ to unlock';

    card.appendChild(h3);
    card.appendChild(p);
    if (unlocked) card.addEventListener('click', function () { startChapter(num); });
    list.appendChild(card);
  });
}

function renderMastery() {
  var mastery = getMastery();
  var list = qs('mastery-list');
  while (list.firstChild) list.removeChild(list.firstChild);

  FLAW_ORDER.forEach(function (flawId) {
    var stats = mastery[flawId] || { correct: 0, total: 0 };
    var pct = stats.total > 0 ? Math.round((stats.correct / stats.total) * 100) : 0;

    var row = document.createElement('div');
    row.className = 'mastery-row';
    row.setAttribute('data-testid', 'mastery-row-' + flawId);

    var label = document.createElement('div');
    label.className = 'mastery-row-label';
    var nameSpan = document.createElement('span');
    nameSpan.textContent = FLAW_TYPES[flawId].name;
    var pctSpan = document.createElement('span');
    pctSpan.setAttribute('data-testid', 'mastery-pct-' + flawId);
    pctSpan.textContent = stats.total > 0
      ? (pct + '% (' + stats.correct + '/' + stats.total + ')')
      : 'Not yet attempted';
    label.appendChild(nameSpan);
    label.appendChild(pctSpan);

    var track = document.createElement('div');
    track.className = 'mastery-bar-track';
    var fill = document.createElement('div');
    fill.className = 'mastery-bar-fill';
    fill.style.width = pct + '%';
    fill.setAttribute('data-testid', 'mastery-bar-' + flawId);
    track.appendChild(fill);

    row.appendChild(label);
    row.appendChild(track);
    list.appendChild(row);
  });
}

function resetAllProgress() {
  localStorage.removeItem(STORAGE_KEYS.progress);
  localStorage.removeItem(STORAGE_KEYS.mastery);
  localStorage.removeItem(STORAGE_KEYS.daily);
}

function showCopyConfirm() {
  qs('daily-copy-confirm').classList.remove('hidden');
}

// ---- Wire up navigation ----
qs('nav-practice').addEventListener('click', function () {
  renderChapterList();
  showScreen('screen-chapters');
});
qs('nav-daily').addEventListener('click', startDaily);
qs('nav-mastery').addEventListener('click', function () {
  renderMastery();
  showScreen('screen-mastery');
});
qs('nav-reset').addEventListener('click', function () {
  qs('reset-confirm-modal').classList.remove('hidden');
});
qs('reset-confirm-btn').addEventListener('click', function () {
  resetAllProgress();
  qs('reset-confirm-modal').classList.add('hidden');
  showScreen('screen-menu');
});
qs('reset-cancel-btn').addEventListener('click', function () {
  qs('reset-confirm-modal').classList.add('hidden');
});

var backButtons = document.querySelectorAll('[data-testid^="back-to-menu"]');
backButtons.forEach(function (b) {
  b.addEventListener('click', function () { showScreen('screen-menu'); });
});

qs('chapter-end-continue').addEventListener('click', function () {
  renderChapterList();
  showScreen('screen-chapters');
});

qs('next-btn').addEventListener('click', function () {
  currentSession.index++;
  if (currentSession.index >= currentSession.vignetteIds.length) {
    finishSession();
  } else {
    renderQuestion();
  }
});

qs('daily-share-btn').addEventListener('click', function () {
  var text = qs('daily-result-text').textContent;
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(showCopyConfirm, showCopyConfirm);
  } else {
    showCopyConfirm();
  }
});
