# Why This? — Bayes Lab

> **Date:** 2026-07-22

---

## How This Idea Was Selected

**Selection method:** Fresh generation.

Tonight's category (Learning Aid, index 4 of the 9-day rotation, day-of-year 203) had two pending backlog ideas — #17 "AI Concepts for Psychologists" and #18 "Forensic Assessment Reasoning Trainer" — both with a blank rating (R=0 numeric-rated ideas), giving a 25% lottery chance. The roll was 82, which is above 25, so the fresh-idea path was taken instead of drawing from the backlog.

## The Decision

I generated three fresh Category E candidates: (1) a Bayesian statistical-inference trainer, (2) a portfolio-risk-metrics trainer using live yfinance data, and (3) a hands-on "how LLM agents actually work" explainer. I picked the Bayesian trainer because it directly answers a learning goal named verbatim in PROFILE.md ("Develop advanced Bayesian statistical workflows") that no build in 41 prior nights has touched, while the two existing statistics-adjacent Learning Aid builds (Power Lab: frequentist power/sample-size; Stats Coach, an unmerged 2026-06-25 build: frequentist test selection) both stay squarely in the frequentist paradigm — leaving the entire Bayesian half of the user's own stated goal unaddressed. It is also mathematically self-contained and rigorously verifiable (I derived and cross-checked the Beta-Binomial, Wilson-CI, and exact-binomial-test math against an independent stdlib-only Python reference implementation before writing a line of the build's JS), which matters for a build whose entire value proposition is teaching *correct* statistical reasoning to someone who is "highly analytical and evidence-driven" and would immediately distrust a tool that got the numbers wrong.

## Connection to User Context

PROFILE.md names "Develop advanced Bayesian statistical workflows" as an explicit learning goal, and separately lists "empathy, psychopathy, and stress research" and "Neuroimaging methods and forensic neuroscience" among the topics the user follows. The five built-in scenarios (clinical response rate, screening-tool positive rate, manipulation-check pass rate, replication success rate, plus Custom) are written to sit directly inside that research vocabulary rather than as generic coin-flip examples, so the tool teaches Bayesian reasoning using the kind of question the user actually asks in their own lab.

## Why Tonight

Category E is due today under the fixed 9-day rotation (day-of-year 203 → index 4 → Learning Aid), and the fresh-idea path was triggered by the lottery roll described above. There is no direct predecessor build to resume or extend — this is the first Bayesian-statistics build in the catalog — though it deliberately positions itself as the missing counterpart to the existing frequentist-focused Power Lab (2026-07-04) and the unmerged Stats Coach (2026-06-25), each of which taught one frequentist workflow (power analysis; test selection) without ever crossing into Bayesian territory.

## What I Hope the User Gets From This

1. A concrete, correct, hands-on feel for how a prior actually gets updated into a posterior by real data — something reading about Bayes' rule rarely produces on its own
2. A working answer to "what does a Bayes factor actually mean, and how is it different from a p-value" using their own research framing, not an abstract textbook example
3. A reusable mental model (prior elicitation via equivalent sample size, Savage-Dickey Bayes factors, credible vs. confidence intervals) they could plausibly bring into their own graduate statistics teaching or their "Stress and Coping" course material

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| Portfolio Risk Metrics Trainer (Sharpe/Sortino/max drawdown/VaR taught interactively with live yfinance data) | E | Ties to the "quantitative investing" learning goal, but the investment/finance domain has already appeared multiple times in the catalog (Investment Research Platform, Investment Thesis Journal, CanEcon Pulse); the Bayesian idea answers a completely uncovered learning goal instead of revisiting a covered one. Logged to the backlog for a future night. |
| Agentic AI Concepts Lab (hands-on tokenization/embeddings/tool-use explainer with real computed demos) | E | Genuinely strong fit for "Master AI agent workflows" and the "AI Applications for Psychologists" course, but a near-identical idea (backlog #17) was already considered and passed over once before for being "less differentiated than a tool built around the user's own less-commonly-covered research domain" — the same critique still applies tonight. Logged to the backlog for a future night with a sharper differentiating angle. |
| Forensic Assessment Reasoning Trainer (backlog #18) | E | Already flagged in the backlog as needing real clinical-guideline grounding before being responsible to build; not attempted again tonight for the same reason. |
