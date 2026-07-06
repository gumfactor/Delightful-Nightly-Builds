const path = require('path');

function pageUrl() {
  return 'file://' + path.join(__dirname, '..', 'index.html');
}

// Loads the game with a guaranteed-clean localStorage, regardless of what
// earlier tests in the same worker may have left behind.
async function gotoFresh(page) {
  await page.goto(pageUrl());
  await page.evaluate(() => window.localStorage.clear());
  await page.reload();
}

async function selectTiles(page, items) {
  for (const item of items) {
    await page.locator(`[data-testid="tile"][data-item="${item}"]`).click();
  }
}

async function submitGuess(page, items) {
  await selectTiles(page, items);
  await page.locator('#submit-btn').click();
}

async function getTodayPuzzle(page) {
  return page.evaluate(() => getPuzzleForDate(new Date().toISOString().slice(0, 10)));
}

module.exports = { pageUrl, gotoFresh, selectTiles, submitGuess, getTodayPuzzle };
