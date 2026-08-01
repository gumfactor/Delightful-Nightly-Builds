# Manual — ItemScope

ItemScope turns a CSV of student exam/quiz responses into a classical-test-theory item analysis report: which items were too easy, too hard, poorly discriminating, or had a broken answer choice — with a dark-mode HTML dashboard and a plain-text or JSON option for scripting.

## Requirements

Python 3.9+. No third-party packages are required to run the tool (stdlib only). `pytest` is only needed to run the test suite.

## Input formats

### 1. Binary-scored (most common LMS/Scantron export)

Each item column already contains 0/1 (or `true`/`false`, `correct`/`incorrect`):

```csv
student_id,item_1,item_2,item_3
S001,1,0,1
S002,1,1,1
S003,0,0,1
```

Run:
```bash
python3 -m itemscope.cli analyze responses.csv
```
(run from inside `src/`, or set `PYTHONPATH=src` first — see Running section below)

### 2. Raw-option (enables distractor analysis)

Each item column contains the option letter the student selected, plus a separate answer key CSV (`item,answer` rows):

```csv
student_id,q1,q2,q3
S001,B,C,A
S002,A,C,B
```
```csv
item,answer
q1,B
q2,C
q3,A
```

Run:
```bash
python3 -m itemscope.cli analyze responses.csv --key answer_key.csv
```

The first column is auto-detected as the student ID column when its values don't look like item responses (not 0/1/true/false, not a single option letter). Pass `--student-id-col NAME` to override auto-detection.

## Running

From the build folder:
```bash
cd builds/2026-08-01-itemscope
PYTHONPATH=src python3 -m itemscope.cli analyze sample_data/responses_binary.csv
PYTHONPATH=src python3 -m itemscope.cli analyze sample_data/responses_raw.csv --key sample_data/answer_key.csv
```

By default this prints a self-contained HTML report to stdout. Redirect or use `--output`:
```bash
PYTHONPATH=src python3 -m itemscope.cli analyze sample_data/responses_binary.csv --output report.html
```
Then open `report.html` directly in any browser — no server needed.

## Options

| Flag | Effect |
|------|--------|
| `--key FILE.csv` | Answer key for raw-option input (`item,answer` rows); enables distractor analysis |
| `--student-id-col NAME` | Explicit student ID column name (auto-detected otherwise) |
| `--format text\|json\|html` | Output format (default: `html`) |
| `--output FILE` | Write to a file instead of stdout |
| `--ai` | Generate a plain-English suggestion for the 3 worst-flagged items via Claude Haiku |

## Using `--ai`

Set `ANTHROPIC_API_KEY` in your environment before running with `--ai`:
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
PYTHONPATH=src python3 -m itemscope.cli analyze responses.csv --ai --format text
```
Only aggregated per-item statistics (p-value, discrimination, flag names) are ever sent — never raw student responses, names, or IDs. Without a key set, ItemScope always falls back to a deterministic, flag-specific template suggestion, so the tool is fully functional with zero network access.

## Reading the report

- **Stat tiles**: student count, item count, mean score, SD, and KR-20 reliability (a 0–1 measure of internal consistency; above ~0.7 is generally considered acceptable for a classroom test).
- **Difficulty vs. Discrimination quadrant chart**: each dot is one item. X-axis is difficulty (p-value, right = easier). Y-axis is discrimination (higher = better at separating strong from weak students). Red dots are flagged items.
- **Flagged Items panel**: every item with at least one issue and why.
- **All Items table**: sortable (click a column header) and searchable by item ID.

### Flag meanings

| Flag | What it means | Suggested action |
|------|----------------|-------------------|
| Too easy | Almost everyone (>95%) got it right | Fine as a confidence-builder; doesn't help distinguish mastery |
| Too hard | Almost everyone (<20%) got it wrong | Check wording, or it may not have been taught as expected |
| Poor discrimination | Doesn't separate strong from weak students well | Consider revising or replacing |
| Negative discrimination | Weaker students did *better* than stronger students on this item | Likely miskeyed or genuinely ambiguous — review first |
| Non-functioning distractor | A wrong answer choice was never picked by top or bottom scorers | Replace with a more plausible wrong answer |
| Reversed distractor pull | A wrong answer choice was picked *more* by top scorers than bottom scorers | Double-check the option isn't defensible, or the key is wrong |

## Running the tests

```bash
cd builds/2026-08-01-itemscope
pip install pytest   # if not already installed
pytest tests/ -v
```
47 tests, all passing.

## Known limitations

- Binary (right/wrong) and single-best-answer MCQ scoring only — no partial credit or short-answer rubric scores.
- Distractor analysis only evaluates option letters that actually appear somewhere in the response data; an option that's a valid answer choice but was never selected by anyone can't be detected as non-functioning without a separate list of all valid options (a possible future enhancement — see FutureFeatures.md).
