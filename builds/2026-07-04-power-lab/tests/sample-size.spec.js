const { test, expect } = require('@playwright/test');
const path = require('path');

test.beforeEach(async ({ page }) => {
  const filePath = path.join(__dirname, '..', 'index.html');
  await page.goto(`file://${filePath}`);
  await page.getByTestId('tab-btn-sample-size').click();
});

test.describe('Sample Size Calculator tab', () => {
  test('default inputs render a required-N result', async ({ page }) => {
    await expect(page.getByTestId('sample-size-result')).toContainText(/Required sample size: N = \d+/);
  });

  test('increasing target power increases the required N', async ({ page }) => {
    await page.getByTestId('ss-power').fill('0.5');
    const nLowPower = await page.getByTestId('sample-size-result').textContent();

    await page.getByTestId('ss-power').fill('0.95');
    const nHighPower = await page.getByTestId('sample-size-result').textContent();

    const extract = (text) => parseInt(text.match(/N = (\d+)/)[1], 10);
    expect(extract(nHighPower)).toBeGreaterThan(extract(nLowPower));
  });

  test('decreasing effect size increases the required N', async ({ page }) => {
    await page.getByTestId('ss-d').fill('0.8');
    const nLargeEffect = await page.getByTestId('sample-size-result').textContent();

    await page.getByTestId('ss-d').fill('0.2');
    const nSmallEffect = await page.getByTestId('sample-size-result').textContent();

    const extract = (text) => parseInt(text.match(/N = (\d+)/)[1], 10);
    expect(extract(nSmallEffect)).toBeGreaterThan(extract(nLargeEffect));
  });

  test('the copy summary sentence contains the computed N and effect size', async ({ page }) => {
    await page.getByTestId('ss-d').fill('0.4');
    await page.getByTestId('ss-power').fill('0.8');
    const resultText = await page.getByTestId('sample-size-result').textContent();
    const n = resultText.match(/N = (\d+)/)[1];
    expect(resultText).toContain(`d = 0.4`);
    expect(resultText).toContain(`N = ${n}`);
  });

  test('invalid target power shows a validation message instead of a bogus result', async ({ page }) => {
    await page.getByTestId('ss-power').fill('1.5');
    await expect(page.getByTestId('sample-size-error')).toContainText('between 0 and 1');
    await expect(page.getByTestId('sample-size-result')).toHaveText('');
  });
});
