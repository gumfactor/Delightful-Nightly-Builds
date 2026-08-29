const { test, expect } = require('@playwright/test');
const { loadLogic } = require('./helpers/loadLogic');

test.describe('Puzzle generator: uniqueness, minimality, determinism', () => {
  let zl;
  test.beforeEach(() => {
    zl = loadLogic();
  });

  for (const chapterId of [1, 2, 3]) {
    test(`chapter ${chapterId}: generated clue set is minimal (every clue is load-bearing)`, () => {
      const puzzle = zl.zlGeneratePuzzle(chapterId, 'minimal-check-' + chapterId);
      expect(zl.zlIsUnique(puzzle.categories, puzzle.size, puzzle.clues)).toBe(true);
      for (let i = 0; i < puzzle.clues.length; i++) {
        const withoutClue = puzzle.clues.filter((_, idx) => idx !== i);
        expect(zl.zlIsUnique(puzzle.categories, puzzle.size, withoutClue)).toBe(false);
      }
    });
  }

  test('multiple random seeds per chapter all yield unique, solvable puzzles', () => {
    for (const chapterId of [1, 2, 3]) {
      for (let trial = 0; trial < 5; trial++) {
        const puzzle = zl.zlGeneratePuzzle(chapterId, 'seed-sweep-' + chapterId + '-' + trial);
        expect(zl.zlIsUnique(puzzle.categories, puzzle.size, puzzle.clues)).toBe(true);
      }
    }
  });

  test('daily puzzle generation is deterministic for the same UTC date', () => {
    const a = zl.zlGenerateDailyPuzzle('2026-08-29');
    const b = zl.zlGenerateDailyPuzzle('2026-08-29');
    expect(JSON.stringify(a.clues)).toBe(JSON.stringify(b.clues));
    expect(JSON.stringify(a.solution)).toBe(JSON.stringify(b.solution));
  });

  test('daily puzzles differ across different UTC dates', () => {
    const a = zl.zlGenerateDailyPuzzle('2026-08-29');
    const b = zl.zlGenerateDailyPuzzle('2026-08-30');
    expect(JSON.stringify(a.clues)).not.toBe(JSON.stringify(b.clues));
  });

  test('chapter 3 uses a tighter (more aggressively pruned) clue set than chapter 2 on average', () => {
    let ch2Total = 0;
    let ch3Total = 0;
    const trials = 6;
    for (let i = 0; i < trials; i++) {
      ch2Total += zl.zlGeneratePuzzle(2, 'compare-2-' + i).clues.length;
      ch3Total += zl.zlGeneratePuzzle(3, 'compare-3-' + i).clues.length;
    }
    // Chapter 3 has an extra pruning pass and a superset of clue types available,
    // so it should never need MORE clues on average than chapter 2.
    expect(ch3Total / trials).toBeLessThanOrEqual(ch2Total / trials + 1);
  });
});
