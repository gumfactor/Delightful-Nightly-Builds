// Heuristic Hunt — deterministic date-seeded selection for the Daily Challenge.
// Uses a plain numeric hash + mulberry32 PRNG (not Math.random) so the same
// UTC date always produces the same 5 questions for every player, and so the
// selection logic itself is deterministic and testable independent of the
// system clock.
window.HH = window.HH || {};

HH.todayUTCString = function (d) {
  var date = d || new Date();
  var y = date.getUTCFullYear();
  var m = String(date.getUTCMonth() + 1).padStart(2, '0');
  var day = String(date.getUTCDate()).padStart(2, '0');
  return y + '-' + m + '-' + day;
};

HH.hashString = function (str) {
  var h = 1779033703 ^ str.length;
  for (var i = 0; i < str.length; i++) {
    h = Math.imul(h ^ str.charCodeAt(i), 3432918353);
    h = (h << 13) | (h >>> 19);
  }
  return function () {
    h = Math.imul(h ^ (h >>> 16), 2246822507);
    h = Math.imul(h ^ (h >>> 13), 3266489909);
    h ^= h >>> 16;
    return h >>> 0;
  };
};

HH.mulberry32 = function (seed) {
  var a = seed;
  return function () {
    a |= 0;
    a = (a + 0x6D2B79F5) | 0;
    var t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
};

// Deterministically shuffle `array` using a PRNG seeded from `seedString`.
// Returns a new array; does not mutate the input.
HH.seededShuffle = function (array, seedString) {
  var seedFn = HH.hashString(seedString);
  var seed = seedFn();
  var rand = HH.mulberry32(seed);
  var result = array.slice();
  for (var i = result.length - 1; i > 0; i--) {
    var j = Math.floor(rand() * (i + 1));
    var tmp = result[i];
    result[i] = result[j];
    result[j] = tmp;
  }
  return result;
};

// Returns the 5 vignettes for the Daily Challenge on a given UTC date string.
HH.dailyVignettes = function (dateString) {
  var shuffled = HH.seededShuffle(HH.VIGNETTES, 'heuristic-hunt-daily-' + dateString);
  return shuffled.slice(0, 5);
};
