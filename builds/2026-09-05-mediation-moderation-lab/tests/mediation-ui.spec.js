const { test, expect } = require('@playwright/test');
const path = require('path');

const INDEX_URL = 'file://' + path.join(__dirname, '..', 'index.html');

async function setSlider(page, testid, value) {
  await page.evaluate(({ testid, value }) => {
    const el = document.querySelector('[data-testid="' + testid + '"]');
    el.value = String(value);
    el.dispatchEvent(new Event('input', { bubbles: true }));
  }, { testid, value });
}

test.beforeEach(async ({ page }) => {
  await page.goto(INDEX_URL);
});

test.describe('Mediation Lab UI', () => {
  test('moving a slider updates its displayed value', async ({ page }) => {
    await setSlider(page, 'med-a', 1.5);
    await expect(page.getByTestId('med-a-val')).toHaveText('1.50');
  });

  test('Generate Sample reveals the results card with populated fields', async ({ page }) => {
    await expect(page.getByTestId('med-results')).toBeHidden();
    await page.getByTestId('med-generate').click();
    await expect(page.getByTestId('med-results')).toBeVisible();
    const indirectText = await page.getByTestId('med-indirect').textContent();
    expect(indirectText.trim().length).toBeGreaterThan(0);
    const ciText = await page.getByTestId('med-ci').textContent();
    expect(ciText).toMatch(/\[.*,.*\]/);
  });

  test('the same seed produces an identical indirect effect across two separate generations', async ({ page }) => {
    await page.getByTestId('med-seed').fill('reproducible-seed');
    await page.getByTestId('med-generate').click();
    const first = await page.getByTestId('med-indirect').textContent();
    await page.getByTestId('med-generate').click();
    const second = await page.getByTestId('med-indirect').textContent();
    expect(first).toBe(second);
  });

  test('a different seed can produce a different indirect effect', async ({ page }) => {
    await page.getByTestId('med-seed').fill('seed-one');
    await page.getByTestId('med-generate').click();
    const first = await page.getByTestId('med-indirect').textContent();
    await page.getByTestId('med-seed').fill('seed-two-different');
    await page.getByTestId('med-generate').click();
    const second = await page.getByTestId('med-indirect').textContent();
    expect(first).not.toBe(second);
  });

  test('a strong true effect (high a, high b, low noise) shows a significant badge', async ({ page }) => {
    await setSlider(page, 'med-a', 1.8);
    await setSlider(page, 'med-b', 1.8);
    await setSlider(page, 'med-noise', 0.3);
    await setSlider(page, 'med-n', 60);
    await page.getByTestId('med-generate').click();
    await expect(page.getByTestId('med-sig-badge')).toHaveClass(/sig/);
  });

  test('Explain button with no API key shows a non-empty deterministic explanation and never says "Thinking..." afterward', async ({ page }) => {
    await page.getByTestId('med-generate').click();
    await page.getByTestId('med-explain-btn').click();
    await expect(page.getByTestId('med-explanation')).not.toHaveText('Thinking...');
    const text = await page.getByTestId('med-explanation').textContent();
    expect(text.length).toBeGreaterThan(20);
  });

  test('no console errors occur during a full mediation interaction sequence', async ({ page }) => {
    const errors = [];
    page.on('pageerror', (err) => errors.push(String(err)));
    page.on('console', (msg) => { if (msg.type() === 'error') errors.push(msg.text()); });
    await page.getByTestId('med-generate').click();
    await page.getByTestId('med-explain-btn').click();
    await page.waitForTimeout(100);
    expect(errors).toEqual([]);
  });
});
