# WhyThis — GitHub Developer Activity Explorer

## Decision path

- **Category tonight:** F — Data Explorer (day 177, index 5)
- **Lottery:** 2 pending ideas in category F (IDs 1 and 10). R=1 (one has a numeric rating). lottery_chance = min(75, 25 + 1×2) = 27%. Roll: 77 > 27 → **fresh ideas**.
- **Idea brief consulted:** None (fresh generation)

## Fresh idea candidates

Three options were generated for category F:

1. **GitHub Developer Activity Explorer** ← SELECTED  
   Pull full commit history via GITHUB_TOKEN, visualize personal coding patterns (hour-of-day, day-of-week, weekly trend, repo focus), compute streaks, and generate an AI developer profile via Claude Haiku. Self-contained HTML dashboard with Chart.js.

2. **Canada List Business Data Explorer**  
   Browser tool to upload a Canada List CSV export and get interactive visual analysis: province breakdown, sector distribution, completeness scoring, quality flags, downloadable cleaned output. Similar concept to the Qualtrics Inspector (rated 9) applied to the user's main business project. Added to ideas.md.

3. **Open-Meteo 5-Year Climate Explorer**  
   Pull 5 years of historical weather from Open-Meteo for Toronto and visualize seasonal patterns: average temperatures by month, year-over-year running/golf/boating comfort score trends, best and worst weeks historically. Added to ideas.md.

## Why this idea won

The GitHub Developer Activity Explorer was selected because:

1. **Genuine gap vs. GitHub's own UI.** GitHub's contribution graph shows daily commit counts in a 52-week heatmap. It does not show: time-of-day distribution, day-of-week patterns, repo focus evolution over time, or streak analytics. This build fills that gap.

2. **Real data, no upload required.** Uses GITHUB_TOKEN (always available) to fetch live data rather than requiring a file upload or manual entry. The data is guaranteed to exist and be fresh.

3. **AI differentiation.** The Anthropic API generates a developer profile from the pattern data — something like "You code almost exclusively on weeknights after 9pm, with Tuesday being your highest-output day..." This is the kind of language GitHub will never write for you.

4. **Pattern: research-quality data tools score high.** The Qualtrics Survey Data Inspector (F category, research QC tool) rated 9/10 — the highest score in the catalog. GitHub developer pattern analysis is the same archetype: turn raw data into actionable insight, presented visually. The profile is a developer, not a researcher, but the principle is identical.

5. **Not investment/finance.** Investment/finance has appeared 4 times in the last 10 builds and is saturated per the diversity check rule.

6. **Self-contained output.** The HTML report can be opened, shared, or saved anywhere. No server, no dependencies beyond the CDN Chart.js import.
