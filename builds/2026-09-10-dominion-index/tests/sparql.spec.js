const { test, expect } = require('@playwright/test');
const path = require('path');
const fs = require('fs');
const sparql = require('../src/sparql.js');

const fixture = JSON.parse(
  fs.readFileSync(path.join(__dirname, '..', 'fixtures', 'sparql-response.json'), 'utf8')
);

test.describe('buildQuery', () => {
  test('uses headquarters-country check instead of the naive company-country filter', () => {
    const query = sparql.buildQuery();
    expect(query).toContain('?company wdt:P159 ?hq');
    expect(query).toContain('?hq wdt:P17 wd:Q16');
    // Must NOT filter on the company's own P17 as the ownership signal.
    expect(query).not.toMatch(/\?company\s+wdt:P17\s+wd:Q16/);
  });

  test('excludes companies with a recorded non-Canadian parent organization', () => {
    const query = sparql.buildQuery();
    expect(query).toContain('FILTER NOT EXISTS');
    expect(query).toContain('wdt:P749 ?parent');
    expect(query).toContain('wdt:P127 ?parent');
    expect(query).toContain('FILTER(?parentCountry != wd:Q16)');
  });

  test('groups by industry and province with a COALESCE fallback bucket', () => {
    const query = sparql.buildQuery();
    expect(query).toContain('COALESCE(?industryLabelRaw, "Unclassified")');
    expect(query).toContain('COALESCE(?provinceLabelRaw, "Unknown")');
    expect(query).toContain('GROUP BY ?industryLabel ?provinceLabel');
  });

  test('restricts province matching to the 13 real province/territory QIDs', () => {
    const query = sparql.buildQuery();
    for (const qid of sparql.PROVINCE_QIDS) {
      expect(query).toContain(qid);
    }
    expect(sparql.PROVINCE_QIDS).toHaveLength(13);
  });
});

test.describe('buildQueryUrl', () => {
  test('targets the public Wikidata endpoint with the query URL-encoded', () => {
    const url = sparql.buildQueryUrl();
    expect(url.startsWith('https://query.wikidata.org/sparql?')).toBe(true);
    expect(url).toContain('format=json');
    const params = new URLSearchParams(url.split('?')[1]);
    expect(params.get('query')).toContain('SELECT ?industryLabel');
  });
});

test.describe('parseResults', () => {
  test('parses a realistic multi-row response into flat {industry, province, count} rows', () => {
    const rows = sparql.parseResults(fixture);
    expect(rows).toHaveLength(14);
    expect(rows[0]).toEqual({ industry: 'Retail', province: 'Ontario', count: 40 });
    const banking = rows.find((r) => r.industry === 'Banking' && r.province === 'Nova Scotia');
    expect(banking.count).toBe(6);
  });

  test('accepts a raw JSON string, not just a parsed object', () => {
    const rows = sparql.parseResults(JSON.stringify(fixture));
    expect(rows).toHaveLength(14);
  });

  test('handles an empty bindings array without error', () => {
    const rows = sparql.parseResults({ head: { vars: [] }, results: { bindings: [] } });
    expect(rows).toEqual([]);
  });

  test('throws a specific error on invalid JSON text (e.g. a Wikidata timeout HTML page)', () => {
    expect(() => sparql.parseResults('<html>java.util.concurrent.TimeoutException</html>')).toThrow(
      sparql.SparqlResultError
    );
  });

  test('throws a specific error when results.bindings is missing', () => {
    expect(() => sparql.parseResults({ head: {} })).toThrow(/results\.bindings/);
  });

  test('throws a specific error when a row is missing a required field', () => {
    expect(() =>
      sparql.parseResults({
        results: { bindings: [{ industryLabel: { value: 'Retail' } }] },
      })
    ).toThrow(sparql.SparqlResultError);
  });

  test('throws a specific error when count is not numeric', () => {
    expect(() =>
      sparql.parseResults({
        results: {
          bindings: [
            {
              industryLabel: { value: 'Retail' },
              provinceLabel: { value: 'Ontario' },
              count: { value: 'not-a-number' },
            },
          ],
        },
      })
    ).toThrow(/non-numeric count/);
  });
});
