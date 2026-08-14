// @ts-nocheck
const { test, expect } = require('@playwright/test');
const path = require('path');

const APP_URL = 'file://' + path.join(__dirname, '..', 'index.html');

test.beforeEach(async ({ page }) => {
  await page.goto(APP_URL);
});

test('loads with the Live Meter tab active and shows the uncalibrated banner', async ({ page }) => {
  await expect(page.locator('[data-tab-panel="live"]')).toHaveClass(/active/);
  await expect(page.locator('#uncalibrated-banner')).toBeVisible();
  await expect(page.locator('[data-testid="db-reading"]')).toHaveText('-- dB');
});

test('tab navigation switches the active panel', async ({ page }) => {
  await page.click('[data-tab-button="history"]');
  await expect(page.locator('[data-tab-panel="history"]')).toHaveClass(/active/);
  await expect(page.locator('[data-tab-panel="live"]')).not.toHaveClass(/active/);

  await page.click('[data-tab-button="calibration"]');
  await expect(page.locator('[data-tab-panel="calibration"]')).toHaveClass(/active/);
});

test('starting the live meter captures real (fake-device) audio readings end-to-end', async ({ page }) => {
  await page.click('[data-testid="start-meter-btn"]');
  await expect(page.locator('[data-testid="stop-meter-btn"]')).toBeVisible();
  await expect(page.locator('[data-testid="start-meter-btn"]')).toBeHidden();

  // wait for at least one real reading to come back through getUserMedia -> AnalyserNode -> audio-math.js
  await expect(page.locator('[data-testid="db-reading"]')).not.toHaveText('-- dB', { timeout: 10000 });
  const reading = await page.locator('[data-testid="db-reading"]').textContent();
  expect(reading).toMatch(/-?\d+\.\d dB\(A\)/);
  await expect(page.locator('[data-testid="zone-badge"]')).not.toHaveText('');

  await page.click('[data-testid="stop-meter-btn"]');
  await expect(page.locator('[data-testid="start-meter-btn"]')).toBeVisible();
  await expect(page.locator('[data-testid="session-summary"]')).toBeVisible();
});

test('save session flow requires a venue name before saving', async ({ page }) => {
  await page.click('[data-testid="start-meter-btn"]');
  await page.waitForTimeout(1200); // let a few readings accumulate
  await page.click('[data-testid="stop-meter-btn"]');
  await expect(page.locator('[data-testid="save-session-panel"]')).toBeVisible();

  await page.click('[data-testid="save-session-btn"]');
  await expect(page.locator('#venue-validation')).toBeVisible();

  await page.fill('[data-testid="venue-input"]', 'Test Cafe');
  await page.click('[data-testid="save-session-btn"]');
  await expect(page.locator('[data-testid="save-session-panel"]')).toBeHidden();
});

test('saved session appears in History with correct venue and reload-persists', async ({ page }) => {
  await page.click('[data-testid="start-meter-btn"]');
  await page.waitForTimeout(1200);
  await page.click('[data-testid="stop-meter-btn"]');
  await page.fill('[data-testid="venue-input"]', 'Library Reading Room');
  await page.click('[data-testid="save-session-btn"]');

  await page.click('[data-tab-button="history"]');
  await expect(page.locator('[data-testid="history-row"]')).toHaveCount(1);
  await expect(page.locator('[data-testid="history-row"]')).toContainText('Library Reading Room');

  await page.reload();
  await page.click('[data-tab-button="history"]');
  await expect(page.locator('[data-testid="history-row"]')).toHaveCount(1);
  await expect(page.locator('[data-testid="history-row"]')).toContainText('Library Reading Room');
});

test('clicking a history row opens the session detail panel with a rendered chart', async ({ page }) => {
  await page.click('[data-testid="start-meter-btn"]');
  await page.waitForTimeout(1200);
  await page.click('[data-testid="stop-meter-btn"]');
  await page.fill('[data-testid="venue-input"]', 'Gym Floor');
  await page.click('[data-testid="save-session-btn"]');

  await page.click('[data-tab-button="history"]');
  await page.click('[data-testid="history-row"]');
  await expect(page.locator('[data-testid="session-detail"]')).toBeVisible();
  await expect(page.locator('#detail-venue')).toHaveText('Gym Floor');
  const chartHandle = page.locator('[data-testid="detail-chart"]');
  await expect(chartHandle).toBeVisible();
});

test('history search filters sessions by venue', async ({ page }) => {
  for (const venue of ['Coffee Shop', 'Subway Platform']) {
    await page.click('[data-testid="start-meter-btn"]');
    await page.waitForTimeout(800);
    await page.click('[data-testid="stop-meter-btn"]');
    await page.fill('[data-testid="venue-input"]', venue);
    await page.click('[data-testid="save-session-btn"]');
  }

  await page.click('[data-tab-button="history"]');
  await expect(page.locator('[data-testid="history-row"]')).toHaveCount(2);

  await page.fill('[data-testid="history-search"]', 'subway');
  await expect(page.locator('[data-testid="history-row"]')).toHaveCount(1);
  await expect(page.locator('[data-testid="history-row"]')).toContainText('Subway Platform');
});

test('deleting a session removes it from history', async ({ page }) => {
  await page.click('[data-testid="start-meter-btn"]');
  await page.waitForTimeout(800);
  await page.click('[data-testid="stop-meter-btn"]');
  await page.fill('[data-testid="venue-input"]', 'Kitchen');
  await page.click('[data-testid="save-session-btn"]');

  await page.click('[data-tab-button="history"]');
  await page.click('[data-testid="history-row"]');
  await page.click('[data-testid="delete-session-btn"]');
  await expect(page.locator('[data-testid="history-row"]')).toHaveCount(0);
  await expect(page.locator('#history-empty')).toBeVisible();
});

test('a script-injection payload in venue and note renders as inert text, not executable markup', async ({ page }) => {
  const payload = '</script><script>window.__xss = true;</script><img src=x onerror="window.__xss2 = true">';
  let dialogFired = false;
  page.on('dialog', () => {
    dialogFired = true;
  });
  const pageErrors = [];
  page.on('pageerror', (err) => pageErrors.push(err));

  await page.click('[data-testid="start-meter-btn"]');
  await page.waitForTimeout(800);
  await page.click('[data-testid="stop-meter-btn"]');
  await page.fill('[data-testid="venue-input"]', payload);
  await page.fill('[data-testid="note-input"]', payload);
  await page.click('[data-testid="save-session-btn"]');

  await page.click('[data-tab-button="history"]');
  await page.click('[data-testid="history-row"]');

  const xssFired = await page.evaluate(() => window.__xss === true || window.__xss2 === true);
  expect(xssFired).toBe(false);
  expect(dialogFired).toBe(false);
  expect(pageErrors.length).toBe(0);

  const venueText = await page.locator('#detail-venue').textContent();
  expect(venueText).toContain('<script>');
  const innerHtml = await page.locator('#detail-venue').innerHTML();
  expect(innerHtml).not.toContain('<img');
});

test('calibration flow sets an offset that changes the live reading', async ({ page }) => {
  await page.click('[data-tab-button="calibration"]');
  await page.click('[data-testid="calib-start-btn"]');
  await expect(page.locator('[data-testid="calib-raw-reading"]')).not.toHaveText('', { timeout: 10000 });

  const rawText = await page.locator('[data-testid="calib-raw-reading"]').textContent();
  const rawDb = parseFloat(rawText);
  expect(Number.isNaN(rawDb)).toBe(false);

  await page.fill('#calib-reference-input', String(rawDb + 10));
  await page.click('[data-testid="calib-set-btn"]');
  await page.click('[data-testid="calib-stop-btn"]');

  await expect(page.locator('[data-testid="calibration-status"]')).toContainText('Calibrated: offset');
  await expect(page.locator('[data-testid="calibration-status"]')).toContainText('10.0 dB');
});

test('calibration set button validates a numeric reference before a raw reading exists', async ({ page }) => {
  await page.click('[data-tab-button="calibration"]');
  await page.click('[data-testid="calib-set-btn"]');
  await expect(page.locator('[data-testid="calib-validation"]')).toBeVisible();
});

test('reset calibration returns to the uncalibrated state', async ({ page }) => {
  await page.click('[data-tab-button="calibration"]');
  await page.click('[data-testid="calib-start-btn"]');
  await expect(page.locator('[data-testid="calib-raw-reading"]')).not.toHaveText('', { timeout: 10000 });
  const rawText = await page.locator('[data-testid="calib-raw-reading"]').textContent();
  await page.fill('#calib-reference-input', String(parseFloat(rawText) + 5));
  await page.click('[data-testid="calib-set-btn"]');
  await page.click('[data-testid="calib-stop-btn"]');
  await expect(page.locator('[data-testid="calibration-status"]')).toContainText('Calibrated');

  await page.click('[data-testid="calib-reset-btn"]');
  await expect(page.locator('[data-testid="calibration-status"]')).toContainText('Not calibrated');

  await page.click('[data-tab-button="live"]');
  await expect(page.locator('#uncalibrated-banner')).toBeVisible();
});

test('AI briefing falls back to a deterministic template and makes zero network requests with no key', async ({ page }) => {
  let anthropicRequestCount = 0;
  await page.route('**://api.anthropic.com/**', (route) => {
    anthropicRequestCount += 1;
    route.abort();
  });

  await page.click('[data-testid="start-meter-btn"]');
  await page.waitForTimeout(800);
  await page.click('[data-testid="stop-meter-btn"]');
  await page.fill('[data-testid="venue-input"]', 'Office Desk');
  await page.click('[data-testid="save-session-btn"]');

  await page.click('[data-tab-button="history"]');
  await page.click('[data-testid="history-row"]');
  await page.click('[data-testid="ai-briefing-btn"]');

  await expect(page.locator('[data-testid="ai-briefing-text"]')).not.toHaveText('', { timeout: 5000 });
  await expect(page.locator('[data-testid="ai-briefing-text"]')).toContainText('Office Desk');
  expect(anthropicRequestCount).toBe(0);
});

test('AI briefing uses a mocked Anthropic response when a key is supplied', async ({ page }) => {
  await page.route('**://api.anthropic.com/v1/messages', (route) => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ content: [{ text: 'This mocked briefing confirms the AI path was used.' }] }),
    });
  });

  await page.click('[data-testid="start-meter-btn"]');
  await page.waitForTimeout(800);
  await page.click('[data-testid="stop-meter-btn"]');
  await page.fill('[data-testid="venue-input"]', 'Studio');
  await page.click('[data-testid="save-session-btn"]');

  await page.click('[data-tab-button="history"]');
  await page.click('[data-testid="history-row"]');
  await page.fill('[data-testid="ai-key-input"]', 'sk-ant-fake-test-key');
  await page.click('[data-testid="ai-briefing-btn"]');

  await expect(page.locator('[data-testid="ai-briefing-text"]')).toContainText('This mocked briefing confirms the AI path was used.');
});

test('microphone permission denial shows an error and re-enables the start button', async ({ page, context }) => {
  await page.addInitScript(() => {
    navigator.mediaDevices.getUserMedia = () => Promise.reject(new DOMException('Permission denied', 'NotAllowedError'));
  });
  await page.reload();

  await page.click('[data-testid="start-meter-btn"]');
  await expect(page.locator('[data-testid="mic-error"]')).toBeVisible();
  await expect(page.locator('[data-testid="start-meter-btn"]')).toBeVisible();
  await expect(page.locator('[data-testid="stop-meter-btn"]')).toBeHidden();
});

test('narrow mobile viewport does not overflow and controls remain usable', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 700 });
  await page.goto(APP_URL);
  const bodyOverflow = await page.evaluate(() => document.body.scrollWidth <= window.innerWidth + 1);
  expect(bodyOverflow).toBe(true);
  await expect(page.locator('[data-testid="start-meter-btn"]')).toBeVisible();
});
