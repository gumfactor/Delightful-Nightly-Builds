const fs = require('fs');
const path = require('path');
const { pathToFileURL } = require('url');
const { test, expect } = require('@playwright/test');

const FILE_URL = pathToFileURL(path.resolve(__dirname, '../index.html')).href;
/* Helper: navigate to a fresh, empty app state */
async function loadFreshPage(page) {
  await page.goto(FILE_URL);
  await page.evaluate(() => localStorage.clear());
  await page.reload();
  await page.waitForLoadState('domcontentloaded');
}

/* Helper: fill and submit the add-entry modal */
async function addEntry(page, { symbol, name, sector = 'Technology', status = 'watchlist', conviction = '3', thesis = '' }) {
  await page.click('[data-testid="add-button"]');
  await page.waitForSelector('[data-testid="entry-modal"].open');
  await page.fill('[data-testid="modal-symbol"]', symbol);
  await page.fill('[data-testid="modal-name"]', name);
  await page.selectOption('[data-testid="modal-sector"]', sector);
  await page.selectOption('[data-testid="modal-status"]', status);
  await page.selectOption('[data-testid="modal-conviction"]', conviction);
  if (thesis) await page.fill('[data-testid="modal-thesis"]', thesis);
  await page.click('[data-testid="modal-save"]');
  /* Wait for modal overlay to become hidden (display:none when .open class is removed) */
  await expect(page.locator('#modal-overlay')).not.toBeVisible();
}

/* ── Tests ── */

test('page loads with empty-state message when no entries exist', async ({ page }) => {
  await loadFreshPage(page);
  await expect(page.locator('[data-testid="empty-state"]')).toBeVisible();
  await expect(page.locator('[data-testid="stats-total"]')).toHaveText('0');
});

test('add-entry modal opens and closes', async ({ page }) => {
  await loadFreshPage(page);
  await page.click('[data-testid="add-button"]');
  await expect(page.locator('[data-testid="entry-modal"]')).toHaveClass(/open/);
  await page.click('[data-testid="modal-cancel"]');
  await expect(page.locator('[data-testid="entry-modal"]')).not.toHaveClass(/open/);
});

test('save is blocked when required fields are empty', async ({ page }) => {
  await loadFreshPage(page);
  await page.click('[data-testid="add-button"]');
  await page.click('[data-testid="modal-save"]');
  /* Error message visible, modal still open */
  await expect(page.locator('#form-error')).toBeVisible();
  await expect(page.locator('[data-testid="entry-modal"]')).toHaveClass(/open/);
});

test('can add an entry and it appears in the entry list', async ({ page }) => {
  await loadFreshPage(page);
  await addEntry(page, { symbol: 'AAPL', name: 'Apple Inc.', sector: 'Technology', status: 'watchlist', conviction: '4', thesis: 'Strong ecosystem moat.' });
  await expect(page.locator('[data-testid="entry-symbol"]').first()).toHaveText('AAPL');
  await expect(page.locator('[data-testid="entry-name"]').first()).toHaveText('Apple Inc.');
});

test('stats update correctly after adding entries', async ({ page }) => {
  await loadFreshPage(page);
  await addEntry(page, { symbol: 'AAPL', name: 'Apple Inc.', status: 'watchlist' });
  await addEntry(page, { symbol: 'MSFT', name: 'Microsoft', status: 'owned' });
  await addEntry(page, { symbol: 'META', name: 'Meta Platforms', status: 'passed' });
  await expect(page.locator('[data-testid="stats-total"]')).toHaveText('3');
  await expect(page.locator('[data-testid="stats-watchlist"]')).toHaveText('1');
  await expect(page.locator('[data-testid="stats-owned"]')).toHaveText('1');
  await expect(page.locator('[data-testid="stats-passed"]')).toHaveText('1');
});

test('filter-watchlist shows only watchlist entries', async ({ page }) => {
  await loadFreshPage(page);
  await addEntry(page, { symbol: 'AAPL', name: 'Apple Inc.', status: 'watchlist' });
  await addEntry(page, { symbol: 'MSFT', name: 'Microsoft', status: 'owned' });
  await page.click('[data-testid="filter-watchlist"]');
  const cards = page.locator('[data-testid="entry-symbol"]');
  await expect(cards).toHaveCount(1);
  await expect(cards.first()).toHaveText('AAPL');
});

test('filter-owned shows only owned entries', async ({ page }) => {
  await loadFreshPage(page);
  await addEntry(page, { symbol: 'AAPL', name: 'Apple Inc.', status: 'watchlist' });
  await addEntry(page, { symbol: 'NVDA', name: 'NVIDIA', status: 'owned' });
  await page.click('[data-testid="filter-owned"]');
  const cards = page.locator('[data-testid="entry-symbol"]');
  await expect(cards).toHaveCount(1);
  await expect(cards.first()).toHaveText('NVDA');
});

test('search filters entries by symbol', async ({ page }) => {
  await loadFreshPage(page);
  await addEntry(page, { symbol: 'AAPL', name: 'Apple Inc.', status: 'watchlist' });
  await addEntry(page, { symbol: 'MSFT', name: 'Microsoft', status: 'watchlist' });
  await page.fill('[data-testid="search-input"]', 'AAPL');
  const cards = page.locator('[data-testid="entry-symbol"]');
  await expect(cards).toHaveCount(1);
  await expect(cards.first()).toHaveText('AAPL');
});

test('search filters entries by thesis text', async ({ page }) => {
  await loadFreshPage(page);
  await addEntry(page, { symbol: 'AAPL', name: 'Apple Inc.', thesis: 'Strong ecosystem moat.' });
  await addEntry(page, { symbol: 'MSFT', name: 'Microsoft', thesis: 'Cloud dominance via Azure.' });
  await page.fill('[data-testid="search-input"]', 'ecosystem');
  const cards = page.locator('[data-testid="entry-symbol"]');
  await expect(cards).toHaveCount(1);
  await expect(cards.first()).toHaveText('AAPL');
});

test('filter-all shows all entries after filtering', async ({ page }) => {
  await loadFreshPage(page);
  await addEntry(page, { symbol: 'AAPL', name: 'Apple Inc.', status: 'watchlist' });
  await addEntry(page, { symbol: 'MSFT', name: 'Microsoft', status: 'owned' });
  await page.click('[data-testid="filter-watchlist"]');
  await expect(page.locator('[data-testid="entry-symbol"]')).toHaveCount(1);
  await page.click('[data-testid="filter-all"]');
  await expect(page.locator('[data-testid="entry-symbol"]')).toHaveCount(2);
});

test('can edit an existing entry', async ({ page }) => {
  await loadFreshPage(page);
  await addEntry(page, { symbol: 'AAPL', name: 'Apple Inc.', status: 'watchlist', conviction: '3' });
  await page.click('[data-testid="entry-edit"]');
  await page.waitForSelector('[data-testid="entry-modal"].open');
  /* Change status to owned and conviction to 5 */
  await page.selectOption('[data-testid="modal-status"]', 'owned');
  await page.selectOption('[data-testid="modal-conviction"]', '5');
  await page.click('[data-testid="modal-save"]');
  await expect(page.locator('#modal-overlay')).not.toBeVisible();
  await expect(page.locator('[data-testid="entry-status"]').first()).toHaveText('Owned');
});

test('can delete an entry via confirm dialog', async ({ page }) => {
  await loadFreshPage(page);
  await addEntry(page, { symbol: 'AAPL', name: 'Apple Inc.' });
  await expect(page.locator('[data-testid="entry-symbol"]')).toHaveCount(1);
  page.once('dialog', dialog => dialog.accept());
  await page.click('[data-testid="entry-delete"]');
  await expect(page.locator('[data-testid="empty-state"]')).toBeVisible();
});

test('export downloads the current entries as JSON', async ({ page }) => {
  await loadFreshPage(page);
  await addEntry(page, { symbol: 'AAPL', name: 'Apple Inc.', status: 'watchlist', conviction: '4', thesis: 'Strong ecosystem moat.' });

  const downloadPromise = page.waitForEvent('download');
  await page.click('[data-testid="export-button"]');
  const download = await downloadPromise;
  const downloadPath = await download.path();
  const exportedEntries = JSON.parse(await fs.promises.readFile(downloadPath, 'utf8'));

  await expect(download.suggestedFilename()).toMatch(/^investment-research-\d{4}-\d{2}-\d{2}\.json$/);
  expect(exportedEntries).toHaveLength(1);
  expect(exportedEntries[0]).toMatchObject({
    symbol: 'AAPL',
    name: 'Apple Inc.',
    status: 'watchlist',
    conviction: 4,
    thesis: 'Strong ecosystem moat.',
  });
});

test('import uploads JSON entries after confirmation and updates the UI', async ({ page }, testInfo) => {
  await loadFreshPage(page);
  await addEntry(page, { symbol: 'MSFT', name: 'Microsoft', status: 'owned' });

  const importFilePath = testInfo.outputPath('import.json');
  await fs.promises.writeFile(importFilePath, JSON.stringify([
    {
      id: 'imported-entry-1',
      symbol: 'NVDA',
      name: 'NVIDIA',
      sector: 'Technology',
      status: 'watchlist',
      conviction: 5,
      thesis: 'AI infrastructure demand.',
      dateAdded: '2026-06-09T00:00:00.000Z',
      lastUpdated: '2026-06-09T00:00:00.000Z',
    }
  ]));

  page.once('dialog', dialog => dialog.accept());
  await page.locator('#import-file-input').setInputFiles(importFilePath);

  await expect(page.locator('[data-testid="entry-symbol"]')).toHaveCount(1);
  await expect(page.locator('[data-testid="entry-symbol"]').first()).toHaveText('NVDA');
  await expect(page.locator('[data-testid="entry-name"]').first()).toHaveText('NVIDIA');
  await expect(page.locator('[data-testid="stats-total"]')).toHaveText('1');
  await expect(page.locator('[data-testid="empty-state"]')).toBeHidden();
});

test('entry persists in localStorage after page reload', async ({ page }) => {
  await loadFreshPage(page);
  await addEntry(page, { symbol: 'AAPL', name: 'Apple Inc.', status: 'watchlist', conviction: '4' });
  await page.reload();
  await page.waitForLoadState('domcontentloaded');
  await expect(page.locator('[data-testid="entry-symbol"]').first()).toHaveText('AAPL');
  await expect(page.locator('[data-testid="stats-total"]')).toHaveText('1');
});
