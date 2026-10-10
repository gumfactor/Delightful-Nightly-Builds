const { test, expect } = require('@playwright/test');
const path = require('path');
const url = 'file://' + path.resolve(__dirname, '..', 'index.html');

test.beforeEach(async ({ page }) => {
  await page.goto(url);
});

test('results stay hidden until a draft is entered', async ({ page }) => {
  await expect(page.locator('#results')).toBeHidden();
  await expect(page.getByTestId('profile-status')).toContainText('No profile yet');
});

test('machine demo shows a high AI-tell score and highlighted spans with tooltips', async ({ page }) => {
  await page.getByTestId('demo-machine').click();
  await expect(page.locator('#results')).toBeVisible();
  expect(Number(await page.getByTestId('ai-score').textContent())).toBeGreaterThan(60);
  const marks = page.locator('[data-testid=highlighted] mark');
  expect(await marks.count()).toBeGreaterThan(10);
  await expect(marks.first()).toHaveAttribute('title', /.+/);
  await expect(page.getByTestId('voice-score')).toHaveText('–');
});

test('flag summary lists categories with counts', async ({ page }) => {
  await page.getByTestId('demo-machine').click();
  await expect(page.getByTestId('flag-summary')).toContainText('Stock AI vocabulary');
  await expect(page.getByTestId('flag-summary')).toContainText('×');
});

test('typing in the draft box live-updates the score', async ({ page }) => {
  await page.getByTestId('draft').fill('I burned the toast again. My kid laughed, then ate it anyway.');
  await expect(page.getByTestId('ai-score')).toHaveText('0');
  await page.getByTestId('draft').fill("It's important to note that we must delve into the rich tapestry.");
  await expect(page.getByTestId('ai-score')).not.toHaveText('0');
});

test('building a profile enables voice match and persists across reload', async ({ page }) => {
  await page.getByTestId('demo-human').click();
  await page.getByTestId('build-profile').click();
  await expect(page.getByTestId('profile-status')).toContainText('Profile ready: 1 sample');
  await page.getByTestId('demo-machine').click();
  const score = Number(await page.getByTestId('voice-score').textContent());
  expect(score).toBeLessThan(45);
  await page.reload();
  await expect(page.getByTestId('profile-status')).toContainText('Profile ready');
});

test('a too-short baseline shows an error and creates no profile', async ({ page }) => {
  await page.getByTestId('baseline').fill('Only a few words.');
  await page.getByTestId('build-profile').click();
  await expect(page.getByTestId('profile-status')).toContainText('40 words');
  await page.reload();
  await expect(page.getByTestId('profile-status')).toContainText('No profile yet');
});

test('profile exports as JSON and re-imports after clearing', async ({ page }) => {
  await page.getByTestId('demo-human').click();
  await page.getByTestId('build-profile').click();
  await page.locator('summary').click();
  await page.getByTestId('export-profile').click();
  const json = await page.getByTestId('profile-json').inputValue();
  expect(JSON.parse(json).version).toBe(1);
  await page.getByTestId('clear-profile').click();
  await expect(page.getByTestId('profile-status')).toContainText('No profile yet');
  await page.getByTestId('profile-json').fill(json);
  await page.getByTestId('import-profile').click();
  await expect(page.getByTestId('profile-status')).toContainText('Profile ready');
});

test('importing invalid JSON reports a failure and keeps state clean', async ({ page }) => {
  await page.locator('summary').click();
  await page.getByTestId('profile-json').fill('{"nope": true}');
  await page.getByTestId('import-profile').click();
  await expect(page.getByTestId('profile-status')).toContainText('Import failed');
});

test('revision prompt is generated for the current draft', async ({ page }) => {
  await page.getByTestId('demo-machine').click();
  await page.getByTestId('make-prompt').click();
  const value = await page.getByTestId('prompt').inputValue();
  expect(value).toContain('DRAFT:');
  expect(value).toContain('In today');
});

test('HTML in a draft is escaped, not executed', async ({ page }) => {
  await page.evaluate(() => { window.__xss = false; });
  await page.getByTestId('draft').fill('<img src=x onerror="window.__xss=true"> <script>window.__xss=true</script> We delve into it.');
  await expect(page.getByTestId('highlighted')).toContainText('<script>');
  expect(await page.evaluate(() => window.__xss)).toBe(false);
  expect(await page.locator('[data-testid=highlighted] img').count()).toBe(0);
});

test('rhythm chart draws one bar per sentence', async ({ page }) => {
  await page.getByTestId('draft').fill('One. Two words here. A much longer third sentence follows now.');
  await expect(page.locator('[data-testid=rhythm] .bar')).toHaveCount(3);
});

test('clearing the draft hides the results again', async ({ page }) => {
  await page.getByTestId('demo-machine').click();
  await expect(page.locator('#results')).toBeVisible();
  await page.getByTestId('clear-draft').click();
  await expect(page.locator('#results')).toBeHidden();
});
