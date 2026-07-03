import { test, expect } from '@playwright/test';
import {
  CITY_PRESETS,
  buildForecastUrl,
  findHourlyIndexForCurrentTime,
  normalizeOpenMeteoResponse,
  getDemoWeather,
  validateCustomCoordinates,
} from '../src/weather.js';

test.describe('weather.js — Open-Meteo fetch and normalization', () => {
  test('CITY_PRESETS contains the five documented Canadian cities', () => {
    expect(Object.keys(CITY_PRESETS).sort()).toEqual(
      ['Calgary', 'Halifax', 'Montreal', 'Toronto', 'Vancouver'].sort()
    );
  });

  test('buildForecastUrl embeds latitude, longitude, and required fields', () => {
    const url = buildForecastUrl(43.65, -79.38);
    expect(url).toContain('api.open-meteo.com/v1/forecast');
    expect(url).toContain('latitude=43.65');
    expect(url).toContain('longitude=-79.38');
    expect(url).toContain('temperature_2m');
    expect(url).toContain('precipitation_probability');
  });

  test('findHourlyIndexForCurrentTime finds the matching hour', () => {
    const times = ['2026-07-03T00:00', '2026-07-03T01:00', '2026-07-03T02:00'];
    expect(findHourlyIndexForCurrentTime(times, '2026-07-03T01:00')).toBe(1);
  });

  test('findHourlyIndexForCurrentTime falls back to 0 when no match is found', () => {
    const times = ['2026-07-03T00:00'];
    expect(findHourlyIndexForCurrentTime(times, '2099-01-01T00:00')).toBe(0);
    expect(findHourlyIndexForCurrentTime(undefined, '2026-07-03T00:00')).toBe(0);
  });

  test('normalizeOpenMeteoResponse converts a valid response into a snapshot', () => {
    const raw = {
      latitude: 43.66,
      longitude: -79.42,
      current: {
        time: '2026-07-03T14:00',
        temperature_2m: 21.4,
        wind_speed_10m: 14.2,
        cloud_cover: 62,
        weather_code: 61,
        is_day: 1,
      },
      hourly: {
        time: ['2026-07-03T13:00', '2026-07-03T14:00'],
        precipitation_probability: [20, 30],
      },
    };
    const snapshot = normalizeOpenMeteoResponse(raw, 'Toronto');
    expect(snapshot.city).toBe('Toronto');
    expect(snapshot.temperatureC).toBe(21.4);
    expect(snapshot.windSpeedKmh).toBe(14.2);
    expect(snapshot.cloudCoverPct).toBe(62);
    expect(snapshot.precipProbabilityPct).toBe(30);
    expect(snapshot.weatherCode).toBe(61);
    expect(snapshot.isDay).toBe(true);
  });

  test('normalizeOpenMeteoResponse defaults precipitation to 0 when hourly data is missing', () => {
    const raw = {
      latitude: 43.66,
      longitude: -79.42,
      current: {
        time: '2026-07-03T14:00',
        temperature_2m: 5,
        wind_speed_10m: 3,
        cloud_cover: 10,
        weather_code: 0,
        is_day: 0,
      },
    };
    const snapshot = normalizeOpenMeteoResponse(raw, 'Toronto');
    expect(snapshot.precipProbabilityPct).toBe(0);
    expect(snapshot.isDay).toBe(false);
  });

  test('normalizeOpenMeteoResponse throws on a malformed response', () => {
    expect(() => normalizeOpenMeteoResponse({}, 'Toronto')).toThrow();
    expect(() => normalizeOpenMeteoResponse(null, 'Toronto')).toThrow();
  });

  test('getDemoWeather returns a complete, usable snapshot', () => {
    const demo = getDemoWeather();
    expect(demo.city).toContain('Demo');
    expect(typeof demo.temperatureC).toBe('number');
    expect(typeof demo.fetchedAt).toBe('string');
  });

  test('validateCustomCoordinates accepts valid latitude/longitude', () => {
    const result = validateCustomCoordinates('43.65', '-79.38');
    expect(result.valid).toBe(true);
    expect(result.latitude).toBeCloseTo(43.65, 5);
    expect(result.longitude).toBeCloseTo(-79.38, 5);
  });

  test('validateCustomCoordinates rejects out-of-range or non-numeric input', () => {
    expect(validateCustomCoordinates('999', '0').valid).toBe(false);
    expect(validateCustomCoordinates('0', '999').valid).toBe(false);
    expect(validateCustomCoordinates('not-a-number', '0').valid).toBe(false);
    expect(validateCustomCoordinates('', '').valid).toBe(false);
  });
});
