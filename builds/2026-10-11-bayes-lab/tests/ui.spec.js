const { test, expect } = require('@playwright/test');
const path = require('path');
const { pathToFileURL } = require('url');

const URL = pathToFileURL(path.join(__dirname, '..', 'index.html')).href;
const t = (page, id) => page.getByTestId(id);
const setRange = (page, id, value) => t(page, id).evaluate((node, v) => { node.value = String(v); node.dispatchEvent(new Event('input', { bubbles: true })); }, value);

test.beforeEach(async ({ page }) => { await page.goto(URL); });

test('app opens on lesson 1 with six tabs and routes by hash', async ({ page }) => {
  await expect(t(page, 'lesson-title')).toHaveText('Update a belief');
  await expect(page.locator('[data-testid="nav"] a')).toHaveCount(6);
  await t(page, 'tab-shrinkage').click();
  await expect(t(page, 'lesson-title')).toHaveText('Shrinkage');
  await page.goto(URL + '#/nonsense');
  await expect(t(page, 'lesson-title')).toHaveText('Update a belief');
});

test('lesson 1: flat prior and 3 of 3 successes yields posterior mean 0.800 and P(theta>0.5)=93.8%', async ({ page }) => {
  for (let i = 0; i < 3; i++) await t(page, 'add-success').click();
  await expect(t(page, 'post-mean')).toHaveText('0.800');
  await expect(t(page, 'post-gt-half')).toHaveText('93.8%');
  await expect(t(page, 'data-n')).toHaveValue('3');
  await expect(page.locator('[data-testid="beta-chart"] svg')).toBeVisible();
});

test('lesson 1: choosing the skeptical preset fills alpha and beta; editing them switches to custom', async ({ page }) => {
  await t(page, 'prior-preset').selectOption('skeptic');
  await expect(t(page, 'prior-a')).toHaveValue('10');
  await expect(t(page, 'prior-mean')).toHaveText('0.500');
  await t(page, 'prior-a').fill('4');
  await expect(t(page, 'prior-preset')).toHaveValue('custom');
});

test('lesson 1: successes above trials are clamped with a visible message; garbage input is flagged, not fatal', async ({ page }) => {
  await t(page, 'data-n').fill('5');
  await t(page, 'data-k').fill('9');
  await expect(t(page, 'data-k')).toHaveValue('5');
  await expect(t(page, 'beta-msg')).toContainText('cannot exceed');
  await t(page, 'prior-a').fill('');
  await expect(t(page, 'prior-a')).toHaveAttribute('aria-invalid', 'true');
  await expect(t(page, 'post-mean')).not.toHaveText('');
});

test('lesson 1: simulate adds exactly 10 trials and reset clears data', async ({ page }) => {
  await t(page, 'simulate').click();
  await expect(t(page, 'data-n')).toHaveValue('10');
  expect(Number(await t(page, 'data-k').inputValue())).toBeLessThanOrEqual(10);
  await t(page, 'reset-data').click();
  await expect(t(page, 'data-n')).toHaveValue('0');
  await expect(t(page, 'post-mean')).toHaveText('0.500');
});

test('lesson 1: ROPE probability for flat prior and [0.45, 0.55] is 10.0%', async ({ page }) => {
  await expect(t(page, 'rope-prob')).toHaveText('10.0%');
});

test('lesson 2: default rare-condition scenario shows PPV 8.3% and 9 of 108 true positives', async ({ page }) => {
  await t(page, 'tab-base-rate').click();
  await expect(t(page, 'ppv')).toHaveText('8.3%');
  await expect(t(page, 'freq-sentence')).toContainText('Of 108 people flagged, only 9 actually have it');
  await expect(page.locator('[data-testid="dots"] circle')).toHaveCount(1000);
});

test('lesson 2: balanced scenario raises PPV above 90% and extreme specificity changes counts', async ({ page }) => {
  await t(page, 'tab-base-rate').click();
  await t(page, 'scenario').selectOption('balanced');
  await expect(t(page, 'ppv')).toHaveText('90.0%');
  await setRange(page, 'spec', 100);
  await expect(t(page, 'ppv')).toHaveText('100.0%');
});

test('lesson 3: more data shrinks disagreement between the two priors', async ({ page }) => {
  await t(page, 'tab-two').click();
  await setRange(page, 'count', 0);
  await expect(t(page, 'mean-gap')).toHaveText('60.0 points');
  await setRange(page, 'count', 300);
  const gap = parseFloat(await t(page, 'mean-gap').innerText());
  expect(gap).toBeLessThan(5);
  await expect(t(page, 'agree-n')).toHaveText(/^\d+$/);
});

test("lesson 4: Lindley preset shows p < .05 yet favours the null, with disagreement message", async ({ page }) => {
  await t(page, 'tab-bayes-factor').click();
  await t(page, 'preset-lindley').click();
  expect(parseFloat(await t(page, 'bf-p').innerText())).toBeLessThan(0.05);
  expect(parseFloat(await t(page, 'bf01').innerText())).toBeGreaterThan(5);
  await expect(t(page, 'bf-verdict')).toContainText('for the null');
  await expect(t(page, 'bf-contrast')).toContainText('Disagreement');
});

test('lesson 4: Savage-Dickey readout agrees with BF01 and ambiguous preset is anecdotal', async ({ page }) => {
  await t(page, 'tab-bayes-factor').click();
  await expect(t(page, 'bf-verdict')).toContainText('no real preference');
  await expect(t(page, 'bf01')).toHaveText(await t(page, 'bf-sd').innerText());
});

test('lesson 4: successes above trials are clamped', async ({ page }) => {
  await t(page, 'tab-bayes-factor').click();
  await t(page, 'bf-n').fill('20');
  await t(page, 'bf-k').fill('50');
  await expect(t(page, 'bf-k')).toHaveValue('20');
  await expect(t(page, 'bf-msg')).toContainText('cannot exceed');
});

test('lesson 5: replication preset shrinks 0.80 toward the prior with equal weight (0.40, 50%)', async ({ page }) => {
  await t(page, 'tab-shrinkage').click();
  await expect(t(page, 'sh-mean')).toHaveText('0.400');
  await expect(t(page, 'sh-weight')).toHaveText('50%');
  await expect(t(page, 'sh-shrunk')).toHaveText('0.400');
});

test('lesson 5: precise new study dominates; zero SE is rejected without NaN output', async ({ page }) => {
  await t(page, 'tab-shrinkage').click();
  await t(page, 'shrink-preset').selectOption('precise');
  expect(parseFloat(await t(page, 'sh-weight').innerText())).toBeGreaterThan(90);
  await t(page, 'sh-se').fill('0');
  await expect(t(page, 'sh-mean')).not.toHaveText(/NaN/);
});

test('quiz: submit disabled until all answered; perfect confident answers give Brier 0.000', async ({ page }) => {
  await t(page, 'tab-quiz').click();
  await expect(t(page, 'quiz-submit')).toBeDisabled();
  const truths = [true, false, false, true, false, true, true, false];
  for (let i = 0; i < truths.length; i++) {
    await t(page, truths[i] ? `quiz-true-${i}` : `quiz-false-${i}`).check();
    await setRange(page, `quiz-conf-${i}`, 100);
  }
  await expect(t(page, 'quiz-submit')).toBeEnabled();
  await t(page, 'quiz-submit').click();
  await expect(t(page, 'quiz-correct')).toHaveText('8 / 8');
  await expect(t(page, 'quiz-brier')).toHaveText('0.000');
  await expect(t(page, 'quiz-why-2')).toContainText('8.3%');
  await expect(t(page, 'quiz-history').locator('li')).toHaveCount(1);
});

test('quiz: all wrong at full confidence gives Brier 1.000 and an overconfidence verdict', async ({ page }) => {
  await t(page, 'tab-quiz').click();
  const wrong = [false, true, true, false, true, false, false, true];
  for (let i = 0; i < wrong.length; i++) {
    await t(page, wrong[i] ? `quiz-true-${i}` : `quiz-false-${i}`).check();
    await setRange(page, `quiz-conf-${i}`, 100);
  }
  await t(page, 'quiz-submit').click();
  await expect(t(page, 'quiz-brier')).toHaveText('1.000');
  await expect(t(page, 'quiz-verdict')).toContainText('Overconfident');
});

test('quiz still scores when localStorage is unavailable', async ({ page }) => {
  await page.addInitScript(() => {
    Object.defineProperty(window, 'localStorage', { get() { throw new Error('blocked'); } });
  });
  await page.goto(URL + '#/quiz');
  for (let i = 0; i < 8; i++) await t(page, `quiz-true-${i}`).check();
  await t(page, 'quiz-submit').click();
  await expect(t(page, 'quiz-correct')).toHaveText('4 / 8');
  await expect(t(page, 'quiz-brier')).toHaveText('0.250');
});

test('layout: no horizontal page scroll at 375px width on every lesson', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 700 });
  for (const id of ['update', 'base-rate', 'two', 'bayes-factor', 'shrinkage', 'quiz']) {
    await page.goto(`${URL}#/${id}`);
    await page.reload();
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    expect(overflow, `lesson ${id}`).toBeLessThanOrEqual(0);
  }
});
