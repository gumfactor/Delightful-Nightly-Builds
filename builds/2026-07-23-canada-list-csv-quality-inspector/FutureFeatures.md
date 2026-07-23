# Future Features

1. **Match against the existing live catalog, not just within-batch.** Right now duplicate detection only catches rows that duplicate each other *within* the CSV being checked. The genuinely bigger win is catching a new submission that duplicates something already published on The Canada List — this needs an export or API of the current live catalog to diff against, which isn't available in the build environment tonight.

2. **Postal code and address format validation.** Add a Canadian postal code regex check (`A1A 1A1` pattern) and a light address-plausibility check if/when `postal_code`/`address` columns are common in real export batches — deferred tonight since the exact real column names weren't available to design against.

3. **Category taxonomy validation against a real canonical list.** `category` is currently only checked for presence, not validated against The Canada List's actual category taxonomy (which isn't available in this build environment). Once a real taxonomy CSV/JSON export exists, add AI-assisted category normalization the same way `ownership_status` is handled now.

4. **Batch history / trend tracking.** Persist each run's summary (row counts, issue-type breakdown) to a local SQLite file so repeated ingestion batches over time can be compared — is data quality from a given source improving or degrading?

5. **Configurable severity levels.** Right now `error` vs `warning` per issue type is hardcoded. Letting `--schema` also override which issue codes count as errors vs warnings (e.g. downgrade `invalid_email` to error if email is business-critical for a given batch) would make the tool adapt to different real-world ingestion policies without code changes.

6. **CSV encoding auto-repair.** Currently non-UTF-8 files are flagged but not fixed. Detecting the likely source encoding (e.g. via a small set of common Windows-1252/Latin-1 heuristics) and offering an `--auto-fix-encoding` flag that re-writes the cleaned CSV in clean UTF-8 would remove a manual step.

7. **Diff mode between two runs.** Given two `report.json` outputs from the same source over time, show what changed — new rows, resolved issues, newly appearing duplicates — useful for tracking whether an upstream data source's quality is trending in the right direction.
