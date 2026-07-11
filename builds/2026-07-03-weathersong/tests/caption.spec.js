import { test, expect } from '@playwright/test';
import { generateCaption, describeTemperature, describeWind, describeSky } from '../src/caption.js';

test.describe('caption.js — deterministic template captions', () => {
  test('describeTemperature covers the full range from bitterly cold to sweltering', () => {
    expect(describeTemperature(-20)).toBe('bitterly cold');
    expect(describeTemperature(-5)).toBe('freezing');
    expect(describeTemperature(5)).toBe('cool');
    expect(describeTemperature(15)).toBe('mild');
    expect(describeTemperature(25)).toBe('warm');
    expect(describeTemperature(35)).toBe('sweltering');
  });

  test('describeWind covers still air through howling wind', () => {
    expect(describeWind(0)).toBe('still air');
    expect(describeWind(10)).toBe('a light breeze');
    expect(describeWind(30)).toBe('a brisk wind');
    expect(describeWind(60)).toBe('a howling wind');
  });

  test('describeSky prioritizes texture layer over raw cloud cover', () => {
    expect(describeSky('thunder', 10)).toContain('storm');
    expect(describeSky('rain', 90)).toContain('rain');
    expect(describeSky('snow', 90)).toContain('snow');
  });

  test('describeSky falls back to cloud cover reading when there is no texture layer', () => {
    expect(describeSky(null, 80)).toContain('overcast');
    expect(describeSky(null, 20)).toContain('scattered');
  });

  test('generateCaption is deterministic for identical inputs', () => {
    const snapshot = { city: 'Toronto', temperatureC: 21, windSpeedKmh: 12, cloudCoverPct: 55, isDay: true };
    const params = { mode: 'major', droneFreqHz: 220, textureLayer: 'clear' };
    const first = generateCaption(snapshot, params);
    const second = generateCaption(snapshot, params);
    expect(first).toBe(second);
  });

  test('generateCaption mentions the city, mode, and rounded drone frequency', () => {
    const snapshot = { city: 'Halifax', temperatureC: -5, windSpeedKmh: 40, cloudCoverPct: 90, isDay: false };
    const params = { mode: 'minor', droneFreqHz: 146.83, textureLayer: 'snow' };
    const caption = generateCaption(snapshot, params);
    expect(caption).toContain('Halifax');
    expect(caption).toContain('minor');
    expect(caption).toContain('147 Hz');
  });
});
