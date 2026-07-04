const { test, expect } = require('@playwright/test');
const path = require('path');

const filePath = path.join(__dirname, '..', 'index.html');

test.beforeEach(async ({ page }) => {
  await page.goto(`file://${filePath}`);
  // Ensure each test starts with clean quiz state.
  await page.evaluate(() => localStorage.removeItem('power-lab-quiz-state'));
  await page.reload();
  await page.getByTestId('tab-btn-quiz').click();
});

test.describe('Power Intuition Quiz tab', () => {
  test('the first question renders on load', async ({ page }) => {
    const questionText = await page.getByTestId('quiz-question').textContent();
    expect(questionText.length).toBeGreaterThan(10);
    await expect(page.getByTestId('quiz-feedback')).toBeHidden();
  });

  test('selecting a bucket reveals feedback with the exact computed power', async ({ page }) => {
    const buckets = page.getByTestId('quiz-bucket-btn');
    await buckets.first().click();
    const feedback = page.getByTestId('quiz-feedback');
    await expect(feedback).toBeVisible();
    await expect(feedback).toContainText(/Actual power = \d+\.\d%/);
  });

  test('a correct answer increments score and streak', async ({ page }) => {
    // Determine the correct bucket the same way quiz.js does, using the
    // globals stats.js/quiz.js expose on window -- no reimplementation.
    const correctBucket = await page.evaluate(() => {
      const state = JSON.parse(localStorage.getItem('power-lab-quiz-state') || '{"answeredIds":[]}');
      const { QUIZ_BANK, bucketForPower } = window.PowerLabQuiz;
      const { computePower } = window.PowerLabStats;
      const q = QUIZ_BANK.find((item) => !state.answeredIds.includes(item.id));
      return bucketForPower(computePower(q));
    });

    await expect(page.getByTestId('quiz-score')).toHaveText('Score: 0');
    await page.locator(`[data-testid="quiz-bucket-btn"][data-bucket="${correctBucket}"]`).click();
    await expect(page.getByTestId('quiz-score')).toHaveText('Score: 1');
    await expect(page.getByTestId('quiz-streak')).toHaveText('Streak: 1 (best: 1)');
  });

  test('an incorrect answer resets streak but not score', async ({ page }) => {
    // Computes the correct bucket for whichever question is currently first
    // in the unanswered queue, reading fresh state each time -- so it stays
    // valid after the queue advances via "Next question".
    const correctBucketForCurrentQuestion = () =>
      page.evaluate(() => {
        const state = JSON.parse(localStorage.getItem('power-lab-quiz-state') || '{"answeredIds":[]}');
        const { QUIZ_BANK, bucketForPower } = window.PowerLabQuiz;
        const { computePower } = window.PowerLabStats;
        const q = QUIZ_BANK.find((item) => !state.answeredIds.includes(item.id));
        return bucketForPower(computePower(q));
      });
    const allBuckets = ['<50%', '50-70%', '70-90%', '>90%'];

    // First answer correctly to build a streak of 1.
    const firstCorrect = await correctBucketForCurrentQuestion();
    await page.locator(`[data-testid="quiz-bucket-btn"][data-bucket="${firstCorrect}"]`).click();
    await expect(page.getByTestId('quiz-streak')).toHaveText('Streak: 1 (best: 1)');
    await page.getByTestId('quiz-next-btn').click();

    // Now answer the next question incorrectly, relative to *that* question's
    // own correct bucket (not the previous question's).
    const secondCorrect = await correctBucketForCurrentQuestion();
    const wrongBucket = allBuckets.find((b) => b !== secondCorrect);
    await page.locator(`[data-testid="quiz-bucket-btn"][data-bucket="${wrongBucket}"]`).click();
    await expect(page.getByTestId('quiz-streak')).toHaveText('Streak: 0 (best: 1)');
    await expect(page.getByTestId('quiz-score')).toHaveText('Score: 1');
  });

  test('clicking Next advances to a different question', async ({ page }) => {
    const firstQuestion = await page.getByTestId('quiz-question').textContent();
    await page.getByTestId('quiz-bucket-btn').first().click();
    await page.getByTestId('quiz-next-btn').click();
    const secondQuestion = await page.getByTestId('quiz-question').textContent();
    expect(secondQuestion).not.toBe(firstQuestion);
  });

  test('score and streak persist across a page reload', async ({ page }) => {
    const buckets = page.getByTestId('quiz-bucket-btn');
    await buckets.first().click();
    await page.reload();
    await page.getByTestId('tab-btn-quiz').click();
    const scoreText = await page.getByTestId('quiz-score').textContent();
    expect(scoreText).toMatch(/Score: [01]/); // persisted regardless of correct/incorrect on the single click
    const state = await page.evaluate(() => JSON.parse(localStorage.getItem('power-lab-quiz-state')));
    expect(state.answeredIds.length).toBe(1);
  });

  test('working through all 18 questions loops back to the start without crashing', async ({ page }) => {
    for (let i = 0; i < 18; i++) {
      await page.getByTestId('quiz-bucket-btn').first().click();
      await page.getByTestId('quiz-next-btn').click();
    }
    // Should have looped back and still show a valid question with working buttons.
    await expect(page.getByTestId('quiz-question')).not.toHaveText('');
    await page.getByTestId('quiz-bucket-btn').first().click();
    await expect(page.getByTestId('quiz-feedback')).toBeVisible();
  });
});
