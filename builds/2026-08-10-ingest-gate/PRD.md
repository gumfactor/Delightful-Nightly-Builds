# PRD — Ingest Gate: CSV Quality Inspector for The Canada List

> **Build date:** 2026-08-10
> **Category:** F — Data Explorer
> **Complexity:** Ambitious
> **Day of week:** Monday

---

## Goal

A self-contained browser tool that inspects a CSV export before it is ingested into The Canada List's business/product directory pipeline, catching malformed rows, schema violations, encoding problems, and duplicate entries so bad data never reaches the live database.

## User Story

As the operator of The Canada List — a large-scale Canadian business and product directory built from CSV data pulled together by an ongoing curation pipeline — I want to drag a CSV export onto a page and immediately see every row that would break ingestion (missing required fields, malformed structure, duplicate business listings, invalid URLs/emails, encoding corruption), so that I can fix or discard bad rows before they pollute the live directory, without writing a one-off validation script every time the schema shifts.

## Scope

### In Scope
- Drag-and-drop / file-picker CSV upload, parsed entirely client-side (no data ever leaves the browser except the optional aggregate-only AI briefing)
- From-scratch RFC 4180-style CSV parser handling quoted fields, embedded commas/newlines, escaped `""` quotes, CRLF/LF, and a UTF-8 BOM
- Configurable schema editor (column name, required flag, type: text/url/email/number/date/enum, enum value list, unique/dedupe-key flag) — persisted to `localStorage`, exportable/importable as JSON, with a "load columns from this file's header" helper and a "reset to Canada-List-style default preset" button
- Validation engine producing per-row, per-column issues at two severities:
  - **Error** (blocking): missing required column in header, missing required value, malformed row (field count mismatch against header), invalid type/format (bad URL, bad email, non-numeric, non-ISO-date, enum value not in whitelist)
  - **Warning** (non-blocking): leading/trailing whitespace, unexpected/unmapped column present in the file, possible mojibake/encoding corruption heuristic
- Duplicate detection: exact full-row duplicates, plus per-unique-column key duplicates (normalized: trimmed, case-folded, and for URL columns protocol/trailing-slash-stripped)
- Encoding handling: file read as raw bytes then decoded via `TextDecoder` with a user-selectable encoding (UTF-8 default, Windows-1252 fallback option); a strict-mode decode pass flags files that are not valid UTF-8
- Results dashboard: summary stat cards (total rows, valid rows, rows with errors, rows with warnings, unique issue types), a searchable/filterable/sortable issues table (all values inserted via `textContent`/`createElement`, never `innerHTML`), and a click-through row detail view
- Two downloads: a cleaned CSV with an appended `QC_Flags` column (mirrors the existing Qualtrics Inspector build's pattern), and a separate issues-only CSV report
- Run History: after each validation run, an aggregate-only summary (filename, timestamp, row/error/warning counts) is appended to a local, persistent history list — never the row content itself — so the operator can see data-quality trend across repeated ingestion attempts
- Optional AI Data Quality Briefing: a direct browser call to the Anthropic Messages API (Claude Haiku, session-only key typed into the page, never persisted) that receives **only the aggregate counts** (never a single raw cell value) and returns a one-paragraph plain-English summary of what to fix first; an unconditional deterministic template runs with zero network calls when no key is supplied

### Out of Scope
- Server-side processing or any persistent hosting — this is a static page the user opens locally
- Actually writing to or connecting with The Canada List's live database/pipeline — this is a pre-ingestion QC gate only, entirely decoupled from the real pipeline
- Fuzzy/AI-assisted near-duplicate matching (e.g. "Tim Hortons" vs "Tim Horton's") — flagged in FutureFeatures.md; tonight's dedupe is exact-normalized-key only, which is deterministic and needs no API key
- Multi-file batch comparison across two different CSV exports (diffing) — single-file inspection only tonight

## Tech Stack

- **Language:** Vanilla HTML/CSS/JS (classic scripts, no ES modules, so `index.html` opens directly via `file://`)
- **Framework:** None
- **Dependencies:** `@playwright/test` (dev/test only, via npm); zero runtime dependencies, zero CDN imports
- **Runtime requirement:** Open `index.html` directly in any modern browser — no build step, no install needed for normal use

## Data Structure

Two persisted `localStorage` keys, both scoped to the page's origin:

- `ingestgate_schema_v1` — JSON array of column definitions:
  ```json
  [{"name": "business_name", "required": true, "type": "text", "unique": true, "enumValues": []}, ...]
  ```
- `ingestgate_history_v1` — JSON array of aggregate-only run summaries (never raw row data):
  ```json
  [{"timestamp": "2026-08-10T09:00:00.000Z", "fileName": "export.csv", "totalRows": 412, "validRows": 388, "errorRows": 18, "warningRows": 24}]
  ```

Uploaded CSV content lives only in page memory for the duration of the session; it is never written to `localStorage` or sent anywhere except the optional aggregate-only AI call.

## Folder Structure

```
builds/2026-08-10-ingest-gate/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── package.json
├── package-lock.json
├── playwright.config.js
├── index.html
├── src/
│   ├── styles.css
│   ├── csv-parser.js       (from-scratch CSV tokenizer/parser)
│   ├── schema.js            (default preset, schema load/save/import/export)
│   ├── validator.js         (header + per-row + type validation engine)
│   ├── dedupe.js             (exact-row and unique-key duplicate detection)
│   ├── report.js             (builds cleaned CSV / issues CSV / QC_Flags text)
│   ├── ai-briefing.js        (optional direct-browser Anthropic call + deterministic fallback)
│   ├── history.js            (localStorage run-history read/write)
│   └── app.js                (DOM wiring: upload, tabs, table render, events)
└── tests/
    └── ingest-gate.spec.js
```

## Testing Strategy

- **Framework:** Playwright (`@playwright/test`)
- **Test file location:** `tests/ingest-gate.spec.js`
- **Run command:** `npx playwright test`
- **What will be tested:**
  - CSV parser: simple rows, quoted commas, quoted embedded newlines, escaped `""` quotes, BOM stripping, ragged rows (too few / too many fields)
  - Schema validation: missing required column, missing required value, invalid URL/email/number/date, enum whitelist violation
  - Duplicate detection: exact duplicate row, normalized unique-key duplicate (case/whitespace/protocol-insensitive)
  - Encoding: control-character detection, invalid-UTF-8 strict-decode detection
  - Summary counts: total/valid/error/warning rows computed correctly against a known fixture
  - Cleaned-CSV / issues-CSV export: `QC_Flags` column content correctness
  - UI: file upload renders the dashboard; search/filter narrows the issues table; schema editor add/remove column changes validation on re-run
  - Security: an XSS payload in a CSV cell renders as inert escaped text in the issues table and row detail view (zero dialogs, zero injected DOM)
  - AI: with no API key, the briefing uses the deterministic template and makes zero network requests (verified via a blocked/aborted route); with a mocked successful Anthropic response, the briefing text is displayed; with a mocked failure, it falls back to the template
  - History: a completed run appends one aggregate-only entry that persists across reload, and never contains raw row values

## Success Criteria

1. All tests pass (zero failures)
2. Uploading a CSV with known seeded errors (malformed row, missing required value, bad URL, duplicate business name, invalid enum) surfaces every one of those issues in the dashboard with correct row/column attribution
3. A clean, fully-valid CSV produces zero errors/warnings and a summary showing 100% valid rows
4. The cleaned-CSV download contains a `QC_Flags` column that is empty for valid rows and lists the specific issue codes for flagged rows
5. No CSV row content is ever sent over the network — verified by asserting the AI briefing request body contains only aggregate counts, never a cell value, and that zero network calls occur with no API key set

---

## Scope Changes

_None — full scope as planned above was delivered._
