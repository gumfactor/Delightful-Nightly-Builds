// Synapse Sort — localStorage persistence for daily-mode stats.
// Classic script, attaches helpers onto the shared SynapseSort namespace.

const STATS_KEY = "synapseSort.stats";
const THEME_KEY = "synapseSort.theme";

function defaultStats() {
  return {
    gamesPlayed: 0,
    wins: 0,
    currentStreak: 0,
    bestStreak: 0,
    totalMistakes: 0,
    lastPlayedDate: null,
    history: {}
  };
}

function getStats() {
  try {
    const raw = window.localStorage.getItem(STATS_KEY);
    if (!raw) return defaultStats();
    const parsed = JSON.parse(raw);
    return Object.assign(defaultStats(), parsed, { history: parsed.history || {} });
  } catch (err) {
    return defaultStats();
  }
}

function saveStats(stats) {
  window.localStorage.setItem(STATS_KEY, JSON.stringify(stats));
}

function hasPlayedDate(dateString) {
  const stats = getStats();
  return Object.prototype.hasOwnProperty.call(stats.history, dateString);
}

// Records a daily-mode result exactly once per date. Calling this again for
// a date already present in history is a no-op, so a page reload after a
// completed daily puzzle can never double-count a streak or a loss.
function recordDailyResult(dateString, won, mistakes) {
  const stats = getStats();
  if (Object.prototype.hasOwnProperty.call(stats.history, dateString)) {
    return stats;
  }
  stats.gamesPlayed += 1;
  stats.totalMistakes += mistakes;
  stats.lastPlayedDate = dateString;
  if (won) {
    stats.wins += 1;
    stats.currentStreak += 1;
    stats.bestStreak = Math.max(stats.bestStreak, stats.currentStreak);
  } else {
    stats.currentStreak = 0;
  }
  stats.history[dateString] = { won: won, mistakes: mistakes };
  saveStats(stats);
  return stats;
}

function resetStats() {
  window.localStorage.removeItem(STATS_KEY);
}

function getTheme() {
  return window.localStorage.getItem(THEME_KEY);
}

function setTheme(theme) {
  window.localStorage.setItem(THEME_KEY, theme);
}

window.SynapseSort = window.SynapseSort || {};
Object.assign(window.SynapseSort, {
  getStats: getStats,
  saveStats: saveStats,
  hasPlayedDate: hasPlayedDate,
  recordDailyResult: recordDailyResult,
  resetStats: resetStats,
  getTheme: getTheme,
  setTheme: setTheme
});
