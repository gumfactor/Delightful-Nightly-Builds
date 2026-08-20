const { defineConfig } = require('@playwright/test');

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
    viewport: { width: 1280, height: 720 },
    launchOptions: {
      executablePath: '/opt/pw-browsers/chromium',
      args: ['--no-sandbox', '--disable-setuid-sandbox'],
    },
  },
});
