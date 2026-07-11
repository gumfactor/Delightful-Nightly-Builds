import { test, expect } from '@playwright/test';

function mockOpenMeteoResponse({
  latitude = 43.6532,
  longitude = -79.3832,
  temperature = 21.4,
  wind = 14.2,
  cloud = 62,
  precip = 30,
  weatherCode = 61,
  isDay = 1,
} = {}) {
  return {
    latitude,
    longitude,
    current: {
      time: '2026-07-03T14:00',
      temperature_2m: temperature,
      wind_speed_10m: wind,
      cloud_cover: cloud,
      weather_code: weatherCode,
      is_day: isDay,
    },
    hourly: {
      time: ['2026-07-03T13:00', '2026-07-03T14:00'],
      precipitation_probability: [20, precip],
    },
  };
}

async function mockWeatherRoute(page, options) {
  await page.route('**/api.open-meteo.com/**', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(mockOpenMeteoResponse(options)),
    })
  );
}

test.describe('WeatherSong — end-to-end UI behaviour', () => {
  test('page loads with a title and the default city weather panel populated', async ({ page }) => {
    await mockWeatherRoute(page);
    await page.goto('/index.html');
    await expect(page).toHaveTitle(/WeatherSong/);
    await expect(page.getByTestId('weather-panel')).toBeVisible();
    await expect(page.getByTestId('weather-city')).toHaveText('Toronto');
    await expect(page.getByTestId('weather-temp')).toHaveText('21.4 °C');
  });

  test('Play button starts playback and Pause stops it', async ({ page }) => {
    await mockWeatherRoute(page);
    await page.goto('/index.html');
    await expect(page.getByTestId('weather-panel')).toBeVisible();

    const playButton = page.getByTestId('play-pause-button');
    await expect(playButton).toHaveText('Play');
    await playButton.click();
    await expect(playButton).toHaveText('Pause');
    await expect.poll(() => page.evaluate(() => window.__weatherSongEngine.isRunning())).toBe(true);

    await playButton.click();
    await expect(playButton).toHaveText('Play');
    await expect.poll(() => page.evaluate(() => window.__weatherSongEngine.isRunning())).toBe(false);
  });

  test('switching city triggers a fresh weather fetch for the new location', async ({ page }) => {
    let requestedLatitudes = [];
    await page.route('**/api.open-meteo.com/**', (route) => {
      const url = new URL(route.request().url());
      requestedLatitudes.push(url.searchParams.get('latitude'));
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockOpenMeteoResponse({ latitude: Number(url.searchParams.get('latitude')) })),
      });
    });
    await page.goto('/index.html');
    await expect(page.getByTestId('weather-city')).toHaveText('Toronto');

    await page.getByTestId('city-select').selectOption('Vancouver');
    await expect(page.getByTestId('weather-city')).toHaveText('Vancouver');
    expect(requestedLatitudes.length).toBeGreaterThanOrEqual(2);
  });

  test('a failed weather fetch shows an error banner with a working demo fallback', async ({ page }) => {
    await page.route('**/api.open-meteo.com/**', (route) => route.fulfill({ status: 500, body: 'server error' }));
    await page.goto('/index.html');

    await expect(page.getByTestId('error-banner')).toBeVisible();
    await expect(page.getByTestId('weather-panel')).toBeHidden();

    await page.getByTestId('demo-weather-button').click();
    await expect(page.getByTestId('error-banner')).toBeHidden();
    await expect(page.getByTestId('weather-panel')).toBeVisible();
    await expect(page.getByTestId('weather-city')).toContainText('Demo');
  });

  test('custom coordinates form validates input before fetching', async ({ page }) => {
    await mockWeatherRoute(page);
    await page.goto('/index.html');

    await page.getByTestId('city-select').selectOption('Custom');
    await expect(page.getByTestId('custom-latitude')).toBeVisible();

    await page.getByTestId('custom-latitude').fill('999');
    await page.getByTestId('custom-longitude').fill('0');
    await page.getByTestId('fetch-custom-button').click();
    await expect(page.getByTestId('error-banner')).toBeVisible();
  });

  test('valid custom coordinates fetch and display weather for the custom location', async ({ page }) => {
    await mockWeatherRoute(page, { temperature: 5.5 });
    await page.goto('/index.html');

    await page.getByTestId('city-select').selectOption('Custom');
    await page.getByTestId('custom-latitude').fill('45.0');
    await page.getByTestId('custom-longitude').fill('-75.0');
    await page.getByTestId('fetch-custom-button').click();

    await expect(page.getByTestId('weather-city')).toHaveText('Custom Location');
    await expect(page.getByTestId('weather-temp')).toHaveText('5.5 °C');
  });

  test('saving to the journal adds a visible entry', async ({ page }) => {
    await mockWeatherRoute(page);
    await page.goto('/index.html');
    await expect(page.getByTestId('weather-panel')).toBeVisible();

    await page.getByTestId('save-journal-button').click();
    const entries = page.getByTestId('journal-entry-load');
    await expect(entries).toHaveCount(1);
    await expect(entries.first()).toContainText('Toronto');
  });

  test('journal starts empty on a fresh visit', async ({ page }) => {
    await mockWeatherRoute(page);
    await page.goto('/index.html');
    await expect(page.getByTestId('journal-entry-load')).toHaveCount(0);
  });

  test('loading a journal entry restores its stored weather without a new network request', async ({ page }) => {
    let requestCount = 0;
    await page.route('**/api.open-meteo.com/**', (route) => {
      requestCount += 1;
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockOpenMeteoResponse()),
      });
    });
    await page.goto('/index.html');
    await page.getByTestId('save-journal-button').click();

    // switch away to a different city, then load the journal entry back
    await page.getByTestId('city-select').selectOption('Halifax');
    await expect(page.getByTestId('weather-city')).toHaveText('Halifax');

    const countBeforeLoad = requestCount;
    await page.getByTestId('journal-entry-load').first().click();
    await expect(page.getByTestId('weather-city')).toHaveText('Toronto');
    expect(requestCount).toBe(countBeforeLoad);
  });

  test('removing a journal entry deletes it from the list', async ({ page }) => {
    await mockWeatherRoute(page);
    await page.goto('/index.html');
    await page.getByTestId('save-journal-button').click();
    await expect(page.getByTestId('journal-entry-load')).toHaveCount(1);

    await page.getByTestId('journal-entry-remove').first().click();
    await expect(page.getByTestId('journal-entry-load')).toHaveCount(0);
  });

  test('volume slider updates without throwing before playback starts', async ({ page }) => {
    await mockWeatherRoute(page);
    await page.goto('/index.html');
    const slider = page.getByTestId('volume-slider');
    await slider.fill('0.2');
    await expect(slider).toHaveValue('0.2');
  });

  test('the generative visual canvas is present and sized', async ({ page }) => {
    await mockWeatherRoute(page);
    await page.goto('/index.html');
    const canvas = page.getByTestId('visual-canvas');
    await expect(canvas).toBeVisible();
    const box = await canvas.boundingBox();
    expect(box.width).toBeGreaterThan(0);
    expect(box.height).toBeGreaterThan(0);
  });
});
