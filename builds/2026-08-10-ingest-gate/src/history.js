// Run history: aggregate-only record of past validation runs, so the
// operator can see data-quality trend across repeated ingestion attempts.
// Deliberately never stores raw row content — only counts and a filename —
// so history persists safely even for files containing business-sensitive
// data.

(function (global) {
  'use strict';

  const STORAGE_KEY = 'ingestgate_history_v1';
  const MAX_ENTRIES = 200;

  function loadHistory(storage) {
    const store = storage || global.localStorage;
    if (!store) return [];
    try {
      const raw = store.getItem(STORAGE_KEY);
      if (!raw) return [];
      const parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed : [];
    } catch (err) {
      return [];
    }
  }

  function saveHistory(entries, storage) {
    const store = storage || global.localStorage;
    if (!store) return;
    store.setItem(STORAGE_KEY, JSON.stringify(entries.slice(-MAX_ENTRIES)));
  }

  // Appends one aggregate summary and returns the updated list.
  function recordRun({ fileName, totalRows, validRows, errorRows, warningRows, timestamp }, storage) {
    const entries = loadHistory(storage);
    entries.push({
      timestamp,
      fileName: String(fileName || 'unnamed.csv'),
      totalRows: Number(totalRows) || 0,
      validRows: Number(validRows) || 0,
      errorRows: Number(errorRows) || 0,
      warningRows: Number(warningRows) || 0,
    });
    saveHistory(entries, storage);
    return entries;
  }

  function clearHistory(storage) {
    const store = storage || global.localStorage;
    if (!store) return;
    store.removeItem(STORAGE_KEY);
  }

  const History = { STORAGE_KEY, loadHistory, saveHistory, recordRun, clearHistory };

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = History;
  } else {
    global.History = History;
  }
})(typeof window !== 'undefined' ? window : globalThis);
