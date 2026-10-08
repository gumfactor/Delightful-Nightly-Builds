# Manual — Lookalike

Finds and merges duplicate business records in a CSV (built for The Canada List ingestion batches).

## Run it

```bash
cd builds/2026-10-08-lookalike
python3 lookalike.py demo --out out-demo            # fictional sample data, whole pipeline
python3 lookalike.py scan batch.csv --out out       # your own file
python3 lookalike.py scan batch.csv --existing directory_export.csv --out out   # also match against what is already live
python3 lookalike.py scan batch.csv --out out --decisions decisions.json        # honour your review calls
ANTHROPIC_API_KEY=... python3 lookalike.py scan batch.csv --out out --ai         # advisory Claude verdicts
```

Python 3.11+, standard library only. Open `out/review.html` in any browser (phone included).

## Input columns

Any subset of: `name` (required; aliases `business_name`, `company`, `title`…), `website`/`url`, `phone`/`tel`, `email`, `address`, `city`, `province`, `postal_code`, `category`, `description`, `updated_at`, and an optional `id`. Unknown columns are carried through untouched. More populated columns means stronger matching; missing columns produce a warning.

## Outputs (in `--out`)

| File | What it is |
|------|-----------|
| `deduped.csv` | One row per surviving business. Merged rows carry `merged_from` (source row ids) and `cluster_id`. |
| `clusters.csv` | Every row that belongs to a duplicate cluster, with status and flags. |
| `merge_report.json` | Summary, clusters with per-field provenance, review and branch pairs with every scoring reason. |
| `review.html` | Pairs needing your decision, cluster details, and chains kept separate. |

## How decisions work

Pair outcomes: **duplicate** (score ≥ 0.85, merged automatically), **review** (0.55–0.85, you decide), **branch** (same brand at a different address or phone, never merged), otherwise distinct. In `review.html` press *Same business* or *Different* on each card, then *Download decisions.json* and re-run with `--decisions decisions.json`. `same` forces a merge; `different` blocks one. A cluster that would only hold together through a chain of weaker links, or that contradicts a `different` call, is flagged `needs_review` and left unmerged. Merging never deletes input: the original CSV is untouched.

## Reading a score

Evidence combines as noisy-OR (`1 − Π(1 − weight)`) then conflict penalties are subtracted. Typical weights: matching name +0.60, same email +0.55, same website domain +0.50, same phone +0.45, same street address +0.40. Penalties: different province −0.30, different domain −0.20, different address −0.15, different phone −0.10, different unit −0.20. Social and marketplace hosts (facebook.com, etsy.com…) are ignored as identity.

## AI step

`--ai` sends only the listing fields of review-tier pairs (name, website, phone, address, city, province, postal code, description) to the Anthropic API, model `claude-haiku-5-5`, at most 50 pairs. Verdicts show on the review cards as advisory text and are never applied automatically.

## Tests

```bash
python3 -m unittest discover -s tests -v     # or: python3 -m pytest tests/ -v
```
