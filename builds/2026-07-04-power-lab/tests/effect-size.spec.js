const { test, expect } = require('@playwright/test');
const path = require('path');

test.beforeEach(async ({ page }) => {
  const filePath = path.join(__dirname, '..', 'index.html');
  await page.goto(`file://${filePath}`);
  await page.getByTestId('tab-btn-effect-size').click();
});

test.describe('Effect Size Converter tab', () => {
  test('d to r conversion matches the expected value at d=0.5', async ({ page }) => {
    await page.getByTestId('conversion-direction').selectOption('d-to-r');
    await page.getByTestId('es-primary-input').fill('0.5');
    await expect(page.getByTestId('effect-size-result')).toContainText('r = 0.243');
  });

  test('r to d is the inverse of d to r within tolerance', async ({ page }) => {
    await page.getByTestId('conversion-direction').selectOption('d-to-r');
    await page.getByTestId('es-primary-input').fill('0.6');
    const resultText = await page.getByTestId('effect-size-result').textContent();
    const r = resultText.match(/r = ([\d.]+)/)[1];

    await page.getByTestId('conversion-direction').selectOption('r-to-d');
    await page.getByTestId('es-primary-input').fill(r);
    const backResult = await page.getByTestId('effect-size-result').textContent();
    const d = parseFloat(backResult.match(/d = ([\d.]+)/)[1]);
    expect(d).toBeCloseTo(0.6, 1);
  });

  test('t to d conversion matches a hand-computed value', async ({ page }) => {
    await page.getByTestId('conversion-direction').selectOption('t-to-d');
    await page.getByTestId('es-t-input').fill('2.0');
    await page.getByTestId('es-n-input').fill('30');
    await page.getByTestId('es-test-type-input').selectOption('two-sample');
    // d = t * sqrt(2/n) = 2.0 * sqrt(2/30) = 0.5164
    await expect(page.getByTestId('effect-size-result')).toContainText('d = 0.516');
  });

  test('switching conversion direction updates which inputs are visible', async ({ page }) => {
    await page.getByTestId('conversion-direction').selectOption('t-to-d');
    await expect(page.getByTestId('es-t-input')).toBeVisible();
    await expect(page.getByTestId('es-primary-input')).toBeHidden();

    await page.getByTestId('conversion-direction').selectOption('d-to-r');
    await expect(page.getByTestId('es-primary-input')).toBeVisible();
    await expect(page.getByTestId('es-t-input')).toBeHidden();
  });

  test('out-of-range r shows a validation message', async ({ page }) => {
    await page.getByTestId('conversion-direction').selectOption('r-to-d');
    await page.getByTestId('es-primary-input').fill('1.5');
    await expect(page.getByTestId('effect-size-error')).toContainText('must satisfy');
  });
});
