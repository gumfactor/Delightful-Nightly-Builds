# PRD — Secret Sweep

> **Build date:** 2026-08-21
> **Category:** H — Developer Tool
> **Complexity:** Ambitious
> **Day of week:** Friday

---

## Goal

A Python CLI that scans one or more local git repositories — the current working tree *and* the full commit history — for accidentally committed secrets and credentials, and produces a redacted, actionable, severity-ranked report.

## User Story

As a mid-career researcher and solo founder who writes a large fraction of their code with AI assistance across several simultaneous repos (The Canada List, Kwyeter, lab infrastructure, and a nightly stream of one-off tools), I want to sweep every repo I touch for API keys, tokens, and credentials that were ever committed — even ones since deleted from HEAD — so that I can rotate anything exposed before it becomes an incident, without having to remember to think about it on every commit.

## Scope

### In Scope
- A pattern library covering 12+ known credential formats (AWS access key ID / secret key, GitHub classic + fine-grained PAT, GitHub OAuth token, Slack token, Stripe live secret/publishable key, Google API key, Anthropic API key, OpenAI API key, SendGrid API key, Twilio SID/auth token, generic PEM private key block, Firebase service-account `private_key` field) plus a generic high-entropy-assignment detector (variable name matches `key|secret|token|passwd|password|credential`, quoted value with sufficient length and Shannon entropy) for anything the named patterns miss.
- An allowlist that suppresses obvious placeholders (`changeme`, `your_api_key_here`, `xxxx...`, `0000...`, `example`, `dummy`, `placeholder`, `test`, `redacted`, repeated-character runs) so the generic entropy detector doesn't drown real findings in noise.
- Two scan surfaces per repo: `scan` (current working tree, respecting `.gitignore`) and `history` (every commit reachable from the current branch via `git log -p`, tracking which file/commit each finding first appeared in).
- Severity ranking: **Critical** — the secret is present in the current working tree or `HEAD` (actively exploitable right now); **High** — the secret only appears in history (removed from HEAD but permanently present in any clone/fork that already has it).
- A local SQLite baseline per repo path: every finding is stored as a redacted preview + SHA-256 hash of the raw match (never the raw value itself) so re-scans are idempotent (no duplicate rows) and a confirmed false positive can be acknowledged once (`ack`) and never resurfaces as "new" on subsequent scans, while still appearing in the full report as acknowledged.
- Per-finding remediation guidance: for Critical findings, add-to-`.gitignore` + remove-from-tracking + rotate-immediately instructions; for High (history-only) findings, a ready-to-copy `git filter-repo` command scoped to the exact file path, plus an explicit reminder that history rewriting does not undo exposure to anyone who already has a clone — the credential must still be treated as compromised and rotated.
- Three report formats from one `report` command: colored terminal summary, JSON export, and a self-contained dark-mode HTML dashboard (per-repo panels, severity badges, search/filter, one-click-copy remediation snippets).
- Optional Claude Haiku second-opinion classifier (`--ai-review`): for each candidate finding, sends only the pattern name, file extension, entropy score, and a masked context snippet (secret value replaced by a fixed placeholder token, never the real characters) and asks for a `likely_secret` / `likely_placeholder` / `uncertain` verdict with a one-sentence rationale — reduces noise on the generic entropy detector without ever transmitting the credential itself. Unconditional deterministic fallback (the raw pattern/entropy classification) when `ANTHROPIC_API_KEY` is unset, verified in tests to make zero network calls in that case.
- A companion Claude Code Skill (`skill/SKILL.md`) exposing a fast, working-tree-only scan invocable mid-coding-session ("scan this repo for secrets before I commit") — deliberately excludes the full-history walk, which is a slower, periodic-audit operation better run from the CLI directly.
- Multi-repo support: every command accepts one or more repo paths (default: current directory) and tags every finding with the originating repo name.

### Out of Scope
- Automatic remediation (deleting files, rewriting history, rotating keys, or committing anything) — this tool only detects and reports; it never modifies the scanned repository. The abort/never-modify-files-outside-the-build-folder principle in STANDARDS.md extends naturally here: this tool must never write to repos it scans either.
- Scanning remote/cloud secret stores (AWS Secrets Manager, GCP Secret Manager, Vault) — local git only.
- A pre-commit git hook installer — noted as a strong Future Feature, but shipping an installer that modifies a scanned repo's `.git/hooks/` would cross the "never modifies the repo it scans" line above and deserves its own dedicated review.
- Binary file content scanning (images, compiled artifacts) — text files only, matching how secrets are actually committed in practice.

## Tech Stack

- **Language:** Python 3.11+
- **Framework:** None
- **Dependencies:** stdlib only (`subprocess`, `sqlite3`, `re`, `math`, `hashlib`, `json`, `urllib.request` for the optional Anthropic call, `argparse`, `pathlib`, `fnmatch` for `.gitignore`-style matching) — plus the user's own local `git` binary invoked as a subprocess, exactly as the precedent set by Waymark (2026-08-07), BugTrace (2026-07-25), and Landing Pattern (2026-08-03).
- **Runtime requirement:** `python3 secretsweep.py <command> [repo paths...]` — no install step, no virtualenv required beyond a stock Python 3.11+ interpreter and `git` on `PATH`.

## Data Structure

SQLite database at `~/.secretsweep/findings.db` (created on first run; a `--db` flag can override the path for testing). One table:

```sql
CREATE TABLE findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repo_path TEXT NOT NULL,
    repo_name TEXT NOT NULL,
    scope TEXT NOT NULL,          -- 'working-tree' or 'history'
    file_path TEXT NOT NULL,
    line_number INTEGER,
    commit_sha TEXT,              -- NULL for working-tree findings
    pattern_name TEXT NOT NULL,
    severity TEXT NOT NULL,       -- 'critical' or 'high'
    entropy REAL,
    masked_preview TEXT NOT NULL, -- e.g. "AKIA••••••••••••WXYZ"
    match_hash TEXT NOT NULL,     -- sha256 of the raw matched value, for dedup only
    status TEXT NOT NULL DEFAULT 'new',  -- 'new' or 'acknowledged'
    ai_verdict TEXT,              -- NULL or 'likely_secret' / 'likely_placeholder' / 'uncertain'
    ai_rationale TEXT,
    first_seen TEXT NOT NULL,     -- ISO8601 UTC
    last_seen TEXT NOT NULL,
    UNIQUE(repo_path, scope, file_path, match_hash, commit_sha)
);
```

The raw secret value is held in memory only long enough to compute its entropy, masked preview, and SHA-256 hash — it is never written to disk, never included in any report, and never sent over the network (the optional AI call receives only the masked context, never the raw match).

## Folder Structure

```
builds/2026-08-21-secret-sweep/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── secretsweep.py
├── src/
│   ├── __init__.py
│   ├── patterns.py
│   ├── redact.py
│   ├── git_ops.py
│   ├── scanner.py
│   ├── db.py
│   ├── ai_review.py
│   └── report.py
├── skill/
│   └── SKILL.md
└── tests/
    ├── __init__.py
    ├── test_patterns.py
    ├── test_redact.py
    ├── test_scanner.py
    ├── test_db.py
    ├── test_ai_review.py
    ├── test_report.py
    └── test_cli.py
```

## Testing Strategy

- **Framework:** pytest
- **Test file location:** `tests/test_*.py`
- **Run command:** `python -m pytest tests/ -v`
- **What will be tested:**
  - Pattern library correctly matches each named credential format (AWS, GitHub PAT, Stripe, PEM block, etc.) and does not false-positive on ordinary code.
  - Generic entropy detector flags a genuinely high-entropy assignment and does not flag ordinary low-entropy strings; allowlist suppresses known placeholders.
  - Redaction: masked preview never contains more than the first/last 4 characters of the raw value; the SHA-256 hash round-trips for dedup but cannot be reversed to the raw value in any stored artifact.
  - Working-tree scan finds a secret in a tracked file; history scan finds a secret that was committed and later removed from HEAD, correctly classified as `high` severity and distinct from a still-present `critical` finding.
  - Real temporary git repositories are created via `subprocess` (`git init`, real commits) as fixtures — no mocked git plumbing — so `git log -p` parsing is exercised against real diff output.
  - SQLite dedup: scanning the same repo twice does not duplicate a finding; `ack` marks a finding acknowledged and it is excluded from the "new" count on a subsequent scan while still present in the full listing.
  - AI review: with a mocked `urlopen`, the outgoing request payload is asserted to contain no substring of the raw secret; with no `ANTHROPIC_API_KEY` set, the mock is asserted never called and the deterministic fallback verdict is used instead.
  - HTML report: a finding whose file path or masked context contains a `<script>`/`<img onerror>` payload renders as inert escaped text, never as executable markup, in the generated HTML string.
  - CLI argument parsing across multiple repo paths, and graceful (non-crashing) handling of a non-git directory and a repo with zero commits.

## Success Criteria

1. All tests pass (zero failures), minimum 15 tests (47 delivered).
2. A known-format secret (e.g. an AWS-shaped key) committed to a fixture repo's working tree is detected as `critical`; the same secret removed from HEAD in a later commit is still detected via `history` as `high`, and never re-appears as `critical`.
3. Every report format (terminal, JSON, HTML) redacts every secret value to a masked preview — grepping the full HTML/JSON output for any full raw fixture-secret string returns zero matches.
4. Re-scanning an unchanged repo produces zero duplicate SQLite rows, and `ack`-ing a finding removes it from the "new" count on the next scan while it remains visible as `acknowledged` in the full report.
5. With no `ANTHROPIC_API_KEY` set, running with `--ai-review` makes zero network calls (verified via a mocked `urlopen` call-count assertion) and still produces a complete, correctly-severity-ranked report using the deterministic fallback.

---

## Scope Changes

None — the full scope above was implemented as planned. The pre-commit-hook installer and remote-secret-store scanning were deliberately scoped out from the start (see Out of Scope) rather than cut mid-build.
