const { test, expect } = require('@playwright/test');
const path = require('path');

const INDEX_URL = 'file://' + path.resolve(__dirname, '..', 'index.html');
const AI_URL = 'https://api.anthropic.com/v1/messages';

async function solveChapter2(page) {
  await page.evaluate(() => window.ZebraLab.startPuzzle('practice', 2));
  await page.evaluate(() => {
    const { puzzle } = window.ZebraLab.state;
    const attrCats = puzzle.categories.filter((c) => c.id !== 'position');
    for (let p = 0; p < puzzle.size; p++) {
      attrCats.forEach((cat) => {
        const select = document.querySelector(`[data-testid="grid-select-${cat.id}-${p}"]`);
        select.value = String(puzzle.solution[cat.id][p]);
        select.dispatchEvent(new Event('change'));
      });
    }
  });
  await page.locator('[data-testid="btn-check"]').click();
  await expect(page.locator('[data-testid="screen-result"]')).toBeVisible({ timeout: 3000 });
}

test.describe('AI explainer: deterministic fallback and mocked network calls', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(INDEX_URL);
    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });
  });

  test('with no API key: shows the deterministic fallback and makes no network call', async ({ page }) => {
    let calledAI = false;
    await page.route(AI_URL, (route) => {
      calledAI = true;
      route.abort();
    });

    await solveChapter2(page);
    await page.waitForFunction(() => document.getElementById('ai-explanation-text').textContent !== 'Loading explanation…');

    const source = await page.locator('[data-testid="ai-explanation-text"]').getAttribute('data-source');
    expect(source).toBe('fallback');
    expect(calledAI).toBe(false);

    const expectedText = await page.evaluate(() => {
      const pair = window.zlPickExplainerPair(window.ZebraLab.state.puzzle);
      return window.zlComposeExplanation(pair.confoundId, pair.threatId);
    });
    await expect(page.locator('[data-testid="ai-explanation-text"]')).toHaveText(expectedText);
  });

  test('with an API key and a successful mocked response: shows the AI-sourced text', async ({ page }) => {
    await page.evaluate(() => sessionStorage.setItem('zebralab_api_key', 'test-key-123'));
    await page.route(AI_URL, (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ content: [{ text: 'MOCKED AI EXPLANATION TEXT' }] }),
      });
    });

    await solveChapter2(page);
    await page.waitForFunction(() => document.getElementById('ai-explanation-text').textContent !== 'Loading explanation…');

    await expect(page.locator('[data-testid="ai-explanation-text"]')).toHaveText('MOCKED AI EXPLANATION TEXT');
    const source = await page.locator('[data-testid="ai-explanation-text"]').getAttribute('data-source');
    expect(source).toBe('ai');
  });

  test('with an API key and a failed mocked response: falls back to the deterministic text without throwing', async ({ page }) => {
    await page.evaluate(() => sessionStorage.setItem('zebralab_api_key', 'test-key-456'));
    await page.route(AI_URL, (route) => {
      route.fulfill({ status: 500, contentType: 'application/json', body: JSON.stringify({ error: 'boom' }) });
    });

    const pageErrors = [];
    page.on('pageerror', (err) => pageErrors.push(err));

    await solveChapter2(page);
    await page.waitForFunction(() => document.getElementById('ai-explanation-text').textContent !== 'Loading explanation…');

    const source = await page.locator('[data-testid="ai-explanation-text"]').getAttribute('data-source');
    expect(source).toBe('fallback');
    expect(pageErrors).toHaveLength(0);
  });

  test('the API key field never persists to localStorage, only sessionStorage', async ({ page }) => {
    await page.fill('[data-testid="api-key-input"]', 'should-not-leak');
    await page.locator('[data-testid="api-key-input"]').dispatchEvent('change');
    const localStorageDump = await page.evaluate(() => JSON.stringify(localStorage));
    expect(localStorageDump).not.toContain('should-not-leak');
    const sessionValue = await page.evaluate(() => sessionStorage.getItem('zebralab_api_key'));
    expect(sessionValue).toBe('should-not-leak');
  });
});
