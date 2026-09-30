// UI smoke tests. Starts the real server against the bundled example transcripts.
const { defineConfig } = require("playwright/test");

module.exports = defineConfig({
  testDir: "./tests",
  testMatch: "*.spec.js",
  use: { baseURL: "http://127.0.0.1:8792", launchOptions: { executablePath: process.env.CHROMIUM_PATH || undefined } },
  webServer: {
    command: "python -m sessionmemory --db .ui-test.db serve --demo --port 8792",
    env: { PYTHONPATH: "src" },
    url: "http://127.0.0.1:8792/api/status",
    reuseExistingServer: false,
    timeout: 15000,
  },
});
