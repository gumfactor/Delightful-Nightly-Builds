const { test, expect } = require('@playwright/test');
const { gotoFresh, selectTiles, submitGuess } = require('./helpers');

// All gameplay-mechanics tests use practice mode loaded with the known
// puzzle "p01" so item content is fixed, regardless of the real calendar
// date the suite happens to run on.
const P01_YELLOW = ['AMYGDALA', 'HIPPOCAMPUS', 'CORTEX', 'INSULA'];
const P01_GREEN = ['DOPAMINE', 'SEROTONIN', 'CORTISOL', 'OXYTOCIN'];
const P01_BLUE = ['AROUSAL', 'HABITUATION', 'RESILIENCE', 'REAPPRAISAL'];
const P01_PURPLE = ['CONFOUND', 'BASELINE', 'PLACEBO', 'EXTINCTION'];

async function loadP01Practice(page) {
  await gotoFresh(page);
  await page.evaluate(() => startPracticeGame('p01'));
}

test.describe('core gameplay mechanics', () => {
  test('renders all 16 tiles on load', async ({ page }) => {
    await loadP01Practice(page);
    await expect(page.locator('[data-testid="tile"]')).toHaveCount(16);
  });

  test('selecting fewer than 4 tiles keeps submit disabled; exactly 4 enables it', async ({ page }) => {
    await loadP01Practice(page);
    await selectTiles(page, P01_YELLOW.slice(0, 3));
    await expect(page.locator('#submit-btn')).toBeDisabled();
    await selectTiles(page, [P01_YELLOW[3]]);
    await expect(page.locator('#submit-btn')).toBeEnabled();
  });

  test('a 5th tile selection is ignored while 4 are already selected', async ({ page }) => {
    await loadP01Practice(page);
    await selectTiles(page, P01_YELLOW);
    await selectTiles(page, [P01_GREEN[0]]);
    const state = await page.evaluate(() => getGameState().selected);
    expect(state).toEqual(P01_YELLOW);
  });

  test('clicking an already-selected tile deselects it', async ({ page }) => {
    await loadP01Practice(page);
    await selectTiles(page, P01_YELLOW.slice(0, 2));
    await selectTiles(page, [P01_YELLOW[0]]);
    const state = await page.evaluate(() => getGameState().selected);
    expect(state).toEqual([P01_YELLOW[1]]);
  });

  test('deselect-all clears the current selection', async ({ page }) => {
    await loadP01Practice(page);
    await selectTiles(page, P01_YELLOW.slice(0, 3));
    await page.locator('#deselect-btn').click();
    const state = await page.evaluate(() => getGameState().selected);
    expect(state).toEqual([]);
    await expect(page.locator('#submit-btn')).toBeDisabled();
  });

  test('shuffle preserves the same 16 tile items', async ({ page }) => {
    await loadP01Practice(page);
    const before = (await page.evaluate(() => getGameState().tiles.map((t) => t.item))).sort();
    await page.locator('#shuffle-btn').click();
    const after = (await page.evaluate(() => getGameState().tiles.map((t) => t.item))).sort();
    expect(after).toEqual(before);
  });

  test('a correct guess locks the category into the solved area and removes its tiles', async ({ page }) => {
    await loadP01Practice(page);
    await submitGuess(page, P01_YELLOW);
    await expect(page.locator('[data-testid="solved-category"]')).toHaveCount(1);
    await expect(page.locator('[data-testid="solved-category"]')).toContainText('Brain Regions');
    await expect(page.locator('[data-testid="tile"]')).toHaveCount(12);
    for (const item of P01_YELLOW) {
      await expect(page.locator(`[data-testid="tile"][data-item="${item}"]`)).toHaveCount(0);
    }
  });

  test('an incorrect guess increments the mistake counter and clears selection', async ({ page }) => {
    await loadP01Practice(page);
    await submitGuess(page, [P01_YELLOW[0], P01_GREEN[0], P01_BLUE[0], P01_PURPLE[0]]);
    const mistakes = await page.evaluate(() => getGameState().mistakes);
    expect(mistakes).toBe(1);
    await expect(page.locator('#mistakes-tracker')).toContainText('Mistakes: 1 / 4');
    const selected = await page.evaluate(() => getGameState().selected);
    expect(selected).toEqual([]);
  });

  test('a "one away" message appears when exactly 3 of 4 selected share a true category', async ({ page }) => {
    await loadP01Practice(page);
    await submitGuess(page, [P01_YELLOW[0], P01_YELLOW[1], P01_YELLOW[2], P01_GREEN[0]]);
    await expect(page.locator('#message-banner')).toContainText('One away');
  });

  test('a guess with no 3-way match shows the generic incorrect message', async ({ page }) => {
    await loadP01Practice(page);
    await submitGuess(page, [P01_YELLOW[0], P01_GREEN[0], P01_BLUE[0], P01_PURPLE[0]]);
    await expect(page.locator('#message-banner')).toContainText('Not quite');
  });
});
