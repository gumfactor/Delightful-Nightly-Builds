# CanPulse Manual
## Run
```
python3 src/main.py              # fetch live data, write dashboard.html, open it in a browser
python3 src/main.py --offline    # re-render from data/cache.json (or illustrative sample data)
python3 src/main.py --no-ai      # skip Claude briefing
python3 src/main.py --verify     # confirm StatCan vector IDs match expected series titles
```
Set `ANTHROPIC_API_KEY` for an AI briefing (only aggregate public statistics are sent); otherwise a rule-based briefing is shown. No other dependencies.
**First thing to do:** run `--verify` once. Vector IDs live in `src/canpulse/config.py` and could not be checked from the build container (network blocked). A wrong ID shows as an "Unavailable" card, not a crash.
## Using the page
Tap a card for the detail chart; use 1Y/5Y/10Y/Max; "Compare" rebases two series to 100. Badges are rule-based (good/bad/watch/neutral), not forecasts. "Stale" means the last observation is older than expected. The committed `dashboard.html` shows illustrative sample data (banner shown).
## Tests
`python -m pytest tests/ -v` (needs pytest) and `npm install && npx playwright test` (set `CHROMIUM_PATH` if needed). Tests use no network.
