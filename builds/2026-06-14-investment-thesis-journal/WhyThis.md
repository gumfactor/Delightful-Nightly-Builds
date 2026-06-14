# Why This? — Investment Thesis Journal

> **Date:** 2026-06-14

---

## How This Idea Was Selected

**Selection method:** Fresh generation (no lottery draw)

The category rotation landed on **C — Personal Knowledge Tool** (day of year 165; `(164) % 9 = 2`). The filtered backlog for Category C with focused complexity was empty — no pending ideas existed. The lottery was skipped per the process, and fresh ideas were generated.

A random integer was generated to determine the fresh path: rolled 72, lottery chance was 25% (only 2 rated builds — fewer than the 3 needed to increase the base rate). Since 72 > 25, fresh generation was confirmed.

## The Decision

Tonight's build is a focused utility for Sunday: one specific, immediately usable thing that solves a concrete problem without requiring infrastructure. Three ideas were evaluated; the Investment Thesis Journal won because it combines personal knowledge management with a real data integration (Yahoo Finance), making it genuinely better than a plain text file. The other candidates — a paper tracker and a GitHub stars organizer — either competed with tools the user already has (Zotero/Mendeley for papers) or required GitHub API complexity better suited to a higher-complexity night.

## Connection to User Context

The user has an active interest in quantitative investing, uses Interactive Brokers, and listed investment research aggregation as a recurring friction point. PROFILE.md explicitly identifies Yahoo Finance as a zero-credential data source. When investment decisions are made, the context (price level, market environment, reasoning) matters enormously for later review. Most investors record what they bought but not *why*, and reviewing a decision six months later without the original context is nearly useless. This tool closes that gap.

## Why Tonight

Category C is the first time the rotation has landed here; the slot was empty and overdue. The Yahoo Finance integration means this build connects to real data automatically — every note is timestamped with the price at writing, giving the user an instant record of entry conditions without manual lookup. It works on Sunday morning with zero setup.

## What I Hope the User Gets From This

1. A lightweight, durable log of investment reasoning that is queryable from the terminal
2. Automatic price context captured at the moment of each note, without needing to look it up later
3. A fast CLI that fits naturally into the developer workflow — one command to record a thought, one command to review it

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| Research Paper Tracker | C | Users with active research programs almost certainly already use Zotero or similar citation managers. A bespoke tracker without a real data integration (DOI lookup, CrossRef, etc.) is just a structured text file — not better than what's already available. Suitable for a future night with solid complexity and a real API integration. |
| GitHub Stars Organizer / Annotator | C | Genuine value, but the GitHub API scoped to starred repos adds authentication complexity and the problem (organizing starred repos) is lower-priority than investment research. Better as a solid-complexity build on a Tuesday or Friday. |
