# Manual — Earshot

> **Version:** 1.0 (built 2026-08-14)
> **Complexity:** Ambitious Project

---

## What This Is

Earshot is a browser dashboard that measures real ambient sound level from your device's microphone, classifies it against published noise-safety guidance, and tracks venue-tagged noise sessions and a running daily exposure dose over time. It's a working first cut of Kwyeter's core mechanic — "how loud is this place, and is it safe to be here" — built as a fully local, single-file-opens tool with no server and no data ever leaving your browser except the optional AI briefing call you explicitly trigger.

---

## Quick Start

1. Open `index.html` directly in a browser (double-click it, or `open index.html` / drag it into a browser window).
2. On the **Live Meter** tab, click **Start Measuring** and allow microphone access when prompted.
3. Watch the live dB(A) reading, zone badge, and rolling chart update in real time.
4. Click **Stop Measuring**, enter a venue name, and click **Save Session**.
5. Switch to the **History** tab to see your saved session, its trend, and your running daily noise dose.

---

## How to Use It

### Live Meter

Shows the current sound level (dB(A), approximate), a color-coded zone badge (Quiet / Moderate / Loud / Hazardous), and a 60-second rolling chart. Readings are **uncalibrated by default** — a banner says so, and the reading itself is labeled "(uncalibrated)" until you calibrate. Stopping a measurement shows an average/peak/duration summary and lets you save it with a venue name (required) and an optional note.

### Calibration

Microphone sensitivity varies a lot by device, so a raw reading isn't a trustworthy absolute sound level out of the box. To calibrate: click **Start Calibration Sampling**, get a known reference value while the same sound is playing (either another sound-meter app/device, or a documented rule-of-thumb reference — e.g. "normal conversation ≈ 60 dB", "quiet library ≈ 40 dB"), enter that reference number, and click **Set Offset**. Every future reading is shifted by that offset. You can re-calibrate any time, or **Reset Calibration** to go back to relative-only readings.

### History

A searchable, sortable table of every saved session (click any column header to sort, type in the search box to filter by venue). Click a row to open its detail panel: venue, note, avg/peak/duration/dose, and a mini chart of that session's own dB-over-time curve. A **Trend** chart above the table shows average dB per session across your whole history. The banner at the top shows your cumulative noise-exposure dose over the last 24 hours, with a plain-language safety message.

### AI Briefing (optional)

On a session's detail panel, paste an Anthropic API key (never saved — it lives only in the page's memory for that session) and click **Get AI Briefing** for a plain-English summary of that session's exposure. Only the session's aggregate numbers (venue label, avg/peak dB, duration, dose %) are ever sent — never raw audio or the per-second chart data. Without a key, you still get a useful deterministic summary built from the same numbers, with zero network calls.

---

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| Calibration offset | 0 dB (uncalibrated) | Set via the Calibration tab; stored in `localStorage`. |
| Anthropic API key | Not set | Entered per-session in the History detail panel; never persisted, never sent anywhere except `api.anthropic.com` when you click "Get AI Briefing". |

No configuration files or environment variables are required to run the tool itself.

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| "Microphone access was denied or is unavailable" | Browser permission denied, or no microphone present | Check your browser's site permissions and grant microphone access, then click Start Measuring again. |
| Readings look implausibly negative or positive | You haven't calibrated yet — the default offset assumes typical mic sensitivity, which varies by device | Calibrate on the Calibration tab against any known reference. |
| Chart looks flat / pinned to one edge | The dB values are outside the chart's fixed 30-110 dB display range (usually because you're uncalibrated) | Calibrate, or just watch the numeric reading — the chart's fixed scale is a display choice, not a measurement limit. |
| AI Briefing always shows the template text | No API key entered, or the request failed | Enter a valid Anthropic API key; check your network connection. |

---

## Known Limitations

- **Not a calibrated sound-level meter.** The A-weighting applied here is a simplified approximation (a small lookup table of standard octave-band correction values, linearly interpolated), not a full IEC 61672 filter bank. Combined with the fact that consumer microphone gain is not standardized, Earshot's dB readings should be treated as relative and useful for trend-spotting, not as clinically or legally authoritative sound-pressure-level measurements.
- **Calibration is manual and per-device.** There's no automatic detection of microphone hardware or gain; you calibrate once per device against whatever reference you have on hand, and it's only as accurate as that reference.
- **No cross-device sync.** All data lives in one browser's `localStorage`. Opening Earshot on a different device or browser starts a fresh, empty history.
- **The meter only runs while the tab is open.** There's no background monitoring or notifications — it's a foreground instrument you start and stop deliberately.
- **Exposure dose uses a simplified continuous model.** The NIOSH 3 dB exchange-rate formula is applied to each session's *average* level over its full duration, not a true continuously-integrated dose across fluctuating levels within the session — a reasonable approximation for a short session, less precise for a very long, highly variable one.
