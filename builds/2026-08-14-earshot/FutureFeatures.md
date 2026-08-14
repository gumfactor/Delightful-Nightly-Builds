# Future Features — Earshot

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **Auto-detect a plausible starting offset from device type** — Use `navigator.userAgent`/`navigator.platform` to nudge the default (still clearly labeled "uncalibrated") baseline offset toward a more plausible starting range for common device classes (laptop mic vs. phone mic), while keeping the honest "uncalibrated until you set a real reference" framing.
2. **Export session history as CSV/JSON** — A one-click download of all saved sessions for use in a spreadsheet or another tool, mirroring the export pattern several other builds in this catalog already use.
3. **Configurable dose reference standard** — Toggle between the NIOSH 85 dB/8hr (used here) and the more conservative WHO/EU 80 dB reference, since different jurisdictions and use cases (occupational vs. recreational/leisure noise) use different thresholds.
4. **"Reset all data" button** — A single confirm-gated action to clear the entire local history, for testing or starting fresh, without needing to delete sessions one at a time.

## Medium Effort (roughly one nightly build session)

5. **True full-order A-weighting filter** — Replace the simplified octave-band lookup-table approximation with a proper IEC 61672 A-weighting IIR filter applied to the raw audio stream before RMS computation, meaningfully closing the gap toward genuinely calibrated-grade accuracy.
6. **Guided calibration wizard with common reference presets** — A short in-app flow offering documented reference levels (library ≈ 40 dB, conversation ≈ 60 dB, busy street ≈ 80 dB) with brief instructions, rather than requiring the user to already know or find a reference value themselves.
7. **Per-venue aggregate view** — Group History by venue name (with fuzzy/normalized matching for near-duplicate venue names) to show "this place is typically X dB" over repeated visits, which is much closer to Kwyeter's actual "venue-level noise information" product vision than a flat session list.

## Ambitious Extensions (multi-session effort)

8. **Kwyeter venue database backend** — The real long-term direction: a shared, crowdsourced venue-noise database (with a backend service, user accounts, and moderation) that this local tool's measurement/calibration/classification engine could feed into, turning "my own measurements" into "everyone's measurements at this venue."
9. **Background/ambient monitoring with local notifications** — A persistent-tab or (eventually) native/PWA mode that monitors continuously and proactively surfaces a notification when the current environment crosses into Loud/Hazardous territory, rather than requiring the user to manually start a session — directly serving the "sensory sensitivities, tinnitus" accessibility use case named in PROFILE.md.

---

## Possible Integration Points

- **Dockside (2026-08-04)** and **TripKit (2026-07-26)** both already integrate Open-Meteo weather data into activity/trip planning for the same user; a future "quiet/loud venue" layer alongside weather comfort scoring could plausibly live in a combined "environment awareness" tool if Kwyeter grows toward that.
- No other prior build in this catalog touches audio, hearing, or Kwyeter at all — this is the first foundation for that entire product line.

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| A-weighting is a coarse octave-band approximation, not a true filter | Implement a proper IEC 61672 A-weighting IIR filter (see Ambitious Extensions #5) |
| No cross-device history sync | Would require a backend/account system — see Ambitious Extensions #8, which is the natural place this belongs |
| Dose model uses per-session average rather than continuous integration | Sample-level dose integration during the live session, summed continuously rather than computed once from the average at save time |
| Calibration requires the user to already have or find a reference value | Guided calibration wizard with documented presets (see Medium Effort #6) |
