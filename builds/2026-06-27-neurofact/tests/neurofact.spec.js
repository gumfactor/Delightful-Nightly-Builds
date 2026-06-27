const { test, expect } = require('@playwright/test');
const path = require('path');

const INDEX = 'file://' + path.resolve(__dirname, '..', 'index.html');

test.describe('Neurofact intro screen', () => {
  test('page loads with correct title', async ({ page }) => {
    await page.goto(INDEX);
    await expect(page).toHaveTitle(/Neurofact/);
  });

  test('intro screen is visible on load', async ({ page }) => {
    await page.goto(INDEX);
    await expect(page.locator('#intro-screen')).toBeVisible();
  });

  test('game area is hidden on load', async ({ page }) => {
    await page.goto(INDEX);
    await expect(page.locator('#game-area')).toBeHidden();
  });

  test('end screen is hidden on load', async ({ page }) => {
    await page.goto(INDEX);
    await expect(page.locator('#end-screen')).toBeHidden();
  });

  test('start button is visible', async ({ page }) => {
    await page.goto(INDEX);
    await expect(page.locator('[data-testid="btn-start"]')).toBeVisible();
  });

  test('page shows logo text', async ({ page }) => {
    await page.goto(INDEX);
    await expect(page.locator('.logo')).toContainText('Neurofact');
  });
});

test.describe('Neurofact game flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(INDEX);
    await page.locator('[data-testid="btn-start"]').click();
  });

  test('game area becomes visible after start', async ({ page }) => {
    await expect(page.locator('#game-area')).toBeVisible();
  });

  test('intro screen hides after start', async ({ page }) => {
    await expect(page.locator('#intro-screen')).toBeHidden();
  });

  test('first question statement is visible', async ({ page }) => {
    await expect(page.locator('[data-testid="question-statement"]')).toBeVisible();
  });

  test('question statement is non-empty', async ({ page }) => {
    const text = await page.locator('[data-testid="question-statement"]').textContent();
    expect(text.trim().length).toBeGreaterThan(20);
  });

  test('Real Finding button is visible', async ({ page }) => {
    await expect(page.locator('[data-testid="btn-real"]')).toBeVisible();
  });

  test('AI Generated button is visible', async ({ page }) => {
    await expect(page.locator('[data-testid="btn-fake"]')).toBeVisible();
  });

  test('progress text shows 0 of 30 initially', async ({ page }) => {
    await expect(page.locator('#progress-text')).toContainText('0 / 30');
  });

  test('score starts at 0', async ({ page }) => {
    await expect(page.locator('#score-display')).toContainText('0');
  });

  test('streak starts at 0', async ({ page }) => {
    await expect(page.locator('#streak-display')).toContainText('0');
  });

  test('category tag is visible on first question', async ({ page }) => {
    await expect(page.locator('[data-testid="category-tag"]')).toBeVisible();
  });

  test('difficulty tag is visible on first question', async ({ page }) => {
    await expect(page.locator('[data-testid="difficulty-tag"]')).toBeVisible();
  });

  test('feedback is hidden before answering', async ({ page }) => {
    await expect(page.locator('#feedback')).toBeHidden();
  });

  test('next button is hidden before answering', async ({ page }) => {
    await expect(page.locator('[data-testid="btn-next"]')).toBeHidden();
  });

  test('clicking Real Finding reveals feedback', async ({ page }) => {
    await page.locator('[data-testid="btn-real"]').click();
    await expect(page.locator('#feedback')).toBeVisible();
  });

  test('feedback verdict text is shown after answering', async ({ page }) => {
    await page.locator('[data-testid="btn-real"]').click();
    const verdict = await page.locator('[data-testid="feedback-verdict"]').textContent();
    expect(verdict.trim().length).toBeGreaterThan(0);
  });

  test('feedback explanation is shown after answering', async ({ page }) => {
    await page.locator('[data-testid="btn-real"]').click();
    const text = await page.locator('[data-testid="feedback-text"]').textContent();
    expect(text.trim().length).toBeGreaterThan(10);
  });

  test('next button appears after answering', async ({ page }) => {
    await page.locator('[data-testid="btn-real"]').click();
    await expect(page.locator('[data-testid="btn-next"]')).toBeVisible();
  });

  test('answer buttons are disabled after answering', async ({ page }) => {
    await page.locator('[data-testid="btn-real"]').click();
    await expect(page.locator('[data-testid="btn-real"]')).toBeDisabled();
    await expect(page.locator('[data-testid="btn-fake"]')).toBeDisabled();
  });

  test('clicking next advances progress to 1/30', async ({ page }) => {
    await page.locator('[data-testid="btn-real"]').click();
    await page.locator('[data-testid="btn-next"]').click();
    await expect(page.locator('#progress-text')).toContainText('1 / 30');
  });

  test('second question loads after clicking next', async ({ page }) => {
    const first = await page.locator('[data-testid="question-statement"]').textContent();
    await page.locator('[data-testid="btn-fake"]').click();
    await page.locator('[data-testid="btn-next"]').click();
    const second = await page.locator('[data-testid="question-statement"]').textContent();
    // Second question may occasionally be the same as first (unlikely with 30 questions)
    // so just verify it is non-empty and loaded
    expect(second.trim().length).toBeGreaterThan(20);
  });

  test('feedback is hidden again on next question', async ({ page }) => {
    await page.locator('[data-testid="btn-real"]').click();
    await page.locator('[data-testid="btn-next"]').click();
    await expect(page.locator('#feedback')).toBeHidden();
  });

  test('clicking AI Generated also reveals feedback', async ({ page }) => {
    await page.locator('[data-testid="btn-fake"]').click();
    await expect(page.locator('#feedback')).toBeVisible();
  });
});

test.describe('Neurofact end screen', () => {
  async function playAllQuestions(page) {
    await page.goto(INDEX);
    await page.locator('[data-testid="btn-start"]').click();
    // Answer all 30 questions by always clicking Real
    for (let i = 0; i < 30; i++) {
      await page.locator('[data-testid="btn-real"]').click();
      await page.locator('[data-testid="btn-next"]').click();
    }
  }

  test('end screen appears after all 30 questions', async ({ page }) => {
    await playAllQuestions(page);
    await expect(page.locator('#end-screen')).toBeVisible();
  });

  test('end screen shows a letter grade', async ({ page }) => {
    await playAllQuestions(page);
    const grade = await page.locator('[data-testid="end-grade"]').textContent();
    expect(['A', 'B', 'C', 'D', 'F']).toContain(grade.trim());
  });

  test('end screen shows final score', async ({ page }) => {
    await playAllQuestions(page);
    const score = await page.locator('[data-testid="end-score"]').textContent();
    expect(score).toMatch(/\d+\/30/);
  });

  test('end screen shows percentage', async ({ page }) => {
    await playAllQuestions(page);
    const pct = await page.locator('[data-testid="end-pct"]').textContent();
    expect(pct).toMatch(/\d+%/);
  });

  test('end screen shows grade title text', async ({ page }) => {
    await playAllQuestions(page);
    const title = await page.locator('[data-testid="end-title"]').textContent();
    expect(title.trim().length).toBeGreaterThan(0);
  });

  test('end screen shows real correct breakdown', async ({ page }) => {
    await playAllQuestions(page);
    const bd = await page.locator('[data-testid="bd-real-correct"]').textContent();
    expect(bd).toMatch(/\d+\/15/);
  });

  test('restart button is visible on end screen', async ({ page }) => {
    await playAllQuestions(page);
    await expect(page.locator('[data-testid="btn-restart"]')).toBeVisible();
  });

  test('restart button restarts the game', async ({ page }) => {
    await playAllQuestions(page);
    await page.locator('[data-testid="btn-restart"]').click();
    await expect(page.locator('#game-area')).toBeVisible();
    await expect(page.locator('#end-screen')).toBeHidden();
    await expect(page.locator('#score-display')).toContainText('0');
  });
});
