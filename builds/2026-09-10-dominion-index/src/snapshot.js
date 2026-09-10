// localStorage-backed "last visit" snapshot. Storage is injected so tests can
// supply a fake implementation instead of touching the real browser storage.

const SNAPSHOT_KEY = 'dominion-index:last-snapshot';

// snapshot: { fetchedAt: ISO string, industryTotals: [{name,count}], provinceTotals: [{name,count}] }
// Never throws — a storage error (quota exceeded, private-browsing lockout)
// is treated the same as "no snapshot saved" and reported via the return value.
function writeSnapshot(storage, snapshot) {
  try {
    storage.setItem(SNAPSHOT_KEY, JSON.stringify(snapshot));
    return true;
  } catch (err) {
    return false;
  }
}

// Returns the parsed snapshot, or null if none exists or it can't be read/parsed.
function readSnapshot(storage) {
  let raw;
  try {
    raw = storage.getItem(SNAPSHOT_KEY);
  } catch (err) {
    return null;
  }
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw);
    if (!parsed || !Array.isArray(parsed.industryTotals) || !Array.isArray(parsed.provinceTotals)) {
      return null;
    }
    return parsed;
  } catch (err) {
    return null;
  }
}

const snapshotApi = { readSnapshot, writeSnapshot, SNAPSHOT_KEY };

if (typeof module !== 'undefined' && module.exports) {
  module.exports = snapshotApi;
}
if (typeof window !== 'undefined') {
  window.DominionSnapshot = snapshotApi;
}
