// From-scratch RFC 4180-style CSV parser. No third-party dependency: the whole
// point of this tool is to be self-contained and trustworthy for sensitive
// business data, so the parsing logic must be auditable in one file.
//
// Handles: quoted fields, embedded commas/newlines inside quotes, escaped ""
// quotes, CRLF and LF line endings, a leading UTF-8 BOM, and ragged rows
// (field count mismatched against the header) which are reported as parse
// issues rather than silently dropped or padded.

(function (global) {
  'use strict';

  const BOM = '﻿';

  // Tokenizes raw CSV text into an array of rows, each row an array of
  // string fields. Does not interpret a header row — that is the caller's
  // job. Ragged rows are still returned (never dropped) so validation can
  // report on them; `meta.raggedRows` lists their 0-based row indices.
  function tokenize(text) {
    const rows = [];
    let i = 0;
    const n = text.length;
    let field = '';
    let row = [];
    let inQuotes = false;
    let sawAnyContent = false;

    function endField() {
      row.push(field);
      field = '';
    }
    function endRow() {
      endField();
      rows.push(row);
      row = [];
    }

    while (i < n) {
      const ch = text[i];

      if (inQuotes) {
        if (ch === '"') {
          if (text[i + 1] === '"') {
            field += '"';
            i += 2;
            continue;
          }
          inQuotes = false;
          i += 1;
          continue;
        }
        field += ch;
        i += 1;
        continue;
      }

      if (ch === '"' && field === '') {
        inQuotes = true;
        sawAnyContent = true;
        i += 1;
        continue;
      }
      if (ch === ',') {
        sawAnyContent = true;
        endField();
        i += 1;
        continue;
      }
      if (ch === '\r') {
        // Treat CRLF and lone CR as one line break.
        sawAnyContent = true;
        endRow();
        i += text[i + 1] === '\n' ? 2 : 1;
        continue;
      }
      if (ch === '\n') {
        sawAnyContent = true;
        endRow();
        i += 1;
        continue;
      }
      sawAnyContent = true;
      field += ch;
      i += 1;
    }

    // Reaching EOF while still inside a quoted field means the file is
    // truncated mid-value (e.g. `name\n"unterminated`) — record that so the
    // caller can flag the affected row rather than silently accepting the
    // partial value as if the quote had closed cleanly.
    const unterminatedQuote = inQuotes;

    // Flush a trailing field/row unless the file ended cleanly on a newline
    // (in which case there is nothing left to flush) or the file was empty.
    if (field !== '' || row.length > 0) {
      endRow();
    }
    if (!sawAnyContent) {
      return { rows: [], unterminatedQuote: false };
    }
    return { rows, unterminatedQuote };
  }

  // Parses raw CSV text (already decoded to a JS string) into
  // { header: string[], rows: string[][], raggedRowIndices: number[] }.
  // `rows` excludes the header row. Row indices in raggedRowIndices are
  // 0-based positions within `rows` (not counting the header).
  function parseCSV(text) {
    let cleaned = text;
    if (cleaned.length > 0 && cleaned[0] === BOM) {
      cleaned = cleaned.slice(1);
    }

    const tokenized = tokenize(cleaned);
    const allRows = tokenized.rows.filter((r) => !(r.length === 1 && r[0] === ''));

    if (allRows.length === 0) {
      return { header: [], rows: [], raggedRowIndices: [] };
    }

    const header = allRows[0].map((h) => h.trim());
    const dataRows = allRows.slice(1);
    const raggedRowIndices = [];
    dataRows.forEach((r, idx) => {
      if (r.length !== header.length) {
        raggedRowIndices.push(idx);
      }
    });

    // An unterminated quote can only have affected the very last row
    // emitted (everything after the opening quote — including any embedded
    // newlines — was consumed as one field up to EOF).
    if (tokenized.unterminatedQuote && dataRows.length > 0) {
      const lastIdx = dataRows.length - 1;
      if (!raggedRowIndices.includes(lastIdx)) {
        raggedRowIndices.push(lastIdx);
      }
    }

    return { header, rows: dataRows, raggedRowIndices };
  }

  const CsvParser = { parseCSV, tokenize, BOM };

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = CsvParser;
  } else {
    global.CsvParser = CsvParser;
  }
})(typeof window !== 'undefined' ? window : globalThis);
