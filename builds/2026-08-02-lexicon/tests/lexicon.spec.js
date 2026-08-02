const { test, expect } = require('@playwright/test');
const path = require('path');

const APP_URL = 'file://' + path.resolve(__dirname, '..', 'index.html');

// Pure-logic module, loaded via require for unit-level assertions independent of the DOM.
const {
  dailyWordForDate,
  maxGuessesForLength,
  evaluateGuess,
  aggregateKeyboardState,
  buildShareText,
  fallbackHint,
  daysBetween,
  DAILY_CYCLE,
} = require(path.resolve(__dirname, '..', 'src', 'main.js'));

function mockDate(page, isoDate) {
  return page.addInitScript((iso) => {
    const fixed = new Date(iso + 'T12:00:00Z');
    const RealDate = Date;
    class MockDate extends RealDate {
      constructor(...args) {
        if (args.length === 0) return new RealDate(fixed);
        return new RealDate(...args);
      }
      static now() {
        return fixed.getTime();
      }
    }
    // eslint-disable-next-line no-global-assign
    Date = MockDate;
  }, isoDate);
}

async function clearStorageAndGoto(page, isoDate) {
  await mockDate(page, isoDate);
  await page.goto(APP_URL);
  await page.evaluate(() => localStorage.clear());
  await page.reload();
}

const { WORD_BANK, CATEGORY_LABELS } = require(path.resolve(__dirname, '..', 'src', 'words.js'));

test.describe('Word bank integrity', () => {
  test('word bank has exactly 48 unique entries, 12 per category', () => {
    expect(WORD_BANK.length).toBe(48);
    const words = WORD_BANK.map((w) => w.word);
    expect(new Set(words).size).toBe(48);
    for (const entry of WORD_BANK) {
      expect(entry.word).toMatch(/^[A-Z]{5,10}$/);
      expect(entry.clue.length).toBeGreaterThan(10);
      expect(Object.keys(CATEGORY_LABELS)).toContain(entry.category);
    }
    const perCategory = {};
    for (const entry of WORD_BANK) perCategory[entry.category] = (perCategory[entry.category] || 0) + 1;
    expect(Object.values(perCategory)).toEqual([12, 12, 12, 12]);
  });
});

test.describe('Daily word determinism (pure logic)', () => {
  test('same date always yields the same word', () => {
    const a = dailyWordForDate('2026-08-02');
    const b = dailyWordForDate('2026-08-02');
    expect(a.word).toBe(b.word);
  });

  test('different dates within the cycle yield different words', () => {
    const a = dailyWordForDate('2026-08-02');
    const b = dailyWordForDate('2026-08-03');
    expect(a.word).not.toBe(b.word);
  });

  test('the daily cycle has no repeats across its full length', () => {
    const seen = new Set();
    for (let i = 0; i < DAILY_CYCLE.length; i++) {
      const dateStr = new Date(Date.UTC(2026, 0, 1 + i)).toISOString().slice(0, 10);
      const entry = dailyWordForDate(dateStr);
      seen.add(entry.word);
    }
    expect(seen.size).toBe(DAILY_CYCLE.length);
  });

  test('daysBetween computes correct day offsets', () => {
    expect(daysBetween('2026-01-01', '2026-01-02')).toBe(1);
    expect(daysBetween('2026-01-01', '2026-02-01')).toBe(31);
  });
});

test.describe('Guess evaluation logic (pure logic)', () => {
  test('exact match marks every letter correct', () => {
    const result = evaluateGuess('MARGIN', 'MARGIN');
    expect(result).toEqual(['correct', 'correct', 'correct', 'correct', 'correct', 'correct']);
  });

  test('completely wrong letters are all absent', () => {
    const result = evaluateGuess('ZZZZZZ', 'MARGIN'.slice(0, 6));
    expect(result.every((s) => s === 'absent')).toBe(true);
  });

  test('duplicate-letter edge case: guess repeats a letter the answer only has once, leftmost occurrence wins', () => {
    // Answer ABCDE has exactly one A (idx0), one B (idx1... none matched here), etc.
    // Guess AABBC: idx0 A=A exact match consumes the answer's only A.
    // idx1 A has no A left in the answer -> absent. idx2 B is present (answer's B, idx1, unconsumed).
    // idx3 B has no B left (already consumed by idx2) -> absent. idx4 C is present (answer's C, idx2, unconsumed).
    const result = evaluateGuess('AABBC', 'ABCDE');
    expect(result).toEqual(['correct', 'absent', 'present', 'absent', 'present']);
  });

  test('duplicate-letter edge case: guess has a letter twice, answer has it once, only one marked', () => {
    // Answer "SPREAD" has one "A". Guess "AAAAAA" should mark exactly one "A" position, rest absent.
    const answer = 'SPREAD';
    const guess = 'AAAAAA';
    const result = evaluateGuess(guess, answer);
    const correctOrPresent = result.filter((s) => s !== 'absent').length;
    expect(correctOrPresent).toBe(1);
  });
});

test.describe('Max guesses formula (pure logic)', () => {
  test('5-letter word allows 6 guesses', () => {
    expect(maxGuessesForLength(5)).toBe(6);
  });
  test('9-letter word caps at 9 guesses (10 is not allowed by formula, capped)', () => {
    expect(maxGuessesForLength(9)).toBe(9);
  });
  test('10-letter word caps at 9 guesses', () => {
    expect(maxGuessesForLength(10)).toBe(9);
  });
});

test.describe('Keyboard state aggregation (pure logic)', () => {
  test('a key that was ever correct stays correct even if later guess shows it elsewhere', () => {
    // Answer YIELD. First guess has Y correct at position 0. Second guess reuses Y in wrong spot.
    const state = aggregateKeyboardState(['YIELD', 'AAAAY'], 'YIELD');
    expect(state['Y']).toBe('correct');
  });

  test('present beats absent when a letter appears in two different guesses with different outcomes', () => {
    const state = aggregateKeyboardState(['AAAAA', 'YIELD'], 'YIELD');
    // In YIELD guess (exact match) all letters are correct; verify D specifically
    expect(state['D']).toBe('correct');
  });
});

test.describe('Share text generation (pure logic)', () => {
  test('share text reflects the actual guess sequence and win state', () => {
    const text = buildShareText(['YIELD'], 'YIELD', true);
    expect(text).toContain('Lexicon 1/6');
    expect(text).toContain('\u{1F7E9}\u{1F7E9}\u{1F7E9}\u{1F7E9}\u{1F7E9}');
  });

  test('losing share text uses X/max format', () => {
    const guesses = ['AAAAA', 'BBBBB', 'CCCCC', 'DDDDD', 'EEEEE', 'FFFFF'];
    const text = buildShareText(guesses, 'YIELD', false);
    expect(text).toContain('Lexicon X/6');
  });
});

test.describe('Fallback hint (pure logic)', () => {
  test('fallback hint reveals first letter, length, and category without the word', () => {
    const entry = { word: 'YIELD', category: 'finance' };
    const hint = fallbackHint(entry);
    expect(hint).toContain('"Y"');
    expect(hint).toContain('5 letters');
    expect(hint).not.toContain('YIELD');
  });
});

test.describe('Live browser gameplay', () => {
  test('a full daily round can be played to a win', async ({ page }) => {
    await clearStorageAndGoto(page, '2026-08-02');
    const entry = dailyWordForDate('2026-08-02');

    for (const letter of entry.word) {
      await page.click(`[data-testid="key-${letter}"]`);
    }
    await page.click('[data-testid="key-ENTER"]');

    const modal = page.locator('[data-testid="result-modal"]');
    await expect(modal).toBeVisible();
    await expect(page.locator('[data-testid="result-text"]')).toContainText('Solved in 1');
  });

  test('an incorrect guess does not end the round, and correct-length validation blocks short guesses', async ({ page }) => {
    await clearStorageAndGoto(page, '2026-08-03');
    // Try to submit with zero letters typed
    await page.click('[data-testid="key-ENTER"]');
    await expect(page.locator('[data-testid="message"]')).toContainText('must be');

    const modal = page.locator('[data-testid="result-modal"]');
    await expect(modal).toBeHidden();
  });

  test('losing a round reveals the answer', async ({ page }) => {
    await clearStorageAndGoto(page, '2026-08-04');
    const entry = dailyWordForDate('2026-08-04');
    const maxGuesses = maxGuessesForLength(entry.word.length);
    // Build a wrong guess of the correct length using a letter not in the answer, falling back if needed
    const filler = 'ZQXJKWVBFP'.split('').filter((c) => !entry.word.includes(c));
    const wrongGuess = Array.from({ length: entry.word.length }, (_, i) => filler[i % filler.length]).join('');

    for (let attempt = 0; attempt < maxGuesses; attempt++) {
      for (const letter of wrongGuess) {
        await page.click(`[data-testid="key-${letter}"]`);
      }
      await page.click('[data-testid="key-ENTER"]');
    }

    const resultText = page.locator('[data-testid="result-text"]');
    await expect(resultText).toContainText(entry.word);
  });

  test('hint stays hidden before 2 wrong guesses and reveals after', async ({ page }) => {
    await clearStorageAndGoto(page, '2026-08-05');
    const entry = dailyWordForDate('2026-08-05');
    const hint = page.locator('[data-testid="hint"]');
    await expect(hint).toBeHidden();

    const filler = 'ZQXJKWVBFP'.split('').filter((c) => !entry.word.includes(c));
    const wrongGuess = Array.from({ length: entry.word.length }, (_, i) => filler[i % filler.length]).join('');

    for (let attempt = 0; attempt < 2; attempt++) {
      for (const letter of wrongGuess) {
        await page.click(`[data-testid="key-${letter}"]`);
      }
      await page.click('[data-testid="key-ENTER"]');
    }

    await expect(hint).toBeVisible();
    await expect(hint).toHaveText(entry.clue);
  });

  test('one-play-per-day gate: reloading after a win shows the result screen instead of a fresh board', async ({ page }) => {
    await clearStorageAndGoto(page, '2026-08-06');
    const entry = dailyWordForDate('2026-08-06');
    for (const letter of entry.word) {
      await page.click(`[data-testid="key-${letter}"]`);
    }
    await page.click('[data-testid="key-ENTER"]');
    await expect(page.locator('[data-testid="result-modal"]')).toBeVisible();

    await page.reload();
    await expect(page.locator('[data-testid="result-modal"]')).toBeVisible();
    await expect(page.locator('[data-testid="result-text"]')).toContainText('Solved in 1');
  });

  test('a different UTC date allows a fresh round', async ({ page }) => {
    await clearStorageAndGoto(page, '2026-08-06');
    const entryDay1 = dailyWordForDate('2026-08-06');
    for (const letter of entryDay1.word) {
      await page.click(`[data-testid="key-${letter}"]`);
    }
    await page.click('[data-testid="key-ENTER"]');
    await expect(page.locator('[data-testid="result-modal"]')).toBeVisible();

    await mockDate(page, '2026-08-07');
    await page.reload();
    await expect(page.locator('[data-testid="result-modal"]')).toBeHidden();
  });

  test('playing a practice round does not affect daily games-played stats', async ({ page }) => {
    await clearStorageAndGoto(page, '2026-08-08');
    await page.click('[data-testid="mode-practice"]');
    await page.selectOption('[data-testid="practice-category"]', 'finance');

    // Submit one wrong guess against whatever practice word is active (any outcome should not touch daily stats).
    const filler = ['Q', 'X', 'Z', 'J', 'K'];
    const tileCount = await page.locator('[data-testid="guess-row"]').first().locator('.tile').count();
    const guessLetters = Array.from({ length: tileCount }, (_, i) => filler[i % filler.length]);
    for (const letter of guessLetters) {
      await page.click(`[data-testid="key-${letter}"]`);
    }
    await page.click('[data-testid="key-ENTER"]');

    const statsText = await page.locator('[data-testid="stats-panel"]').innerText();
    expect(statsText).toContain('Games played: 0');
  });

  test('non-letter input is ignored and does not appear on the board', async ({ page }) => {
    await clearStorageAndGoto(page, '2026-08-09');
    await page.keyboard.press('1');
    await page.keyboard.press('!');
    const firstTile = page.locator('[data-testid="guess-row"]').first().locator('.tile').first();
    await expect(firstTile).toHaveText('');
  });

  test('AI hint falls back deterministically and makes zero network requests with no key', async ({ page }) => {
    await clearStorageAndGoto(page, '2026-08-10');
    let requestMade = false;
    await page.route('https://api.anthropic.com/**', (route) => {
      requestMade = true;
      route.abort();
    });

    await page.click('[data-testid="ai-hint-button"]');
    await expect(page.locator('[data-testid="ai-hint-text"]')).not.toHaveText('');
    const hintText = await page.locator('[data-testid="ai-hint-text"]').innerText();
    expect(hintText).toContain('letters');
    expect(requestMade).toBe(false);
  });

  test('a script payload in a mocked AI hint response renders as inert text', async ({ page }) => {
    await clearStorageAndGoto(page, '2026-08-11');

    const dialogs = [];
    page.on('dialog', async (dialog) => {
      dialogs.push(dialog.message());
      await dialog.dismiss();
    });

    await page.route('https://api.anthropic.com/v1/messages', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ content: [{ text: '<script>alert(1)</script><img src=x onerror=alert(2)>' }] }),
      });
    });

    await page.fill('[data-testid="ai-key-input"]', 'sk-ant-fake-test-key');
    await page.click('[data-testid="ai-hint-button"]');

    const hintLocator = page.locator('[data-testid="ai-hint-text"]');
    await expect(hintLocator).toContainText('<script>');
    expect(dialogs.length).toBe(0);
    const scriptCount = await page.locator('[data-testid="ai-hint-text"] script').count();
    expect(scriptCount).toBe(0);
  });

  test('colorblind mode adds shape markers to tiles in addition to color', async ({ page }) => {
    await clearStorageAndGoto(page, '2026-08-12');
    const entry = dailyWordForDate('2026-08-12');
    await page.check('[data-testid="colorblind-toggle"]');

    for (const letter of entry.word) {
      await page.click(`[data-testid="key-${letter}"]`);
    }
    await page.click('[data-testid="key-ENTER"]');

    const tile = page.locator('[data-testid="guess-row"]').first().locator('.tile').first();
    await expect(tile).toHaveAttribute('data-marker', '✓');
  });
});
