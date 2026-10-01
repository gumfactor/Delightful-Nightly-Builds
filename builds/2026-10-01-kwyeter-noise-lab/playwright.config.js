const { defineConfig } = require('@playwright/test');

module.exports = defineConfig({
  testDir: './tests',
  timeout: 60000,
  expect: { timeout: 5000 },
  fullyParallel: false,
  retries: 0,
  reporter: [['list']],
  use: {
    browserName: 'chromium',
    headless: true,
    viewport: { width: 390, height: 844 },
    launchOptions: {
      executablePath: process.env.CHROMIUM_PATH || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
      args: ['--no-sandbox', '--disable-setuid-sandbox', '--autoplay-policy=no-user-gesture-required'],
    },
  },
});
