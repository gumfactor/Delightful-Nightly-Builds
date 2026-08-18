const { test, expect } = require('@playwright/test');
const path = require('path');

const pageUrl = `file://${path.resolve(__dirname, '../index.html')}`;

test.describe('Quiz tab', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(pageUrl);
    await page.locator('[data-testid="tab-quiz"]').click();
  });

  test('quiz loads with a question, choices, and progress indicator on question 1', async ({ page }) => {
    await expect(page.locator('[data-testid="panel-quiz"]')).toHaveClass(/active/);
    await expect(page.locator('[data-testid="quiz-progress"]')).toContainText('Question 1 of');
    const choiceCount = await page.locator('[data-testid="quiz-choices"] .choice-btn').count();
    expect(choiceCount).toBeGreaterThanOrEqual(3);
  });

  test('selecting a choice shows feedback and enables Next; Next is disabled before answering', async ({ page }) => {
    await expect(page.locator('[data-testid="quiz-next"]')).toBeDisabled();
    await page.locator('[data-testid="quiz-choices"] .choice-btn').first().click();
    await expect(page.locator('[data-testid="quiz-feedback"]')).not.toBeEmpty();
    await expect(page.locator('[data-testid="quiz-next"]')).toBeEnabled();
  });

  test('a second click on a choice after answering does not change the recorded answer (no double-scoring)', async ({ page }) => {
    const choices = page.locator('[data-testid="quiz-choices"] .choice-btn');
    await choices.first().click();
    const feedbackAfterFirst = await page.locator('[data-testid="quiz-feedback"]').textContent();
    await choices.nth(1).click({ force: true });
    const feedbackAfterSecond = await page.locator('[data-testid="quiz-feedback"]').textContent();
    expect(feedbackAfterSecond).toBe(feedbackAfterFirst);
  });

  test('completing the full quiz tracks score correctly and shows a final grade', async ({ page }) => {
    const totalQuestions = await page.evaluate(() => window.VoxelQuiz.buildQuiz(1).length);
    let correctCount = 0;

    for (let i = 0; i < totalQuestions; i++) {
      // Always click the choice marked "correct" once revealed by clicking
      // the first option, then checking which one the app marks correct —
      // instead, click index 0 and read back whether it was right, so we
      // can independently tally the running score.
      await page.locator('[data-testid="quiz-choices"] .choice-btn').first().click();
      const feedback = await page.locator('[data-testid="quiz-feedback"]').textContent();
      if (feedback === 'Correct!') correctCount++;
      await page.locator('[data-testid="quiz-next"]').click();
    }

    await expect(page.locator('[data-testid="quiz-final"]')).toBeVisible();
    const finalText = await page.locator('[data-testid="quiz-final"]').textContent();
    expect(finalText).toContain(`${correctCount} / ${totalQuestions}`);
  });

  test('computed questions are checked against the live formula, not a hardcoded value', async ({ page }) => {
    // Verify a "q-bonferroni" computed question's marked-correct choice
    // actually equals bonferroniThreshold(alpha, n) recomputed independently,
    // for several different seeds (proving it isn't a fixed string).
    const checks = await page.evaluate(() => {
      const results = [];
      for (const seed of [1, 2, 3, 4, 5]) {
        const questions = window.VoxelQuiz.buildQuiz(seed);
        const q = questions.find((item) => item.id === 'q-bonferroni');
        const promptMatch = q.prompt.match(/alpha = ([\d.]+) and ([\d,]+) independent/);
        const alpha = parseFloat(promptMatch[1]);
        const n = parseInt(promptMatch[2].replace(/,/g, ''), 10);
        const expected = window.VoxelStats.bonferroniThreshold(alpha, n).toExponential(3);
        const actualChoiceText = q.choices[q.correctIndex];
        results.push(actualChoiceText === expected);
      }
      return results;
    });
    expect(checks.every(Boolean)).toBe(true);
  });

  test('quiz includes both conceptual and computed question types', async ({ page }) => {
    const types = await page.evaluate(() => {
      const questions = window.VoxelQuiz.buildQuiz(7);
      return questions.map((q) => q.type);
    });
    expect(types).toContain('choice');
    expect(types).toContain('computed');
  });
});
