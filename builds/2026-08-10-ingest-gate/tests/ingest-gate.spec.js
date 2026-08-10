const { test, expect } = require('@playwright/test');
const path = require('path');
const fs = require('fs');

const APP_URL = 'file://' + path.join(__dirname, '..', 'index.html');

async function gotoApp(page) {
  await page.goto(APP_URL);
  await page.evaluate(() => localStorage.clear());
  await page.reload();
}

// A single seeded fixture exercising: a valid row, a missing-required-value
// row, an invalid URL, an invalid enum value, a whitespace + duplicate-key
// row, and a malformed (ragged) row — against the default schema preset
// (business_name, website, category, province_territory,
// canadian_ownership_pct, notes).
const HEADER = 'business_name,website,category,province_territory,canadian_ownership_pct,notes';
const ROW_VALID = 'Maple Made Goods,https://mapledgoods.ca,Retail,ON,100,Great local shop';
const ROW_MISSING_VALUE = 'Northern Lights Co,https://northernlights.ca,,BC,80,';
const ROW_BAD_URL = 'Prairie Provisions,not-a-url,Food & Beverage,SK,90,';
const ROW_BAD_ENUM = 'Coastal Crafts,https://coastalcrafts.ca,Nonsense Category,NS,100,';
const ROW_DUP_WHITESPACE = ' maple made goods ,https://different.ca,Services,AB,50,';
const ROW_MALFORMED = 'Broken Row,https://broken.ca,Retail,ON';

const SEEDED_CSV = [
  HEADER,
  ROW_VALID,
  ROW_MISSING_VALUE,
  ROW_BAD_URL,
  ROW_BAD_ENUM,
  ROW_DUP_WHITESPACE,
  ROW_MALFORMED,
].join('\n');

async function uploadCsvText(page, csvText, fileName) {
  await page.setInputFiles('[data-testid="file-input"]', {
    name: fileName || 'test.csv',
    mimeType: 'text/csv',
    buffer: Buffer.from(csvText, 'utf-8'),
  });
  await expect(page.locator('[data-testid="results"]')).toBeVisible();
}

// ---------------------------------------------------------------------
// CSV parser
// ---------------------------------------------------------------------

test.describe('CsvParser', () => {
  test('parses a simple CSV into header and rows', async ({ page }) => {
    await gotoApp(page);
    const result = await page.evaluate(() => window.CsvParser.parseCSV('a,b,c\n1,2,3\n4,5,6'));
    expect(result.header).toEqual(['a', 'b', 'c']);
    expect(result.rows).toEqual([
      ['1', '2', '3'],
      ['4', '5', '6'],
    ]);
    expect(result.raggedRowIndices).toEqual([]);
  });

  test('handles a quoted field containing a comma', async ({ page }) => {
    await gotoApp(page);
    const result = await page.evaluate(() =>
      window.CsvParser.parseCSV('name,notes\n"Acme, Inc.",Great supplier')
    );
    expect(result.rows[0]).toEqual(['Acme, Inc.', 'Great supplier']);
  });

  test('handles a quoted field containing an embedded newline', async ({ page }) => {
    await gotoApp(page);
    const result = await page.evaluate(() =>
      window.CsvParser.parseCSV('name,notes\n"Acme","Line one\nLine two"')
    );
    expect(result.rows[0]).toEqual(['Acme', 'Line one\nLine two']);
  });

  test('handles an escaped double-quote inside a quoted field', async ({ page }) => {
    await gotoApp(page);
    const result = await page.evaluate(() =>
      window.CsvParser.parseCSV('name\n"She said ""hi"""')
    );
    expect(result.rows[0]).toEqual(['She said "hi"']);
  });

  test('strips a leading UTF-8 BOM from the header', async ({ page }) => {
    await gotoApp(page);
    const result = await page.evaluate(() => window.CsvParser.parseCSV('﻿name,url\nAcme,https://acme.ca'));
    expect(result.header).toEqual(['name', 'url']);
  });

  test('flags a ragged row with too few fields', async ({ page }) => {
    await gotoApp(page);
    const result = await page.evaluate(() => window.CsvParser.parseCSV('a,b,c\n1,2'));
    expect(result.raggedRowIndices).toEqual([0]);
  });

  test('flags a ragged row with too many fields', async ({ page }) => {
    await gotoApp(page);
    const result = await page.evaluate(() => window.CsvParser.parseCSV('a,b,c\n1,2,3,4'));
    expect(result.raggedRowIndices).toEqual([0]);
  });

  test('treats CRLF line endings the same as LF', async ({ page }) => {
    await gotoApp(page);
    const result = await page.evaluate(() => window.CsvParser.parseCSV('a,b\r\n1,2\r\n3,4'));
    expect(result.rows).toEqual([
      ['1', '2'],
      ['3', '4'],
    ]);
  });
});

// ---------------------------------------------------------------------
// Schema
// ---------------------------------------------------------------------

test.describe('Schema', () => {
  test('defaultPreset includes business_name and website as required unique columns', async ({ page }) => {
    await gotoApp(page);
    const preset = await page.evaluate(() => window.Schema.defaultPreset());
    const byName = Object.fromEntries(preset.map((c) => [c.name, c]));
    expect(byName.business_name.required).toBe(true);
    expect(byName.business_name.unique).toBe(true);
    expect(byName.website.type).toBe('url');
  });

  test('saveSchema/loadSchema round-trips a custom schema through localStorage', async ({ page }) => {
    await gotoApp(page);
    const loaded = await page.evaluate(() => {
      const custom = [{ name: 'sku', required: true, type: 'text', unique: true, enumValues: [] }];
      window.Schema.saveSchema(custom);
      return window.Schema.loadSchema();
    });
    expect(loaded).toEqual([{ name: 'sku', required: true, type: 'text', unique: true, enumValues: [] }]);
  });

  test('schemaFromHeader builds all-optional text columns from a header row', async ({ page }) => {
    await gotoApp(page);
    const schema = await page.evaluate(() => window.Schema.schemaFromHeader(['name', 'url']));
    expect(schema).toEqual([
      { name: 'name', required: false, type: 'text', unique: false, enumValues: [] },
      { name: 'url', required: false, type: 'text', unique: false, enumValues: [] },
    ]);
  });

  test('importSchemaJSON rejects a JSON shape without column names', async ({ page }) => {
    await gotoApp(page);
    const errorMessage = await page.evaluate(() => {
      try {
        window.Schema.importSchemaJSON('[{"required": true}]');
        return null;
      } catch (err) {
        return err.message;
      }
    });
    expect(errorMessage).toContain('name');
  });
});

// ---------------------------------------------------------------------
// Validator
// ---------------------------------------------------------------------

test.describe('Validator', () => {
  const schema = [
    { name: 'business_name', required: true, type: 'text', unique: true, enumValues: [] },
    { name: 'website', required: true, type: 'url', unique: false, enumValues: [] },
    { name: 'category', required: true, type: 'enum', unique: false, enumValues: ['Retail', 'Services'] },
    { name: 'ownership_pct', required: false, type: 'number', unique: false, enumValues: [] },
    { name: 'launched', required: false, type: 'date', unique: false, enumValues: [] },
    { name: 'contact_email', required: false, type: 'email', unique: false, enumValues: [] },
  ];

  test('flags a missing required column at the header level', async ({ page }) => {
    await gotoApp(page);
    const issues = await page.evaluate(
      (s) => window.Validator.validateHeader(['business_name', 'category'], s),
      schema
    );
    expect(issues.some((i) => i.code === 'missing_required_column' && i.column === 'website')).toBe(true);
  });

  test('flags an empty required value', async ({ page }) => {
    await gotoApp(page);
    const header = schema.map((c) => c.name);
    const issues = await page.evaluate(
      ({ h, s }) => window.Validator.validateRow(['Acme', 'https://acme.ca', '', '', '', ''], 0, h, s, []),
      { h: header, s: schema }
    );
    expect(issues.find((i) => i.code === 'missing_required_value').column).toBe('category');
  });

  test('flags an invalid URL', async ({ page }) => {
    await gotoApp(page);
    const header = schema.map((c) => c.name);
    const issues = await page.evaluate(
      ({ h, s }) => window.Validator.validateRow(['Acme', 'not-a-url', 'Retail', '', '', ''], 0, h, s, []),
      { h: header, s: schema }
    );
    expect(issues.some((i) => i.code === 'invalid_url')).toBe(true);
  });

  test('flags an invalid email', async ({ page }) => {
    await gotoApp(page);
    const header = schema.map((c) => c.name);
    const issues = await page.evaluate(
      ({ h, s }) =>
        window.Validator.validateRow(['Acme', 'https://acme.ca', 'Retail', '', '', 'not-an-email'], 0, h, s, []),
      { h: header, s: schema }
    );
    expect(issues.some((i) => i.code === 'invalid_email')).toBe(true);
  });

  test('flags an enum value outside the allowed list', async ({ page }) => {
    await gotoApp(page);
    const header = schema.map((c) => c.name);
    const issues = await page.evaluate(
      ({ h, s }) =>
        window.Validator.validateRow(['Acme', 'https://acme.ca', 'Nonsense', '', '', ''], 0, h, s, []),
      { h: header, s: schema }
    );
    expect(issues.some((i) => i.code === 'invalid_enum')).toBe(true);
  });

  test('flags an invalid date', async ({ page }) => {
    await gotoApp(page);
    const header = schema.map((c) => c.name);
    const issues = await page.evaluate(
      ({ h, s }) =>
        window.Validator.validateRow(['Acme', 'https://acme.ca', 'Retail', '', '2024-13-40', ''], 0, h, s, []),
      { h: header, s: schema }
    );
    expect(issues.some((i) => i.code === 'invalid_date')).toBe(true);
  });

  test('flags a non-numeric value in a number column', async ({ page }) => {
    await gotoApp(page);
    const header = schema.map((c) => c.name);
    const issues = await page.evaluate(
      ({ h, s }) =>
        window.Validator.validateRow(['Acme', 'https://acme.ca', 'Retail', 'lots', '', ''], 0, h, s, []),
      { h: header, s: schema }
    );
    expect(issues.some((i) => i.code === 'invalid_number')).toBe(true);
  });

  test('flags leading/trailing whitespace as a warning, not an error', async ({ page }) => {
    await gotoApp(page);
    const header = schema.map((c) => c.name);
    const issues = await page.evaluate(
      ({ h, s }) =>
        window.Validator.validateRow([' Acme ', 'https://acme.ca', 'Retail', '', '', ''], 0, h, s, []),
      { h: header, s: schema }
    );
    const whitespaceIssue = issues.find((i) => i.code === 'whitespace');
    expect(whitespaceIssue.severity).toBe('warning');
  });

  test('a malformed row is reported once and skips all other column checks', async ({ page }) => {
    await gotoApp(page);
    const header = schema.map((c) => c.name);
    const issues = await page.evaluate(
      ({ h, s }) => window.Validator.validateRow(['Acme', 'not-a-url'], 0, h, s, [0]),
      { h: header, s: schema }
    );
    expect(issues).toHaveLength(1);
    expect(issues[0].code).toBe('malformed_row');
  });

  test('validateFile computes correct total/valid/error/warning counts on the seeded fixture', async ({ page }) => {
    await gotoApp(page);
    const summary = await page.evaluate((csv) => {
      const parsed = window.CsvParser.parseCSV(csv);
      const result = window.Validator.validateFile(parsed, window.Schema.defaultPreset());
      return result.summary;
    }, SEEDED_CSV);
    expect(summary.totalRows).toBe(6);
    // rows: valid, missing-value, bad-url, bad-enum, whitespace-warning, malformed
    expect(summary.errorRows).toBe(4); // missing-value, bad-url, bad-enum, malformed
    expect(summary.warningRows).toBe(1); // whitespace row
    expect(summary.validRows).toBe(1); // the clean first row
  });
});

// ---------------------------------------------------------------------
// Dedupe
// ---------------------------------------------------------------------

test.describe('Dedupe', () => {
  test('flags an exact full-row duplicate', async ({ page }) => {
    await gotoApp(page);
    const issues = await page.evaluate(() =>
      window.Dedupe.findExactRowDuplicates(
        [
          ['Acme', 'https://acme.ca'],
          ['Acme', 'https://acme.ca'],
        ],
        []
      )
    );
    expect(issues).toHaveLength(1);
    expect(issues[0].rowIndex).toBe(1);
    expect(issues[0].firstOccurrenceDisplayRow).toBe(2);
  });

  test('flags a normalized URL duplicate (protocol/www/trailing-slash insensitive)', async ({ page }) => {
    await gotoApp(page);
    const schema = [{ name: 'website', required: true, type: 'url', unique: true, enumValues: [] }];
    const issues = await page.evaluate(
      (s) =>
        window.Dedupe.findUniqueColumnDuplicates(
          ['website'],
          [['https://Example.com/'], ['www.example.com']],
          s,
          []
        ),
      schema
    );
    expect(issues).toHaveLength(1);
    expect(issues[0].code).toBe('duplicate_key');
  });

  test('flags a case- and whitespace-insensitive name duplicate', async ({ page }) => {
    await gotoApp(page);
    const schema = [{ name: 'business_name', required: true, type: 'text', unique: true, enumValues: [] }];
    const issues = await page.evaluate(
      (s) =>
        window.Dedupe.findUniqueColumnDuplicates(
          ['business_name'],
          [['Maple Made Goods'], [' maple  made goods ']],
          s,
          []
        ),
      schema
    );
    expect(issues).toHaveLength(1);
  });

  test('does not flag a ragged row in unique-column dedupe', async ({ page }) => {
    await gotoApp(page);
    const schema = [{ name: 'business_name', required: true, type: 'text', unique: true, enumValues: [] }];
    const issues = await page.evaluate(
      (s) =>
        window.Dedupe.findUniqueColumnDuplicates(
          ['business_name'],
          [['Acme'], ['Acme', 'extra-field']],
          s,
          [1]
        ),
      schema
    );
    expect(issues).toHaveLength(0);
  });
});

// ---------------------------------------------------------------------
// Report (cleaned CSV / issues CSV)
// ---------------------------------------------------------------------

test.describe('Report', () => {
  test('buildCleanedCsv appends a QC_Flags column populated only for flagged rows', async ({ page }) => {
    await gotoApp(page);
    const csv = await page.evaluate(() => {
      const parsed = { header: ['name'], rows: [['Acme'], ['']] };
      const rowIssues = [
        { code: 'missing_required_value', severity: 'error', rowIndex: 1, column: 'name', value: '' },
      ];
      return window.Report.buildCleanedCsv(parsed, rowIssues, []);
    });
    const lines = csv.trim().split('\r\n');
    expect(lines[0]).toBe('name,QC_Flags');
    expect(lines[1]).toBe('Acme,');
    expect(lines[2]).toBe(',missing_required_value');
  });

  test('buildIssuesCsv lists header, row, and dedupe issues with their severity', async ({ page }) => {
    await gotoApp(page);
    const csv = await page.evaluate(() => {
      const headerIssues = [
        { code: 'missing_required_column', severity: 'error', displayRow: null, column: 'website', message: 'x', value: null },
      ];
      const rowIssues = [
        { code: 'invalid_url', severity: 'error', displayRow: 3, column: 'website', message: 'y', value: 'bad' },
      ];
      const dedupeIssues = [
        { code: 'duplicate_row', severity: 'error', displayRow: 4, column: null, message: 'z', value: null },
      ];
      return window.Report.buildIssuesCsv(headerIssues, rowIssues, dedupeIssues);
    });
    expect(csv).toContain('header,website,error,missing_required_column');
    expect(csv).toContain('3,website,error,invalid_url');
    expect(csv).toContain('4,,error,duplicate_row');
  });
});

// ---------------------------------------------------------------------
// AI briefing (privacy + fallback behaviour)
// ---------------------------------------------------------------------

test.describe('AiBriefing', () => {
  const summary = {
    totalRows: 10,
    validRows: 6,
    errorRows: 3,
    warningRows: 1,
    byCode: { invalid_url: 2, whitespace: 1, missing_required_value: 1 },
  };

  test('the AI prompt contains only aggregate counts, never a raw cell value', async ({ page }) => {
    await gotoApp(page);
    const prompt = await page.evaluate((s) => window.AiBriefing.buildPrompt(s), summary);
    const jsonMatch = prompt.match(/Aggregate summary \(JSON\): (\{.*\})/);
    expect(jsonMatch).not.toBeNull();
    expect(JSON.parse(jsonMatch[1])).toEqual(summary);
  });

  test('templateBriefing deterministically summarizes counts with no network access', async ({ page }) => {
    await gotoApp(page);
    const text = await page.evaluate((s) => window.AiBriefing.templateBriefing(s), summary);
    expect(text).toContain('10 row(s)');
    expect(text).toContain('6');
  });

  test('generateBriefing with no API key uses the template and makes zero network calls', async ({ page }) => {
    await gotoApp(page);
    let hits = 0;
    await page.route('**://api.anthropic.com/**', (route) => {
      hits += 1;
      route.abort();
    });
    const result = await page.evaluate((s) => window.AiBriefing.generateBriefing(s, null), summary);
    expect(result.source).toBe('template');
    expect(hits).toBe(0);
  });

  test('generateBriefing with a mocked successful Anthropic response returns the AI text', async ({ page }) => {
    await gotoApp(page);
    await page.route('**://api.anthropic.com/v1/messages', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ content: [{ type: 'text', text: 'Fix the URLs first.' }] }),
      });
    });
    const result = await page.evaluate((s) => window.AiBriefing.generateBriefing(s, 'fake-key'), summary);
    expect(result.source).toBe('ai');
    expect(result.text).toBe('Fix the URLs first.');
  });

  test('generateBriefing falls back to the template when the Anthropic call fails', async ({ page }) => {
    await gotoApp(page);
    await page.route('**://api.anthropic.com/v1/messages', (route) => {
      route.fulfill({ status: 500, body: 'server error' });
    });
    const result = await page.evaluate((s) => window.AiBriefing.generateBriefing(s, 'fake-key'), summary);
    expect(result.source).toBe('template-fallback');
    expect(result.text.length).toBeGreaterThan(0);
  });
});

// ---------------------------------------------------------------------
// Full app / UI integration
// ---------------------------------------------------------------------

test.describe('App integration', () => {
  test('uploading the seeded CSV renders the correct summary dashboard', async ({ page }) => {
    await gotoApp(page);
    await uploadCsvText(page, SEEDED_CSV);
    await expect(page.locator('[data-testid="stat-total"]')).toHaveText('6');
    await expect(page.locator('[data-testid="stat-valid"]')).toHaveText('1');
    await expect(page.locator('[data-testid="stat-errors"]')).toHaveText('5');
    await expect(page.locator('[data-testid="stat-warnings"]')).toHaveText('0');
  });

  test('the search box filters the issues table', async ({ page }) => {
    await gotoApp(page);
    await uploadCsvText(page, SEEDED_CSV);
    const before = await page.locator('[data-testid="issue-row"]').count();
    await page.fill('[data-testid="search-input"]', 'malformed_row');
    const after = await page.locator('[data-testid="issue-row"]').count();
    expect(after).toBeLessThan(before);
    expect(after).toBeGreaterThan(0);
  });

  test('the error severity filter chip narrows the table to errors only', async ({ page }) => {
    await gotoApp(page);
    await uploadCsvText(page, SEEDED_CSV);
    await page.click('[data-testid="filter-error"]');
    const severities = await page.locator('[data-testid="issue-row"] td:nth-child(3)').allTextContents();
    expect(severities.length).toBeGreaterThan(0);
    expect(severities.every((s) => s === 'error')).toBe(true);
  });

  test('adding a new required column in the schema editor produces new errors on re-upload', async ({ page }) => {
    await gotoApp(page);
    await page.click('[data-testid="tab-schema"]');
    await page.click('[data-testid="schema-add"]');
    const idx = (await page.locator('[data-testid="schema-table"] tbody tr').count()) - 1;
    await page.fill(`[data-testid="schema-name-${idx}"]`, 'phone_number');
    await page.check(`[data-testid="schema-required-${idx}"]`);

    await page.click('[data-testid="tab-validate"]');
    await uploadCsvText(page, SEEDED_CSV);
    const errorCount = await page.evaluate(() =>
      window.IngestGateApp.state.headerIssues.filter((i) => i.code === 'missing_required_column').length
    );
    expect(errorCount).toBe(1);
  });

  test('clicking a row link opens the row detail panel with the flagged column highlighted', async ({ page }) => {
    await gotoApp(page);
    await uploadCsvText(page, SEEDED_CSV);
    await page.locator('[data-testid="row-link"]').first().click();
    await expect(page.locator('[data-testid="row-detail"]')).toBeVisible();
    const flaggedCount = await page.locator('#row-detail-content .flagged-col').count();
    expect(flaggedCount).toBeGreaterThan(0);
  });

  test('an XSS payload in a CSV cell renders as inert text, never executes', async ({ page }) => {
    await gotoApp(page);
    let dialogFired = false;
    page.on('dialog', async (dialog) => {
      dialogFired = true;
      await dialog.dismiss();
    });

    const payloadCsv = [
      HEADER,
      '<img src=x onerror=alert(1)>,https://acme.ca,Retail,ON,50,"</script><script>window.__xss=1</script>"',
    ].join('\n');
    await uploadCsvText(page, payloadCsv);

    const tableHtml = await page.locator('[data-testid="issues-tbody"]').innerHTML();
    expect(tableHtml).not.toContain('<img');
    expect(tableHtml).not.toContain('<script>');
    const xssFlag = await page.evaluate(() => window.__xss);
    expect(xssFlag).toBeUndefined();
    expect(dialogFired).toBe(false);
  });

  test('downloading the cleaned CSV produces a file containing the QC_Flags column', async ({ page }) => {
    await gotoApp(page);
    await uploadCsvText(page, SEEDED_CSV);
    const downloadPromise = page.waitForEvent('download');
    await page.click('[data-testid="download-cleaned"]');
    const download = await downloadPromise;
    const filePath = await download.path();
    const content = fs.readFileSync(filePath, 'utf-8');
    expect(content.split('\r\n')[0]).toContain('QC_Flags');
    expect(content).toContain('malformed_row');
  });

  test('downloading the issues report produces a file listing every issue code', async ({ page }) => {
    await gotoApp(page);
    await uploadCsvText(page, SEEDED_CSV);
    const downloadPromise = page.waitForEvent('download');
    await page.click('[data-testid="download-issues"]');
    const download = await downloadPromise;
    const filePath = await download.path();
    const content = fs.readFileSync(filePath, 'utf-8');
    expect(content).toContain('invalid_enum');
    expect(content).toContain('duplicate_key');
  });

  test('a completed run appends an aggregate-only entry to History that survives reload', async ({ page }) => {
    await gotoApp(page);
    await uploadCsvText(page, SEEDED_CSV, 'canada-list-export.csv');
    await page.click('[data-testid="tab-history"]');
    await expect(page.locator('[data-testid="history-row"]')).toHaveCount(1);
    const rowText = await page.locator('[data-testid="history-row"]').first().innerText();
    expect(rowText).toContain('canada-list-export.csv');
    expect(rowText).not.toContain('Maple Made Goods');

    await page.reload();
    await page.click('[data-testid="tab-history"]');
    await expect(page.locator('[data-testid="history-row"]')).toHaveCount(1);
  });

  test('uploading a file with invalid UTF-8 bytes shows the encoding warning banner', async ({ page }) => {
    await gotoApp(page);
    const invalidBytes = Buffer.concat([
      Buffer.from('business_name,website\n'),
      Buffer.from([0x41, 0xff, 0xfe]),
      Buffer.from(',https://acme.ca\n'),
    ]);
    await page.setInputFiles('[data-testid="file-input"]', {
      name: 'bad-encoding.csv',
      mimeType: 'text/csv',
      buffer: invalidBytes,
    });
    await expect(page.locator('[data-testid="encoding-warning"]')).toBeVisible();
  });

  test('a clean file with no issues reports 100% valid rows and no warning banner', async ({ page }) => {
    await gotoApp(page);
    const cleanCsv = [HEADER, ROW_VALID, 'Second Shop,https://secondshop.ca,Services,QC,100,All good'].join('\n');
    await uploadCsvText(page, cleanCsv);
    await expect(page.locator('[data-testid="stat-total"]')).toHaveText('2');
    await expect(page.locator('[data-testid="stat-valid"]')).toHaveText('2');
    await expect(page.locator('[data-testid="stat-errors"]')).toHaveText('0');
    await expect(page.locator('[data-testid="issues-empty"]')).toBeVisible();
  });
});
