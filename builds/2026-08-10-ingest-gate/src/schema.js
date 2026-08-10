// Schema definition, default preset, and localStorage persistence for the
// column rules Ingest Gate validates a CSV against. The default preset is a
// generic starting example for a Canadian business/product directory — the
// operator is expected to edit it (via the Schema tab) to match their real
// pipeline's actual column names before relying on it.

(function (global) {
  'use strict';

  const STORAGE_KEY = 'ingestgate_schema_v1';

  const VALID_TYPES = ['text', 'url', 'email', 'number', 'date', 'enum'];

  const CANADIAN_PROVINCES_TERRITORIES = [
    'AB', 'BC', 'MB', 'NB', 'NL', 'NS', 'NT', 'NU', 'ON', 'PE', 'QC', 'SK', 'YT',
  ];

  function defaultPreset() {
    return [
      { name: 'business_name', required: true, type: 'text', unique: true, enumValues: [] },
      { name: 'website', required: true, type: 'url', unique: true, enumValues: [] },
      {
        name: 'category',
        required: true,
        type: 'enum',
        unique: false,
        enumValues: ['Food & Beverage', 'Retail', 'Manufacturing', 'Services', 'Technology', 'Other'],
      },
      {
        name: 'province_territory',
        required: true,
        type: 'enum',
        unique: false,
        enumValues: CANADIAN_PROVINCES_TERRITORIES.slice(),
      },
      { name: 'canadian_ownership_pct', required: false, type: 'number', unique: false, enumValues: [] },
      { name: 'notes', required: false, type: 'text', unique: false, enumValues: [] },
    ];
  }

  function normalizeColumn(col) {
    const type = VALID_TYPES.includes(col.type) ? col.type : 'text';
    return {
      name: String(col.name || '').trim(),
      required: Boolean(col.required),
      type,
      unique: Boolean(col.unique),
      enumValues: Array.isArray(col.enumValues)
        ? col.enumValues.map((v) => String(v).trim()).filter(Boolean)
        : [],
    };
  }

  function validateSchemaShape(schema) {
    if (!Array.isArray(schema)) return false;
    return schema.every(
      (c) => c && typeof c === 'object' && typeof c.name === 'string' && c.name.trim() !== ''
    );
  }

  function loadSchema(storage) {
    const store = storage || global.localStorage;
    if (!store) return defaultPreset();
    try {
      const raw = store.getItem(STORAGE_KEY);
      if (!raw) return defaultPreset();
      const parsed = JSON.parse(raw);
      if (!validateSchemaShape(parsed)) return defaultPreset();
      return parsed.map(normalizeColumn);
    } catch (err) {
      return defaultPreset();
    }
  }

  function saveSchema(schema, storage) {
    const store = storage || global.localStorage;
    if (!store) return;
    const normalized = schema.map(normalizeColumn);
    store.setItem(STORAGE_KEY, JSON.stringify(normalized));
  }

  // Builds a bare schema (all optional, type text, none unique) from a CSV
  // header row — a starting point the operator can then promote fields on.
  function schemaFromHeader(header) {
    return header.map((name) => ({
      name: name.trim(),
      required: false,
      type: 'text',
      unique: false,
      enumValues: [],
    }));
  }

  function exportSchemaJSON(schema) {
    return JSON.stringify(schema.map(normalizeColumn), null, 2);
  }

  function importSchemaJSON(text) {
    const parsed = JSON.parse(text);
    if (!validateSchemaShape(parsed)) {
      throw new Error('Schema JSON must be an array of columns with a non-empty "name" field.');
    }
    return parsed.map(normalizeColumn);
  }

  const Schema = {
    STORAGE_KEY,
    VALID_TYPES,
    CANADIAN_PROVINCES_TERRITORIES,
    defaultPreset,
    normalizeColumn,
    validateSchemaShape,
    loadSchema,
    saveSchema,
    schemaFromHeader,
    exportSchemaJSON,
    importSchemaJSON,
  };

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = Schema;
  } else {
    global.Schema = Schema;
  }
})(typeof window !== 'undefined' ? window : globalThis);
