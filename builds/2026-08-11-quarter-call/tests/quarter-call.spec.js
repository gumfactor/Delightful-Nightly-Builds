const { test, expect } = require('@playwright/test');
const path = require('path');

const HARNESS_URL = 'file://' + path.join(__dirname, 'fixtures', 'test-harness.html');
const REAL_INDEX_URL = 'file://' + path.join(__dirname, '..', 'index.html');

const FIXTURE_TICKERS = ['UPCO', 'DOWNCO', 'FLATCO', 'XSSCO', 'GROWCO', 'SLIPCO'];

async function canvasHasContent(page, testId) {
  return page.evaluate((tid) => {
    const canvas = document.querySelector(`[data-testid="${tid}"]`);
    const blank = document.createElement('canvas');
    blank.width = canvas.width;
    blank.height = canvas.height;
    return canvas.toDataURL() !== blank.toDataURL();
  }, testId);
}

test.describe('Honest empty state (real shipped index.html)', () => {
  test('shows the no-data banner and hides gameplay when ROUNDS_DATA is null', async ({ page }) => {
    const errors = [];
    page.on('pageerror', (e) => errors.push(e));
    await page.goto(REAL_INDEX_URL);

    await expect(page.locator('[data-testid="no-data-banner"]')).toBeVisible();
    await expect(page.locator('[data-testid="app"]')).toBeHidden();
    expect(errors).toEqual([]);
  });

  test('no-data banner names the exact fetch command to run', async ({ page }) => {
    await page.goto(REAL_INDEX_URL);
    await expect(page.locator('[data-testid="no-data-banner"] code')).toContainText('python3 fetch_data.py');
  });
});

test.describe('Practice mode (fixture data)', () => {
  test('loads a round with ticker, company, sector, industry, and metrics visible', async ({ page }) => {
    await page.goto(HARNESS_URL);
    await expect(page.locator('[data-testid="app"]')).toBeVisible();
    await expect(page.locator('[data-testid="ticker"]')).not.toHaveText('');
    await expect(page.locator('[data-testid="company"]')).not.toHaveText('');
    await expect(page.locator('[data-testid="sector-badge"]')).not.toHaveText('');
    await expect(page.locator('[data-testid="industry-badge"]')).not.toHaveText('');
    await expect(page.locator('[data-testid="metric-return"]')).toContainText('6-mo return');
    await expect(page.locator('[data-testid="metric-vol"]')).toContainText('volatility');
  });

  test('draws a non-blank chart for the current round', async ({ page }) => {
    await page.goto(HARNESS_URL);
    expect(await canvasHasContent(page, 'chart-canvas')).toBe(true);
  });

  test('reveal panel is hidden until a guess is made', async ({ page }) => {
    await page.goto(HARNESS_URL);
    await expect(page.locator('[data-testid="reveal-panel"]')).toBeHidden();
    await expect(page.locator('[data-testid="guess-buttons"]')).toBeVisible();
  });

  test('correct guess shows a Correct reveal and increments streak to 1', async ({ page }) => {
    await page.goto(HARNESS_URL);
    // Read the round's real outcome from the fixture via ticker, then guess it correctly.
    const ticker = await page.locator('[data-testid="ticker"]').textContent();
    const round = require('./fixtures/rounds-fixture-node.js').find(ticker);
    await page.locator(`[data-testid="guess-${round.forward.outcome}"]`).click();

    await expect(page.locator('[data-testid="guess-buttons"]')).toBeHidden();
    await expect(page.locator('[data-testid="reveal-panel"]')).toBeVisible();
    await expect(page.locator('[data-testid="reveal-result"]')).toContainText('Correct');
    await expect(page.locator('[data-testid="stat-streak"]')).toContainText('Streak: 1');
  });

  test('incorrect guess shows a "Not this time" reveal and resets streak to 0', async ({ page }) => {
    await page.goto(HARNESS_URL);
    const ticker = await page.locator('[data-testid="ticker"]').textContent();
    const round = require('./fixtures/rounds-fixture-node.js').find(ticker);
    const wrongGuess = ['up', 'down', 'flat'].find((g) => g !== round.forward.outcome);
    await page.locator(`[data-testid="guess-${wrongGuess}"]`).click();

    await expect(page.locator('[data-testid="reveal-result"]')).toContainText('Not this time');
    await expect(page.locator('[data-testid="stat-streak"]')).toContainText('Streak: 0');
  });

  test('draws a non-blank reveal chart after guessing', async ({ page }) => {
    await page.goto(HARNESS_URL);
    await page.locator('[data-testid="guess-up"]').click();
    expect(await canvasHasContent(page, 'reveal-canvas')).toBe(true);
  });

  test('double-clicking the same guess button only counts once', async ({ page }) => {
    await page.goto(HARNESS_URL);
    await page.evaluate(() => {
      const btn = document.querySelector('[data-testid="guess-up"]');
      btn.click();
      btn.click();
    });
    // Only one round has been recorded, so totalPlayed is 1 regardless of guess correctness.
    await expect(page.locator('[data-testid="stat-accuracy"]')).toContainText('/1)');
  });

  test('clicking Next cycles through every fixture round exactly once before repeating', async ({ page }) => {
    await page.goto(HARNESS_URL);
    const seen = new Set();
    for (let i = 0; i < FIXTURE_TICKERS.length; i++) {
      const ticker = await page.locator('[data-testid="ticker"]').textContent();
      seen.add(ticker);
      await page.locator('[data-testid="guess-up"]').click();
      await page.locator('[data-testid="next-round-btn"]').click();
    }
    expect([...seen].sort()).toEqual([...FIXTURE_TICKERS].sort());
  });

  test('accuracy math is correct after two correct and one incorrect guess', async ({ page }) => {
    await page.goto(HARNESS_URL);
    for (let i = 0; i < 3; i++) {
      const ticker = await page.locator('[data-testid="ticker"]').textContent();
      const round = require('./fixtures/rounds-fixture-node.js').find(ticker);
      const guess = i < 2 ? round.forward.outcome : ['up', 'down', 'flat'].find((g) => g !== round.forward.outcome);
      await page.locator(`[data-testid="guess-${guess}"]`).click();
      await page.locator('[data-testid="next-round-btn"]').click();
    }
    await expect(page.locator('[data-testid="stat-accuracy"]')).toContainText('(2/3)');
  });

  test('stats persist across a page reload', async ({ page }) => {
    await page.goto(HARNESS_URL);
    await page.locator('[data-testid="guess-up"]').click();
    await page.reload();
    await expect(page.locator('[data-testid="stat-accuracy"]')).toContainText('/1)');
  });
});

test.describe('XSS safety', () => {
  test('an injected script/img payload in round data renders as inert text', async ({ page }) => {
    const dialogs = [];
    page.on('dialog', (d) => dialogs.push(d));
    await page.goto(HARNESS_URL);

    let sawXssRound = false;
    for (let i = 0; i < FIXTURE_TICKERS.length; i++) {
      const ticker = await page.locator('[data-testid="ticker"]').textContent();
      if (ticker === 'XSSCO') {
        sawXssRound = true;
        const companyText = await page.locator('[data-testid="company"]').textContent();
        expect(companyText).toContain('<img');
        break;
      }
      await page.locator('[data-testid="guess-up"]').click();
      await page.locator('[data-testid="next-round-btn"]').click();
    }

    expect(sawXssRound).toBe(true);
    expect(dialogs).toEqual([]);
    const fired = await page.evaluate(() => ({
      a: window.__xssFired || false,
      b: window.__xssFired2 || false,
    }));
    expect(fired).toEqual({ a: false, b: false });
  });
});

test.describe('Daily Challenge (fixture data)', () => {
  test('selects the same 5 rounds on repeated visits for the same UTC date', async ({ page }) => {
    await page.goto(HARNESS_URL);
    await page.clock.setFixedTime(new Date('2026-08-11T12:00:00Z'));

    await page.locator('[data-testid="tab-daily"]').click();
    const firstTicker = await page.locator('[data-testid="ticker"]').textContent();

    await page.reload();
    await page.clock.setFixedTime(new Date('2026-08-11T18:00:00Z')); // same UTC day, different hour
    await page.locator('[data-testid="tab-daily"]').click();
    const secondTicker = await page.locator('[data-testid="ticker"]').textContent();

    expect(secondTicker).toBe(firstTicker);
  });

  test('completing all 5 rounds shows the completion banner and a matching emoji share string', async ({ page }) => {
    await page.goto(HARNESS_URL);
    await page.clock.setFixedTime(new Date('2026-08-12T09:00:00Z'));
    await page.locator('[data-testid="tab-daily"]').click();

    const results = [];
    for (let i = 0; i < 5; i++) {
      await expect(page.locator('[data-testid="progress-indicator"]')).toContainText(`Round ${i + 1} of 5`);
      const ticker = await page.locator('[data-testid="ticker"]').textContent();
      const round = require('./fixtures/rounds-fixture-node.js').find(ticker);
      const guessCorrectly = i % 2 === 0; // alternate correct/incorrect for a mixed share string
      const guess = guessCorrectly
        ? round.forward.outcome
        : ['up', 'down', 'flat'].find((g) => g !== round.forward.outcome);
      results.push(guessCorrectly ? '\u{1F7E9}' : '\u{1F7E5}');
      await page.locator(`[data-testid="guess-${guess}"]`).click();
      await page.locator('[data-testid="next-round-btn"]').click();
    }

    await expect(page.locator('[data-testid="daily-complete-banner"]')).toBeVisible();
    const shareText = await page.locator('[data-testid="share-result"]').textContent();
    expect(shareText).toContain(results.join(''));
  });

  test('a second visit the same day shows the already-complete summary instead of new gameplay', async ({ page }) => {
    await page.goto(HARNESS_URL);
    await page.clock.setFixedTime(new Date('2026-08-13T09:00:00Z'));
    await page.locator('[data-testid="tab-daily"]').click();

    for (let i = 0; i < 5; i++) {
      const ticker = await page.locator('[data-testid="ticker"]').textContent();
      const round = require('./fixtures/rounds-fixture-node.js').find(ticker);
      await page.locator(`[data-testid="guess-${round.forward.outcome}"]`).click();
      await page.locator('[data-testid="next-round-btn"]').click();
    }
    const accuracyAfterFirstPlay = await page.locator('[data-testid="stat-accuracy"]').textContent();

    await page.reload();
    await page.clock.setFixedTime(new Date('2026-08-13T20:00:00Z'));
    await page.locator('[data-testid="tab-daily"]').click();

    await expect(page.locator('[data-testid="daily-complete-banner"]')).toBeVisible();
    await expect(page.locator('[data-testid="guess-buttons"]')).toBeHidden();
    await expect(page.locator('[data-testid="stat-accuracy"]')).toHaveText(accuracyAfterFirstPlay);
  });
});

test.describe('Pure date math (guards the Date.UTC 0-indexed-month bug)', () => {
  test('daysBetween counts correctly across a month boundary', async ({ page }) => {
    await page.goto(HARNESS_URL);
    const days = await page.evaluate(() => window.daysBetween('2020-01-31', '2020-02-01'));
    expect(days).toBe(1);
  });

  test('daysBetween counts correctly across a year boundary', async ({ page }) => {
    await page.goto(HARNESS_URL);
    const days = await page.evaluate(() => window.daysBetween('2020-12-31', '2021-01-02'));
    expect(days).toBe(2);
  });

  test('dailyChallengeRounds is deterministic for the same date and data', async ({ page }) => {
    await page.goto(HARNESS_URL);
    const [first, second] = await page.evaluate(() => {
      const a = dailyChallengeRounds('2026-09-01', ROUNDS_DATA, 5).map((r) => r.id);
      const b = dailyChallengeRounds('2026-09-01', ROUNDS_DATA, 5).map((r) => r.id);
      return [a, b];
    });
    expect(first).toEqual(second);
  });
});

test.describe('Optional AI note (mocked network)', () => {
  test('with no API key set, the fallback note appears and zero network calls are made', async ({ page }) => {
    let calls = 0;
    await page.route('https://api.anthropic.com/**', (route) => {
      calls += 1;
      route.abort();
    });
    await page.goto(HARNESS_URL);
    await page.locator('[data-testid="guess-up"]').click();
    await expect(page.locator('[data-testid="ai-note"]')).not.toHaveText('Loading note…');
    await expect(page.locator('[data-testid="ai-note"]')).toContainText('data point');
    expect(calls).toBe(0);
  });

  test('with an API key set, exactly one mocked call is made and only aggregate data is sent', async ({ page }) => {
    let requestBody = null;
    let calls = 0;
    await page.route('https://api.anthropic.com/v1/messages', async (route) => {
      calls += 1;
      requestBody = route.request().postDataJSON();
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ content: [{ text: 'Mocked historical context note.' }] }),
      });
    });
    await page.goto(HARNESS_URL);
    await page.locator('[data-testid="api-key-input"]').fill('sk-ant-test-key');
    await page.locator('[data-testid="api-key-input"]').dispatchEvent('input');
    await page.locator('[data-testid="guess-up"]').click();

    await expect(page.locator('[data-testid="ai-note"]')).toContainText('Mocked historical context note.');
    expect(calls).toBe(1);
    const bodyStr = JSON.stringify(requestBody);
    expect(bodyStr).not.toContain('"chart"');
  });

  test('a failed AI call falls back to the deterministic note without crashing', async ({ page }) => {
    await page.route('https://api.anthropic.com/v1/messages', (route) => route.fulfill({ status: 500, body: '{}' }));
    const errors = [];
    page.on('pageerror', (e) => errors.push(e));

    await page.goto(HARNESS_URL);
    await page.locator('[data-testid="api-key-input"]').fill('sk-ant-test-key');
    await page.locator('[data-testid="api-key-input"]').dispatchEvent('input');
    await page.locator('[data-testid="guess-up"]').click();

    await expect(page.locator('[data-testid="ai-note"]')).toContainText('data point');
    expect(errors).toEqual([]);
  });
});
