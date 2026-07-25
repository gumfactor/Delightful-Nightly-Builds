# Why This? — BugTrace: Personal Bug-Pattern Miner

> **Date:** 2026-07-25

---

## How This Idea Was Selected

**Selection method:** Fresh generation.

Day of year 206 → `(206-1) % 9 = 7` → Category H (Developer Tool). The backlog (`builds/ideas.md`) had exactly one pending Category H row (#9, "GitHub Actions Performance Analyzer") with no numeric rating, so `lottery_chance = min(75, 25 + 0*2) = 25%`. Rolled 73 (via `$RANDOM`) — above the 25% threshold, so the fresh-idea path was taken. This also sidestepped a real problem with idea #9: it is now a near-duplicate of the already-built 2026-06-28 `ci-pulse` (GitHub Actions performance analyzer with trend charts and per-job breakdown), so drawing it would have produced a redundant build.

## The Decision

Three Category H candidates were generated (see Alternatives table). BugTrace won because its differentiating layer is AI-driven pattern classification of the user's *own* mistakes over time — not another mechanical report — which directly matches CLAUDE.md's "AI integration signal" guidance and the calibration note's warning against builds a power user could trivially replicate with mechanical data processing alone. It also targets a PROFILE.md learning goal ("Become substantially stronger as a Python developer") that no prior build has addressed directly.

## Connection to User Context

PROFILE.md names "increasingly function like [a software engineer] in practice" despite not being formally trained, "Master AI agent workflows," and "Become substantially stronger as a Python developer" as explicit learning goals, alongside "Building increasingly sophisticated software despite not being a full-time developer" as a named recurring friction point. BugTrace turns the user's own multi-repo commit history (Canada List, Kwyeter, lab tooling, this nightly-build repo) into an evidence-based mirror of which specific mistake types recur, rather than relying on generic advice.

## Why Tonight

Category H falls tonight per the fixed rotation. Four prior H builds (Git Standup Reporter, dep-check, Schema Sentinel, ci-pulse) and one AgentLint build already covered dependency auditing, schema diffing, CI performance, and instruction-file linting — none addressed *why* bugs happen or mined the user's own fix history for a personal pattern. GITHUB_TOKEN-based multi-repo commit mining is a proven, reliable architecture in this build container (used successfully by four prior A/H builds), so tonight reuses that proven data-access pattern for a genuinely new analytical question.

## What I Hope the User Gets From This

1. A concrete, evidence-based answer to "what kind of bugs do I actually write most often" across all their repos, not a guess.
2. A reason to revisit the tool periodically as a personal-growth tracker — if a category's frequency declines over months, that's visible, measurable improvement.
3. A fully-offline mode (local `--repo-path` git log, keyword classifier, zero API keys) so it is useful immediately, with the AI layer as a pure upgrade rather than a hard dependency.

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| Deadweight — AST-based dead code / unused symbol finder for Python | H | `vulture` (an established PyPI package) already solves this well; a homegrown clone risks the same "redundant with existing tools" critique that scored 2026-06-08's Quick Data Profiler a 1/10, without a strong enough differentiating layer to justify rebuilding it. |
| Flaky Test Detector — rerun a pytest suite N times, rank tests by pass/fail variance | H | Genuinely useful but narrow: only valuable for repos that already have an intermittently-failing test suite, which most of the user's current projects don't. Less broadly applicable than a tool that works against any commit history. |
| GitHub Actions Performance Analyzer (backlog #9, lost the lottery draw) | H | Would have been a near-duplicate of the already-built 2026-06-28 ci-pulse build (same data source, same trend-chart/per-job-breakdown framing). Appended a note to the backlog row rather than building it. |

Both non-winning fresh ideas (Deadweight, Flaky Test Detector) were appended to `builds/ideas.md` as new pending rows for future consideration.
