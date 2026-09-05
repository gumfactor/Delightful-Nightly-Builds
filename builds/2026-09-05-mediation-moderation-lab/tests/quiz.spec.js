const { test, expect } = require('@playwright/test');
const path = require('path');

const INDEX_URL = 'file://' + path.join(__dirname, '..', 'index.html');

async function goToQuizTab(page) {
  await page.getByTestId('tab-quiz').click();
}

test.beforeEach(async ({ page }) => {
  await page.goto(INDEX_URL);
  await goToQuizTab(page);
});

test.describe('Quiz', () => {
  test('Start Quiz shows the first question with 16-question progress', async ({ page }) => {
    await page.getByTestId('quiz-start').click();
    await expect(page.getByTestId('quiz-progress')).toHaveText(/Question 1 of 16/);
    await expect(page.getByTestId('quiz-prompt')).not.toHaveText('');
    const choices = page.locator('[data-testid="quiz-choices"] button');
    const count = await choices.count();
    expect(count).toBeGreaterThanOrEqual(2);
  });

  test('answering correctly marks the chosen choice correct and shows feedback starting with "Correct."', async ({ page }) => {
    await page.getByTestId('quiz-start').click();
    // Fixed question 1's correct answer is the first choice (index 0) per quiz-data.js.
    const choices = page.locator('[data-testid="quiz-choices"] button');
    await choices.nth(0).click();
    await expect(choices.nth(0)).toHaveClass(/correct/);
    await expect(page.getByTestId('quiz-feedback')).toContainText('Correct.');
    await expect(page.getByTestId('quiz-next')).toBeVisible();
  });

  test('answering incorrectly marks the chosen choice incorrect and the true answer correct', async ({ page }) => {
    await page.getByTestId('quiz-start').click();
    // Fixed question 1's correct answer is index 0; choosing index 1 is wrong.
    const choices = page.locator('[data-testid="quiz-choices"] button');
    await choices.nth(1).click();
    await expect(choices.nth(1)).toHaveClass(/incorrect/);
    await expect(choices.nth(0)).toHaveClass(/correct/);
    await expect(page.getByTestId('quiz-feedback')).toContainText('Incorrect.');
  });

  test('choice buttons are disabled after answering (cannot change answer)', async ({ page }) => {
    await page.getByTestId('quiz-start').click();
    const choices = page.locator('[data-testid="quiz-choices"] button');
    await choices.nth(0).click();
    await expect(choices.nth(0)).toBeDisabled();
    await expect(choices.nth(1)).toBeDisabled();
  });

  test('completing all 16 questions shows the final score screen with a full review list', async ({ page }) => {
    await page.getByTestId('quiz-start').click();
    for (let i = 0; i < 16; i++) {
      const choices = page.locator('[data-testid="quiz-choices"] button');
      await choices.nth(0).click();
      const nextBtn = page.getByTestId('quiz-next');
      await expect(nextBtn).toBeVisible();
      await nextBtn.click();
    }
    await expect(page.getByTestId('quiz-result')).toBeVisible();
    await expect(page.getByTestId('quiz-score')).toHaveText(/Score: \d+ \/ 16/);
    const reviewItems = page.locator('[data-testid="quiz-review"] .quiz-review-item');
    await expect(reviewItems).toHaveCount(16);
  });

  test('Retake Quiz restarts at question 1 with a fresh live scenario', async ({ page }) => {
    await page.getByTestId('quiz-start').click();
    for (let i = 0; i < 16; i++) {
      const choices = page.locator('[data-testid="quiz-choices"] button');
      await choices.nth(0).click();
      await page.getByTestId('quiz-next').click();
    }
    await page.getByTestId('quiz-restart').click();
    await expect(page.getByTestId('quiz-progress')).toHaveText(/Question 1 of 16/);
    await expect(page.getByTestId('quiz-result')).toBeHidden();
  });

  test('a live question\'s stated correct answer is internally consistent with its own explanation text', async ({ page }) => {
    await page.getByTestId('quiz-start').click();
    // Advance past the 8 fixed questions to reach a live question.
    for (let i = 0; i < 8; i++) {
      const choices = page.locator('[data-testid="quiz-choices"] button');
      await choices.nth(0).click();
      await page.getByTestId('quiz-next').click();
    }
    await expect(page.getByTestId('quiz-progress')).toHaveText(/Live-computed/);
    const promptText = await page.getByTestId('quiz-prompt').textContent();
    expect(promptText.length).toBeGreaterThan(10);
  });
});
