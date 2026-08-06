# Future Features — Manuscript Pipeline

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **Coauthor reminder export** — a `remind` command that prints a copy-pasteable one-line status summary per manuscript (e.g. "Study of Empathy: revise & resubmit, due 2026-09-01") formatted for dropping into an email to coauthors.
2. **CSV export** — an `export --csv` flag on `report` that dumps the manuscript table (title, journal, status, days-in-stage, DOI) for import into a spreadsheet or CV-building workflow.
3. **`--journal` filter on `list`/`report`** — narrow the view to manuscripts at one journal, useful once the pipeline has a dozen+ entries across many outlets.

## Medium Effort (roughly one nightly build session)

4. **Per-journal review-time learning** — instead of a single flat `expected_review_days` default, track the actual submitted→decision duration for every manuscript that reaches a terminal or revise state, and use the median for that specific journal (falling back to the global default until 2+ data points exist) to make the "at risk" flag more accurate over time.
5. **PubMed as a second publication-detection source** — `sync` currently only queries Crossref; adding a PubMed E-utilities esearch pass (also free, no-auth) as a second signal would catch biomedical journals that are sometimes slower to register DOIs with Crossref than to appear in PubMed.

## Ambitious Extensions (multi-session effort)

6. **Response-to-Reviewers Letter Builder integration** — the idea logged tonight in `builds/ideas.md` (paste reviewer comments, get an AI-assisted point-by-point response draft with per-comment resolution tracking) would fit naturally as a `respond <id>` subcommand on top of this tracker's existing manuscript records, rather than a separate tool.
7. **Grant Budget & Compliance Tracker integration** — the other idea logged tonight could share this build's SQLite/CLI/report architecture, giving the user one consistent "research administration" tool covering both manuscripts and grants instead of two separate ones.

---

## Possible Integration Points

- **Citation Vault** (2026-07-29) — once a manuscript here transitions to `published` via `sync`, its DOI could be handed directly to Citation Vault's `add --doi` command to seed a citation-ledger entry automatically, closing the loop from "in review" to "in my reading/citation library."
- **Impact Ledger** (2026-08-05) — Impact Ledger tracks citation counts for already-published work via OpenAlex; once this tracker detects a new publication, a shared `sync` step could also trigger an Impact Ledger snapshot for that specific new paper.
- **Deadline Guardian** (2026-07-17) — currently tracks general recurring academic deadlines; a revise-and-resubmit deadline captured here could optionally also be pushed into Deadline Guardian's SQLite store so all deadlines (grant, ethics, manuscript) surface in one dashboard.

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| `days_in_stage` is computed from the original `submitted_date`, not from when the manuscript entered its *current* stage — so "17 days" after an acceptance actually means 17 days since submission, not 17 days since acceptance. | Add a `stage_entered_at` timestamp captured on every `update_status` call and compute days-in-stage from that instead. |
| `sync`'s Crossref match only checks the first author's surname against all Crossref-listed authors; a manuscript with a very common author surname and a moderately generic title could theoretically produce a false match. | Add a secondary confirmation step (e.g. print a candidate match and require `--confirm` before auto-transitioning to `published`, instead of fully automatic). |
| `capture`'s AI path expects a single well-formed JSON object back from Claude Haiku; a verbose or conversational response (not following the "reply with ONLY JSON" instruction) currently falls back silently to the deterministic parser rather than warning the user the AI path was attempted and failed. | Log a one-line note to stderr ("AI parse failed, using deterministic fallback") when `ai_parse` returns `None` but an API key was present, so the user knows which path was used. |
| No `delete`/`withdraw`-with-cleanup command — a manuscript can be marked `withdrawn` via `update` but its full status history is never purged, which is correct for audit purposes but means a duplicate/test entry can't be removed from `list` output. | Add an explicit `archive <id>` command that excludes archived manuscripts from `list`/`report` by default (with a `--include-archived` flag) without deleting their row. |
