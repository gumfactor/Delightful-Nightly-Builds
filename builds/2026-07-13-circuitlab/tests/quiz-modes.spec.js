const path = require('path');
const { test, expect } = require('@playwright/test');

const APP_URL = 'file://' + path.resolve(__dirname, '../index.html');

test.describe('Label Quiz mode', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(APP_URL);
    await page.click('[data-testid="mode-tab-label"]');
  });

  test('shows both diagrams and highlights the target region for the current question', async ({ page }) => {
    await expect(page.locator('#view-lateral')).toBeVisible();
    await expect(page.locator('#view-medial')).toBeVisible();
    await expect(page.locator('.region.highlighted')).toHaveCount(1);
  });

  test('choosing the correct answer marks it correct and enables Next', async ({ page }) => {
    const q = await page.evaluate(() => window.CircuitLabApp.getCurrentQuestion());
    await page.click(`.choice-btn[data-choice-region="${q.regionId}"]`);
    await expect(page.locator('#label-feedback')).toHaveClass(/feedback-correct/);
    await expect(page.locator('#label-next')).toBeEnabled();
  });

  test('choosing a wrong answer marks it incorrect and reveals the correct name', async ({ page }) => {
    const q = await page.evaluate(() => window.CircuitLabApp.getCurrentQuestion());
    const wrongChoice = q.choices.find((c) => c !== q.regionId);
    await page.click(`.choice-btn[data-choice-region="${wrongChoice}"]`);
    await expect(page.locator('#label-feedback')).toHaveClass(/feedback-incorrect/);
    await expect(page.locator('#label-next')).toBeEnabled();
  });

  test('correct answer increases the region mastery level by one', async ({ page }) => {
    const q = await page.evaluate(() => window.CircuitLabApp.getCurrentQuestion());
    const before = await page.evaluate(() => window.CircuitLabApp.getMastery());
    await page.click(`.choice-btn[data-choice-region="${q.regionId}"]`);
    const after = await page.evaluate(() => window.CircuitLabApp.getMastery());
    expect(after[q.regionId]).toBe(before[q.regionId] + 1);
  });

  test('Next advances to a new question with a different highlighted region state', async ({ page }) => {
    const q1 = await page.evaluate(() => window.CircuitLabApp.getCurrentQuestion());
    await page.click(`.choice-btn[data-choice-region="${q1.regionId}"]`);
    await page.click('#label-next');
    await expect(page.locator('#label-progress')).toHaveText('2 / 13');
    await expect(page.locator('.region.highlighted')).toHaveCount(1);
  });
});

test.describe('Function Match mode', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(APP_URL);
    await page.click('[data-testid="mode-tab-function"]');
  });

  test('shows a function prompt with no diagram highlight (the diagram click is the answer)', async ({ page }) => {
    await expect(page.locator('#function-prompt')).not.toHaveText('');
    await expect(page.locator('.region.highlighted')).toHaveCount(0);
  });

  test('clicking the correct region on the diagram registers correct', async ({ page }) => {
    const q = await page.evaluate(() => window.CircuitLabApp.getCurrentQuestion());
    // both views are visible simultaneously in quiz mode, regardless of the (hidden) view tabs
    await page.click(`.region[data-region="${q.regionId}"]`);
    await expect(page.locator('#function-feedback')).toHaveClass(/feedback-correct/);
    await expect(page.locator('#function-next')).toBeEnabled();
  });

  test('clicking the wrong region on the diagram registers incorrect and highlights the correct one', async ({ page }) => {
    const q = await page.evaluate(() => window.CircuitLabApp.getCurrentQuestion());
    const wrongId = q.regionId === 'amygdala' ? 'hippocampus' : 'amygdala';
    await page.click(`.region[data-region="${wrongId}"]`);
    await expect(page.locator('#function-feedback')).toHaveClass(/feedback-incorrect/);
    await expect(page.locator(`.region[data-region="${q.regionId}"].highlighted`)).toHaveCount(1);
  });

  test('a second click after answering does not double-count the result', async ({ page }) => {
    const q = await page.evaluate(() => window.CircuitLabApp.getCurrentQuestion());
    await page.click(`.region[data-region="${q.regionId}"]`);
    await page.click(`.region[data-region="${q.regionId}"]`);
    await expect(page.locator('#function-progress')).toHaveText('1 / 13');
  });
});

test.describe('Circuit Trace mode', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(APP_URL);
    await page.click('[data-testid="mode-tab-circuit"]');
  });

  test('shows a circuit name and both diagrams', async ({ page }) => {
    await expect(page.locator('#circuit-name')).not.toHaveText('');
    await expect(page.locator('#view-lateral')).toBeVisible();
    await expect(page.locator('#view-medial')).toBeVisible();
  });

  test('clicking the correct sequence in order completes the circuit successfully', async ({ page }) => {
    const q = await page.evaluate(() => window.CircuitLabApp.getCurrentQuestion());
    for (const regionId of q.sequence) {
      await page.click(`.region[data-region="${regionId}"]`);
    }
    await expect(page.locator('#circuit-feedback')).toHaveClass(/feedback-correct/);
    await expect(page.locator('#circuit-next')).toBeEnabled();
    await expect(page.locator('#circuit-steps')).toHaveText(`${q.sequence.length} / ${q.sequence.length} regions selected`);
  });

  test('clicking a region out of order is rejected as incorrect', async ({ page }) => {
    const q = await page.evaluate(() => window.CircuitLabApp.getCurrentQuestion());
    const allRegionIds = ['dlpfc', 'vlpfc', 'insula', 'sts', 'temporal_pole', 'tpj', 'vmpfc', 'ofc', 'acc', 'amygdala', 'hippocampus', 'hypothalamus', 'ventral_striatum'];
    const outOfOrder = allRegionIds.find((id) => !q.sequence.includes(id)) || allRegionIds.find((id) => id !== q.sequence[0]);
    await page.click(`.region[data-region="${outOfOrder}"]`);
    await expect(page.locator('#circuit-feedback')).toHaveClass(/feedback-incorrect/);
    await expect(page.locator('#circuit-next')).toBeEnabled();
  });

  test('correct sequence completion raises mastery for every region in the circuit', async ({ page }) => {
    const q = await page.evaluate(() => window.CircuitLabApp.getCurrentQuestion());
    const before = await page.evaluate(() => window.CircuitLabApp.getMastery());
    for (const regionId of q.sequence) {
      await page.click(`.region[data-region="${regionId}"]`);
    }
    const after = await page.evaluate(() => window.CircuitLabApp.getMastery());
    for (const regionId of q.sequence) {
      expect(after[regionId]).toBe(Math.min(3, before[regionId] + 1));
    }
  });
});
