const { defineConfig } = require('@playwright/test');
const fs = require('fs');

const bundled = '/opt/pw-browsers/chromium';
module.exports = defineConfig({
  testDir: './tests',
  fullyParallel: true,
  reporter: 'list',
  use: {
    launchOptions: fs.existsSync(bundled) ? { executablePath: bundled } : {},
  },
});
