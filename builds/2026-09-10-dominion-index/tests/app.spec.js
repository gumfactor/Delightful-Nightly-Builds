const { test, expect } = require('@playwright/test');
const path = require('path');
const fs = require('fs');

const fixture = fs.readFileSync(path.join(__dirname, '..', 'fixtures', 'sparql-response.json'), 'utf8');
const WIKIDATA_PATTERN = /https:\/\/query\.wikidata\.org\/sparql/;
const CHARTJS_PATTERN = /cdnjs\.cloudflare\.com\/ajax\/libs\/Chart\.js/;
const chartJsSource = fs.readFileSync(
  path.join(__dirname, '..', 'node_modules', 'chart.js', 'dist', 'chart.umd.js'),
  'utf8'
);

const CORS_HEADERS = { 'Access-Control-Allow-Origin': '*' };

// This build container's sandbox has no route to the public internet (confirmed
// during this session — see BUILD_LOG.md), so the shipped Chart.js CDN URL
// (index.html) can never be reached from a test browser here. Tests stub that
// one script request with the exact same pinned version installed locally via
// npm; the shipped page itself is untouched and still loads the real CDN for
// the user, who runs it with normal internet access.
test.beforeEach(async ({ page }) => {
  await page.route(CHARTJS_PATTERN, (route) =>
    route.fulfill({ status: 200, contentType: 'application/javascript', body: chartJsSource })
  );
});

async function mockSuccess(page, body) {
  await page.route(WIKIDATA_PATTERN, (route) =>
    route.fulfill({ status: 200, contentType: 'application/sparql-results+json', headers: CORS_HEADERS, body })
  );
}

test.describe('happy path', () => {
  test('renders charts, totals, and a full table from a mocked Wikidata response', async ({ page }) => {
    await mockSuccess(page, fixture);
    await page.goto('/');
    await expect(page.locator('#dashboard')).toBeVisible();
    await expect(page.locator('#status-message')).toBeHidden();

    await expect(page.locator('#results-tbody tr')).toHaveCount(14);
    await expect(page.locator('#total-count')).toContainText('219 companies');

    const industryItems = page.locator('#industry-totals li');
    await expect(industryItems.first()).toContainText('Retail');
    await expect(industryItems.first()).toContainText('65');

    const provinceItems = page.locator('#province-totals li');
    await expect(provinceItems.first()).toContainText('Ontario');

    const hasCharts = await page.evaluate(
      () => window.DominionApp.state.industryChart !== null && window.DominionApp.state.provinceChart !== null
    );
    expect(hasCharts).toBe(true);
  });

  test('shows delta badges on a second successful fetch against the saved snapshot', async ({ page }) => {
    await mockSuccess(page, fixture);
    await page.goto('/');
    await expect(page.locator('#dashboard')).toBeVisible();

    const increasedFixture = JSON.parse(fixture);
    increasedFixture.results.bindings[0].count.value = '90'; // Retail/Ontario 40 -> 90, industry total 65 -> 115
    await page.unroute(WIKIDATA_PATTERN);
    await mockSuccess(page, JSON.stringify(increasedFixture));
    await page.reload();
    await expect(page.locator('#dashboard')).toBeVisible();

    const retailBadge = page.locator('#industry-totals li', { hasText: 'Retail' }).locator('.delta-badge');
    await expect(retailBadge).toHaveText('+50');
    await expect(retailBadge).toHaveClass(/delta-increased/);
  });
});

test.describe('failure states', () => {
  test('shows a specific message and no dashboard when Wikidata returns an empty result set', async ({ page }) => {
    await mockSuccess(page, JSON.stringify({ head: { vars: [] }, results: { bindings: [] } }));
    await page.goto('/');
    await expect(page.locator('#status-message')).toContainText('zero matching companies');
    await expect(page.locator('#dashboard')).toBeHidden();
  });

  test('shows the HTTP status and verbatim body text on a server error', async ({ page }) => {
    await page.route(WIKIDATA_PATTERN, (route) =>
      route.fulfill({
        status: 500,
        contentType: 'text/plain',
        headers: CORS_HEADERS,
        body: 'java.util.concurrent.TimeoutException',
      })
    );
    await page.goto('/');
    await expect(page.locator('#status-message')).toContainText('500');
    await expect(page.locator('#status-message')).toContainText('TimeoutException');
    await expect(page.locator('#dashboard')).toBeHidden();
  });

  test('shows a specific message on malformed JSON', async ({ page }) => {
    await mockSuccess(page, 'not valid json at all');
    await page.goto('/');
    await expect(page.locator('#status-message')).toContainText('did not return valid JSON');
  });

  test('shows CORS/network guidance when the request is aborted (simulated network failure)', async ({ page }) => {
    await page.route(WIKIDATA_PATTERN, (route) => route.abort('failed'));
    await page.goto('/');
    await expect(page.locator('#status-message')).toContainText('Could not reach the Wikidata SPARQL endpoint');
    await expect(page.locator('#status-message')).toContainText('file://');
  });
});

test.describe('CSV export', () => {
  test('downloads a CSV containing the header and every row', async ({ page }) => {
    await mockSuccess(page, fixture);
    await page.goto('/');
    await expect(page.locator('#dashboard')).toBeVisible();

    const [download] = await Promise.all([page.waitForEvent('download'), page.click('#csv-export')]);
    const downloadPath = await download.path();
    const content = fs.readFileSync(downloadPath, 'utf8');
    const lines = content.split('\r\n');
    expect(lines[0]).toBe('industry,province,count');
    expect(lines).toHaveLength(15); // header + 14 rows
    expect(content).toContain('Retail,Ontario,40');
  });
});

test.describe('security', () => {
  test('renders a hostile industry/province label as inert text, never as injected HTML', async ({ page }) => {
    const dialogs = [];
    page.on('dialog', (dialog) => {
      dialogs.push(dialog.message());
      dialog.dismiss();
    });

    const payload = JSON.parse(fixture);
    payload.results.bindings[0].industryLabel.value = '<img src=x onerror="window.__xss=true">Retail</script><script>window.__xss2=true</script>';
    await mockSuccess(page, JSON.stringify(payload));
    await page.goto('/');
    await expect(page.locator('#dashboard')).toBeVisible();

    expect(dialogs).toHaveLength(0);
    const xssFired = await page.evaluate(() => window.__xss === true || window.__xss2 === true);
    expect(xssFired).toBe(false);

    const imgCount = await page.locator('#results-tbody img').count();
    expect(imgCount).toBe(0);

    const cellText = await page.locator('#results-tbody tr').first().locator('td').first().textContent();
    expect(cellText).toContain('<img');
  });
});

test.describe('theme', () => {
  test('toggles between dark and light and persists the choice', async ({ page }) => {
    await mockSuccess(page, fixture);
    await page.goto('/');
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');

    await page.click('#theme-toggle');
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'light');

    await page.reload();
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'light');
  });
});

test.describe('mobile viewport', () => {
  test('does not overflow horizontally on a narrow screen', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await mockSuccess(page, fixture);
    await page.goto('/');
    await expect(page.locator('#dashboard')).toBeVisible();
    const { scrollWidth, clientWidth } = await page.evaluate(() => ({
      scrollWidth: document.documentElement.scrollWidth,
      clientWidth: document.documentElement.clientWidth,
    }));
    expect(scrollWidth).toBeLessThanOrEqual(clientWidth + 1);
  });
});

test.describe('table interactions', () => {
  test('filters rows by typed text', async ({ page }) => {
    await mockSuccess(page, fixture);
    await page.goto('/');
    await expect(page.locator('#dashboard')).toBeVisible();

    await page.fill('#table-filter', 'retail');
    await expect(page.locator('#results-tbody tr')).toHaveCount(3);
  });

  test('sorts by count ascending then descending on repeated header click', async ({ page }) => {
    await mockSuccess(page, fixture);
    await page.goto('/');
    await expect(page.locator('#dashboard')).toBeVisible();

    // Default render is already sorted by count descending — max count (40) leads.
    const firstRowDefault = await page.locator('#results-tbody tr').first().locator('td').nth(2).textContent();
    expect(firstRowDefault).toBe('40');

    // Clicking the already-active sort column flips the direction to ascending.
    await page.click('th[data-sort-key="count"]');
    const firstRowAsc = await page.locator('#results-tbody tr').first().locator('td').nth(2).textContent();
    expect(firstRowAsc).toBe('3');

    // Clicking again flips back to descending.
    await page.click('th[data-sort-key="count"]');
    const firstRowDesc = await page.locator('#results-tbody tr').first().locator('td').nth(2).textContent();
    expect(firstRowDesc).toBe('40');
  });
});
