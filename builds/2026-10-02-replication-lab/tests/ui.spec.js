const { test, expect } = require('@playwright/test');
const path = require('path');
const url = 'file://' + path.resolve(__dirname, '../index.html');

async function open(page, tab) {
  await page.goto(url);
  await page.getByTestId('tab-' + tab).click();
}

test('opens on the Power lab with a prediction prompt and no results yet', async ({ page }) => {
  await page.goto(url);
  await expect(page.getByRole('heading', { name: /Power/ })).toBeVisible();
  await expect(page.getByTestId('predict')).toBeVisible();
  await expect(page.getByTestId('takeaway')).toHaveCount(0);
});

test('power lab: running reveals simulated power and records the prediction miss', async ({ page }) => {
  await open(page, 'power');
  await page.getByTestId('c-d').fill('0.5');
  await page.getByTestId('c-n').fill('64');
  await page.getByTestId('predict').fill('80');
  await page.getByTestId('run').click();
  const power = await page.getByTestId('stat-power').innerText();
  expect(parseFloat(power)).toBeGreaterThan(74);
  expect(parseFloat(power)).toBeLessThan(86);
  await expect(page.getByTestId('predict-note')).toContainText('You said 80');
  await expect(page.getByTestId('calibration')).toContainText('Your predictions: 1');
});

test('power lab: same seed gives identical results, new random sample changes the seed', async ({ page }) => {
  await open(page, 'power');
  await page.getByTestId('run').click();
  const first = await page.getByTestId('stat-power').innerText();
  await page.getByTestId('run').click();
  await expect(page.getByTestId('stat-power')).toHaveText(first);
  const seedBefore = await page.getByTestId('seed').inputValue();
  await page.getByTestId('reroll').click();
  await expect(page.getByTestId('stat-power')).toBeVisible();
  expect(await page.getByTestId('seed').inputValue()).not.toBe(seedBefore);
});

test('power lab: n needed for 80% power is about 64 for d = 0.5', async ({ page }) => {
  await open(page, 'power');
  await page.getByTestId('c-d').fill('0.5');
  await page.getByTestId('run').click();
  const needed = parseInt(await page.getByTestId('stat-needed').innerText(), 10);
  expect(needed).toBeGreaterThanOrEqual(63);
  expect(needed).toBeLessThanOrEqual(66);
});

test('peeking lab: peeking inflates false positives above one planned test', async ({ page }) => {
  await open(page, 'peeking');
  await page.getByTestId('run').click();
  const peek = parseFloat(await page.getByTestId('stat-peek').innerText());
  const fixedRate = parseFloat(await page.getByTestId('stat-fixed').innerText());
  expect(peek).toBeGreaterThan(fixedRate * 2);
  await expect(page.getByTestId('takeaway')).toContainText('stopping rule');
});

test('many-outcomes lab: Bonferroni brings the familywise rate back near alpha', async ({ page }) => {
  await open(page, 'forking');
  await page.getByTestId('run').click();
  const uncorrected = parseFloat(await page.getByTestId('stat-family').innerText());
  await page.getByTestId('c-correction').selectOption('bonferroni');
  await page.getByTestId('run').click();
  await expect(page.getByTestId('takeaway')).toContainText('bonferroni');
  const corrected = parseFloat(await page.getByTestId('stat-family').innerText());
  expect(uncorrected).toBeGreaterThan(20);
  expect(corrected).toBeLessThan(9);
});

test('winner\'s curse lab: published average exceeds the true effect', async ({ page }) => {
  await open(page, 'curse');
  await page.getByTestId('run').click();
  const published = parseFloat(await page.getByTestId('stat-published').innerText());
  expect(published).toBeGreaterThan(0.5);
  await expect(page.getByTestId('stat-inflation')).toContainText('x');
});

test('bayes lab: renders immediately and moving the prior changes the posterior', async ({ page }) => {
  await open(page, 'bayes');
  await expect(page.getByTestId('stat-mean')).toHaveText('68.2%');
  await page.getByTestId('c-prior').selectOption('skeptic');
  await expect(page.getByTestId('stat-mean')).toHaveText('56.7%');
});

test('bayes lab: successes above trials are clamped instead of crashing', async ({ page }) => {
  await open(page, 'bayes');
  await page.getByTestId('c-n').fill('10');
  await page.getByTestId('c-k').fill('50');
  await expect(page.getByTestId('stat-mean')).toHaveText('91.7%');
});

test('layout fits a 390px phone without horizontal scroll', async ({ page }) => {
  await open(page, 'forking');
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow).toBeLessThanOrEqual(0);
});
