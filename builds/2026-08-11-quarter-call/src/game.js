// Pure game logic: date math, seeded shuffling, round selection, guess evaluation.
// No DOM access here so it can be exercised directly in tests.

function parseDateUTC(dateStr) {
  const [y, m, d] = dateStr.split('-').map(Number);
  return Date.UTC(y, m - 1, d); // JS months are 0-indexed; the bug this guards against
}

function daysBetween(dateStrA, dateStrB) {
  const msPerDay = 86400000;
  return Math.round((parseDateUTC(dateStrB) - parseDateUTC(dateStrA)) / msPerDay);
}

function stringToSeed(str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = (Math.imul(31, hash) + str.charCodeAt(i)) | 0;
  }
  return hash >>> 0;
}

function mulberry32(seed) {
  let a = seed >>> 0;
  return function () {
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function seededShuffle(array, seedStr) {
  const rng = mulberry32(stringToSeed(seedStr));
  const result = array.slice();
  for (let i = result.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    const tmp = result[i];
    result[i] = result[j];
    result[j] = tmp;
  }
  return result;
}

function dailyChallengeRounds(dateStr, roundsData, count) {
  if (!roundsData || roundsData.length === 0) return [];
  const n = Math.min(count, roundsData.length);
  const shuffled = seededShuffle(roundsData, `daily-${dateStr}`);
  return shuffled.slice(0, n);
}

function getNextPracticeRound(stats, roundsData) {
  const needsReshuffle =
    !stats.practiceOrder ||
    stats.practiceOrder.length !== roundsData.length ||
    stats.practiceIndex >= stats.practiceOrder.length;

  if (needsReshuffle) {
    stats.practiceCycle = (stats.practiceCycle || 0) + 1;
    stats.practiceOrder = seededShuffle(roundsData.map((r) => r.id), `practice-${stats.practiceCycle}`);
    stats.practiceIndex = 0;
  }

  const roundId = stats.practiceOrder[stats.practiceIndex];
  stats.practiceIndex += 1;
  return roundsData.find((r) => r.id === roundId) || null;
}

function evaluateGuess(guess, outcome) {
  return guess === outcome;
}
