const { defineConfig } = require('@playwright/test');

module.exports = defineConfig({
  testDir: './tests',
  timeout: 20000,
  expect: { timeout: 5000 },
  fullyParallel: false,
  retries: 0,
  reporter: [['list']],
  webServer: {
    command: 'python3 -m http.server 4173',
    port: 4173,
    reuseExistingServer: false,
    cwd: __dirname,
  },
  use: {
    baseURL: 'http://localhost:4173',
    browserName: 'chromium',
    headless: true,
    viewport: { width: 1280, height: 800 },
    launchOptions: {
      executablePath: '/opt/pw-browsers/chromium',
      args: ['--no-sandbox', '--disable-setuid-sandbox'],
    },
  },
});
