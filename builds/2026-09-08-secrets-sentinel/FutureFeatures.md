# FutureFeatures — Secrets Sentinel

1. **Baseline/diff mode** — save a JSON snapshot (`--json-out`) and let a future run accept `--baseline previous.json` to only report *new* findings since the last scan, so a pre-commit or CI hook doesn't re-flag the same already-triaged history-only findings every run.

2. **`git filter-repo` remediation script generation** — for a confirmed high-confidence, still-in-history finding, emit a ready-to-review `git filter-repo --path <file> --invert-paths` (or blob-ID-targeted) command so remediation is one reviewed copy-paste away instead of a manual lookup.

3. **Remote/pushed-commit awareness** — cross-reference findings against `git branch -r --contains <sha>` to flag which leaks have actually been pushed to a shared remote (higher urgency) versus ones that only ever existed in local, unpushed commits.

4. **Per-repo allowlist file** — a `.secrets-sentinel-ignore` (file:line or matched-pattern-hash based) so a confirmed false positive (e.g. a real-looking key in a fixtures file that's intentionally public test data) doesn't need to be re-triaged by AI on every run.

5. **Pre-commit hook installer** — a `--install-hook` flag that drops a `pre-commit` script into `.git/hooks/` running Secrets Sentinel against just the staged diff (`git diff --cached`), catching a secret before it's committed at all rather than after.

6. **Entropy threshold tuning per repo** — some repos (crypto/hashing-heavy codebases) naturally contain lots of legitimate high-entropy strings; a `--entropy-threshold` override would cut noise for those without weakening the default for everyone else.

7. **Parallel repo scanning** — for a `--scan-dir` covering many repos, scan them concurrently (`concurrent.futures.ProcessPoolExecutor`) instead of sequentially; git subprocess calls are I/O-bound enough that this could meaningfully cut wall-clock time on a large multi-repo sweep.
