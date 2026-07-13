const path = require('path');
const { test, expect } = require('@playwright/test');

const APP_URL = 'file://' + path.resolve(__dirname, '../index.html');

test.describe('Brain diagram (Explore mode)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(APP_URL);
  });

  test('loads with the lateral view active and 6 lateral regions clickable/labeled', async ({ page }) => {
    await expect(page.locator('#view-lateral')).toBeVisible();
    await expect(page.locator('#view-medial')).toBeHidden();
    const lateralRegions = page.locator('#view-lateral .region');
    await expect(lateralRegions).toHaveCount(6);
    await expect(page.locator('.region[data-region="dlpfc"] .region-label')).toHaveText('dlPFC');
  });

  test('switching to the medial view shows all 7 subcortical regions', async ({ page }) => {
    await page.click('[data-testid="view-tab-medial"]');
    await expect(page.locator('#view-medial')).toBeVisible();
    await expect(page.locator('#view-lateral')).toBeHidden();
    const medialRegions = page.locator('#view-medial .region');
    await expect(medialRegions).toHaveCount(7);
    await expect(page.locator('.region[data-region="amygdala"] .region-label')).toHaveText('Amyg');
  });

  test('all 13 regions across both views are present in the document', async ({ page }) => {
    const allRegions = page.locator('.region');
    await expect(allRegions).toHaveCount(13);
  });

  test('clicking a region shows its name, function, and relevance in the explore detail panel', async ({ page }) => {
    await page.click('[data-testid="view-tab-medial"]');
    await page.click('.region[data-region="amygdala"]');
    const detail = page.locator('#explore-detail');
    await expect(detail).toContainText('Amygdala');
    await expect(detail).toContainText('threat');
  });

  test('a region is reachable and activatable via keyboard (Tab + Enter)', async ({ page }) => {
    const region = page.locator('.region[data-region="dlpfc"]');
    await region.focus();
    await expect(region).toBeFocused();
    await page.keyboard.press('Enter');
    await expect(page.locator('#explore-detail')).toContainText('Dorsolateral Prefrontal Cortex');
  });

  test('view tab buttons reflect aria-selected state correctly', async ({ page }) => {
    await expect(page.locator('[data-testid="view-tab-lateral"]')).toHaveAttribute('aria-selected', 'true');
    await page.click('[data-testid="view-tab-medial"]');
    await expect(page.locator('[data-testid="view-tab-medial"]')).toHaveAttribute('aria-selected', 'true');
    await expect(page.locator('[data-testid="view-tab-lateral"]')).toHaveAttribute('aria-selected', 'false');
  });

  test('no console errors occur while browsing every region in both views', async ({ page }) => {
    const errors = [];
    page.on('console', (msg) => { if (msg.type() === 'error') errors.push(msg.text()); });
    page.on('pageerror', (err) => errors.push(err.message));

    for (const id of ['dlpfc', 'vlpfc', 'insula', 'sts', 'temporal_pole', 'tpj']) {
      await page.click(`.region[data-region="${id}"]`);
    }
    await page.click('[data-testid="view-tab-medial"]');
    for (const id of ['vmpfc', 'ofc', 'acc', 'amygdala', 'hippocampus', 'hypothalamus', 'ventral_striatum']) {
      await page.click(`.region[data-region="${id}"]`);
    }

    expect(errors).toEqual([]);
  });
});
