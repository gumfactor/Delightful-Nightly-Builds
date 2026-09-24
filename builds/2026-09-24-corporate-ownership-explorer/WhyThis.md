# WhyThis.md — Corporate Ownership Chain Explorer

## Category and date
2026-09-24. Day of year 267. `(267 - 1) % 9 = 5` → Category **F — Data Explorer**.

## Selection path: lottery draw
Read `builds/ideas.md` for pending Category F rows: 9 pending entries (IDs 10, 20, 21, 30, 31, 45, 46, 61, 62), all with blank `Your Rating` (R = 0 rated entries among the 9 — none of them carry a numeric rating, so `R` for the lottery-chance formula, which counts entries *with* a numeric rating, is 0).

- `lottery_chance = min(75, 25 + 0 * 2) = 25%`
- Roll: **11** (1–100) → 11 ≤ 25, so **draw**.
- Tickets: each of the 9 pending rows gets 5 tickets (blank rating = default weight), for 45 total tickets, weighted-random pick.
- Draw result: **idea #61 — Corporate Ownership Chain Explorer**.
- Idea #61 marked `built` in `builds/ideas.md`; no fresh-idea generation was needed for tonight (lottery path skips Step 2d).

## Idea Brief
Idea #61's `Idea Brief` column is `—` (no linked brief). Step 2e (consult linked brief) does not apply; the backlog row's own description is the full spec basis for tonight's PRD.

## Why this idea, on its own terms
The backlog row itself explains why it was passed over twice before (2026-08-28, 2026-09-15) in favor of EDGAR Lens and Rotation Radar — never because the idea was weak, but because of topic-diversity timing against SEC EDGAR / Wikidata builds that had just run. Neither objection holds tonight:

- **Topic diversity check (last 10 builds):** Secrets Sentinel (H), Headroom (I), Dominion Index (A), GradeLine (B), Throughline (C), Preprint Pulse (D), ERP Lab (E), Rotation Radar (F), Marginal Gains (G), Eligible Spend (I), Grant Horizon (A), Counterpoint (B), Star Atlas (C), Wake Log (D), Pooling Lab (E). Wikidata/SPARQL last appeared 14 nights ago (Dominion Index, 2026-09-10) — well outside the window this idea's own rating notes flagged as too close. SEC EDGAR (EDGAR Lens) is 27 nights back. Neither source is saturated.
- **Distinct mechanic, not a rehash:** Dominion Index (2026-09-10) is an *aggregate* view — industry/province counts across many companies. This build is a *per-entity drill-down* — search one company, walk its live parent/subsidiary ownership chain, click through the chain interactively. Different question, different interaction model, same underlying data source used in a genuinely different way.
- **Real, named editorial need:** PROFILE.md names The Canada List's "ingestion and quality control pipeline" as a manual friction point, and identifying true Canadian ownership (a Canadian-branded product owned by a foreign parent, or vice versa) is exactly the kind of fact a per-entity ownership lineage tool answers that an aggregate dashboard cannot.
- **Fits the calibration note:** live data (Wikidata Query Service + wbsearchentities, both free/no-auth, CORS-enabled, called directly from the browser), a real visual/interactive interface (Category F requires one — a script that prints to stdout does not count), and it does not duplicate a tool already in the user's stack (nothing in PROFILE.md's daily tools does per-entity ownership-chain lookups with citation transparency).

## Deviations from the backlog description
None of substance. The backlog description promises "citations back to Wikidata's own claim sources" — implemented as a direct link from every ownership edge to that exact Wikidata statement (`https://www.wikidata.org/wiki/Q<id>#P<prop>`), which is what "citation back to the source" means for Wikidata specifically: the statement page is where a human can inspect the actual reference (stated-in, reference URL, retrieval date) Wikidata itself records. Parsing and re-displaying arbitrary reference metadata client-side was considered and rejected as unreliable — Wikidata references are heterogeneous and often absent — in favor of always linking to the canonical, always-current source of truth.
