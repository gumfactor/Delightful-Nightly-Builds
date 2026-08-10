# Manual — Ingest Gate

CSV quality inspector for The Canada List's ingestion pipeline. Runs entirely in your browser — your CSV data never leaves your machine, except the optional AI briefing, which only ever sends aggregate counts (never a row or cell value).

## Opening the tool

Double-click `index.html`, or open it directly in any modern browser (`file:///path/to/builds/2026-08-10-ingest-gate/index.html`). No install, no server, no build step.

## 1. Set up your schema first

Click the **Schema** tab. A generic example schema ships by default (`business_name`, `website`, `category`, `province_territory`, `canadian_ownership_pct`, `notes`) — **edit this to match your real pipeline's actual column names** before relying on the results. For each column you can set:

- **Required** — flags rows with an empty value in this column as an error, and flags the whole file if the column is missing from the header entirely
- **Type** — `text`, `url` (must be `http(s)://…`), `email`, `number`, `date` (`YYYY-MM-DD`), or `enum` (comma-separated allowed values in the next field)
- **Unique / dedupe key** — any column marked unique gets checked for duplicate values (case/whitespace-insensitive; for `url` columns, protocol and trailing slash are also ignored, so `https://Example.com/` and `www.example.com` are correctly caught as the same value)

Useful shortcuts:
- **Load Columns From Uploaded File's Header** (after uploading a CSV on the Validate tab) — seeds the schema from the file's actual header row as a starting point, all optional/text, so you can promote fields from there
- **Reset to Default Preset** — back to the shipped example
- **Export / Import Schema (JSON)** — save your schema to a file so you can reuse it on another machine or share it with a teammate

Your schema is saved automatically to this browser's local storage — it persists across sessions on this machine, but is not synced anywhere.

## 2. Validate a file

Go to the **Validate** tab, drag a CSV onto the drop zone (or click it to browse). If your export isn't UTF-8 (e.g. it came out of Excel on Windows), switch the **File encoding** dropdown to Windows-1252 before or after upload — a warning banner appears automatically if the file doesn't decode cleanly as UTF-8.

You'll see:
- **Summary cards** — total rows, valid rows, rows with blocking errors, rows with non-blocking warnings
- **AI Data Quality Briefing** (optional) — paste an Anthropic API key (never saved, cleared when you close the tab) and click **Get Briefing** for a one-paragraph plain-English summary of what to fix first. Leave the key blank and click the button anyway — you still get a useful rule-based summary, with zero network calls.
- **Issues table** — every problem found, one row per issue. Click a **row number** to see the full row with the offending column(s) highlighted. Use the search box or the All/Errors/Warnings chips to narrow it down. Click a column header to sort.
- **Downloads** — **Cleaned CSV** (your original data plus a `QC_Flags` column listing the issue codes found on each row, empty for clean rows) and **Issues Report CSV** (one line per issue, for pasting into a ticket or spreadsheet).

### What counts as an error vs. a warning

| Error (blocks a row from being "valid") | Warning (flagged, non-blocking) |
|---|---|
| Missing required column in the header | Unexpected column not in your schema |
| Empty required value | Leading/trailing whitespace |
| Malformed row (wrong field count) | Possible mojibake (mis-decoded text) |
| Invalid URL / email / number / date / enum value | |
| Duplicate row or duplicate unique-key value | |
| Unicode replacement character present (likely encoding corruption) | |

## 3. Check the History tab

Every completed run adds one line (filename, timestamp, total/valid/error/warning counts — never the row content itself) so you can see whether data quality is improving or degrading across repeated ingestion attempts. **Clear History** wipes it.

## Running the tests

```bash
cd builds/2026-08-10-ingest-gate
npm install
npx playwright test
```

44 tests, all passing as of this build.
