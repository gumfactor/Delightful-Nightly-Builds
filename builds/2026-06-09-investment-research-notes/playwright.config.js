const fs = require('fs');
const { defineConfig } = require('@playwright/test');

const bundledChromium = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';
const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH || (fs.existsSync(bundledChromium) ? bundledChromium : undefined);

module.exports = defineConfig({
  testDir: './tests',
  use: {
    headless: true,
    /* Use bundled Chromium in CI when available, otherwise fall back to Playwright defaults */
    launchOptions: executablePath ? { executablePath } : {},
    /* Each test gets a fresh browser context with isolated localStorage */
    storageState: { cookies: [], origins: [] },
  },
  reporter: [['list']],
});
