// Builds the two downloadable artifacts: a cleaned CSV (original data plus
// an appended QC_Flags column listing every issue code found on that row)
// and a standalone issues-only CSV report.

(function (global) {
  'use strict';

  function csvEscape(value) {
    const str = String(value === null || value === undefined ? '' : value);
    if (/[",\n\r]/.test(str)) {
      return '"' + str.replace(/"/g, '""') + '"';
    }
    return str;
  }

  function toCsvLine(fields) {
    return fields.map(csvEscape).join(',');
  }

  // Groups row-level issues (validator rowIssues + dedupe issues) by
  // rowIndex, returning a Map<rowIndex, string[]> of unique issue codes.
  function groupIssuesByRow(rowIssues, dedupeIssues) {
    const byRow = new Map();
    [...rowIssues, ...dedupeIssues].forEach((issue) => {
      if (issue.rowIndex === null || issue.rowIndex === undefined) return;
      if (!byRow.has(issue.rowIndex)) byRow.set(issue.rowIndex, []);
      const codes = byRow.get(issue.rowIndex);
      if (!codes.includes(issue.code)) codes.push(issue.code);
    });
    return byRow;
  }

  function buildCleanedCsv(parsed, rowIssues, dedupeIssues) {
    const { header, rows } = parsed;
    const byRow = groupIssuesByRow(rowIssues, dedupeIssues);
    const lines = [toCsvLine([...header, 'QC_Flags'])];

    rows.forEach((row, idx) => {
      const flags = (byRow.get(idx) || []).join(';');
      lines.push(toCsvLine([...row, flags]));
    });

    return lines.join('\r\n') + '\r\n';
  }

  function buildIssuesCsv(headerIssues, rowIssues, dedupeIssues) {
    const lines = [toCsvLine(['Row', 'Column', 'Severity', 'Code', 'Message', 'Value'])];
    const allIssues = [...headerIssues, ...rowIssues, ...dedupeIssues];

    allIssues.forEach((issue) => {
      lines.push(
        toCsvLine([
          issue.displayRow === null || issue.displayRow === undefined ? 'header' : issue.displayRow,
          issue.column || '',
          issue.severity,
          issue.code,
          issue.message,
          issue.value === null || issue.value === undefined ? '' : issue.value,
        ])
      );
    });

    return lines.join('\r\n') + '\r\n';
  }

  const Report = { csvEscape, toCsvLine, groupIssuesByRow, buildCleanedCsv, buildIssuesCsv };

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = Report;
  } else {
    global.Report = Report;
  }
})(typeof window !== 'undefined' ? window : globalThis);
