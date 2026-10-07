const { defineConfig } = require('@playwright/test');
module.exports = defineConfig({
  testDir: './tests',
  testMatch: '*.spec.js',
  use: { launchOptions: { executablePath: process.env.CHROMIUM_PATH || undefined } },
});
