const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

const pageUrl = `file://${path.resolve(__dirname, '../index.html')}`;
const srcDir = path.resolve(__dirname, '../src');

test.describe('Security', () => {
  test('no source file assigns innerHTML, calls eval/Function, or uses document.write', async () => {
    const files = fs.readdirSync(srcDir).filter((f) => f.endsWith('.js'));
    expect(files.length).toBeGreaterThan(0);
    for (const file of files) {
      const content = fs.readFileSync(path.join(srcDir, file), 'utf8');
      expect(content, `${file} must not assign innerHTML`).not.toMatch(/\.innerHTML\s*=/);
      expect(content, `${file} must not call eval()`).not.toMatch(/\beval\s*\(/);
      expect(content, `${file} must not construct Function() from a string`).not.toMatch(/new\s+Function\s*\(/);
      expect(content, `${file} must not call document.write`).not.toMatch(/document\.write/);
    }
  });

  test('no source file contains a hardcoded credential-like assignment', async () => {
    const files = fs.readdirSync(srcDir).filter((f) => f.endsWith('.js'));
    const credentialPattern = /(password|api[_-]?key|secret|private[_-]?key)\s*[:=]\s*['"][^'"]+['"]/i;
    for (const file of files) {
      const content = fs.readFileSync(path.join(srcDir, file), 'utf8');
      expect(content, `${file} must not hardcode credential-like values`).not.toMatch(credentialPattern);
    }
  });

  test('a full session (all tabs, pipeline steps, MC run, full quiz) produces zero dialogs and zero page errors', async ({ page }) => {
    const dialogs = [];
    const pageErrors = [];
    page.on('dialog', (dialog) => {
      dialogs.push(dialog.message());
      dialog.dismiss();
    });
    page.on('pageerror', (err) => pageErrors.push(err.message));

    await page.goto(pageUrl);

    // Exercise every pipeline step and both phases.
    for (let i = 0; i < 6; i++) {
      await page.locator('[data-testid="step-nav"] .step-nav-btn').nth(i).click();
      await page.locator('[data-testid="phase-after"]').click();
      await page.locator('[data-testid="phase-before"]').click();
    }

    // Exercise the Multiple Comparisons Lab.
    await page.locator('[data-testid="tab-mc"]').click();
    await page.locator('[data-testid="mc-run"]').click();

    // Exercise the full quiz.
    await page.locator('[data-testid="tab-quiz"]').click();
    const totalQuestions = await page.evaluate(() => window.VoxelQuiz.buildQuiz(1).length);
    for (let i = 0; i < totalQuestions; i++) {
      await page.locator('[data-testid="quiz-choices"] .choice-btn').first().click();
      await page.locator('[data-testid="quiz-next"]').click();
    }

    expect(dialogs).toEqual([]);
    expect(pageErrors).toEqual([]);
  });

  test('no network requests are made anywhere in the app', async ({ page }) => {
    const requests = [];
    page.on('request', (req) => {
      // file:// navigation of the page itself and its own local assets are
      // expected; anything else (http/https) would indicate a real network call.
      if (req.url().startsWith('http://') || req.url().startsWith('https://')) {
        requests.push(req.url());
      }
    });

    await page.goto(pageUrl);
    await page.locator('[data-testid="tab-mc"]').click();
    await page.locator('[data-testid="mc-run"]').click();
    await page.locator('[data-testid="tab-quiz"]').click();
    await page.locator('[data-testid="quiz-choices"] .choice-btn').first().click();

    expect(requests).toEqual([]);
  });
});
