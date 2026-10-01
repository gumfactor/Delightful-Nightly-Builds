# Manual — Noise Lab

## Open it
Double-click `index.html` (or open it from your phone's file browser). No server, install or build step. Works offline.

## Use it
1. **Pick a preset** or shape your own with Colour (slope: 0 white, 1 pink, 2 brown), Low cut and High cut.
2. **Press Play.** It fades in over 2 seconds. Start with the volume low and raise it slowly.
3. The **spectrum** and the **RMS / A-weighted / peak** numbers describe the exact loop you are hearing. They are in dBFS (relative to digital full scale at your chosen volume), not SPL.
4. **Sleep timer:** choose a duration; volume holds, then fades over the last 30 seconds and stops.
5. **Advanced:** notch (centre, width, depth), two boost/cut bands, and three slow swells. Swell rates snap to whole cycles per ~6 s loop so the loop never clicks.
6. **Tinnitus pitch match:** play the quiet test tone, slide until it matches your tinnitus, press "Centre notch on this pitch". This is an experimental research approach, not treatment. Ask an audiologist.
7. **Export:** WAV of the seamless loop (about 6 s, loops without a gap in most players), 1 minute, or 10 minutes. Stereo, 16-bit, at your current volume setting.
8. **Copy link:** puts the whole sound in the URL. Opening that link restores it. A broken link falls back to the Focus preset.

## Run the tests
```
npm install
npx playwright test
```
The Playwright config points at `/opt/pw-browsers/chromium-1194/chrome-linux/chrome`; set `CHROMIUM_PATH` to use another Chromium.

## Limits
- Not a calibrated meter. Real loudness depends on your headphones and phone volume.
- Sample rate follows the browser's audio output (typically 44.1 or 48 kHz). The first tone/loop is built at 44.1 kHz and the browser resamples if needed.
- Changing a slider rebuilds the loop in about 150 ms and crossfades during playback.
