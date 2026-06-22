# Future Features — Morning Briefing

## 1. Claude Code Routine Integration
Package the script as a proper Claude Code Routine with a `routine.md` configuration file. The Routine would run every morning at 7:00 AM ET, generate the HTML report, and push a `PushNotification` with the headline (e.g., "3 repos active, NVDA +4.6%, good run window at 9am"). This turns the briefing from a tool the user must remember to run into a pull tool that arrives automatically.

## 2. Persistent Watchlist CLI
Add a `python src/main.py watchlist add TICKER` and `remove TICKER` command that edits `config.json` in place. Right now the watchlist is only editable by hand. A quick `morning-briefing watchlist add GOOG` would make the config feel more like a living tool and less like a config file to maintain.

## 3. Week-Over-Week Digest Mode
Add a `--weekly` flag that generates a Sunday digest: 7 days of commit activity across repos, 5-day portfolio performance, weather summary for the week past. Store each day's raw data in `output/data/YYYY-MM-DD.json` before generating the report so the weekly mode can reconstruct the trend without re-fetching.

## 4. GitHub Commit Detail Layer
Currently only the "repos with recent pushes" level is shown. Add an optional `--commits` flag that fetches the last 5 commit messages per active repo and includes them in the GitHub section. Useful for reconstructing exactly what was done yesterday when resuming a session. Rate-limit this with a per-repo cache TTL stored in `output/cache/`.

## 5. Configurable Activity Profiles
Add a `profiles` section to `config.json` that lets the user define named activity profiles (e.g., `"marathon_training"` with different temperature/wind thresholds than the default). Selected via `--profile marathon_training`. The scoring functions accept a config dict so this is mostly a config schema addition.

## 6. SEC EDGAR Earnings Calendar Integration
Pull upcoming earnings dates for watchlist tickers from SEC EDGAR (no auth) and highlight any earnings in the next 5 business days in the portfolio section. Currently the briefing doesn't flag "NVDA reports tomorrow" — this would close that gap.

## 7. AI Summary Caching
The AI synthesis call costs tokens every run. Cache the AI summary to `output/cache/YYYY-MM-DD-ai.txt` and reuse it for the rest of the day (identified by date + a hash of the input data). Only re-generate when the data changes meaningfully. This enables `--refresh` to force regeneration while keeping routine runs cheap.
