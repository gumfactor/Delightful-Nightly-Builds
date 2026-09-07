const { test, expect } = require('@playwright/test');
const path = require('path');

const INDEX_URL = `file://${path.resolve(__dirname, '../index.html')}`;

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => localStorage.clear());
  await page.goto(INDEX_URL);
});

async function currentPuzzle(page) {
  return page.evaluate(() => window.__TC_DEBUG.getCurrentPuzzle());
}

async function answerChoicePuzzle(page, { correct }) {
  const puzzle = await currentPuzzle(page);
  const target = correct
    ? puzzle.correctAnswer
    : puzzle.choices.find((c) => c !== puzzle.correctAnswer);
  await page.locator(`[data-testid="choice-btn"][data-choice="${target}"]`).click();
  return puzzle;
}

test('page loads with the correct title and main menu', async ({ page }) => {
  await expect(page).toHaveTitle('True Course');
  await expect(page.locator('[data-testid="menu-voyage-btn"]')).toBeVisible();
  await expect(page.locator('[data-testid="menu-practice-btn"]')).toBeVisible();
  await expect(page.locator('[data-testid="menu-daily-btn"]')).toBeVisible();
  await expect(page.locator('[data-testid="menu-dashboard-btn"]')).toBeVisible();
});

test('Voyage Mode opens directly into Chapter 1 (Buoyage), round 1 of 6', async ({ page }) => {
  await page.locator('[data-testid="menu-voyage-btn"]').click();
  await expect(page.locator('[data-testid="round-title"]')).toHaveText('Chapter 1 — Buoyage — Round 1/6');
  await expect(page.locator('[data-testid="question-text"]')).not.toBeEmpty();
  await expect(page.locator('[data-testid="puzzle-canvas"]')).toBeVisible();
});

test('answering a buoyage round correctly shows correct feedback', async ({ page }) => {
  await page.locator('[data-testid="menu-voyage-btn"]').click();
  await answerChoicePuzzle(page, { correct: true });
  const feedback = page.locator('[data-testid="feedback"]');
  await expect(feedback).toHaveClass(/correct/);
});

test('answering a buoyage round incorrectly shows incorrect feedback', async ({ page }) => {
  await page.locator('[data-testid="menu-voyage-btn"]').click();
  await answerChoicePuzzle(page, { correct: false });
  const feedback = page.locator('[data-testid="feedback"]');
  await expect(feedback).toHaveClass(/incorrect/);
});

test('a perfect Chapter 1 run unlocks Chapter 2 and the dashboard reflects it', async ({ page }) => {
  await page.locator('[data-testid="menu-voyage-btn"]').click();
  for (let i = 0; i < 6; i++) {
    await answerChoicePuzzle(page, { correct: true });
    await page.locator('[data-testid="next-btn"]').click();
  }
  await expect(page.locator('[data-testid="chapter-result"]')).toHaveText('Score: 6 / 6 (100%)');
  await expect(page.locator('[data-testid="unlock-note"]')).toBeVisible();
  await expect(page.locator('[data-testid="next-chapter-btn"]')).toBeVisible();

  await page.locator('[data-testid="back-to-menu-btn"]').click();
  await page.locator('[data-testid="menu-dashboard-btn"]').click();
  const rightOfWayBadge = page.locator('tr', { hasText: 'Right of Way' }).locator('.badge');
  await expect(rightOfWayBadge).toHaveText('Unlocked');
});

test('a failing Chapter 1 run does not unlock Chapter 2', async ({ page }) => {
  await page.locator('[data-testid="menu-voyage-btn"]').click();
  for (let i = 0; i < 6; i++) {
    await answerChoicePuzzle(page, { correct: false });
    await page.locator('[data-testid="next-btn"]').click();
  }
  await expect(page.locator('[data-testid="chapter-result"]')).toHaveText('Score: 0 / 6 (0%)');
  await expect(page.locator('[data-testid="unlock-note"]')).toHaveCount(0);
  await expect(page.locator('[data-testid="next-chapter-btn"]')).toHaveCount(0);

  await page.locator('[data-testid="back-to-menu-btn"]').click();
  await page.locator('[data-testid="menu-dashboard-btn"]').click();
  const rightOfWayBadge = page.locator('tr', { hasText: 'Right of Way' }).locator('.badge');
  await expect(rightOfWayBadge).toHaveText('Locked');
});

test('Practice mode generates a fresh, answerable round after each answer', async ({ page }) => {
  await page.locator('[data-testid="menu-practice-btn"]').click();
  await page.locator('[data-testid="practice-choose-buoyage"]').click();
  await answerChoicePuzzle(page, { correct: true });
  await expect(page.locator('[data-testid="feedback"]')).toHaveClass(/correct/);
  await page.locator('[data-testid="next-btn"]').click();

  // A brand new round loaded: type is still buoyage, feedback has reset,
  // and it is answerable again (proving the round actually regenerated
  // rather than the old, already-answered state lingering).
  const second = await currentPuzzle(page);
  expect(second.type).toBe('buoyage');
  await expect(page.locator('[data-testid="feedback"]')).toHaveText('');
  await answerChoicePuzzle(page, { correct: true });
  await expect(page.locator('[data-testid="feedback"]')).toHaveClass(/correct/);
});

test('Practice mode accepts a numeric set-drift answer within tolerance', async ({ page }) => {
  await page.locator('[data-testid="menu-practice-btn"]').click();
  await page.locator('[data-testid="practice-choose-set-drift"]').click();
  const puzzle = await currentPuzzle(page);
  await page.locator('[data-testid="answer-input"]').fill(String(puzzle.correctAnswer));
  await page.locator('[data-testid="submit-btn"]').click();
  await expect(page.locator('[data-testid="feedback"]')).toHaveClass(/correct/);
});

test('a set-drift answer outside tolerance is marked incorrect', async ({ page }) => {
  await page.locator('[data-testid="menu-practice-btn"]').click();
  await page.locator('[data-testid="practice-choose-set-drift"]').click();
  const puzzle = await currentPuzzle(page);
  const wrong = (Math.round(puzzle.correctAnswer) + 30) % 360;
  await page.locator('[data-testid="answer-input"]').fill(String(wrong));
  await page.locator('[data-testid="submit-btn"]').click();
  await expect(page.locator('[data-testid="feedback"]')).toHaveClass(/incorrect/);
});

test('the Daily Challenge can be completed and produces a 5-round shareable result', async ({ page }) => {
  await page.locator('[data-testid="menu-daily-btn"]').click();
  for (let i = 0; i < 5; i++) {
    const puzzle = await currentPuzzle(page);
    if (puzzle.type === 'set-drift') {
      await page.locator('[data-testid="answer-input"]').fill(String(puzzle.correctAnswer));
      await page.locator('[data-testid="submit-btn"]').click();
    } else {
      await page.locator(`[data-testid="choice-btn"][data-choice="${puzzle.correctAnswer}"]`).click();
    }
    await page.locator('[data-testid="next-btn"]').click();
  }
  const shareBox = page.locator('[data-testid="daily-share-box"]');
  await expect(shareBox).toContainText('5/5');
  await expect(shareBox).toContainText('✅ ✅ ✅ ✅ ✅');
});

test('the Daily Challenge only allows one attempt per UTC day', async ({ page }) => {
  await page.locator('[data-testid="menu-daily-btn"]').click();
  for (let i = 0; i < 5; i++) {
    const puzzle = await currentPuzzle(page);
    if (puzzle.type === 'set-drift') {
      await page.locator('[data-testid="answer-input"]').fill(String(puzzle.correctAnswer));
      await page.locator('[data-testid="submit-btn"]').click();
    } else {
      await page.locator(`[data-testid="choice-btn"][data-choice="${puzzle.correctAnswer}"]`).click();
    }
    await page.locator('[data-testid="next-btn"]').click();
  }
  await expect(page.locator('[data-testid="daily-share-box"]')).toBeVisible();
  await page.locator('[data-testid="back-to-menu-btn"]').click();
  await expect(page.locator('[data-testid="daily-done-note"]')).toBeVisible();

  await page.locator('[data-testid="menu-daily-btn"]').click();
  // Re-opening the Daily Challenge after completion shows the same results,
  // not a fresh puzzle screen.
  await expect(page.locator('[data-testid="daily-share-box"]')).toBeVisible();
  await expect(page.locator('[data-testid="question-text"]')).toHaveCount(0);
});

test('two independently seeded runs of the same UTC date produce an identical Daily Challenge puzzle set', async ({ page }) => {
  const setA = await page.evaluate(() => {
    const rng = TC.mulberry32(TC.dailySeed('2026-09-07'));
    const order = [];
    for (let i = 0; i < 5; i++) order.push(TC.CHAPTER_ORDER[i % TC.CHAPTER_ORDER.length]);
    return order.map((t) => JSON.stringify(TC.generatePuzzle(t, rng).params));
  });
  const setB = await page.evaluate(() => {
    const rng = TC.mulberry32(TC.dailySeed('2026-09-07'));
    const order = [];
    for (let i = 0; i < 5; i++) order.push(TC.CHAPTER_ORDER[i % TC.CHAPTER_ORDER.length]);
    return order.map((t) => JSON.stringify(TC.generatePuzzle(t, rng).params));
  });
  expect(setA).toEqual(setB);
});

test('the mastery dashboard reflects attempts and accuracy after play', async ({ page }) => {
  await page.locator('[data-testid="menu-voyage-btn"]').click();
  for (let i = 0; i < 6; i++) {
    await answerChoicePuzzle(page, { correct: true });
    await page.locator('[data-testid="next-btn"]').click();
  }
  await page.locator('[data-testid="back-to-menu-btn"]').click();
  await page.locator('[data-testid="menu-dashboard-btn"]').click();
  const buoyageRow = page.locator('tr', { hasText: 'Buoyage' });
  await expect(buoyageRow.locator('td').nth(1)).toHaveText('6');
  await expect(buoyageRow.locator('td').nth(2)).toHaveText('100%');
});

test('the back-to-menu button returns to the main menu from the dashboard', async ({ page }) => {
  await page.locator('[data-testid="menu-dashboard-btn"]').click();
  await expect(page.locator('[data-testid="dashboard-table"]')).toBeVisible();
  await page.locator('[data-testid="back-to-menu-btn"]').click();
  await expect(page.locator('[data-testid="menu-voyage-btn"]')).toBeVisible();
});
