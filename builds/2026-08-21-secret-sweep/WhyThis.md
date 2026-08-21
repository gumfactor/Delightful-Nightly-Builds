# Why This? — Secret Sweep

> **Date:** 2026-08-21

---

## How This Idea Was Selected

**Selection method:** Fresh generation.

The Category H (Developer Tool) backlog in `builds/ideas.md` held exactly one `pending` row matching tonight's category (#9, "GitHub Actions Performance Analyzer"), and its description turned out to be a verbatim duplicate of the already-built `ci-pulse` (2026-06-28) — same mechanism (GITHUB_TOKEN → per-workflow avg/p95 duration, failure rates, trend charts), just written up in the backlog a month before ci-pulse actually got built. Corrected its status to `skipped` with a note rather than let it survive to a future lottery draw. That emptied the Category H pool entirely, so per Step 2c the lottery was skipped and Step 2d (fresh generation) ran directly — no roll was needed since there was nothing left to draw from.

## The Decision

Scanned the last 10 builds and all 8 prior Category H builds specifically (Git Standup Reporter, dep-check, ci-pulse, Schema Sentinel, AgentLint, BugTrace, Landing Pattern, Snipvault) before generating candidates. Every one of them is either dependency/CI hygiene, schema/data diffing, instruction-file linting, or git-history mining for bug patterns or decision logs — none touch security or credential hygiene, which is a real and distinct developer-tool subdomain. Generated three candidates (secret scanner, dead-code finder, type-hint coverage auditor — full list below) and picked the secret scanner: it's the only one of the three where finding something actually changes what the user needs to do next (rotate a key), versus the other two which are code-quality nice-to-haves. Given the explicit calibration note in CLAUDE.md that low scores correlate with builds that don't clear a real bar of usefulness, "did I ever leak a credential" clears that bar more decisively than "is this function reachable."

## Connection to User Context

PROFILE.md names AI-assisted coding across "many simultaneous projects" (The Canada List, Kwyeter, lab infrastructure, this very nightly-build repo) as the user's actual working mode, explicitly using ChatGPT, Claude, Codex, and Copilot daily, and separately names "Managing many simultaneous projects" and "Context switching between academic and entrepreneurial roles" as recurring friction points. AI-assisted, high-velocity, multi-repo development is exactly the profile most likely to accidentally commit a `.env` value, a hardcoded key pasted into a debugging session, or a config file that was supposed to be gitignored — and the more repos and the faster the pace, the less likely any one of them gets manually audited. This build is the first in the catalog to apply the "mine full git history, not just the current tree" pattern (already proven by Waymark and BugTrace) to security rather than decision logs or bug patterns.

## Why Tonight

Day-of-year rotation put tonight at Category H (index 7 of 9). No direct sequel to a specific prior build, but it explicitly closes a gap: this repo's own STANDARDS.md hard-codes a security checklist ("No credentials, API keys, or passwords hardcoded in source files") that every nightly build session is supposed to self-check by hand every night — Secret Sweep is the first build that turns that specific checklist item into a reusable, automated tool the user can point at any of their repos, not just this one.

## What I Hope the User Gets From This

1. A genuine "oh, I should rotate that" moment on at least one of their real repos — the tool is designed to find exactly the kind of history-only leak that a quick `grep` of the current tree would miss entirely.
2. A tool that respects the sensitivity of what it's looking for: every report format is redacted by construction, so running it and sharing the HTML report (e.g. pasting into a Slack message to a collaborator) can't itself become a new leak.
3. A companion Skill for the fast path (pre-commit sanity check mid-session) without forcing a full, slower history walk every time — matching how the user actually works day to day.

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| Dead Code / Unreachable Symbol Finder — Python CLI that builds an import + call graph via AST and flags functions/classes never referenced elsewhere, with confidence scoring for `__all__` exports, test-only usage, and dynamic-dispatch caveats | H | Genuinely useful and novel (no prior build does this), logged to `builds/ideas.md` for a future night. Passed over because it's a code-quality nice-to-have, not something that changes what the user does next the way a live credential leak does — a closer fit for a "solid" complexity night than the strongest possible "ambitious" pick tonight. |
| Type Hint Coverage & Drift Auditor — computes % of functions with complete type hints across a repo, flags coverage regressions commit-over-commit via git history, HTML report with hotspots | H | Reasonable and on-theme with PROFILE.md's "Become substantially stronger as a Python developer" learning goal, but thematically the weakest of the three — a metrics dashboard for a stylistic preference, not a tool that surfaces something actionable the user didn't already know they were missing. Logged to `builds/ideas.md`. |
| API Surface / Breaking-Change Detector for Python packages (AST-diff public signatures between two git refs) | H | Considered but not logged — too structurally similar to the already-built Schema Sentinel (2026-07-07), which already does "diff two snapshots, classify breaking/risky/safe" for JSON/CSV/git-history schemas; applying the identical shape to Python signatures specifically would read as a near-duplicate rather than a genuinely new capability. |
