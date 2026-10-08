# Future Features — Lookalike

1. **Direct directory sync.** Read the existing Canada List records from Firebase/Firestore (service account) instead of a CSV export, and write approved merges back as a reviewed batch.
2. **Geocoded distance.** Use a postal-code centroid table (Statistics Canada) so "same brand, 40 m apart" is a duplicate and "same brand, 40 km apart" is a branch, rather than relying on street text.
3. **Learned weights.** Fit the evidence weights to the `decisions.json` history (logistic regression on the stored reasons) so the scorer adapts to the user's own data and thresholds.
4. **Phonetic and bilingual name keys.** Add Double-Metaphone style keys and an English/French token dictionary (`Boulangerie` ↔ `Bakery`) to catch translated duplicates.
5. **Incremental mode.** Persist a fingerprint index (SQLite) so each nightly ingest compares only new rows against the accumulated directory instead of rescanning everything.
6. **Merge undo.** Emit a reversible patch file (`unmerge.json`) so a bad merge can be rolled back by row id.
7. **Scheduled Routine.** Package as a Claude Code Routine that runs on the ingestion export and posts the review page link plus counts.
