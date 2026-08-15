---
name: provenance
description: Batch-classify a CSV of business names as Canadian-owned, foreign-owned, or uncertain, using free Wikidata lookups plus an optional Claude Haiku note on ambiguous cases. Use when the user asks to research, verify, or classify the Canadian ownership status of a list/batch of businesses for The Canada List, or says something like "classify this batch of businesses" or "check which of these companies are Canadian-owned."
---

# Provenance — Batch Canadian-Ownership Classifier

Wraps the `provenance` CLI (from `builds/2026-08-15-provenance/` in the Delightful-Nightly-Builds repo) so a coding session can classify a batch of businesses without leaving the session.

## When to use this

The user has, or can produce, a CSV of business names (from a submission form, a scrape, a spreadsheet export — anything with at least a `name` column) and wants to know which are Canadian-owned, which are foreign, and which need a human look.

## How to run it

1. Confirm the input CSV has a `name` column (optionally `website` and any other columns — they pass through untouched).
2. From the `builds/2026-08-15-provenance/` directory, run:

   ```bash
   python3 -m src.cli classify <input.csv> --out <output.csv> --render <report.html>
   ```

   Add `--ai-enrich` if `ANTHROPIC_API_KEY` is set in the environment and the user wants plain-English notes on ambiguous (`uncertain`) results.

3. Report back: the terminal summary's verdict counts, and the list of `uncertain` businesses worth a manual look (also printed to stdout, capped at 10 — read the output CSV directly for the full list on larger batches).
4. If the user wants a browsable report, open `<report.html>` — it is a single self-contained file with no external dependencies (safe to open via `file://`).

## Notes

- Requires network access to `www.wikidata.org` from wherever this session is running. If Wikidata is unreachable, every row will come back `uncertain` with confidence `0.0` rather than crashing — that is expected honest degradation, not a bug (see `Manual.md`'s Troubleshooting section).
- Re-running `classify` on overlapping business lists is cheap — already-resolved businesses are served from the tool's local SQLite cache (`provenance.db` in the CLI's working directory) rather than re-queried.
- This tool never writes anything back into The Canada List's production systems — its output is a CSV for the user to review and import manually.
