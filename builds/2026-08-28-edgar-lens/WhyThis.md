# Why This? — EDGAR Lens

> **Date:** 2026-08-28

---

## How This Idea Was Selected

**Selection method:** Fresh generation.

Day-of-year rotation (day 240 → `(240-1) % 9 = 5` → Category F, Data Explorer). Category F's backlog held 3 pending rows (#10 SEC EDGAR Financial History Extractor, #20 Manuscript Citation Cross-Checker, #21 StatsCan Canadian Business Data Explorer), none rated (R=0), giving a 25% lottery chance. Rolled 29 — missed the draw, so fresh ideas were generated per Step 2d.

## The Decision

Three fresh Category F candidates were considered (see Alternatives below). SEC EDGAR's XBRL `companyfacts` API — a real, free, no-auth financial-statement data source named explicitly in PROFILE.md's Data Sources but never once used across 111 prior builds despite two backlog rows (#10, #27) proposing SEC EDGAR or StatsCan variants — won because it is the only candidate with both a genuinely untouched real data source and a deterministic, testable core (tag resolution, fiscal-year alignment, ratio math, anomaly thresholds) rather than a thin AI-prose wrapper, directly avoiding the failure mode that scored 2026-06-24's AI Lecture Builder a 2/10.

## Connection to User Context

PROFILE.md names "Quantitative investing and market structure" as a rabbit-hole interest and "Continue learning quantitative investing and algorithmic trading" as a learning goal. Every prior investing-adjacent build (SiliconWatch, Trading Book, Portfolio Lab, Quarter Call) works from live prices or a live brokerage account — none has looked at the actual filed financial statements behind those prices. Reading multi-year 10-K trends and ratio deterioration by hand is exactly the kind of repetitive analytical work PROFILE.md's "Recurring friction points" section flags as worth automating.

## Why Tonight

Category F (Data Explorer) came up via the fixed 9-day rotation. STANDARDS.md requires F builds to ship a visual/interactive interface, which ruled out a stdout-only script and pointed toward the CLI + self-contained HTML dashboard shape this catalog has used successfully for prior Category F/A builds (Qualtrics Survey Data Inspector, Impact Ledger, Effort Ledger).

## What I Hope the User Gets From This

1. A fast way to check a watchlist company's actual revenue/margin/leverage trend from real filed data, instead of re-deriving it from a 10-K by hand each time
2. Automatic surfacing of the specific years where a company's fundamentals genuinely deteriorated (not just price moved), which price-only tools (Trading Book, SiliconWatch, Quarter Call) cannot show
3. A concrete example of applying the "verifiable-statistics QC report" pattern (the catalog's highest-rated shape, per Qualtrics at 9/10) to financial-statement data

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| SEC EDGAR Form 4 Insider Transaction Explorer | F | Same underlying SEC data source as EDGAR Lens but a narrower, single-signal build (insider buy/sell clustering) with less deterministic depth than full statement analysis; noted in `builds/ideas.md` for a future night |
| Wikipedia Pageview Trend Explorer for Canadian companies | F | Genuinely untouched data source (Wikimedia REST pageviews API) tied to The Canada List, but "public interest as a proxy signal" is a weaker, less verifiable core than real filed financial statements — logged as a backlog idea instead |
| Backlog #21 — StatsCan Canadian Business Data Explorer | F | Already passed over twice (2026-08-19, 2026-08-23) for the same documented reason: StatsCan's table/vector-ID schema needs a real exploration pass this build container's egress 403 makes hard to verify live; still unresolved tonight |
