const { test, expect } = require('@playwright/test');
const path = require('path');

const indexPath = 'file://' + path.join(__dirname, '..', 'index.html');

test.beforeEach(async ({ page }) => {
  const errors = [];
  page.on('pageerror', (err) => errors.push(err));
  page.on('console', (msg) => {
    if (msg.type() === 'error') errors.push(new Error(msg.text()));
  });
  page._collectedErrors = errors;
  await page.goto(indexPath);
});

test('page loads, canvas renders, and ICC readouts populate on load', async ({ page }) => {
  await expect(page.getByTestId('chart-canvas')).toBeVisible();
  const trueIccText = await page.getByTestId('true-icc').textContent();
  expect(trueIccText).toMatch(/^\d+\.\d{3}$/);
  const grandMeanText = await page.getByTestId('grand-mean').textContent();
  expect(grandMeanText).not.toBe('—');
  expect(page._collectedErrors).toHaveLength(0);
});

test('moving the tau slider to 0 sets the true ICC readout to 0.000', async ({ page }) => {
  const tauSlider = page.getByTestId('tau-slider');
  await tauSlider.fill('0');
  await tauSlider.dispatchEvent('input');
  await expect(page.getByTestId('true-icc')).toHaveText('0.000');
  await expect(page.getByTestId('tau-value')).toHaveText('0.0');
});

test('moving the tau slider updates the true ICC readout live without reload', async ({ page }) => {
  const before = await page.getByTestId('true-icc').textContent();
  const tauSlider = page.getByTestId('tau-slider');
  await tauSlider.fill('9');
  await tauSlider.dispatchEvent('input');
  const after = await page.getByTestId('true-icc').textContent();
  expect(after).not.toBe(before);
  // Confirm no navigation occurred (same document context still has our testids).
  await expect(page.getByTestId('chart-canvas')).toBeVisible();
});

test('regenerate produces a new dataset (group table values change) without reload', async ({ page }) => {
  const before = await page.getByTestId('group-table-body').innerText();
  await page.getByTestId('seed-input').fill('999');
  await page.getByTestId('regenerate-btn').click();
  const after = await page.getByTestId('group-table-body').innerText();
  expect(after).not.toBe(before);
});

test('switching to the one-small profile and regenerating shows a group with n=3', async ({ page }) => {
  await page.getByTestId('profile-select').selectOption('one-small');
  await page.getByTestId('regenerate-btn').click();
  const tableText = await page.getByTestId('group-table-body').innerText();
  expect(tableText).toContain('3');
});

test('a group with a small sample size shrinks more (lower weight) than a large one in the rendered table', async ({ page }) => {
  await page.getByTestId('profile-select').selectOption('one-small');
  await page.getByTestId('regenerate-btn').click();
  const rows = await page.getByTestId('group-table-body').locator('tr').allInnerTexts();
  const parsed = rows.map((r) => r.split('\t').map((s) => s.trim()));
  // Columns: Group, n, noPooling, shrinkageWeight, partialPooling
  const smallGroup = parsed.find((r) => r[1] === '3');
  const largeGroup = parsed.find((r) => r[1] === '30');
  expect(smallGroup).toBeTruthy();
  expect(largeGroup).toBeTruthy();
  expect(parseFloat(smallGroup[3])).toBeLessThan(parseFloat(largeGroup[3]));
});

test('quiz: selecting the correct answer marks it correct and increments the score', async ({ page }) => {
  // Question 0 (tau-zero) has a fixed, known correct choice at index 0.
  await page.getByTestId('quiz-choice-0-0').click();
  await expect(page.getByTestId('quiz-choice-0-0')).toHaveClass(/correct/);
  await expect(page.getByTestId('quiz-score')).toHaveText('1');
});

test('quiz: selecting an incorrect answer marks it incorrect and does not increment the score', async ({ page }) => {
  // Question 0's correct index is 0; choice 1 is wrong.
  await page.getByTestId('quiz-choice-0-1').click();
  await expect(page.getByTestId('quiz-choice-0-1')).toHaveClass(/incorrect/);
  await expect(page.getByTestId('quiz-choice-0-0')).toHaveClass(/correct/);
  await expect(page.getByTestId('quiz-score')).toHaveText('0');
});

test('quiz choices become disabled after answering', async ({ page }) => {
  await page.getByTestId('quiz-choice-1-1').click();
  await expect(page.getByTestId('quiz-choice-1-0')).toBeDisabled();
  await expect(page.getByTestId('quiz-choice-1-1')).toBeDisabled();
});

test('explain panel with no API key shows a deterministic explanation and makes no network request', async ({ page }) => {
  let requested = false;
  await page.route('https://api.anthropic.com/**', (route) => {
    requested = true;
    route.abort();
  });
  await page.getByTestId('explain-btn').click();
  await expect(page.getByTestId('explain-output')).not.toHaveText('');
  const text = await page.getByTestId('explain-output').textContent();
  expect(text).toContain('ICC');
  expect(requested).toBe(false);
});

test('explain panel renders a hostile mocked API response as inert text, not executed HTML', async ({ page }) => {
  await page.route('https://api.anthropic.com/v1/messages', (route) => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        content: [{ type: 'text', text: '<img src=x onerror="window.__xss=true">' }],
      }),
    });
  });
  await page.getByTestId('api-key-input').fill('fake-test-key-not-real');
  await page.getByTestId('explain-btn').click();
  await expect(page.getByTestId('explain-output')).toHaveText('<img src=x onerror="window.__xss=true">');
  const xssRan = await page.evaluate(() => window.__xss === true);
  expect(xssRan).toBe(false);
  const htmlContent = await page.getByTestId('explain-output').innerHTML();
  // innerHTML should show the escaped entities, proving textContent (not innerHTML) was used.
  expect(htmlContent).not.toContain('<img');
  expect(page._collectedErrors).toHaveLength(0);
});

test('page renders without horizontal overflow at a 375px mobile viewport', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 800 });
  await page.waitForTimeout(50);
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1);
  expect(overflow).toBe(false);
  await expect(page.getByTestId('chart-canvas')).toBeVisible();
});

test('quiz total reflects 8 questions (5 fixed + 3 dynamic)', async ({ page }) => {
  await expect(page.getByTestId('quiz-total')).toHaveText('8');
});
