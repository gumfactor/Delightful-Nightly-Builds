const { test, expect } = require('@playwright/test');
const path = require('path');

const INDEX_URL = `file://${path.resolve(__dirname, '../index.html')}`;

const SEARCH_FIXTURES = {
  acme: [{ id: 'Q1', label: 'Acme Retail', description: 'Retail company' }],
  standalone: [{ id: 'Q5', label: 'Standalone Co', description: '' }],
  errorco: [{ id: 'Q9', label: 'Error Co', description: '' }],
};

const PARENT_FIXTURES = {
  Q1: [{ prop: 'P127', id: 'Q2', label: 'Acme Holdings', pointInTime: '2020-00-00T00:00:00Z' }],
  Q2: [{ prop: 'P749', id: 'Q3', label: 'Global Corp' }],
  Q3: [],
  Q4: [],
  Q5: [],
};

const SUBSIDIARY_FIXTURES = {
  Q1: [{ prop: 'P355', id: 'Q4', label: 'Acme Logistics' }],
  Q2: [],
  Q3: [],
  Q4: [],
  Q5: [],
};

function sparqlBindings(rows, kind) {
  return {
    results: {
      bindings: rows.map((row) => {
        const idKey = kind === 'parents' ? 'parent' : 'sub';
        const labelKey = kind === 'parents' ? 'parentLabel' : 'subLabel';
        const binding = {
          prop: { value: `http://www.wikidata.org/prop/direct/${row.prop}` },
          [idKey]: { value: `http://www.wikidata.org/entity/${row.id}` },
          [labelKey]: { value: row.label },
        };
        if (row.pointInTime) binding.pointInTime = { value: row.pointInTime };
        return binding;
      }),
    },
  };
}

async function mockWikidata(page, { errorFor } = {}) {
  await page.route('**/w/api.php**', async (route) => {
    const url = new URL(route.request().url());
    const q = (url.searchParams.get('search') || '').toLowerCase();
    const key = Object.keys(SEARCH_FIXTURES).find((k) => q.includes(k));
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ search: key ? SEARCH_FIXTURES[key] : [] }) });
  });

  await page.route('**/sparql**', async (route) => {
    const url = new URL(route.request().url());
    const rawQuery = decodeURIComponent(url.searchParams.get('query') || '');
    const idMatch = rawQuery.match(/wd:(Q\d+)/);
    const id = idMatch ? idMatch[1] : null;

    if (errorFor && id === errorFor) {
      await route.fulfill({ status: 500, contentType: 'application/json', body: '{}' });
      return;
    }

    const isSubsidiaryQuery = rawQuery.includes('P355');
    const fixtureSet = isSubsidiaryQuery ? SUBSIDIARY_FIXTURES : PARENT_FIXTURES;
    const rows = (id && fixtureSet[id]) || [];
    const body = sparqlBindings(rows, isSubsidiaryQuery ? 'subs' : 'parents');
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) });
  });
}

test.describe('Corporate Ownership Chain Explorer — UI', () => {
  // Each test runs in a fresh, isolated browser context (Playwright's
  // default), so localStorage starts empty per test with no manual reset
  // needed — and no reset that would also (wrongly) fire on page.reload().

  test('initial state shows the empty-state placeholder and no open dropdown', async ({ page }) => {
    await mockWikidata(page);
    await page.goto(INDEX_URL);
    await expect(page.getByTestId('focus-panel')).toContainText('Search for a company');
    await expect(page.getByTestId('search-results')).toBeHidden();
    await expect(page.getByTestId('breadcrumb')).toBeEmpty();
  });

  test('typing a query renders a debounced dropdown of search results', async ({ page }) => {
    await mockWikidata(page);
    await page.goto(INDEX_URL);
    await page.getByTestId('search-input').fill('acme');
    await expect(page.getByTestId('search-results')).toBeVisible();
    await expect(page.getByTestId('search-result')).toHaveText(/Acme Retail/);
  });

  test('selecting a search result populates the focus panel', async ({ page }) => {
    await mockWikidata(page);
    await page.goto(INDEX_URL);
    await page.getByTestId('search-input').fill('acme');
    await page.getByTestId('search-result').first().click();
    await expect(page.getByTestId('focus-label')).toHaveText('Acme Retail');
    await expect(page.getByTestId('focus-qid-link')).toHaveAttribute('href', 'https://www.wikidata.org/wiki/Q1');
  });

  test('the parent ownership chain renders in order with a working citation link', async ({ page }) => {
    await mockWikidata(page);
    await page.goto(INDEX_URL);
    await page.getByTestId('search-input').fill('acme');
    await page.getByTestId('search-result').first().click();
    const nodes = page.getByTestId('parent-chain').getByTestId('chain-node');
    await expect(nodes).toHaveCount(2);
    await expect(nodes.nth(0)).toContainText('Acme Holdings');
    await expect(nodes.nth(0)).toContainText('as of 2020');
    await expect(nodes.nth(1)).toContainText('Global Corp');
    await expect(nodes.nth(0).getByTestId('citation-link')).toHaveAttribute('href', 'https://www.wikidata.org/wiki/Q2#P127');
  });

  test('clicking a subsidiary drills down and updates the breadcrumb', async ({ page }) => {
    await mockWikidata(page);
    await page.goto(INDEX_URL);
    await page.getByTestId('search-input').fill('acme');
    await page.getByTestId('search-result').first().click();
    await expect(page.getByTestId('subsidiaries').getByTestId('chain-node-button')).toHaveText('Acme Logistics');
    await page.getByTestId('subsidiaries').getByTestId('chain-node-button').click();
    await expect(page.getByTestId('focus-label')).toHaveText('Acme Logistics');
    await expect(page.getByTestId('breadcrumb-item')).toHaveCount(2);
  });

  test('clicking an earlier breadcrumb entry jumps back without duplicating history', async ({ page }) => {
    await mockWikidata(page);
    await page.goto(INDEX_URL);
    await page.getByTestId('search-input').fill('acme');
    await page.getByTestId('search-result').first().click();
    await page.getByTestId('subsidiaries').getByTestId('chain-node-button').click();
    await expect(page.getByTestId('focus-label')).toHaveText('Acme Logistics');

    await page.getByTestId('breadcrumb-item').first().click();
    await expect(page.getByTestId('focus-label')).toHaveText('Acme Retail');
    await expect(page.getByTestId('breadcrumb-item')).toHaveCount(1);
  });

  test('a company with no recorded ownership data shows explicit empty-state text', async ({ page }) => {
    await mockWikidata(page);
    await page.goto(INDEX_URL);
    await page.getByTestId('search-input').fill('standalone');
    await page.getByTestId('search-result').first().click();
    await expect(page.getByTestId('parent-chain-empty')).toBeVisible();
    await expect(page.getByTestId('subsidiaries-empty')).toBeVisible();
  });

  test('a failed ownership request shows an error banner and leaves the UI usable', async ({ page }) => {
    await mockWikidata(page, { errorFor: 'Q9' });
    await page.goto(INDEX_URL);
    await page.getByTestId('search-input').fill('errorco');
    await page.getByTestId('search-result').first().click();
    await expect(page.getByTestId('error-banner')).toBeVisible();
    await expect(page.getByTestId('error-message')).toContainText('status 500');

    // UI must still be usable after the error.
    await page.getByTestId('search-input').fill('acme');
    await expect(page.getByTestId('search-results')).toBeVisible();
  });

  test('recent searches persist to localStorage and re-render after reload', async ({ page }) => {
    await mockWikidata(page);
    await page.goto(INDEX_URL);
    await page.getByTestId('search-input').fill('acme');
    await page.getByTestId('search-result').first().click();
    await expect(page.getByTestId('focus-label')).toHaveText('Acme Retail');

    const stored = await page.evaluate(() => window.localStorage.getItem('ownership-explorer:recent'));
    expect(JSON.parse(stored)[0].label).toBe('Acme Retail');

    await mockWikidata(page);
    await page.reload();
    await expect(page.getByTestId('recent-item').first()).toContainText('Acme Retail');
  });

  test('narrow mobile viewport does not overflow horizontally', async ({ page }) => {
    await mockWikidata(page);
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(INDEX_URL);
    await expect(page.getByTestId('search-input')).toBeVisible();
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    expect(overflow).toBeLessThanOrEqual(1);
  });
});
