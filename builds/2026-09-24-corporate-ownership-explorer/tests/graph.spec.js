const { test, expect } = require('@playwright/test');
const path = require('path');

const INDEX_URL = `file://${path.resolve(__dirname, '../index.html')}`;

test.describe('OwnershipGraph — pure logic', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(INDEX_URL);
  });

  test('buildParentChain resolves a linear chain until no parent is found', async ({ page }) => {
    const result = await page.evaluate(async () => {
      const parents = {
        Q1: { id: 'Q2', label: 'B Holdings', property: 'P127' },
        Q2: { id: 'Q3', label: 'C Group', property: 'P749' },
        Q3: null,
      };
      const getParent = async (id) => parents[id] || null;
      return window.OwnershipGraph.buildParentChain('Q1', getParent);
    });
    expect(result.chain.map((n) => n.id)).toEqual(['Q2', 'Q3']);
    expect(result.cycleDetected).toBe(false);
    expect(result.depthCapped).toBe(false);
  });

  test('buildParentChain returns an empty chain for a company with no recorded parent', async ({ page }) => {
    const result = await page.evaluate(async () => {
      const getParent = async () => null;
      return window.OwnershipGraph.buildParentChain('Q1', getParent);
    });
    expect(result.chain).toEqual([]);
    expect(result.cycleDetected).toBe(false);
  });

  test('buildParentChain stops and flags a cycle instead of looping forever', async ({ page }) => {
    const result = await page.evaluate(async () => {
      const parents = {
        Q1: { id: 'Q2', label: 'B', property: 'P127' },
        Q2: { id: 'Q1', label: 'A', property: 'P127' },
      };
      const getParent = async (id) => parents[id] || null;
      return window.OwnershipGraph.buildParentChain('Q1', getParent);
    });
    expect(result.chain.map((n) => n.id)).toEqual(['Q2']);
    expect(result.cycleDetected).toBe(true);
  });

  test('buildParentChain respects the default max depth and flags depthCapped', async ({ page }) => {
    const result = await page.evaluate(async () => {
      const getParent = async (id) => {
        const n = Number(id.slice(1));
        if (n >= 20) return null;
        return { id: `Q${n + 1}`, label: `Company ${n + 1}`, property: 'P127' };
      };
      return window.OwnershipGraph.buildParentChain('Q0', getParent);
    });
    expect(result.chain).toHaveLength(8); // MAX_CHAIN_DEPTH default
    expect(result.depthCapped).toBe(true);
    expect(result.cycleDetected).toBe(false);
  });

  test('buildParentChain honors a custom maxDepth and does not flag depthCapped when the chain ends naturally within it', async ({ page }) => {
    const result = await page.evaluate(async () => {
      const parents = {
        Q1: { id: 'Q2', label: 'B', property: 'P127' },
        Q2: null,
      };
      const getParent = async (id) => parents[id] || null;
      return window.OwnershipGraph.buildParentChain('Q1', getParent, 3);
    });
    expect(result.chain.map((n) => n.id)).toEqual(['Q2']);
    expect(result.depthCapped).toBe(false);
  });

  test('dedupeEntities keeps the first occurrence and drops later duplicates by id', async ({ page }) => {
    const result = await page.evaluate(() => {
      return window.OwnershipGraph.dedupeEntities([
        { id: 'Q1', label: 'First' },
        { id: 'Q2', label: 'Other' },
        { id: 'Q1', label: 'Duplicate, should be dropped' },
      ]);
    });
    expect(result).toEqual([
      { id: 'Q1', label: 'First' },
      { id: 'Q2', label: 'Other' },
    ]);
  });

  test('dedupeEntities ignores entries without an id', async ({ page }) => {
    const result = await page.evaluate(() => {
      return window.OwnershipGraph.dedupeEntities([{ label: 'No id' }, { id: 'Q1', label: 'Valid' }]);
    });
    expect(result).toEqual([{ id: 'Q1', label: 'Valid' }]);
  });

  test('formatCitationUrl builds the exact Wikidata statement anchor', async ({ page }) => {
    const url = await page.evaluate(() => window.OwnershipGraph.formatCitationUrl('Q123', 'P127'));
    expect(url).toBe('https://www.wikidata.org/wiki/Q123#P127');
  });

  test('formatCitationUrl returns null when the entity or property id is missing', async ({ page }) => {
    const results = await page.evaluate(() => [
      window.OwnershipGraph.formatCitationUrl(null, 'P127'),
      window.OwnershipGraph.formatCitationUrl('Q123', null),
    ]);
    expect(results).toEqual([null, null]);
  });

  test('formatQualifiers formats a point-in-time qualifier as "as of <year>"', async ({ page }) => {
    const text = await page.evaluate(() =>
      window.OwnershipGraph.formatQualifiers({ pointInTime: '2020-00-00T00:00:00Z' })
    );
    expect(text).toBe('as of 2020');
  });

  test('formatQualifiers formats a start+end range as "<start>–<end>"', async ({ page }) => {
    const text = await page.evaluate(() =>
      window.OwnershipGraph.formatQualifiers({
        startTime: '2015-00-00T00:00:00Z',
        endTime: '2019-00-00T00:00:00Z',
      })
    );
    expect(text).toBe('2015–2019');
  });

  test('formatQualifiers formats a start-only qualifier as "since <year>"', async ({ page }) => {
    const text = await page.evaluate(() =>
      window.OwnershipGraph.formatQualifiers({ startTime: '2018-00-00T00:00:00Z' })
    );
    expect(text).toBe('since 2018');
  });

  test('formatQualifiers formats an end-only qualifier as "until <year>"', async ({ page }) => {
    const text = await page.evaluate(() =>
      window.OwnershipGraph.formatQualifiers({ endTime: '2022-00-00T00:00:00Z' })
    );
    expect(text).toBe('until 2022');
  });

  test('formatQualifiers returns null when there are no qualifiers at all', async ({ page }) => {
    const results = await page.evaluate(() => [
      window.OwnershipGraph.formatQualifiers(null),
      window.OwnershipGraph.formatQualifiers({}),
    ]);
    expect(results).toEqual([null, null]);
  });

  test('parseSparqlBindings normalizes a full row including qualifiers and a statement URL', async ({ page }) => {
    const result = await page.evaluate(() => {
      const json = {
        results: {
          bindings: [
            {
              parent: { value: 'http://www.wikidata.org/entity/Q42' },
              parentLabel: { value: 'Acme Holdings' },
              prop: { value: 'http://www.wikidata.org/prop/direct/P127' },
              pointInTime: { value: '2021-00-00T00:00:00Z' },
            },
          ],
        },
      };
      return window.OwnershipGraph.parseSparqlBindings(json, {
        idVar: 'parent',
        labelVar: 'parentLabel',
        propVar: 'prop',
        pointInTimeVar: 'pointInTime',
      });
    });
    expect(result).toEqual([
      {
        id: 'Q42',
        label: 'Acme Holdings',
        property: 'P127',
        qualifierText: 'as of 2021',
        statementUrl: 'https://www.wikidata.org/wiki/Q42#P127',
      },
    ]);
  });

  test('parseSparqlBindings handles a row with missing optional qualifier fields', async ({ page }) => {
    const result = await page.evaluate(() => {
      const json = {
        results: {
          bindings: [
            {
              sub: { value: 'http://www.wikidata.org/entity/Q7' },
              subLabel: { value: 'Sub Co' },
              prop: { value: 'http://www.wikidata.org/prop/direct/P355' },
            },
          ],
        },
      };
      return window.OwnershipGraph.parseSparqlBindings(json, {
        idVar: 'sub',
        labelVar: 'subLabel',
        propVar: 'prop',
      });
    });
    expect(result).toEqual([
      { id: 'Q7', label: 'Sub Co', property: 'P355', qualifierText: null, statementUrl: 'https://www.wikidata.org/wiki/Q7#P355' },
    ]);
  });

  test('parseSparqlBindings returns an empty list for malformed or empty SPARQL JSON', async ({ page }) => {
    const results = await page.evaluate(() => [
      window.OwnershipGraph.parseSparqlBindings(null, { idVar: 'x' }),
      window.OwnershipGraph.parseSparqlBindings({}, { idVar: 'x' }),
      window.OwnershipGraph.parseSparqlBindings({ results: { bindings: [] } }, { idVar: 'x' }),
    ]);
    expect(results).toEqual([[], [], []]);
  });

  test('parseSearchResults normalizes a typical wbsearchentities response', async ({ page }) => {
    const result = await page.evaluate(() => {
      const json = {
        search: [
          { id: 'Q95', label: 'Google', description: 'American technology company' },
          { id: 'Q312', label: 'Apple Inc.' },
        ],
      };
      return window.OwnershipGraph.parseSearchResults(json);
    });
    expect(result).toEqual([
      { id: 'Q95', label: 'Google', description: 'American technology company' },
      { id: 'Q312', label: 'Apple Inc.', description: '' },
    ]);
  });

  test('parseSearchResults returns an empty list for zero results', async ({ page }) => {
    const result = await page.evaluate(() => window.OwnershipGraph.parseSearchResults({ search: [] }));
    expect(result).toEqual([]);
  });

  test('parseSearchResults returns an empty list for malformed input rather than throwing', async ({ page }) => {
    const results = await page.evaluate(() => [
      window.OwnershipGraph.parseSearchResults(null),
      window.OwnershipGraph.parseSearchResults({}),
    ]);
    expect(results).toEqual([[], []]);
  });

  test('choosePrimaryParent prefers "owned by" (P127) over "parent organization" (P749)', async ({ page }) => {
    const result = await page.evaluate(() =>
      window.OwnershipGraph.choosePrimaryParent([
        { id: 'Q2', property: 'P749' },
        { id: 'Q3', property: 'P127' },
      ])
    );
    expect(result).toEqual({ id: 'Q3', property: 'P127' });
  });

  test('choosePrimaryParent breaks ties on the same property by ascending id, deterministically', async ({ page }) => {
    const result = await page.evaluate(() =>
      window.OwnershipGraph.choosePrimaryParent([
        { id: 'Q9', property: 'P127' },
        { id: 'Q2', property: 'P127' },
      ])
    );
    expect(result.id).toBe('Q2');
  });

  test('choosePrimaryParent returns null for an empty list', async ({ page }) => {
    const result = await page.evaluate(() => window.OwnershipGraph.choosePrimaryParent([]));
    expect(result).toBeNull();
  });
});
