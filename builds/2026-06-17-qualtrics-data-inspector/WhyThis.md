# WhyThis.md — Qualtrics Survey Data Inspector

## Lottery Result

- **Rotation:** Day 168 → category index 5 → **F — Data Explorer**
- **Pending F ideas:** 1 (ID 1: Canada List CSV Quality Inspector, rating 7)
- **R (rated pending ideas):** 1
- **Lottery chance:** min(75, 25 + 1×2) = **27%**
- **Roll:** 74
- **Result:** 74 > 27 → **Fresh ideas path**

## Ideas Generated

| Rank | Title | Why considered | Why not chosen |
|------|-------|---------------|----------------|
| 2 | GitHub Actions Performance Analyzer | GITHUB_TOKEN available, dev workflow focus | Developer tool angle fits category H better; less daily impact than lab data |
| 3 | SEC EDGAR Financial History Extractor | Public API, finance interest | Investment builds are saturated (4 of last 7); user doesn't need another finance tool tonight |
| **Winner** | **Qualtrics Survey Data Inspector** | **Directly addresses daily lab workflow; domain-specific; saves real time** | — |

## Why the Qualtrics Inspector Won

The user runs a neuroscience lab and processes Qualtrics survey data constantly. Every dataset requires manual inspection before statistical analysis: checking for incomplete responses, timing anomalies, attention check failures, missing data patterns, and scale reliability. This is currently done manually — a mix of pandas exploration and eyeballing.

The discarded Jun 8 Quick Data Profiler (rated 1) was "totally redundant with pandas df.describe()." This build is explicitly not that: it understands Qualtrics's 3-row header format, recognizes psychological scale structure, computes Cronbach's alpha, and flags researcher-relevant quality issues (straight-lining, fast responders, duplicate IPs). pandas.describe() knows nothing about any of this.

Alignment with PROFILE.md priorities:
- Saves real time (QC that takes 30 minutes → 2 minutes)
- Daily/weekly utility (every new dataset)
- Connects to a named recurring friction point: "Student evaluation workflows" and "Research administration"
- Python only, stdlib only — matches preferred stack, no install friction

## Non-Winners Appended to ideas.md

- ID 9: GitHub Actions Performance Analyzer (category H, ambitious)
- ID 10: SEC EDGAR Financial History Extractor (category F, ambitious)
