const { defineConfig } = require("@playwright/test");

const PORT = 4761;

module.exports = defineConfig({
  testDir: "./tests",
  timeout: 20000,
  expect: { timeout: 5000 },
  fullyParallel: false,
  retries: 0,
  reporter: [["list"]],
  use: {
    baseURL: `http://127.0.0.1:${PORT}`,
    browserName: "chromium",
    headless: true,
    viewport: { width: 1280, height: 900 },
    launchOptions: {
      executablePath: "/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
      args: ["--no-sandbox", "--disable-setuid-sandbox"]
    }
  },
  webServer: {
    command: "node test-server.js",
    port: PORT,
    reuseExistingServer: false,
    timeout: 10000
  }
});
