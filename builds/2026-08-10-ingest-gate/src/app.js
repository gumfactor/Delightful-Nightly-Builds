// DOM wiring for Ingest Gate. Depends on CsvParser, Schema, Validator,
// Dedupe, Report, AiBriefing, History (all attached to `window` by their
// respective classic-script files, loaded before this one).

(function () {
  'use strict';

  const state = {
    parsed: null,
    schema: [],
    headerIssues: [],
    rowIssues: [],
    dedupeIssues: [],
    summary: null,
    fileName: null,
    searchTerm: '',
    severityFilter: 'all',
    sortKey: 'displayRow',
    sortDir: 'asc',
  };

  function $(id) {
    return document.getElementById(id);
  }

  // ---------- Tabs ----------
  function initTabs() {
    document.querySelectorAll('.tab-btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.tab-btn').forEach((b) => {
          b.classList.remove('active');
          b.setAttribute('aria-selected', 'false');
        });
        btn.classList.add('active');
        btn.setAttribute('aria-selected', 'true');

        document.querySelectorAll('.panel').forEach((p) => p.classList.add('hidden-panel'));
        $('panel-' + btn.dataset.tab).classList.remove('hidden-panel');
      });
    });
  }

  // ---------- File upload & encoding ----------
  async function readFileWithEncoding(file, encodingLabel) {
    const buffer = await file.arrayBuffer();
    let utf8Valid = true;
    try {
      new TextDecoder('utf-8', { fatal: true }).decode(buffer);
    } catch (err) {
      utf8Valid = false;
    }
    const text = new TextDecoder(encodingLabel, { fatal: false }).decode(buffer);
    return { text, utf8Valid };
  }

  async function handleFile(file) {
    state.currentFile = file;
    state.fileName = file.name;
    $('file-status').textContent = 'Reading ' + file.name + '…';

    const encodingLabel = $('encoding-select').value;
    const { text, utf8Valid } = await readFileWithEncoding(file, encodingLabel);

    const warningEl = $('encoding-warning');
    if (encodingLabel === 'utf-8' && !utf8Valid) {
      warningEl.textContent =
        'This file does not decode cleanly as UTF-8 — some characters may be shown as replacement characters (�). Try switching the encoding dropdown to Windows-1252 and re-uploading.';
      warningEl.hidden = false;
    } else {
      warningEl.hidden = true;
    }

    state.parsed = window.CsvParser.parseCSV(text);
    state.schema = window.Schema.loadSchema();
    const validation = window.Validator.validateFile(state.parsed, state.schema);
    state.headerIssues = validation.headerIssues;
    state.rowIssues = validation.rowIssues;
    state.dedupeIssues = window.Dedupe.findDuplicates(state.parsed, state.schema);

    // Recompute combined per-row severity from scratch (validator severity,
    // upgraded to 'error' by any duplicate finding) rather than patching the
    // validator's totals with a delta — a row can move warning->error, which
    // a simple valid-count decrement would get wrong.
    const combinedSeverity = validation.rowSeverity.slice();
    state.dedupeIssues.forEach((issue) => {
      combinedSeverity[issue.rowIndex] = 'error';
    });
    const errorRows = combinedSeverity.filter((s) => s === 'error').length;
    const warningRows = combinedSeverity.filter((s) => s === 'warning').length;
    const validRows = combinedSeverity.length - errorRows - warningRows;

    const byCode = { ...validation.summary.byCode };
    state.dedupeIssues.forEach((i) => {
      byCode[i.code] = (byCode[i.code] || 0) + 1;
    });

    state.summary = {
      totalRows: validation.summary.totalRows,
      validRows,
      errorRows,
      warningRows,
      byCode,
    };

    $('file-status').textContent =
      'Loaded ' + file.name + ' — ' + state.parsed.rows.length + ' data row(s).';

    window.History.recordRun({
      fileName: file.name,
      totalRows: state.summary.totalRows,
      validRows: state.summary.validRows,
      errorRows: state.summary.errorRows,
      warningRows: state.summary.warningRows,
      timestamp: new Date().toISOString(),
    });
    renderHistory();

    $('results').hidden = false;
    $('ai-briefing-output').textContent = '';
    renderSummary();
    renderIssuesTable();
    $('row-detail').hidden = true;
  }

  function initUpload() {
    const dropZone = $('drop-zone');
    const fileInput = $('file-input');

    dropZone.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', () => {
      if (fileInput.files[0]) handleFile(fileInput.files[0]);
    });

    dropZone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropZone.classList.add('drag-over');
    });
    dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
    dropZone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropZone.classList.remove('drag-over');
      if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]);
    });

    // Re-decode and re-validate the already-uploaded file when the operator
    // switches encodings — otherwise the recovery path the warning banner
    // recommends ("switch to Windows-1252") silently does nothing.
    $('encoding-select').addEventListener('change', () => {
      if (state.currentFile) handleFile(state.currentFile);
    });
  }

  // ---------- Summary cards ----------
  function renderSummary() {
    $('stat-total').textContent = String(state.summary.totalRows);
    $('stat-valid').textContent = String(state.summary.validRows);
    $('stat-errors').textContent = String(state.summary.errorRows);
    $('stat-warnings').textContent = String(state.summary.warningRows);
  }

  // ---------- Issues table ----------
  function allIssues() {
    return [...state.headerIssues, ...state.rowIssues, ...state.dedupeIssues];
  }

  function filteredSortedIssues() {
    const term = state.searchTerm.trim().toLowerCase();
    let issues = allIssues().filter((issue) => {
      if (state.severityFilter !== 'all' && issue.severity !== state.severityFilter) return false;
      if (!term) return true;
      const haystack = [issue.column, issue.code, issue.message, issue.value]
        .filter((v) => v !== null && v !== undefined)
        .join(' ')
        .toLowerCase();
      return haystack.includes(term);
    });

    const key = state.sortKey;
    const dir = state.sortDir === 'asc' ? 1 : -1;
    issues = issues.slice().sort((a, b) => {
      const av = a[key] === null || a[key] === undefined ? '' : a[key];
      const bv = b[key] === null || b[key] === undefined ? '' : b[key];
      if (av < bv) return -1 * dir;
      if (av > bv) return 1 * dir;
      return 0;
    });
    return issues;
  }

  function renderIssuesTable() {
    const tbody = $('issues-tbody');
    tbody.innerHTML = '';
    const issues = filteredSortedIssues();

    $('issues-empty').hidden = issues.length !== 0;

    issues.forEach((issue) => {
      const tr = document.createElement('tr');
      tr.className = 'severity-' + issue.severity;
      tr.dataset.testid = 'issue-row';

      const rowCell = document.createElement('td');
      if (issue.displayRow === null || issue.displayRow === undefined) {
        rowCell.textContent = 'header';
      } else {
        const link = document.createElement('button');
        link.className = 'row-link';
        link.textContent = String(issue.displayRow);
        link.dataset.testid = 'row-link';
        link.addEventListener('click', () => showRowDetail(issue.rowIndex));
        rowCell.appendChild(link);
      }
      tr.appendChild(rowCell);

      const colCell = document.createElement('td');
      colCell.textContent = issue.column || '';
      tr.appendChild(colCell);

      const sevCell = document.createElement('td');
      sevCell.textContent = issue.severity;
      tr.appendChild(sevCell);

      const codeCell = document.createElement('td');
      codeCell.textContent = issue.code;
      tr.appendChild(codeCell);

      const msgCell = document.createElement('td');
      msgCell.textContent = issue.message;
      tr.appendChild(msgCell);

      tbody.appendChild(tr);
    });
  }

  function showRowDetail(rowIndex) {
    if (rowIndex === null || rowIndex === undefined || !state.parsed) return;
    const detail = $('row-detail');
    const content = $('row-detail-content');
    content.innerHTML = '';

    const row = state.parsed.rows[rowIndex] || [];
    const issuesForRow = allIssues().filter((i) => i.rowIndex === rowIndex);
    const flaggedColumns = new Set(issuesForRow.map((i) => i.column).filter(Boolean));

    const dl = document.createElement('dl');
    state.parsed.header.forEach((colName, i) => {
      const dt = document.createElement('dt');
      dt.textContent = colName;
      if (flaggedColumns.has(colName)) dt.classList.add('flagged-col');
      const dd = document.createElement('dd');
      dd.textContent = row[i] !== undefined ? row[i] : '';
      if (flaggedColumns.has(colName)) dd.classList.add('flagged-col');
      dl.appendChild(dt);
      dl.appendChild(dd);
    });
    content.appendChild(dl);
    detail.hidden = false;
  }

  function initIssueControls() {
    $('search-input').addEventListener('input', (e) => {
      state.searchTerm = e.target.value;
      renderIssuesTable();
    });

    document.querySelectorAll('.chip').forEach((chip) => {
      chip.addEventListener('click', () => {
        document.querySelectorAll('.chip').forEach((c) => c.classList.remove('active'));
        chip.classList.add('active');
        state.severityFilter = chip.dataset.severity;
        renderIssuesTable();
      });
    });

    document.querySelectorAll('.issues-table th[data-sort]').forEach((th) => {
      th.addEventListener('click', () => {
        const key = th.dataset.sort;
        if (state.sortKey === key) {
          state.sortDir = state.sortDir === 'asc' ? 'desc' : 'asc';
        } else {
          state.sortKey = key;
          state.sortDir = 'asc';
        }
        renderIssuesTable();
      });
    });
  }

  // ---------- Downloads ----------
  function triggerDownload(filename, text, mime) {
    const blob = new Blob([text], { type: mime || 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  function getCleanedCsvText() {
    if (!state.parsed) return '';
    return window.Report.buildCleanedCsv(state.parsed, state.rowIssues, state.dedupeIssues);
  }

  function getIssuesCsvText() {
    return window.Report.buildIssuesCsv(state.headerIssues, state.rowIssues, state.dedupeIssues);
  }

  function initDownloads() {
    $('download-cleaned').addEventListener('click', () => {
      if (!state.parsed) return;
      const base = (state.fileName || 'data.csv').replace(/\.csv$/i, '');
      triggerDownload(base + '_cleaned.csv', getCleanedCsvText());
    });
    $('download-issues').addEventListener('click', () => {
      if (!state.parsed) return;
      const base = (state.fileName || 'data.csv').replace(/\.csv$/i, '');
      triggerDownload(base + '_issues.csv', getIssuesCsvText());
    });
  }

  // ---------- AI briefing ----------
  function initAiBriefing() {
    $('ai-briefing-btn').addEventListener('click', async () => {
      if (!state.summary) return;
      const apiKey = $('ai-key-input').value.trim();
      const outputEl = $('ai-briefing-output');
      outputEl.textContent = 'Generating briefing…';
      const result = await window.AiBriefing.generateBriefing(state.summary, apiKey || null);
      outputEl.textContent = result.text;
    });
  }

  // ---------- Schema tab ----------
  function renderSchemaTable() {
    const tbody = $('schema-tbody');
    tbody.innerHTML = '';

    state.schema.forEach((col, idx) => {
      const tr = document.createElement('tr');
      tr.dataset.testid = 'schema-row';

      const nameCell = document.createElement('td');
      const nameInput = document.createElement('input');
      nameInput.type = 'text';
      nameInput.value = col.name;
      nameInput.dataset.testid = 'schema-name-' + idx;
      nameInput.addEventListener('change', () => {
        state.schema[idx].name = nameInput.value;
        persistSchema();
      });
      nameCell.appendChild(nameInput);
      tr.appendChild(nameCell);

      const reqCell = document.createElement('td');
      const reqInput = document.createElement('input');
      reqInput.type = 'checkbox';
      reqInput.checked = col.required;
      reqInput.dataset.testid = 'schema-required-' + idx;
      reqInput.addEventListener('change', () => {
        state.schema[idx].required = reqInput.checked;
        persistSchema();
      });
      reqCell.appendChild(reqInput);
      tr.appendChild(reqCell);

      const typeCell = document.createElement('td');
      const typeSelect = document.createElement('select');
      typeSelect.dataset.testid = 'schema-type-' + idx;
      window.Schema.VALID_TYPES.forEach((t) => {
        const opt = document.createElement('option');
        opt.value = t;
        opt.textContent = t;
        if (t === col.type) opt.selected = true;
        typeSelect.appendChild(opt);
      });
      typeSelect.addEventListener('change', () => {
        state.schema[idx].type = typeSelect.value;
        persistSchema();
        renderSchemaTable();
      });
      typeCell.appendChild(typeSelect);
      tr.appendChild(typeCell);

      const enumCell = document.createElement('td');
      const enumInput = document.createElement('input');
      enumInput.type = 'text';
      enumInput.placeholder = 'comma-separated values';
      enumInput.value = col.enumValues.join(', ');
      enumInput.disabled = col.type !== 'enum';
      enumInput.dataset.testid = 'schema-enum-' + idx;
      enumInput.addEventListener('change', () => {
        state.schema[idx].enumValues = enumInput.value
          .split(',')
          .map((v) => v.trim())
          .filter(Boolean);
        persistSchema();
      });
      enumCell.appendChild(enumInput);
      tr.appendChild(enumCell);

      const uniqCell = document.createElement('td');
      const uniqInput = document.createElement('input');
      uniqInput.type = 'checkbox';
      uniqInput.checked = col.unique;
      uniqInput.dataset.testid = 'schema-unique-' + idx;
      uniqInput.addEventListener('change', () => {
        state.schema[idx].unique = uniqInput.checked;
        persistSchema();
      });
      uniqCell.appendChild(uniqInput);
      tr.appendChild(uniqCell);

      const removeCell = document.createElement('td');
      const removeBtn = document.createElement('button');
      removeBtn.textContent = 'Remove';
      removeBtn.dataset.testid = 'schema-remove-' + idx;
      removeBtn.addEventListener('click', () => {
        state.schema.splice(idx, 1);
        persistSchema();
        renderSchemaTable();
      });
      removeCell.appendChild(removeBtn);
      tr.appendChild(removeCell);

      tbody.appendChild(tr);
    });
  }

  function persistSchema() {
    window.Schema.saveSchema(state.schema);
  }

  function initSchemaTab() {
    $('schema-add').addEventListener('click', () => {
      state.schema.push({ name: 'new_column', required: false, type: 'text', unique: false, enumValues: [] });
      persistSchema();
      renderSchemaTable();
    });

    $('schema-from-header').addEventListener('click', () => {
      if (!state.parsed || state.parsed.header.length === 0) {
        $('schema-status').textContent = 'Upload a CSV on the Validate tab first.';
        return;
      }
      state.schema = window.Schema.schemaFromHeader(state.parsed.header);
      persistSchema();
      renderSchemaTable();
      $('schema-status').textContent = 'Schema loaded from file header — set required/type/unique as needed.';
    });

    $('schema-reset').addEventListener('click', () => {
      state.schema = window.Schema.defaultPreset();
      persistSchema();
      renderSchemaTable();
      $('schema-status').textContent = 'Schema reset to default preset.';
    });

    $('schema-export').addEventListener('click', () => {
      triggerDownload('ingest-gate-schema.json', window.Schema.exportSchemaJSON(state.schema), 'application/json');
    });

    $('schema-import-btn').addEventListener('click', () => $('schema-import-input').click());
    $('schema-import-input').addEventListener('change', async (e) => {
      const file = e.target.files[0];
      if (!file) return;
      try {
        const text = await file.text();
        state.schema = window.Schema.importSchemaJSON(text);
        persistSchema();
        renderSchemaTable();
        $('schema-status').textContent = 'Schema imported.';
      } catch (err) {
        $('schema-status').textContent = 'Import failed: ' + err.message;
      }
      e.target.value = '';
    });
  }

  // ---------- History tab ----------
  function renderHistory() {
    const entries = window.History.loadHistory();
    const tbody = $('history-tbody');
    tbody.innerHTML = '';
    $('history-empty').hidden = entries.length !== 0;

    entries
      .slice()
      .reverse()
      .forEach((entry) => {
        const tr = document.createElement('tr');
        tr.dataset.testid = 'history-row';
        [
          new Date(entry.timestamp).toLocaleString(),
          entry.fileName,
          entry.totalRows,
          entry.validRows,
          entry.errorRows,
          entry.warningRows,
        ].forEach((val) => {
          const td = document.createElement('td');
          td.textContent = String(val);
          tr.appendChild(td);
        });
        tbody.appendChild(tr);
      });
  }

  function initHistoryTab() {
    $('history-clear').addEventListener('click', () => {
      window.History.clearHistory();
      renderHistory();
    });
  }

  function init() {
    state.schema = window.Schema.loadSchema();
    initTabs();
    initUpload();
    initIssueControls();
    initDownloads();
    initAiBriefing();
    initSchemaTab();
    initHistoryTab();
    renderSchemaTable();
    renderHistory();
  }

  document.addEventListener('DOMContentLoaded', init);

  // Exposed for tests only — not part of the visual UI.
  window.IngestGateApp = { state, getCleanedCsvText, getIssuesCsvText, handleFile, readFileWithEncoding };
})();
