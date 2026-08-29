const { test, expect } = require('@playwright/test');
const { loadLogic } = require('./helpers/loadLogic');

test.describe('CSP solver correctness', () => {
  let zl;
  test.beforeEach(() => {
    zl = loadLogic();
  });

  for (const chapterId of [1, 2, 3]) {
    test(`chapter ${chapterId}: solver recovers the exact known solution from the generated clue set`, () => {
      const puzzle = zl.zlGeneratePuzzle(chapterId, 'solver-known-' + chapterId);
      const result = zl.zlCountSolutions(puzzle.categories, puzzle.size, puzzle.clues, 2);
      expect(result.aborted).toBe(false);
      expect(result.count).toBe(1);
      const attrCats = puzzle.categories.filter((c) => c.id !== 'position');
      for (const cat of attrCats) {
        expect(result.solution[cat.id]).toEqual(puzzle.solution[cat.id]);
      }
    });
  }

  test('solver reports multiple solutions for a deliberately underspecified clue set', () => {
    const puzzle = zl.zlGeneratePuzzle(1, 'underspecified-1');
    // A single clue almost never pins down a whole 4x3 grid.
    const result = zl.zlCountSolutions(puzzle.categories, puzzle.size, puzzle.clues.slice(0, 1), 2);
    expect(result.count).toBeGreaterThan(1);
  });

  test('solver reports zero solutions for a genuinely contradictory clue set', () => {
    const puzzle = zl.zlGeneratePuzzle(1, 'contradiction-1');
    const categories = puzzle.categories;
    const attrCat = categories.find((c) => c.id !== 'position');
    // Force value 0 of the first attribute category to two different, incompatible studies.
    const contradictory = [
      { type: 'eq', a: { cat: 'position', val: 0 }, b: { cat: attrCat.id, val: 0 } },
      { type: 'eq', a: { cat: 'position', val: 1 }, b: { cat: attrCat.id, val: 0 } },
    ];
    const result = zl.zlCountSolutions(categories, puzzle.size, contradictory, 2);
    expect(result.count).toBe(0);
  });

  test('empty clue set has many solutions (all-different constraint only)', () => {
    const puzzle = zl.zlGeneratePuzzle(2, 'empty-clues-2');
    const result = zl.zlCountSolutions(puzzle.categories, puzzle.size, [], 2);
    expect(result.count).toBe(2); // capped at 2, but definitely more than 1 exist
  });
});
