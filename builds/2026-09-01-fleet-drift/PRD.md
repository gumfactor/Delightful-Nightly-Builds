# PRD — Fleet Drift

## Goal

Give the user a single dashboard that shows, across every GitHub repository they own, which third-party dependencies are pinned to inconsistent versions between repos and which are meaningfully behind their latest release — so keeping many simultaneous projects' dependencies sane stops requiring a manual repo-by-repo check.

## User Story

As a solo founder and lab director running many simultaneous GitHub repositories (Canada List tooling, Kwyeter, nightly-build infrastructure, lab code), I want to run one command against my own `GITHUB_TOKEN` and see, in one dashboard, which dependencies are pinned to different versions across my repos and how far behind the latest release each pin is — so I can consolidate versions deliberately instead of discovering the drift when something breaks.

## Scope

### In scope
- `sync`: list every repository owned by the authenticated `GITHUB_TOKEN` user (GitHub REST API `GET /user/repos`, paginated, `type=owner`), fetch `requirements.txt` and `package.json` from each repo's default branch via the Contents API (missing file → skipped for that ecosystem, not fatal), parse pinned dependencies:
  - Python (`requirements.txt`): `name==version` lines; comments, blank lines, `-r`/`-e`/VCS/URL lines are skipped (recorded as unparseable, never crash the sync); `pkg[extra]==1.0` extras are stripped to the base name; environment markers (`; python_version >= "3.8"`) are stripped before parsing.
  - JavaScript (`package.json`): `dependencies` + `devDependencies`; a leading `^`/`~`/`>=`/`>` on the version string is stripped to a base pinned version, and the spec is recorded as `exact` or `range` (a `range` entry is still shown in the matrix but never scored as "drift" against another range covering the same base version — only real pin mismatches count as drift).
- For every unique `(ecosystem, dependency)` pair, query the real registry for the latest version:
  - PyPI JSON API: `GET https://pypi.org/pypi/{name}/json` → `info.version`.
  - npm registry API: `GET https://registry.npmjs.org/{name}` → `dist-tags.latest`.
  - A registry lookup failure (404, network error) degrades that dependency's `latest_version` to `null` — reported as "unknown," never treated as up-to-date and never crashes the sync.
- Persist one dated snapshot row per `(repo, ecosystem, dependency)` per UTC day in local SQLite; a same-day re-sync upserts in place (matches this catalog's established snapshot pattern) so a `history` view can show real drift/staleness trend across multiple sync runs over time.
- Drift computation: group snapshots by `(ecosystem, dependency)` across all repos in the latest sync; if 2+ repos pin different base versions of the same dependency, flag it as drifted with a severity (`major`/`minor`/`patch`) from a from-scratch semver comparison of the lowest vs. highest pinned version present.
- Staleness computation: per `(repo, ecosystem, dependency)`, classify the pinned version against the latest known version as `current`/`patch-behind`/`minor-behind`/`major-behind`/`unknown`.
- `render`: self-contained dark-mode HTML dashboard — hero stats (repos scanned, unique dependencies, drifted-dependency count, major-drift count), a sortable/searchable drift matrix table (dependency, ecosystem, per-repo pinned versions, severity badge), a Chart.js 4.4.4 bar chart of the most-drifted dependencies with a DOM-table fallback when the CDN is unreachable, and a per-repo staleness panel (count of behind-latest dependencies per repo, worst offender highlighted).
- `list`: terminal summary of the latest sync's drift findings.
- `history`: terminal or JSON view of a given dependency's pinned-version history across snapshots.
- Optional `--ai` flag on `render`: a Claude Haiku "what to fix first" briefing built strictly from the aggregate counts and dependency/repo *names* already computed (never file contents or full dependency lists) — unconditional deterministic-template fallback, verified to make zero network calls when `ANTHROPIC_API_KEY` is unset.
- `requirements.txt` listing the one dependency this build needs beyond stdlib: none — stdlib only (`urllib`, `sqlite3`, `json`, `argparse`).

### Out of scope (tonight)
- Auto-fixing, opening PRs, or committing version bumps — read-only, matching the established convention for GitHub-reading tools in this catalog (e.g. Landing Pattern: "never merges, closes, or comments").
- Ecosystems beyond Python/`requirements.txt` and JS/`package.json` (no Dart/`pubspec.yaml`, R, `Pipfile`, `pyproject.toml`/`poetry.lock`, `setup.cfg`) — documented as a `FutureFeatures.md` item; `dep-check` (2026-06-19) already covers `setup.cfg`/`Pipfile` for single-repo audits, and adding every manifest format tonight would dilute the cross-repo drift feature that is this build's actual differentiator.
- CVE/vulnerability data — no free vulnerability-database API is listed in PROFILE.md's Data Sources; noted as a future feature if one is added.
- Private/internal npm or PyPI registries — public registries only.

## Tech Stack

Python 3, standard library only (`urllib.request` for GitHub/PyPI/npm HTTP calls, `sqlite3`, `json`, `argparse`), Anthropic API optional via `urllib` (never a required dependency), Chart.js 4.4.4 pinned via CDN in the rendered HTML with a verified fallback path, `pytest` for tests. No third-party packages — `requirements.txt` is intentionally empty (stdlib-only), consistent with STANDARDS.md's guidance to leave it empty when true.

## Data Structure

SQLite (`fleetdrift.db`, created in the build folder at runtime, never committed):

```sql
CREATE TABLE snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repo TEXT NOT NULL,
    ecosystem TEXT NOT NULL CHECK (ecosystem IN ('python', 'npm')),
    dependency TEXT NOT NULL,
    pinned_version TEXT,
    pin_kind TEXT NOT NULL CHECK (pin_kind IN ('exact', 'range', 'unparseable')),
    latest_version TEXT,
    fetched_at_date TEXT NOT NULL,
    UNIQUE(repo, ecosystem, dependency, fetched_at_date)
);
```

In-memory result shapes (`src/drift.py`): a `DriftEntry` (dependency, ecosystem, `{repo: pinned_version}`, severity, min/max version) and a `StalenessEntry` (repo, ecosystem, dependency, pinned_version, latest_version, classification).

## Folder Structure

```
builds/2026-09-01-fleet-drift/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── main.py
├── src/
│   ├── __init__.py
│   ├── gh_client.py       # GitHub REST API (list repos, fetch file contents)
│   ├── req_parser.py      # requirements.txt parser
│   ├── pkg_parser.py      # package.json dependency parser
│   ├── semver.py          # from-scratch semver parse/compare/classify
│   ├── registry.py        # PyPI + npm latest-version lookups
│   ├── store.py           # SQLite snapshot persistence
│   ├── drift.py           # cross-repo drift + per-repo staleness computation
│   ├── ai.py               # optional Claude Haiku briefing
│   ├── report.py           # HTML dashboard renderer
│   └── cli.py               # sync / list / render / history subcommands
└── tests/
    ├── test_req_parser.py
    ├── test_pkg_parser.py
    ├── test_semver.py
    ├── test_registry.py
    ├── test_store.py
    ├── test_drift.py
    ├── test_ai.py
    ├── test_report.py
    ├── test_gh_client.py
    └── test_cli.py
```

## Testing Strategy

`pytest`, all external HTTP calls (GitHub Contents/repos API, PyPI JSON API, npm registry API, Anthropic API) mocked by injecting a fake `urlopen`-compatible transport — no test ever makes a real network call. Coverage:

- `req_parser`: exact pins, comments, blank lines, extras (`pkg[extra]==1.0`), environment markers, `-r`/`-e`/VCS lines skipped without crashing, an unpinned line (`name` with no `==`) recorded as `unparseable` rather than dropped silently.
- `pkg_parser`: exact versions, `^`/`~`/`>=` range prefixes stripped and classified as `range`, `dependencies` + `devDependencies` both read, malformed JSON handled without crashing the whole sync.
- `semver`: parse of `X.Y.Z` and `X.Y` (missing patch defaults to 0) forms, pre-release suffix handling, comparison ordering, `classify()` boundary cases (identical → `none`, patch-only diff → `patch`, minor diff → `minor`, major diff → `major`).
- `registry`: PyPI/npm success responses parsed correctly, a 404/network error degrades to `latest_version=None` without raising.
- `store`: insert-then-upsert-on-same-day dedup (same `(repo, ecosystem, dependency, date)` doesn't duplicate), distinct dates accumulate real history, `history()` query returns rows in chronological order.
- `drift`: a dependency pinned identically across repos is never flagged; a dependency pinned to 3+ different versions is flagged once with the correct max-severity classification; a dependency appearing in only 1 repo is never flagged (drift requires ≥2 repos); staleness classification (`current`/`patch-behind`/`minor-behind`/`major-behind`/`unknown` when `latest_version` is `None`).
- `ai`: builds a prompt containing only aggregate counts/names (asserted via string checks — no raw file content ever appears), makes exactly one mocked call when a key is set, and zero real `urlopen` calls when no key is set (call-count assertion, matching this catalog's established verification pattern).
- `report`: renders valid self-contained HTML from a fixture dataset; a `</script><script>alert(1)</script>` payload and an `<img onerror>` payload placed in a repo name and a dependency name are asserted to appear only as escaped/JSON-encoded text inside the `<script type="application/json">` payload, never as an unescaped tag in the surrounding HTML string.
- `gh_client`: pagination across multiple pages of `/user/repos`, a missing `requirements.txt`/`package.json` (404) handled as "no dependencies for that ecosystem" rather than an error.
- `cli`: `sync`/`list`/`render`/`history` argument parsing and end-to-end wiring against an injected fake GitHub/PyPI/npm transport and a temp SQLite path.

Run with `python -m pytest tests/ -v` from the build folder. Minimum 15 tests; target well above that given the parser/semver/drift edge-case surface.

## Success Criteria

1. `sync` correctly parses `requirements.txt` and `package.json` dependency pins from a mocked multi-repo GitHub fixture and persists deduplicated SQLite snapshots (verified: a same-day re-sync produces no duplicate rows; a next-day sync accumulates real history).
2. Cross-repo drift is detected only when 2+ repos pin different versions of the same dependency, and severity (`patch`/`minor`/`major`) matches hand-computed semver cases exactly.
3. `render` produces a self-contained HTML dashboard containing the hero stats, drift matrix, and Chart.js bar chart (with a working DOM-table fallback path), and a malicious repo/dependency name is verified to render only as inert escaped text, never as an executable tag.
4. The optional AI briefing is verified (via mocked-`urlopen` call-count assertions) to send only aggregate counts/names and to make zero network calls when `ANTHROPIC_API_KEY` is unset.
5. The full test suite (`python -m pytest tests/ -v`) passes with zero failures, and a live end-to-end run of `sync` → `render` against a realistic hand-built fixture (multiple repos, at least one genuinely drifted dependency, at least one stale dependency) produces the expected drift/staleness output.

## Idea Brief Traceability

No linked Idea Brief — this idea was freshly generated tonight (see `WhyThis.md`), not drawn from an existing `builds/ideas.md` row with a brief.
