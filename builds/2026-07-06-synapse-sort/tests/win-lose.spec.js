const { test, expect } = require('@playwright/test');
const { gotoFresh, submitGuess } = require('./helpers');

const P01_YELLOW = ['AMYGDALA', 'HIPPOCAMPUS', 'CORTEX', 'INSULA'];
const P01_GREEN = ['DOPAMINE', 'SEROTONIN', 'CORTISOL', 'OXYTOCIN'];
const P01_BLUE = ['AROUSAL', 'HABITUATION', 'RESILIENCE', 'REAPPRAISAL'];
const P01_PURPLE = ['CONFOUND', 'BASELINE', 'PLACEBO', 'EXTINCTION'];

async function loadP01Practice(page) {
  await gotoFresh(page);
  await page.evaluate(() => startPracticeGame('p01'));
}

test.describe('win and lose flows', () => {
  test('solving all 4 categories triggers a win with a zero-mistake share grid', async ({ page }) => {
    await loadP01Practice(page);
    await submitGuess(page, P01_YELLOW);
    await submitGuess(page, P01_GREEN);
    await submitGuess(page, P01_BLUE);
    await submitGuess(page, P01_PURPLE);

    await expect(page.locator('#result-panel')).toBeVisible();
    await expect(page.locator('#result-heading')).toHaveText('Solved!');
    const shareText = await page.locator('#share-grid-text').innerText();
    expect(shareText).toContain('Synapse Sort — Brain & Body');
    expect(shareText).toContain('Solved with 0/4 mistakes');
    // 4 correct guesses = 4 emoji rows between the header and footer line.
    const emojiRows = shareText.split('\n').filter((line) => /^[\u{1F7E8}\u{1F7E9}\u{1F7E6}\u{1F7EA}]+$/u.test(line));
    expect(emojiRows).toHaveLength(4);

    const solved = await page.evaluate(() => getGameState().solvedCategoryIndexes.length);
    expect(solved).toBe(4);
  });

  test('4 wrong guesses trigger a loss and reveal every remaining category', async ({ page }) => {
    await loadP01Practice(page);
    await submitGuess(page, [P01_YELLOW[0], P01_GREEN[0], P01_BLUE[0], P01_PURPLE[0]]);
    await submitGuess(page, [P01_YELLOW[1], P01_GREEN[1], P01_BLUE[1], P01_PURPLE[1]]);
    await submitGuess(page, [P01_YELLOW[2], P01_GREEN[2], P01_BLUE[2], P01_PURPLE[2]]);
    await submitGuess(page, [P01_YELLOW[3], P01_GREEN[3], P01_BLUE[3], P01_PURPLE[3]]);

    await expect(page.locator('#result-panel')).toBeVisible();
    await expect(page.locator('#result-heading')).toHaveText('Better luck tomorrow');
    const shareText = await page.locator('#share-grid-text').innerText();
    expect(shareText).toContain('Not solved — 4/4 mistakes');

    await expect(page.locator('[data-testid="solved-category"]')).toHaveCount(4);
    const gameOver = await page.evaluate(() => getGameState().gameOver);
    expect(gameOver).toBe(true);
  });

  test('the share grid has one emoji row per guess actually made, including wrong guesses', async ({ page }) => {
    await loadP01Practice(page);
    // One wrong guess, then solve the yellow category correctly.
    await submitGuess(page, [P01_YELLOW[0], P01_GREEN[0], P01_BLUE[0], P01_PURPLE[0]]);
    await submitGuess(page, P01_YELLOW);
    const history = await page.evaluate(() => getGameState().guessHistory.length);
    expect(history).toBe(2);
  });

  test('the puzzle counter shows "(practice)" while playing a non-daily puzzle', async ({ page }) => {
    await loadP01Practice(page);
    await expect(page.locator('#puzzle-counter')).toContainText('(practice)');
  });
});
