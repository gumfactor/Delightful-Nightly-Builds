// Heuristic Hunt — localStorage persistence helpers.
window.HH = window.HH || {};

HH.STORAGE_KEY = 'heuristicHunt_v1';

HH.defaultState = function () {
  var chapterProgress = {};
  [1, 2, 3].forEach(function (ch) {
    chapterProgress[ch] = { attempted: 0, correct: 0, unlocked: ch === 1 };
  });

  var biasMastery = {};
  HH.BIASES.forEach(function (b) {
    biasMastery[b.id] = { attempts: 0, correct: 0 };
  });

  return {
    chapterProgress: chapterProgress,
    biasMastery: biasMastery,
    dailyChallenge: { lastPlayedDate: null, lastResult: null, history: [] },
    bestStreak: 0,
    currentStreak: 0
  };
};

HH.loadState = function () {
  var raw;
  try {
    raw = window.localStorage.getItem(HH.STORAGE_KEY);
  } catch (e) {
    return HH.defaultState();
  }
  if (!raw) return HH.defaultState();

  try {
    var parsed = JSON.parse(raw);
    var fresh = HH.defaultState();
    // Merge shallowly against defaults so a partially-corrupt or older-shape
    // object never crashes the app — missing keys fall back to fresh values.
    return {
      chapterProgress: (parsed && parsed.chapterProgress) || fresh.chapterProgress,
      biasMastery: (parsed && parsed.biasMastery) || fresh.biasMastery,
      dailyChallenge: (parsed && parsed.dailyChallenge) || fresh.dailyChallenge,
      bestStreak: (parsed && typeof parsed.bestStreak === 'number') ? parsed.bestStreak : 0,
      currentStreak: (parsed && typeof parsed.currentStreak === 'number') ? parsed.currentStreak : 0
    };
  } catch (e) {
    return HH.defaultState();
  }
};

HH.saveState = function (state) {
  try {
    window.localStorage.setItem(HH.STORAGE_KEY, JSON.stringify(state));
  } catch (e) {
    // localStorage unavailable (e.g. private browsing quota) — fail silently,
    // the session still works, progress just won't persist.
  }
};

HH.resetState = function () {
  try {
    window.localStorage.removeItem(HH.STORAGE_KEY);
  } catch (e) {
    // ignore
  }
  return HH.defaultState();
};
