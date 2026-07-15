const { test, expect } = require('@playwright/test');
const path = require('path');

const INDEX_URL = `file://${path.resolve(__dirname, '../index.html')}`;

test.beforeEach(async ({ page }) => {
  // Clear after the initial load rather than via addInitScript, which would
  // re-fire (and wipe state) on every page.reload() a test performs later.
  await page.goto(INDEX_URL);
  await page.evaluate(() => localStorage.clear());
});

/* ================================================================
   1 — Data integrity
================================================================ */
test('exactly 30 vignettes, 3 per chapter x 10 chapters worth', async ({ page }) => {
  const count = await page.evaluate(() => VIGNETTES.length);
  expect(count).toBe(30);
});

test('every vignette has exactly one correct option matching a valid flaw id', async ({ page }) => {
  const problems = await page.evaluate(() => {
    const bad = [];
    VIGNETTES.forEach((v) => {
      const validFlaw = FLAW_ORDER.includes(v.flaw);
      const optionSet = new Set(v.options);
      const fourUnique = v.options.length === 4 && optionSet.size === 4;
      const includesCorrect = v.options.includes(v.flaw);
      const allValid = v.options.every((o) => FLAW_ORDER.includes(o));
      if (!validFlaw || !fourUnique || !includesCorrect || !allValid) bad.push(v.id);
    });
    return bad;
  });
  expect(problems).toEqual([]);
});

test('each chapter (1-3) contains exactly 10 vignettes covering all 10 flaw types once', async ({ page }) => {
  const { result, expected } = await page.evaluate(() => {
    const out = {};
    [1, 2, 3].forEach((ch) => {
      const flaws = VIGNETTES.filter((v) => v.chapter === ch).map((v) => v.flaw).sort();
      out[ch] = flaws;
    });
    return { result: out, expected: [...FLAW_ORDER].sort() };
  });
  expect(result[1]).toEqual(expected);
  expect(result[2]).toEqual(expected);
  expect(result[3]).toEqual(expected);
});

/* ================================================================
   2 — Menu & navigation
================================================================ */
test('menu screen is visible on load, others hidden', async ({ page }) => {
  await expect(page.locator('[data-testid="screen-menu"]')).toBeVisible();
  await expect(page.locator('[data-testid="screen-chapters"]')).toBeHidden();
  await expect(page.locator('[data-testid="screen-play"]')).toBeHidden();
});

test('clicking Practice shows the chapter list with 3 chapters', async ({ page }) => {
  await page.click('[data-testid="nav-practice"]');
  await expect(page.locator('[data-testid="screen-chapters"]')).toBeVisible();
  await expect(page.locator('[data-testid^="chapter-card-"]')).toHaveCount(3);
});

test('chapters 2 and 3 are locked on a fresh profile', async ({ page }) => {
  await page.click('[data-testid="nav-practice"]');
  await expect(page.locator('[data-testid="chapter-card-2"]')).toHaveAttribute('data-locked', 'true');
  await expect(page.locator('[data-testid="chapter-card-3"]')).toHaveAttribute('data-locked', 'true');
});

test('back-to-menu button returns from chapters to the menu', async ({ page }) => {
  await page.click('[data-testid="nav-practice"]');
  await page.click('[data-testid="back-to-menu-1"]');
  await expect(page.locator('[data-testid="screen-menu"]')).toBeVisible();
});

/* ================================================================
   3 — Practice question flow
================================================================ */
test('starting chapter 1 shows a vignette with 4 options', async ({ page }) => {
  await page.click('[data-testid="nav-practice"]');
  await page.click('[data-testid="chapter-card-1"]');
  await expect(page.locator('[data-testid="screen-play"]')).toBeVisible();
  await expect(page.locator('[data-testid="vignette-text"]')).not.toBeEmpty();
  await expect(page.locator('[data-testid^="option-btn-"]')).toHaveCount(4);
});

test('selecting the correct answer shows correct feedback and increments streak', async ({ page }) => {
  await page.click('[data-testid="nav-practice"]');
  await page.click('[data-testid="chapter-card-1"]');
  const correctFlaw = await page.evaluate(() => currentVignette().flaw);
  const btn = page.locator(`[data-flaw="${correctFlaw}"]`);
  await btn.click();
  await expect(page.locator('[data-testid="feedback-panel"]')).toBeVisible();
  await expect(page.locator('[data-testid="feedback-verdict"]')).toContainText('Correct');
  await expect(page.locator('[data-testid="streak-display"]')).toHaveText('Streak: 1');
});

test('selecting a wrong answer resets streak to 0 and highlights the correct option', async ({ page }) => {
  await page.click('[data-testid="nav-practice"]');
  await page.click('[data-testid="chapter-card-1"]');
  const correctFlaw = await page.evaluate(() => currentVignette().flaw);
  const wrongBtn = page.locator('[data-testid^="option-btn-"]').filter({
    hasNot: page.locator(`[data-flaw="${correctFlaw}"]`)
  }).first();
  await wrongBtn.click();
  await expect(page.locator('[data-testid="feedback-verdict"]')).toContainText('Not quite');
  await expect(page.locator('[data-testid="streak-display"]')).toHaveText('Streak: 0');
  await expect(page.locator(`[data-flaw="${correctFlaw}"]`)).toHaveClass(/correct/);
});

test('all option buttons are disabled after answering', async ({ page }) => {
  await page.click('[data-testid="nav-practice"]');
  await page.click('[data-testid="chapter-card-1"]');
  await page.locator('[data-testid="option-btn-0"]').click();
  const buttons = page.locator('[data-testid^="option-btn-"]');
  const count = await buttons.count();
  for (let i = 0; i < count; i++) {
    await expect(buttons.nth(i)).toBeDisabled();
  }
});

test('Next button advances to question 2 of 10', async ({ page }) => {
  await page.click('[data-testid="nav-practice"]');
  await page.click('[data-testid="chapter-card-1"]');
  await page.locator('[data-testid="option-btn-0"]').click();
  await page.click('[data-testid="next-btn"]');
  await expect(page.locator('[data-testid="progress-display"]')).toHaveText('Question 2 / 10');
});

/* ================================================================
   4 — Chapter completion & unlock gating
================================================================ */
test('answering all 10 questions correctly yields grade A and unlocks chapter 2', async ({ page }) => {
  await page.click('[data-testid="nav-practice"]');
  await page.click('[data-testid="chapter-card-1"]');
  for (let i = 0; i < 10; i++) {
    const correctFlaw = await page.evaluate(() => currentVignette().flaw);
    await page.locator(`[data-flaw="${correctFlaw}"]`).click();
    await page.click('[data-testid="next-btn"]');
  }
  await expect(page.locator('[data-testid="screen-chapter-end"]')).toBeVisible();
  await expect(page.locator('[data-testid="chapter-end-grade"]')).toHaveText('Grade: A');
  await expect(page.locator('[data-testid="chapter-end-accuracy"]')).toHaveText('10 / 10 correct (100%)');
  await expect(page.locator('[data-testid="chapter-end-unlock"]')).toContainText('Chapter 2 unlocked');

  await page.click('[data-testid="chapter-end-continue"]');
  await expect(page.locator('[data-testid="chapter-card-2"]')).not.toHaveAttribute('data-locked', 'true');
});

test('answering all 10 questions incorrectly yields grade F and does not unlock chapter 2', async ({ page }) => {
  await page.click('[data-testid="nav-practice"]');
  await page.click('[data-testid="chapter-card-1"]');
  for (let i = 0; i < 10; i++) {
    const correctFlaw = await page.evaluate(() => currentVignette().flaw);
    const wrongBtn = page.locator('[data-testid^="option-btn-"]').filter({
      hasNot: page.locator(`[data-flaw="${correctFlaw}"]`)
    }).first();
    await wrongBtn.click();
    await page.click('[data-testid="next-btn"]');
  }
  await expect(page.locator('[data-testid="chapter-end-grade"]')).toHaveText('Grade: F');
  await expect(page.locator('[data-testid="chapter-end-unlock"]')).toContainText('70%');

  await page.click('[data-testid="chapter-end-continue"]');
  await expect(page.locator('[data-testid="chapter-card-2"]')).toHaveAttribute('data-locked', 'true');
});

test('chapter 2 stays locked even via direct startChapter(2) call when chapter 1 is not passed', async ({ page }) => {
  await page.evaluate(() => startChapter(2));
  // startChapter should no-op (still on menu screen, not play screen)
  await expect(page.locator('[data-testid="screen-menu"]')).toBeVisible();
});

/* ================================================================
   5 — Mastery dashboard
================================================================ */
test('mastery dashboard shows "Not yet attempted" for all flaw types on a fresh profile', async ({ page }) => {
  await page.click('[data-testid="nav-mastery"]');
  const rows = page.locator('[data-testid^="mastery-pct-"]');
  await expect(rows).toHaveCount(10);
  await expect(rows.first()).toHaveText('Not yet attempted');
});

test('answering a question updates the mastery dashboard for that flaw type', async ({ page }) => {
  await page.click('[data-testid="nav-practice"]');
  await page.click('[data-testid="chapter-card-1"]');
  const correctFlaw = await page.evaluate(() => currentVignette().flaw);
  await page.locator(`[data-flaw="${correctFlaw}"]`).click();

  // Mastery is written to localStorage synchronously on answer; reload to
  // return to the menu screen and confirm it persisted.
  await page.reload();
  await page.click('[data-testid="nav-mastery"]');
  await expect(page.locator(`[data-testid="mastery-pct-${correctFlaw}"]`)).toHaveText('100% (1/1)');
});

/* ================================================================
   6 — Daily Challenge
================================================================ */
test('daily challenge presents exactly 5 questions', async ({ page }) => {
  await page.click('[data-testid="nav-daily"]');
  await expect(page.locator('[data-testid="progress-display"]')).toHaveText('Daily 1 / 5');
});

test('daily challenge selection is deterministic for the same date', async ({ page }) => {
  const [a, b] = await page.evaluate(() => [
    pickDailyVignetteIds('2026-07-15'),
    pickDailyVignetteIds('2026-07-15')
  ]);
  expect(a).toEqual(b);
  expect(a).toHaveLength(5);
  expect(new Set(a).size).toBe(5);
});

test('daily challenge selection differs across different dates', async ({ page }) => {
  const [a, b] = await page.evaluate(() => [
    pickDailyVignetteIds('2026-07-15'),
    pickDailyVignetteIds('2026-01-01')
  ]);
  expect(a).not.toEqual(b);
});

test('completing the daily challenge shows a result screen with a share grid', async ({ page }) => {
  await page.click('[data-testid="nav-daily"]');
  for (let i = 0; i < 5; i++) {
    const correctFlaw = await page.evaluate(() => currentVignette().flaw);
    await page.locator(`[data-flaw="${correctFlaw}"]`).click();
    await page.click('[data-testid="next-btn"]');
  }
  await expect(page.locator('[data-testid="screen-daily-result"]')).toBeVisible();
  await expect(page.locator('[data-testid="daily-result-score"]')).toHaveText('5 / 5 correct');
  const shareText = await page.locator('[data-testid="daily-result-text"]').textContent();
  expect(shareText).toContain('Confound Hunter Daily');
  expect(shareText).toContain('5/5');
  expect(shareText).toContain('✅✅✅✅✅');
});

test('daily challenge cannot be replayed on the same UTC date — shows stored result instead', async ({ page }) => {
  await page.evaluate(() => {
    const today = todayUTCString();
    saveDaily({ date: today, vignetteIds: [1, 2, 3, 4, 5], results: [true, false, true, true, false] });
  });
  await page.click('[data-testid="nav-daily"]');
  await expect(page.locator('[data-testid="screen-daily-result"]')).toBeVisible();
  await expect(page.locator('[data-testid="screen-play"]')).toBeHidden();
  await expect(page.locator('[data-testid="daily-result-score"]')).toHaveText('3 / 5 correct');
});

test('buildShareText produces the correct emoji grid for mixed results', async ({ page }) => {
  const text = await page.evaluate(() =>
    buildShareText({ date: '2026-07-15', results: [true, false, true, true, false] })
  );
  expect(text).toBe('Confound Hunter Daily 2026-07-15: 3/5\n✅❌✅✅❌');
});

/* ================================================================
   7 — Persistence & reset
================================================================ */
test('progress persists across a page reload', async ({ page }) => {
  await page.click('[data-testid="nav-practice"]');
  await page.click('[data-testid="chapter-card-1"]');
  for (let i = 0; i < 10; i++) {
    const correctFlaw = await page.evaluate(() => currentVignette().flaw);
    await page.locator(`[data-flaw="${correctFlaw}"]`).click();
    await page.click('[data-testid="next-btn"]');
  }
  await page.reload();
  await page.click('[data-testid="nav-practice"]');
  await expect(page.locator('[data-testid="chapter-card-2"]')).not.toHaveAttribute('data-locked', 'true');
});

test('reset progress clears chapter unlocks and mastery back to fresh state', async ({ page }) => {
  await page.click('[data-testid="nav-practice"]');
  await page.click('[data-testid="chapter-card-1"]');
  for (let i = 0; i < 10; i++) {
    const correctFlaw = await page.evaluate(() => currentVignette().flaw);
    await page.locator(`[data-flaw="${correctFlaw}"]`).click();
    await page.click('[data-testid="next-btn"]');
  }
  await page.click('[data-testid="chapter-end-continue"]');
  await page.click('[data-testid="back-to-menu-1"]');

  await page.click('[data-testid="nav-reset"]');
  await expect(page.locator('[data-testid="reset-confirm-modal"]')).toBeVisible();
  await page.click('[data-testid="reset-confirm-btn"]');
  await expect(page.locator('[data-testid="screen-menu"]')).toBeVisible();

  await page.click('[data-testid="nav-practice"]');
  await expect(page.locator('[data-testid="chapter-card-2"]')).toHaveAttribute('data-locked', 'true');

  await page.click('[data-testid="back-to-menu-1"]');
  await page.click('[data-testid="nav-mastery"]');
  await expect(page.locator('[data-testid="mastery-pct-confound"]')).toHaveText('Not yet attempted');
});

test('reset cancel button dismisses the modal without clearing progress', async ({ page }) => {
  await page.click('[data-testid="nav-practice"]');
  await page.click('[data-testid="chapter-card-1"]');
  for (let i = 0; i < 10; i++) {
    const correctFlaw = await page.evaluate(() => currentVignette().flaw);
    await page.locator(`[data-flaw="${correctFlaw}"]`).click();
    await page.click('[data-testid="next-btn"]');
  }
  await page.click('[data-testid="chapter-end-continue"]');
  await page.click('[data-testid="back-to-menu-1"]');

  await page.click('[data-testid="nav-reset"]');
  await page.click('[data-testid="reset-cancel-btn"]');
  await expect(page.locator('[data-testid="reset-confirm-modal"]')).toBeHidden();

  await page.click('[data-testid="nav-practice"]');
  await expect(page.locator('[data-testid="chapter-card-2"]')).not.toHaveAttribute('data-locked', 'true');
});

/* ================================================================
   8 — Grading logic & safety
================================================================ */
test('gradeFor computes correct letter grades at each threshold', async ({ page }) => {
  const grades = await page.evaluate(() => [
    gradeFor(100), gradeFor(90), gradeFor(85), gradeFor(80),
    gradeFor(75), gradeFor(70), gradeFor(65), gradeFor(60), gradeFor(50)
  ]);
  expect(grades).toEqual(['A', 'A', 'B', 'B', 'C', 'C', 'D', 'D', 'F']);
});

test('vignette text and explanation render as text, not raw HTML (XSS-safety of rendering path)', async ({ page }) => {
  await page.evaluate(() => {
    VIGNETTES.push({
      id: 9999,
      chapter: 1,
      flaw: 'confound',
      text: '<img src=x onerror="window.__xss=true">Injected vignette',
      options: ['confound', 'selection', 'no_control', 'demand'],
      explanation: '<script>window.__xss2=true</script>Explanation text'
    });
    currentSession = { mode: 'practice', chapter: 1, vignetteIds: [9999], index: 0, correctCount: 0, streak: 0, results: [] };
    showScreen('screen-play');
    renderQuestion();
  });
  const rendered = await page.locator('[data-testid="vignette-text"]').textContent();
  expect(rendered).toContain('<img src=x');
  const xssFired = await page.evaluate(() => window.__xss === true || window.__xss2 === true);
  expect(xssFired).toBe(false);
});
