# Future Features — Run Planner

## 1. Garmin Connect Integration (via Garmin API or GPX import)
Accept `.gpx` or `.fit` file exports from Garmin Connect and auto-populate runs with actual GPS distance, pace, cadence, heart rate, and elevation. Eliminates manual entry entirely — you run, sync Garmin, run `python src/main.py import --gpx ~/Downloads/run.gpx`.

## 2. Training Load Score & Ramp Rate Warning
Compute weekly training load (distance × effort multiplier: easy=0.7, moderate=1.0, hard=1.3) and calculate the week-over-week ramp rate. Show a warning when ramp rate exceeds 10% — the standard threshold for injury risk. Surface this prominently in both the CLI `week` output and the HTML report.

## 3. Pace Trend Chart in HTML Report
Add a second Chart.js line chart to the HTML report showing pace over the last 30 individual runs, with a moving average overlay. Lets you see at a glance whether fitness is improving — the core metric a competitive runner cares about.

## 4. Race Goal Pace Predictor
Given a recent race or time trial result (e.g., `--race 5k --time 22:30`), compute predicted finish times for 10k, half-marathon, and marathon using the Riegel formula. Output a target pace band for each race distance. Stored in the JSON data file as a goal entry.

## 5. Location Support for Multiple Cities / Coordinates
Add a `config.json` in the build folder storing a default lat/lon and city name. Support named locations (`--location cottage` → pre-saved coordinates for cottage country, `--location toronto` → default). Eliminates having to remember coordinate values.

## 6. Weekly Email/Notification Summary (as a Claude Code Routine)
Package the `week` and `plan` outputs as a scheduled Claude Code Routine that runs every Sunday evening, generates a Markdown summary of the past week's training and the upcoming week's best windows, and delivers it via the Anthropic API to a Claude conversation or as a webhook notification. Turns this from a pull tool into a push tool.

## 7. Best Run Conditions Historical Correlation
After 30+ runs are logged, correlate weather conditions at run time (stored by extending `log_run` to optionally fetch and record weather) with pace outcomes. Show whether this runner performs better at 8°C vs 18°C, or whether wind has a measurable pace penalty for them personally. Personalizes the weather scoring algorithm to actual data rather than generic comfort ranges.
