# PRD — Stats Coach

## Goal
A Flask web app that guides researchers and students through selecting and using the correct statistical test by asking about their research design, then using the Anthropic API to generate a plain-English explanation, R code, and Python code tailored to their specific context.

## User Story
As a researcher or graduate student who knows their research design but is uncertain which statistical test to use, I want to describe my data (outcome type, number of groups, whether groups are independent or paired, normality) and receive an authoritative test recommendation with a clear explanation, runnable code in R and Python, and an interpretation guide — so I can proceed confidently without scheduling an office hours appointment.

## Scope

### In
- Interactive browser form: users choose outcome type, number of groups, paired/independent, normality assumption, and optionally add a sentence about their study context
- Backend decision logic (Python, no AI) selects the recommended statistical test from a decision tree
- Anthropic API (claude-haiku-4-5-20251001) generates a personalized 3-paragraph explanation: what the test does, why it fits this design, and what the results will tell you
- R code snippet for the recommended test
- Python (scipy/pingouin) code snippet for the recommended test
- SQLite cache: same design → same cached response (avoids repeated API calls for identical queries)
- Dark-mode HTML UI with smooth results panel
- Interpretation guide section (what p-value, effect size, and confidence interval mean for this test)
- Mobile-readable layout

### Out
- User accounts or saved history (localStorage or DB per user)
- Uploading actual data files
- Running the analysis on uploaded data
- Bayesian tests (future feature)
- Multivariate designs (MANOVA, SEM, etc.)

## Tech Stack
- Python 3.11, Flask 3.0, anthropic SDK, sqlite3 (stdlib)
- Vanilla HTML/CSS/JS frontend served by Flask
- pytest for backend tests (no Playwright — Python stack)
- `requirements.txt` with pinned versions

## Data Structure

### SQLite: `stats_coach.db`
Table `cache`:
- `id` INTEGER PRIMARY KEY
- `design_hash` TEXT UNIQUE — SHA256 of canonical JSON design params
- `test_name` TEXT
- `ai_explanation` TEXT
- `r_code` TEXT
- `python_code` TEXT
- `interpretation` TEXT
- `created_at` TEXT

### Test Decision Tree (in-app logic, `src/advisor.py`)
Input params:
- `outcome_type`: "continuous" | "categorical" | "ordinal"
- `num_groups`: 1 | 2 | 3+
- `paired`: true | false
- `normality`: "assumed" | "violated" | "unknown"
- `relationship`: true | false (testing a relationship, not group difference)
- `study_context`: free text (optional, fed to AI)

Output: `test_name`, `family`, `assumptions`, `r_snippet`, `python_snippet`

## Folder Structure
```
builds/2026-06-25-stats-coach/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── src/
│   ├── server.py           ← Flask entry point
│   ├── advisor.py          ← Decision tree logic
│   ├── cache.py            ← SQLite cache layer
│   ├── ai_explainer.py     ← Anthropic API calls
│   ├── templates/
│   │   └── index.html      ← Single-page UI
│   └── static/
│       └── app.js          ← Form submission + results rendering
└── tests/
    ├── test_advisor.py     ← Decision tree unit tests
    ├── test_cache.py       ← SQLite cache tests
    ├── test_server.py      ← Flask route integration tests
    └── test_explainer.py   ← AI explainer (mocked) tests
```

## Testing Strategy
- `test_advisor.py`: 15 tests covering every decision tree branch — each test supplies design params and asserts the correct test name. Covers happy paths (t-test, paired t-test, ANOVA, chi-square, Mann-Whitney, Wilcoxon, Kruskal-Wallis, Pearson, Spearman, linear regression, logistic regression, McNemar, Fisher's exact) and edge cases (unknown normality, 1 group, ordinal outcome).
- `test_cache.py`: Tests for cache write, cache read (hit), cache miss, hash stability for same inputs, hash difference for different inputs.
- `test_server.py`: Tests Flask routes — GET / returns 200, POST /api/advise with valid params returns expected structure, POST with missing params returns 400, POST with invalid values returns 400.
- `test_explainer.py`: Tests the AI explainer with a mocked Anthropic client — asserts prompt construction, response parsing, fallback on API error.

Total: ≥ 25 tests.

## Success Criteria
1. A user can select a research design and receive a test recommendation with explanation and code without any console errors.
2. The decision tree correctly recommends a different test for every meaningfully distinct design combination (verified by test suite covering ≥ 13 distinct test types).
3. AI explanation is generated via the Anthropic API and cached — a second identical request returns the same response without a new API call.
4. R and Python code snippets are syntactically valid and appropriate for the recommended test (verified by inspection and test assertions).
5. All 25+ tests pass with zero failures.
