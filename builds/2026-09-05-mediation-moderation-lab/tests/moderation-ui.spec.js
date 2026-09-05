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

async function goToModerationTab(page) {
  await page.getByTestId('tab-moderation').click();
}

test.beforeEach(async ({ page }) => {
  await page.goto(INDEX_URL);
});

test.describe('Moderation Lab UI', () => {
  test('tab switches from Mediation to Moderation panel', async ({ page }) => {
    await expect(page.getByTestId('panel-mediation')).toBeVisible();
    await goToModerationTab(page);
    await expect(page.getByTestId('panel-moderation')).toBeVisible();
    await expect(page.getByTestId('panel-mediation')).toBeHidden();
  });

  test('moving the interaction slider updates its displayed value', async ({ page }) => {
    await goToModerationTab(page);
    // 0.30 is a step-aligned value for min=-1, step=0.02 (range inputs snap
    // to the nearest step when their value is set programmatically).
    await setSlider(page, 'mod-b3', 0.30);
    await expect(page.getByTestId('mod-b3-val')).toHaveText('0.30');
  });

  test('Generate Sample populates the simple-slopes table with 3 rows', async ({ page }) => {
    await goToModerationTab(page);
    await page.getByTestId('mod-generate').click();
    await expect(page.getByTestId('mod-results')).toBeVisible();
    const rows = page.locator('[data-testid="mod-simple-slopes"] tbody tr');
    await expect(rows).toHaveCount(3);
    const labels = await rows.allTextContents();
    expect(labels[0]).toContain('-1 SD');
    expect(labels[1]).toContain('Mean');
    expect(labels[2]).toContain('+1 SD');
  });

  test('Johnson-Neyman region text is populated after generating a sample', async ({ page }) => {
    await goToModerationTab(page);
    await page.getByTestId('mod-generate').click();
    const text = await page.getByTestId('mod-jn-region').textContent();
    expect(text.trim().length).toBeGreaterThan(0);
  });

  test('a strong interaction (high b3, low noise) shows a significant interaction badge', async ({ page }) => {
    await goToModerationTab(page);
    await setSlider(page, 'mod-b3', 0.9);
    await setSlider(page, 'mod-noise', 0.3);
    await setSlider(page, 'mod-n', 60);
    await page.getByTestId('mod-generate').click();
    await expect(page.getByTestId('mod-sig-badge')).toHaveClass(/sig/);
  });

  test('a near-zero interaction with high noise shows a non-significant badge', async ({ page }) => {
    await goToModerationTab(page);
    await setSlider(page, 'mod-b3', 0.0);
    await setSlider(page, 'mod-noise', 5.0);
    await setSlider(page, 'mod-n', 30);
    await page.getByTestId('mod-seed').fill('flat-interaction-seed');
    await page.getByTestId('mod-generate').click();
    await expect(page.getByTestId('mod-sig-badge')).toHaveClass(/nonsig/);
  });

  test('no horizontal overflow at a 375px mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 800 });
    await goToModerationTab(page);
    await page.getByTestId('mod-generate').click();
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    expect(overflow).toBeLessThanOrEqual(1);
  });

  test('no console errors occur while generating and switching tabs repeatedly', async ({ page }) => {
    const errors = [];
    page.on('pageerror', (err) => errors.push(String(err)));
    page.on('console', (msg) => { if (msg.type() === 'error') errors.push(msg.text()); });
    await goToModerationTab(page);
    await page.getByTestId('mod-generate').click();
    await page.getByTestId('tab-mediation').click();
    await page.getByTestId('med-generate').click();
    await page.getByTestId('tab-moderation').click();
    await page.waitForTimeout(100);
    expect(errors).toEqual([]);
  });
});
