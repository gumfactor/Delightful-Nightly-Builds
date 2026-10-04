const { test, expect } = require('@playwright/test');
const path = require('path');
const fs = require('fs');

const BASE = 'file://' + path.resolve(__dirname, '..', 'index.html');
const url = (trials) => BASE + '?fast=1&test=1&trials=' + trials;
const INK_KEY = { red: 'r', green: 'g', blue: 'b', yellow: 'y' };

async function play(page, task, trials, chooser) {
  await page.getByTestId('play-' + task).click();
  await page.getByTestId('start-task').click();
  const stimulusId = task === 'ultimatum' ? 'offer' : 'stimulus';
  for (let i = 1; i <= trials; i++) {
    const stimulus = page.locator('[data-testid="' + stimulusId + '"][data-trial="' + i + '"]');
    await stimulus.waitFor({ state: 'attached' });
    const key = await chooser(stimulus);
    if (key) await page.keyboard.press(key);
  }
  await expect(page.getByTestId('summary')).toBeVisible();
}

const stroopCorrect = async (stimulus) => INK_KEY[await stimulus.getAttribute('data-ink')];
const stroopWrong = async (stimulus) => {
  const ink = await stimulus.getAttribute('data-ink');
  return INK_KEY[ink === 'red' ? 'blue' : 'red'];
};
const nbackPerfect = async (stimulus) => ((await stimulus.getAttribute('data-target')) === 'true' ? ' ' : null);
const gonogoPerfect = async (stimulus) => ((await stimulus.getAttribute('data-kind')) === 'go' ? ' ' : null);
const acceptAll = async () => 'a';

const savedSessions = (page) => page.evaluate(() => JSON.parse(localStorage.getItem('neuro-arcade.sessions.v1') || '[]'));

test('play tab lists the four tasks with zero saved sessions', async ({ page }) => {
  await page.goto(url(6));
  for (const key of ['stroop', 'nback', 'gonogo', 'ultimatum']) {
    await expect(page.getByTestId('task-card-' + key)).toContainText('0 sessions saved');
  }
});

test('Stroop is playable end to end and saves a scored session', async ({ page }) => {
  await page.goto(url(8));
  await play(page, 'stroop', 8, stroopCorrect);
  await expect(page.getByTestId('metric-accuracy').getByTestId('metric-value')).toHaveText('100%');
  const [session] = await savedSessions(page);
  expect(session.task).toBe('stroop');
  expect(session.trials).toHaveLength(8);
  expect(session.trials.every((t) => t.rt > 0)).toBe(true);
  expect(session.metrics.accuracy).toBe(1);
});

test('wrong Stroop key presses are scored as errors', async ({ page }) => {
  await page.goto(url(6));
  await play(page, 'stroop', 6, stroopWrong);
  const [session] = await savedSessions(page);
  expect(session.trials.some((t) => t.correct && t.response !== null && t.stimulus.split('/')[1] !== t.response)).toBe(false);
  expect(session.metrics.accuracy).toBeLessThan(0.5);
});

test('2-back is playable and perfect play yields a high d-prime', async ({ page }) => {
  await page.goto(url(12));
  await play(page, 'nback', 12, nbackPerfect);
  const [session] = await savedSessions(page);
  expect(session.task).toBe('nback');
  expect(session.metrics.targets).toBeGreaterThan(0);
  expect(session.metrics.hits).toBeGreaterThan(0);
  expect(session.metrics.falseAlarms).toBe(0);
});

test('Go/No-Go is playable and withholding on red squares gives zero commission errors', async ({ page }) => {
  await page.goto(url(12));
  await play(page, 'gonogo', 12, gonogoPerfect);
  const [session] = await savedSessions(page);
  expect(session.metrics.commissions).toBe(0);
  expect(session.metrics.nogoTrials).toBe(3);
  await expect(page.getByTestId('metric-commissionRate').getByTestId('metric-value')).toHaveText('0%');
});

test('Ultimatum accept-all earns the sum of offers and shows acceptance bars', async ({ page }) => {
  await page.goto(url(10));
  await play(page, 'ultimatum', 10, acceptAll);
  const [session] = await savedSessions(page);
  expect(session.metrics.earned).toBe(2 * (1 + 2 + 3 + 4 + 5));
  expect(session.metrics.rejectUnfair).toBe(0);
  await expect(page.getByTestId('accept-bars')).toBeVisible();
});

test('Escape quits a task without saving anything', async ({ page }) => {
  await page.goto(url(30));
  await page.getByTestId('play-ultimatum').click();
  await page.getByTestId('start-task').click();
  await page.getByTestId('offer').waitFor();
  await page.keyboard.press('Escape');
  await expect(page.getByTestId('start-task')).toBeHidden();
  expect(await savedSessions(page)).toHaveLength(0);
});

test('results tab shows the latest session after playing', async ({ page }) => {
  await page.goto(url(5));
  await play(page, 'ultimatum', 5, acceptAll);
  await page.getByTestId('close-summary').click();
  await page.getByTestId('tab-results').click();
  await expect(page.getByTestId('results-ultimatum')).toContainText('1 session');
  await expect(page.getByTestId('results-stroop')).toContainText('Not played yet');
});

test('export downloads trial-level CSV and import into a clean browser reproduces the session', async ({ page, browser }, testInfo) => {
  await page.goto(url(5));
  await play(page, 'ultimatum', 5, acceptAll);
  await page.getByTestId('close-summary').click();
  await page.getByTestId('tab-data').click();
  const [download] = await Promise.all([page.waitForEvent('download'), page.getByTestId('export-csv').click()]);
  const file = testInfo.outputPath('export.csv');
  await download.saveAs(file);
  const text = fs.readFileSync(file, 'utf8');
  expect(text.split('\n')[0]).toBe('session_id,task,timestamp,label,seed,trial,condition,stimulus,response,correct,rt_ms');
  expect(text.trim().split('\n')).toHaveLength(6);

  const original = (await savedSessions(page))[0];
  const other = await (await browser.newContext()).newPage();
  await other.goto(url(5));
  await other.getByTestId('tab-data').click();
  await other.getByTestId('import-csv').setInputFiles(file);
  await expect(other.getByTestId('data-status')).toContainText('Imported 1 new sessions');
  const [imported] = await savedSessions(other);
  expect(imported).toEqual(original);

  await other.getByTestId('import-csv').setInputFiles(file);
  await expect(other.getByTestId('data-status')).toContainText('skipped 1 already present');
  expect(await savedSessions(other)).toHaveLength(1);
});

test('importing a non-Neuro-Arcade CSV shows an error and leaves data untouched', async ({ page }, testInfo) => {
  await page.goto(url(5));
  const bad = testInfo.outputPath('bad.csv');
  fs.writeFileSync(bad, 'name,score\nann,3\n');
  await page.getByTestId('tab-data').click();
  await page.getByTestId('import-csv').setInputFiles(bad);
  await expect(page.getByTestId('data-status')).toContainText('Import failed');
  expect(await savedSessions(page)).toHaveLength(0);
});

test('delete all data asks for confirmation and clears sessions', async ({ page }) => {
  await page.goto(url(5));
  await play(page, 'ultimatum', 5, acceptAll);
  await page.getByTestId('close-summary').click();
  await page.getByTestId('tab-data').click();
  page.once('dialog', (dialog) => dialog.dismiss());
  await page.getByTestId('clear-data').click();
  expect(await savedSessions(page)).toHaveLength(1);
  page.once('dialog', (dialog) => dialog.accept());
  await page.getByTestId('clear-data').click();
  await expect(page.getByTestId('data-status')).toContainText('deleted');
  expect(await savedSessions(page)).toHaveLength(0);
});

test('participant label is rendered as text, never as HTML', async ({ page }) => {
  await page.goto(url(5));
  const evil = '<u id=x onclick=1>hi</u>';
  await page.getByTestId('tab-data').click();
  await page.getByTestId('label-input').fill(evil);
  await page.getByTestId('tab-play').click();
  await play(page, 'ultimatum', 5, acceptAll);
  await page.getByTestId('close-summary').click();
  await page.getByTestId('tab-data').click();
  await expect(page.getByTestId('class-table')).toContainText(evil);
  expect(await page.locator('#view-data u').count()).toBe(0);
});

test('class view groups sessions by label', async ({ page }, testInfo) => {
  await page.goto(url(5));
  const header = await page.evaluate(() => NAStore.HEADER.join(','));
  const rows = [1, 2, 3, 4, 5].map((n) => ['u-' + n, 'ultimatum', 1, 'S' + (n % 2), 1, 1, 'offer_' + n, n, 'accept', '', 700].join(','));
  const file = testInfo.outputPath('class.csv');
  fs.writeFileSync(file, [header].concat(rows).join('\n'));
  await page.getByTestId('tab-data').click();
  await page.getByTestId('import-csv').setInputFiles(file);
  await expect(page.getByTestId('class-table').locator('tbody tr')).toHaveCount(2);
});

test('layout fits a 390px phone screen without horizontal scrolling', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 800 });
  await page.goto(url(5));
  for (const tab of ['play', 'results', 'data']) {
    await page.getByTestId('tab-' + tab).click();
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    expect(overflow).toBeLessThanOrEqual(0);
  }
});
