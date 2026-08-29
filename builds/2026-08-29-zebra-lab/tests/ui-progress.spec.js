const { test, expect } = require('@playwright/test');
const path = require('path');

const INDEX_URL = 'file://' + path.resolve(__dirname, '..', 'index.html');

function todayUtc() {
  const d = new Date();
  const y = d.getUTCFullYear();
  const m = String(d.getUTCMonth() + 1).padStart(2, '0');
  const day = String(d.getUTCDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

test.describe('Chapter gating, daily gate, and persistent stats', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(INDEX_URL);
    await page.evaluate(() => localStorage.clear());
  });

  test('chapter 2 is locked before any chapter 1 solves are recorded', async ({ page }) => {
    await page.reload();
    await expect(page.locator('[data-testid="btn-practice-1"]')).toBeEnabled();
    await expect(page.locator('[data-testid="btn-practice-2"]')).toBeDisabled();
    await expect(page.locator('[data-testid="btn-practice-3"]')).toBeDisabled();
  });

  test('chapter 2 unlocks after 3 recorded chapter-1 solves (persisted, survives reload)', async ({ page }) => {
    await page.evaluate(() => {
      localStorage.setItem('zebralab_progress', JSON.stringify({ solvedByChapter: { 1: 3, 2: 0, 3: 0 } }));
    });
    await page.reload();
    await expect(page.locator('[data-testid="btn-practice-2"]')).toBeEnabled();
    await expect(page.locator('[data-testid="btn-practice-3"]')).toBeDisabled();
  });

  test('chapter 3 unlocks after 3 recorded chapter-2 solves', async ({ page }) => {
    await page.evaluate(() => {
      localStorage.setItem('zebralab_progress', JSON.stringify({ solvedByChapter: { 1: 3, 2: 3, 3: 0 } }));
    });
    await page.reload();
    await expect(page.locator('[data-testid="btn-practice-3"]')).toBeEnabled();
  });

  test('daily challenge allows exactly one completion per UTC day', async ({ page }) => {
    const date = todayUtc();
    await page.evaluate((d) => {
      localStorage.setItem('zebralab_daily', JSON.stringify({ date: d, completed: true, checksUsed: 1, hintsUsed: 0 }));
    }, date);
    await page.reload();
    const dailyBtn = page.locator('[data-testid="btn-daily"]');
    await expect(dailyBtn).toBeDisabled();
    await expect(dailyBtn).toContainText('Completed Today');
  });

  test('daily challenge is available when no completion is recorded for today', async ({ page }) => {
    await page.evaluate(() => {
      localStorage.setItem(
        'zebralab_daily',
        JSON.stringify({ date: '2000-01-01', completed: true, checksUsed: 1, hintsUsed: 0 })
      );
    });
    await page.reload();
    await expect(page.locator('[data-testid="btn-daily"]')).toBeEnabled();
  });

  test('stats persist across a reload', async ({ page }) => {
    await page.evaluate(() => {
      localStorage.setItem(
        'zebralab_stats',
        JSON.stringify({
          totalSolved: 7,
          totalChecks: 20,
          totalHints: 3,
          currentStreak: 4,
          bestStreak: 9,
          lastDailyDate: '2026-08-28',
          fastestChecksByChapter: {},
        })
      );
    });
    await page.reload();
    await expect(page.locator('[data-testid="stats-total-solved"]')).toHaveText('7');
    await expect(page.locator('[data-testid="stats-current-streak"]')).toHaveText('4');
    await expect(page.locator('[data-testid="stats-best-streak"]')).toHaveText('9');
  });

  test('share string never reveals any puzzle content, only the date, symbol, and counts', async ({ page }) => {
    const shareText = await page.evaluate(() => window.zlBuildShareString('2026-08-29', 1, 0, true));
    expect(shareText).toContain('2026-08-29');
    // None of the taxonomy category labels should ever leak into a share string.
    const forbidden = ['Undergraduate', 'Randomized', 'Random Assignment', 'Selection Bias'];
    for (const term of forbidden) {
      expect(shareText).not.toContain(term);
    }
  });

  test('streak increments on consecutive-day completion and resets on a gap', async ({ page }) => {
    const consecutive = await page.evaluate(() => {
      const stats = { totalSolved: 0, totalChecks: 0, totalHints: 0, currentStreak: 2, bestStreak: 2, lastDailyDate: '2026-08-28', fastestChecksByChapter: {} };
      window.zlUpdateStreakOnDailyComplete(stats, '2026-08-29');
      return stats.currentStreak;
    });
    expect(consecutive).toBe(3);

    const afterGap = await page.evaluate(() => {
      const stats = { totalSolved: 0, totalChecks: 0, totalHints: 0, currentStreak: 5, bestStreak: 5, lastDailyDate: '2026-08-20', fastestChecksByChapter: {} };
      window.zlUpdateStreakOnDailyComplete(stats, '2026-08-29');
      return stats.currentStreak;
    });
    expect(afterGap).toBe(1);
  });
});
