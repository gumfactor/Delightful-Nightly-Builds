# Manual — Canada List CSV Quality Inspector

## What it does

Checks a business/product-directory CSV (the kind of batch you'd load into The Canada List) for the problems that would otherwise slip into the live catalog: rows missing required fields, malformed/ragged rows, bad encoding, invalid province codes or website URLs, out-of-range ownership percentages, unrecognized ownership-status values, and exact or near-duplicate entries. It never touches the live catalog itself — it only reads your CSV and writes report files.

## Requirements

- Python 3.10+ (standard library only — nothing to `pip install` to run the tool itself)
- Optional: set `ANTHROPIC_API_KEY` in your shell environment to enable the AI enrichment layer (Claude Haiku confirms ambiguous near-duplicates and suggests canonical mappings for unrecognized `ownership_status` values). Everything works without it — you just get fewer AI-assisted judgment calls, and every near-duplicate falls back to name-similarity scoring alone.

## Running it

From this build folder's root (so the `src` package resolves correctly):

```bash
python -m src.main path/to/your.csv
```

This writes three files to `./canlist_qc_output/` by default: `report.html` (open this in a browser), `report.json`, and `cleaned.csv`.

### Options

```bash
python -m src.main path/to/your.csv --out-dir ./my_output
python -m src.main path/to/your.csv --schema my_schema.json
python -m src.main path/to/your.csv --no-ai   # skip AI enrichment even if a key is set
```

### Custom schema

By default the tool expects (case-insensitively): `business_name`, `category`, `province`, `website` as required columns, and treats `canadian_ownership_pct`, `ownership_status`, `email` as optional columns it validates *if present*. To override the required-column list or the canonical `ownership_status` values for a different export shape, pass `--schema`:

```json
{
  "required_columns": ["business_name", "category", "province", "website"],
  "ownership_status_values": ["canadian-owned", "foreign-owned", "unknown"]
}
```

## Reading the output

- **`report.html`** — open directly in any browser, no server needed. Stat tiles at the top show total rows and the keep/review/drop split. Below that, a bar chart (or a text table if you're offline / the CDN is blocked) shows issue counts by type. The row table is sortable (click a column header), searchable, and filterable by recommended action. The bottom section shows every detected duplicate cluster with the rows involved side by side.
- **`report.json`** — the same data in machine-readable form, for scripting or feeding into another tool.
- **`cleaned.csv`** — your original CSV, unchanged, with two columns appended: `QC_Flags` (every issue found on that row, semicolon-separated) and `Recommended_Action` (`keep`, `review`, or `drop`). `drop` means at least one hard error (missing required field, invalid province, malformed row, etc.); `review` means only soft warnings (possible duplicate, unmapped category, invalid-looking email/website); `keep` means the row passed every check clean.

Duplicates are always `review`, never auto-`drop` — two rows that look alike (e.g. two franchise locations of the same business) might both be legitimate, so the tool flags them for a human decision rather than guessing.

## Running the tests

```bash
python -m pytest tests/ -v
```

66 tests, stdlib + pytest only. Every Anthropic API call in the test suite is mocked — no network access or API key is needed to run the tests.
