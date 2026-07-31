# WhyThis — Project Pulse

## Lottery or Fresh?

Fresh generation. No pending Category I (Life Admin Helper) ideas in the backlog.

Roll: N/A (skipped — pool empty)
Pool size: 0

## Category

I — Life Admin Helper
Day of year: 180 → category_index = (180-1) % 9 = 8 → Category I

## Topic Diversity Check

Last 10 builds by domain:
- GitHub/developer tools: 4 (dep-check, GitHub Health Scorecard, GitHub Activity Explorer, ci-pulse)
- Academic productivity: 3 (Paper Lens, AI Lecture Builder, Stats Coach)
- Gaming: 2 (Regex Dojo, Neurofact)
- Fitness: 1 (Run Planner)
- Productivity: 1 (Morning Briefing)
- Investment/finance: 0 in last 10

GitHub tooling is saturated. Academic tools are saturated. Fitness was covered by the only prior Category I build (Run Planner).

## The Three Candidates

1. **Project Pulse** ← selected
   Multi-project context manager: define projects in SQLite, sync GitHub commits automatically, generate AI context briefs for switching, HTML dashboard with staleness indicators. Directly solves "managing many simultaneous projects" and "context switching between academic and entrepreneurial roles" — PROFILE.md friction points 2 and 3.

2. **Academic Grant & Deadline Calendar** (→ added to ideas.md)
   Track grant deadlines, ethics submissions, manuscript stages. HTML calendar view. AI-generated application checklists. Narrow focus limits daily use.

3. **Personal Finance Tracker (Canadian)** (→ added to ideas.md)
   Budget tracking with CAD/USD support, Statistics Canada CPI data, spending breakdown charts. The user likely has financial tooling already; unclear how much daily admin value this adds.

## Why Project Pulse Wins

The user explicitly lists "Managing many simultaneous projects" and "Context switching between academic and entrepreneurial roles" in PROFILE.md's friction points. They run 6+ simultaneous projects across completely different domains (lab, Canada List, Kwyeter, teaching, AI builds, investing) — and no existing tool in their stack (Teamwork.com, GitHub, MyFitnessPal, Garmin) gives a unified cross-project activity view with AI-powered context restoration.

The AI brief is the differentiating layer. Without it, this is a project tracker (Teamwork already does this). With it, you can open a terminal and in one command have a 3-5 sentence brief that restores working memory for any project — something that currently takes 5-15 minutes of reading back through notes and code.

The HTML dashboard surfaces staleness — which projects have gone quiet — something no tool currently shows across academic + code + writing domains simultaneously.

## Calibration Note

The lowest-scoring builds failed by (a) lacking visual interface, (b) using mock data, or (c) duplicating existing tools. This build:
- Has visual interface: Chart.js stacked bar timeline + project cards ✓
- Uses real data: GitHub API via GITHUB_TOKEN + Anthropic API ✓
- Doesn't duplicate existing tools: Teamwork tracks tasks; this tracks cross-domain project activity and restores context ✓
