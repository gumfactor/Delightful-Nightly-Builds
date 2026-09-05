const { test, expect } = require('@playwright/test');
const path = require('path');

const INDEX_URL = 'file://' + path.join(__dirname, '..', 'index.html');
const XSS_PAYLOAD = '</script><script>window.__xss_fired=true;</script><img src=x onerror="window.__xss_fired=true">';

test.beforeEach(async ({ page }) => {
  await page.goto(INDEX_URL);
});

test.describe('Security', () => {
  test('an XSS payload in a mocked Claude API response renders as inert text, never executes', async ({ page }) => {
    await page.route('https://api.anthropic.com/v1/messages', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ content: [{ text: XSS_PAYLOAD }] }),
      });
    });

    await page.getByTestId('med-generate').click();
    await page.getByTestId('api-key-input').fill('fake-test-key-not-real');
    await page.getByTestId('med-explain-btn').click();
    await expect(page.getByTestId('med-explanation')).toHaveText(XSS_PAYLOAD);

    const xssFired = await page.evaluate(() => window.__xss_fired);
    expect(xssFired).toBeUndefined();

    // Confirm no extra <script> or <img> nodes were injected into the explanation container.
    const injectedNodes = await page.evaluate(() => {
      const el = document.querySelector('[data-testid="med-explanation"]');
      return el.querySelectorAll('script, img').length;
    });
    expect(injectedNodes).toBe(0);
  });

  test('with no API key set, the Explain button makes zero network requests to the Claude API', async ({ page }) => {
    let requestCount = 0;
    await page.route('https://api.anthropic.com/**', (route) => {
      requestCount++;
      route.abort();
    });
    await page.getByTestId('med-generate').click();
    await page.getByTestId('med-explain-btn').click();
    await page.waitForTimeout(150);
    expect(requestCount).toBe(0);
    const text = await page.getByTestId('med-explanation').textContent();
    expect(text.length).toBeGreaterThan(0);
  });

  test('a script-payload seed value is only hashed to a number, never rendered or executed', async ({ page }) => {
    const dialogs = [];
    page.on('dialog', (d) => { dialogs.push(d.message()); d.dismiss(); });
    await page.getByTestId('med-seed').fill('<img src=x onerror="window.__seed_xss=true">');
    await page.getByTestId('med-generate').click();
    await expect(page.getByTestId('med-results')).toBeVisible();
    const xssFired = await page.evaluate(() => window.__seed_xss);
    expect(xssFired).toBeUndefined();
    expect(dialogs).toEqual([]);
  });

  test('no horizontal overflow at a 375px mobile viewport on the mediation tab', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 800 });
    await page.getByTestId('med-generate').click();
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    expect(overflow).toBeLessThanOrEqual(1);
  });

  test('the API key input is type="password" so it is not shown in plain text on screen', async ({ page }) => {
    const type = await page.getByTestId('api-key-input').getAttribute('type');
    expect(type).toBe('password');
  });
});
