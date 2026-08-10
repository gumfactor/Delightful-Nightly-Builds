const { defineConfig } = require('@playwright/test');
const fs = require('fs');

// This build's dev/CI container ships a pinned Chromium at a fixed path
// with no sandbox available. On a contributor's own machine that path
// won't exist, so fall back to Playwright's normal browser resolution
// (its own downloaded/managed Chromium) instead of failing outright.
const PINNED_CHROMIUM = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';
const launchOptions = fs.existsSync(PINNED_CHROMIUM)
  ? { executablePath: PINNED_CHROMIUM, args: ['--no-sandbox', '--disable-setuid-sandbox'] }
  : {};

module.exports = defineConfig({
  testDir: './tests',
  timeout: 15000,
  expect: { timeout: 5000 },
  fullyParallel: false,
  retries: 0,
  reporter: [['list']],
  use: {
    browserName: 'chromium',
    headless: true,
    viewport: { width: 1280, height: 800 },
    acceptDownloads: true,
    launchOptions,
  },
});
