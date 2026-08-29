const { test, expect } = require('@playwright/test');
const path = require('path');

const INDEX_URL = 'file://' + path.resolve(__dirname, '..', 'index.html');

test.describe('Answer grid interactions', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(INDEX_URL);
    await page.evaluate(() => localStorage.clear());
  });

  test('practicing chapter 1 renders one select per (study x category) cell', async ({ page }) => {
    await page.evaluate(() => window.ZebraLab.startPuzzle('practice', 1));
    const puzzle = await page.evaluate(() => window.ZebraLab.state.puzzle);
    const attrCatCount = puzzle.categories.length - 1; // minus the position category
    const selects = page.locator('#answer-grid select');
    await expect(selects).toHaveCount(puzzle.size * attrCatCount);
  });

  test('checking an all-blank grid reports zero fully-correct studies', async ({ page }) => {
    await page.evaluate(() => window.ZebraLab.startPuzzle('practice', 1));
    await page.locator('[data-testid="btn-check"]').click();
    await expect(page.locator('[data-testid="check-feedback"]')).toContainText('0 of');
    await expect(page.locator('[data-testid="checks-used"]')).toHaveText('1');
  });

  test('filling in the exact solution and checking solves the puzzle and shows the result screen', async ({ page }) => {
    await page.evaluate(() => window.ZebraLab.startPuzzle('practice', 1));
    await page.evaluate(() => {
      const { puzzle } = window.ZebraLab.state;
      const attrCats = puzzle.categories.filter((c) => c.id !== 'position');
      for (let p = 0; p < puzzle.size; p++) {
        attrCats.forEach((cat) => {
          const select = document.querySelector(`[data-testid="grid-select-${cat.id}-${p}"]`);
          select.value = String(puzzle.solution[cat.id][p]);
          select.dispatchEvent(new Event('change'));
        });
      }
    });
    await page.locator('[data-testid="btn-check"]').click();
    await expect(page.locator('[data-testid="check-feedback"]')).toContainText('Solved!');
    await expect(page.locator('[data-testid="screen-result"]')).toBeVisible({ timeout: 3000 });
  });

  test('hint button reveals a correct study and is capped at 2 uses', async ({ page }) => {
    await page.evaluate(() => window.ZebraLab.startPuzzle('practice', 2));
    await page.locator('[data-testid="btn-hint"]').click();
    await expect(page.locator('#hint-count')).toHaveText('1');
    await page.locator('[data-testid="btn-hint"]').click();
    await expect(page.locator('#hint-count')).toHaveText('0');

    const correctAfterTwoHints = await page.evaluate(() =>
      window.ZebraLab.state.puzzle.categories
        .filter((c) => c.id !== 'position')
        .reduce((count, cat) => {
          for (let p = 0; p < window.ZebraLab.state.puzzle.size; p++) {
            if (window.ZebraLab.state.playerAssign[cat.id][p] === window.ZebraLab.state.puzzle.solution[cat.id][p]) {
              count++;
            }
          }
          return count;
        }, 0)
    );
    expect(correctAfterTwoHints).toBeGreaterThan(0);

    // A third click should have no further effect (capped at MAX_HINTS = 2).
    await page.locator('[data-testid="btn-hint"]').click();
    await expect(page.locator('#hint-count')).toHaveText('0');
  });

  test('back-to-menu button returns to the home screen', async ({ page }) => {
    await page.evaluate(() => window.ZebraLab.startPuzzle('practice', 1));
    await page.locator('[data-testid="btn-back-to-menu"]').click();
    await expect(page.locator('[data-testid="screen-home"]')).toBeVisible();
    await expect(page.locator('[data-testid="screen-puzzle"]')).toBeHidden();
  });
});
