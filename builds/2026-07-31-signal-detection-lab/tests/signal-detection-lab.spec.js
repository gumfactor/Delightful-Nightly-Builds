const { test, expect } = require('@playwright/test');
const path = require('path');

const PAGE_URL = 'file://' + path.resolve(__dirname, '..', 'index.html');

test.beforeEach(async ({ page }) => {
  await page.goto(PAGE_URL);
  await page.evaluate(() => window.localStorage.clear());
  await page.reload();
});

// ---------- Core math correctness (independently cross-checked reference values) ----------

test('SdtMath: normalQuantile at known percentiles matches textbook z-values', async ({ page }) => {
  const results = await page.evaluate(() => ({
    median: window.SdtMath.normalQuantile(0.5),
    p975: window.SdtMath.normalQuantile(0.975),
    p025: window.SdtMath.normalQuantile(0.025),
  }));
  expect(results.median).toBeCloseTo(0, 4);
  expect(results.p975).toBeCloseTo(1.959964, 4);
  expect(results.p025).toBeCloseTo(-1.959964, 4);
});

test('SdtMath: normalCdf and normalQuantile are inverses of each other', async ({ page }) => {
  const results = await page.evaluate(() => {
    const M = window.SdtMath;
    return [0.1, 0.3, 0.5, 0.7, 0.9].map((p) => M.normalCdf(M.normalQuantile(p)));
  });
  results.forEach((val, i) => {
    expect(val).toBeCloseTo([0.1, 0.3, 0.5, 0.7, 0.9][i], 4);
  });
});

test('SdtMath: dPrime and criterionC match a textbook hit/false-alarm-rate pair', async ({ page }) => {
  const result = await page.evaluate(() => {
    const M = window.SdtMath;
    return { d: M.dPrime(0.8, 0.2), c: M.criterionC(0.8, 0.2) };
  });
  // z(0.8) ≈ 0.8416, z(0.2) ≈ -0.8416 -> d' ≈ 1.6833, c ≈ 0 (symmetric case)
  expect(result.d).toBeCloseTo(1.6833, 3);
  expect(result.c).toBeCloseTo(0, 3);
});

test('SdtMath: criterionC is negative (liberal) when hit rate exceeds (1 - FA rate)', async ({ page }) => {
  const c = await page.evaluate(() => window.SdtMath.criterionC(0.9, 0.5));
  expect(c).toBeLessThan(0);
});

test('SdtMath: criterionC is positive (conservative) when hit rate is well below (1 - FA rate)', async ({ page }) => {
  const c = await page.evaluate(() => window.SdtMath.criterionC(0.5, 0.05));
  expect(c).toBeGreaterThan(0);
});

test('SdtMath: rocAuc closed form matches trapezoidal numeric integration of rocCurve', async ({ page }) => {
  const diffs = await page.evaluate(() => {
    const M = window.SdtMath;
    return [0, 0.5, 1, 1.5, 2, 3].map((d) => {
      const auc = M.rocAuc(d);
      const numeric = M.rocAucNumeric(M.rocCurve(d, 401));
      return Math.abs(auc - numeric);
    });
  });
  diffs.forEach((diff) => expect(diff).toBeLessThan(0.001));
});

test('SdtMath: rocCurve endpoints are exactly (0,0) and (1,1)', async ({ page }) => {
  const points = await page.evaluate(() => window.SdtMath.rocCurve(1.5, 21));
  expect(points[0]).toEqual({ fa: 0, hit: 0 });
  expect(points[points.length - 1]).toEqual({ fa: 1, hit: 1 });
});

test('SdtMath: rocAuc(0) is 0.5 (chance) and increases monotonically with d\'', async ({ page }) => {
  const aucs = await page.evaluate(() => [0, 1, 2, 3].map((d) => window.SdtMath.rocAuc(d)));
  expect(aucs[0]).toBeCloseTo(0.5, 4);
  for (let i = 1; i < aucs.length; i++) {
    expect(aucs[i]).toBeGreaterThan(aucs[i - 1]);
  }
});

test('SdtMath: bDoublePrime is 0 at the unbiased point (hitRate + faRate = 1)', async ({ page }) => {
  const results = await page.evaluate(() => {
    const M = window.SdtMath;
    return [M.bDoublePrime(0.5, 0.5), M.bDoublePrime(0.7, 0.3), M.bDoublePrime(0.9, 0.1)];
  });
  results.forEach((b) => expect(Math.abs(b)).toBeLessThan(1e-9));
});

test('SdtMath: aPrime equals 0.5 at chance (hitRate == faRate) and 1.0 at perfect performance', async ({ page }) => {
  const results = await page.evaluate(() => {
    const M = window.SdtMath;
    return { chance: M.aPrime(0.5, 0.5), perfect: M.aPrime(0.999999, 0.000001) };
  });
  expect(results.chance).toBeCloseTo(0.5, 6);
  expect(results.perfect).toBeGreaterThan(0.99);
});

test('SdtMath: ratesFromCounts loglinear correction avoids infinite d\' at 0%/100% rates', async ({ page }) => {
  const result = await page.evaluate(() => {
    const M = window.SdtMath;
    const { hitRate, faRate } = M.ratesFromCounts(60, 0, 0, 60);
    return { hitRate, faRate, dPrime: M.dPrime(hitRate, faRate) };
  });
  expect(result.hitRate).toBeLessThan(1);
  expect(result.faRate).toBeGreaterThan(0);
  expect(isFinite(result.dPrime)).toBe(true);
  expect(result.dPrime).toBeGreaterThan(3);
});

test('SdtMath: ratesFromCounts throws when a condition has zero trials', async ({ page }) => {
  const threw = await page.evaluate(() => {
    try {
      window.SdtMath.ratesFromCounts(0, 0, 5, 5);
      return false;
    } catch (err) {
      return true;
    }
  });
  expect(threw).toBe(true);
});

test('SdtMath: dPrimeBucket classifies known values into the correct bucket', async ({ page }) => {
  const results = await page.evaluate(() => {
    const M = window.SdtMath;
    return [M.dPrimeBucket(0.3), M.dPrimeBucket(0.75), M.dPrimeBucket(1.5), M.dPrimeBucket(2.5), M.dPrimeBucket(4)];
  });
  expect(results).toEqual(['poor', 'weak', 'moderate', 'good', 'excellent']);
});

// ---------- UI: tab navigation ----------

test('UI: all four tabs are reachable and show their panel', async ({ page }) => {
  const tabs = ['explainer', 'roc', 'calculator', 'quiz'];
  for (const tab of tabs) {
    await page.getByTestId('tab-' + tab).click();
    await expect(page.getByTestId('panel-' + tab)).toBeVisible();
  }
});

test('UI: only the active tab panel is visible at a time', async ({ page }) => {
  await page.getByTestId('tab-calculator').click();
  await expect(page.getByTestId('panel-calculator')).toBeVisible();
  await expect(page.getByTestId('panel-explainer')).toBeHidden();
});

// ---------- UI: Explainer tab ----------

test('Explainer: dragging the criterion line updates d\', c, hit rate, and FA rate', async ({ page }) => {
  await page.getByTestId('tab-explainer').click();
  const before = await page.getByTestId('explainer-c').textContent();

  const canvas = page.getByTestId('explainer-canvas');
  const box = await canvas.boundingBox();
  await page.mouse.move(box.x + box.width * 0.3, box.y + box.height * 0.5);
  await page.mouse.down();
  await page.mouse.move(box.x + box.width * 0.85, box.y + box.height * 0.5);
  await page.mouse.up();

  const after = await page.getByTestId('explainer-c').textContent();
  expect(after).not.toBe(before);
});

test('Explainer: moving the d\' slider updates the displayed d\' and stays in sync with the ROC tab', async ({ page }) => {
  await page.getByTestId('tab-explainer').click();
  const slider = page.getByTestId('dprime-slider');
  await slider.fill('3');
  await slider.dispatchEvent('input');
  await expect(page.getByTestId('dprime-slider-value')).toHaveText('3.00');

  await page.getByTestId('tab-roc').click();
  await expect(page.getByTestId('roc-dprime')).toHaveText('3.00');
  const expectedAuc = await page.evaluate(() => window.SdtMath.rocAuc(3).toFixed(3));
  await expect(page.getByTestId('roc-auc')).toHaveText(expectedAuc);
});

// ---------- UI: Calculator tab ----------

test('Calculator: computing from raw counts matches sdt-math.js applied to the same corrected rates', async ({ page }) => {
  await page.getByTestId('tab-calculator').click();
  await page.getByTestId('calc-hits').fill('42');
  await page.getByTestId('calc-misses').fill('18');
  await page.getByTestId('calc-fa').fill('12');
  await page.getByTestId('calc-cr').fill('48');
  await page.getByTestId('calc-submit').click();

  const expected = await page.evaluate(() => {
    const M = window.SdtMath;
    const { hitRate, faRate } = M.ratesFromCounts(42, 18, 12, 48);
    return { d: M.dPrime(hitRate, faRate).toFixed(3), c: M.criterionC(hitRate, faRate).toFixed(3) };
  });
  await expect(page.getByTestId('calc-out-dprime')).toHaveText(expected.d);
  await expect(page.getByTestId('calc-out-c')).toHaveText(expected.c);
});

test('Calculator: unchecking the loglinear correction changes the computed d\' for extreme counts', async ({ page }) => {
  await page.getByTestId('tab-calculator').click();
  await page.getByTestId('calc-hits').fill('30');
  await page.getByTestId('calc-misses').fill('0');
  await page.getByTestId('calc-fa').fill('0');
  await page.getByTestId('calc-cr').fill('30');
  await page.getByTestId('calc-correction').uncheck();
  await page.getByTestId('calc-submit').click();

  const withoutCorrection = await page.getByTestId('calc-out-dprime').textContent();

  await page.getByTestId('calc-correction').check();
  await page.getByTestId('calc-submit').click();
  const withCorrection = await page.getByTestId('calc-out-dprime').textContent();

  expect(withoutCorrection).not.toBe(withCorrection);
});

test('Calculator: A\' and B\'\' are displayed and B\'\' is near zero for the near-symmetric default example', async ({ page }) => {
  await page.getByTestId('tab-calculator').click();
  await page.getByTestId('calc-submit').click();
  const aPrimeText = await page.getByTestId('calc-out-aprime').textContent();
  expect(parseFloat(aPrimeText)).toBeGreaterThan(0.5);
  expect(parseFloat(aPrimeText)).toBeLessThanOrEqual(1);
});

// ---------- UI: Scenario Quiz ----------

test('Quiz: a scenario is shown by default with a non-empty title and matrix counts', async ({ page }) => {
  await page.getByTestId('tab-quiz').click();
  const title = await page.getByTestId('quiz-title').textContent();
  expect(title.length).toBeGreaterThan(0);
  const hits = await page.getByTestId('quiz-hits').textContent();
  expect(parseInt(hits, 10)).toBeGreaterThan(0);
});

test('Quiz: submitting the correct bucket and bias is scored correct and updates the score display', async ({ page }) => {
  await page.getByTestId('tab-quiz').click();

  const truth = await page.evaluate(() => {
    const M = window.SdtMath;
    const s = window.SDT_SCENARIOS[0];
    const { hitRate, faRate } = M.ratesFromCounts(s.hits, s.misses, s.falseAlarms, s.correctRejections);
    const d = M.dPrime(hitRate, faRate);
    const c = M.criterionC(hitRate, faRate);
    return { bucket: M.dPrimeBucket(d), bias: M.criterionLabel(c) };
  });

  await page.locator(`input[name="quiz-bucket"][value="${truth.bucket}"]`).check();
  await page.locator(`input[name="quiz-bias"][value="${truth.bias}"]`).check();
  await page.getByTestId('quiz-submit').click();

  await expect(page.getByTestId('quiz-feedback')).toContainText('Correct');
  await expect(page.getByTestId('quiz-score')).toHaveText('1 / 1');
});

test('Quiz: submitting an incorrect answer is scored incorrect', async ({ page }) => {
  await page.getByTestId('tab-quiz').click();

  const truth = await page.evaluate(() => {
    const M = window.SdtMath;
    const s = window.SDT_SCENARIOS[0];
    const { hitRate, faRate } = M.ratesFromCounts(s.hits, s.misses, s.falseAlarms, s.correctRejections);
    return M.dPrimeBucket(M.dPrime(hitRate, faRate));
  });
  const wrongBucket = ['poor', 'weak', 'moderate', 'good', 'excellent'].find((b) => b !== truth);

  await page.locator(`input[name="quiz-bucket"][value="${wrongBucket}"]`).check();
  await page.locator('input[name="quiz-bias"][value="neutral"]').check();
  await page.getByTestId('quiz-submit').click();

  await expect(page.getByTestId('quiz-feedback')).toContainText('Not quite');
});

test('Quiz: score persists in localStorage across a page reload', async ({ page }) => {
  await page.getByTestId('tab-quiz').click();
  await page.locator('input[name="quiz-bucket"]').first().check();
  await page.locator('input[name="quiz-bias"]').first().check();
  await page.getByTestId('quiz-submit').click();

  const scoreBefore = await page.getByTestId('quiz-score').textContent();
  expect(scoreBefore).not.toBe('0 / 0');

  await page.reload();
  await page.getByTestId('tab-quiz').click();
  await expect(page.getByTestId('quiz-score')).toHaveText(scoreBefore);
});

test('Quiz: "Next Scenario" loads a different scenario and clears the previous feedback', async ({ page }) => {
  await page.getByTestId('tab-quiz').click();
  const firstTitle = await page.getByTestId('quiz-title').textContent();

  await page.locator('input[name="quiz-bucket"]').first().check();
  await page.locator('input[name="quiz-bias"]').first().check();
  await page.getByTestId('quiz-submit').click();
  await expect(page.getByTestId('quiz-feedback')).toBeVisible();

  await page.getByTestId('quiz-next').click();
  await expect(page.getByTestId('quiz-feedback')).toBeHidden();
  // Not a guarantee of a different title on every run (random pick), but across
  // several clicks it must differ at least once for more than one scenario to exist.
  let sawDifferent = firstTitle !== (await page.getByTestId('quiz-title').textContent());
  for (let i = 0; i < 5 && !sawDifferent; i++) {
    await page.getByTestId('quiz-next').click();
    sawDifferent = firstTitle !== (await page.getByTestId('quiz-title').textContent());
  }
  expect(sawDifferent).toBe(true);
});

// ---------- AI scenario generation ----------

test('AI scenario: with no API key supplied, zero network requests are made to Anthropic', async ({ page }) => {
  let requestMade = false;
  await page.route('**://api.anthropic.com/**', (route) => {
    requestMade = true;
    route.abort();
  });

  await page.getByTestId('tab-quiz').click();
  await page.getByTestId('ai-context').fill('eyewitness identification under stress');
  await page.getByTestId('ai-generate').click();
  await expect(page.getByTestId('ai-status')).toContainText('deterministic generator');
  expect(requestMade).toBe(false);
});

test('AI scenario: with a mocked successful Anthropic response, the returned scenario is used', async ({ page }) => {
  await page.route('**://api.anthropic.com/v1/messages', (route) => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        content: [{
          type: 'text',
          text: JSON.stringify({
            title: 'Mocked Scenario Title',
            description: 'A mocked description for testing.',
            hits: 40, misses: 10, falseAlarms: 8, correctRejections: 42,
          }),
        }],
      }),
    });
  });

  await page.getByTestId('tab-quiz').click();
  await page.getByTestId('ai-context').fill('memory recognition');
  await page.getByTestId('ai-key').fill('sk-ant-test-key-not-real');
  await page.getByTestId('ai-generate').click();

  await expect(page.getByTestId('quiz-title')).toHaveText('Mocked Scenario Title');
  await expect(page.getByTestId('ai-status')).toContainText('generated by Claude');
});

test('AI scenario: a failed Anthropic response falls back to the deterministic generator with no thrown error', async ({ page }) => {
  await page.route('**://api.anthropic.com/v1/messages', (route) => {
    route.fulfill({ status: 500, body: 'server error' });
  });

  const errors = [];
  page.on('pageerror', (err) => errors.push(err.message));

  await page.getByTestId('tab-quiz').click();
  await page.getByTestId('ai-context').fill('threat detection');
  await page.getByTestId('ai-key').fill('sk-ant-test-key-not-real');
  await page.getByTestId('ai-generate').click();

  await expect(page.getByTestId('ai-status')).toContainText('AI request failed');
  const title = await page.getByTestId('quiz-title').textContent();
  expect(title.length).toBeGreaterThan(0);
  expect(errors).toEqual([]);
});

// ---------- Security ----------

test('Security: a script payload typed into the AI context field renders as inert text, not executed', async ({ page }) => {
  let dialogFired = false;
  page.on('dialog', async (dialog) => {
    dialogFired = true;
    await dialog.dismiss();
  });

  await page.getByTestId('tab-quiz').click();
  await page.getByTestId('ai-context').fill('<script>alert(1)</script>');
  await page.getByTestId('ai-generate').click();

  await expect(page.getByTestId('quiz-title')).toContainText('<script>');
  expect(dialogFired).toBe(false);
});

test('Security: a persisted AI-generated title with an img onerror payload renders inert after reload', async ({ page }) => {
  await page.route('**://api.anthropic.com/v1/messages', (route) => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        content: [{
          type: 'text',
          text: JSON.stringify({
            title: '<img src=x onerror="window.__xss=true">',
            description: 'payload description',
            hits: 20, misses: 5, falseAlarms: 4, correctRejections: 21,
          }),
        }],
      }),
    });
  });

  let dialogFired = false;
  page.on('dialog', async (dialog) => {
    dialogFired = true;
    await dialog.dismiss();
  });

  await page.getByTestId('tab-quiz').click();
  await page.getByTestId('ai-key').fill('sk-ant-test-key-not-real');
  await page.getByTestId('ai-generate').click();

  const xssTriggered = await page.evaluate(() => window.__xss === true);
  expect(xssTriggered).toBe(false);
  expect(dialogFired).toBe(false);
});

// ---------- Responsive layout ----------

test('Responsive: layout does not overflow horizontally at a narrow mobile viewport', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 700 });
  await page.goto(PAGE_URL);
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  expect(overflow).toBeLessThanOrEqual(1);
});

test('Page loads with zero console errors', async ({ page }) => {
  const errors = [];
  page.on('pageerror', (err) => errors.push(err.message));
  page.on('console', (msg) => {
    if (msg.type() === 'error') errors.push(msg.text());
  });
  await page.goto(PAGE_URL);
  await page.getByTestId('tab-roc').click();
  await page.getByTestId('tab-calculator').click();
  await page.getByTestId('tab-quiz').click();
  expect(errors).toEqual([]);
});
