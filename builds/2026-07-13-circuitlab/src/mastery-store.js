/* CircuitLab mastery persistence: localStorage-backed 0-3 mastery level per region. */

var MASTERY_STORAGE_KEY = 'circuitlab_mastery_v1';
var SESSION_STORAGE_KEY = 'circuitlab_last_session_v1';
var MASTERY_MAX = 3;
var MASTERY_LABELS = ['New', 'Learning', 'Reviewing', 'Mastered'];

function defaultMastery() {
  var mastery = {};
  for (var i = 0; i < REGION_ORDER.length; i++) {
    mastery[REGION_ORDER[i]] = 0;
  }
  return mastery;
}

function loadMastery() {
  var mastery = defaultMastery();
  try {
    var raw = window.localStorage.getItem(MASTERY_STORAGE_KEY);
    if (raw) {
      var stored = JSON.parse(raw);
      for (var id in mastery) {
        if (typeof stored[id] === 'number' && stored[id] >= 0 && stored[id] <= MASTERY_MAX) {
          mastery[id] = stored[id];
        }
      }
    }
  } catch (err) {
    /* Corrupt or inaccessible storage: fall back to defaults silently. */
  }
  return mastery;
}

function saveMastery(mastery) {
  try {
    window.localStorage.setItem(MASTERY_STORAGE_KEY, JSON.stringify(mastery));
  } catch (err) {
    /* Storage unavailable (e.g. private browsing quota): progress just won't persist. */
  }
}

function updateMastery(mastery, regionId, correct) {
  var next = {};
  for (var id in mastery) {
    next[id] = mastery[id];
  }
  if (!(regionId in next)) {
    return next;
  }
  if (correct) {
    next[regionId] = Math.min(MASTERY_MAX, next[regionId] + 1);
  } else {
    next[regionId] = 0;
  }
  saveMastery(next);
  return next;
}

function resetMastery() {
  var fresh = defaultMastery();
  try {
    window.localStorage.removeItem(MASTERY_STORAGE_KEY);
    window.localStorage.removeItem(SESSION_STORAGE_KEY);
  } catch (err) {
    /* ignore */
  }
  return fresh;
}

function saveLastSession(summary) {
  try {
    window.localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(summary));
  } catch (err) {
    /* ignore */
  }
}

function loadLastSession() {
  try {
    var raw = window.localStorage.getItem(SESSION_STORAGE_KEY);
    if (raw) {
      return JSON.parse(raw);
    }
  } catch (err) {
    /* ignore */
  }
  return null;
}

function overallMasteryPercent(mastery) {
  var total = 0;
  var count = 0;
  for (var id in mastery) {
    total += mastery[id];
    count += 1;
  }
  if (count === 0) {
    return 0;
  }
  return Math.round((total / (count * MASTERY_MAX)) * 100);
}
