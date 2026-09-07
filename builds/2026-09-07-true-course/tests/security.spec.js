const { test, expect } = require('@playwright/test');
const path = require('path');

const INDEX_URL = `file://${path.resolve(__dirname, '../index.html')}`;

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => localStorage.clear());
  await page.goto(INDEX_URL);
});

async function completeDailyChallenge(page) {
  await page.locator('[data-testid="menu-daily-btn"]').click();
  for (let i = 0; i < 5; i++) {
    const puzzle = await page.evaluate(() => window.__TC_DEBUG.getCurrentPuzzle());
    if (puzzle.type === 'set-drift') {
      await page.locator('[data-testid="answer-input"]').fill(String(puzzle.correctAnswer));
      await page.locator('[data-testid="submit-btn"]').click();
    } else {
      await page.locator(`[data-testid="choice-btn"][data-choice="${puzzle.correctAnswer}"]`).click();
    }
    await page.locator('[data-testid="next-btn"]').click();
  }
}

test('a malicious AI response renders as inert text with zero dialogs or page errors', async ({ page }) => {
  const dialogs = [];
  const pageErrors = [];
  page.on('dialog', (d) => {
    dialogs.push(d.message());
    d.dismiss();
  });
  page.on('pageerror', (e) => pageErrors.push(String(e)));

  await page.route('https://api.anthropic.com/v1/messages', (route) => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        content: [
          { type: 'text', text: '<img src=x onerror="window.__xssFired=true">' + '</script><script>window.__xssFired2=true</script>' },
        ],
      }),
    });
  });

  await completeDailyChallenge(page);
  const scriptCountBefore = await page.locator('script').count();

  await page.locator('[data-testid="ai-key-input"]').fill('sk-test-fake-key');
  await page.locator('[data-testid="ai-fetch-btn"]').click();

  await expect(page.locator('[data-testid="ai-note-box"]')).toContainText('onerror');

  const scriptCountAfter = await page.locator('script').count();
  expect(scriptCountAfter).toBe(scriptCountBefore);
  expect(dialogs).toEqual([]);
  expect(pageErrors).toEqual([]);
  const xssFired = await page.evaluate(() => window.__xssFired === true || window.__xssFired2 === true);
  expect(xssFired).toBe(false);

  // Rendered as an inert <img> DOM node it would still not execute (no
  // dialog would fire from a broken image), so also confirm no such node
  // was ever created — the payload must be plain text, not parsed markup.
  const imgCount = await page.locator('[data-testid="ai-note-box"] img').count();
  expect(imgCount).toBe(0);
});

test('with no API key, zero network requests are made and the deterministic fallback note is shown', async ({ page }) => {
  let requestSeen = false;
  await page.route('https://api.anthropic.com/v1/messages', (route) => {
    requestSeen = true;
    route.abort();
  });

  await completeDailyChallenge(page);
  await page.locator('[data-testid="ai-fetch-btn"]').click();

  await expect(page.locator('[data-testid="ai-note-box"]')).toContainText("First Mate's Log");
  expect(requestSeen).toBe(false);
});

test('a failed AI request falls back to the deterministic note instead of hanging', async ({ page }) => {
  await page.route('https://api.anthropic.com/v1/messages', (route) => {
    route.fulfill({ status: 500, contentType: 'application/json', body: '{}' });
  });

  await completeDailyChallenge(page);
  await page.locator('[data-testid="ai-key-input"]').fill('sk-test-fake-key');
  await page.locator('[data-testid="ai-fetch-btn"]').click();

  await expect(page.locator('[data-testid="ai-note-box"]')).toContainText("First Mate's Log");
  await expect(page.locator('[data-testid="ai-note-box"]')).not.toContainText('Consulting');
});

test('the API key field is a password input and is never exposed on the debug hook', async ({ page }) => {
  await completeDailyChallenge(page);
  const keyInput = page.locator('[data-testid="ai-key-input"]');
  await expect(keyInput).toHaveAttribute('type', 'password');
  await keyInput.fill('sk-super-secret-value');

  const debugDump = await page.evaluate(() => JSON.stringify(window.__TC_DEBUG.getSession()));
  expect(debugDump).not.toContain('sk-super-secret-value');
});
