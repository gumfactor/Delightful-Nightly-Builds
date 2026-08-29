const { test, expect } = require('@playwright/test');
const { loadLogic } = require('./helpers/loadLogic');

test.describe('Clue-text formatting matches underlying relation', () => {
  let zl;
  test.beforeEach(() => {
    zl = loadLogic();
  });

  test('eq clue between two attribute categories reads as "same study uses both"', () => {
    const puzzle = zl.zlGeneratePuzzle(1, 'clue-text-eq');
    const eqClue = puzzle.clues.find(
      (c) => c.type === 'eq' && c.a.cat !== 'position' && c.b.cat !== 'position'
    );
    test.skip(!eqClue, 'no cross-attribute eq clue in this generated puzzle');
    if (eqClue) {
      const text = zl.zlFormatClue(eqClue, puzzle.categories);
      expect(text).toMatch(/^The same study uses both .+ and .+\.$/);
    }
  });

  test('neq clue between two attribute categories reads as "does NOT use"', () => {
    const puzzle = zl.zlGeneratePuzzle(1, 'clue-text-neq');
    const neqClue = puzzle.clues.find(
      (c) => c.type === 'neq' && c.a.cat !== 'position' && c.b.cat !== 'position'
    );
    test.skip(!neqClue, 'no cross-attribute neq clue in this generated puzzle');
    if (neqClue) {
      const text = zl.zlFormatClue(neqClue, puzzle.categories);
      expect(text).toContain('does NOT use');
    }
  });

  test('position-fixed eq clue reads as "was Study #k."', () => {
    const puzzle = zl.zlGeneratePuzzle(1, 'clue-text-position');
    const posClue = puzzle.clues.find((c) => c.type === 'eq' && (c.a.cat === 'position' || c.b.cat === 'position'));
    expect(posClue).toBeTruthy();
    const text = zl.zlFormatClue(posClue, puzzle.categories);
    expect(text).toMatch(/^.+ was Study #\d\.$/);
  });

  test('adjacent clue relation is actually |posA - posB| === 1 in the generating solution', () => {
    // Search across several seeds since chapter 1 has no adjacent clues.
    let found = null;
    for (let i = 0; i < 15 && !found; i++) {
      const puzzle = zl.zlGeneratePuzzle(2, 'clue-text-adjacent-' + i);
      found = puzzle.clues.find((c) => c.type === 'adjacent');
      if (found) {
        const invA = zl.zlInvert(puzzle.solution[found.a.cat] || zl.zlIdentity(puzzle.size));
        const invB = zl.zlInvert(puzzle.solution[found.b.cat] || zl.zlIdentity(puzzle.size));
        const posA = found.a.cat === 'position' ? found.a.val : invA[found.a.val];
        const posB = found.b.cat === 'position' ? found.b.val : invB[found.b.val];
        expect(Math.abs(posA - posB)).toBe(1);
        const text = zl.zlFormatClue(found, puzzle.categories);
        expect(text.toLowerCase()).toContain('next to');
      }
    }
    expect(found).toBeTruthy();
  });

  test('less clue relation is actually posA < posB in the generating solution, and a is always the earlier side', () => {
    let found = null;
    for (let i = 0; i < 15 && !found; i++) {
      const puzzle = zl.zlGeneratePuzzle(3, 'clue-text-less-' + i);
      found = puzzle.clues.find((c) => c.type === 'less');
      if (found) {
        const invA = zl.zlInvert(puzzle.solution[found.a.cat] || zl.zlIdentity(puzzle.size));
        const invB = zl.zlInvert(puzzle.solution[found.b.cat] || zl.zlIdentity(puzzle.size));
        const posA = found.a.cat === 'position' ? found.a.val : invA[found.a.val];
        const posB = found.b.cat === 'position' ? found.b.val : invB[found.b.val];
        expect(posA).toBeLessThan(posB);
        const text = zl.zlFormatClue(found, puzzle.categories);
        expect(text.toLowerCase()).toMatch(/before|lower study number/);
      }
    }
    expect(found).toBeTruthy();
  });
});
