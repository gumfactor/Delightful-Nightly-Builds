const { test, expect } = require('@playwright/test');
const path = require('path');

const URL = 'file://' + path.join(__dirname, '..', 'index.html');

async function goto(page, dateOverride) {
  if (dateOverride) {
    await page.addInitScript((iso) => {
      const RealDate = Date;
      class FixedDate extends RealDate {
        constructor(...args) {
          if (args.length === 0) return new RealDate(iso);
          return new RealDate(...args);
        }
        static now() { return new RealDate(iso).getTime(); }
      }
      // eslint-disable-next-line no-global-assign
      Date = FixedDate;
    }, dateOverride);
  }
  await page.goto(URL);
  await page.waitForSelector('[data-testid="menu-view"]');
}

test.describe('Menu and navigation', () => {
  test('main menu renders all navigation options', async ({ page }) => {
    await goto(page);
    await expect(page.locator('[data-testid="btn-campaign"]')).toBeVisible();
    await expect(page.locator('[data-testid="btn-daily"]')).toBeVisible();
    await expect(page.locator('[data-testid="btn-practice"]')).toBeVisible();
    await expect(page.locator('[data-testid="btn-mastery"]')).toBeVisible();
    await expect(page.locator('[data-testid="btn-reset"]')).toBeVisible();
  });

  test('back button on chapter select returns to menu', async ({ page }) => {
    await goto(page);
    await page.click('[data-testid="btn-campaign"]');
    await expect(page.locator('[data-testid="chapter-select-view"]')).toBeVisible();
    await page.click('[data-testid="btn-back"]');
    await expect(page.locator('[data-testid="menu-view"]')).toBeVisible();
  });
});

test.describe('Data integrity', () => {
  test('every vignette has exactly 3 distractors and a valid correct bias id', async ({ page }) => {
    await goto(page);
    const result = await page.evaluate(() => {
      const biasIds = window.HH.BIASES.map((b) => b.id);
      const problems = [];
      window.HH.VIGNETTES.forEach((v) => {
        if (!biasIds.includes(v.biasId)) problems.push('bad biasId: ' + v.id);
        if (v.distractors.length !== 3) problems.push('wrong distractor count: ' + v.id);
        v.distractors.forEach((d) => {
          if (!biasIds.includes(d)) problems.push('bad distractor id: ' + v.id);
        });
        if (v.distractors.includes(v.biasId)) problems.push('distractor equals correct answer: ' + v.id);
      });
      return problems;
    });
    expect(result).toEqual([]);
  });

  test('chapters contain exactly 10 vignettes each, 30 total', async ({ page }) => {
    await goto(page);
    const counts = await page.evaluate(() => {
      const byChapter = { 1: 0, 2: 0, 3: 0 };
      window.HH.VIGNETTES.forEach((v) => { byChapter[v.chapter] += 1; });
      return { byChapter, total: window.HH.VIGNETTES.length };
    });
    expect(counts.byChapter[1]).toBe(10);
    expect(counts.byChapter[2]).toBe(10);
    expect(counts.byChapter[3]).toBe(10);
    expect(counts.total).toBe(30);
  });

  test('every bias in the taxonomy is used as the correct answer at least twice', async ({ page }) => {
    await goto(page);
    const counts = await page.evaluate(() => {
      const tally = {};
      window.HH.BIASES.forEach((b) => { tally[b.id] = 0; });
      window.HH.VIGNETTES.forEach((v) => { tally[v.biasId] += 1; });
      return tally;
    });
    Object.values(counts).forEach((count) => {
      expect(count).toBeGreaterThanOrEqual(2);
    });
  });
});

test.describe('Chapter unlock gating', () => {
  test('chapter 1 is unlocked by default, chapters 2 and 3 are locked', async ({ page }) => {
    await goto(page);
    await page.click('[data-testid="btn-campaign"]');
    await expect(page.locator('[data-testid="chapter-play-1"]')).toBeEnabled();
    await expect(page.locator('[data-testid="chapter-play-2"]')).toBeDisabled();
    await expect(page.locator('[data-testid="chapter-play-3"]')).toBeDisabled();
  });

  test('answering correctly shows correct feedback and increments score toward completion', async ({ page }) => {
    await goto(page);
    await page.click('[data-testid="btn-campaign"]');
    await page.click('[data-testid="chapter-play-1"]');

    for (let i = 0; i < 10; i++) {
      const questionText = await page.locator('[data-testid="question-text"]').textContent();
      const vignette = await page.evaluate((text) => {
        return window.HH.VIGNETTES.find((v) => v.text === text);
      }, questionText);

      // Click whichever answer button's visible label matches the correct bias name.
      const correctName = await page.evaluate((biasId) => {
        return window.HH.BIASES.find((b) => b.id === biasId).name;
      }, vignette.biasId);

      const buttons = page.locator('[data-testid^="answer-btn-"]');
      const count = await buttons.count();
      let clicked = false;
      for (let b = 0; b < count; b++) {
        const label = await buttons.nth(b).textContent();
        if (label === correctName) {
          await buttons.nth(b).click();
          clicked = true;
          break;
        }
      }
      expect(clicked).toBe(true);

      await expect(page.locator('[data-testid="feedback-panel"][data-result="correct"]')).toBeVisible();
      await page.click('[data-testid="btn-next"]');
    }

    await expect(page.locator('[data-testid="chapter-complete-view"]')).toBeVisible();
    await expect(page.locator('[data-testid="chapter-complete-accuracy"]')).toContainText('10 / 10');
  });

  test('completing a chapter at 100% unlocks the next chapter and persists across reload', async ({ page }) => {
    await goto(page);
    await page.click('[data-testid="btn-campaign"]');
    await page.click('[data-testid="chapter-play-1"]');

    for (let i = 0; i < 10; i++) {
      const questionText = await page.locator('[data-testid="question-text"]').textContent();
      const vignette = await page.evaluate((text) => window.HH.VIGNETTES.find((v) => v.text === text), questionText);
      const correctName = await page.evaluate((biasId) => window.HH.BIASES.find((b) => b.id === biasId).name, vignette.biasId);
      const buttons = page.locator('[data-testid^="answer-btn-"]');
      const count = await buttons.count();
      for (let b = 0; b < count; b++) {
        const label = await buttons.nth(b).textContent();
        if (label === correctName) { await buttons.nth(b).click(); break; }
      }
      await page.click('[data-testid="btn-next"]');
    }

    await expect(page.locator('[data-testid="chapter-complete-unlock-message"]')).toContainText('Chapter 2 unlocked');
    await page.click('[data-testid="btn-back-to-chapters"]');
    await expect(page.locator('[data-testid="chapter-play-2"]')).toBeEnabled();

    await page.reload();
    await page.waitForSelector('[data-testid="menu-view"]');
    await page.click('[data-testid="btn-campaign"]');
    await expect(page.locator('[data-testid="chapter-play-2"]')).toBeEnabled();
  });

  test('answering incorrectly shows incorrect feedback with the correct answer revealed', async ({ page }) => {
    await goto(page);
    await page.click('[data-testid="btn-campaign"]');
    await page.click('[data-testid="chapter-play-1"]');

    const questionText = await page.locator('[data-testid="question-text"]').textContent();
    const vignette = await page.evaluate((text) => window.HH.VIGNETTES.find((v) => v.text === text), questionText);
    const wrongBiasId = vignette.distractors[0];
    const wrongName = await page.evaluate((biasId) => window.HH.BIASES.find((b) => b.id === biasId).name, wrongBiasId);

    const buttons = page.locator('[data-testid^="answer-btn-"]');
    const count = await buttons.count();
    for (let b = 0; b < count; b++) {
      const label = await buttons.nth(b).textContent();
      if (label === wrongName) { await buttons.nth(b).click(); break; }
    }

    await expect(page.locator('[data-testid="feedback-panel"][data-result="incorrect"]')).toBeVisible();
    await expect(page.locator('[data-testid="explanation-text"]')).toContainText(vignette.explanation.slice(0, 20));
  });

  test('finishing a chapter below 70% accuracy does not unlock the next chapter', async ({ page }) => {
    await goto(page);
    await page.click('[data-testid="btn-campaign"]');
    await page.click('[data-testid="chapter-play-1"]');

    for (let i = 0; i < 10; i++) {
      const questionText = await page.locator('[data-testid="question-text"]').textContent();
      const vignette = await page.evaluate((text) => window.HH.VIGNETTES.find((v) => v.text === text), questionText);
      // Answer wrong for the first 6 questions, correct for the remaining 4 — 40% net, below 70%.
      const targetBiasId = i < 6 ? vignette.distractors[0] : vignette.biasId;
      const targetName = await page.evaluate((biasId) => window.HH.BIASES.find((b) => b.id === biasId).name, targetBiasId);
      const buttons = page.locator('[data-testid^="answer-btn-"]');
      const count = await buttons.count();
      for (let b = 0; b < count; b++) {
        const label = await buttons.nth(b).textContent();
        if (label === targetName) { await buttons.nth(b).click(); break; }
      }
      await page.click('[data-testid="btn-next"]');
    }

    await expect(page.locator('[data-testid="chapter-complete-unlock-message"]')).toContainText('40%');
    await page.click('[data-testid="btn-back-to-chapters"]');
    await expect(page.locator('[data-testid="chapter-play-2"]')).toBeDisabled();
  });
});

test.describe('Daily Challenge', () => {
  test('daily challenge selects exactly 5 questions', async ({ page }) => {
    await goto(page, '2026-08-01T12:00:00Z');
    await page.click('[data-testid="btn-daily"]');
    await page.click('[data-testid="btn-start-daily"]');
    await expect(page.locator('[data-testid="question-progress"]')).toContainText('of 5');
  });

  test('daily challenge is deterministic for a given date', async ({ page, context }) => {
    await goto(page, '2026-08-02T12:00:00Z');
    const firstQuestion = await page.evaluate((date) => window.HH.dailyVignettes(date).map((v) => v.id), '2026-08-02');

    const page2 = await context.newPage();
    await goto(page2, '2026-08-02T12:00:00Z');
    const secondQuestion = await page2.evaluate((date) => window.HH.dailyVignettes(date).map((v) => v.id), '2026-08-02');

    expect(firstQuestion).toEqual(secondQuestion);
    await page2.close();
  });

  test('daily challenge cannot be replayed twice on the same UTC date', async ({ page }) => {
    await goto(page, '2026-08-03T12:00:00Z');
    await page.click('[data-testid="btn-daily"]');
    await page.click('[data-testid="btn-start-daily"]');

    for (let i = 0; i < 5; i++) {
      const buttons = page.locator('[data-testid^="answer-btn-"]');
      await buttons.first().click();
      await page.click('[data-testid="btn-next"]');
    }

    await expect(page.locator('[data-testid="daily-result-view"]')).toBeVisible();
    await page.click('[data-testid="btn-back-to-menu"]');
    await page.click('[data-testid="btn-daily"]');
    await expect(page.locator('[data-testid="daily-already-played"]')).toBeVisible();
    await expect(page.locator('[data-testid="btn-start-daily"]')).toHaveCount(0);
  });

  test('daily result screen renders a shareable emoji grid matching the right/wrong sequence', async ({ page }) => {
    await goto(page, '2026-08-04T12:00:00Z');
    await page.click('[data-testid="btn-daily"]');
    await page.click('[data-testid="btn-start-daily"]');

    const outcomes = [];
    for (let i = 0; i < 5; i++) {
      const questionText = await page.locator('[data-testid="question-text"]').textContent();
      const vignette = await page.evaluate((text) => window.HH.VIGNETTES.find((v) => v.text === text), questionText);
      const useCorrect = i % 2 === 0;
      const targetBiasId = useCorrect ? vignette.biasId : vignette.distractors[0];
      outcomes.push(useCorrect);
      const targetName = await page.evaluate((biasId) => window.HH.BIASES.find((b) => b.id === biasId).name, targetBiasId);
      const buttons = page.locator('[data-testid^="answer-btn-"]');
      const count = await buttons.count();
      for (let b = 0; b < count; b++) {
        const label = await buttons.nth(b).textContent();
        if (label === targetName) { await buttons.nth(b).click(); break; }
      }
      await page.click('[data-testid="btn-next"]');
    }

    const expectedGrid = outcomes.map((ok) => (ok ? '🟩' : '🟥')).join('');
    await expect(page.locator('[data-testid="daily-result-grid"]')).toHaveText(expectedGrid);
    const expectedScore = outcomes.filter(Boolean).length;
    await expect(page.locator('[data-testid="daily-result-score"]')).toContainText(expectedScore + ' / 5');
  });
});

test.describe('Practice mode', () => {
  test('practice mode allows drilling a single bias type outside chapter-unlock constraints', async ({ page }) => {
    await goto(page);
    await page.click('[data-testid="btn-practice"]');
    await page.click('[data-testid="practice-bias-btn-anchoring"]');
    await expect(page.locator('[data-testid="question-view"]')).toBeVisible();

    const questionText = await page.locator('[data-testid="question-text"]').textContent();
    const vignette = await page.evaluate((text) => window.HH.VIGNETTES.find((v) => v.text === text), questionText);
    expect(vignette.biasId).toBe('anchoring');
  });

  test('practice "all biases" mode pulls from the full 30-vignette pool', async ({ page }) => {
    await goto(page);
    await page.click('[data-testid="btn-practice"]');
    await page.click('[data-testid="practice-all-btn"]');
    await expect(page.locator('[data-testid="question-progress"]')).toContainText('of 30');
  });
});

test.describe('Mastery Dashboard', () => {
  test('mastery dashboard reflects accumulated attempts and color-codes mastery level', async ({ page }) => {
    await goto(page);
    await page.click('[data-testid="btn-practice"]');
    await page.click('[data-testid="practice-bias-btn-anchoring"]');

    for (let i = 0; i < 3; i++) {
      const questionText = await page.locator('[data-testid="question-text"]').textContent();
      const vignette = await page.evaluate((text) => window.HH.VIGNETTES.find((v) => v.text === text), questionText);
      const correctName = await page.evaluate((biasId) => window.HH.BIASES.find((b) => b.id === biasId).name, vignette.biasId);
      const buttons = page.locator('[data-testid^="answer-btn-"]');
      const count = await buttons.count();
      for (let b = 0; b < count; b++) {
        const label = await buttons.nth(b).textContent();
        if (label === correctName) { await buttons.nth(b).click(); break; }
      }
      await page.click('[data-testid="btn-next"]');
    }

    await page.click('[data-testid="btn-back-to-menu"]');
    await page.click('[data-testid="btn-mastery"]');
    await expect(page.locator('[data-testid="mastery-pct-anchoring"]')).toContainText('100%');
    await expect(page.locator('[data-testid="mastery-row-anchoring"]')).toHaveAttribute('data-level', 'high');
  });
});

test.describe('Reset Progress', () => {
  test('reset progress clears all state and returns to first-run state', async ({ page }) => {
    await goto(page);
    await page.click('[data-testid="btn-practice"]');
    await page.click('[data-testid="practice-bias-btn-anchoring"]');

    const anchoringVignetteCount = await page.evaluate(
      () => window.HH.VIGNETTES.filter((v) => v.biasId === 'anchoring').length
    );
    for (let i = 0; i < anchoringVignetteCount; i++) {
      const buttons = page.locator('[data-testid^="answer-btn-"]');
      await buttons.first().click();
      await page.click('[data-testid="btn-next"]');
    }
    await page.click('[data-testid="btn-back-to-menu"]');

    await page.click('[data-testid="btn-reset"]');
    await expect(page.locator('[data-testid="reset-confirm-view"]')).toBeVisible();
    await page.click('[data-testid="btn-confirm-reset"]');
    await expect(page.locator('[data-testid="menu-view"]')).toBeVisible();

    await page.click('[data-testid="btn-mastery"]');
    await expect(page.locator('[data-testid="mastery-pct-anchoring"]')).toContainText('Not attempted');

    await page.click('[data-testid="btn-back"]');
    await page.click('[data-testid="btn-campaign"]');
    await expect(page.locator('[data-testid="chapter-play-2"]')).toBeDisabled();
  });

  test('reset progress cancel button returns to menu without clearing state', async ({ page }) => {
    await goto(page);
    await page.click('[data-testid="btn-reset"]');
    await page.click('[data-testid="btn-cancel-reset"]');
    await expect(page.locator('[data-testid="menu-view"]')).toBeVisible();
  });
});

test.describe('Robustness', () => {
  test('no console errors or page errors occur during a full campaign playthrough', async ({ page }) => {
    const errors = [];
    page.on('pageerror', (err) => errors.push(String(err)));
    page.on('console', (msg) => { if (msg.type() === 'error') errors.push(msg.text()); });

    await goto(page);
    await page.click('[data-testid="btn-campaign"]');
    await page.click('[data-testid="chapter-play-1"]');
    for (let i = 0; i < 10; i++) {
      const buttons = page.locator('[data-testid^="answer-btn-"]');
      await buttons.first().click();
      await page.click('[data-testid="btn-next"]');
    }
    await expect(page.locator('[data-testid="chapter-complete-view"]')).toBeVisible();
    expect(errors).toEqual([]);
  });

  test('layout does not break at a narrow 375px mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 700 });
    await goto(page);
    const app = page.locator('#app');
    const box = await app.boundingBox();
    expect(box.width).toBeLessThanOrEqual(375);
    await expect(page.locator('[data-testid="menu-view"]')).toBeVisible();
  });

  test('corrupt localStorage state falls back to defaults without throwing', async ({ page }) => {
    await page.addInitScript(() => {
      window.localStorage.setItem('heuristicHunt_v1', '{not valid json');
    });
    const errors = [];
    page.on('pageerror', (err) => errors.push(String(err)));
    await goto(page);
    expect(errors).toEqual([]);
    await expect(page.locator('[data-testid="menu-view"]')).toBeVisible();
  });
});
