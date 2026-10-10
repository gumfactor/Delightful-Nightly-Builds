const { test, expect } = require('@playwright/test');
const path = require('path');
const url = 'file://' + path.resolve(__dirname, '..', 'index.html');

const HELD_OUT_HUMAN = `The first time I tried to run a marathon I got the pacing exactly wrong. I went out at a speed I hadn't trained for, because everyone around me was moving that way, and by kilometre twenty-five my legs had stopped listening.

You learn quickly what you can't fake. Water stops don't help when the problem is a plan. I walked a lot of the last stretch, and a stranger handed me half a banana at one point, which I still think about.

My second attempt went better. I slowed down at the start, which felt silly, and then passed about forty people in the final ten kilometres. It wasn't fast. But I'd learned to trust the boring part of the plan, and that's what I remember.`;

test.beforeEach(async ({ page }) => {
  await page.goto(url);
});

const run = (page, fn, arg) => page.evaluate(fn, arg);

test('splits sentences without breaking on abbreviations, initials or decimals', async ({ page }) => {
  const out = await run(page, () => window.VoicePrint.splitSentences('Dr. Smith met J. Doe in 3.5 hours. Was it fun? Yes!').map((s) => s.text));
  expect(out).toEqual(['Dr. Smith met J. Doe in 3.5 hours.', 'Was it fun?', 'Yes!']);
});

test('sentence offsets point back into the original text', async ({ page }) => {
  const ok = await run(page, () => {
    const text = '  First one here.\n\nSecond   one there! Third?';
    return window.VoicePrint.splitSentences(text).every((s) => text.slice(s.start, s.end) === s.text);
  });
  expect(ok).toBe(true);
});

test('empty and whitespace-only input yields zero scores and no crash', async ({ page }) => {
  const r = await run(page, () => window.VoicePrint.analyze('   \n '));
  expect(r.aiScore).toBe(0);
  expect(r.flags).toEqual([]);
  expect(r.metrics.words).toBe(0);
});

test('metrics: contractions, first person and questions are counted', async ({ page }) => {
  const m = await run(page, () => window.VoicePrint.computeMetrics("I can't go. We don't know why? It's odd."));
  expect(m.contractionRate).toBeGreaterThan(30);
  expect(m.firstPersonRate).toBeGreaterThan(10);
  expect(m.questionRate).toBeCloseTo(1 / 3, 2);
});

test('detects stock vocabulary and phrases with exact spans', async ({ page }) => {
  const r = await run(page, () => {
    const text = "We must delve here. It's important to note that results vary.";
    const res = window.VoicePrint.analyze(text);
    return res.flags.map((f) => ({ type: f.type, hit: text.slice(f.start, f.end).toLowerCase() }));
  });
  expect(r.some((f) => f.type === 'vocab' && f.hit === 'delve')).toBe(true);
  expect(r.some((f) => f.type === 'phrase' && f.hit.startsWith("it's important to note"))).toBe(true);
});

test('detects "not just X, but Y" and "it\'s not X, it\'s Y" frames', async ({ page }) => {
  const types = await run(page, () => [
    'This is not just a tool, but a movement.',
    "It's not about speed, it's about care.",
    'Time management is not a skill — it is a habit.',
    'The plan is not only cheap — it is fast.',
  ].map((t) => window.VoicePrint.analyze(t).flags.map((f) => f.type)));
  expect(types[0]).toContain('contrast');
  expect(types[1]).toContain('contrast');
  expect(types[3]).toContain('contrast');
});

test('detects tacked-on participles and stiff transitions only at sentence start', async ({ page }) => {
  const r = await run(page, () => ({
    tacked: window.VoicePrint.analyze('The study ran for a year, highlighting the need for care.').flags.map((f) => f.type),
    start: window.VoicePrint.analyze('We ran it. Moreover, it worked.').flags.map((f) => f.type),
    mid: window.VoicePrint.analyze('We ran it and moreover it worked.').flags.map((f) => f.type),
  }));
  expect(r.tacked).toContain('participle');
  expect(r.start).toContain('transition');
  expect(r.mid).not.toContain('transition');
});

test('plain human sentences produce no flags', async ({ page }) => {
  const r = await run(page, () => window.VoicePrint.analyze("I burned the toast again. My kid laughed, then ate it anyway.").flags);
  expect(r).toEqual([]);
});

test('flags never overlap and stay inside the text', async ({ page }) => {
  const ok = await run(page, () => {
    const text = window.VP_SAMPLES.machine;
    const flags = window.VoicePrint.analyze(text).flags;
    return flags.every((f, i) => f.end <= text.length && f.start < f.end && (i === 0 || flags[i - 1].end <= f.start));
  });
  expect(ok).toBe(true);
});

test('em dashes are only flagged once they are frequent', async ({ page }) => {
  const r = await run(page, () => ({
    rare: window.VoicePrint.analyze('One dash — here. ' + 'Plain words follow. '.repeat(120)).flags.filter((f) => f.type === 'emdash').length,
    heavy: window.VoicePrint.analyze('Dash — dash — dash — dash — dash. Short text here.').flags.filter((f) => f.type === 'emdash').length,
  }));
  expect(r.rare).toBe(0);
  expect(r.heavy).toBeGreaterThan(0);
});

test('machine demo scores far higher than human demo, and both stay in 0-100', async ({ page }) => {
  const r = await run(page, () => ({ m: window.VoicePrint.analyze(window.VP_SAMPLES.machine).aiScore, h: window.VoicePrint.analyze(window.VP_SAMPLES.human).aiScore }));
  expect(r.m).toBeGreaterThan(60);
  expect(r.h).toBeLessThan(20);
  expect(r.m).toBeLessThanOrEqual(100);
});

test('uniform rhythm triggers the global rhythm flag', async ({ page }) => {
  const types = await run(page, () => window.VoicePrint.analyze('The cat sat down. The dog ran off. The bird flew up. The fish swam on. The cow ate hay. The pig lay low. The hen sat still.').globalFlags.map((f) => f.type));
  expect(types).toContain('rhythm');
});

test('buildProfile rejects too-short baselines', async ({ page }) => {
  const msg = await run(page, () => { try { window.VoicePrint.buildProfile(['too short']); return 'no error'; } catch (e) { return e.message; } });
  expect(msg).toMatch(/40 words/);
});

test('profile records finite stats and merges more samples', async ({ page }) => {
  const r = await run(page, () => {
    const VP = window.VoicePrint;
    const first = VP.buildProfile([window.VP_SAMPLES.human]);
    const second = VP.buildProfile([window.VP_SAMPLES.human], first);
    return { n1: first.sampleCount, n2: second.sampleCount, w2: second.wordCount, w1: first.wordCount, finite: VP.VOICE_METRICS.every((m) => Number.isFinite(second.metrics[m].mean) && Number.isFinite(second.metrics[m].sd)) };
  });
  expect(r.n2).toBe(r.n1 + 1);
  expect(r.w2).toBe(r.w1 * 2);
  expect(r.finite).toBe(true);
});

test('own-style held-out text matches the profile better than the machine draft', async ({ page }) => {
  const r = await run(page, (held) => {
    const VP = window.VoicePrint;
    const profile = VP.buildProfile([window.VP_SAMPLES.human]);
    return { own: VP.analyze(held, profile).voiceMatch, machine: VP.analyze(window.VP_SAMPLES.machine, profile).voiceMatch };
  }, HELD_OUT_HUMAN);
  expect(r.own).toBeGreaterThan(r.machine + 25);
  expect(r.own).toBeGreaterThan(50);
});

test('validateProfile rejects malformed objects', async ({ page }) => {
  const r = await run(page, () => {
    const attempts = [null, {}, { version: 2, metrics: {}, functionWords: {} }, { version: 1, metrics: {}, functionWords: {} }];
    return attempts.map((a) => { try { window.VoicePrint.validateProfile(a); return 'ok'; } catch (e) { return 'err'; } });
  });
  expect(r).toEqual(['err', 'err', 'err', 'err']);
});

test('revision prompt includes flagged examples, voice targets and the draft', async ({ page }) => {
  const prompt = await run(page, () => {
    const VP = window.VoicePrint;
    const profile = VP.buildProfile([window.VP_SAMPLES.human]);
    const text = window.VP_SAMPLES.machine;
    return VP.buildRevisionPrompt(text, VP.analyze(text, profile), profile);
  });
  expect(prompt).toContain('Problems found by a style linter');
  expect(prompt).toContain('Target voice');
  expect(prompt).toContain('DRAFT:');
  expect(prompt).toMatch(/delve|tapestry|testament/i);
});
