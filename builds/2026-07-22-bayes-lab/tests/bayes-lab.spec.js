const { test, expect } = require('@playwright/test');
const path = require('path');

const PAGE_URL = 'file://' + path.resolve(__dirname, '..', 'index.html');

test.beforeEach(async ({ page }) => {
  await page.goto(PAGE_URL);
});

// ---------- Core math correctness (independently cross-checked reference values) ----------

test('BetaMath: posterior update Beta(1,1) + 3 successes/2 failures matches Beta(4,3)', async ({ page }) => {
  const result = await page.evaluate(() => {
    const post = { alpha: 1 + 3, beta: 1 + 2 };
    return {
      mean: window.BetaMath.betaMean(post.alpha, post.beta),
      variance: window.BetaMath.betaVariance(post.alpha, post.beta),
    };
  });
  expect(result.mean).toBeCloseTo(0.5714285714285714, 9);
  expect(result.variance).toBeCloseTo(0.030612244897959183, 9);
});

test('BetaMath: 95% credible interval for Beta(4,3) matches reference values', async ({ page }) => {
  const ci = await page.evaluate(() => window.BetaMath.credibleInterval(4, 3, 0.95));
  expect(ci.lower).toBeCloseTo(0.22277809550314487, 6);
  expect(ci.upper).toBeCloseTo(0.8818827512427561, 6);
});

test('BetaMath: P(theta > 0.5) for Beta(4,3) matches reference value', async ({ page }) => {
  const p = await page.evaluate(() => window.BetaMath.posteriorProbGreaterThan(4, 3, 0.5));
  expect(p).toBeCloseTo(0.6562499999999998, 9);
});

test('BetaMath: Savage-Dickey Bayes factor BF10/BF01 are reciprocal and match reference values', async ({ page }) => {
  const bf = await page.evaluate(() => window.BetaMath.savageDickeyBayesFactor(1, 1, 4, 3, 0.5));
  expect(bf.bf01).toBeCloseTo(1.875000000000002, 6);
  expect(bf.bf10).toBeCloseTo(0.5333333333333328, 6);
  expect(bf.bf10 * bf.bf01).toBeCloseTo(1.0, 9);
});

test('BetaMath: Wilson score interval for 7/10 matches reference value', async ({ page }) => {
  const w = await page.evaluate(() => window.BetaMath.wilsonScoreInterval(7, 10, 0.95));
  expect(w.lower).toBeCloseTo(0.3967781474611453, 6);
  expect(w.upper).toBeCloseTo(0.8922087325936988, 6);
});

test('BetaMath: exact two-sided binomial test p-value matches known R binom.test result', async ({ page }) => {
  const p1 = await page.evaluate(() => window.BetaMath.exactBinomialTestPValue(7, 10, 0.5));
  const p2 = await page.evaluate(() => window.BetaMath.exactBinomialTestPValue(3, 10, 0.5));
  expect(p1).toBeCloseTo(0.34375, 6);
  expect(p2).toBeCloseTo(0.34375, 6);
});

test('BetaMath: credible interval bounds always satisfy 0 <= lower < upper <= 1 across varied shapes', async ({ page }) => {
  const shapes = [[0.5, 0.5], [1, 1], [50, 2], [2, 50], [200, 200]];
  for (const [a, b] of shapes) {
    const ci = await page.evaluate(([a, b]) => window.BetaMath.credibleInterval(a, b, 0.95), [a, b]);
    expect(ci.lower).toBeGreaterThanOrEqual(0);
    expect(ci.upper).toBeLessThanOrEqual(1);
    expect(ci.lower).toBeLessThan(ci.upper);
  }
});

// ---------- Scenario picker ----------

test('scenario picker sets threshold and description for a built-in scenario', async ({ page }) => {
  await page.selectOption('#scenario-select', 'manipulation');
  await expect(page.locator('#p0-input')).toHaveValue('0.8');
  const desc = await page.locator('#scenario-description').inputValue();
  expect(desc).toContain('manipulation');
});

test('Custom scenario allows free-text description and a custom p0', async ({ page }) => {
  await page.selectOption('#scenario-select', 'custom');
  await expect(page.locator('#scenario-description')).not.toHaveAttribute('readonly', '');
  await page.fill('#scenario-description', 'My own research question about response rates.');
  await page.fill('#p0-input', '0.42');
  await expect(page.locator('#scenario-description')).toHaveValue('My own research question about response rates.');
  await expect(page.locator('#p0-input')).toHaveValue('0.42');
});

// ---------- Prior elicitation modes ----------

test('Belief mode and Advanced mode stay in sync (rate 30%, weight 10 -> Beta(3,7))', async ({ page }) => {
  await page.evaluate(() => {
    const rate = document.getElementById('belief-rate');
    rate.value = '30';
    rate.dispatchEvent(new Event('input'));
    const weight = document.getElementById('belief-weight');
    weight.value = '10';
    weight.dispatchEvent(new Event('input'));
  });
  await expect(page.locator('#prior-readout')).toContainText('α=3.00');
  await expect(page.locator('#prior-readout')).toContainText('β=7.00');

  await page.click('#prior-mode-advanced');
  await expect(page.locator('#prior-alpha')).toHaveValue('3.00');
  await expect(page.locator('#prior-beta')).toHaveValue('7.00');
});

test('Advanced mode direct alpha/beta entry updates the prior readout', async ({ page }) => {
  await page.click('#prior-mode-advanced');
  await page.fill('#prior-alpha', '5');
  await page.fill('#prior-beta', '5');
  await expect(page.locator('#prior-readout')).toContainText('α=5.00');
  await expect(page.locator('#prior-readout')).toContainText('β=5.00');
});

// ---------- Trial entry, undo, reset ----------

test('adding successes and failures updates the trial summary and posterior mean', async ({ page }) => {
  await page.click('#prior-mode-advanced');
  await page.fill('#prior-alpha', '1');
  await page.fill('#prior-beta', '1');

  await page.click('#btn-add-success');
  await page.click('#btn-add-success');
  await page.click('#btn-add-failure');

  await expect(page.locator('#trial-summary')).toHaveText('n = 3 (2 successes, 1 failures)');
  // Posterior Beta(1+2, 1+1) = Beta(3,2), mean = 3/5 = 60.0%
  await expect(page.locator('#posterior-mean')).toHaveText('60.0%');
});

test('batch add inserts multiple trials at once', async ({ page }) => {
  await page.click('#prior-mode-advanced');
  await page.fill('#prior-alpha', '1');
  await page.fill('#prior-beta', '1');

  await page.fill('#batch-successes', '8');
  await page.fill('#batch-failures', '2');
  await page.click('#btn-batch-add');

  await expect(page.locator('#trial-summary')).toHaveText('n = 10 (8 successes, 2 failures)');
  const rows = page.locator('#history-body tr');
  await expect(rows).toHaveCount(1);
});

test('undo removes the most recent trial entry and recomputes the posterior', async ({ page }) => {
  await page.click('#btn-add-success');
  await page.click('#btn-add-success');
  await expect(page.locator('#trial-summary')).toHaveText(/n = 2 /);

  await page.click('#btn-undo');
  await expect(page.locator('#trial-summary')).toHaveText(/n = 1 /);
  const rows = page.locator('#history-body tr');
  await expect(rows).toHaveCount(1);
});

test('reset clears all trials and empties the history table', async ({ page }) => {
  await page.click('#btn-add-success');
  await page.click('#btn-add-failure');
  await page.click('#btn-reset');

  await expect(page.locator('#trial-summary')).toHaveText('n = 0 (0 successes, 0 failures)');
  const rows = page.locator('#history-body tr');
  await expect(rows).toHaveCount(0);
});

test('invalid batch input (negative counts) is rejected and does not corrupt state', async ({ page }) => {
  await page.fill('#batch-successes', '-3');
  await page.fill('#batch-failures', '2');
  await page.click('#btn-batch-add');
  // Negative successes rejected -> no trial should have been added
  await expect(page.locator('#trial-summary')).toHaveText('n = 0 (0 successes, 0 failures)');
});

test('switching scenario resets trial history', async ({ page }) => {
  await page.click('#btn-add-success');
  await page.click('#btn-add-success');
  await expect(page.locator('#trial-summary')).toHaveText(/n = 2 /);

  await page.selectOption('#scenario-select', 'replication');
  await expect(page.locator('#trial-summary')).toHaveText('n = 0 (0 successes, 0 failures)');
});

// ---------- Frequentist contrast panel ----------

test('frequentist panel shows MLE, Wilson CI, and p-value consistent with the entered data', async ({ page }) => {
  await page.fill('#batch-successes', '7');
  await page.fill('#batch-failures', '3');
  await page.click('#btn-batch-add');

  await expect(page.locator('#freq-mle')).toHaveText('70.0%');
  await expect(page.locator('#freq-pvalue')).not.toHaveText('—');
});

// ---------- AI narrative: template fallback (no network) and mocked key path ----------

test('AI narrative falls back to a deterministic template with zero network calls when no key is supplied', async ({ page }) => {
  let networkCalled = false;
  await page.route('**://api.anthropic.com/**', (route) => {
    networkCalled = true;
    route.abort();
  });

  await page.click('#btn-add-success');
  await page.click('#btn-generate-narrative');
  await expect(page.locator('#narrative-output')).not.toHaveText('Generating…');
  const text = await page.locator('#narrative-output').textContent();
  expect(text.length).toBeGreaterThan(20);
  expect(networkCalled).toBe(false);
});

test('AI narrative with a key present calls the API (intercepted, never live) and renders the mocked response', async ({ page }) => {
  await page.route('**://api.anthropic.com/v1/messages', (route) => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ content: [{ type: 'text', text: 'MOCKED AI NARRATIVE RESPONSE' }] }),
    });
  });

  await page.fill('#api-key-input', 'sk-ant-test-fake-key-not-real');
  await page.click('#btn-add-success');
  await page.click('#btn-generate-narrative');

  await expect(page.locator('#narrative-output')).toHaveText('MOCKED AI NARRATIVE RESPONSE');
});

test('a failed mocked API call gracefully falls back to the template rather than breaking the UI', async ({ page }) => {
  await page.route('**://api.anthropic.com/v1/messages', (route) => {
    route.fulfill({ status: 500, body: 'server error' });
  });

  await page.fill('#api-key-input', 'sk-ant-test-fake-key-not-real');
  await page.click('#btn-add-success');
  await page.click('#btn-generate-narrative');

  await expect(page.locator('#narrative-output')).toContainText('AI narrative unavailable');
});

// ---------- Security: script-injection inertness ----------

test('a script-injection payload in the Custom scenario description does not execute', async ({ page }) => {
  const dialogs = [];
  page.on('dialog', (d) => { dialogs.push(d.message()); d.dismiss(); });
  const pageErrors = [];
  page.on('pageerror', (err) => pageErrors.push(err.message));

  await page.selectOption('#scenario-select', 'custom');
  await page.fill('#scenario-description', '<img src=x onerror="window.__xssFired = true">');
  await page.click('#btn-add-success'); // triggers a render cycle

  const xssFired = await page.evaluate(() => window.__xssFired === true);
  expect(xssFired).toBe(false);
  expect(dialogs.length).toBe(0);
  expect(pageErrors.length).toBe(0);
});

// ---------- Layout ----------

test('layout remains usable at a narrow mobile viewport', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await expect(page.locator('#scenario-select')).toBeVisible();
  await expect(page.locator('#btn-add-success')).toBeVisible();
  await expect(page.locator('#beta-chart')).toBeVisible();
});

// ---------- Chart rendering ----------

test('the Beta chart canvas renders without throwing as the posterior updates', async ({ page }) => {
  const errors = [];
  page.on('pageerror', (err) => errors.push(err.message));
  await page.click('#btn-add-success');
  await page.click('#btn-add-failure');
  await page.fill('#batch-successes', '15');
  await page.fill('#batch-failures', '2');
  await page.click('#btn-batch-add');
  expect(errors.length).toBe(0);
});
