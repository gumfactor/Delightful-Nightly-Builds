const { test, expect } = require('@playwright/test');
const path = require('path');
const fs = require('fs');
const sparql = require('../src/sparql.js');
const aggregate = require('../src/aggregate.js');

const fixture = JSON.parse(
  fs.readFileSync(path.join(__dirname, '..', 'fixtures', 'sparql-response.json'), 'utf8')
);
const rows = sparql.parseResults(fixture);

test.describe('aggregateIndustryTotals', () => {
  test('sums counts per industry and sorts descending, matching hand-computed totals', () => {
    const totals = aggregate.aggregateIndustryTotals(rows);
    expect(totals.map((t) => [t.name, t.count])).toEqual([
      ['Retail', 65],
      ['Technology', 55],
      ['Mining', 30],
      ['Banking', 28],
      ['Food industry', 26],
      ['Unclassified', 15],
    ]);
  });

  test('percentages sum to 100 across all industries', () => {
    const totals = aggregate.aggregateIndustryTotals(rows);
    const totalPct = totals.reduce((sum, t) => sum + t.pct, 0);
    expect(totalPct).toBeCloseTo(100, 5);
  });

  test('Retail is computed as ~29.68% of the total', () => {
    const totals = aggregate.aggregateIndustryTotals(rows);
    const retail = totals.find((t) => t.name === 'Retail');
    expect(retail.pct).toBeCloseTo((65 / 219) * 100, 5);
  });
});

test.describe('aggregateProvinceTotals', () => {
  test('sums counts per province and breaks a count tie alphabetically', () => {
    const totals = aggregate.aggregateProvinceTotals(rows);
    // British Columbia and Unknown are tied at 15; "British Columbia" sorts first.
    expect(totals.map((t) => [t.name, t.count])).toEqual([
      ['Ontario', 117],
      ['Quebec', 41],
      ['Alberta', 25],
      ['British Columbia', 15],
      ['Unknown', 15],
      ['Nova Scotia', 6],
    ]);
  });
});

test.describe('totalsToSortedList via empty input', () => {
  test('returns an empty list with no division-by-zero error on percentages', () => {
    const totals = aggregate.aggregateIndustryTotals([]);
    expect(totals).toEqual([]);
  });
});

test.describe('topNWithOther', () => {
  test('keeps the list unchanged when n is >= the list length', () => {
    const totals = aggregate.aggregateIndustryTotals(rows);
    expect(aggregate.topNWithOther(totals, 10)).toEqual(totals);
  });

  test('folds the remainder into a single Other bucket that preserves the grand total', () => {
    const totals = aggregate.aggregateIndustryTotals(rows);
    const top3 = aggregate.topNWithOther(totals, 3);
    expect(top3).toHaveLength(4);
    expect(top3[3].name).toBe('Other');
    expect(top3[3].count).toBe(28 + 26 + 15);
    const grandTotal = top3.reduce((sum, t) => sum + t.count, 0);
    expect(grandTotal).toBe(219);
  });
});

test.describe('computeDelta', () => {
  const previous = [
    { name: 'Retail', count: 50 },
    { name: 'Mining', count: 30 },
    { name: 'OldIndustry', count: 10 },
  ];
  const current = [
    { name: 'Retail', count: 65 },
    { name: 'Mining', count: 30 },
    { name: 'Technology', count: 55 },
  ];
  const delta = aggregate.computeDelta(previous, current);

  test('classifies a count increase with the correct delta', () => {
    expect(delta.get('Retail')).toEqual({ previousCount: 50, currentCount: 65, status: 'increased', delta: 15 });
  });

  test('classifies an unchanged count', () => {
    expect(delta.get('Mining')).toEqual({ previousCount: 30, currentCount: 30, status: 'unchanged', delta: 0 });
  });

  test('classifies an entry only present now as new', () => {
    expect(delta.get('Technology')).toEqual({ previousCount: 0, currentCount: 55, status: 'new', delta: 55 });
  });

  test('classifies an entry only present before as removed', () => {
    expect(delta.get('OldIndustry')).toEqual({ previousCount: 10, currentCount: 0, status: 'removed', delta: -10 });
  });

  test('handles an empty previous snapshot by marking everything new', () => {
    const freshDelta = aggregate.computeDelta([], current);
    expect(freshDelta.get('Retail').status).toBe('new');
    expect(freshDelta.size).toBe(3);
  });

  test('handles a decrease correctly', () => {
    const decreaseDelta = aggregate.computeDelta([{ name: 'X', count: 20 }], [{ name: 'X', count: 12 }]);
    expect(decreaseDelta.get('X')).toEqual({ previousCount: 20, currentCount: 12, status: 'decreased', delta: -8 });
  });
});
