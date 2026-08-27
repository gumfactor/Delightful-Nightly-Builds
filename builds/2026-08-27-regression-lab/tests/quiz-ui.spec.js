const { test, expect } = require('@playwright/test');
const path = require('path');

const APP_URL = 'file://' + path.join(__dirname, '..', 'index.html');

test.describe('Quiz tab', () => {
  test('starting the quiz shows the first question and 4 options', async ({ page }) => {
    await page.goto(APP_URL);
    await page.click('[data-testid=tab-quiz]');
    await page.click('[data-testid=start-quiz-btn]');
    await expect(page.locator('[data-testid=quiz-active]')).toBeVisible();
    await expect(page.locator('#quiz-options .quiz-option-btn')).toHaveCount(4);
    const progress = await page.textContent('[data-testid=quiz-progress]');
    expect(progress).toContain('Question 1 of 12');
  });

  test('answering correctly highlights the chosen option and reveals Next', async ({ page }) => {
    await page.goto(APP_URL);
    await page.click('[data-testid=tab-quiz]');
    await page.click('[data-testid=start-quiz-btn]');
    await page.locator('#quiz-options .quiz-option-btn').first().click();
    await expect(page.locator('[data-testid=quiz-next-btn]')).toBeVisible();
    const feedback = await page.textContent('[data-testid=quiz-feedback]');
    expect(feedback.length).toBeGreaterThan(0);
    const disabledCount = await page.locator('#quiz-options .quiz-option-btn[disabled]').count();
    expect(disabledCount).toBe(4);
  });

  test('clicking an option a second time does not change the recorded answer', async ({ page }) => {
    await page.goto(APP_URL);
    await page.click('[data-testid=tab-quiz]');
    await page.click('[data-testid=start-quiz-btn]');
    const options = page.locator('#quiz-options .quiz-option-btn');
    await options.nth(0).click();
    const progressAfterFirst = await page.textContent('[data-testid=quiz-progress]');
    await options.nth(1).click({ force: true });
    const progressAfterSecond = await page.textContent('[data-testid=quiz-progress]');
    expect(progressAfterFirst).toBe(progressAfterSecond);
  });

  test('completing all 12 questions shows a final score and persists a best score', async ({ page }) => {
    await page.goto(APP_URL);
    await page.click('[data-testid=tab-quiz]');
    await page.click('[data-testid=start-quiz-btn]');

    for (let i = 0; i < 12; i++) {
      await page.locator('#quiz-options .quiz-option-btn').first().click();
      const nextBtn = page.locator('[data-testid=quiz-next-btn]');
      await expect(nextBtn).toBeVisible();
      await nextBtn.click();
    }

    await expect(page.locator('[data-testid=quiz-results]')).toBeVisible();
    const score = await page.textContent('[data-testid=quiz-score]');
    expect(score).toMatch(/^\d+ \/ 12$/);

    const stored = await page.evaluate(() => localStorage.getItem('regressionLabQuizBest'));
    expect(stored).not.toBeNull();
    const parsed = JSON.parse(stored);
    expect(parsed.total).toBe(12);
  });

  test('a diagnose-type question renders its residual-plot chart', async ({ page }) => {
    await page.goto(APP_URL);
    await page.click('[data-testid=tab-quiz]');
    await page.click('[data-testid=start-quiz-btn]');

    let sawChart = false;
    for (let i = 0; i < 12; i++) {
      const chartVisible = await page.locator('[data-testid=quiz-chart-card]').isVisible();
      if (chartVisible) {
        sawChart = true;
        break;
      }
      await page.locator('#quiz-options .quiz-option-btn').first().click();
      await page.locator('[data-testid=quiz-next-btn]').click();
    }
    expect(sawChart).toBe(true);
  });
});
