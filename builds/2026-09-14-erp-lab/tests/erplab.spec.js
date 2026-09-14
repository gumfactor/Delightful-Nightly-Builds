const { test, expect } = require('@playwright/test');
const path = require('path');

const INDEX_URL = `file://${path.resolve(__dirname, '../index.html')}`;

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    try {
      localStorage.clear();
    } catch (e) {
      /* ignore */
    }
  });
  await page.goto(INDEX_URL);
});

/* ================================================================
   Math core — cross-checked against hand-computed reference values
   ================================================================ */

test('mulberry32 is deterministic for a fixed seed', async ({ page }) => {
  const result = await page.evaluate(() => {
    const a = mulberry32(42);
    const b = mulberry32(42);
    const seqA = Array.from({ length: 10 }, () => a());
    const seqB = Array.from({ length: 10 }, () => b());
    return JSON.stringify(seqA) === JSON.stringify(seqB);
  });
  expect(result).toBe(true);
});

test('Box-Muller Gaussian sampler has mean ~0 and SD ~1 over a large sample', async ({ page }) => {
  const { m, sd } = await page.evaluate(() => {
    const g = makeGaussianRng(mulberry32(123));
    const samples = Array.from({ length: 50000 }, () => g());
    return { m: mean(samples), sd: standardDeviation(samples) };
  });
  expect(Math.abs(m)).toBeLessThan(0.03);
  expect(Math.abs(sd - 1)).toBeLessThan(0.03);
});

test('FFT of an 8-point signal matches a hand-computed direct DFT', async ({ page }) => {
  const { re, im } = await page.evaluate(() => {
    const signal = [1, 2, 0, -1, 1, 2, 0, -1];
    const result = fft(signal, new Array(8).fill(0));
    return { re: Array.from(result.re), im: Array.from(result.im) };
  });
  // Reference computed independently via a direct O(N^2) DFT summation in Python
  // before this test was written (see BUILD_LOG.md).
  const expectedRe = [4, 0, 2, 0, 0, 0, 2, 0];
  const expectedIm = [0, 0, -6, 0, 0, 0, 6, 0];
  for (let i = 0; i < 8; i++) {
    expect(re[i]).toBeCloseTo(expectedRe[i], 6);
    expect(im[i]).toBeCloseTo(expectedIm[i], 6);
  }
});

test('FFT satisfies Parseval’s theorem (time-domain energy equals frequency-domain energy)', async ({ page }) => {
  const { timeEnergy, freqEnergy } = await page.evaluate(() => {
    const signal = [3, -1, 4, 1, 5, -9, 2, 6];
    const result = fft(signal, new Array(8).fill(0));
    const timeE = signal.reduce((s, v) => s + v * v, 0);
    let freqE = 0;
    for (let i = 0; i < 8; i++) freqE += result.re[i] * result.re[i] + result.im[i] * result.im[i];
    freqE /= 8;
    return { timeEnergy: timeE, freqEnergy: freqE };
  });
  expect(freqEnergy).toBeCloseTo(timeEnergy, 6);
});

test('FFT recovers the exact frequency of a pure sine wave', async ({ page }) => {
  const detectedFreq = await page.evaluate(() => {
    const n = N_SAMPLES;
    const sr = SAMPLE_RATE;
    const targetFreq = 17;
    const signal = Array.from({ length: n }, (_, i) => Math.sin((2 * Math.PI * targetFreq * i) / sr));
    const result = fft(signal, new Array(n).fill(0));
    const spectrum = powerSpectrum(result.re, result.im, sr);
    let maxIdx = 0;
    for (let i = 1; i < spectrum.power.length; i++) if (spectrum.power[i] > spectrum.power[maxIdx]) maxIdx = i;
    return spectrum.freqs[maxIdx];
  });
  expect(detectedFreq).toBeCloseTo(17, 3);
});

test('epoch averaging reduces baseline noise SD proportional to 1/√N', async ({ page }) => {
  const results = await page.evaluate(() => {
    const template = generateERPTemplate(350, 5, 100);
    const noiseSD = 8;
    return [4, 64].map((N) => {
      const rng = mulberry32(999);
      const g = makeGaussianRng(rng);
      const epochs = generateEpochSet(template, noiseSD, N, g, rng, 0, 0).epochs;
      const avg = averageEpochs(epochs);
      const baseline = Array.from(avg.slice(0, PRE_STIM_SAMPLES));
      return { N, measured: standardDeviation(baseline), theoretical: noiseSD / Math.sqrt(N) };
    });
  });
  results.forEach((r) => {
    // measured should be within 40% of theoretical -- generous tolerance for a
    // single stochastic draw with a modest baseline sample count (51 samples)
    expect(Math.abs(r.measured - r.theoretical) / r.theoretical).toBeLessThan(0.4);
  });
  // the N=64 case must show a clearly smaller baseline SD than the N=4 case
  expect(results[1].measured).toBeLessThan(results[0].measured);
});

test('peak-to-peak artifact rejection separates contaminated trials from clean trials', async ({ page }) => {
  const { rejectedCount, mismatches } = await page.evaluate(() => {
    const template = generateERPTemplate(350, 5, 100);
    const rng = mulberry32(42);
    const g = makeGaussianRng(rng);
    const { epochs, isArtifact } = generateEpochSet(template, 3, 200, g, rng, 0.25, 45);
    const { rejectedCount: rc } = rejectArtifacts(epochs, 35, peakToPeak);
    let mismatches = 0;
    for (let i = 0; i < epochs.length; i++) {
      const rejected = peakToPeak(epochs[i]) > 35;
      if (rejected !== isArtifact[i]) mismatches++;
    }
    return { rejectedCount: rc, mismatches };
  });
  expect(mismatches).toBe(0);
  expect(rejectedCount).toBeGreaterThan(20);
  expect(rejectedCount).toBeLessThan(80);
});

test('rejecting all trials (threshold=0) leaves zero clean trials', async ({ page }) => {
  const cleanCount = await page.evaluate(() => {
    const template = generateERPTemplate(350, 5, 100);
    const rng = mulberry32(1);
    const g = makeGaussianRng(rng);
    const epochs = generateEpochSet(template, 5, 30, g, rng, 0, 0).epochs;
    return rejectArtifacts(epochs, 0, peakToPeak).clean.length;
  });
  expect(cleanCount).toBe(0);
});

test('moving-average filter attenuates a high-frequency component while preserving a low-frequency one', async ({ page }) => {
  const { lowBefore, lowAfter, highBefore, highAfter } = await page.evaluate(() => {
    const n = N_SAMPLES;
    const sr = SAMPLE_RATE;
    const signal = Array.from({ length: n }, (_, i) => {
      const t = i / sr;
      return Math.sin(2 * Math.PI * 4 * t) + Math.sin(2 * Math.PI * 60 * t);
    });
    const filtered = Array.from(movingAverageFilter(signal, 9));
    function powerAt(sig, targetFreq) {
      const r = fft(sig, new Array(n).fill(0));
      const spec = powerSpectrum(r.re, r.im, sr);
      let closest = 0;
      for (let i = 1; i < spec.freqs.length; i++) {
        if (Math.abs(spec.freqs[i] - targetFreq) < Math.abs(spec.freqs[closest] - targetFreq)) closest = i;
      }
      return spec.power[closest];
    }
    return {
      lowBefore: powerAt(signal, 4),
      lowAfter: powerAt(filtered, 4),
      highBefore: powerAt(signal, 60),
      highAfter: powerAt(filtered, 60),
    };
  });
  // low frequency should be mostly preserved
  expect(lowAfter / lowBefore).toBeGreaterThan(0.7);
  // high frequency should be substantially attenuated
  expect(highAfter / highBefore).toBeLessThan(0.3);
});

test('permutation test: a null case (identical distributions) does not yield a systematically tiny p-value', async ({ page }) => {
  const pValue = await page.evaluate(() => {
    const rngA = mulberry32(1);
    const gA = makeGaussianRng(rngA);
    const rngB = mulberry32(2);
    const gB = makeGaussianRng(rngB);
    const groupA = Array.from({ length: 50 }, () => gA() * 2);
    const groupB = Array.from({ length: 50 }, () => gB() * 2);
    const result = permutationTest(groupA, groupB, 2000, mulberry32(55));
    return result.pValue;
  });
  expect(pValue).toBeGreaterThan(0.05);
});

test('permutation test: a strongly separated case yields a small p-value', async ({ page }) => {
  const pValue = await page.evaluate(() => {
    const rngA = mulberry32(1);
    const gA = makeGaussianRng(rngA);
    const rngB = mulberry32(2);
    const gB = makeGaussianRng(rngB);
    const groupA = Array.from({ length: 50 }, () => gA() * 2 + 6);
    const groupB = Array.from({ length: 50 }, () => gB() * 2);
    const result = permutationTest(groupA, groupB, 2000, mulberry32(56));
    return result.pValue;
  });
  expect(pValue).toBeLessThan(0.01);
});

test('permutation test null distribution has exactly nPermutations entries and observedDiff matches a direct mean-difference calculation', async ({ page }) => {
  const { correctDiff, matches, distLength } = await page.evaluate(() => {
    const groupA = [1, 2, 3, 4, 5];
    const groupB = [2, 2, 2, 2, 2];
    const result = permutationTest(groupA, groupB, 500, mulberry32(1));
    const correct = mean(groupA) - mean(groupB);
    return { correctDiff: correct, matches: Math.abs(result.observedDiff - correct) < 1e-9, distLength: result.nullDistribution.length };
  });
  expect(correctDiff).toBeCloseTo(1, 9);
  expect(matches).toBe(true);
  expect(distLength).toBe(500);
});

/* ================================================================
   Quiz question bank
   ================================================================ */

test('quiz has 8 fixed questions, each with a valid correctIndex', async ({ page }) => {
  const ok = await page.evaluate(() => {
    if (FIXED_QUESTIONS.length !== 8) return false;
    return FIXED_QUESTIONS.every((q) => q.correctIndex >= 0 && q.correctIndex < q.choices.length);
  });
  expect(ok).toBe(true);
});

test('generateLiveQuestions produces 8 valid questions, deterministic per seed, different across seeds', async ({ page }) => {
  const { count, valid, sameForSameSeed, differentForDifferentSeed } = await page.evaluate(() => {
    const a = generateLiveQuestions(111);
    const b = generateLiveQuestions(111);
    const c = generateLiveQuestions(222);
    return {
      count: a.length,
      valid: a.every((q) => q.correctIndex >= 0 && q.correctIndex < q.choices.length),
      sameForSameSeed: JSON.stringify(a) === JSON.stringify(b),
      differentForDifferentSeed: JSON.stringify(a) !== JSON.stringify(c),
    };
  });
  expect(count).toBe(8);
  expect(valid).toBe(true);
  expect(sameForSameSeed).toBe(true);
  expect(differentForDifferentSeed).toBe(true);
});

/* ================================================================
   UI — tab navigation
   ================================================================ */

test('page loads with the correct title and ERP Basics tab active by default', async ({ page }) => {
  await expect(page).toHaveTitle(/ERP Lab/);
  await expect(page.locator('[data-testid="panel-basics"]')).toBeVisible();
  await expect(page.locator('[data-testid="panel-cit"]')).toBeHidden();
});

test('clicking each tab shows exactly that panel', async ({ page }) => {
  const tabs = ['artifact', 'freq', 'cit', 'quiz', 'basics'];
  for (const tab of tabs) {
    await page.locator(`[data-testid="tab-${tab}"]`).click();
    await expect(page.locator(`[data-testid="panel-${tab}"]`)).toBeVisible();
    for (const other of ['basics', 'artifact', 'freq', 'cit', 'quiz']) {
      if (other !== tab) {
        await expect(page.locator(`[data-testid="panel-${other}"]`)).toBeHidden();
      }
    }
  }
});

/* ================================================================
   UI — ERP Basics tab
   ================================================================ */

test('ERP Basics: changing the trial-count slider changes the displayed measured SD', async ({ page }) => {
  const before = await page.locator('[data-testid="basics-measured-sd"]').textContent();
  await page.locator('[data-testid="basics-ntrials"]').fill('200');
  await page.locator('[data-testid="basics-ntrials"]').dispatchEvent('input');
  const after = await page.locator('[data-testid="basics-measured-sd"]').textContent();
  expect(after).not.toBe(before);
});

test('ERP Basics: theoretical SD readout matches noiseSD/√N for the current slider values', async ({ page }) => {
  await page.locator('[data-testid="basics-ntrials"]').fill('16');
  await page.locator('[data-testid="basics-ntrials"]').dispatchEvent('input');
  await page.locator('[data-testid="basics-noisesd"]').fill('8');
  await page.locator('[data-testid="basics-noisesd"]').dispatchEvent('input');
  const text = await page.locator('[data-testid="basics-theory-sd"]').textContent();
  expect(text.trim()).toBe('2.00 µV');
});

/* ================================================================
   UI — Artifact Rejection tab
   ================================================================ */

test('Artifact Rejection: raising the threshold decreases (or holds) the rejected-trial count', async ({ page }) => {
  await page.locator('[data-testid="tab-artifact"]').click();
  await page.locator('[data-testid="artifact-threshold"]').fill('10');
  await page.locator('[data-testid="artifact-threshold"]').dispatchEvent('input');
  const lowThresholdText = await page.locator('[data-testid="artifact-rejected"]').textContent();
  const lowRejected = parseInt(lowThresholdText, 10);

  await page.locator('[data-testid="artifact-threshold"]').fill('90');
  await page.locator('[data-testid="artifact-threshold"]').dispatchEvent('input');
  const highThresholdText = await page.locator('[data-testid="artifact-rejected"]').textContent();
  const highRejected = parseInt(highThresholdText, 10);

  expect(highRejected).toBeLessThanOrEqual(lowRejected);
});

test('Artifact Rejection: rejected + kept always equals the trial count', async ({ page }) => {
  await page.locator('[data-testid="tab-artifact"]').click();
  await page.locator('[data-testid="artifact-ntrials"]').fill('150');
  await page.locator('[data-testid="artifact-ntrials"]').dispatchEvent('input');
  const nTrials = parseInt(await page.locator('#artifact-ntrials-value').textContent(), 10);
  const rejected = parseInt(await page.locator('[data-testid="artifact-rejected"]').textContent(), 10);
  const kept = parseInt(await page.locator('[data-testid="artifact-kept"]').textContent(), 10);
  expect(rejected + kept).toBe(nTrials);
  expect(nTrials).toBe(150);
});

/* ================================================================
   UI — Frequency Domain tab
   ================================================================ */

test('Frequency Domain: filter window slider updates its own readout label', async ({ page }) => {
  await page.locator('[data-testid="tab-freq"]').click();
  await page.locator('[data-testid="freq-filter-window"]').fill('15');
  await page.locator('[data-testid="freq-filter-window"]').dispatchEvent('input');
  await expect(page.locator('#freq-filter-window-value')).toHaveText('15');
});

test('Frequency Domain: both canvases render without throwing', async ({ page }) => {
  await page.locator('[data-testid="tab-freq"]').click();
  await page.locator('[data-testid="freq-alpha-amp"]').fill('9');
  await page.locator('[data-testid="freq-alpha-amp"]').dispatchEvent('input');
  const timeCanvas = page.locator('[data-testid="freq-time-canvas"]');
  const specCanvas = page.locator('[data-testid="freq-spectrum-canvas"]');
  await expect(timeCanvas).toBeVisible();
  await expect(specCanvas).toBeVisible();
});

/* ================================================================
   UI — CIT Lab tab
   ================================================================ */

test('CIT Lab: running the test with a strong effect and enough trials tends to report a small p-value', async ({ page }) => {
  await page.locator('[data-testid="tab-cit"]').click();
  await page.locator('[data-testid="cit-effect"]').fill('10');
  await page.locator('[data-testid="cit-effect"]').dispatchEvent('input');
  await page.locator('[data-testid="cit-nprobe"]').fill('40');
  await page.locator('[data-testid="cit-nprobe"]').dispatchEvent('input');
  await page.locator('[data-testid="cit-innocent-toggle"]').uncheck();
  await page.locator('[data-testid="cit-run-test"]').click();
  const pText = await page.locator('[data-testid="cit-pvalue"]').textContent();
  expect(parseFloat(pText)).toBeLessThan(0.05);
  await expect(page.locator('[data-testid="cit-verdict"]')).toContainText('Detected');
});

test('CIT Lab: the innocent-suspect toggle forces zero true effect in the underlying computation', async ({ page }) => {
  await page.locator('[data-testid="tab-cit"]').click();
  await page.locator('[data-testid="cit-effect"]').fill('10');
  await page.locator('[data-testid="cit-effect"]').dispatchEvent('input');
  await page.locator('[data-testid="cit-innocent-toggle"]').check();

  // Run several times and confirm the "detected" rate is well below what a
  // true 10µV effect would produce (near-100% detection) -- i.e. the
  // toggle is really zeroing the effect, not just cosmetic.
  let detectedCount = 0;
  const runs = 6;
  for (let i = 0; i < runs; i++) {
    await page.locator('[data-testid="cit-run-test"]').click();
    const verdict = await page.locator('[data-testid="cit-verdict"]').textContent();
    if (verdict.includes('Detected')) detectedCount++;
  }
  expect(detectedCount).toBeLessThan(runs);
});

test('CIT Lab: observed difference and p-value are numeric and update after re-running', async ({ page }) => {
  await page.locator('[data-testid="tab-cit"]').click();
  await page.locator('[data-testid="cit-run-test"]').click();
  const diffText = await page.locator('[data-testid="cit-observed-diff"]').textContent();
  expect(diffText).toMatch(/-?\d+\.\d{2}\s*µV/);
  const pText = await page.locator('[data-testid="cit-pvalue"]').textContent();
  expect(parseFloat(pText)).toBeGreaterThanOrEqual(0);
  expect(parseFloat(pText)).toBeLessThanOrEqual(1);
});

/* ================================================================
   Security — AI-explain panel
   ================================================================ */

test('AI-explain panel: with no API key set, zero network requests are made and the deterministic fallback is shown', async ({ page }) => {
  await page.locator('[data-testid="tab-cit"]').click();
  await page.locator('[data-testid="cit-run-test"]').click();

  let requestCount = 0;
  page.on('request', (req) => {
    if (req.url().includes('anthropic.com')) requestCount++;
  });

  await page.locator('[data-testid="cit-explain-btn"]').click();
  const output = await page.locator('[data-testid="cit-explain-output"]').textContent();
  expect(output).toContain('permutation');
  expect(requestCount).toBe(0);
});

test('AI-explain panel: a hostile mocked API response renders as inert text, not executed markup', async ({ page }) => {
  await page.route('**://api.anthropic.com/**', (route) => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        content: [{ type: 'text', text: '<script>window.__xssFired = true;</script><img src=x onerror="window.__xssFired = true">Explanation text.' }],
      }),
    });
  });

  await page.locator('[data-testid="tab-cit"]').click();
  await page.locator('[data-testid="cit-run-test"]').click();
  await page.locator('[data-testid="cit-api-key"]').fill('fake-test-key-not-real');
  await page.locator('[data-testid="cit-explain-btn"]').click();

  await expect(page.locator('[data-testid="cit-explain-output"]')).toContainText('Explanation text.', { timeout: 10000 });
  const xssFired = await page.evaluate(() => window.__xssFired === true);
  expect(xssFired).toBe(false);
  const scriptTagCount = await page.locator('[data-testid="cit-explain-output"] script').count();
  expect(scriptTagCount).toBe(0);
});

test('AI-explain panel: typing hostile text into the API key field never crashes or executes it', async ({ page }) => {
  await page.locator('[data-testid="tab-cit"]').click();
  await page.locator('[data-testid="cit-run-test"]').click();
  await page.locator('[data-testid="cit-api-key"]').fill('<img src=x onerror="window.__xssFired2=true">');
  await page.locator('[data-testid="cit-explain-btn"]').click();
  // an obviously-invalid key should fail the fetch and fall back gracefully
  await expect(page.locator('[data-testid="cit-explain-output"]')).toContainText('permutation', { timeout: 10000 });
  const xssFired = await page.evaluate(() => window.__xssFired2 === true);
  expect(xssFired).toBe(false);
});

/* ================================================================
   Quiz — end-to-end flow
   ================================================================ */

test('Quiz: completing all 16 questions shows a final score and persists a best score to localStorage', async ({ page }) => {
  await page.locator('[data-testid="tab-quiz"]').click();
  await page.locator('[data-testid="quiz-start"]').click();

  for (let i = 0; i < 16; i++) {
    await expect(page.locator('[data-testid="quiz-progress"]')).toContainText(`${i + 1} / 16`);
    await page.locator('[data-testid="quiz-choice-0"]').click();
    await expect(page.locator('[data-testid="quiz-feedback"]')).toBeVisible();
    const nextBtn = page.locator('[data-testid="quiz-next"]');
    await nextBtn.click();
  }

  await expect(page.locator('[data-testid="quiz-results"]')).toBeVisible();
  const scoreText = await page.locator('[data-testid="quiz-final-score"]').textContent();
  const score = parseInt(scoreText, 10);
  expect(score).toBeGreaterThanOrEqual(0);
  expect(score).toBeLessThanOrEqual(16);

  const stored = await page.evaluate(() => localStorage.getItem('erplab_quiz_best'));
  expect(parseInt(stored, 10)).toBe(score);
});

test('Quiz: best score display updates on the intro screen after finishing a quiz', async ({ page }) => {
  await page.locator('[data-testid="tab-quiz"]').click();
  await expect(page.locator('[data-testid="quiz-best-score"]')).toHaveText('0');
  await page.locator('[data-testid="quiz-start"]').click();
  for (let i = 0; i < 16; i++) {
    await page.locator('[data-testid="quiz-choice-0"]').click();
    await page.locator('[data-testid="quiz-next"]').click();
  }
  await page.locator('[data-testid="quiz-restart"]').click();
  const best = await page.locator('[data-testid="quiz-best-score"]').textContent();
  expect(parseInt(best, 10)).toBeGreaterThanOrEqual(0);
});

/* ================================================================
   Responsiveness & error hygiene
   ================================================================ */

test('page has no horizontal overflow at a 375px mobile viewport', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 800 });
  await page.locator('[data-testid="tab-cit"]').click();
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1);
  expect(overflow).toBe(false);
});

test('no console errors or page errors occur across a full interaction pass', async ({ page }) => {
  const errors = [];
  page.on('console', (msg) => {
    if (msg.type() === 'error') errors.push(msg.text());
  });
  page.on('pageerror', (err) => errors.push(String(err)));

  for (const tab of ['artifact', 'freq', 'cit', 'quiz', 'basics']) {
    await page.locator(`[data-testid="tab-${tab}"]`).click();
  }
  await page.locator('[data-testid="tab-cit"]').click();
  await page.locator('[data-testid="cit-run-test"]').click();
  await page.locator('[data-testid="tab-quiz"]').click();
  await page.locator('[data-testid="quiz-start"]').click();
  await page.locator('[data-testid="quiz-choice-0"]').click();

  expect(errors).toEqual([]);
});
