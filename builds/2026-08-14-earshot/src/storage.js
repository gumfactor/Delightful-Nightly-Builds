/**
 * localStorage-backed persistence for calibration settings and session log.
 * All reads/writes go through this module so the schema stays in one place.
 */

const STORAGE_KEY = 'earshot:v1';
const SCHEMA_VERSION = 1;

function defaultState() {
  return {
    schemaVersion: SCHEMA_VERSION,
    calibration: {
      offsetDb: 0,
      calibratedAt: null,
      referenceLabel: null,
    },
    sessions: [],
  };
}

function loadState() {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return defaultState();
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== 'object' || parsed.schemaVersion !== SCHEMA_VERSION) {
      return defaultState();
    }
    if (!Array.isArray(parsed.sessions)) parsed.sessions = [];
    if (!parsed.calibration) parsed.calibration = defaultState().calibration;
    return parsed;
  } catch (err) {
    return defaultState();
  }
}

function saveState(state) {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function saveCalibration(state, offsetDb, referenceLabel) {
  state.calibration = {
    offsetDb,
    calibratedAt: new Date().toISOString(),
    referenceLabel,
  };
  saveState(state);
  return state;
}

function resetCalibration(state) {
  state.calibration = defaultState().calibration;
  saveState(state);
  return state;
}

/** Downsample a raw {t, db} series to roughly one point per whole second. */
function downsampleSeries(rawSeries) {
  const seen = new Map();
  for (const point of rawSeries) {
    const bucket = Math.floor(point.t);
    // keep the last reading in each 1-second bucket
    seen.set(bucket, { t: bucket, db: point.db });
  }
  return Array.from(seen.values()).sort((a, b) => a.t - b.t);
}

function addSession(state, session) {
  const record = {
    id: session.id,
    venue: session.venue,
    note: session.note || '',
    startedAt: session.startedAt,
    endedAt: session.endedAt,
    durationSec: session.durationSec,
    avgDb: session.avgDb,
    peakDb: session.peakDb,
    doseDeltaPct: session.doseDeltaPct,
    series: downsampleSeries(session.series || []),
  };
  state.sessions.push(record);
  saveState(state);
  return record;
}

function deleteSession(state, id) {
  state.sessions = state.sessions.filter((s) => s.id !== id);
  saveState(state);
  return state;
}

/** Sum of doseDeltaPct for sessions ended within the last 24 hours of `nowIso`. */
function cumulativeDosePct(state, nowIso) {
  const now = new Date(nowIso).getTime();
  const windowMs = 24 * 60 * 60 * 1000;
  return state.sessions
    .filter((s) => {
      const ended = new Date(s.endedAt).getTime();
      return now - ended <= windowMs && now - ended >= 0;
    })
    .reduce((sum, s) => sum + (s.doseDeltaPct || 0), 0);
}

function genId() {
  return `s_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    STORAGE_KEY,
    SCHEMA_VERSION,
    defaultState,
    loadState,
    saveState,
    saveCalibration,
    resetCalibration,
    downsampleSeries,
    addSession,
    deleteSession,
    cumulativeDosePct,
    genId,
  };
}
