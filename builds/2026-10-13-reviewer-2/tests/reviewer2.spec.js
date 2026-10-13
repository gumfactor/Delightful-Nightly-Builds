const { test, expect } = require('@playwright/test');
const path = require('path');
const url = 'file://' + path.resolve(__dirname, '..', 'index.html');

test.beforeEach(async ({ page }) => {
  await page.goto(url);
  await page.evaluate(() => { localStorage.clear(); sessionStorage.clear(); });
  await page.goto(url);
});

// Click the correct (or a wrong) choice for the case currently on screen.
async function answerCurrent(page, wantCorrect) {
  const title = await page.getByTestId('case-title').textContent();
  const flaw = await page.evaluate((t) => CASES.find((c) => c.title === t).flaw, title);
  const buttons = page.getByTestId('choice');
  const n = await buttons.count();
  for (let i = 0; i < n; i++) {
    const f = await buttons.nth(i).getAttribute('data-flaw');
    if ((f === flaw) === wantCorrect) { await buttons.nth(i).click(); return; }
  }
}

async function openFresh(page, key) {
  await page.getByText('Fresh cases from Claude').click();
  if (key) {
    await page.getByTestId('key-input').fill(key);
    await page.getByTestId('key-save').click();
  }
}

test.describe('case data integrity', () => {
  test('every case has a valid flaw, explanation and hint', async ({ page }) => {
    const bad = await page.evaluate(() => CASES.filter((c) => !R2.validateCase(c, FLAWS)).map((c) => c.id));
    expect(bad).toEqual([]);
  });
  test('case ids are unique and there are at least 30 cases', async ({ page }) => {
    const info = await page.evaluate(() => ({ n: CASES.length, u: new Set(CASES.map((c) => c.id)).size }));
    expect(info.n).toBeGreaterThanOrEqual(30);
    expect(info.u).toBe(info.n);
  });
  test('every flaw type is used by at least two cases', async ({ page }) => {
    const counts = await page.evaluate(() => FLAWS.map((f) => CASES.filter((c) => c.flaw === f.id).length));
    counts.forEach((c) => expect(c).toBeGreaterThanOrEqual(2));
  });
});

test.describe('pure logic', () => {
  test('daily cases are deterministic per date and differ across dates', async ({ page }) => {
    const r = await page.evaluate(() => {
      const ids = (d) => R2.dailyCases(d, CASES).map((c) => c.id).join(',');
      return { a: ids('2026-10-13'), b: ids('2026-10-13'), c: ids('2026-10-14'), len: R2.dailyCases('2026-10-13', CASES).length };
    });
    expect(r.a).toBe(r.b);
    expect(r.a).not.toBe(r.c);
    expect(r.len).toBe(8);
  });
  test('daily cases contain no duplicates', async ({ page }) => {
    const ok = await page.evaluate(() => { const ids = R2.dailyCases('2026-01-01', CASES).map((c) => c.id); return new Set(ids).size === ids.length; });
    expect(ok).toBe(true);
  });
  test('choices contain the correct flaw exactly once among 4 unique options', async ({ page }) => {
    const ok = await page.evaluate(() => CASES.every((c) => {
      const ch = R2.choicesFor(c, FLAWS, R2.mulberry32(c.id));
      return ch.length === 4 && new Set(ch).size === 4 && ch.filter((x) => x === c.flaw).length === 1;
    }));
    expect(ok).toBe(true);
  });
  test('scoring: base, streak bonus capped, hint penalty, wrong is zero', async ({ page }) => {
    const s = await page.evaluate(() => [R2.scoreFor(true, 1, false), R2.scoreFor(true, 3, false), R2.scoreFor(true, 20, false), R2.scoreFor(true, 1, true), R2.scoreFor(false, 0, false)]);
    expect(s).toEqual([10, 14, 20, 6, 0]);
  });
  test('rank thresholds map points to titles', async ({ page }) => {
    const r = await page.evaluate(() => [R2.rankFor(0), R2.rankFor(40), R2.rankFor(100), R2.rankFor(500)]);
    expect(r).toEqual(['Desk Rejection', 'Reviewer 3', 'Reviewer 2', 'Associate Editor']);
  });
  test('practice weights favour missed flaws', async ({ page }) => {
    const share = await page.evaluate(() => {
      const stats = R2.emptyStats();
      FLAWS.forEach((f) => { stats.flaws[f.id] = { seen: 10, right: 10 }; });
      stats.flaws.baserate = { seen: 10, right: 0 };
      let hits = 0;
      for (let i = 0; i < 300; i++) {
        if (R2.pickPractice(stats, CASES, 1, R2.mulberry32(i + 1))[0].flaw === 'baserate') hits++;
      }
      return hits / 300;
    });
    expect(share).toBeGreaterThan(0.2); // uniform would be about 12%
  });
  test('practice returns requested count without repeats', async ({ page }) => {
    const ok = await page.evaluate(() => { const p = R2.pickPractice(R2.emptyStats(), CASES, 8, R2.mulberry32(5)); return p.length === 8 && new Set(p.map((c) => c.id)).size === 8; });
    expect(ok).toBe(true);
  });
  test('parseAiCase accepts JSON wrapped in prose and rejects bad output', async ({ page }) => {
    const r = await page.evaluate(() => {
      const good = 'Here: {"flaw":"power","title":"Tiny study","text":"Six people took a pill.","hint":"How many people?","explain":"Too few participants."} done';
      return [
        !!R2.parseAiCase(good, FLAWS),
        R2.parseAiCase('{"flaw":"nonsense","title":"Tiny study","text":"Six people took a pill.","hint":"How many?","explain":"Too few."}', FLAWS),
        R2.parseAiCase('not json at all', FLAWS),
        R2.parseAiCase('{"flaw":"power"', FLAWS),
        R2.parseAiCase(null, FLAWS),
      ];
    });
    expect(r).toEqual([true, null, null, null, null]);
  });
});

test.describe('UI flow', () => {
  test('home shows rank and a row for each flaw type', async ({ page }) => {
    await expect(page.getByTestId('rank')).toHaveText('Desk Rejection');
    await expect(page.getByTestId('flaw-row')).toHaveCount(12);
  });
  test('daily round plays 8 cases and perfect play scores 130', async ({ page }) => {
    await page.getByTestId('daily-btn').click();
    for (let i = 0; i < 8; i++) {
      await expect(page.getByTestId('progress')).toHaveText(`Case ${i + 1} / 8`);
      await answerCurrent(page, true);
      await page.getByTestId('next-btn').click();
    }
    await expect(page.getByTestId('results')).toBeVisible();
    await expect(page.getByTestId('final-correct')).toHaveText('8 / 8');
    await expect(page.getByTestId('final-score')).toHaveText('130');
  });
  test('wrong answer reveals the flaw and explanation and resets streak', async ({ page }) => {
    await page.getByTestId('practice-btn').click();
    await answerCurrent(page, true);
    await expect(page.getByTestId('streak')).toHaveText('1');
    await page.getByTestId('next-btn').click();
    await answerCurrent(page, false);
    await expect(page.getByTestId('feedback-head')).toContainText('Not quite');
    await expect(page.getByTestId('feedback-body')).not.toBeEmpty();
    await expect(page.getByTestId('streak')).toHaveText('0');
  });
  test('answer buttons lock after answering', async ({ page }) => {
    await page.getByTestId('practice-btn').click();
    await answerCurrent(page, true);
    for (const b of await page.getByTestId('choice').all()) await expect(b).toBeDisabled();
  });
  test('hint reduces the points for a correct answer', async ({ page }) => {
    await page.getByTestId('practice-btn').click();
    await page.getByTestId('hint-btn').click();
    await expect(page.getByTestId('hint')).toBeVisible();
    await answerCurrent(page, true);
    await expect(page.getByTestId('points')).toHaveText('6');
  });
  test('stats persist across reload and daily score is recorded', async ({ page }) => {
    await page.getByTestId('daily-btn').click();
    for (let i = 0; i < 8; i++) { await answerCurrent(page, false); await page.getByTestId('next-btn').click(); }
    await expect(page.getByTestId('final-score')).toHaveText('0');
    await page.reload();
    const seen = await page.evaluate(() => Object.values(JSON.parse(localStorage.getItem('reviewer2.stats.v1')).flaws).reduce((s, e) => s + e.seen, 0));
    expect(seen).toBe(8);
    await expect(page.locator('#daily-status')).toContainText("Today's score: 0");
  });
  test('missed flaws are listed on the results screen', async ({ page }) => {
    await page.getByTestId('daily-btn').click();
    for (let i = 0; i < 8; i++) { await answerCurrent(page, false); await page.getByTestId('next-btn').click(); }
    await expect(page.getByTestId('missed')).toContainText('Review these');
  });
});

test.describe('fresh case mode (mocked API)', () => {
  const body = { content: [{ type: 'text', text: JSON.stringify({ flaw: 'power', title: 'Mock study', text: 'Five people tried a new drug.', hint: 'How many?', explain: 'Too few people.' }) }] };

  test('requires an API key', async ({ page }) => {
    await openFresh(page);
    await page.getByTestId('fresh-btn').click();
    await expect(page.getByTestId('ai-status')).toContainText('Enter an Anthropic API key');
  });
  test('plays three generated cases and sends the key header', async ({ page }) => {
    let header = null;
    await page.route('https://api.anthropic.com/v1/messages', (route) => {
      header = route.request().headers()['x-api-key'];
      route.fulfill({ json: body });
    });
    await openFresh(page, 'test-key');
    await page.getByTestId('fresh-btn').click();
    await expect(page.getByTestId('case-title')).toHaveText('Mock study');
    await expect(page.getByTestId('progress')).toHaveText('Case 1 / 3');
    expect(header).toBe('test-key');
  });
  test('malformed model output shows an error and stays on home', async ({ page }) => {
    await page.route('https://api.anthropic.com/v1/messages', (route) => route.fulfill({ json: { content: [{ type: 'text', text: 'sorry, no' }] } }));
    await openFresh(page, 'k');
    await page.getByTestId('fresh-btn').click();
    await expect(page.getByTestId('ai-status')).toContainText('unusable case');
    await expect(page.getByTestId('home')).toBeVisible();
  });
  test('API error status is surfaced', async ({ page }) => {
    await page.route('https://api.anthropic.com/v1/messages', (route) => route.fulfill({ status: 401, json: {} }));
    await openFresh(page, 'bad');
    await page.getByTestId('fresh-btn').click();
    await expect(page.getByTestId('ai-status')).toContainText('API error 401');
  });
  test('API key is never written to localStorage', async ({ page }) => {
    await openFresh(page, 'secret-123');
    const dump = await page.evaluate(() => JSON.stringify(localStorage));
    expect(dump).not.toContain('secret-123');
  });
});
