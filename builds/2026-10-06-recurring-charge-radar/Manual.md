# Manual — Recurring Charge Radar

Finds subscriptions, bills and annual renewals in your bank/credit-card CSV exports. Runs fully offline; nothing is uploaded. Python 3.11+, no installs.

## Run

```bash
cd builds/2026-10-06-recurring-charge-radar
PYTHONPATH=src python3 -m recurring --demo                       # try it on synthetic data
PYTHONPATH=src python3 -m recurring ~/statements/*.csv --out report.html --ics upcoming.ics
```

Open `report.html` in any browser (works on a phone; email or AirDrop it). Import `upcoming.ics` into Google/Outlook/Apple Calendar for reminders two days ahead.

Options: `--rules rules.json`, `--json out.json`, `--days 90` (forecast window), `--today YYYY-MM-DD`.

## Getting CSVs
Download CSV from RBC, TD, CIBC, Scotiabank, BMO online banking (chequing and credit cards). Use at least 12 months, ideally 14+, so annual renewals show up twice. Overlapping files are fine; duplicates across files are removed.

## Reading the report
- **Tiles:** live monthly and annual cost, count, and what is due in 7 days.
- **Red alert (zombie):** you declared a cancellation date in the rules file but the charge kept coming.
- **Amber alert:** a confirmed price increase.
- **Tags:** `ended` (stopped charging), `price change`, `varies` (bills like hydro; shown as `~` median).
- Tap a row for the sparkline and the last 12 charges.

## rules.json
```json
{
  "ignore": ["TRANSFER", "INTERAC"],
  "aliases": {"ANTHROPIC": "Claude", "OPENAI": "ChatGPT"},
  "cancelled": {"Goodlife Fitness": "2026-07-01"}
}
```
`ignore` and `aliases` match as case-insensitive substrings of the raw description. `cancelled` keys are the display names shown in the report.

## How detection works
Charges are grouped by cleaned merchant name, then gaps between dates are matched to weekly/biweekly/monthly/quarterly/annual with tolerance for weekend drift. At least 3 charges are needed (2 for annual, exactly a year apart). Frequent, widely varying charges (groceries, coffee) are rejected. A price level change of 4% and $0.50 or more is reported; smaller FX wobble is ignored. Two subscriptions from one merchant at different prices are split.

## Tests
```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v     # or: python -m pytest tests/
```
