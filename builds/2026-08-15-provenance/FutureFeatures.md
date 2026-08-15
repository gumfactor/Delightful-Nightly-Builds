# FutureFeatures.md — Provenance

Enhancements to a working, valuable tool — none of these are required for tonight's build to be useful as shipped.

1. **Direct write-back into The Canada List's production database.** Tonight's tool outputs a reviewable CSV a curator imports manually, which is the right first step (never trust a batch classifier to write directly to production without a human checkpoint) but is real friction at scale. A future version could add a `--push` mode that writes only `canadian`-verdict rows above a confidence threshold directly into whatever the live ingestion pipeline expects, leaving `uncertain` rows for manual review as they are today.

2. **Confidence-threshold auto-approval tuning.** Right now every verdict is reported with its raw confidence and it's up to the curator to decide what's "good enough." A `--auto-approve-above 0.9` flag that splits output into an `approved.csv` and a `needs-review.csv` would turn a research aid into a real triage tool for large batches.

3. **Corporate registry cross-check for the `uncertain` bucket.** Wikidata coverage is good for larger or notable companies but thin for small Canadian businesses — exactly the kind The Canada List cares most about. A second-pass lookup against a free provincial/federal corporate registry API (where one exists with a stable, documented endpoint) for businesses that come back `uncertain` from Wikidata alone would meaningfully raise the tool's real-world hit rate.

4. **Duplicate/near-duplicate business detection before classification.** If a curator's CSV has "Acme Inc." and "Acme Incorporated" as separate rows, they're currently resolved (and possibly cached) independently. A pre-pass that flags likely-duplicate names before the batch runs would save wasted Wikidata queries and catch data-entry inconsistency at the source, complementing (not duplicating) Ingest Gate's schema-level QC.

5. **Batch progress and rate-limit backoff for very large CSVs.** Tonight's batch loop is synchronous and has no explicit rate-limiting beyond Wikidata's own tolerance for burst traffic. For a 1,000+ row CSV, adding a small delay between cache-miss requests plus a `--resume-from-row N` flag (so an interrupted run doesn't have to restart from the top, even though the cache already avoids most redundant work) would make very large batches more robust.

6. **A lightweight local review UI in the `--render` report.** The HTML report is currently read-only. Adding a "mark as reviewed" checkbox per row (persisted to `localStorage`, matching the pattern this catalog's browser tools already use) would let a curator work through the `uncertain` bucket directly in the report instead of switching to a spreadsheet.

7. **Multi-language Wikidata label support.** `get_label` and the search query both hardcode `language=en`. Some Canadian businesses (especially Quebec-based ones) have their canonical Wikidata entries or clearer claims in French — falling back to a `fr` search when an `en` search returns nothing would likely improve hit rate for a real subset of Canada List submissions.
