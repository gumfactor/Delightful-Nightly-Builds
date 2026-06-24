// @ts-check
const { test, expect } = require('@playwright/test');
const path = require('path');

const FIXTURE = 'file://' + path.resolve(__dirname, 'fixtures/sample.html');

test.beforeEach(async ({ page }) => {
  await page.goto(FIXTURE);
});

test('page loads with lecture title in <title>', async ({ page }) => {
  const title = await page.title();
  expect(title).toContain('Cortisol');
});

test('course meta header is visible', async ({ page }) => {
  const meta = page.getByTestId('course-meta');
  await expect(meta).toBeVisible();
  await expect(meta).toContainText('Stress and Coping');
});

test('lecture title is displayed in header', async ({ page }) => {
  const heading = page.getByTestId('lecture-title');
  await expect(heading).toBeVisible();
  await expect(heading).toContainText('Cortisol');
});

test('all seven section tabs are visible', async ({ page }) => {
  const expectedTabs = ['Objectives', 'Outline', 'Hook', 'Discussion', 'Quiz', 'Concepts', 'Homework'];
  for (const label of expectedTabs) {
    const btn = page.locator(`.tab-btn`, { hasText: label });
    await expect(btn).toBeVisible();
  }
});

test('objectives tab is active by default', async ({ page }) => {
  const objectivesPanel = page.locator('#tab-objectives');
  await expect(objectivesPanel).toHaveClass(/active/);
});

test('objectives panel shows content', async ({ page }) => {
  const panel = page.locator('#tab-objectives');
  await expect(panel).toContainText('cortisol');
});

test('clicking Outline tab shows outline content', async ({ page }) => {
  await page.click('.tab-btn[data-tab="tab-outline"]');
  const panel = page.locator('#tab-outline');
  await expect(panel).toHaveClass(/active/);
  await expect(panel).toContainText('Introduction');
});

test('outline shows time ranges', async ({ page }) => {
  await page.click('.tab-btn[data-tab="tab-outline"]');
  await expect(page.locator('#tab-outline')).toContainText('0-5 min');
});

test('clicking Hook tab shows hook content', async ({ page }) => {
  await page.click('.tab-btn[data-tab="tab-hook"]');
  const panel = page.locator('#tab-hook');
  await expect(panel).toHaveClass(/active/);
  await expect(panel).toContainText('racing heart');
});

test('clicking Discussion tab shows discussion questions', async ({ page }) => {
  await page.click('.tab-btn[data-tab="tab-discussion"]');
  const panel = page.locator('#tab-discussion');
  await expect(panel).toHaveClass(/active/);
  await expect(panel).toContainText('Q1');
});

test('clicking Quiz tab shows quiz items', async ({ page }) => {
  await page.click('.tab-btn[data-tab="tab-quiz"]');
  const panel = page.locator('#tab-quiz');
  await expect(panel).toHaveClass(/active/);
  await expect(panel).toContainText('Question 1');
});

test('quiz shows A B C D options', async ({ page }) => {
  await page.click('.tab-btn[data-tab="tab-quiz"]');
  const panel = page.locator('#tab-quiz');
  for (const opt of ['A.', 'B.', 'C.', 'D.']) {
    await expect(panel).toContainText(opt);
  }
});

test('Show Answer button is present in quiz', async ({ page }) => {
  await page.click('.tab-btn[data-tab="tab-quiz"]');
  const btn = page.locator('.quiz-answer-btn').first();
  await expect(btn).toBeVisible();
  await expect(btn).toContainText('Show Answer');
});

test('Show Answer reveals rationale and correct option', async ({ page }) => {
  await page.click('.tab-btn[data-tab="tab-quiz"]');
  const answerBtn = page.locator('#answerBtn-0');
  await answerBtn.click();
  const rationale = page.locator('#rationale-0');
  await expect(rationale).toHaveClass(/visible/);
  await expect(rationale).toContainText('adrenal');
});

test('clicking Concepts tab shows key concepts', async ({ page }) => {
  await page.click('.tab-btn[data-tab="tab-concepts"]');
  const panel = page.locator('#tab-concepts');
  await expect(panel).toHaveClass(/active/);
  await expect(panel).toContainText('cortisol');
});

test('key concept term is styled distinctly', async ({ page }) => {
  await page.click('.tab-btn[data-tab="tab-concepts"]');
  const term = page.locator('.concept-term').first();
  await expect(term).toBeVisible();
});

test('clicking Homework tab shows assignment', async ({ page }) => {
  await page.click('.tab-btn[data-tab="tab-homework"]');
  const panel = page.locator('#tab-homework');
  await expect(panel).toHaveClass(/active/);
  await expect(panel).toContainText('diary');
});

test('copy button is visible per section', async ({ page }) => {
  const copyBtns = page.locator('.copy-btn');
  const count = await copyBtns.count();
  expect(count).toBeGreaterThanOrEqual(7);
});

test('export markdown button is present', async ({ page }) => {
  const btn = page.getByTestId('export-btn');
  await expect(btn).toBeVisible();
  await expect(btn).toContainText('Export');
});

test('page does not break at 375px (mobile)', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  const header = page.locator('header');
  await expect(header).toBeVisible();
  const tabBar = page.locator('.tab-bar');
  await expect(tabBar).toBeVisible();
});

test('switching tabs hides previous panel', async ({ page }) => {
  const objectivesPanel = page.locator('#tab-objectives');
  await expect(objectivesPanel).toHaveClass(/active/);
  await page.click('.tab-btn[data-tab="tab-outline"]');
  await expect(objectivesPanel).not.toHaveClass(/active/);
});

test('discussion question shows teaching note', async ({ page }) => {
  await page.click('.tab-btn[data-tab="tab-discussion"]');
  await expect(page.locator('#tab-discussion')).toContainText('Teaching note');
});

test('quiz second question is present', async ({ page }) => {
  await page.click('.tab-btn[data-tab="tab-quiz"]');
  await expect(page.locator('#tab-quiz')).toContainText('Question 2');
});
