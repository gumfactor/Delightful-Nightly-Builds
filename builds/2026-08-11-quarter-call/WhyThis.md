# Why This? — Quarter Call

> **Date:** 2026-08-11

---

## How This Idea Was Selected

**Selection method:** Lottery draw from `builds/ideas.md`.

Tonight's day-of-year rotation (day 223, `(223-1) % 9 = 6`) landed on **Category G — Game/Puzzle**. The backlog held two pending Category G rows, both blank-rated (5 tickets each, since a blank rating defaults to 5 tickets): #11 "Market Cap Higher or Lower" and #12 "Stock Chart Direction Quiz." With zero rated ideas in the pool (`R = 0`), `lottery_chance = min(75, 25 + 0) = 25%`. A shell `$RANDOM` roll of **22** (≤ 25) triggered the draw. A second roll of **6** out of 10 (tickets 1–5 = #11, 6–10 = #12) selected **#12, Stock Chart Direction Quiz**.

## The Decision

This was a lottery draw, not a fresh idea, so the selection itself wasn't a deliberate choice between alternatives — but it landed on a strong fit anyway. The idea as written in the backlog ("show a real historical stock chart... guess whether it went up, down, or flat... uses pre-generated yfinance data") maps directly onto this catalog's single highest-rated build to date (Qualtrics Survey Data Inspector, 9/10) and its strongest recurring pattern: verifiable, real-data-backed mechanics beat prose wrappers or synthetic toys. It also let me correct a real gap — every prior Category G build (Regex Dojo, Neurofact, Synapse Sort, Confound Hunter, Heuristic Hunt, Lexicon) has been entirely synthetic/hand-authored content; this is the first Game/Puzzle build that pulls in genuine external market history as its core content.

## Connection to User Context

PROFILE.md names "quantitative investing" and "market structure" as an active personal interest and a named learning goal ("Continue learning quantitative investing and algorithmic trading"), and lists Interactive Brokers among daily tools. This build trains the specific skill of reading a price chart without being told the ticker's recent news — a genuinely useful pattern-recognition exercise for someone actively engaged with markets, framed honestly as a game rather than a trading signal.

## Why Tonight

Category G's rotation slot landed tonight regardless of topic; the lottery (not a deliberate override) picked the investing-themed idea. Investing/finance had appeared once in the last 10 builds (Portfolio Lab, 2026-08-09, Category E) — not saturated per the topic-diversity check in CLAUDE.md, which only requires an override when a domain appears more than twice in 10. No override was warranted or applied.

## What I Hope the User Gets From This

1. A genuinely fun few minutes of chart-reading practice against real, settled market history — with an honest reminder (in the footer and the AI note) that any single quarter is close to a random walk, so this teaches pattern-recognition literacy rather than false confidence in prediction.
2. A Daily Challenge habit loop (5 rounds/day, shareable emoji result) in the same vein as this catalog's other daily-cadence games (Lexicon, Confound Hunter, Heuristic Hunt).
3. A concrete, reusable pattern for future builds: "ship honest, run `fetch_data.py` locally" — this build container can't reach Yahoo Finance, so nothing here is faked; the user gets real 2016–2023 history across 48 tickers and 11 sectors the moment they run one command.

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|-----------------|
| Market Cap Higher or Lower (backlog #11) | G | Lost the weighted lottery draw (tickets 1–5 vs. the winning #12's 6–10). Also a thinner mechanic — a single relative comparison per round vs. #12's richer chart-reading + sector/metrics context. |
| A fresh idea in Category G | G | Not reached — the lottery drew successfully (roll 22 ≤ 25% chance), so per CLAUDE.md's Step 2c the process skips straight to building the drawn idea rather than generating alternatives. |
