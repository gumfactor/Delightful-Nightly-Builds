const { test, expect } = require('@playwright/test');
const path = require('path');
const fs = require('fs');
const sparql = require('../src/sparql.js');
const render = require('../src/render.js');

const fixture = JSON.parse(
  fs.readFileSync(path.join(__dirname, '..', 'fixtures', 'sparql-response.json'), 'utf8')
);
const rows = sparql.parseResults(fixture);

test.describe('escapeCsvField', () => {
  test('leaves a plain field unquoted', () => {
    expect(render.escapeCsvField('Retail')).toBe('Retail');
  });

  test('quotes and escapes a field containing a comma', () => {
    expect(render.escapeCsvField('Oil, Gas & Mining')).toBe('"Oil, Gas & Mining"');
  });

  test('doubles embedded quotes', () => {
    expect(render.escapeCsvField('The "Big" Bank')).toBe('"The ""Big"" Bank"');
  });

  test('quotes a field containing a newline', () => {
    expect(render.escapeCsvField('Line1\nLine2')).toBe('"Line1\nLine2"');
  });
});

test.describe('rowsToCSV', () => {
  test('produces a header row plus one row per entry', () => {
    const csv = render.rowsToCSV([{ industry: 'Retail', province: 'Ontario', count: 40 }]);
    const lines = csv.split('\r\n');
    expect(lines[0]).toBe('industry,province,count');
    expect(lines[1]).toBe('Retail,Ontario,40');
    expect(lines).toHaveLength(2);
  });

  test('escapes a comma-bearing industry name in context', () => {
    const csv = render.rowsToCSV([{ industry: 'Oil, Gas & Mining', province: 'Alberta', count: 5 }]);
    expect(csv).toContain('"Oil, Gas & Mining",Alberta,5');
  });

  test('round-trips the full fixture without dropping rows', () => {
    const csv = render.rowsToCSV(rows);
    expect(csv.split('\r\n')).toHaveLength(rows.length + 1);
  });
});

test.describe('filterRows', () => {
  test('returns all rows when filter text is empty', () => {
    expect(render.filterRows(rows, '')).toHaveLength(rows.length);
  });

  test('matches case-insensitively on industry', () => {
    const filtered = render.filterRows(rows, 'retail');
    expect(filtered).toHaveLength(3);
    expect(filtered.every((r) => r.industry === 'Retail')).toBe(true);
  });

  test('matches on province too', () => {
    const filtered = render.filterRows(rows, 'ontario');
    expect(filtered.every((r) => r.province === 'Ontario')).toBe(true);
    expect(filtered).toHaveLength(6);
  });

  test('returns an empty array when nothing matches', () => {
    expect(render.filterRows(rows, 'zzz-nonexistent')).toEqual([]);
  });
});

test.describe('sortRows', () => {
  test('sorts by count ascending', () => {
    const sorted = render.sortRows(rows, 'count', 1);
    expect(sorted[0].count).toBeLessThanOrEqual(sorted[1].count);
    expect(sorted[0].count).toBe(3);
  });

  test('sorts by count descending', () => {
    const sorted = render.sortRows(rows, 'count', -1);
    expect(sorted[0].count).toBe(40);
  });

  test('sorts by industry name alphabetically', () => {
    const sorted = render.sortRows(rows, 'industry', 1);
    expect(sorted[0].industry).toBe('Banking');
  });

  test('does not mutate the input array', () => {
    const copy = rows.slice();
    render.sortRows(rows, 'count', -1);
    expect(rows).toEqual(copy);
  });
});

test.describe('deltaLabel', () => {
  test('formats an increase with a leading plus sign', () => {
    expect(render.deltaLabel({ status: 'increased', delta: 15 })).toBe('+15');
  });

  test('formats a decrease with the sign already present', () => {
    expect(render.deltaLabel({ status: 'decreased', delta: -8 })).toBe('-8');
  });

  test('formats new/removed/unchanged as words or a dash', () => {
    expect(render.deltaLabel({ status: 'new', delta: 55 })).toBe('new');
    expect(render.deltaLabel({ status: 'removed', delta: -10 })).toBe('gone');
    expect(render.deltaLabel({ status: 'unchanged', delta: 0 })).toBe('—');
  });

  test('returns an empty string when there is no delta entry', () => {
    expect(render.deltaLabel(null)).toBe('');
  });
});

test.describe('buildChartConfig', () => {
  test('maps totals into Chart.js bar-chart labels and data arrays', () => {
    const totals = [
      { name: 'Retail', count: 65, pct: 29.68 },
      { name: 'Technology', count: 55, pct: 25.11 },
    ];
    const config = render.buildChartConfig(totals, 'Companies', { text: '#000', grid: '#ccc', bar: '#00f' });
    expect(config.type).toBe('bar');
    expect(config.data.labels).toEqual(['Retail', 'Technology']);
    expect(config.data.datasets[0].data).toEqual([65, 55]);
    expect(config.data.datasets[0].label).toBe('Companies');
  });
});
