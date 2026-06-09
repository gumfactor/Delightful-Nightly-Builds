# Why This? — Quick Data Profiler

> **Date:** 2026-06-08

---

## How This Idea Was Selected

**Selection method:** Fresh generation

Tonight is Monday (day 1), which targets a Focused Utility (1–3 source files, usable in under 5 minutes). I chose category F (Data Explorer) because neither B nor H has been used in the last two nights, and F hadn't been used at all. The ideas backlog contained no F-category focused ideas (all three pending ideas are ambitious-complexity) so the lottery was skipped and I generated fresh ideas.

Fresh path: rolled 72 (lottery threshold was 25, since 0 rated ideas in the filtered pool). Roll > 25 → fresh ideas path.

Filtered pool size before roll: 0.

Three ideas were generated; Quick Data Profiler was chosen. The two non-winning ideas have been appended to builds/ideas.md.

## The Decision

The user mentioned The Canada List ingestion and quality control pipeline as a recurring friction point, and PROFILE.md lists "The Canada List ingestion and quality control pipeline" and "Investment research aggregation" as things they do manually that could be aided by a tool. A data profiler that runs in one command and shows column types, null rates, and distributions addresses this friction directly. The previous rated build (ctxlog, 3/10) was penalized for requiring manual input — this tool requires zero manual effort: drop in a file, get instant insight.

## Connection to User Context

The user operates The Canada List, a large-scale Canadian business and product directory that involves significant CSV ingestion and QC. They also run a neuroscience lab collecting behavioral and neuroimaging data, and are building quantitative investing systems — all of which regularly produce CSV and JSON files that need quick structural assessment. Writing one-off pandas snippets to check column types, null rates, and distributions is a recurring friction in this workflow. A single command replaces that.

## Why Tonight

Monday calls for a focused utility — polished, self-contained, usable in under 5 minutes. A Python CLI data profiler is a textbook focused utility: one entry point, one module of logic, immediately actionable output. It also fills category F, which has never been built before and doesn't overlap with the last two builds (B, H).

## What I Hope the User Gets From This

1. A command they can run immediately on any CSV or JSON dump to get instant structural understanding — no setup, no library imports, no Jupyter kernel.
2. A replacement for the first 10 lines of every exploratory data analysis script (importing pandas, printing dtypes, checking nulls) — this does it faster with no dependencies.
3. A foundation that can be extended toward the Canada List CSV Quality Inspector idea already in the backlog.

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| Research Data Codebook Generator | F | Narrower use case (academic only); SPSS/R codebook format is too specific for a general utility; harder to test in isolation |
| Neuroscience Flashcard Deck | E | The user is the domain expert — they likely don't need to review their own material; less "time saving" value than a data tool |
| Running Pace & Race Planner | I | Garmin Connect already provides this; the user has the app and uses it; would be a duplicate of an existing tool they carry |
