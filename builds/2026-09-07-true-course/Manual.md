# Manual — True Course

> **Version:** 1.0 (built 2026-09-07)
> **Complexity:** Ambitious Project

---

## What This Is

True Course is a browser navigation-puzzle game for small-boat seamanship: correcting a heading for wind/current drift, judging a safe tide window, knowing who has the right of way, and reading a buoy correctly. Every puzzle is generated fresh from real navigational math and rules — a current-triangle vector solver, a cosine tide-height model, a COLREGS Rules 13/14/15 geometric classifier, and IALA System B buoyage rules — so there's no fixed content bank to memorize and no puzzle whose "correct answer" was just typed in by hand.

---

## Quick Start

1. Open `index.html` directly in any modern browser (double-click it, or drag it into a browser window). No install, no server, no build step.
2. From the main menu, pick **Voyage Mode** to play the four chapters in order, **Practice** to drill one puzzle type at a time, or **Daily Challenge** for today's fixed 5-round set.
3. Answer each round (numeric heading entry for Set & Drift, multiple choice for the other three), then click **Next** to continue.
4. Check **Mastery Dashboard** any time to see your accuracy per puzzle type and which Voyage chapters you've unlocked.

---

## How to Use It

### Voyage Mode

Four chapters, played in order: **Buoyage → Right of Way → Tide Windows → Set & Drift**. Each chapter is a freshly generated set of rounds (6, 8, 6, and 8 respectively) — replaying a chapter never repeats the same puzzles. Score **70% or higher** on a chapter to unlock the next one. Voyage Mode always resumes at the furthest chapter you've unlocked, so you can jump straight back into new territory without replaying earlier chapters (though you can always choose **Replay Chapter** to practice one again).

### Practice

Pick any one of the four puzzle types and answer an unlimited stream of freshly generated rounds. Good for drilling a specific skill (e.g. only Set & Drift) without the chapter structure.

### Daily Challenge

A single 5-round mix, deterministically generated from the current UTC date — everyone who plays on the same day gets the identical set of puzzles. You get one attempt per UTC day; returning to the Daily Challenge after finishing shows your result instead of a new attempt. After finishing, click **Copy Result** to copy a shareable ✅/❌ score grid to your clipboard.

### Mastery Dashboard

Shows lifetime attempts and accuracy per puzzle type, and whether each Voyage chapter is unlocked.

### Puzzle Types

- **Set & Drift** — Given a desired track, distance, boat speed, and the current's set/drift, type the course to steer (in degrees true). Answers within 2° of the exact computed heading are accepted, since real-world steering has that much slop anyway. After answering, the compass diagram reveals the current vector (orange) alongside your guess (yellow) and the target track (cyan).
- **Tide Window** — Given a low tide and the next high tide (time + height), your boat's draft, a safety margin, and the charted depth, pick the earliest safe departure time from four options.
- **Right of Way** — Given both vessels' headings and the bearing between them, pick who must give way: you, the other vessel (you're stand-on), or both (head-on, both alter to starboard).
- **Buoyage** — Given IALA System B rules ("red right returning," the system used in Canada/US), answer which side to pass a buoy on, what shape it should be, or what color a given buoy number implies.

### First Mate's Log (optional)

After finishing a Voyage chapter or the Daily Challenge, you can paste an Anthropic API key (used only in that browser tab for that one request — never saved, never sent anywhere else) to get a one-line flavor comment on your score. Leave the key field blank and click **Get Note** anyway to see the built-in deterministic version — the game never makes a network call without a key.

---

## Configuration

No configuration required. All state (mastery stats, chapter unlocks, today's Daily Challenge result) lives in your browser's `localStorage`, scoped to wherever you open `index.html` from.

| Setting | Default | Description |
|---------|---------|--------------|
| Set & Drift answer tolerance | ±2° | How close a typed heading must be to the exact computed answer to count as correct |
| Chapter unlock threshold | 70% | Minimum accuracy on a Voyage chapter to unlock the next one |

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| Dashboard shows 0 attempts after playing | A private/incognito window or a browser blocking `localStorage` | Play in a normal browser window; the game still works without persistence, it just won't remember stats across reloads |
| "Get Note" shows the generic First Mate's Log line even with a key entered | No `ANTHROPIC_API_KEY`, an invalid key, or no network access from the browser | This is the intended graceful fallback — the deterministic note always appears when the AI call can't complete |
| Daily Challenge shows "already complete" and won't let you replay | You already played today's Daily Challenge (UTC date) | Come back after 00:00 UTC for a new one, or use Practice/Voyage Mode in the meantime |

---

## Known Limitations

- The Tide Window puzzles use a simplified cosine (harmonic) approximation between one known low and high tide — it is a real, commonly-taught navigational estimation technique, but it is not tide-table-grade precision for actual trip planning.
- Right of Way covers COLREGS Rules 13/14/15 for two power-driven vessels only; sailing-vessel rules (Rule 12) are out of scope.
- IALA System B buoyage only (used in Canada/US) — IALA System A (used in most of the rest of the world) is not covered.
