const { defineConfig, devices } = require('@playwright/test');

module.exports = defineConfig({
  testDir: './tests',
  use: {
    headless: true,
    /* Use the pre-installed Chromium binary */
    launchOptions: {
      executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
    },
    /* Each test gets a fresh browser context with isolated localStorage */
    storageState: { cookies: [], origins: [] },
  },
  reporter: [['list']],
});
