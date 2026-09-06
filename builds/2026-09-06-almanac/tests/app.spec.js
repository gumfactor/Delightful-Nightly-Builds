const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

function fixture(name) {
  return JSON.parse(fs.readFileSync(path.join(__dirname, 'fixtures', name), 'utf8'));
}

async function mockGeocode(page, fixtureName, status = 200) {
  await page.route('https://geocoding-api.open-meteo.com/**', (route) =>
    route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(fixture(fixtureName)) })
  );
}

async function mockArchive(page, fixtureName, status = 200) {
  await page.route('https://archive-api.open-meteo.com/**', (route) =>
    route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(fixture(fixtureName)) })
  );
}

async function searchAndSelect(page, query, geocodeFixture) {
  await mockGeocode(page, geocodeFixture);
  await page.getByTestId('location-input').fill(query);
  await page.getByTestId('search-btn').click();
}

test.beforeEach(async ({ page }) => {
  await page.goto('/index.html');
});

test('location search: a single match auto-selects and enables the fetch button', async ({ page }) => {
  await searchAndSelect(page, 'Toronto', 'geocode-single.json');
  await expect(page.getByTestId('selected-location')).toHaveText('Toronto, Ontario, Canada');
  await expect(page.getByTestId('fetch-btn')).toBeEnabled();
});

test('location search: multiple matches render a picker, and clicking one selects it', async ({ page }) => {
  await searchAndSelect(page, 'Springfield', 'geocode-multi.json');
  const results = page.getByTestId('search-results');
  await expect(results.locator('li')).toHaveCount(3);
  await results.locator('li').nth(1).click();
  await expect(page.getByTestId('selected-location')).toHaveText('Springfield, Massachusetts, United States');
});

test('location search: zero matches shows an error and does not crash', async ({ page }) => {
  await searchAndSelect(page, 'Nowhereatall', 'geocode-empty.json');
  await expect(page.locator('#searchError')).toBeVisible();
  await expect(page.locator('#searchError')).toContainText('No locations found');
  await expect(page.getByTestId('fetch-btn')).toBeDisabled();
});

test('location search: empty query shows a validation message instead of calling the API', async ({ page }) => {
  await page.getByTestId('search-btn').click();
  await expect(page.locator('#searchError')).toContainText('Type a location name');
});

test('XSS safety: a malicious location name from the API renders as inert text everywhere it appears', async ({ page }) => {
  await searchAndSelect(page, 'evil', 'geocode-xss.json');
  // The single malicious result auto-selects (mapped.length === 1), so it shows in the "selected location" text.
  await expect(page.getByTestId('selected-location')).toContainText(
    '<img src=x onerror=window.__xssFired=true>Eviltown'
  );

  const fired = await page.evaluate(() => ({
    a: window.__xssFired,
    b: window.__xssFired2,
    c: window.__xssFired3
  }));
  expect(fired.a).toBeUndefined();
  expect(fired.b).toBeUndefined();
  expect(fired.c).toBeUndefined();

  // Exactly the page's own 3 <script> tags (Chart.js CDN, analytics.js, app.js) — no injected node.
  const scriptCount = await page.locator('script').count();
  expect(scriptCount).toBe(3);
});

test('historical fetch: happy path renders charts, extreme events, and a year table from real fetched data', async ({ page }) => {
  await searchAndSelect(page, 'Toronto', 'geocode-single.json');
  await mockArchive(page, 'archive-toronto.json');
  await page.getByTestId('fetch-btn').click();

  await expect(page.getByTestId('results-section')).toBeVisible();
  await expect(page.locator('#extremeEventsPanel')).toContainText('Heat waves (≥3 consecutive days ≥30°C) (1)');
  await expect(page.locator('#extremeEventsPanel')).toContainText('Cold snaps (≥2 consecutive days ≤-10°C) (1)');
  await expect(page.locator('#extremeEventsPanel')).toContainText('Heavy rain days (≥25mm): 1');
  await expect(page.locator('#extremeEventsPanel')).toContainText('High wind days (≥40km/h): 1');

  const rows = page.locator('#yearTableBody tr');
  await expect(rows).toHaveCount(2);
});

test('historical fetch: suitability % matches the hand-computed value for the Running preset', async ({ page }) => {
  await searchAndSelect(page, 'Toronto', 'geocode-single.json');
  await mockArchive(page, 'archive-toronto.json');
  await page.getByTestId('fetch-btn').click();
  await expect(page.getByTestId('results-section')).toBeVisible();

  const cards = page.getByTestId('summary-cards');
  await expect(cards).toContainText('12.5%'); // 2 of 16 valid days suitable for Running
});

test('historical fetch: switching the activity preset recomputes the suitability % without refetching', async ({ page }) => {
  await searchAndSelect(page, 'Toronto', 'geocode-single.json');
  await mockArchive(page, 'archive-toronto.json');
  await page.getByTestId('fetch-btn').click();
  await expect(page.getByTestId('results-section')).toBeVisible();
  await expect(page.getByTestId('summary-cards')).toContainText('12.5%');

  await page.getByTestId('activity-preset').selectOption('golf');
  await expect(page.getByTestId('summary-cards')).toContainText('6.3%'); // 1 of 16 valid days suitable for Golf (6.25 -> toFixed(1))
});

test('historical fetch: a non-2xx API error surfaces the API\'s own reason text without crashing', async ({ page }) => {
  await searchAndSelect(page, 'Toronto', 'geocode-single.json');
  await mockArchive(page, 'archive-error.json', 400);
  await page.getByTestId('fetch-btn').click();

  await expect(page.getByTestId('status-message')).toContainText("Parameter 'start_date' is out of allowed range");
  await expect(page.getByTestId('results-section')).toBeHidden();
});

test('historical fetch: an empty daily block shows a "no data" state instead of crashing', async ({ page }) => {
  await searchAndSelect(page, 'Toronto', 'geocode-single.json');
  await mockArchive(page, 'archive-empty.json');
  await page.getByTestId('fetch-btn').click();

  await expect(page.getByTestId('status-message')).toContainText('no data');
  await expect(page.getByTestId('results-section')).toBeHidden();
});

test('CSV export: raw daily data downloads with the fetched rows, correctly formatted', async ({ page }) => {
  await searchAndSelect(page, 'Toronto', 'geocode-single.json');
  await mockArchive(page, 'archive-toronto.json');
  await page.getByTestId('fetch-btn').click();
  await expect(page.getByTestId('results-section')).toBeVisible();

  const [download] = await Promise.all([
    page.waitForEvent('download'),
    page.getByTestId('export-daily-csv').click()
  ]);
  expect(download.suggestedFilename()).toBe('almanac-daily-toronto.csv');
  const downloadPath = await download.path();
  const content = fs.readFileSync(downloadPath, 'utf8');
  expect(content.split('\r\n')[0]).toBe('date,temp_max_c,temp_min_c,precipitation_mm,wind_speed_max_kmh');
  expect(content).toContain('2021-03-15,10,2,30,10');
});

test('CSV export: year summary downloads with per-year aggregates', async ({ page }) => {
  await searchAndSelect(page, 'Toronto', 'geocode-single.json');
  await mockArchive(page, 'archive-toronto.json');
  await page.getByTestId('fetch-btn').click();
  await expect(page.getByTestId('results-section')).toBeVisible();

  const [download] = await Promise.all([
    page.waitForEvent('download'),
    page.getByTestId('export-summary-csv').click()
  ]);
  expect(download.suggestedFilename()).toBe('almanac-summary-toronto.csv');
  const downloadPath = await download.path();
  const content = fs.readFileSync(downloadPath, 'utf8');
  expect(content).toContain('2020,');
  expect(content).toContain('2021,');
});

test('recent locations persist across a reload via localStorage', async ({ page }) => {
  await searchAndSelect(page, 'Toronto', 'geocode-single.json');
  await expect(page.getByTestId('selected-location')).toHaveText('Toronto, Ontario, Canada');

  await page.reload();
  await expect(page.locator('#recentWrap')).toBeVisible();
  await expect(page.getByTestId('recent-locations').locator('li')).toHaveCount(1);
  await expect(page.getByTestId('recent-locations').locator('li').first()).toHaveText('Toronto, Ontario, Canada');
});

test('year table sorting: clicking a column header re-sorts the rows', async ({ page }) => {
  await searchAndSelect(page, 'Toronto', 'geocode-single.json');
  await mockArchive(page, 'archive-toronto.json');
  await page.getByTestId('fetch-btn').click();
  await expect(page.getByTestId('results-section')).toBeVisible();

  const firstCellBefore = await page.locator('#yearTableBody tr').first().locator('td').first().textContent();
  expect(firstCellBefore).toBe('2020');

  await page.locator('#yearTable thead th[data-sort="year"]').click(); // toggles to desc
  const firstCellAfter = await page.locator('#yearTableBody tr').first().locator('td').first().textContent();
  expect(firstCellAfter).toBe('2021');
});

test('mobile viewport (375px) does not cause horizontal overflow', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 800 });
  await searchAndSelect(page, 'Toronto', 'geocode-single.json');
  await mockArchive(page, 'archive-toronto.json');
  await page.getByTestId('fetch-btn').click();
  await expect(page.getByTestId('results-section')).toBeVisible();

  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  expect(overflow).toBeLessThanOrEqual(1);
});
