# Why This? — Landing Pattern

> **Date:** 2026-08-03

---

## How This Idea Was Selected

**Selection method:** Fresh generation.

Tonight's category (day-of-year 215 → index 7) is H — Developer Tool. The Category H backlog held three pending rows: #9 (GitHub Actions Performance Analyzer — a verbatim duplicate of the already-built 2026-06-28 `ci-pulse`, corrected to `skipped` below), #13 (Deadweight, a dead-code finder previously passed over because `vulture` already does the mechanical core), and #14 (Flaky Test Detector, previously passed over as too narrow). None had a numeric rating, so R=0 and `lottery_chance = min(75, 25 + 0*2) = 25%`. Rolled 100/100 — missed the draw, so fresh ideas were generated per Step 2d.

## The Decision

Before generating ideas, orientation surfaced something the category rotation and lottery process couldn't have known about on their own: this repository currently has **50 open pull requests**, stretching back to PR #3 (2026-06-11), none merged — `main` is still sitting at the 2026-06-18 Regex Dojo build. Every build since has shipped correctly (`report_json`... rather, `builds/index.md` on the most recent branch shows 49 completed builds through 2026-08-02) but none of that work has landed. Nothing has been rated since 2026-06-24 either. A Developer Tool build that helps clear that exact backlog is about as directly useful as a nightly build can be. I checked the catalog first to make sure this wasn't already solved: the 2026-07-09 build **Pipeline Pulse** already answers "which builds are stuck in an open PR and for how long" by diffing this repo's own catalog against git history — so a second detector would be a pure duplicate. What doesn't exist yet is the next question: *given that a backlog exists, which PRs are actually safe to merge right now, in what order, and which ones will silently conflict with each other if merged out of sequence?* That's a distinct, unanswered question, so I built the answer to it instead of re-building detection.

## Connection to User Context

PROFILE.md names "managing many simultaneous projects" and "administrative overhead" as recurring friction points, and states a preference for "practical systems that reduce cognitive load." This repo's own PR backlog is a live, concrete instance of exactly that friction — the user runs many parallel GitHub-backed projects (The Canada List, Kwyeter, this nightly-build system itself) and can't reasonably open 50 PRs one at a time to figure out which are safe to merge unattended.

## Why Tonight

Timely in the literal sense: the backlog exists right now, in this repo, and the tool can be validated against it directly rather than against synthetic data. It also follows on from Pipeline Pulse (2026-07-09) as a natural second step — detection existed, sequencing/conflict-risk didn't.

## What I Hope the User Gets From This

1. A concrete, ordered starting point for clearing the 50-PR backlog in one sitting instead of reviewing each PR cold
2. Visibility into which open PRs will conflict with each other if merged carelessly (the file-overlap graph), which is invisible from the GitHub PR list view
3. A reusable tool for any of their other GitHub-backed repos, not just this one

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|-----------------|
| Local Dev Environment Doctor — audits a local repo for env/lockfile/config drift | H | Genuinely useful, but no live data source makes it feel thinner next to a tool that can be validated against this repo's real, current 50-PR backlog tonight |
| Snippet Vault — searchable personal code-snippet library with AI natural-language search | H | Architecturally close to the already-built Citation Vault (2026-07-29) and Connectome (2026-07-11) — same "personal indexed library with AI-assisted retrieval" shape on a third content type; would need a more distinct mechanic to be worth a third pass at that pattern |
| GitHub Actions Performance Analyzer (backlog idea #9) | H | Verbatim duplicate of the already-built and already-shipped 2026-06-28 `ci-pulse` build; corrected in `builds/ideas.md` |
