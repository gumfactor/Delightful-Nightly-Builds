import { test, expect } from '@playwright/test';
import {
  clamp,
  temperatureToScaleDegree,
  isDaytimeMode,
  droneFrequencyHz,
  windSpeedToTempoHz,
  windSpeedToFilterCutoffHz,
  cloudCoverToReverbWetness,
  precipProbabilityToPercussionDensity,
  weatherCodeToTextureLayer,
  mapWeatherToParams,
} from '../src/mapping.js';

test.describe('mapping.js — pure weather-to-sound mapping', () => {
  test('clamp restricts a value to the given range', () => {
    expect(clamp(-100, -30, 40)).toBe(-30);
    expect(clamp(100, -30, 40)).toBe(40);
    expect(clamp(10, -30, 40)).toBe(10);
  });

  test('temperatureToScaleDegree clamps out-of-range temperatures to the scale bounds', () => {
    expect(temperatureToScaleDegree(-999)).toBe(0);
    expect(temperatureToScaleDegree(999)).toBe(4);
  });

  test('temperatureToScaleDegree is monotonic non-decreasing with temperature', () => {
    const degrees = [-30, -10, 0, 10, 20, 30, 40].map(temperatureToScaleDegree);
    for (let i = 1; i < degrees.length; i += 1) {
      expect(degrees[i]).toBeGreaterThanOrEqual(degrees[i - 1]);
    }
  });

  test('isDaytimeMode returns major for day and minor for night', () => {
    expect(isDaytimeMode(true)).toBe('major');
    expect(isDaytimeMode(false)).toBe('minor');
  });

  test('droneFrequencyHz produces a positive frequency for cold night and hot day', () => {
    const cold = droneFrequencyHz(-20, false);
    const hot = droneFrequencyHz(35, true);
    expect(cold).toBeGreaterThan(0);
    expect(hot).toBeGreaterThan(0);
  });

  test('droneFrequencyHz drops an octave for cold temperatures relative to a warm one at the same scale degree', () => {
    const cold = droneFrequencyHz(-10, true);
    const warm = droneFrequencyHz(30, true);
    expect(cold).toBeLessThan(warm);
  });

  test('windSpeedToTempoHz is monotonically increasing with wind speed', () => {
    const tempos = [0, 20, 40, 60, 80].map(windSpeedToTempoHz);
    for (let i = 1; i < tempos.length; i += 1) {
      expect(tempos[i]).toBeGreaterThan(tempos[i - 1]);
    }
  });

  test('windSpeedToTempoHz clamps extreme wind speeds', () => {
    expect(windSpeedToTempoHz(-50)).toBeCloseTo(windSpeedToTempoHz(0), 5);
    expect(windSpeedToTempoHz(500)).toBeCloseTo(windSpeedToTempoHz(80), 5);
  });

  test('windSpeedToFilterCutoffHz is monotonically increasing with wind speed', () => {
    const cutoffs = [0, 40, 80].map(windSpeedToFilterCutoffHz);
    expect(cutoffs[1]).toBeGreaterThan(cutoffs[0]);
    expect(cutoffs[2]).toBeGreaterThan(cutoffs[1]);
  });

  test('cloudCoverToReverbWetness maps 0-100% to 0-1', () => {
    expect(cloudCoverToReverbWetness(0)).toBe(0);
    expect(cloudCoverToReverbWetness(100)).toBe(1);
    expect(cloudCoverToReverbWetness(50)).toBeCloseTo(0.5, 5);
  });

  test('precipProbabilityToPercussionDensity maps 0-100% to 0-1 and clamps out-of-range', () => {
    expect(precipProbabilityToPercussionDensity(-10)).toBe(0);
    expect(precipProbabilityToPercussionDensity(150)).toBe(1);
    expect(precipProbabilityToPercussionDensity(25)).toBeCloseTo(0.25, 5);
  });

  test('weatherCodeToTextureLayer identifies thunder, rain, snow, and clear codes', () => {
    expect(weatherCodeToTextureLayer(95)).toBe('thunder');
    expect(weatherCodeToTextureLayer(61)).toBe('rain');
    expect(weatherCodeToTextureLayer(71)).toBe('snow');
    expect(weatherCodeToTextureLayer(0)).toBe('clear');
  });

  test('weatherCodeToTextureLayer returns null for an unrecognized code', () => {
    expect(weatherCodeToTextureLayer(3)).toBeNull();
  });

  test('mapWeatherToParams returns a complete, well-typed params object', () => {
    const params = mapWeatherToParams({
      temperatureC: 21,
      windSpeedKmh: 15,
      cloudCoverPct: 60,
      precipProbabilityPct: 30,
      weatherCode: 61,
      isDay: true,
    });
    expect(params).toMatchObject({
      mode: 'major',
      textureLayer: 'rain',
    });
    expect(typeof params.droneFreqHz).toBe('number');
    expect(typeof params.tempoHz).toBe('number');
    expect(typeof params.filterCutoffHz).toBe('number');
    expect(params.reverbWetness).toBeCloseTo(0.6, 5);
    expect(params.percussionDensity).toBeCloseTo(0.3, 5);
  });
});
