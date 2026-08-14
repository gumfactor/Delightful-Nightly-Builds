// @ts-nocheck
const { test, expect } = require('@playwright/test');
const path = require('path');

const {
  computeRms,
  rmsToDb,
  applyAWeighting,
  aWeightingDb,
  classifyZone,
  computeDoseFraction,
  computeDosePercent,
  doseSafetyMessage,
  ZONES,
} = require(path.join(__dirname, '..', 'src', 'audio-math.js'));

test.describe('computeRms', () => {
  test('returns 0 for a silent (all-zero) buffer', () => {
    expect(computeRms(new Array(100).fill(0))).toBe(0);
  });

  test('returns 0 for an empty buffer', () => {
    expect(computeRms([])).toBe(0);
  });

  test('returns 1 for a full-scale constant buffer (clipping edge case)', () => {
    expect(computeRms(new Array(50).fill(1))).toBeCloseTo(1, 6);
  });

  test('computes correct RMS for a known mixed buffer', () => {
    // RMS of [1, -1, 1, -1] is 1
    expect(computeRms([1, -1, 1, -1])).toBeCloseTo(1, 6);
  });
});

test.describe('rmsToDb', () => {
  test('a higher RMS produces a higher dB reading', () => {
    const low = rmsToDb(0.01, 0);
    const high = rmsToDb(0.5, 0);
    expect(high).toBeGreaterThan(low);
  });

  test('calibration offset shifts the reading by exactly the offset', () => {
    const base = rmsToDb(0.1, 0);
    const shifted = rmsToDb(0.1, 12.5);
    expect(shifted - base).toBeCloseTo(12.5, 6);
  });

  test('negative calibration offset shifts the reading down', () => {
    const base = rmsToDb(0.1, 0);
    const shifted = rmsToDb(0.1, -7);
    expect(shifted - base).toBeCloseTo(-7, 6);
  });

  test('true silence does not produce -Infinity (uses a noise floor)', () => {
    const db = rmsToDb(0, 0);
    expect(Number.isFinite(db)).toBe(true);
  });
});

test.describe('A-weighting', () => {
  test('applyAWeighting adds the correct attenuation at an exact table frequency', () => {
    const base = 60;
    const weighted = applyAWeighting(base, 1000); // 1000 Hz has 0.0 dB correction
    expect(weighted).toBeCloseTo(60, 6);
  });

  test('applyAWeighting attenuates low frequencies more than mid frequencies', () => {
    const lowFreqAttenuation = aWeightingDb(63);
    const midFreqAttenuation = aWeightingDb(1000);
    expect(lowFreqAttenuation).toBeLessThan(midFreqAttenuation);
  });

  test('aWeightingDb clamps below the lowest table frequency', () => {
    expect(aWeightingDb(10)).toBe(aWeightingDb(63));
  });

  test('aWeightingDb clamps above the highest table frequency', () => {
    expect(aWeightingDb(20000)).toBe(aWeightingDb(8000));
  });

  test('aWeightingDb interpolates linearly between table points', () => {
    // halfway between 500 (-3.2) and 1000 (0.0) should be close to -1.6
    const mid = aWeightingDb(750);
    expect(mid).toBeCloseTo(-1.6, 1);
  });
});

test.describe('classifyZone', () => {
  test('classifies a clearly quiet value', () => {
    expect(classifyZone(35).key).toBe('quiet');
  });

  test('boundary exactly at 50 is Moderate, not Quiet', () => {
    expect(classifyZone(50).key).toBe('moderate');
  });

  test('boundary exactly at 70 is Loud, not Moderate', () => {
    expect(classifyZone(70).key).toBe('loud');
  });

  test('boundary exactly at 85 is Hazardous, not Loud', () => {
    expect(classifyZone(85).key).toBe('hazardous');
  });

  test('classifies a very loud value as Hazardous', () => {
    expect(classifyZone(110).key).toBe('hazardous');
  });

  test('every zone has a color and label defined', () => {
    ZONES.forEach((zone) => {
      expect(typeof zone.color).toBe('string');
      expect(typeof zone.label).toBe('string');
    });
  });
});

test.describe('computeDoseFraction / computeDosePercent', () => {
  test('exactly 8 hours at 85 dB consumes exactly 100% of the daily dose', () => {
    const pct = computeDosePercent(85, 8 * 3600);
    expect(pct).toBeCloseTo(100, 0);
  });

  test('exactly 4 hours at 88 dB (one 3dB step up) also consumes 100% of the dose', () => {
    // 3 dB exchange rate: permissible time halves for every 3 dB increase
    const pct = computeDosePercent(88, 4 * 3600);
    expect(pct).toBeCloseTo(100, 0);
  });

  test('exactly 16 hours at 82 dB (one 3dB step down) also consumes 100% of the dose', () => {
    const pct = computeDosePercent(82, 16 * 3600);
    expect(pct).toBeCloseTo(100, 0);
  });

  test('zero-duration session consumes 0% dose', () => {
    expect(computeDoseFraction(95, 0)).toBe(0);
  });

  test('negative or zero duration never throws and returns 0', () => {
    expect(computeDoseFraction(95, -5)).toBe(0);
  });

  test('a quiet, short session consumes a negligible dose', () => {
    const pct = computeDosePercent(40, 60);
    expect(pct).toBeLessThan(0.1);
  });
});

test.describe('doseSafetyMessage', () => {
  test('under 50% gives a comfortable message', () => {
    expect(doseSafetyMessage(20)).toContain('comfortably within');
  });

  test('between 50% and 100% gives an approaching-limit message', () => {
    expect(doseSafetyMessage(75)).toContain('approaching');
  });

  test('over 100% gives an over-limit message with a recommendation', () => {
    const msg = doseSafetyMessage(120);
    expect(msg).toContain('over the NIOSH daily limit');
    expect(msg).toContain('hearing protection');
  });
});
