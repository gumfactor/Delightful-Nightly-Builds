const { test, expect } = require('@playwright/test');
const path = require('path');

test('home screen loads with zero console/page errors', async ({ page }) => {
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e)));
  page.on('console', (msg) => {
    if (msg.type() === 'error') errors.push(msg.text());
  });
  await page.goto('file://' + path.join(__dirname, '..', 'index.html'));
  await expect(page.getByTestId('btn-tutorial')).toBeVisible();
  expect(errors).toEqual([]);
});
