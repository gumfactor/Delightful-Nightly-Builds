const { test, expect } = require('@playwright/test');
const path = require('path');

const INDEX_URL = `file://${path.resolve(__dirname, '../index.html')}`;
const HOSTILE_LABEL = '<img src=x onerror="window.__xssFired = true">';

test.describe('Security', () => {
  test('a hostile label in search results renders as inert text, never executes', async ({ page }) => {
    await page.route('**/w/api.php**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ search: [{ id: 'Q666', label: HOSTILE_LABEL, description: '' }] }),
      });
    });
    await page.goto(INDEX_URL);
    await page.getByTestId('search-input').fill('anything');
    await expect(page.getByTestId('search-result')).toBeVisible();

    const fired = await page.evaluate(() => window.__xssFired);
    expect(fired).toBeUndefined();

    // The literal markup must appear as visible text, not be parsed as an <img> tag.
    await expect(page.getByTestId('search-result')).toContainText('<img src=x onerror=');
    const imgCount = await page.locator('[data-testid="search-result"] img').count();
    expect(imgCount).toBe(0);
  });

  test('a hostile label reaching the ownership chain renders as inert text, never executes', async ({ page }) => {
    await page.route('**/w/api.php**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ search: [{ id: 'Q1', label: 'Acme Retail', description: '' }] }),
      });
    });
    await page.route('**/sparql**', async (route) => {
      const rawQuery = decodeURIComponent(new URL(route.request().url()).searchParams.get('query') || '');
      if (rawQuery.includes('P355')) {
        await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ results: { bindings: [] } }) });
        return;
      }
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          results: {
            bindings: [
              {
                prop: { value: 'http://www.wikidata.org/prop/direct/P127' },
                parent: { value: 'http://www.wikidata.org/entity/Q666' },
                parentLabel: { value: HOSTILE_LABEL },
              },
            ],
          },
        }),
      });
    });

    await page.goto(INDEX_URL);
    await page.getByTestId('search-input').fill('acme');
    await page.getByTestId('search-result').first().click();
    await expect(page.getByTestId('chain-node')).toBeVisible();

    const fired = await page.evaluate(() => window.__xssFired);
    expect(fired).toBeUndefined();
    const imgCount = await page.locator('[data-testid="chain-node"] img').count();
    expect(imgCount).toBe(0);
  });

  test('a search query with reserved URL characters is correctly percent-encoded', async ({ page }) => {
    let capturedUrl = null;
    await page.route('**/w/api.php**', async (route) => {
      capturedUrl = route.request().url();
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ search: [] }) });
    });
    await page.goto(INDEX_URL);
    await page.getByTestId('search-input').fill('AT&T / Co?');
    await expect.poll(() => capturedUrl).not.toBeNull();

    const url = new URL(capturedUrl);
    // Round-tripping through a standard URL parser must recover the exact
    // original string — this is only possible if '&', '/', and '?' inside
    // the value were percent-encoded rather than left as literal separators.
    expect(url.searchParams.get('search')).toBe('AT&T / Co?');
    expect(Array.from(url.searchParams.keys())).toEqual(['action', 'search', 'language', 'type', 'format', 'limit', 'origin']);
  });

  test('a malformed API response is caught gracefully, never an unhandled page error', async ({ page }) => {
    const pageErrors = [];
    page.on('pageerror', (err) => pageErrors.push(err));

    await page.route('**/w/api.php**', async (route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ search: [{ id: 'Q1', label: 'Acme Retail', description: '' }] }) });
    });
    await page.route('**/sparql**', async (route) => {
      await route.fulfill({ status: 200, contentType: 'text/html', body: 'not valid json' });
    });

    await page.goto(INDEX_URL);
    await page.getByTestId('search-input').fill('acme');
    await page.getByTestId('search-result').first().click();
    await expect(page.getByTestId('error-banner')).toBeVisible();
    await expect(page.getByTestId('error-message')).toContainText('unreadable');
    expect(pageErrors).toHaveLength(0);
  });
});
