// @ts-check
const { test, expect } = require('@playwright/test');
const path = require('path');

const INDEX_URL = 'file://' + path.resolve(__dirname, '../index.html');
const FIXTURE_PATH = path.resolve(__dirname, 'fixtures/fixture-data.js');

async function gotoWithFixture(page, testSeed) {
  await page.addInitScript({ path: FIXTURE_PATH });
  if (testSeed !== undefined) {
    await page.addInitScript((seed) => {
      window.__TEST_SEED__ = seed;
    }, testSeed);
  }
  await page.goto(INDEX_URL);
}

// ---- Onboarding state ---------------------------------------------------

test('shows the onboarding screen when no market data has been fetched', async ({ page }) => {
  await page.goto(INDEX_URL); // no fixture injected -> default data.js -> PORTFOLIO_DATA = null
  await expect(page.getByTestId('onboarding')).toBeVisible();
  await expect(page.getByTestId('app')).toBeHidden();
  await expect(page.getByText('python fetch_data.py')).toBeVisible();
});

test('shows the main app once real (fixture) data is present', async ({ page }) => {
  await gotoWithFixture(page, 1);
  await expect(page.getByTestId('app')).toBeVisible();
  await expect(page.getByTestId('onboarding')).toBeHidden();
  await expect(page.getByTestId('data-meta')).toContainText('4 assets');
});

// ---- Tabs ---------------------------------------------------------------

test('tab navigation switches the visible panel', async ({ page }) => {
  await gotoWithFixture(page, 1);
  await expect(page.getByTestId('panel-explainer')).toBeVisible();
  await expect(page.getByTestId('panel-frontier')).toBeHidden();

  await page.getByTestId('tab-frontier').click();
  await expect(page.getByTestId('panel-frontier')).toBeVisible();
  await expect(page.getByTestId('panel-explainer')).toBeHidden();

  await page.getByTestId('tab-quiz').click();
  await expect(page.getByTestId('panel-quiz')).toBeVisible();
});

// ---- Explainer / two-asset mixer -----------------------------------------

test('two-asset mixer at 0% and 100% matches the pure single-asset stats', async ({ page }) => {
  await gotoWithFixture(page, 1);
  await page.getByTestId('asset-a').selectOption('AAA');
  await page.getByTestId('asset-b').selectOption('BBB');

  await page.getByTestId('mix-weight').fill('100');
  await page.getByTestId('mix-weight').dispatchEvent('input');
  await expect(page.getByTestId('mixer-return')).toHaveText('10.0%');
  await expect(page.getByTestId('mixer-vol')).toHaveText('20.0%'); // sqrt(0.04) = 0.20

  await page.getByTestId('mix-weight').fill('0');
  await page.getByTestId('mix-weight').dispatchEvent('input');
  await expect(page.getByTestId('mixer-return')).toHaveText('6.0%');
  await expect(page.getByTestId('mixer-vol')).toHaveText('10.0%'); // sqrt(0.01) = 0.10
});

test('mixer shows the real correlation for the selected pair', async ({ page }) => {
  await gotoWithFixture(page, 1);
  await page.getByTestId('asset-a').selectOption('AAA');
  await page.getByTestId('asset-b').selectOption('CCC');
  await expect(page.getByTestId('mixer-corr')).toHaveText('0.60');
});

test('mixer selection persists to localStorage and survives reload', async ({ page }) => {
  await gotoWithFixture(page, 1);
  await page.getByTestId('asset-a').selectOption('CCC');
  await page.getByTestId('asset-b').selectOption('DDD');
  await page.waitForTimeout(50);

  await gotoWithFixture(page, 1);
  await expect(page.getByTestId('asset-a')).toHaveValue('CCC');
  await expect(page.getByTestId('asset-b')).toHaveValue('DDD');
});

// ---- AI explain: mocked success, and no-key deterministic fallback -------

test('AI explain button renders a mocked Claude response when a key is supplied', async ({ page }) => {
  await gotoWithFixture(page, 1);
  await page.route('https://api.anthropic.com/v1/messages', (route) => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ content: [{ type: 'text', text: 'Mocked plain-English explanation.' }] }),
    });
  });

  await page.getByTestId('api-key-input').fill('sk-ant-test-key');
  await page.getByTestId('explain-mixer').click();
  await expect(page.getByTestId('explain-mixer-output')).toHaveText('Mocked plain-English explanation.');
});

test('AI explain falls back to the deterministic template and makes zero network calls with no key', async ({ page }) => {
  await gotoWithFixture(page, 1);
  let callCount = 0;
  await page.route('https://api.anthropic.com/v1/messages', (route) => {
    callCount += 1;
    route.abort();
  });

  await page.getByTestId('asset-a').selectOption('AAA');
  await page.getByTestId('asset-b').selectOption('CCC');
  // api-key-input deliberately left empty
  await page.getByTestId('explain-mixer').click();

  const output = await page.getByTestId('explain-mixer-output').textContent();
  expect(output).toContain('AAA');
  expect(output).toContain('CCC');
  expect(callCount).toBe(0);
});

// ---- Efficient frontier tab ------------------------------------------------

test('frontier tab shows the global minimum-variance readouts and resample changes the cloud', async ({ page }) => {
  await gotoWithFixture(page, 5);
  await page.getByTestId('tab-frontier').click();
  await expect(page.getByTestId('gmv-return')).not.toHaveText('');
  await expect(page.getByTestId('gmv-vol')).not.toHaveText('');

  const before = await page.evaluate(() => document.getElementById('frontier-canvas').toDataURL());
  await page.getByTestId('resample-cloud').click();
  const after = await page.evaluate(() => document.getElementById('frontier-canvas').toDataURL());
  expect(before).not.toEqual(after);
});

// ---- Sharpe & risk-free tab -------------------------------------------------

test('moving the risk-free slider changes the tangency Sharpe readout', async ({ page }) => {
  await gotoWithFixture(page, 1);
  await page.getByTestId('tab-sharpe').click();
  const before = await page.getByTestId('tangency-sharpe').textContent();

  await page.getByTestId('riskfree-slider').fill('5');
  await page.getByTestId('riskfree-slider').dispatchEvent('input');

  const after = await page.getByTestId('tangency-sharpe').textContent();
  expect(before).not.toEqual(after);
});

// ---- Correlation heatmap --------------------------------------------------

test('correlation heatmap cell click jumps to the Explainer tab with that pair preselected', async ({ page }) => {
  await gotoWithFixture(page, 1);
  await page.getByTestId('tab-correlation').click();
  await page.getByTestId('corr-cell-AAA-DDD').click();

  await expect(page.getByTestId('panel-explainer')).toBeVisible();
  await expect(page.getByTestId('asset-a')).toHaveValue('AAA');
  await expect(page.getByTestId('asset-b')).toHaveValue('DDD');
});

// ---- Quiz mode --------------------------------------------------------------

test('quiz mode tracks attempts, correct answers, and streak in localStorage across reload', async ({ page }) => {
  await gotoWithFixture(page, 2026);
  await page.getByTestId('tab-quiz').click();

  const round = await page.evaluate(() => window.__portfolioLabTestHooks.getQuizRound());
  const correctIndex = round.correctIndex;

  await page.getByTestId('quiz-option-' + correctIndex).click();
  await expect(page.getByTestId('quiz-attempts')).toHaveText('1');
  await expect(page.getByTestId('quiz-correct')).toHaveText('1');
  await expect(page.getByTestId('quiz-streak')).toHaveText('1');

  await page.getByTestId('quiz-next').click();
  await page.waitForTimeout(30);

  await gotoWithFixture(page, 2026);
  await page.getByTestId('tab-quiz').click();
  await expect(page.getByTestId('quiz-attempts')).toHaveText('1');
  await expect(page.getByTestId('quiz-correct')).toHaveText('1');
});

test('quiz mode resets streak on an incorrect answer', async ({ page }) => {
  await gotoWithFixture(page, 2026);
  await page.getByTestId('tab-quiz').click();

  const round = await page.evaluate(() => window.__portfolioLabTestHooks.getQuizRound());
  const wrongIndex = round.correctIndex === 0 ? 1 : 0;

  await page.getByTestId('quiz-option-' + wrongIndex).click();
  await expect(page.getByTestId('quiz-streak')).toHaveText('0');
  await expect(page.getByTestId('quiz-feedback')).toContainText('Not quite');
});

test('quiz options cannot be answered twice in the same round', async ({ page }) => {
  await gotoWithFixture(page, 2026);
  await page.getByTestId('tab-quiz').click();
  await page.getByTestId('quiz-option-0').click();
  await expect(page.getByTestId('quiz-option-0')).toBeDisabled();
  await expect(page.getByTestId('quiz-option-1')).toBeDisabled();
});

// ---- Security: no script execution from injected data --------------------

test('a script-injection payload in ticker metadata renders as inert text, never executes', async ({ page }) => {
  let dialogFired = false;
  page.on('dialog', async (dialog) => {
    dialogFired = true;
    await dialog.dismiss();
  });

  await page.addInitScript(() => {
    window.PORTFOLIO_DATA = {
      generated_at: '2026-08-09T00:00:00Z',
      years: 3,
      tickers: ['XXX', 'YYY'],
      meta: {
        XXX: { name: '<img src=x onerror="window.__xssFired=true">', sector: '</script><script>window.__xssFired=true</script>' },
        YYY: { name: 'Safe Asset', sector: 'Test' },
      },
      mean_return: { XXX: 0.08, YYY: 0.05 },
      volatility: { XXX: 0.15, YYY: 0.08 },
      cov_matrix: [[0.0225, 0.003], [0.003, 0.0064]],
      corr_matrix: [[1.0, 0.25], [0.25, 1.0]],
    };
  });
  await page.goto(INDEX_URL);

  const xssFired = await page.evaluate(() => window.__xssFired === true);
  expect(xssFired).toBe(false);
  expect(dialogFired).toBe(false);

  const optionText = await page.getByTestId('asset-a').locator('option').first().textContent();
  expect(optionText).toContain('<img'); // rendered as literal text, not parsed as HTML
});

// ---- Responsive smoke check ------------------------------------------------

test('app remains usable at a narrow (375px) viewport with no horizontal overflow', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 700 });
  await gotoWithFixture(page, 1);

  const hasOverflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1);
  expect(hasOverflow).toBe(false);
  await expect(page.getByTestId('tab-nav')).toBeVisible();
});
