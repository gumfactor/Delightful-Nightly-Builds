const { test, expect } = require('@playwright/test');
const { gotoFresh, submitGuess, getTodayPuzzle } = require('./helpers');

async function submitAllCorrect(page, puzzle) {
  for (const category of puzzle.categories) {
    await submitGuess(page, category.items);
  }
}

async function submitFourWrongGuesses(page, puzzle) {
  // Build 4 cross-category guesses (one item per category each time) so
  // none of them can accidentally match a true category.
  for (let round = 0; round < 4; round++) {
    const items = puzzle.categories.map((c) => c.items[round]);
    await submitGuess(page, items);
  }
}

test.describe('stats persistence and archive mode', () => {
  test('practice mode play does not affect saved stats', async ({ page }) => {
    await gotoFresh(page);
    const before = await page.evaluate(() => window.SynapseSort.getStats());
    expect(before.gamesPlayed).toBe(0);

    await page.evaluate(() => startPracticeGame('p01'));
    await submitGuess(page, ['AMYGDALA', 'HIPPOCAMPUS', 'CORTEX', 'INSULA']);
    await submitGuess(page, ['DOPAMINE', 'SEROTONIN', 'CORTISOL', 'OXYTOCIN']);
    await submitGuess(page, ['AROUSAL', 'HABITUATION', 'RESILIENCE', 'REAPPRAISAL']);
    await submitGuess(page, ['CONFOUND', 'BASELINE', 'PLACEBO', 'EXTINCTION']);

    const after = await page.evaluate(() => window.SynapseSort.getStats());
    expect(after.gamesPlayed).toBe(0);
  });

  test('archive mode loads a specific puzzle by id, independent of the daily puzzle', async ({ page }) => {
    await gotoFresh(page);
    await page.locator('#archive-btn').click();
    await page.locator('[data-testid="archive-item"][data-id="p05"]').click();
    await expect(page.locator('#puzzle-title')).toHaveText('Finish Line to Fairway');
    await expect(page.locator('#puzzle-counter')).toContainText('(practice)');
  });

  test('winning the daily puzzle records a win and starts a streak', async ({ page }) => {
    await gotoFresh(page);
    const puzzle = await getTodayPuzzle(page);
    await submitAllCorrect(page, puzzle);

    const stats = await page.evaluate(() => window.SynapseSort.getStats());
    const today = await page.evaluate(() => new Date().toISOString().slice(0, 10));
    expect(stats.gamesPlayed).toBe(1);
    expect(stats.wins).toBe(1);
    expect(stats.currentStreak).toBe(1);
    expect(stats.bestStreak).toBe(1);
    expect(stats.history[today]).toEqual({ won: true, mistakes: 0 });
  });

  test('losing the daily puzzle resets an existing streak to 0', async ({ page }) => {
    await gotoFresh(page);
    // Seed a streak of 1 from a prior (fake) day before playing today.
    await page.evaluate(() => window.SynapseSort.recordDailyResult('2020-01-01', true, 0));
    await page.reload();

    const puzzle = await getTodayPuzzle(page);
    await submitFourWrongGuesses(page, puzzle);

    const stats = await page.evaluate(() => window.SynapseSort.getStats());
    expect(stats.wins).toBe(1);
    expect(stats.gamesPlayed).toBe(2);
    expect(stats.currentStreak).toBe(0);
    expect(stats.bestStreak).toBe(1);
  });

  test('reloading after completing the daily puzzle shows the already-played state', async ({ page }) => {
    await gotoFresh(page);
    const puzzle = await getTodayPuzzle(page);
    await submitAllCorrect(page, puzzle);

    await page.reload();
    await expect(page.locator('[data-testid="tile"]')).toHaveCount(0);
    await expect(page.locator('#message-banner')).toContainText('already played');
  });

  test('the stats panel displays computed win rate and average mistakes', async ({ page }) => {
    await gotoFresh(page);
    const puzzle = await getTodayPuzzle(page);
    await submitAllCorrect(page, puzzle);

    await page.locator('#stats-btn').click();
    await expect(page.locator('[data-testid="stat-value"][data-stat="Games played"]')).toHaveText('1');
    await expect(page.locator('[data-testid="stat-value"][data-stat="Win rate"]')).toHaveText('100%');
    await expect(page.locator('[data-testid="stat-value"][data-stat="Average mistakes"]')).toHaveText('0.0');
  });
});
