const { test, expect } = require('@playwright/test');
const path = require('path');

const APP_URL = 'file://' + path.join(__dirname, '..', 'index.html');

test.describe('Multicollinearity Lab tab', () => {
  test('starts at correlation 0.00 with a moderate VIF', async ({ page }) => {
    await page.goto(APP_URL);
    await page.click('[data-testid=tab-multicollinearity]');
    await expect(page.locator('[data-testid=corr-value]')).toHaveText('0.00');
    const vifText = await page.textContent('[data-testid=mc-vif]');
    expect(parseFloat(vifText)).toBeLessThan(2);
  });

  test('raising the correlation slider inflates VIF and both coefficient SEs sharply, while R2 stays roughly flat', async ({ page }) => {
    await page.goto(APP_URL);
    await page.click('[data-testid=tab-multicollinearity]');

    const r2Before = parseFloat(await page.textContent('[data-testid=mc-r2]'));
    const se1Before = parseFloat(await page.textContent('[data-testid=mc-se1]'));

    const slider = page.locator('[data-testid=corr-slider]');
    await slider.fill('97');
    await slider.dispatchEvent('input');

    await expect(page.locator('[data-testid=corr-value]')).toHaveText('0.97');
    const vifAfter = parseFloat(await page.textContent('[data-testid=mc-vif]'));
    const r2After = parseFloat(await page.textContent('[data-testid=mc-r2]'));
    const se1After = parseFloat(await page.textContent('[data-testid=mc-se1]'));

    expect(vifAfter).toBeGreaterThan(10);
    expect(se1After).toBeGreaterThan(se1Before * 2);
    expect(Math.abs(r2After - r2Before)).toBeLessThan(0.15);
  });
});
