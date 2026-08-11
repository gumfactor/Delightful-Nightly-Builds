// localStorage-backed persistent stats: streak, accuracy, per-sector breakdown,
// practice shuffle progress, and daily-challenge completion history.

const STATS_STORAGE_KEY = 'quarterCallStats';

function defaultStats() {
  return {
    streak: 0,
    bestStreak: 0,
    totalPlayed: 0,
    totalCorrect: 0,
    sectorStats: {},
    practiceOrder: null,
    practiceIndex: 0,
    practiceCycle: 0,
    dailyHistory: {},
  };
}

function loadStats() {
  try {
    const raw = localStorage.getItem(STATS_STORAGE_KEY);
    if (!raw) return defaultStats();
    const parsed = JSON.parse(raw);
    return Object.assign(defaultStats(), parsed);
  } catch (e) {
    return defaultStats();
  }
}

function saveStats(stats) {
  localStorage.setItem(STATS_STORAGE_KEY, JSON.stringify(stats));
}

function recordResult(stats, round, correct) {
  stats.totalPlayed += 1;
  if (correct) {
    stats.totalCorrect += 1;
    stats.streak += 1;
    stats.bestStreak = Math.max(stats.bestStreak, stats.streak);
  } else {
    stats.streak = 0;
  }
  const sector = round.sector || 'Unknown';
  if (!stats.sectorStats[sector]) stats.sectorStats[sector] = { played: 0, correct: 0 };
  stats.sectorStats[sector].played += 1;
  if (correct) stats.sectorStats[sector].correct += 1;
  return stats;
}

function accuracyPct(stats) {
  if (stats.totalPlayed === 0) return 0;
  return Math.round((stats.totalCorrect / stats.totalPlayed) * 1000) / 10;
}

function hasDailyCompleted(stats, dateStr) {
  return !!(stats.dailyHistory[dateStr] && stats.dailyHistory[dateStr].completed);
}

function recordDailyCompletion(stats, dateStr, results) {
  stats.dailyHistory[dateStr] = { completed: true, results: results.slice() };
  return stats;
}

function shareString(results) {
  return results.map((r) => (r === 'correct' ? '\u{1F7E9}' : '\u{1F7E5}')).join('');
}
