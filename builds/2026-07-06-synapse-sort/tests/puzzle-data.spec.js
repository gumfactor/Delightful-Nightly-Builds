const { test, expect } = require('@playwright/test');
const { pageUrl } = require('./helpers');

test.describe('puzzle bank data integrity', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(pageUrl());
  });

  test('contains exactly 30 puzzles', async ({ page }) => {
    const count = await page.evaluate(() => PUZZLES.length);
    expect(count).toBe(30);
  });

  test('every puzzle has 4 categories with 4 unique items each (16 unique total)', async ({ page }) => {
    const results = await page.evaluate(() =>
      PUZZLES.map((p) => {
        const allItems = p.categories.flatMap((c) => c.items);
        return {
          id: p.id,
          categoryCount: p.categories.length,
          itemCounts: p.categories.map((c) => c.items.length),
          uniqueItemCount: new Set(allItems).size,
          totalItemCount: allItems.length
        };
      })
    );
    for (const r of results) {
      expect(r.categoryCount, r.id).toBe(4);
      expect(r.itemCounts, r.id).toEqual([4, 4, 4, 4]);
      expect(r.totalItemCount, r.id).toBe(16);
      expect(r.uniqueItemCount, r.id).toBe(16);
    }
  });

  test('every puzzle has exactly one category of each difficulty tier', async ({ page }) => {
    const results = await page.evaluate(() =>
      PUZZLES.map((p) => p.categories.map((c) => c.difficulty).sort().join(','))
    );
    for (const diffs of results) {
      expect(diffs).toBe('blue,green,purple,yellow');
    }
  });

  test('every puzzle id is unique', async ({ page }) => {
    const ids = await page.evaluate(() => PUZZLES.map((p) => p.id));
    expect(new Set(ids).size).toBe(ids.length);
  });

  test('DIFFICULTY_ORDER and DIFFICULTY_EMOJI cover exactly the four tiers', async ({ page }) => {
    const order = await page.evaluate(() => DIFFICULTY_ORDER);
    const emojiKeys = await page.evaluate(() => Object.keys(DIFFICULTY_EMOJI).sort());
    expect(order.sort()).toEqual(['blue', 'green', 'purple', 'yellow']);
    expect(emojiKeys).toEqual(['blue', 'green', 'purple', 'yellow']);
  });
});
