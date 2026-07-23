# PRD — Canada List CSV Quality Inspector

## Goal

Catch structural, format, encoding, and duplicate-entry problems in a business/product directory CSV *before* it is ingested into The Canada List catalog, and hand back a cleaned CSV plus a reviewable report so bad rows never reach the live site.

## User Story

As the operator of The Canada List's data pipeline, I regularly receive or generate CSV batches of Canadian business/product listings (from manual research, partner submissions, or scraped sources) that need to go into the catalog. I need a tool that runs against any such CSV, tells me exactly which rows are broken or duplicated and why, gives me a clear keep/review/drop recommendation per row, and gives me back a corrected CSV I can safely load — without me having to eyeball hundreds of rows by hand.

## Scope

### In scope
- CLI tool (run from the build folder root): `python -m src.main <input.csv> [--schema config.json] [--out-dir DIR] [--no-ai]`
- Structural validation: empty file, missing/empty header, ragged rows (column count mismatch), duplicate column headers
- Required-field completeness checks against a configurable schema, with sensible defaults for a business-directory CSV (`business_name`, `category`, `province`, `website` required by default)
- Format validation: website URL syntax, Canadian province/territory code or name (13 canonical values + common aliases), ownership percentage (0–100 numeric, if column present), ownership status against a canonical set (if column present), email syntax (if column present)
- Encoding validation: non-UTF-8 byte sequences, BOM detection, replacement-character (mojibake) detection, disallowed control characters in field values
- Exact duplicate row detection
- Near-duplicate detection: normalized-name similarity (legal-suffix stripping + `difflib.SequenceMatcher`) clustered with same-province or same-website-domain corroboration
- Optional AI enrichment via `ANTHROPIC_API_KEY` (Claude Haiku, called directly over `urllib`, never in tests): confirms/denies near-duplicate clusters with one-sentence reasoning, and suggests a canonical mapping for unrecognized `ownership_status` values. Fully functional deterministic fallback when no key is set.
- Per-row `QC_Flags` (semicolon-separated) and `Recommended_Action` (`keep` / `review` / `drop`) computed from severity (error/warning) of accumulated flags
- Four output modes, all generated every run: colored terminal summary (degrades gracefully when not a TTY), JSON report, self-contained dark-mode HTML dashboard (stat tiles, Chart.js 4.4.4 pinned CDN bar chart with a text-table fallback if the CDN is unreachable, sortable/searchable/filterable row table, duplicate-cluster viewer), cleaned CSV with the two new columns appended
- Configurable schema via an optional `--schema config.json` (required columns, canonical ownership-status values) so the tool isn't hardwired to one exact export format
- Synthetic sample CSV fixture (`tests/fixtures/sample_directory.csv`) with fabricated business names — no real personal or business data

### Out of scope
- Actually writing to The Canada List's live database or any external ingestion API — this tool only inspects a CSV and produces reviewable output files
- Fuzzy matching against an existing "already in the catalog" master list (no such export is available in the build environment) — this build only catches duplicates *within* the batch being checked
- A browser-based upload/drag-drop interface — this is a CLI that renders a static HTML report, not a live web app (the 2026-06-06 backlog note explicitly questioned why a browser+Playwright shell was needed for what is fundamentally a data-processing task; this build follows the proven pattern from the 2026-06-17 Qualtrics Survey Data Inspector instead: Python core logic, self-contained HTML report as the visual layer)
- Address/postal-code geocoding validation (no free geocoding API is listed in PROFILE.md's Data Sources)

## Tech Stack

- Python 3, standard library only (`csv`, `json`, `re`, `difflib`, `unicodedata`, `urllib.request`, `urllib.parse`, `dataclasses`, `argparse`) — no third-party dependencies required, so `requirements.txt` is intentionally empty
- Optional runtime dependency: `ANTHROPIC_API_KEY` environment variable for the AI enrichment layer (Claude Haiku, `claude-haiku-4-5-20251001`, called via `urllib.request` — no `anthropic` SDK needed)
- Chart.js 4.4.4 via pinned CDN URL in the generated HTML, with an inline text-table fallback if the CDN fails to load
- pytest for the test suite

## Data Structure

**Input:** any CSV with a header row. Column names are matched case-insensitively against the schema; unmapped columns are passed through untouched.

**Default schema** (overridable via `--schema`):
```json
{
  "required_columns": ["business_name", "category", "province", "website"],
  "ownership_status_values": ["canadian-owned", "foreign-owned", "unknown"]
}
```

**Internal row record:** `{row_index, raw_fields: dict, flags: [{code, severity, message}], recommended_action}`

**Duplicate cluster record:** `{cluster_id, row_indices: [...], match_basis, similarity_score, ai_confirmed: bool|None, ai_reasoning: str|None}`

**Report JSON top-level shape:** `{summary: {...}, rows: [...], duplicate_clusters: [...], generated_with_ai: bool}`

## Folder Structure

```
builds/2026-07-23-canada-list-csv-quality-inspector/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── schema.py            # default schema, canonical province/ownership lists
│   ├── qc_engine.py         # structural, required-field, format, encoding checks
│   ├── duplicates.py        # exact + near-duplicate clustering
│   ├── ai_enrichment.py     # optional Claude Haiku calls via urllib, deterministic fallback
│   ├── report_html.py       # self-contained dark-mode HTML dashboard renderer
│   └── main.py              # CLI entry point: orchestrates the above, writes all 4 outputs
└── tests/
    ├── __init__.py
    ├── fixtures/
    │   └── sample_directory.csv   # synthetic business-directory CSV with seeded issues
    ├── test_schema.py
    ├── test_qc_engine.py
    ├── test_duplicates.py
    ├── test_ai_enrichment.py
    ├── test_report_html.py
    └── test_main_integration.py
```

## Testing Strategy

- `pytest`, tests live in `tests/`, run via `python -m pytest tests/ -v`
- Every external network call (Anthropic API) is mocked with `unittest.mock.patch` on the `urllib.request.urlopen` call inside `ai_enrichment.py` — no live API calls in any test, and tests must pass with `ANTHROPIC_API_KEY` unset
- `test_schema.py`: default schema shape, province alias normalization
- `test_qc_engine.py`: happy-path clean row, missing required field, ragged row, empty file, duplicate headers, invalid website, invalid province, out-of-range ownership percentage, unmapped ownership status, invalid email, non-UTF-8 byte sequence, BOM detection, control-character detection, `Recommended_Action` derivation (keep/review/drop) for each severity combination
- `test_duplicates.py`: exact duplicate rows detected, near-duplicate by normalized name + legal-suffix stripping, near-duplicate corroborated by same province, no false-positive cluster for genuinely distinct businesses with similar-but-different names
- `test_ai_enrichment.py`: AI path returns a parsed confirmation when key is set and API call is mocked, deterministic fallback path when no key is set, malformed/error API response falls back gracefully without crashing
- `test_report_html.py`: HTML output is valid self-contained HTML, contains no unescaped raw field text (script-injection payload in a business name is neutralized — inserted via safe DOM APIs, not `innerHTML` string concatenation), Chart.js CDN URL is pinned to an exact version
- `test_main_integration.py`: end-to-end run against `tests/fixtures/sample_directory.csv` produces all 4 output artifacts with the expected row counts, flag counts, and cluster count
- Minimum 15 tests, target ~25+, all must pass with zero failures before commit

## Success Criteria

1. Running the CLI against the synthetic fixture CSV correctly flags every seeded issue type (missing required field, ragged row, invalid province, invalid website, out-of-range ownership percentage, unmapped ownership status, exact duplicate, near-duplicate) with zero false negatives on the seeded cases.
2. The generated HTML dashboard opens directly in a browser with no build step, renders the stat tiles, issue chart (or its text fallback), sortable/filterable row table, and duplicate-cluster viewer correctly, and is verified live in headless Chromium to be immune to script injection via a malicious business name in the fixture.
3. The cleaned output CSV preserves every original column and value, and adds correct `QC_Flags` and `Recommended_Action` values for every row.
4. The tool runs to completion and produces correct, non-AI (deterministic-fallback) output with `ANTHROPIC_API_KEY` unset, and the AI-enrichment code path is exercised and passes with the Anthropic call mocked.
5. All tests pass (`python -m pytest tests/ -v`, 0 failures) and the STANDARDS.md security checklist passes against every file created tonight.

## Idea Brief Traceability

No linked Idea Brief exists for backlog idea #1 ("The Canada List CSV Quality Inspector") — it is a plain backlog row, not a briefed idea. This PRD is the full specification.

## Scope Changes

None — full scope as planned was delivered.
