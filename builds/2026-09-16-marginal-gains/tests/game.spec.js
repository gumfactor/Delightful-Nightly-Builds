const { test, expect } = require('@playwright/test');
const path = require('path');

const Engine = require(path.join(__dirname, '..', 'src', 'engine.js'));

const INDEX_URL = `file://${path.resolve(__dirname, '../index.html')}`;

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => localStorage.clear());
});

async function goHome(page) {
  await page.goto(INDEX_URL);
}

/* ================================================================
   1 — Page load & Home
================================================================ */
test('page loads with correct title and home view visible', async ({ page }) => {
  await goHome(page);
  await expect(page).toHaveTitle('Marginal Gains');
  await expect(page.locator('#view-home')).toBeVisible();
  await expect(page.locator('[data-testid="btn-daily"]')).toBeEnabled();
  await expect(page.locator('[data-testid="daily-status"]')).toContainText('available');
});

/* ================================================================
   2 — Tutorial
================================================================ */
test('tutorial slider updates value and marginal readouts to the correct computed numbers', async ({ page }) => {
  await goHome(page);
  await page.locator('[data-testid="btn-tutorial"]').click();
  await expect(page.locator('#view-tutorial')).toBeVisible();

  const slider = page.locator('[data-testid="tutorial-slider"]');
  await slider.fill('5');
  await slider.dispatchEvent('input');

  // Fixed tutorial project: threshold=2, weight=10, maxHours=10 -> value(h) = round(10*sqrt(h-2))
  const expectedValueAt5 = Math.round(10 * Math.sqrt(5 - 2)); // 17
  const expectedValueAt6 = Math.round(10 * Math.sqrt(6 - 2)); // 20
  await expect(page.locator('[data-testid="tut-hours"]')).toHaveText('5');
  await expect(page.locator('[data-testid="tut-value"]')).toHaveText(String(expectedValueAt5));
  await expect(page.locator('[data-testid="tut-marginal"]')).toHaveText(String(expectedValueAt6 - expectedValueAt5));
});

test('tutorial value is zero below the threshold', async ({ page }) => {
  await goHome(page);
  await page.locator('[data-testid="btn-tutorial"]').click();
  const slider = page.locator('[data-testid="tutorial-slider"]');
  await slider.fill('1');
  await slider.dispatchEvent('input');
  await expect(page.locator('[data-testid="tut-value"]')).toHaveText('0');
});

test('finishing the tutorial returns to Home', async ({ page }) => {
  await goHome(page);
  await page.locator('[data-testid="btn-tutorial"]').click();
  await page.locator('[data-testid="btn-tutorial-done"]').click();
  await expect(page.locator('#view-home')).toBeVisible();
});

/* ================================================================
   3 — Practice round: setup, allocation, budget gating
================================================================ */
test('practice mode difficulty picker leads to a play view with the right project count and budget', async ({ page }) => {
  await goHome(page);
  await page.locator('[data-testid="btn-practice"]').click();
  await expect(page.locator('#view-difficulty')).toBeVisible();
  await page.locator('[data-testid="diff-6"]').click();

  await expect(page.locator('#view-play')).toBeVisible();
  await expect(page.locator('.project-card')).toHaveCount(6);
  await expect(page.locator('[data-testid="budget-total"]')).toHaveText('40');
  await expect(page.locator('[data-testid="budget-used"]')).toHaveText('0');
});

test('allocating hours on a project updates its displayed value and the budget bar', async ({ page }) => {
  await goHome(page);
  await page.locator('[data-testid="btn-practice"]').click();
  await page.locator('[data-testid="diff-4"]').click();

  const firstCard = page.locator('.project-card').first();
  await firstCard.locator('[data-action="plus5"]').click();
  await firstCard.locator('[data-action="plus1"]').click();

  await expect(firstCard.locator('.project-hours')).toHaveText('6h');
  await expect(page.locator('[data-testid="budget-used"]')).toHaveText('6');
  await expect(page.locator('[data-testid="budget-remaining"]')).toHaveText('18'); // 24 - 6
});

test('allocating past the total budget disables Lock In', async ({ page }) => {
  // Pin Math.random's single seeding call so the practice draw is fully
  // deterministic and reproducible via the same engine.js required here.
  await page.addInitScript(() => {
    Math.random = () => 0.999999;
  });
  const seed = (0.999999 * 4294967296) >>> 0;
  const projects = Engine.drawProjects(Engine.mulberry32(seed), 4);
  const maxTotal = projects.reduce((s, p) => s + p.maxHours, 0);
  expect(maxTotal).toBeGreaterThan(24); // sanity check on the fixed seed's draw vs. the 24h diff-4 budget

  await goHome(page);
  await page.locator('[data-testid="btn-practice"]').click();
  await page.locator('[data-testid="diff-4"]').click(); // 4 projects, 24h budget

  const cards = page.locator('.project-card');
  for (let i = 0; i < 4; i++) {
    const card = cards.nth(i);
    for (let click = 0; click < 4; click++) {
      await card.locator('[data-action="plus5"]').click();
    }
  }
  await expect(page.locator('[data-testid="btn-lock-in"]')).toBeDisabled();
});

test('a minus stepper never takes a project below 0 hours', async ({ page }) => {
  await goHome(page);
  await page.locator('[data-testid="btn-practice"]').click();
  await page.locator('[data-testid="diff-4"]').click();

  const firstCard = page.locator('.project-card').first();
  await firstCard.locator('[data-action="minus5"]').click();
  await expect(firstCard.locator('.project-hours')).toHaveText('0h');
});

/* ================================================================
   4 — Lock-in, results, AI advisor
================================================================ */
test('locking in a valid allocation shows results with a full breakdown table', async ({ page }) => {
  await goHome(page);
  await page.locator('[data-testid="btn-practice"]').click();
  await page.locator('[data-testid="diff-4"]').click();

  const firstCard = page.locator('.project-card').first();
  await firstCard.locator('[data-action="plus5"]').click();
  await page.locator('[data-testid="btn-lock-in"]').click();

  await expect(page.locator('#view-results')).toBeVisible();
  await expect(page.locator('#results-tbody tr')).toHaveCount(4);
  const percentText = await page.locator('[data-testid="score-percent"]').textContent();
  const percent = Number(percentText);
  expect(percent).toBeGreaterThanOrEqual(0);
  expect(percent).toBeLessThanOrEqual(100);
  await expect(page.locator('[data-testid="grade-badge"]')).not.toHaveText('-');
});

test('AI advisor shows a non-empty deterministic fallback note immediately, with no key required', async ({ page }) => {
  await goHome(page);
  await page.locator('[data-testid="btn-practice"]').click();
  await page.locator('[data-testid="diff-4"]').click();
  await page.locator('[data-testid="btn-lock-in"]').click();

  const note = page.locator('[data-testid="advisor-note"]');
  await expect(note).not.toHaveText('');
});

test('AI advisor makes zero network requests when no API key is supplied', async ({ page }) => {
  let requestCount = 0;
  await page.route('https://api.anthropic.com/**', async (route) => {
    requestCount += 1;
    await route.abort();
  });
  await goHome(page);
  await page.locator('[data-testid="btn-practice"]').click();
  await page.locator('[data-testid="diff-4"]').click();
  await page.locator('[data-testid="btn-lock-in"]').click();

  await page.locator('[data-testid="btn-get-coaching"]').click();
  await page.waitForTimeout(200);
  expect(requestCount).toBe(0);
  const note = await page.locator('[data-testid="advisor-note"]').textContent();
  expect(note.length).toBeGreaterThan(0);
  expect(note).not.toBe('Thinking…');
});

test('a malicious AI response renders as inert text, never as executed markup', async ({ page }) => {
  const dialogs = [];
  page.on('dialog', (d) => {
    dialogs.push(d.message());
    d.dismiss();
  });

  await page.route('https://api.anthropic.com/**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        content: [{ text: '<img src=x onerror="alert(1)"> </script><script>window.__pwned = true;</script>' }]
      })
    });
  });

  await goHome(page);
  await page.locator('[data-testid="btn-practice"]').click();
  await page.locator('[data-testid="diff-4"]').click();
  await page.locator('[data-testid="btn-lock-in"]').click();

  await page.locator('[data-testid="ai-key-input"]').fill('fake-session-only-key');
  await page.locator('[data-testid="btn-get-coaching"]').click();

  await expect(page.locator('[data-testid="advisor-note"]')).toContainText('onerror', { timeout: 5000 });
  expect(dialogs.length).toBe(0);
  const pwned = await page.evaluate(() => window.__pwned === true);
  expect(pwned).toBe(false);
  const injectedImg = await page.locator('[data-testid="advisor-note"] img').count();
  expect(injectedImg).toBe(0);
});

/* ================================================================
   5 — Daily Challenge gating
================================================================ */
test('Daily Challenge can be completed once and produces a shareable result', async ({ page }) => {
  await goHome(page);
  await page.locator('[data-testid="btn-daily"]').click();
  await expect(page.locator('#view-play')).toBeVisible();
  await expect(page.locator('.project-card')).toHaveCount(6);

  await page.locator('[data-testid="btn-lock-in"]').click();
  await expect(page.locator('#view-results')).toBeVisible();
  await expect(page.locator('[data-testid="share-text"]')).toBeVisible();
  await expect(page.locator('[data-testid="share-text"]')).toContainText('Daily Challenge');
});

test('a second Daily Challenge attempt on the same UTC date is blocked', async ({ page }) => {
  await goHome(page);
  await page.locator('[data-testid="btn-daily"]').click();
  await page.locator('[data-testid="btn-lock-in"]').click();
  await expect(page.locator('#view-results')).toBeVisible();

  await page.locator('[data-testid="btn-back-home"]').click();
  await expect(page.locator('[data-testid="btn-daily"]')).toBeDisabled();
  await expect(page.locator('[data-testid="daily-status"]')).toContainText('complete');
});

/* ================================================================
   6 — Dashboard
================================================================ */
test('Mastery Dashboard reflects a completed round', async ({ page }) => {
  await goHome(page);
  await page.locator('[data-testid="btn-practice"]').click();
  await page.locator('[data-testid="diff-4"]').click();
  await page.locator('[data-testid="btn-lock-in"]').click();

  await page.locator('[data-nav="dashboard"]').click();
  await expect(page.locator('#view-dashboard')).toBeVisible();
  const stats = page.locator('[data-testid="dashboard-stats"] .stat-tile');
  await expect(stats).toHaveCount(4);
  await expect(stats.first().locator('.stat-value')).toHaveText('1'); // Rounds Played
  const categoryStats = page.locator('[data-testid="category-stats"] .stat-tile');
  await expect(categoryStats.first()).toBeVisible();
});

/* ================================================================
   7 — Cross-cutting: mobile layout and console cleanliness
================================================================ */
test('renders without horizontal overflow at a 375px mobile viewport', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 700 });
  await goHome(page);
  const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
  expect(scrollWidth).toBeLessThanOrEqual(380);
});

test('a full play-through produces zero console errors and zero page errors', async ({ page }) => {
  const errors = [];
  page.on('pageerror', (err) => errors.push(String(err)));
  page.on('console', (msg) => {
    if (msg.type() === 'error') errors.push(msg.text());
  });

  await goHome(page);
  await page.locator('[data-testid="btn-tutorial"]').click();
  await page.locator('[data-testid="tutorial-slider"]').fill('4');
  await page.locator('[data-testid="tutorial-slider"]').dispatchEvent('input');
  await page.locator('[data-testid="btn-tutorial-done"]').click();

  await page.locator('[data-testid="btn-practice"]').click();
  await page.locator('[data-testid="diff-6"]').click();
  await page.locator('.project-card').first().locator('[data-action="plus5"]').click();
  await page.locator('[data-testid="btn-lock-in"]').click();

  await page.locator('[data-nav="dashboard"]').click();

  expect(errors).toEqual([]);
});
