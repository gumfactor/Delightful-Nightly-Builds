const { test, expect } = require('@playwright/test');
const path = require('path');

const INDEX_URL = `file://${path.resolve(__dirname, '../index.html')}`;

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => localStorage.clear());
  await page.goto(INDEX_URL);
});

test('generated set-drift puzzles are always solvable and self-consistent with the engine', async ({ page }) => {
  const outcome = await page.evaluate(() => {
    const rng = TC.mulberry32(12345);
    let failures = 0;
    for (let i = 0; i < 200; i++) {
      const puzzle = TC.generatePuzzle('set-drift', rng);
      const recomputed = TC.courseToSteer(puzzle.params);
      if (!recomputed.solvable) failures++;
      if (Math.round(recomputed.headingDeg) !== puzzle.correctAnswer) failures++;
      if (Math.abs(recomputed.correctionDeg) < 3 || Math.abs(recomputed.correctionDeg) > 45) failures++;
    }
    return { failures };
  });
  expect(outcome.failures).toBe(0);
});

test('generated tide-window puzzles always land in the mid-leg window, never the trivial always/never case', async ({ page }) => {
  const outcome = await page.evaluate(() => {
    const rng = TC.mulberry32(777);
    let failures = 0;
    for (let i = 0; i < 100; i++) {
      const puzzle = TC.generatePuzzle('tide-window', rng);
      const recomputed = TC.tideWindowStart(puzzle.params);
      if (recomputed.status !== 'window') failures++;
      if (TC.formatClock(recomputed.startTime) !== puzzle.correctAnswer) failures++;
      if (!puzzle.choices.includes(puzzle.correctAnswer)) failures++;
      const uniqueChoices = new Set(puzzle.choices);
      if (uniqueChoices.size !== puzzle.choices.length) failures++;
    }
    return { failures };
  });
  expect(outcome.failures).toBe(0);
});

test('generated right-of-way puzzles stay clear of every classification boundary and match a fresh classification', async ({ page }) => {
  const outcome = await page.evaluate(() => {
    const rng = TC.mulberry32(4242);
    let failures = 0;
    for (let i = 0; i < 300; i++) {
      const puzzle = TC.generatePuzzle('right-of-way', rng);
      const margin = TC.encounterBoundaryMargin(puzzle.params);
      if (margin < 6) failures++;
      const recomputed = TC.classifyEncounter(puzzle.params);
      if (recomputed.giveWay !== puzzle.correctAnswer) failures++;
      if (recomputed.type !== puzzle.encounterType) failures++;
    }
    return { failures };
  });
  expect(outcome.failures).toBe(0);
});

test('generated buoyage puzzles match the rule engine for every variant', async ({ page }) => {
  const outcome = await page.evaluate(() => {
    const rng = TC.mulberry32(99);
    let failures = 0;
    const variantsSeen = new Set();
    for (let i = 0; i < 150; i++) {
      const puzzle = TC.generatePuzzle('buoyage', rng);
      variantsSeen.add(puzzle.variant);
      let expected;
      if (puzzle.variant === 'side') expected = TC.buoyage.sideForBuoy(puzzle.params.color, puzzle.params.direction);
      else if (puzzle.variant === 'shape') expected = TC.buoyage.shapeForColor(puzzle.params.color);
      else expected = TC.buoyage.colorForNumber(puzzle.params.number);
      if (expected !== puzzle.correctAnswer) failures++;
      if (!puzzle.choices.includes(puzzle.correctAnswer)) failures++;
    }
    return { failures, variantCount: variantsSeen.size };
  });
  expect(outcome.failures).toBe(0);
  expect(outcome.variantCount).toBe(3); // side, shape, parity all exercised over 150 draws
});

test('the same seed always produces the same puzzle sequence', async ({ page }) => {
  const outcome = await page.evaluate(() => {
    const rng1 = TC.mulberry32(555);
    const rng2 = TC.mulberry32(555);
    const a = [];
    const b = [];
    for (let i = 0; i < 10; i++) {
      a.push(rng1());
      b.push(rng2());
    }
    return { equal: JSON.stringify(a) === JSON.stringify(b) };
  });
  expect(outcome.equal).toBe(true);
});

test('the daily seed is deterministic per UTC date and differs across dates', async ({ page }) => {
  const outcome = await page.evaluate(() => {
    const seedA1 = TC.dailySeed('2026-09-07');
    const seedA2 = TC.dailySeed('2026-09-07');
    const seedB = TC.dailySeed('2026-09-08');
    return { sameDateEqual: seedA1 === seedA2, differentDateDiffers: seedA1 !== seedB };
  });
  expect(outcome.sameDateEqual).toBe(true);
  expect(outcome.differentDateDiffers).toBe(true);
});

test('CHAPTER_ORDER contains exactly the four puzzle types with no duplicates', async ({ page }) => {
  const order = await page.evaluate(() => TC.CHAPTER_ORDER);
  expect(new Set(order).size).toBe(4);
  expect(order.sort()).toEqual(['buoyage', 'right-of-way', 'set-drift', 'tide-window']);
});
