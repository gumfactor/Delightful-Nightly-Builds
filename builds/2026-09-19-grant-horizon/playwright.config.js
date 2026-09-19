// @ts-check
const { defineConfig } = require('@playwright/test');

module.exports = defineConfig({
  testDir: './tests',
  testMatch: '*.spec.js',
  timeout: 30000,
  fullyParallel: true,
  reporter: 'list',
  globalSetup: require.resolve('./tests/global-setup.js'),
  use: {
    // Pinned to the chromium build actually installed in this environment.
    // The globally installed Playwright (1.56.1) defaults to a browser
    // build id this container doesn't have on disk -- the same fix prior
    // browser builds in this catalog needed (see Regex Dojo, 2026-06-18,
    // and Secrets Sentinel, 2026-09-08, BUILD_LOG.md entries).
    launchOptions: {
      executablePath:
        process.env.PLAYWRIGHT_CHROMIUM_PATH ||
        '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
    },
  },
});
