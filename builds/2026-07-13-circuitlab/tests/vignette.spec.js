const path = require('path');
const { test, expect } = require('@playwright/test');

const APP_URL = 'file://' + path.resolve(__dirname, '../index.html');

test.describe('Case Vignette mode — offline curated bank', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(APP_URL);
    await page.click('[data-testid="mode-tab-vignette"]');
  });

  test('shows a curated vignette with 4 region choices and no network activity', async ({ page }) => {
    const requests = [];
    page.on('request', (req) => requests.push(req.url()));

    await expect(page.locator('#vignette-text')).not.toHaveText('');
    await expect(page.locator('#vignette-source')).toHaveText('Curated');
    await expect(page.locator('.choice-btn[data-testid="vignette-choice"]')).toHaveCount(4);

    const anthropicCalls = requests.filter((u) => u.includes('anthropic.com'));
    expect(anthropicCalls).toEqual([]);
  });

  test('the Generate New Vignette button is disabled until an API key is entered', async ({ page }) => {
    await expect(page.locator('#generate-vignette-btn')).toBeDisabled();
    await page.fill('#anthropic-key-input', 'sk-ant-test-key');
    await expect(page.locator('#generate-vignette-btn')).toBeEnabled();
    await page.fill('#anthropic-key-input', '');
    await expect(page.locator('#generate-vignette-btn')).toBeDisabled();
  });

  test('selecting the correct region shows correct feedback and its explanation', async ({ page }) => {
    const q = await page.evaluate(() => window.CircuitLabApp.getCurrentQuestion());
    await page.click(`.choice-btn[data-choice-region="${q.vignette.targetRegion}"]`);
    await expect(page.locator('#vignette-feedback')).toHaveClass(/feedback-correct/);
    await expect(page.locator('#vignette-feedback')).toContainText(q.vignette.explanation);
  });

  test('selecting a wrong region shows incorrect feedback naming the target region', async ({ page }) => {
    const q = await page.evaluate(() => window.CircuitLabApp.getCurrentQuestion());
    const wrongChoice = q.choices.find((c) => c !== q.vignette.targetRegion);
    await page.click(`.choice-btn[data-choice-region="${wrongChoice}"]`);
    await expect(page.locator('#vignette-feedback')).toHaveClass(/feedback-incorrect/);
  });

  test('Next cycles to a different curated vignette and updates progress', async ({ page }) => {
    const q1 = await page.evaluate(() => window.CircuitLabApp.getCurrentQuestion());
    await page.click(`.choice-btn[data-choice-region="${q1.vignette.targetRegion}"]`);
    await page.click('#vignette-next');
    await expect(page.locator('#vignette-progress')).toHaveText('2 / 8');
  });

  test('completing all 8 curated vignettes shows the session summary', async ({ page }) => {
    for (let i = 0; i < 8; i++) {
      const q = await page.evaluate(() => window.CircuitLabApp.getCurrentQuestion());
      await page.click(`.choice-btn[data-choice-region="${q.vignette.targetRegion}"]`);
      await page.click('#vignette-next');
    }
    await expect(page.locator('#panel-session-summary')).toBeVisible();
    await expect(page.locator('#summary-text')).toHaveText('8 / 8 correct (100%)');
  });
});

test.describe('Case Vignette mode — AI generation (mocked, no live network calls)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(APP_URL);
    await page.click('[data-testid="mode-tab-vignette"]');
  });

  test('generating a vignette calls the mocked Anthropic endpoint and displays the AI result', async ({ page }) => {
    await page.route('https://api.anthropic.com/v1/messages', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          content: [
            {
              type: 'tool_use',
              name: 'submit_vignette',
              input: {
                text: 'A mocked vignette about reward learning and reversal deficits.',
                targetRegion: 'ofc',
                explanation: 'Mocked explanation tying the vignette to OFC.',
              },
            },
          ],
        }),
      });
    });

    await page.fill('#anthropic-key-input', 'sk-ant-mock-key');
    await page.click('#generate-vignette-btn');

    await expect(page.locator('#vignette-source')).toHaveText('AI-generated');
    await expect(page.locator('#vignette-text')).toHaveText('A mocked vignette about reward learning and reversal deficits.');
    await expect(page.locator('#vignette-ai-status')).toHaveText('New vignette generated.');
    await expect(page.locator('.choice-btn[data-choice-region="ofc"]')).toBeVisible();
  });

  test('an API error response is surfaced to the user without crashing the app', async ({ page }) => {
    await page.route('https://api.anthropic.com/v1/messages', (route) => {
      route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({ error: { message: 'invalid x-api-key' } }),
      });
    });

    const errors = [];
    page.on('pageerror', (err) => errors.push(err.message));

    await page.fill('#anthropic-key-input', 'sk-ant-bad-key');
    await page.click('#generate-vignette-btn');

    await expect(page.locator('#vignette-ai-status')).toHaveText('invalid x-api-key');
    await expect(page.locator('#vignette-ai-status')).toHaveClass(/ai-status-error/);
    expect(errors).toEqual([]);
  });

  test('a malformed/empty API key is handled gracefully without a network call', async ({ page }) => {
    let called = false;
    await page.route('https://api.anthropic.com/v1/messages', (route) => {
      called = true;
      route.abort();
    });

    await page.fill('#anthropic-key-input', '   ');
    await expect(page.locator('#generate-vignette-btn')).toBeDisabled();
    expect(called).toBe(false);
  });

  test('the AI request is sent with the direct-browser-access header and never includes a hardcoded key', async ({ page }) => {
    let capturedHeaders = null;
    await page.route('https://api.anthropic.com/v1/messages', (route, request) => {
      capturedHeaders = request.headers();
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          content: [{ type: 'tool_use', name: 'submit_vignette', input: { text: 'x', targetRegion: 'amygdala', explanation: 'y' } }],
        }),
      });
    });

    await page.fill('#anthropic-key-input', 'sk-ant-header-check');
    await page.click('#generate-vignette-btn');
    await expect(page.locator('#vignette-ai-status')).toHaveText('New vignette generated.');

    expect(capturedHeaders['anthropic-dangerous-direct-browser-access']).toBe('true');
    expect(capturedHeaders['x-api-key']).toBe('sk-ant-header-check');

    const pageSource = await page.content();
    expect(pageSource).not.toContain('sk-ant-header-check');
  });
});
