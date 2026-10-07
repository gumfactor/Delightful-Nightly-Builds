const { test, expect } = require('@playwright/test');
const { execFileSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const root = path.resolve(__dirname, '..');
const chartJs = fs.readFileSync(path.join(root, 'node_modules/chart.js/dist/chart.umd.js'), 'utf8');
const out = path.join(root, 'test-results', 'ui-dashboard.html');

test.beforeAll(() => {
  fs.mkdirSync(path.dirname(out), { recursive: true });
  execFileSync('python3', [path.join(root, 'src/main.py'), '--offline', '--no-ai', '--out', out]);
});

async function open(page, { block = false } = {}) {
  // Serve pinned Chart.js locally so tests never touch the network.
  await page.route('**/chart.js@4.4.4/**', (route) =>
    block ? route.abort() : route.fulfill({ contentType: 'application/javascript', body: chartJs }));
  await page.goto('file://' + out);
}

test('renders a card for every indicator and derived series', async ({ page }) => {
  await open(page);
  for (const id of ['cpi', 'policy_rate', 'usdcad', 'unemployment', 'gdp', 'real_rate', 'curve']) {
    await expect(page.getByTestId('card-' + id)).toBeVisible();
  }
});

test('sample data shows the illustrative banner', async ({ page }) => {
  await open(page);
  await expect(page.getByTestId('sample-banner')).toBeVisible();
});

test('clicking a card opens the detail chart with facts', async ({ page }) => {
  await open(page);
  await expect(page.getByTestId('detail')).toBeHidden();
  await page.getByTestId('card-unemployment').click();
  await expect(page.getByTestId('detail')).toBeVisible();
  await expect(page.getByTestId('fact-trend')).toHaveText(/rising|falling|flat/);
  await expect(page.getByTestId('main-chart')).toHaveAttribute('data-series', '1');
});

test('range buttons change how many points are plotted', async ({ page }) => {
  await open(page);
  await page.getByTestId('card-cpi').click();
  await page.getByTestId('range-1Y').click();
  const oneYear = Number(await page.getByTestId('main-chart').getAttribute('data-points'));
  await page.getByTestId('range-Max').click();
  const max = Number(await page.getByTestId('main-chart').getAttribute('data-points'));
  expect(oneYear).toBeGreaterThan(5);
  expect(max).toBeGreaterThan(oneYear * 5);
});

test('compare mode plots two rebased series', async ({ page }) => {
  await open(page);
  await page.getByTestId('card-usdcad').click();
  await page.getByTestId('compare').selectOption('cpi');
  await expect(page.getByTestId('main-chart')).toHaveAttribute('data-series', '2');
});

test('theme toggle switches data-theme', async ({ page }) => {
  await open(page);
  await page.getByTestId('theme-toggle').click();
  await expect(page.locator('html')).toHaveAttribute('data-theme', /dark|light/);
});

test('page degrades gracefully when Chart.js cannot load', async ({ page }) => {
  await open(page, { block: true });
  await page.getByTestId('card-cpi').click();
  await expect(page.getByTestId('fact-latest')).not.toBeEmpty();
  await expect(page.locator('#note')).toContainText('Chart library unavailable');
});

test('failed indicator renders an error card, others still render', async ({ page }) => {
  const html = fs.readFileSync(out, 'utf8').replace('"failed":[]',
    '"failed":[{"id":"retail_x","label":"Retail sales","group":"Output","error":"HTTP 403"}]');
  const broken = path.join(root, 'test-results', 'ui-broken.html');
  fs.writeFileSync(broken, html);
  await page.route('**/chart.js@4.4.4/**', (r) => r.fulfill({ contentType: 'application/javascript', body: chartJs }));
  await page.goto('file://' + broken);
  await expect(page.getByTestId('error-retail_x')).toContainText('HTTP 403');
  await expect(page.getByTestId('card-cpi')).toBeVisible();
});
