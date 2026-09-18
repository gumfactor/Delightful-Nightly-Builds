# Manual — Eligible Spend

> **Version:** 1.0 (built 2026-09-18)
> **Complexity:** Ambitious Project

---

## What This Is

A Tri-Agency (NSERC/CIHR/SSHRC) grant budget compliance checker. You give it an itemized budget CSV and your grant's start/end dates; it runs every line item through a rule engine grounded in the Tri-Agency Guide on Financial Administration's (TAGFA) principles-based framework and flags anything that's dated outside the grant period, matches a specifically-named ineligible category (alcohol, tuition, institutional overhead, passport/immigration fees, an international driver's licence, commuting, frequent-flyer-points airfare, sabbatical living expenses), or needs a justification note before it can be cleared (hospitality, or any item with no description tying it to the funded research). It produces a terminal report, a self-contained HTML dashboard, and a CSV of just the flagged items to bring to your grants office.

**Important:** this is a decision-support heuristic against the *general public* Tri-Agency guide, not legal or financial advice, and it does not model your institution's negotiated overhead/indirect-cost rate. It never tells you a budget is "compliant" — only that no *known* rule fired. Always confirm with your institution's research grants or financial office before submitting.

---

## Quick Start

1. Build a CSV of your budget line items with columns `item, category, amount, date` (and optionally `justification`) — see `sample_data/sample_budget.csv` for the exact format.
2. Run:
   ```bash
   cd builds/2026-09-18-eligible-spend
   python3 src/main.py sample_data/sample_budget.csv --grant-start 2026-04-01 --grant-end 2027-03-31
   ```
3. Read the terminal summary, then open `report.html` (written to the current directory by default) in any browser.
4. Bring `flagged_items.csv` to your grants office to resolve, or edit your source budget and re-run.

---

## How to Use It

### The input CSV

| Column | Required | Format |
|---|---|---|
| `item` | Yes | Free text description |
| `category` | Yes | Free text (e.g. "Personnel", "Travel", "Hospitality") |
| `amount` | Yes | Number, optionally with `$` and commas |
| `date` | Yes | `YYYY-MM-DD` |
| `justification` | No | Free text tying the item to the funded research |

### Command-line options

```
python3 src/main.py BUDGET.csv --grant-start YYYY-MM-DD --grant-end YYYY-MM-DD [--out-dir DIR] [--ai]
```

- `--grant-start` / `--grant-end`: the eligible grant period. Any line item dated outside this range is flagged regardless of category.
- `--out-dir`: where to write `report.html` and `flagged_items.csv` (default: current directory).
- `--ai`: adds a one-sentence Claude Haiku note to every `requires_justification`/`no_blocking_rule_found` item, assessing whether the stated justification plausibly satisfies the direct-cost and not-institution-provided principles. Requires `ANTHROPIC_API_KEY` in your environment; without it, the tool runs the same report using a deterministic fallback note and makes zero network calls.

### Reading a verdict

Every flagged item carries a `reason` (in plain English) and a `principle` (the specific TAGFA principle or directive it's checked against). "No Blocking Rule Found" is deliberately not labeled "eligible" — it means nothing in the rule set caught a problem, but the three general principles (direct cost, not institution-provided, effective/economical) still apply and this tool cannot verify all of them automatically.

### The dashboard

Four summary tiles (total budget, $ ineligible, $ requiring justification, $ clean), a bar breakdown by verdict, and a searchable/sortable/filterable line-item table with the reason and cited principle under each flagged row. Opens directly via `file://`, no server required. Works down to a 375px mobile width.

---

## Configuration

| Setting | Default | Description |
|---------|---------|--------------|
| `--out-dir` | Current directory | Where `report.html` / `flagged_items.csv` are written |
| `ANTHROPIC_API_KEY` | Unset | Enables `--ai` review notes; the tool works fully without it |

No other configuration required.

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| "invalid date" error | A `date` cell isn't `YYYY-MM-DD` | Reformat the date column |
| "missing required column(s)" | CSV header doesn't include `item`, `category`, `amount`, or `date` | Check the header row matches the format above |
| Everything is flagged `outside_grant_period` | `--grant-start`/`--grant-end` don't match your actual budget dates | Double-check the grant period arguments |
| `--ai` note says "AI review not available" | No `ANTHROPIC_API_KEY` set, or the API call failed | Set the key in your environment, or ignore — the deterministic report is complete without it |

---

## Known Limitations

- Category matching is keyword-based, not a full NLP classifier — an oddly-worded category/description could slip past a rule it should trigger, or (rarely) trigger a rule it shouldn't. Always read the flagged reasons, don't just trust the counts.
- Does not model institution-negotiated overhead/indirect-cost rates at all — by design (see PRD's Out of Scope).
- CAD only, no currency conversion.
- Covers NSERC/CIHR/SSHRC (Tri-Agency) rules only, not other funders (CFI, provincial agencies, foundations).
