# Manual — Neuro Arcade

## Open it
Open `index.html` in any modern browser (works from disk, also on a phone if you copy the folder or host it yourself). Nothing is uploaded; sessions live in that browser's localStorage.

## Play
Play tab, choose a task, read the instructions, press Start.

| Task | Respond | Trials |
|------|---------|--------|
| Stroop | Ink colour: R, G, B, Y or buttons (4 practice trials first) | 48 |
| 2-back | Space, M or the button when the letter matches two back | 40 |
| Go/No-Go | Space/button for green circle; nothing for red square | 60 |
| Ultimatum | A accept / R reject offers of $1 to $5 out of $10 | 20 |

Esc or Quit abandons a run; nothing is saved.

## Results
Each metric appears with a bar showing your value (dot) against a reference range (dark band ±1 SD, light band ±2 SD). Ranges are approximate teaching values, not clinical norms. The percentile says how you compare with that reference sample; for the Ultimatum game neither answer is better.

Metrics: Stroop interference (incongruent minus congruent RT on correct trials) and accuracy; 2-back d′ (log-linear corrected) and hit RT; Go/No-Go commission rate and go RT; Ultimatum unfair-offer rejection and acceptance by offer.

## Data tab
- **Participant label**: stored with each new session. Use a code, not a name.
- **Export CSV**: one row per trial. Columns: `session_id,task,timestamp,label,seed,trial,condition,stimulus,response,correct,rt_ms`.
- **Import CSV**: merges files from other devices, skipping session ids already present. Metrics are recomputed from the trial rows.
- **Class view**: per label, the mean main metric per task (session count in brackets).
- **Delete all data**: asks for confirmation.

## Timing note
RT is measured from the first animation frame showing the stimulus to the key or pointer event. Device input latency is not corrected, so compare conditions within a device rather than absolute RTs across devices.

## Tests
```
npm install
npx playwright test
```
`playwright.config.js` points to `/opt/pw-browsers/chromium-1194/chrome-linux/chrome`; change `executablePath` (or remove it) on another machine. Test URLs use `?fast=1&test=1&trials=N`, which shortens delays and exposes answer attributes for the scripted player; do not use these for real data.
