# Manual — Ledger Lens

> **Version:** 1.0 (built 2026-07-08)
> **Complexity:** Ambitious Project

---

## What This Is

Ledger Lens turns a raw bank or credit-card CSV export into a categorized, visual spending report. Drop in a CSV, and it auto-detects the date/description/amount columns, classifies every transaction into one of 14 categories (rule-based, with optional Claude enrichment for anything it can't confidently place), flags recurring subscriptions and charges, and produces a self-contained dark-mode HTML dashboard you can open in any browser — no server, no account, no internet dependency beyond the optional Chart.js CDN load for the two charts (everything else works fully offline).

---

## Quick Start

1. `cd builds/2026-07-08-ledger-lens`
2. Try it immediately with the bundled demo data: `python3 src/main.py analyze sample_transactions.csv --html report.html`
3. Open `report.html` in your browser.
4. For your own data: export a transaction CSV from your bank/card issuer, then run `python3 src/main.py analyze your_export.csv --html report.html`.
5. (Optional) Copy `budgets.example.json` to `budgets.json`, edit the category caps, and add `--budgets budgets.json` to see budget-vs-actual bars.

---

## How to Use It

### CSV Input Format

Ledger Lens auto-detects columns by header name, so most exports work without modification. It recognizes:
- **Date** columns named `Date`, `Transaction Date`, `Posting Date`, etc.
- **Description** columns named `Description`, `Details`, `Memo`, `Merchant`, etc.
- **Amount**: either a single `Amount` column (negative = expense, positive = income, by default), or separate `Debit`/`Credit` columns (common with Canadian bank exports).

If your issuer records charges as *positive* numbers instead of negative (some card issuers do this), add `--invert-sign`.

### Output Modes

- **Terminal (default):** `python3 src/main.py analyze data.csv` — colored summary in your terminal.
- **HTML dashboard:** add `--html report.html` — hero stats, category donut chart, monthly income/expense trend, recurring charges, budget bars (if `--budgets` given), and a searchable/sortable transaction table.
- **JSON:** add `--json` for machine-readable output instead of the terminal summary (useful for piping into other tools).
- **Cleaned CSV:** add `--out-csv cleaned.csv` to get your original data back with `Category` and `Recurring` columns added.

### Budgets

Copy `budgets.example.json`, edit the monthly cap per category, and pass `--budgets your_budgets.json`. Any category you omit is simply not compared — it doesn't need to cover every category.

### AI Enrichment (optional)

If `ANTHROPIC_API_KEY` is set in your environment, any transaction the built-in keyword rules can't confidently categorize is sent (merchant description only, with any long digit sequences like account/reference numbers redacted first) to Claude for a second pass, and the HTML/terminal insights paragraph is AI-generated instead of template-based. Without a key, everything still works — it just uses the deterministic rule-based categorizer and a template-based insights paragraph. Add `--no-ai` to force the deterministic path even if a key is present.

### Recurring Charge Detection

A charge is flagged as recurring when the same normalized merchant name appears with a similar amount (within 5%) in at least 2 different months. This deliberately clusters by amount within a merchant, so a genuine price change (e.g. a subscription going from $9.99 to $12.99) still gets tracked as recurring rather than silently missed, while two unrelated same-merchant purchases at very different amounts are not incorrectly merged.

---

## Configuration

| Setting | Default | Description |
|---------|---------|--------------|
| `--budgets PATH` | none | JSON file mapping category name → monthly cap |
| `--html PATH` | none | Write the HTML dashboard to this path |
| `--json` | off | Print JSON instead of the terminal summary |
| `--out-csv PATH` | none | Write a cleaned CSV with Category/Recurring columns |
| `--currency-symbol` | `$` | Symbol shown in terminal and HTML output |
| `--invert-sign` | off | Treat positive amounts as expenses instead of negative |
| `--no-ai` | off | Force the deterministic path even if `ANTHROPIC_API_KEY` is set |

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `Could not identify required column(s)` error | Your CSV's headers don't match any recognized naming variant | Rename the relevant column(s) in the CSV to `Date`, `Description`, and `Amount` (or `Debit`/`Credit`) |
| Most transactions land in "Other" | The built-in keyword rules don't recognize your specific merchants (common outside North America) | Set `ANTHROPIC_API_KEY` for AI enrichment, or extend `KEYWORD_RULES` in `src/categorize.py` |
| Income/expenses look reversed | Your issuer records charges as positive numbers | Add `--invert-sign` |
| The two charts in the HTML report show a "Chart.js could not be loaded" message instead of rendering | No internet access when the report was opened, or the CDN was blocked | All other functionality (stats, tables, search, sort, budgets) still works fully offline — the charts specifically need one-time access to `cdn.jsdelivr.net` |

---

## Known Limitations

- Each run is a snapshot of one CSV — there is no persistent multi-month history across separate runs (see FutureFeatures.md for a planned SQLite-backed version)
- The keyword-based categorizer is tuned for common Canadian/US retail and subscription merchants; unrecognized merchants fall to "Other" unless AI enrichment is enabled
- Recurring detection requires the *exact same* normalized merchant string across months; a subscription whose billing descriptor changes between charges may be missed
- Single currency per run — no automatic currency conversion
