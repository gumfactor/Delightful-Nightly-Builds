# Why This? — Effort Ledger

> **Date:** 2026-08-19

---

## How This Idea Was Selected

**Selection method:** Fresh generation, after a lottery draw was overridden.

Day-of-year rotation (day 231 of 2026) put tonight at category index `(231-1) % 9 = 5` → **F — Data Explorer**. `builds/ideas.md` had two pending Category F rows: idea #1 (The Canada List CSV Quality Inspector, rated 7 → 7 tickets) and idea #10 (SEC EDGAR Financial History Extractor, unrated → 5 tickets), so `R = 1` rated idea and `lottery_chance = min(75, 25 + 1*2) = 27%`. A roll of 8 (≤27) triggered a draw; a weighted pick across the 12 tickets (roll 5, within idea #1's 1–7 range) selected idea #1.

Idea #1 was written on 2026-06-06, before the 2026-08-10 build "Ingest Gate" existed. Ingest Gate's actual description — "Browser CSV quality inspector for The Canada List's own ingestion pipeline... flags missing required columns/values, malformed... rows, invalid... values... alongside a separate... duplicate detector" — is now word-for-word what idea #1 asks for. Building it again would violate CLAUDE.md's explicit novelty requirement ("not already in `builds/index.md`") and the calibration note's named failure pattern ("duplicate functionality already in the user's tools" — here, in a prior build). I marked idea #1 `skipped` with a note explaining the supersession rather than building a near-duplicate of an existing catalog entry, and generated fresh Category F ideas instead, per the same "if the filtered pool is empty [of genuinely available ideas], generate fresh" spirit the process already follows for a literally-empty pool.

## The Decision

Of three fresh Category F candidates (see Alternatives below), Effort Ledger was chosen because it fits the category's single highest-rated build to date — 2026-06-17's Qualtrics Survey Data Inspector (9/10, "research-quality data QC" on the user's own exported data, fully deterministic and verifiable) — while covering territory no prior build has touched: budget-line arithmetic and cross-grant effort-commitment auditing. Six prior Category F builds already exist (Qualtrics Inspector, GitHub Activity Explorer, TrialScope, GrantScope, ItemScope, Ingest Gate); all six are "upload structured data, get a deterministic QC report" tools, which is the category's proven-strongest shape, so Effort Ledger follows that shape rather than inventing a new one.

## Connection to User Context

PROFILE.md names "Grant writing" and "Research administration" directly under "Things you do manually that you suspect could be automated or aided by a tool," and separately lists "Run a forensic and affective neuroscience lab... write grants and manuscripts... supervise research assistants and graduate students" as day-to-day work. No prior build audits budget math or effort commitments — GrantScope searches for funding opportunities, Panel Prep critiques proposal *prose*, Protocol Forge checks IRB *ethics* compliance, and Impact Ledger/Manuscript Pipeline track post-submission citation/publication status. Cross-grant effort overcommitment (a person certifying more combined effort across simultaneous awards than they actually have) and indirect-cost math errors are the two most common findings in a real grants-office pre-award or post-award review — a genuine, previously-unaddressed friction point.

## Why Tonight

Straightforward category-rotation night (day 231 → index 5 → F). No linked Idea Brief was involved (idea #1 had none, and this is a fresh-generation build, not a brief-backed one).

## What I Hope the User Gets From This

1. A tool that catches a real class of grant/budget errors — indirect-cost miscalculation and effort overcommitment — before a grants office or auditor does, on the user's own real budget/effort spreadsheets
2. A concrete, load-bearing example of the "verifiable-statistics QC report" pattern (the catalog's best-performing Category F shape) applied to a friction point named directly in PROFILE.md
3. Sample data and a CLI that runs immediately, so the value is checkable in minutes rather than requiring the user's real award documents on first use

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| Manuscript Citation Cross-Checker (in-text citations vs. reference list, flag mismatches) | F | Real gap (idea #13's rating notes had already flagged citation consistency as a good differentiator), but citation-string matching is a simpler, less novel verification problem than the effort-overcommitment interval-overlap algorithm, and overlaps conceptually with Citation Vault's existing BibTeX handling. Appended to `builds/ideas.md` as idea #20 for a future night. |
| StatsCan Canadian Business Data Explorer (live open-data dashboard for The Canada List market context) | F | Good live-API shape and a genuine Canada List gap, but StatsCan's table/vector-ID API structure needs a real scouting pass before a build session can commit to a reliable schema — riskier to deliver complete and correct in one session than a CSV-upload audit tool. Appended to `builds/ideas.md` as idea #21 for a future night with time budgeted to survey the API first. |
| The Canada List CSV Quality Inspector (original lottery draw, idea #1) | F | Now functionally duplicate of the already-built Ingest Gate (2026-08-10) — see "How This Idea Was Selected" above. |
