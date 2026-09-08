# PRD — Secrets Sentinel

## Goal
Give the user a local CLI that walks the full commit history of their own git repositories and finds credentials that were ever committed — including ones already deleted from the current tree but still recoverable from history — so they can rotate and purge them before a real leak happens.

## User Story
As a solo founder/researcher running several long-lived repos (The Canada List, Kwyeter, lab tooling, this nightly-build repo), I want to point a tool at a directory of repos and get back a prioritized list of every place a real secret was ever committed — not just what's in the working tree today — because `git log` history is exactly the place `.gitignore` and code review can't protect me, and a secret removed from HEAD is still live until it's rotated and purged from history.

## Scope

### In scope
- Discover git repositories under a root directory (or accept explicit repo paths)
- Walk every commit on every local branch (`git log --all`) up to a configurable cap
- Parse each commit's diff to find **added** lines (a secret must have been introduced as an addition at some commit)
- Detect secrets two ways:
  1. **Known vendor patterns** (AWS access key, GitHub PAT, Slack token, Stripe key, Google/Firebase API key, generic PEM private key block, JWT) — regex-based, high confidence
  2. **Generic high-entropy tokens** — a from-scratch Shannon entropy calculator flags long base64/hex-like strings that don't match a named vendor, tiered by entropy + whether they sit next to a secret-sounding variable name (`api_key`, `token`, `secret`, `password`, `credential`)
- Confidence tiers: `high` (named vendor pattern), `medium` (high entropy + suspicious variable name), `low` (high entropy only)
- For every finding, determine whether the exact secret string is still present in the current HEAD version of the file (`still_in_head`) — a finding that's gone from HEAD but present in history is still a live leak requiring history rewrite, not just a code edit
- Optional AI triage pass (medium/low tier only — high tier is unambiguous and skips AI) using `ANTHROPIC_API_KEY` at runtime: sends Claude Haiku a **redacted** context window (variable name + 2 lines of surrounding code, secret value replaced with `[REDACTED:Nchars]`) and asks it to classify the finding as `likely_real_secret`, `likely_test_fixture_or_hash`, or `uncertain`. The actual secret substring is never sent to any third party. Deterministic fallback (`unreviewed` tag, tier stands as-is) when no key is set.
- Terminal summary report, JSON export, and a self-contained dark-mode HTML report (grouped by repo → tier, with still-in-HEAD badges and per-finding remediation guidance)
- `--no-ai` flag to force the deterministic-only path even with a key present

### Out of scope
- Automatically rotating credentials or rewriting git history (this tool reports; the user acts)
- Scanning remote-only branches not fetched locally, or GitHub's server-side secret scanning API
- Binary file content scanning (binary files are skipped, not crashed on)
- A daemon/watch mode — this is a run-on-demand CLI

## Tech Stack
Python 3, stdlib only for the core engine (`subprocess` for git, `re`, `math`, `json`, `argparse`), `anthropic` package for the optional AI triage pass (imported lazily, never required to run). Tests with `pytest`, using real temporary git repos (`git init` in `tmp_path`) for scanner tests and a mocked Anthropic client for classifier tests — no live network calls in any test.

## Data Structure
`Finding` (dataclass): `repo: str`, `commit: str`, `file: str`, `line: int`, `pattern_name: str`, `tier: Literal["high","medium","low"]`, `redacted_snippet: str`, `still_in_head: bool`, `ai_verdict: str | None`

No persistent storage — each run is a fresh scan; JSON export is the durable artifact if the user wants to diff runs over time (documented as a future feature).

## Folder Structure
```
builds/2026-09-08-secrets-sentinel/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── entropy.py       # Shannon entropy + candidate token extraction
│   ├── patterns.py      # known vendor secret regex library
│   ├── scanner.py       # repo discovery, git log/diff walking, Finding assembly
│   ├── classifier.py    # tier assignment + optional Claude Haiku triage (redacted)
│   ├── report.py        # terminal / JSON / HTML rendering
│   └── main.py          # CLI entry point (argparse)
└── tests/
    ├── __init__.py
    ├── test_entropy.py
    ├── test_patterns.py
    ├── test_scanner.py
    ├── test_classifier.py
    ├── test_report.py
    └── test_cli.py
```

## Testing Strategy
- `pytest`, run via `python -m pytest tests/ -v` from the build folder
- Real temporary git repositories (`tmp_path` + `subprocess.run(["git", "init", ...])`) exercise the scanner end-to-end: multi-commit history, a secret added then later removed (proves `still_in_head=False` still gets reported), binary file present (proves no crash), multiple repos under one root directory (proves discovery), a `--max-commits` cap (proves it's respected)
- Pattern tests are parametrized against one canonical real-shaped example per vendor pattern, plus a negative case that must not match
- Entropy tests check that a high-entropy random-looking token scores above threshold and a low-entropy repeated/English-word token scores below it
- Classifier tests use a mocked `anthropic.Anthropic` client (no network) and assert the exact secret substring never appears in any argument passed to the mock — this is the security property the whole AI-triage feature depends on
- Report tests assert HTML-escaping of attacker-controlled fields (a file path or snippet containing `<script>`) never renders as raw HTML, and that JSON/terminal output counts match the underlying findings
- No test ever calls a live Anthropic or GitHub API

## Success Criteria
1. Scanning a test repo where a secret was committed and later deleted correctly reports it with `still_in_head=False` and the correct historical commit/file/line
2. All 6 named vendor patterns (AWS, GitHub PAT, Slack, Stripe, Google/Firebase, PEM block) plus JWT are each detected from a canonical real-shaped example and correctly tiered `high`
3. The redacted-context guarantee holds: no test can construct a call to the (mocked) Anthropic client that contains the literal matched secret substring
4. The HTML report renders without executing injected markup from any user-controlled field (path, snippet, repo name)
5. At least 15 tests exist and all pass with zero failures
