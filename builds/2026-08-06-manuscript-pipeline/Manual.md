# Manual — Manuscript Pipeline

> **Version:** 1.0 (built 2026-08-06)
> **Complexity:** Ambitious Project

---

## What This Is

Manuscript Pipeline is a command-line tool that keeps one durable record of every academic manuscript you have in flight — from the day it's submitted, through review, through any revise-and-resubmit cycle, to acceptance and eventual publication. Instead of reconstructing a manuscript's status from memory or old email threads, `list`/`report` shows you every manuscript's current stage and how long it's been there, flags anything that's overdue relative to how long it's expected to take, and — via the `sync` command — automatically checks the free Crossref API to notice when a manuscript you're still tracking as "under review" has quietly gone live with a real DOI.

---

## Quick Start

1. From the build folder, register a manuscript:
   ```
   python3 src/main.py add --title "My Paper Title" --authors "Jane Doe, John Smith" \
       --journal "Journal of Examples" --submitted 2026-08-01
   ```
2. See where everything stands:
   ```
   python3 src/main.py list
   ```
3. When you get a decision email, paste it in:
   ```
   python3 src/main.py capture 1 --text "We are pleased to accept your manuscript..."
   ```
4. Periodically (weekly is reasonable), check whether anything has quietly been published:
   ```
   python3 src/main.py sync
   ```
5. Generate a shareable dashboard:
   ```
   python3 src/main.py report --out report.html
   ```
   Then open `report.html` in any browser.

A SQLite file `manuscripts.db` is created automatically in the build folder on first use — no setup step required.

---

## How to Use It

### `add` — register a new manuscript

```
python3 src/main.py add --title "..." --authors "Jane Doe, John Smith" \
    --journal "..." --type original-research --submitted 2026-08-01 [--expected-days 90]
```

- `--authors`: comma-separated; the **first** name listed is treated as the corresponding author and is what `sync` uses for its Crossref author check.
- `--type`: one of `original-research`, `review`, `commentary`, `other`. Defaults to `original-research`.
- `--expected-days`: how many days a typical review takes at this journal before the manuscript is flagged "at risk." Defaults to 90 — override per-manuscript if you know a particular journal is faster or slower.

### `list` / `report` — see current status

`list` prints a terminal summary (funnel counts, at-risk list, full manuscript list with days-in-stage).

`report --out report.html` prints the same terminal summary **and** writes a self-contained dark-mode HTML dashboard with a funnel chart, a sortable/searchable manuscript table, and an at-risk panel highlighted in red. Open the file directly in a browser — no server required.

### `update` — manually change a manuscript's status

```
python3 src/main.py update <id> --status revise_resubmit --deadline 2026-09-15 --note "Two reviewers, minor concerns"
```

Valid `--status` values: `submitted`, `under_review`, `revise_resubmit`, `accepted`, `rejected`, `published`, `withdrawn`. Every update is permanently logged — nothing is ever overwritten, so a manuscript's full history is always recoverable.

### `capture` — extract a decision from a pasted email

```
python3 src/main.py capture <id> --text "paste the email here"
```
or pipe text in:
```
cat decision_email.txt | python3 src/main.py capture <id>
```

A deterministic keyword/regex parser always runs first and requires no setup. If you set the `ANTHROPIC_API_KEY` environment variable, an optional Claude Haiku pass is attempted and used instead when it returns a valid, well-formed result — with the deterministic result as an automatic fallback on any error, so `capture` always works, key or no key.

### `sync` — auto-detect publication via Crossref

```
python3 src/main.py sync
```

For every manuscript not already `published`/`rejected`/`withdrawn`, queries the free, no-auth Crossref API by title and first-author surname. A manuscript is only auto-transitioned to `published` when a candidate result's title has a normalized token-overlap similarity of **at least 0.72** to your recorded title **and** at least one author surname matches — this two-part check is intentionally strict to avoid a false "published" flip on an unrelated, similarly-titled paper.

---

## Configuration

| Setting | Default | Description |
|---------|---------|--------------|
| `--db <path>` | `manuscripts.db` in the build folder | Path to the SQLite database file. |
| `--expected-days` (on `add`) | `90` | Days after submission before a `submitted`/`under_review` manuscript is flagged "at risk." |
| `ANTHROPIC_API_KEY` (environment variable) | unset | If set, enables the optional AI-assisted `capture` pass. Never required. |
| Crossref match threshold | `0.72` (title similarity) + 1 matching author surname | Hardcoded in `src/crossref.py` (`MATCH_THRESHOLD`) — edit that constant if you find it too strict/loose for your field's naming conventions. |

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `sync` reports "No new publications detected" for a paper you know is published | Crossref may not have indexed it yet, or the title/author match didn't clear the threshold | Wait a few days and re-run `sync`; if it's genuinely published and still not detected, use `update <id> --status published --doi <doi>` manually |
| `capture` says "Could not confidently determine a decision" | The pasted text didn't contain a recognizable decision phrase (e.g. a plain "thank you for your submission" acknowledgment, not an actual decision) | This is expected for acknowledgment-only emails — use `capture` only for actual decision letters, or `update` manually |
| Network error when running `sync` | Crossref (`api.crossref.org`) is unreachable from your network | `sync` is designed to run in your normal local environment, where the free Crossref API is reachable without authentication; a restrictive corporate/build-container network is the usual cause |
| `report.html` shows a plain table instead of the funnel bar chart | The Chart.js CDN (`cdn.jsdelivr.net`) was unreachable when the page loaded | This is the intended graceful fallback — the DOM-built table shows the same funnel counts with no loss of information |

---

## Known Limitations

- `days_in_stage` measures time since original submission, not time since entering the *current* stage — see `FutureFeatures.md` for the planned fix.
- `sync`'s auto-publication detection only queries Crossref; it will not catch a publication that Crossref hasn't indexed a DOI for yet (rare, but happens with some smaller or non-DOI-registering outlets).
- `capture`'s deterministic parser recognizes a curated set of decision phrases and two date formats (ISO `YYYY-MM-DD` and `Month D, YYYY`); an unusually worded decision letter may require a manual `update` instead.
