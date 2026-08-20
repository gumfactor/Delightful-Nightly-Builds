# Manual — Fairway Physics

> **Version:** 1.0 (built 2026-08-20)
> **Complexity:** Ambitious Project

---

## What This Is

Fairway Physics is a browser golf game where every shot is resolved by a real, hand-built physics model instead of luck or a scripted animation. Pick a club, set your power and aim, choose a shot shape (draw/fade/straight), and the engine computes carry distance, wind drift, elevation effect, and post-landing roll to determine exactly where the ball ends up — including realistic consequences like a stroke-and-distance penalty for a shot that finds water or goes out of bounds. Play a 9-hole **Daily Round** (same wind for everyone on a given day, one attempt per day, shareable emoji scorecard) or grind any single hole repeatedly in **Practice** mode.

---

## Quick Start

1. Open `index.html` directly in a browser (double-click it, or drag it into a browser window) — no install, no server needed.
2. Click **Play Daily Round** for today's 9-hole round, or pick a hole from the dropdown and click **Start Practice** to practice one hole repeatedly.
3. Pick a club, set power/aim/shot shape, and click **Take Shot**.
4. Once your ball is on the green, use the **Putt Power** and **Break Aim** sliders and click **Putt** until the ball is holed.
5. After 9 holes in Daily Round mode, review your scorecard and copy the shareable result.

---

## How to Use It

### Taking a Shot

- **Club** — Driver (longest) down to Pitching Wedge (shortest); the putter only appears once you're on the green.
- **Power** — 0–100%, scales the club's carry distance linearly.
- **Aim** — degrees left/right of the direct line to the pin.
- **Shot Shape** — Straight, Draw (curves left), or Fade (curves right); the curve grows with shot distance.
- Wind (shown above the course view) affects both distance (headwind/tailwind) and lateral drift (crosswind) — bigger effect on longer clubs.
- If your ball lands in water or out of bounds, you'll see a penalty message and the ball returns to where you hit from, plus one penalty stroke (standard stroke-and-distance rule).

### Putting

Once your ball's lie shows "green," the shot controls are replaced by putting controls: **Putt Power** (how hard) and **Break Aim** (compensating for the green's built-in slope). A putt that finishes within about half a yard of the pin holes out.

### Daily Round vs. Practice

- **Daily Round** — Wind for each hole is seeded from today's UTC date, so it's the same for every attempt today but different tomorrow. You get one completed round per UTC day; finishing shows a scorecard with a shareable emoji-grid result you can copy.
- **Practice** — Pick any of the 9 holes and play it as many times as you like. Wind defaults to calm; click **Shuffle Wind** for a random condition. Practice completions don't touch the Daily Round gate, but they do feed your per-hole stroke averages.

### Ask the Caddie

An optional strategy tip. Leave the API key field blank for a solid rule-based tip (distance/hazard-aware, computed instantly, no network call). Paste in your own Anthropic API key (never saved — it lives only in the page for this session) for a short AI-generated tip instead. If the API call fails for any reason, the rule-based tip is shown automatically.

### Stats

Click **Stats** in the header to see rounds completed, your best round score relative to par, practice holes completed, and your average strokes per hole across every round and practice session you've played on this device.

---

## Configuration

| Setting | Default | Description |
|---------|---------|--------------|
| Anthropic API key | (empty — deterministic caddie tips) | Enter your own key in the "Ask the Caddie" panel to get AI-generated strategy tips instead of the rule-based fallback. Held in memory only, never written to storage. |

No other configuration is required — the course, physics constants, and daily-seed logic are all built in.

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| "Play Daily Round" is missing, only "View Today's Result" shows | You already completed today's Daily Round (UTC date) | Come back after midnight UTC, or play Practice mode in the meantime |
| Ask the Caddie always shows the rule-based tip even with a key entered | The key is invalid, or the network request failed | Double-check the key; the app always falls back safely rather than showing an error, by design |
| Stats show `—` for a hole's average | You haven't completed that hole yet (in either mode) | Play that hole at least once — averages populate after the first completion |
| Progress seems to have reset | Stats and the daily gate are stored in `localStorage`, which is scoped per browser profile and device | Play from the same browser/profile you started in; clearing browser data will reset progress |

---

## Known Limitations

- Hazard and fairway/rough zones are rectangles, not true polygons — doglegs are approximated with two adjoining rectangles rather than a smoothly curving corridor.
- Elevation change is a single value per hole applied identically to every shot on that hole, not the true remaining elevation from the ball's current position.
- Wind is constant across an entire Daily Round hole (fair and repeatable, but not gusty/variable shot-to-shot).
- No true 3D ball flight — the canvas shows a top-down 2D view with an animated flight-path line, not a realistic arc.
