const { test, expect } = require('@playwright/test');
const path = require('path');

const PAGE = 'file://' + path.resolve(__dirname, '..', 'index.html');

test.beforeEach(async ({ page }) => {
  await page.goto(PAGE);
});

test('probit and normalCdf are inverses at familiar z values', async ({ page }) => {
  const out = await page.evaluate(() => ({
    z975: NAStats.probit(0.975), cdf196: NAStats.normalCdf(1.96), mid: NAStats.probit(0.5), neg: NAStats.normalCdf(-1),
  }));
  expect(out.z975).toBeCloseTo(1.96, 2);
  expect(out.cdf196).toBeCloseTo(0.975, 3);
  expect(out.mid).toBeCloseTo(0, 6);
  expect(out.neg).toBeCloseTo(0.1587, 3);
});

test('probit rejects probabilities of exactly 0 or 1', async ({ page }) => {
  const out = await page.evaluate(() => {
    const attempt = (p) => { try { NAStats.probit(p); return 'ok'; } catch (e) { return e.name; } };
    return [attempt(0), attempt(1), attempt(0.3)];
  });
  expect(out).toEqual(['RangeError', 'RangeError', 'ok']);
});

test('d-prime stays finite for perfect and zero performance and is about 0 at chance', async ({ page }) => {
  const out = await page.evaluate(() => ({
    perfect: NAStats.dPrime(10, 10, 0, 30),
    worst: NAStats.dPrime(0, 10, 30, 30),
    chance: NAStats.dPrime(5, 10, 15, 30),
    empty: NAStats.dPrime(0, 0, 0, 10),
  }));
  expect(Number.isFinite(out.perfect)).toBe(true);
  expect(out.perfect).toBeGreaterThan(3);
  expect(out.worst).toBeLessThan(-3);
  expect(Math.abs(out.chance)).toBeLessThan(0.1);
  expect(out.empty).toBeNull();
});

test('mean and sd handle empty and single-value input without NaN', async ({ page }) => {
  const out = await page.evaluate(() => ({
    mean: NAStats.mean([]), sdOne: NAStats.sd([5]), sd: NAStats.sd([2, 4, 4, 4, 5, 5, 7, 9]),
  }));
  expect(out.mean).toBeNull();
  expect(out.sdOne).toBeNull();
  expect(out.sd).toBeCloseTo(2.138, 3);
});

test('seeded generators are reproducible and different seeds differ', async ({ page }) => {
  const out = await page.evaluate(() => {
    const a = NATasks.stroopTrials(20, NATasks.makeRng(7));
    const b = NATasks.stroopTrials(20, NATasks.makeRng(7));
    const c = NATasks.stroopTrials(20, NATasks.makeRng(8));
    return { same: JSON.stringify(a) === JSON.stringify(b), differ: JSON.stringify(a) !== JSON.stringify(c) };
  });
  expect(out).toEqual({ same: true, differ: true });
});

test('Stroop trials are half incongruent and incongruent words never match their ink', async ({ page }) => {
  const trials = await page.evaluate(() => NATasks.stroopTrials(48, NATasks.makeRng(1)));
  const incongruent = trials.filter((t) => t.condition === 'incongruent');
  expect(incongruent).toHaveLength(24);
  expect(incongruent.every((t) => t.word !== t.ink)).toBe(true);
  expect(trials.filter((t) => t.condition === 'congruent').every((t) => t.word === t.ink)).toBe(true);
});

test('n-back targets repeat the letter two back and nothing else does', async ({ page }) => {
  const seq = await page.evaluate(() => NATasks.nbackSequence(200, 2, NATasks.makeRng(3), 0.3));
  expect(seq[0].isTarget || seq[1].isTarget).toBe(false);
  seq.forEach((item, i) => {
    if (i < 2) return;
    expect(item.letter === seq[i - 2].letter).toBe(item.isTarget);
  });
  const rate = seq.filter((s) => s.isTarget).length / 198;
  expect(rate).toBeGreaterThan(0.2);
  expect(rate).toBeLessThan(0.4);
});

test('Go/No-Go has the requested No-Go share and Ultimatum covers every offer evenly', async ({ page }) => {
  const out = await page.evaluate(() => ({
    gng: NATasks.goNoGoTrials(60, NATasks.makeRng(2), 0.25).filter((t) => t.kind === 'nogo').length,
    tiny: NATasks.goNoGoTrials(2, NATasks.makeRng(2), 0.1).filter((t) => t.kind === 'nogo').length,
    offers: NATasks.ultimatumOffers(20, NATasks.makeRng(2)).map((o) => o.offer),
  }));
  expect(out.gng).toBe(15);
  expect(out.tiny).toBe(1);
  for (let amount = 1; amount <= 5; amount++) expect(out.offers.filter((o) => o === amount)).toHaveLength(4);
});

test('Stroop scoring computes interference from correct trials only', async ({ page }) => {
  const metrics = await page.evaluate(() => NATasks.scoreStroop([
    { condition: 'congruent', response: 'red', correct: true, rt: 500 },
    { condition: 'congruent', response: 'red', correct: true, rt: 600 },
    { condition: 'incongruent', response: 'blue', correct: true, rt: 700 },
    { condition: 'incongruent', response: 'red', correct: false, rt: 200 },
    { condition: 'incongruent', response: null, correct: false, rt: null },
  ]));
  expect(metrics.congruentRt).toBe(550);
  expect(metrics.incongruentRt).toBe(700);
  expect(metrics.interference).toBe(150);
  expect(metrics.accuracy).toBe(0.6);
  expect(metrics.timeouts).toBe(1);
});

test('scorers return nulls instead of throwing when every trial timed out', async ({ page }) => {
  const out = await page.evaluate(() => {
    const timeouts = (condition) => Array.from({ length: 4 }, () => ({ condition, stimulus: '1', response: null, correct: false, rt: null }));
    return {
      stroop: NATasks.scoreStroop(timeouts('incongruent')),
      empty: NATasks.scoreStroop([]),
      ultimatum: NATasks.scoreUltimatum(timeouts('offer_1')),
    };
  });
  expect(out.stroop.interference).toBeNull();
  expect(out.empty.accuracy).toBeNull();
  expect(out.ultimatum.lowestAccepted).toBeNull();
});

test('n-back and Go/No-Go scorers count hits, false alarms, and commission rate', async ({ page }) => {
  const out = await page.evaluate(() => {
    const t = (condition, response, rt) => ({ condition, response, correct: null, rt });
    const nback = NATasks.scoreNback([
      t('target', 'press', 600), t('target', 'press', 700), t('target', null, null),
      t('nontarget', 'press', 500), t('nontarget', null, null), t('nontarget', null, null), t('nontarget', null, null),
    ]);
    const gng = NATasks.scoreGoNoGo([
      t('go', 'press', 300), t('go', 'press', 340), t('go', null, null),
      t('nogo', 'press', 250), t('nogo', null, null),
    ]);
    return { nback, gng };
  });
  expect(out.nback).toMatchObject({ hits: 2, targets: 3, falseAlarms: 1, hitRt: 650 });
  expect(out.nback.dPrime).toBeGreaterThan(0.5);
  expect(out.gng).toMatchObject({ hits: 2, goTrials: 3, commissions: 1, nogoTrials: 2, commissionRate: 0.5, goRt: 320 });
});

test('Ultimatum scoring reports unfair rejection, lowest accepted offer, and per-offer rates', async ({ page }) => {
  const m = await page.evaluate(() => {
    const t = (offer, response) => ({ condition: 'offer_' + offer, stimulus: String(offer), response, correct: null, rt: 800 });
    return NATasks.scoreUltimatum([t(1, 'reject'), t(2, 'reject'), t(2, 'accept'), t(3, 'accept'), t(5, 'accept')]);
  });
  expect(m.rejectUnfair).toBeCloseTo(0.667, 3);
  expect(m.lowestAccepted).toBe(2);
  expect(m.earned).toBe(10);
  expect(m.acceptByOffer.find((row) => row.offer === 2)).toMatchObject({ offered: 2, rate: 0.5 });
});

test('CSV export then import reproduces sessions, including labels with commas and quotes', async ({ page }) => {
  const out = await page.evaluate(() => {
    const trials = [
      { n: 1, condition: 'congruent', stimulus: 'red/red', response: 'red', correct: true, rt: 512.3 },
      { n: 2, condition: 'incongruent', stimulus: 'red/blue', response: null, correct: false, rt: null },
      { n: 3, condition: 'incongruent', stimulus: 'green/blue', response: 'blue', correct: true, rt: 640 },
    ];
    const session = { id: 's1', task: 'stroop', ts: 1700000000000, label: 'A, "B"\nC', seed: 42, trials, metrics: NATasks.score('stroop', trials) };
    const back = NAStore.fromCsv(NAStore.toCsv([session]));
    return { session, back };
  });
  expect(out.back).toEqual([out.session]);
});

test('fromCsv rejects foreign headers, unknown tasks, ragged rows, and unterminated quotes', async ({ page }) => {
  const header = await page.evaluate(() => NAStore.HEADER.join(','));
  const out = await page.evaluate((head) => {
    const attempt = (text) => { try { NAStore.fromCsv(text); return 'ok'; } catch (e) { return e.message; } };
    return [
      attempt('a,b,c\n1,2,3\n'),
      attempt(head + '\ns,chess,1,me,1,1,x,x,x,true,1\n'),
      attempt(head + '\ns,stroop,1,me\n'),
      attempt(head + '\ns,stroop,1,"me,1,1,x,x,x,true,1\n'),
    ];
  }, header);
  expect(out[0]).toMatch(/header/);
  expect(out[1]).toMatch(/unknown task/);
  expect(out[2]).toMatch(/columns/);
  expect(out[3]).toMatch(/Unterminated/);
});

test('merge adds only sessions whose id is new', async ({ page }) => {
  const out = await page.evaluate(() => NAStore.merge([{ id: 'a' }, { id: 'b' }], [{ id: 'b' }, { id: 'c' }]));
  expect(out.added).toBe(1);
  expect(out.skipped).toBe(1);
  expect(out.sessions.map((s) => s.id)).toEqual(['a', 'b', 'c']);
});
