const { test, expect } = require('@playwright/test');
const path = require('path');

const INDEX_URL = `file://${path.resolve(__dirname, '../index.html')}`;

/* Clear localStorage before every test for a clean slate */
test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => localStorage.clear());
  await page.goto(INDEX_URL);
});

/* ================================================================
   1 — Page load & initial state
================================================================ */
test('page loads with correct title', async ({ page }) => {
  await expect(page).toHaveTitle('Regex Dojo');
});

test('level select view is shown on initial load', async ({ page }) => {
  const selectView = page.locator('[data-testid="view-select"]');
  await expect(selectView).toBeVisible();
  const gameView = page.locator('[data-testid="view-game"]');
  await expect(gameView).not.toBeVisible();
});

test('progress shows 0 / 20 complete on fresh load', async ({ page }) => {
  const progress = page.locator('[data-testid="total-progress"]');
  await expect(progress).toHaveText('0 / 20 complete');
});

test('level grid shows 20 level cards', async ({ page }) => {
  const cards = page.locator('[data-testid^="level-card-"]');
  await expect(cards).toHaveCount(20);
});

test('level 1 card is unlocked (clickable)', async ({ page }) => {
  const card1 = page.locator('[data-testid="level-card-1"]');
  await expect(card1).not.toHaveClass(/locked/);
});

test('level 2 card is locked on fresh load', async ({ page }) => {
  const card2 = page.locator('[data-testid="level-card-2"]');
  await expect(card2).toHaveClass(/locked/);
});

/* ================================================================
   2 — Navigating to a level
================================================================ */
test('clicking level 1 shows the game view', async ({ page }) => {
  await page.locator('[data-testid="level-card-1"]').click();
  const gameView = page.locator('[data-testid="view-game"]');
  await expect(gameView).toBeVisible();
});

test('game view shows correct level title for level 1', async ({ page }) => {
  await page.locator('[data-testid="level-card-1"]').click();
  const title = page.locator('[data-testid="level-title"]');
  await expect(title).toHaveText('Find the Greeting');
});

test('game view shows concept badge for level 1', async ({ page }) => {
  await page.locator('[data-testid="level-card-1"]').click();
  const badge = page.locator('[data-testid="concept-badge"]');
  await expect(badge).toHaveText('Literal Match');
});

test('game view shows level description', async ({ page }) => {
  await page.locator('[data-testid="level-card-1"]').click();
  const desc = page.locator('[data-testid="level-desc"]');
  await expect(desc).not.toBeEmpty();
});

test('match strings container is visible in game view', async ({ page }) => {
  await page.locator('[data-testid="level-card-1"]').click();
  const rows = page.locator('[data-testid="rows-match"]');
  await expect(rows).toBeVisible();
});

test('reject strings container is visible in game view', async ({ page }) => {
  await page.locator('[data-testid="level-card-1"]').click();
  const rows = page.locator('[data-testid="rows-reject"]');
  await expect(rows).toBeVisible();
});

/* ================================================================
   3 — Regex input and feedback
================================================================ */
test('submit button is disabled when regex input is empty', async ({ page }) => {
  await page.locator('[data-testid="level-card-1"]').click();
  const submitBtn = page.locator('[data-testid="btn-submit"]');
  await expect(submitBtn).toBeDisabled();
});

test('typing a wrong regex keeps submit disabled', async ({ page }) => {
  await page.locator('[data-testid="level-card-1"]').click();
  await page.locator('[data-testid="regex-input"]').fill('world');
  const submitBtn = page.locator('[data-testid="btn-submit"]');
  await expect(submitBtn).toBeDisabled();
});

test('correct regex for level 1 enables submit button', async ({ page }) => {
  await page.locator('[data-testid="level-card-1"]').click();
  await page.locator('[data-testid="regex-input"]').fill('hello');
  const submitBtn = page.locator('[data-testid="btn-submit"]');
  await expect(submitBtn).toBeEnabled();
});

test('correct regex for level 1 shows passing indicators on match rows', async ({ page }) => {
  await page.locator('[data-testid="level-card-1"]').click();
  await page.locator('[data-testid="regex-input"]').fill('hello');
  /* Level 1 has 4 match strings — all should show ✓ */
  const ind0 = page.locator('[data-testid="ind-match-0"]');
  await expect(ind0).toHaveText('✓');
});

test('correct regex for level 1 shows passing indicators on reject rows', async ({ page }) => {
  await page.locator('[data-testid="level-card-1"]').click();
  await page.locator('[data-testid="regex-input"]').fill('hello');
  /* Reject strings should show ✓ (meaning the pattern correctly rejects them) */
  const ind0 = page.locator('[data-testid="ind-reject-0"]');
  await expect(ind0).toHaveText('✓');
});

test('invalid regex shows error message', async ({ page }) => {
  await page.locator('[data-testid="level-card-1"]').click();
  await page.locator('[data-testid="regex-input"]').fill('[invalid');
  const errorEl = page.locator('[data-testid="regex-error"]');
  await expect(errorEl).not.toBeEmpty();
});

test('invalid regex keeps submit button disabled', async ({ page }) => {
  await page.locator('[data-testid="level-card-1"]').click();
  await page.locator('[data-testid="regex-input"]').fill('[unclosed');
  const submitBtn = page.locator('[data-testid="btn-submit"]');
  await expect(submitBtn).toBeDisabled();
});

/* ================================================================
   4 — Hint button
================================================================ */
test('hint text is not visible initially', async ({ page }) => {
  await page.locator('[data-testid="level-card-1"]').click();
  const hint = page.locator('[data-testid="hint-text"]');
  await expect(hint).not.toBeVisible();
});

test('clicking hint button shows hint text', async ({ page }) => {
  await page.locator('[data-testid="level-card-1"]').click();
  await page.locator('[data-testid="btn-hint"]').click();
  const hint = page.locator('[data-testid="hint-text"]');
  await expect(hint).toBeVisible();
});

test('clicking hint button again hides hint text', async ({ page }) => {
  await page.locator('[data-testid="level-card-1"]').click();
  await page.locator('[data-testid="btn-hint"]').click();
  await page.locator('[data-testid="btn-hint"]').click();
  const hint = page.locator('[data-testid="hint-text"]');
  await expect(hint).not.toBeVisible();
});

/* ================================================================
   5 — Level completion flow
================================================================ */
test('submitting correct answer shows success banner', async ({ page }) => {
  await page.locator('[data-testid="level-card-1"]').click();
  await page.locator('[data-testid="regex-input"]').fill('hello');
  await page.locator('[data-testid="btn-submit"]').click();
  const banner = page.locator('[data-testid="success-banner"]');
  await expect(banner).toBeVisible();
});

test('success banner contains a next level button', async ({ page }) => {
  await page.locator('[data-testid="level-card-1"]').click();
  await page.locator('[data-testid="regex-input"]').fill('hello');
  await page.locator('[data-testid="btn-submit"]').click();
  const nextBtn = page.locator('[data-testid="btn-next"]');
  await expect(nextBtn).toBeVisible();
});

test('clicking next level advances to level 2', async ({ page }) => {
  await page.locator('[data-testid="level-card-1"]').click();
  await page.locator('[data-testid="regex-input"]').fill('hello');
  await page.locator('[data-testid="btn-submit"]').click();
  await page.locator('[data-testid="btn-next"]').click();
  const title = page.locator('[data-testid="level-title"]');
  await expect(title).toHaveText('Vowel Starter');
});

test('progress counter increments after completing level 1', async ({ page }) => {
  await page.locator('[data-testid="level-card-1"]').click();
  await page.locator('[data-testid="regex-input"]').fill('hello');
  await page.locator('[data-testid="btn-submit"]').click();
  const progress = page.locator('[data-testid="progress"]');
  await expect(progress).toHaveText('1 / 20');
});

/* ================================================================
   6 — Back to menu and persistence
================================================================ */
test('back to levels button shows the level select view', async ({ page }) => {
  await page.locator('[data-testid="level-card-1"]').click();
  await page.locator('[data-testid="btn-menu"]').click();
  const selectView = page.locator('[data-testid="view-select"]');
  await expect(selectView).toBeVisible();
});

test('completing level 1 and returning to menu shows updated progress', async ({ page }) => {
  await page.locator('[data-testid="level-card-1"]').click();
  await page.locator('[data-testid="regex-input"]').fill('hello');
  await page.locator('[data-testid="btn-submit"]').click();
  await page.locator('[data-testid="btn-menu"]').click();
  const totalProgress = page.locator('[data-testid="total-progress"]');
  await expect(totalProgress).toHaveText('1 / 20 complete');
});

test('completed level 1 shows complete styling in level select', async ({ page }) => {
  await page.locator('[data-testid="level-card-1"]').click();
  await page.locator('[data-testid="regex-input"]').fill('hello');
  await page.locator('[data-testid="btn-submit"]').click();
  await page.locator('[data-testid="btn-menu"]').click();
  const card1 = page.locator('[data-testid="level-card-1"]');
  await expect(card1).toHaveClass(/complete/);
});

test('completing level 1 unlocks level 2 in the select view', async ({ page }) => {
  await page.locator('[data-testid="level-card-1"]').click();
  await page.locator('[data-testid="regex-input"]').fill('hello');
  await page.locator('[data-testid="btn-submit"]').click();
  await page.locator('[data-testid="btn-menu"]').click();
  const card2 = page.locator('[data-testid="level-card-2"]');
  await expect(card2).not.toHaveClass(/locked/);
});

/* ================================================================
   7 — Level 2 correctness
================================================================ */
test('correct regex for level 2 enables submit', async ({ page }) => {
  /* Complete level 1 first to unlock level 2 */
  await page.locator('[data-testid="level-card-1"]').click();
  await page.locator('[data-testid="regex-input"]').fill('hello');
  await page.locator('[data-testid="btn-submit"]').click();
  await page.locator('[data-testid="btn-next"]').click();

  /* Now on level 2 */
  await page.locator('[data-testid="regex-input"]').fill('^[aeiou]');
  const submitBtn = page.locator('[data-testid="btn-submit"]');
  await expect(submitBtn).toBeEnabled();
});

test('partial regex for level 1 does not enable submit', async ({ page }) => {
  await page.locator('[data-testid="level-card-1"]').click();
  /* 'helo' matches some strings but not all — also won't match 'hello' */
  await page.locator('[data-testid="regex-input"]').fill('helo');
  const submitBtn = page.locator('[data-testid="btn-submit"]');
  await expect(submitBtn).toBeDisabled();
});

test('level 2 shows different content from level 1', async ({ page }) => {
  /* Complete level 1 to unlock level 2 */
  await page.locator('[data-testid="level-card-1"]').click();
  await page.locator('[data-testid="regex-input"]').fill('hello');
  await page.locator('[data-testid="btn-submit"]').click();
  await page.locator('[data-testid="btn-next"]').click();
  const title = page.locator('[data-testid="level-title"]');
  await expect(title).not.toHaveText('Find the Greeting');
});
