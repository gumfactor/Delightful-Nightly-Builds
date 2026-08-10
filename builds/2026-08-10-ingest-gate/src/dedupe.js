// Duplicate detection: exact full-row duplicates, plus per-unique-column
// normalized-key duplicates (a schema column can be flagged `unique`, e.g.
// business_name or website, so that "Tim Hortons" appearing twice — or the
// same URL with/without a protocol and trailing slash — is caught even
// though the rows aren't byte-identical).
//
// Both duplicate kinds are treated as blocking errors: a duplicate listing
// reaching the live directory is exactly the kind of thing this tool exists
// to catch before ingestion.

(function (global) {
  'use strict';

  function normalizeText(value) {
    return value.trim().toLowerCase().replace(/\s+/g, ' ');
  }

  function normalizeUrl(value) {
    let v = normalizeText(value);
    v = v.replace(/^https?:\/\//, '');
    v = v.replace(/^www\./, '');
    v = v.replace(/\/+$/, '');
    return v;
  }

  function normalizeForColumn(value, columnType) {
    return columnType === 'url' ? normalizeUrl(value) : normalizeText(value);
  }

  function findExactRowDuplicates(rows, raggedRowIndices) {
    const issues = [];
    const seen = new Map(); // normalized row key -> first rowIndex

    rows.forEach((row, idx) => {
      if (raggedRowIndices.includes(idx)) return; // alignment untrustworthy
      const key = row.map((f) => normalizeText(f)).join('');
      if (key === '') return; // skip fully-blank rows

      if (seen.has(key)) {
        issues.push({
          code: 'duplicate_row',
          severity: 'error',
          rowIndex: idx,
          displayRow: idx + 2,
          column: null,
          value: null,
          firstOccurrenceDisplayRow: seen.get(key) + 2,
          message: `Row is an exact duplicate of row ${seen.get(key) + 2}.`,
        });
      } else {
        seen.set(key, idx);
      }
    });

    return issues;
  }

  function findUniqueColumnDuplicates(header, rows, schema, raggedRowIndices) {
    const issues = [];
    const uniqueColumns = schema.filter((c) => c.unique);
    if (uniqueColumns.length === 0) return issues;

    uniqueColumns.forEach((col) => {
      const colIndex = header.indexOf(col.name);
      if (colIndex === -1) return; // header-level "missing" already reported

      const seen = new Map(); // normalized value -> first rowIndex
      rows.forEach((row, idx) => {
        if (raggedRowIndices.includes(idx)) return;
        const raw = row[colIndex];
        if (raw === undefined || raw === '') return;
        const key = normalizeForColumn(raw, col.type);
        if (key === '') return;

        if (seen.has(key)) {
          issues.push({
            code: 'duplicate_key',
            severity: 'error',
            rowIndex: idx,
            displayRow: idx + 2,
            column: col.name,
            value: raw,
            firstOccurrenceDisplayRow: seen.get(key) + 2,
            message: `"${raw}" in column "${col.name}" duplicates row ${seen.get(key) + 2}.`,
          });
        } else {
          seen.set(key, idx);
        }
      });
    });

    return issues;
  }

  function findDuplicates(parsed, schema) {
    const { header, rows, raggedRowIndices } = parsed;
    return [
      ...findExactRowDuplicates(rows, raggedRowIndices),
      ...findUniqueColumnDuplicates(header, rows, schema, raggedRowIndices),
    ];
  }

  const Dedupe = {
    normalizeText,
    normalizeUrl,
    normalizeForColumn,
    findExactRowDuplicates,
    findUniqueColumnDuplicates,
    findDuplicates,
  };

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = Dedupe;
  } else {
    global.Dedupe = Dedupe;
  }
})(typeof window !== 'undefined' ? window : globalThis);
