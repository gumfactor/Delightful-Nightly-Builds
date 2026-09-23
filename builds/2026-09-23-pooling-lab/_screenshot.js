/*
 * Manual QA helper — not part of the shipped app or the automated test suite.
 * Takes a full-page screenshot of index.html and reports any console/page
 * errors, for eyeballing layout/theme issues that Playwright's DOM
 * assertions don't catch. Run with: node _screenshot.js
 */
const { chromium } = require('@playwright/test');
const path = require('path');

(async () => {
  const browser = await chromium.launch({
    executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
    args: ['--no-sandbox'],
  });
  const page = await browser.newPage({ viewport: { width: 1200, height: 1400 } });
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  page.on('console', (m) => {
    if (m.type() === 'error') errors.push(m.text());
  });
  await page.goto('file://' + path.join(__dirname, 'index.html'));
  await page.waitForTimeout(300);
  await page.screenshot({ path: path.join(__dirname, 'qa-screenshot.png'), fullPage: true });
  console.log('errors:', errors);
  await browser.close();
})();
