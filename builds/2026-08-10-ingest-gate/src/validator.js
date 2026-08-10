// Validation engine: takes a parsed CSV (header + rows) and a schema, and
// produces a list of issues at two severities.
//
// severity: 'error'   — blocks a row from being counted "valid" (missing
//                        required column/value, malformed row, bad type,
//                        replacement-character corruption)
// severity: 'warning'  — worth flagging but non-blocking (whitespace,
//                        unexpected column, possible mojibake)
//
// A ragged (malformed) row skips all other per-column checks for that row,
// since column alignment cannot be trusted once field count is wrong.

(function (global) {
  'use strict';

  const CONTROL_CHAR_RE = /[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/;
  const REPLACEMENT_CHAR_RE = /�/;
  // Common UTF-8-decoded-as-Latin-1 mojibake byte sequences.
  const MOJIBAKE_RE = /Ã[-¿]|â€[-]|Â[ -¿]/;
  const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  const ISO_DATE_RE = /^\d{4}-\d{2}-\d{2}$/;

  function isValidUrl(value) {
    try {
      const u = new URL(value);
      return u.protocol === 'http:' || u.protocol === 'https:';
    } catch (err) {
      return false;
    }
  }

  function isValidDate(value) {
    if (!ISO_DATE_RE.test(value)) return false;
    const d = new Date(value + 'T00:00:00Z');
    if (Number.isNaN(d.getTime())) return false;
    // Reject rollover dates like 2024-02-30 which Date would otherwise
    // silently normalize into March.
    return d.toISOString().slice(0, 10) === value;
  }

  function checkType(column, value) {
    if (value === '') return null; // emptiness is handled by the required check
    switch (column.type) {
      case 'url':
        return isValidUrl(value) ? null : 'invalid_url';
      case 'email':
        return EMAIL_RE.test(value) ? null : 'invalid_email';
      case 'number':
        return Number.isFinite(Number(value)) && value.trim() !== '' ? null : 'invalid_number';
      case 'date':
        return isValidDate(value) ? null : 'invalid_date';
      case 'enum':
        if (column.enumValues.length === 0) return null;
        return column.enumValues.some((ev) => ev.toLowerCase() === value.toLowerCase())
          ? null
          : 'invalid_enum';
      default:
        return null;
    }
  }

  const MESSAGES = {
    missing_required_column: (col) => `Required column "${col}" is missing from the file header.`,
    unexpected_column: (col) => `Column "${col}" is not defined in the schema.`,
    malformed_row: (expected, actual) =>
      `Row has ${actual} field(s), expected ${expected} based on the header.`,
    missing_required_value: (col) => `Required column "${col}" is empty.`,
    invalid_url: (col, value) => `"${value}" in column "${col}" is not a valid http(s) URL.`,
    invalid_email: (col, value) => `"${value}" in column "${col}" is not a valid email address.`,
    invalid_number: (col, value) => `"${value}" in column "${col}" is not a valid number.`,
    invalid_date: (col, value) => `"${value}" in column "${col}" is not a valid YYYY-MM-DD date.`,
    invalid_enum: (col, value) =>
      `"${value}" in column "${col}" is not one of the allowed values.`,
    whitespace: (col) => `Column "${col}" has leading or trailing whitespace.`,
    encoding_control_char: (col) => `Column "${col}" contains a non-printable control character.`,
    encoding_replacement_char: (col) =>
      `Column "${col}" contains the Unicode replacement character — the file may not be valid UTF-8.`,
    encoding_mojibake: (col) =>
      `Column "${col}" contains a pattern consistent with mis-decoded text (mojibake).`,
  };

  const SEVERITY = {
    missing_required_column: 'error',
    unexpected_column: 'warning',
    malformed_row: 'error',
    missing_required_value: 'error',
    invalid_url: 'error',
    invalid_email: 'error',
    invalid_number: 'error',
    invalid_date: 'error',
    invalid_enum: 'error',
    whitespace: 'warning',
    encoding_control_char: 'warning',
    encoding_replacement_char: 'error',
    encoding_mojibake: 'warning',
  };

  // `messageArgs`, when given, is spread directly into the MESSAGES[code]
  // template instead of the default (column, value) pairing — used by
  // malformed_row, whose message needs (expectedCount, actualCount) rather
  // than a column name.
  function makeIssue(code, rowIndex, column, value, messageArgs) {
    const msgFn = MESSAGES[code];
    let message;
    if (typeof msgFn !== 'function') {
      message = code;
    } else if (messageArgs) {
      message = msgFn(...messageArgs);
    } else {
      message = msgFn(column, value);
    }
    return {
      code,
      severity: SEVERITY[code] || 'warning',
      rowIndex, // 0-based index into data rows; null for header-level issues
      displayRow: rowIndex === null ? null : rowIndex + 2, // header is row 1
      column: column || null,
      value: value === undefined ? null : value,
      message,
    };
  }

  function validateHeader(header, schema) {
    const issues = [];
    const headerSet = new Set(header);
    const schemaNames = new Set(schema.map((c) => c.name));

    schema
      .filter((c) => c.required)
      .forEach((c) => {
        if (!headerSet.has(c.name)) {
          issues.push(makeIssue('missing_required_column', null, c.name));
        }
      });

    header.forEach((h) => {
      if (h && !schemaNames.has(h)) {
        issues.push(makeIssue('unexpected_column', null, h));
      }
    });

    return issues;
  }

  function validateRow(row, rowIndex, header, schema, raggedRowIndices) {
    const issues = [];

    if (raggedRowIndices.includes(rowIndex)) {
      issues.push(
        makeIssue('malformed_row', rowIndex, null, row.length, [header.length, row.length])
      );
      return issues; // column alignment untrustworthy — stop here for this row
    }

    const byName = {};
    header.forEach((h, i) => {
      byName[h] = row[i] !== undefined ? row[i] : '';
    });

    schema.forEach((col) => {
      if (!(col.name in byName)) return; // header already flagged as missing
      const rawValue = byName[col.name];
      const value = rawValue === undefined ? '' : rawValue;

      if (value === '') {
        if (col.required) {
          issues.push(makeIssue('missing_required_value', rowIndex, col.name));
        }
        return;
      }

      if (REPLACEMENT_CHAR_RE.test(value)) {
        issues.push(makeIssue('encoding_replacement_char', rowIndex, col.name, value));
      } else if (MOJIBAKE_RE.test(value)) {
        issues.push(makeIssue('encoding_mojibake', rowIndex, col.name, value));
      }
      if (CONTROL_CHAR_RE.test(value)) {
        issues.push(makeIssue('encoding_control_char', rowIndex, col.name, value));
      }
      if (value !== value.trim()) {
        issues.push(makeIssue('whitespace', rowIndex, col.name, value));
      }

      const typeIssue = checkType(col, value);
      if (typeIssue) {
        issues.push(makeIssue(typeIssue, rowIndex, col.name, value));
      }
    });

    return issues;
  }

  // Full-file validation. Returns:
  // {
  //   headerIssues, rowIssues: [...],
  //   rowSeverity: Map<rowIndex, 'error'|'warning'|null>,
  //   summary: { totalRows, validRows, errorRows, warningRows, byCode: {code: count} }
  // }
  function validateFile(parsed, schema) {
    const { header, rows, raggedRowIndices } = parsed;
    const headerIssues = validateHeader(header, schema);
    const rowIssues = [];
    const rowSeverity = new Array(rows.length).fill(null);

    rows.forEach((row, idx) => {
      const issues = validateRow(row, idx, header, schema, raggedRowIndices);
      rowIssues.push(...issues);
      if (issues.some((i) => i.severity === 'error')) {
        rowSeverity[idx] = 'error';
      } else if (issues.some((i) => i.severity === 'warning')) {
        rowSeverity[idx] = 'warning';
      }
    });

    const errorRows = rowSeverity.filter((s) => s === 'error').length;
    const warningRows = rowSeverity.filter((s) => s === 'warning').length;
    const validRows = rows.length - errorRows - warningRows;

    const byCode = {};
    [...headerIssues, ...rowIssues].forEach((issue) => {
      byCode[issue.code] = (byCode[issue.code] || 0) + 1;
    });

    return {
      headerIssues,
      rowIssues,
      rowSeverity,
      summary: {
        totalRows: rows.length,
        validRows,
        errorRows,
        warningRows,
        byCode,
      },
    };
  }

  const Validator = {
    isValidUrl,
    isValidDate,
    checkType,
    validateHeader,
    validateRow,
    validateFile,
    MESSAGES,
    SEVERITY,
  };

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = Validator;
  } else {
    global.Validator = Validator;
  }
})(typeof window !== 'undefined' ? window : globalThis);
