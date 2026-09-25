const { test, expect } = require('@playwright/test');
const path = require('path');

const URL = 'file://' + path.join(__dirname, '..', 'index.html');
const HOSTILE = '</script><script>window.__xss=true;</script><img src=x onerror="window.__xss2=true">';

test.describe('hostile-payload rendering safety', () => {
  test('a hostile task name in a custom level renders as inert text everywhere it appears', async ({ page }) => {
    const dialogs = [];
    page.on('dialog', async (d) => {
      dialogs.push(d.message());
      await d.dismiss();
    });
    const pageErrors = [];
    page.on('pageerror', (e) => pageErrors.push(String(e)));

    await page.goto(URL);

    // Inject a hostile campaign level after load, before any script reads Levels,
    // by mutating the already-parsed Levels.CAMPAIGN_LEVELS in place.
    await page.evaluate((hostile) => {
      window.Levels.CAMPAIGN_LEVELS[0] = {
        id: 'L1',
        title: hostile,
        flavor: hostile,
        numLanes: 2,
        tasks: [
          { id: 'A', name: hostile, duration: 2, deps: [] },
          { id: 'B', name: hostile, duration: 3, deps: ['A'] },
        ],
      };
    }, HOSTILE);

    await page.getByTestId('btn-campaign').click();
    await page.getByTestId('level-btn-L1').click();

    // Reach the result screen (which also renders the hostile name in the lane recap).
    await page.getByTestId('ready-A').click();
    await page.getByTestId('lane-0').click();
    await page.getByTestId('ready-B').click();
    await page.getByTestId('lane-0').click();
    await page.getByTestId('btn-submit').click();
    await expect(page.getByTestId('result-grade')).toBeVisible();

    expect(dialogs).toEqual([]);
    expect(pageErrors).toEqual([]);
    const xssFired = await page.evaluate(() => window.__xss === true || window.__xss2 === true);
    expect(xssFired).toBe(false);

    // Exactly the page's own two <script> tags for engine/levels/graph/ai/game — never an injected one.
    const scriptCount = await page.evaluate(() => document.querySelectorAll('script').length);
    expect(scriptCount).toBe(5);
    const injectedImgs = await page.evaluate(() => document.querySelectorAll('img').length);
    expect(injectedImgs).toBe(0);

    // The hostile string appears verbatim as text, not parsed as markup.
    const resultLanesText = await page.getByTestId('result-lanes').innerText();
    expect(resultLanesText).toContain(HOSTILE);
  });

  test('a hostile mocked AI response renders as inert text, not executed markup', async ({ page }) => {
    const dialogs = [];
    page.on('dialog', async (d) => {
      dialogs.push(d.message());
      await d.dismiss();
    });
    await page.route('https://api.anthropic.com/**', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ content: [{ text: HOSTILE }] }),
      });
    });

    await page.goto(URL);
    await page.getByTestId('btn-tutorial').click();
    await page.getByTestId('ready-A').click();
    await page.getByTestId('lane-0').click();
    await page.getByTestId('ready-B').click();
    await page.getByTestId('lane-0').click();
    await page.getByTestId('ready-C').click();
    await page.getByTestId('lane-1').click();
    await page.getByTestId('btn-submit').click();

    await page.getByTestId('ai-key-input').fill('sk-test-not-real');
    await page.getByTestId('btn-get-debrief').click();
    await expect(page.getByTestId('ai-note')).toHaveText(HOSTILE);

    expect(dialogs).toEqual([]);
    const xssFired = await page.evaluate(() => window.__xss === true || window.__xss2 === true);
    expect(xssFired).toBe(false);
    const injectedImgs = await page.evaluate(() => document.querySelectorAll('img').length);
    expect(injectedImgs).toBe(0);
  });

  test('the shipped source has zero innerHTML assignments', async ({}, testInfo) => {
    const fs = require('fs');
    const files = ['engine.js', 'levels.js', 'graph.js', 'ai.js', 'game.js'].map((f) =>
      fs.readFileSync(path.join(__dirname, '..', 'src', f), 'utf8')
    );
    files.forEach((content) => {
      expect(content).not.toMatch(/\.innerHTML\s*=/);
    });
  });

  test('the AI key input never leaves the page as anything but the Anthropic header on an explicit user action', async ({ page }) => {
    const requestedUrls = [];
    await page.route('**/*', (route) => {
      requestedUrls.push(route.request().url());
      route.continue();
    });
    await page.goto(URL);
    await page.getByTestId('btn-tutorial').click();
    // Never type a key or click "Get Debrief" — confirm no outbound request was attempted at all
    // beyond loading the local page's own files.
    const external = requestedUrls.filter((u) => !u.startsWith('file://'));
    expect(external).toEqual([]);
  });
});
