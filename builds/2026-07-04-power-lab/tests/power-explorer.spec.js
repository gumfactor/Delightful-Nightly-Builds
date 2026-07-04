const { test, expect } = require('@playwright/test');
const path = require('path');

test.beforeEach(async ({ page }) => {
  const filePath = path.join(__dirname, '..', 'index.html');
  await page.goto(`file://${filePath}`);
});

test.describe('Power Explorer tab', () => {
  test('loads with the Power Explorer tab active by default', async ({ page }) => {
    await expect(page.getByTestId('tab-btn-explorer')).toHaveClass(/active/);
    await expect(page.getByTestId('panel-explorer')).toHaveClass(/active/);
    await expect(page.getByTestId('panel-sample-size')).not.toHaveClass(/active/);
  });

  test('shows the default classic-benchmark power reading on load', async ({ page }) => {
    const readout = page.getByTestId('power-readout');
    await expect(readout).toHaveText(/80\.\d%/);
  });

  test('moving the effect-size number input changes the displayed power', async ({ page }) => {
    const readoutBefore = await page.getByTestId('power-readout').textContent();
    await page.getByTestId('d-number').fill('1.5');
    await page.getByTestId('d-number').dispatchEvent('input');
    const readoutAfter = await page.getByTestId('power-readout').textContent();
    expect(readoutAfter).not.toBe(readoutBefore);
    expect(parseFloat(readoutAfter)).toBeGreaterThan(parseFloat(readoutBefore));
  });

  test('moving the N number input changes the displayed power', async ({ page }) => {
    await page.getByTestId('n-number').fill('10');
    await page.getByTestId('n-number').dispatchEvent('input');
    const lowN = parseFloat(await page.getByTestId('power-readout').textContent());

    await page.getByTestId('n-number').fill('400');
    await page.getByTestId('n-number').dispatchEvent('input');
    const highN = parseFloat(await page.getByTestId('power-readout').textContent());

    expect(highN).toBeGreaterThan(lowN);
  });

  test('switching design type changes the computed power for the same d and n', async ({ page }) => {
    const twoSamplePower = await page.getByTestId('power-readout').textContent();
    await page.getByTestId('test-type-select').selectOption('one-sample');
    const oneSamplePower = await page.getByTestId('power-readout').textContent();
    expect(oneSamplePower).not.toBe(twoSamplePower);
    expect(parseFloat(oneSamplePower)).toBeGreaterThan(parseFloat(twoSamplePower));
  });

  test('both charts render with non-empty canvases', async ({ page }) => {
    const distCanvas = page.getByTestId('distribution-chart');
    const curveCanvas = page.getByTestId('power-curve-chart');
    await expect(distCanvas).toBeVisible();
    await expect(curveCanvas).toBeVisible();

    const dims = await page.evaluate(() => {
      const d = document.querySelector('[data-testid="distribution-chart"]');
      const c = document.querySelector('[data-testid="power-curve-chart"]');
      return { d: [d.width, d.height], c: [c.width, c.height] };
    });
    expect(dims.d[0]).toBeGreaterThan(0);
    expect(dims.c[0]).toBeGreaterThan(0);
  });

  test('changing alpha shifts the computed power', async ({ page }) => {
    const at05 = await page.getByTestId('power-readout').textContent();
    await page.getByTestId('alpha-select').selectOption('0.10');
    const at10 = await page.getByTestId('power-readout').textContent();
    expect(parseFloat(at10)).toBeGreaterThan(parseFloat(at05));
  });

  test('the qualitative power label updates across the low/medium/high power range', async ({ page }) => {
    await page.getByTestId('n-number').fill('5');
    await page.getByTestId('n-number').dispatchEvent('input');
    await page.getByTestId('d-number').fill('0.1');
    await page.getByTestId('d-number').dispatchEvent('input');
    await expect(page.getByTestId('power-label')).toHaveText('severely underpowered');

    await page.getByTestId('n-number').fill('800');
    await page.getByTestId('n-number').dispatchEvent('input');
    await page.getByTestId('d-number').fill('1.5');
    await page.getByTestId('d-number').dispatchEvent('input');
    await expect(page.getByTestId('power-label')).toHaveText('well-powered');
  });
});
