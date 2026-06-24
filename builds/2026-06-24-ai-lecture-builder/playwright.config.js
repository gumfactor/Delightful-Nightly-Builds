// @ts-check
const { defineConfig, devices } = require('@playwright/test');
const path = require('path');

module.exports = defineConfig({
  testDir: './tests',
  testMatch: '**/*.spec.js',
  timeout: 15000,
  retries: 0,
  reporter: 'list',
  use: {
    headless: true,
    launchOptions: {
      executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
      args: ['--no-sandbox', '--disable-setuid-sandbox'],
    },
    baseURL: 'file://' + path.resolve(__dirname, 'tests/fixtures'),
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
