const { test, expect } = require('@playwright/test');
const path = require('path');

const INDEX = 'file://' + path.resolve(__dirname, '..', 'index.html');

// ─── SM-2 Algorithm Tests ────────────────────────────────────────────────────
// These tests call window.SM2 directly via page.evaluate() to verify
// the algorithm produces correct outputs without relying on UI state.

test('SM2: rating 0 (Again) resets repetitions to 0', async ({ page }) => {
  await page.goto(INDEX);
  const result = await page.evaluate(() => {
    const state = { ef: 2.5, interval: 6, repetitions: 2, due: '2026-06-10', lastRating: 3 };
    return window.SM2.update(state, 0).repetitions;
  });
  expect(result).toBe(0);
});

test('SM2: rating 0 (Again) resets interval to 1', async ({ page }) => {
  await page.goto(INDEX);
  const result = await page.evaluate(() => {
    const state = { ef: 2.5, interval: 14, repetitions: 3, due: '2026-06-10', lastRating: 3 };
    return window.SM2.update(state, 0).interval;
  });
  expect(result).toBe(1);
});

test('SM2: rating 3 (Good) on first repetition sets interval to 1', async ({ page }) => {
  await page.goto(INDEX);
  const result = await page.evaluate(() => {
    const state = window.SM2.newCard();
    const updated = window.SM2.update(state, 3);
    return { interval: updated.interval, repetitions: updated.repetitions };
  });
  expect(result.interval).toBe(1);
  expect(result.repetitions).toBe(1);
});

test('SM2: rating 3 (Good) on second repetition sets interval to 6', async ({ page }) => {
  await page.goto(INDEX);
  const result = await page.evaluate(() => {
    const state = { ef: 2.36, interval: 1, repetitions: 1, due: '2026-06-17', lastRating: 3 };
    const updated = window.SM2.update(state, 3);
    return { interval: updated.interval, repetitions: updated.repetitions };
  });
  expect(result.interval).toBe(6);
  expect(result.repetitions).toBe(2);
});

test('SM2: rating 3 (Good) on third+ repetition multiplies interval by EF', async ({ page }) => {
  await page.goto(INDEX);
  const result = await page.evaluate(() => {
    const state = { ef: 2.36, interval: 6, repetitions: 2, due: '2026-06-23', lastRating: 3 };
    return window.SM2.update(state, 3).interval;
  });
  // interval = Math.round(6 * 2.36) = Math.round(14.16) = 14
  expect(result).toBe(14);
});

test('SM2: rating 5 (Easy) increases EF by 0.1', async ({ page }) => {
  await page.goto(INDEX);
  const result = await page.evaluate(() => {
    const state = window.SM2.newCard(); // ef starts at 2.5
    return window.SM2.update(state, 5).ef;
  });
  // ef = 2.5 + 0.1 - 0*(0.08+0) = 2.6
  expect(result).toBeCloseTo(2.6, 2);
});

test('SM2: rating 0 (Again) decreases EF significantly', async ({ page }) => {
  await page.goto(INDEX);
  const result = await page.evaluate(() => {
    const state = { ef: 2.5, interval: 1, repetitions: 0, due: '2026-06-16', lastRating: null };
    return window.SM2.update(state, 0).ef;
  });
  // ef = 2.5 + 0.1 - 5*(0.08+5*0.02) = 2.5 + 0.1 - 0.9 = 1.7
  expect(result).toBeCloseTo(1.7, 2);
});

test('SM2: EF never drops below the 1.3 floor', async ({ page }) => {
  await page.goto(INDEX);
  const result = await page.evaluate(() => {
    const state = { ef: 1.3, interval: 1, repetitions: 0, due: '2026-06-16', lastRating: null };
    return window.SM2.update(state, 0).ef;
  });
  // Without floor: 1.3 + 0.1 - 0.9 = 0.5; floored to 1.3
  expect(result).toBe(1.3);
});

test('SM2: isDue returns true when due date is today', async ({ page }) => {
  await page.goto(INDEX);
  const result = await page.evaluate(() => {
    const today = window.SM2.todayStr();
    return window.SM2.isDue({ ef: 2.5, interval: 1, repetitions: 0, due: today, lastRating: null });
  });
  expect(result).toBe(true);
});

test('SM2: isDue returns false when due date is in the future', async ({ page }) => {
  await page.goto(INDEX);
  const result = await page.evaluate(() => {
    return window.SM2.isDue({ ef: 2.5, interval: 14, repetitions: 2, due: '2099-01-01', lastRating: 3 });
  });
  expect(result).toBe(false);
});

test('SM2: isNew returns true for a card that has never been rated', async ({ page }) => {
  await page.goto(INDEX);
  const result = await page.evaluate(() => {
    return window.SM2.isNew(window.SM2.newCard());
  });
  expect(result).toBe(true);
});

test('SM2: isNew returns false after any rating', async ({ page }) => {
  await page.goto(INDEX);
  const result = await page.evaluate(() => {
    const updated = window.SM2.update(window.SM2.newCard(), 3);
    return window.SM2.isNew(updated);
  });
  expect(result).toBe(false);
});

// ─── UI Tests ────────────────────────────────────────────────────────────────

test('page loads without console errors', async ({ page }) => {
  const errors = [];
  page.on('pageerror', err => errors.push(err.message));
  await page.goto(INDEX);
  await page.waitForLoadState('domcontentloaded');
  expect(errors).toHaveLength(0);
});

test('three deck tabs are visible', async ({ page }) => {
  await page.goto(INDEX);
  const tabs = page.locator('.deck-tab');
  await expect(tabs).toHaveCount(3);
  await expect(page.locator('[data-testid="deck-tab-bayesian"]')).toBeVisible();
  await expect(page.locator('[data-testid="deck-tab-python"]')).toBeVisible();
  await expect(page.locator('[data-testid="deck-tab-git"]')).toBeVisible();
});

test('stats bar shows due and new counts', async ({ page }) => {
  await page.goto(INDEX);
  await expect(page.locator('[data-testid="stats-bar"]')).toBeVisible();
  await expect(page.locator('[data-testid="stat-due"]')).toBeVisible();
  await expect(page.locator('[data-testid="stat-new"]')).toBeVisible();
});

test('"Show Answer" button is visible when viewing a card front', async ({ page }) => {
  await page.goto(INDEX);
  await expect(page.locator('[data-testid="reveal-btn"]')).toBeVisible();
  await expect(page.locator('[data-testid="card-front"]')).not.toBeEmpty();
});

test('clicking "Show Answer" reveals the card back', async ({ page }) => {
  await page.goto(INDEX);
  await expect(page.locator('[data-testid="card-back"]')).toBeHidden();
  await page.locator('[data-testid="reveal-btn"]').click();
  await expect(page.locator('[data-testid="card-back"]')).toBeVisible();
  await expect(page.locator('[data-testid="card-back"]')).not.toBeEmpty();
});

test('four rating buttons are visible after revealing the answer', async ({ page }) => {
  await page.goto(INDEX);
  await page.locator('[data-testid="reveal-btn"]').click();
  await expect(page.locator('[data-testid="rating-buttons"]')).toBeVisible();
  await expect(page.locator('[data-testid="btn-again"]')).toBeVisible();
  await expect(page.locator('[data-testid="btn-hard"]')).toBeVisible();
  await expect(page.locator('[data-testid="btn-good"]')).toBeVisible();
  await expect(page.locator('[data-testid="btn-easy"]')).toBeVisible();
});

test('clicking "Good" advances to the next card', async ({ page }) => {
  await page.goto(INDEX);
  const firstFront = await page.locator('[data-testid="card-front"]').textContent();
  await page.locator('[data-testid="reveal-btn"]').click();
  await page.locator('[data-testid="btn-good"]').click();
  // After rating, either a new card is shown (different front) or the done screen appears
  const doneVisible = await page.locator('[data-testid="done-screen"]').isVisible();
  if (!doneVisible) {
    const secondFront = await page.locator('[data-testid="card-front"]').textContent();
    expect(secondFront).not.toBe(firstFront);
  }
  // Either way the "done" count should have incremented to 1
  await expect(page.locator('[data-testid="stat-done"]')).toHaveText('1');
});

test('switching deck tabs loads the selected deck', async ({ page }) => {
  await page.goto(INDEX);
  const firstFront = await page.locator('[data-testid="card-front"]').textContent();
  // Switch to Git deck
  await page.locator('[data-testid="deck-tab-git"]').click();
  const gitFront = await page.locator('[data-testid="card-front"]').textContent();
  expect(gitFront).not.toBe(firstFront);
  // Switch to Python deck
  await page.locator('[data-testid="deck-tab-python"]').click();
  const pyFront = await page.locator('[data-testid="card-front"]').textContent();
  expect(pyFront).not.toBe(firstFront);
  expect(pyFront).not.toBe(gitFront);
});

test('done screen appears when all deck cards are scheduled for the future', async ({ page }) => {
  await page.goto(INDEX);
  // Pre-mark all bayesian cards as reviewed with future due dates
  await page.evaluate(() => {
    const state = {};
    for (const card of window.DECKS.bayesian.cards) {
      state['bayesian::' + card.id] = {
        ef: 2.5, interval: 30, repetitions: 3, due: '2099-01-01', lastRating: 3
      };
    }
    localStorage.setItem('srf_state_v1', JSON.stringify(state));
  });
  await page.reload();
  await expect(page.locator('[data-testid="done-screen"]')).toBeVisible();
  await expect(page.locator('[data-testid="done-screen"] h2')).toBeVisible();
});

test('page has a dark background', async ({ page }) => {
  await page.goto(INDEX);
  const bg = await page.evaluate(() => getComputedStyle(document.body).backgroundColor);
  // Parse rgb(r, g, b)
  const nums = bg.match(/\d+/g).map(Number);
  const sum = nums[0] + nums[1] + nums[2];
  // Dark theme: r+g+b well below 200
  expect(sum).toBeLessThan(100);
});

test('no horizontal overflow at 375px mobile width', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto(INDEX);
  const overflow = await page.evaluate(() => document.body.scrollWidth > window.innerWidth);
  expect(overflow).toBe(false);
});
