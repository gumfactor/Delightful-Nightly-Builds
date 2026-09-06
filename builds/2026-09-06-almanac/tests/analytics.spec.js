const { test, expect } = require('@playwright/test');

test.beforeEach(async ({ page }) => {
  await page.goto('/index.html');
  await page.waitForFunction(() => typeof window.Almanac !== 'undefined');
});

test('computePercentiles: odd-length array matches hand-computed values', async ({ page }) => {
  const result = await page.evaluate(() => window.Almanac.computePercentiles([10, 20, 30, 40, 50]));
  expect(result.count).toBe(5);
  expect(result.p50).toBe(30);
  expect(result.mean).toBe(30);
  // p10 index = 0.1*4 = 0.4 -> interpolate between 10 and 20 -> 14
  expect(result.p10).toBeCloseTo(14, 5);
  // p90 index = 0.9*4 = 3.6 -> interpolate between 40 and 50 -> 46
  expect(result.p90).toBeCloseTo(46, 5);
});

test('computePercentiles: even-length array interpolates the median', async ({ page }) => {
  const result = await page.evaluate(() => window.Almanac.computePercentiles([10, 20, 30, 40]));
  // p50 index = 0.5*3 = 1.5 -> interpolate between 20 and 30 -> 25
  expect(result.p50).toBeCloseTo(25, 5);
});

test('computePercentiles: single value returns that value for every percentile', async ({ page }) => {
  const result = await page.evaluate(() => window.Almanac.computePercentiles([42]));
  expect(result.p10).toBe(42);
  expect(result.p50).toBe(42);
  expect(result.p90).toBe(42);
  expect(result.count).toBe(1);
});

test('computePercentiles: all-null / empty input returns null, not NaN', async ({ page }) => {
  const result = await page.evaluate(() => window.Almanac.computePercentiles([null, null, undefined]));
  expect(result).toBeNull();
});

test('computePercentiles: null values are excluded from the mean, not treated as zero', async ({ page }) => {
  const result = await page.evaluate(() => window.Almanac.computePercentiles([10, null, 20, null, 30]));
  expect(result.count).toBe(3);
  expect(result.mean).toBe(20); // (10+20+30)/3, NOT (10+0+20+0+30)/5
});

test('findRuns: identifies consecutive true runs with correct start/length', async ({ page }) => {
  const runs = await page.evaluate(() =>
    window.Almanac.findRuns([false, true, true, false, true, true, true, false])
  );
  expect(runs).toEqual([
    { startIndex: 1, length: 2 },
    { startIndex: 4, length: 3 }
  ]);
});

test('findRuns: no true values returns an empty array', async ({ page }) => {
  const runs = await page.evaluate(() => window.Almanac.findRuns([false, false, false]));
  expect(runs).toEqual([]);
});

test('detectExtremeEvents: exactly 3 consecutive hot days counts as one heat wave', async ({ page }) => {
  const events = await page.evaluate(() => {
    const daily = {
      time: ['2022-06-01', '2022-06-02', '2022-06-03'],
      temperature_2m_max: [31, 32, 33],
      temperature_2m_min: [18, 19, 20],
      precipitation_sum: [0, 0, 0],
      wind_speed_10m_max: [10, 10, 10]
    };
    return window.Almanac.detectExtremeEvents(daily, window.Almanac.DEFAULT_THRESHOLDS);
  });
  expect(events.heatWaveEvents).toHaveLength(1);
  expect(events.heatWaveEvents[0]).toMatchObject({ length: 3, startDate: '2022-06-01', endDate: '2022-06-03' });
});

test('detectExtremeEvents: exactly 2 consecutive hot days does NOT count as a heat wave (min 3)', async ({ page }) => {
  const events = await page.evaluate(() => {
    const daily = {
      time: ['2022-06-01', '2022-06-02'],
      temperature_2m_max: [31, 32],
      temperature_2m_min: [18, 19],
      precipitation_sum: [0, 0],
      wind_speed_10m_max: [10, 10]
    };
    return window.Almanac.detectExtremeEvents(daily, window.Almanac.DEFAULT_THRESHOLDS);
  });
  expect(events.heatWaveEvents).toHaveLength(0);
});

test('detectExtremeEvents: one cool day in the middle breaks a heat streak into two separate events', async ({ page }) => {
  const events = await page.evaluate(() => {
    const daily = {
      time: ['2022-06-01', '2022-06-02', '2022-06-03', '2022-06-04', '2022-06-05'],
      temperature_2m_max: [31, 32, 33, 20, 34], // day 4 breaks the streak, day 5 alone doesn't reach 3
      temperature_2m_min: [18, 19, 20, 12, 21],
      precipitation_sum: [0, 0, 0, 0, 0],
      wind_speed_10m_max: [10, 10, 10, 10, 10]
    };
    return window.Almanac.detectExtremeEvents(daily, window.Almanac.DEFAULT_THRESHOLDS);
  });
  expect(events.heatWaveEvents).toHaveLength(1);
  expect(events.heatWaveEvents[0].length).toBe(3);
});

test('detectExtremeEvents: a heat streak spanning a year boundary is attributed to its start-date year', async ({ page }) => {
  const events = await page.evaluate(() => {
    const daily = {
      time: ['2020-12-30', '2020-12-31', '2021-01-01'],
      temperature_2m_max: [31, 32, 33],
      temperature_2m_min: [18, 19, 20],
      precipitation_sum: [0, 0, 0],
      wind_speed_10m_max: [10, 10, 10]
    };
    return window.Almanac.detectExtremeEvents(daily, window.Almanac.DEFAULT_THRESHOLDS);
  });
  expect(events.heatWaveEvents).toHaveLength(1);
  expect(events.heatWaveEvents[0].startDate).toBe('2020-12-30');
  expect(events.heatWaveEvents[0].endDate).toBe('2021-01-01');
});

test('computeYearSummary: attributes a year-boundary-spanning event to the year its streak started', async ({ page }) => {
  const summary = await page.evaluate(() => {
    const daily = {
      time: ['2020-12-30', '2020-12-31', '2021-01-01'],
      temperature_2m_max: [31, 32, 33],
      temperature_2m_min: [18, 19, 20],
      precipitation_sum: [0, 0, 0],
      wind_speed_10m_max: [10, 10, 10]
    };
    const events = window.Almanac.detectExtremeEvents(daily, window.Almanac.DEFAULT_THRESHOLDS);
    const suitability = window.Almanac.computeSuitability(daily, window.Almanac.ACTIVITY_PRESETS.running);
    return window.Almanac.computeYearSummary(daily, events, suitability);
  });
  const y2020 = summary.find((y) => y.year === '2020');
  const y2021 = summary.find((y) => y.year === '2021');
  expect(y2020.heatWaveCount).toBe(1);
  expect(y2021.heatWaveCount).toBe(0);
});

test('computeSuitability: running preset correctly flags suitable vs unsuitable days and excludes null-data days', async ({ page }) => {
  const result = await page.evaluate(() => {
    const daily = {
      time: ['2021-08-10', '2021-08-11', '2021-01-01'],
      temperature_2m_max: [20, 35, null], // day 3 has no data at all
      temperature_2m_min: [10, 25, null],
      precipitation_sum: [0, 0, null],
      wind_speed_10m_max: [5, 5, null]
    };
    return window.Almanac.computeSuitability(daily, window.Almanac.ACTIVITY_PRESETS.running);
  });
  expect(result.totalDays).toBe(2); // the null day is excluded entirely, not counted as unsuitable
  expect(result.suitableDays).toBe(1); // only the 20°C day qualifies (running max is 22°C)
  expect(result.pct).toBeCloseTo(50, 5);
});

test('formatCSV: escapes a field containing a comma and quotes correctly', async ({ page }) => {
  const csv = await page.evaluate(() =>
    window.Almanac.formatCSV(['name', 'note'], [['Springfield, IL', 'has a "nickname"']])
  );
  const lines = csv.split('\r\n');
  expect(lines[1]).toBe('"Springfield, IL","has a ""nickname"""');
});

test('filterByMonthWindow: normal (non-wrapping) range keeps only matching months', async ({ page }) => {
  const filtered = await page.evaluate(() => {
    const daily = {
      time: ['2021-01-15', '2021-06-15', '2021-07-15', '2021-12-15'],
      temperature_2m_max: [1, 2, 3, 4],
      temperature_2m_min: [1, 2, 3, 4],
      precipitation_sum: [1, 2, 3, 4],
      wind_speed_10m_max: [1, 2, 3, 4]
    };
    return window.Almanac.filterByMonthWindow(daily, 6, 7);
  });
  expect(filtered.time).toEqual(['2021-06-15', '2021-07-15']);
});

test('filterByMonthWindow: wraparound range (Dec-Feb) crosses the year boundary correctly', async ({ page }) => {
  const filtered = await page.evaluate(() => {
    const daily = {
      time: ['2021-01-15', '2021-02-15', '2021-06-15', '2021-12-15'],
      temperature_2m_max: [1, 2, 3, 4],
      temperature_2m_min: [1, 2, 3, 4],
      precipitation_sum: [1, 2, 3, 4],
      wind_speed_10m_max: [1, 2, 3, 4]
    };
    return window.Almanac.filterByMonthWindow(daily, 12, 2);
  });
  expect(filtered.time).toEqual(['2021-01-15', '2021-02-15', '2021-12-15']);
});

test('extractYear and extractMonth parse an ISO date string correctly', async ({ page }) => {
  const result = await page.evaluate(() => ({
    year: window.Almanac.extractYear('2021-08-10'),
    month: window.Almanac.extractMonth('2021-08-10')
  }));
  expect(result.year).toBe('2021');
  expect(result.month).toBe(8);
});
