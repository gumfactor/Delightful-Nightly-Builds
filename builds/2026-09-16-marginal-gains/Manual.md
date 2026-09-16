# Manual — Marginal Gains

> **Version:** 1.0 (built 2026-09-16)
> **Complexity:** Ambitious Project

---

## What This Is

Marginal Gains is a browser puzzle game about the real skill of splitting a limited number of hours across several competing projects, each with diminishing returns. Every round draws a handful of flavor-text projects (grant reports, manuscript revisions, course prep, lab supervision, Canada List work, and more), gives you a weekly hour budget, and asks you to allocate it. When you lock in, the game compares your allocation to the mathematically optimal one — computed live by a real dynamic-programming solver, not a hardcoded answer — and shows you exactly where you left points on the table.

---

## Quick Start

1. Open `index.html` directly in any modern browser (double-click it, or drag it into a browser window). No install, no server, no internet connection required.
2. Click **Tutorial** first if this is your first time — it walks through the diminishing-returns curve on one example project.
3. Click **Daily Challenge** for today's puzzle (same for everyone, resets at 00:00 UTC, one attempt per day) or **Practice** to pick a difficulty and play as many rounds as you like.
4. Use the **-5 / -1 / +1 / +5** buttons on each project card to allocate hours. Watch the budget bar at the top.
5. Click **Lock In Allocation** once you're happy (it's disabled if you've gone over budget) to see your score.

---

## How to Use It

### Tutorial

A single example project ("Grant Progress Report") with a slider from 0 to its max useful hours. Drag it to see the value curve update live on the chart and the "next hour adds" readout drop as you allocate more — this is the core intuition the whole game is built on.

### Daily Challenge

A fixed 6-project, 40-hour round, the same for everyone on a given UTC calendar day (seeded from the date, not random). You get exactly one attempt per day; the Home screen shows your grade once you've played and blocks a second attempt until the next UTC day. After locking in, a shareable text result (grade, % of optimal, and a colored emoji grid showing how close each project was to optimal) appears under the results table.

### Practice

Pick a difficulty — Light (4 projects / 24h), Standard (6 projects / 40h), or Heavy (8 projects / 56h) — and play as many freshly randomized rounds as you want. Nothing here is saved to a daily gate.

### Results & Scoring

After locking in, you see:
- A letter grade (S/A/B/C/D/F) and your score as a percent of the optimal total
- A per-project table comparing your hours/value to the optimal hours/value
- An **AI Advisor** note — a plain-English coaching tip computed from the real numbers above. Without an API key, it always shows a deterministic note (e.g. "You left N points on the table by putting Xh into Project instead of the optimal Yh"). If you paste your own Anthropic API key into the field (never saved anywhere — it lives only in that page's memory for that session) and click **Get AI Coaching**, the game calls the Anthropic API directly from your browser for a short natural-language version of the same coaching.

### Mastery Dashboard

Tracks every round you've completed in this browser (via `localStorage`, so it's private to this machine and this browser): total rounds played, your average % of optimal, your current and best Daily Challenge streaks, and a per-category (Research / Teaching / Admin / Writing / Ventures) breakdown of how well you tend to allocate hours in each.

---

## Configuration

No configuration required. The optional Anthropic API key field on the Results screen is the only "setting," and it's entered per-session — nothing to edit in code or a config file.

| Setting | Default | Description |
|---------|---------|-------------|
| Anthropic API key | none | Optional, entered on the Results screen. Enables the live AI Advisor call. Never persisted. |

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| Daily Challenge button is grayed out | You already completed today's UTC-dated challenge | Come back after 00:00 UTC, or play Practice mode in the meantime |
| "Lock In Allocation" stays disabled | Your total allocated hours exceed the budget shown in the bar | Reduce hours on one or more projects until the bar is no longer red |
| AI Advisor just shows the deterministic note even after clicking "Get AI Coaching" | No API key was entered, the key is invalid, or the request failed | Double-check the key; the game always falls back to the deterministic note rather than showing an error, by design |
| Dashboard shows "Play a round to see category performance" | No rounds completed yet in this browser | Play at least one Practice or Daily round |
| Progress/streaks disappeared | Browser storage was cleared, or you're in a private/incognito window | Expected — `localStorage` is per-browser-profile and not synced anywhere |

---

## Known Limitations

- The project pool is illustrative flavor text (Grant Progress Report, Manuscript R&R, etc.), not a live import of your actual tasks — see `FutureFeatures.md` for the path toward a real-task-import mode.
- Progress, streaks, and history live only in the current browser's `localStorage` — clearing site data or switching browsers/devices resets them.
- The AI Advisor requires you to supply your own Anthropic API key each session; the game never ships or stores one.
