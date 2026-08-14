/**
 * Pure dB / noise-exposure math. No DOM, no Web Audio, no localStorage —
 * every function here takes plain numbers/arrays and returns plain numbers,
 * so it can be unit-tested directly and reused by both the live meter and
 * the history/dose calculations.
 */

// Noise zone thresholds, in dB. Sourced from commonly cited NIOSH/WHO
// consumer-noise guidance (WHO 2018 environmental noise guidelines;
// NIOSH 85 dB / 8-hr occupational reference). These are round, well-known
// reference points, not a claim of clinical precision.
const ZONE_THRESHOLDS = {
  QUIET_MAX: 50, // below this: Quiet (library, quiet room)
  MODERATE_MAX: 70, // below this: Moderate (normal conversation, office)
  LOUD_MAX: 85, // below this: Loud (busy traffic, restaurant) — 85 dB is the NIOSH 8-hr occupational limit
  // >= LOUD_MAX: Hazardous
};

const ZONES = [
  { key: 'quiet', label: 'Quiet', max: ZONE_THRESHOLDS.QUIET_MAX, color: '#4ade80', icon: '●' },
  { key: 'moderate', label: 'Moderate', max: ZONE_THRESHOLDS.MODERATE_MAX, color: '#facc15', icon: '▲' },
  { key: 'loud', label: 'Loud', max: ZONE_THRESHOLDS.LOUD_MAX, color: '#fb923c', icon: '■' },
  { key: 'hazardous', label: 'Hazardous', max: Infinity, color: '#f87171', icon: '✕' },
];

/**
 * Simplified A-weighting attenuation approximation, in dB, per octave band
 * center frequency. This is NOT a full IEC 61672 A-weighting filter — it is
 * a small lookup table of well-known standard A-weighting correction values
 * at standard octave-band centers, used to attenuate a band-energy estimate.
 * Documented as an approximation in Manual.md.
 */
const A_WEIGHTING_TABLE = [
  { hz: 63, db: -26.2 },
  { hz: 125, db: -16.1 },
  { hz: 250, db: -8.6 },
  { hz: 500, db: -3.2 },
  { hz: 1000, db: 0.0 },
  { hz: 2000, db: 1.2 },
  { hz: 4000, db: 1.0 },
  { hz: 8000, db: -1.1 },
];

/** Linear interpolation of the A-weighting table at an arbitrary frequency. */
function aWeightingDb(hz) {
  if (hz <= A_WEIGHTING_TABLE[0].hz) return A_WEIGHTING_TABLE[0].db;
  const last = A_WEIGHTING_TABLE[A_WEIGHTING_TABLE.length - 1];
  if (hz >= last.hz) return last.db;
  for (let i = 0; i < A_WEIGHTING_TABLE.length - 1; i++) {
    const lo = A_WEIGHTING_TABLE[i];
    const hi = A_WEIGHTING_TABLE[i + 1];
    if (hz >= lo.hz && hz <= hi.hz) {
      const frac = (hz - lo.hz) / (hi.hz - lo.hz);
      return lo.db + frac * (hi.db - lo.db);
    }
  }
  return 0;
}

/** Root-mean-square of a Float32Array (or plain array) of samples in [-1, 1]. */
function computeRms(samples) {
  if (!samples || samples.length === 0) return 0;
  let sumSquares = 0;
  for (let i = 0; i < samples.length; i++) {
    sumSquares += samples[i] * samples[i];
  }
  return Math.sqrt(sumSquares / samples.length);
}

const MIN_RMS = 1e-8; // floor to avoid -Infinity on true silence

/**
 * Convert RMS amplitude (0-1 scale, dBFS-style) into an approximate dB(A)
 * reading using a calibration offset. The offset maps device-relative dBFS
 * onto an absolute dB(A) scale once the user has calibrated against a known
 * reference; with offset 0 the number is only relative/uncalibrated.
 */
function rmsToDb(rms, calibrationOffsetDb = 0) {
  const safeRms = Math.max(rms, MIN_RMS);
  const dbfs = 20 * Math.log10(safeRms);
  return dbfs + 94 + calibrationOffsetDb; // +94 centers a typical mid-level RMS near a plausible ambient dB range before calibration
}

/**
 * Apply an approximate A-weighting attenuation to a raw dB(FS)+offset value,
 * given the dominant frequency (Hz) of the current buffer (e.g. from an FFT
 * peak-bin estimate). Used as a small correction, not a full filter bank.
 */
function applyAWeighting(dbValue, dominantHz) {
  return dbValue + aWeightingDb(dominantHz);
}

/** Classify a dB(A) value into a noise zone. Boundaries are inclusive-low: exactly 50 is "moderate". */
function classifyZone(db) {
  for (const zone of ZONES) {
    if (db < zone.max) return zone;
  }
  return ZONES[ZONES.length - 1];
}

/**
 * NIOSH-style noise exposure dose using the standard 3 dB exchange rate:
 * permissible exposure time halves for every 3 dB above the 85 dB / 8-hour
 * reference. Returns the dose *fraction* (not percent) consumed by
 * `durationSec` seconds at a constant `avgDb` level.
 *
 * doseFraction = durationHours / permissibleHours
 * permissibleHours = 8 / 2^((avgDb - 85) / 3)
 */
function computeDoseFraction(avgDb, durationSec) {
  if (durationSec <= 0) return 0;
  const durationHours = durationSec / 3600;
  const permissibleHours = 8 / Math.pow(2, (avgDb - 85) / 3);
  return durationHours / permissibleHours;
}

/** Convenience wrapper returning dose as a percentage, rounded to 1 decimal. */
function computeDosePercent(avgDb, durationSec) {
  return Math.round(computeDoseFraction(avgDb, durationSec) * 1000) / 10;
}

/** Human-readable safety message for a cumulative daily dose percentage. */
function doseSafetyMessage(cumulativeDosePct) {
  if (cumulativeDosePct < 50) {
    return `You've used ${cumulativeDosePct.toFixed(1)}% of today's recommended noise dose — comfortably within the NIOSH daily limit.`;
  }
  if (cumulativeDosePct < 100) {
    return `You've used ${cumulativeDosePct.toFixed(1)}% of today's recommended noise dose — approaching the NIOSH daily limit.`;
  }
  return `You've used ${cumulativeDosePct.toFixed(1)}% of today's recommended noise dose — over the NIOSH daily limit. Consider hearing protection or a quieter environment.`;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    ZONE_THRESHOLDS,
    ZONES,
    A_WEIGHTING_TABLE,
    aWeightingDb,
    computeRms,
    rmsToDb,
    applyAWeighting,
    classifyZone,
    computeDoseFraction,
    computeDosePercent,
    doseSafetyMessage,
  };
}
