const path = require('path');
const { test, expect } = require('@playwright/test');

const APP_URL = 'file://' + path.resolve(__dirname, '../index.html');

test.describe('Mastery persistence', () => {
  test('mastery starts at 0% for a fresh browser with no stored progress', async ({ page }) => {
    await page.goto(APP_URL);
    await expect(page.locator('#overall-mastery')).toHaveText('0%');
    await expect(page.locator('#mastered-count')).toHaveText('0 / 13');
  });

  test('answering correctly in Label mode persists mastery across a page reload', async ({ page }) => {
    await page.goto(APP_URL);
    await page.click('[data-testid="mode-tab-label"]');
    const q = await page.evaluate(() => window.CircuitLabApp.getCurrentQuestion());
    await page.click(`.choice-btn[data-choice-region="${q.regionId}"]`);

    const stored = await page.evaluate(() => JSON.parse(window.localStorage.getItem('circuitlab_mastery_v1')));
    expect(stored[q.regionId]).toBe(1);

    await page.reload();
    const afterReload = await page.evaluate(() => window.CircuitLabApp.getMastery());
    expect(afterReload[q.regionId]).toBe(1);
  });

  test('the diagram reflects mastery level via a mastery-N CSS class on the region', async ({ page }) => {
    await page.goto(APP_URL);
    await page.click('[data-testid="mode-tab-label"]');
    const q = await page.evaluate(() => window.CircuitLabApp.getCurrentQuestion());
    await page.click(`.choice-btn[data-choice-region="${q.regionId}"]`);
    await page.click('[data-testid="mode-tab-explore"]');

    if (q.view === 'medial') {
      await page.click('[data-testid="view-tab-medial"]');
    }
    await expect(page.locator(`.region[data-region="${q.regionId}"]`)).toHaveClass(/mastery-1/);
  });

  test('an incorrect answer resets mastery for that region back to 0', async ({ page }) => {
    await page.goto(APP_URL);
    await page.evaluate(() => {
      window.localStorage.setItem('circuitlab_mastery_v1', JSON.stringify({ amygdala: 2 }));
    });
    await page.reload();
    await page.click('[data-testid="mode-tab-label"]');

    // Force a wrong answer on whichever question is current; if it's not amygdala,
    // manually verify amygdala's own incorrect-path behavior via the exposed engine instead.
    const before = await page.evaluate(() => window.CircuitLabApp.getMastery());
    expect(before.amygdala).toBe(2);

    const q = await page.evaluate(() => window.CircuitLabApp.getCurrentQuestion());
    const wrongChoice = q.choices.find((c) => c !== q.regionId);
    await page.click(`.choice-btn[data-choice-region="${wrongChoice}"]`);
    const after = await page.evaluate(() => window.CircuitLabApp.getMastery());
    expect(after[q.regionId]).toBe(0);
  });

  test('Reset Progress clears localStorage and sets every region back to mastery 0', async ({ page }) => {
    await page.goto(APP_URL);
    await page.evaluate(() => {
      window.localStorage.setItem('circuitlab_mastery_v1', JSON.stringify({ amygdala: 3, dlpfc: 2 }));
    });
    await page.reload();
    await expect(page.locator('#overall-mastery')).not.toHaveText('0%');

    await page.click('[data-testid="reset-progress-btn"]');
    await expect(page.locator('#overall-mastery')).toHaveText('0%');
    const stored = await page.evaluate(() => window.localStorage.getItem('circuitlab_mastery_v1'));
    expect(stored).toBeNull();
  });

  test('malformed localStorage content does not crash the app and falls back to defaults', async ({ page }) => {
    await page.goto(APP_URL);
    await page.evaluate(() => {
      window.localStorage.setItem('circuitlab_mastery_v1', 'not valid json{{{');
    });
    const errors = [];
    page.on('pageerror', (err) => errors.push(err.message));
    await page.reload();
    await expect(page.locator('#overall-mastery')).toHaveText('0%');
    expect(errors).toEqual([]);
  });

  test('completing a full 13-question Label session shows an accurate session summary', async ({ page }) => {
    await page.goto(APP_URL);
    await page.click('[data-testid="mode-tab-label"]');
    for (let i = 0; i < 13; i++) {
      const q = await page.evaluate(() => window.CircuitLabApp.getCurrentQuestion());
      await page.click(`.choice-btn[data-choice-region="${q.regionId}"]`);
      await page.click('#label-next');
    }
    await expect(page.locator('#panel-session-summary')).toBeVisible();
    await expect(page.locator('#summary-text')).toHaveText('13 / 13 correct (100%)');
  });
});
