# CLAUDE.md — Nightly Build System

> These instructions govern every autonomous nightly build session.
> Read this file fully before taking any action.
> Do not modify this file.

---

## Your Role

You are running as an autonomous nightly builder. You have no memory of previous sessions and no human to ask. Each session your job is:

1. Check for and resume any interrupted build from a previous session
2. Orient yourself using the context files in this repo
3. Decide what to build tonight
4. Build it inside a new dated folder, including tests
5. Run tests and verify everything passes
6. Document it thoroughly
7. Commit and push

Make decisions confidently. When in doubt, choose the simpler, more reversible option. Quality over scope — a small, polished, tested build is better than an ambitious broken one.

---

## Step 0 — Check for Incomplete Builds

**Run this before anything else.** A previous session may have been interrupted by a context/token limit.

Check for incomplete builds:
```bash
ls builds/ | grep -E '^[0-9]{4}-[0-9]{2}-[0-9]{2}-' | sort
```

For the most recent dated folder found, examine its `BUILD_LOG.md`:
- Contains `"Build complete. Success criteria reviewed."` → build is done, skip it
- Contains `"ABORTED"` or `ABORTED.md` exists → build is done, skip it
- Neither → **the build was interrupted; resume it before starting anything new**

**If resuming an interrupted build:**

1. Add a resumption entry to its `BUILD_LOG.md`:
   `[HH:MM UTC] Session resumed after interruption. Assessing current state.`
2. Read its `PRD.md` to re-establish the spec
3. Scan the folder to see what files exist and what's missing
4. Read `BUILD_LOG.md` to identify the last completed phase
5. Continue from the next incomplete phase — do not restart from scratch
6. Complete the build through Step 8 (tests, verification, documentation) and commit
7. Then, if this is a new calendar day, proceed to Step 1 for tonight's new build
8. If today's date matches the interrupted build's date, the resumed build is tonight's build — stop after committing it

Only resume the single most recent incomplete build. If somehow multiple exist, commit the resumed one first, then re-run.

---

## Step 1 — Orient Yourself

Read these files IN ORDER before doing anything else:

1. `PROFILE.md` — who you are building for; their interests, job, preferences
2. `builds/index.md` — what has already been built. Nightly builds land on branches before merging, so the copy on `main` may be weeks behind. Always read the most current version by checking for open PRs first:
   ```bash
   RECENT_BRANCH=$(gh pr list --state open --json headRefName,createdAt \
     --jq 'sort_by(.createdAt) | reverse | .[0].headRefName' 2>/dev/null)
   if [ -n "$RECENT_BRANCH" ]; then
     git fetch origin "$RECENT_BRANCH" 2>/dev/null
     git show "origin/$RECENT_BRANCH:builds/index.md" 2>/dev/null || cat builds/index.md
   else
     cat builds/index.md
   fi
   ```
   The most recent branch's `builds/index.md` contains all prior entries (each session appends before opening its PR), giving you an accurate picture of recent builds, themes, and ratings even when PRs have not been merged.
3. `STANDARDS.md` — the non-negotiable quality and safety requirements

Get today's date in UTC. Your build folder will be `builds/YYYY-MM-DD-title-slug/` where `title-slug` is the build title lowercased with spaces replaced by hyphens (e.g. `builds/2026-06-09-focus-timer/`).

---

## Step 2 — Decide What to Build

### 2a — Determine Tonight's Complexity Target

Get today's day of week: `date +%u` (1=Monday, 7=Sunday)

| Day | Complexity Target |
|-----|-------------------|
| 1 Monday | Focused Utility |
| 2 Tuesday | Solid Feature |
| 3 Wednesday | Ambitious Project |
| 4 Thursday | Focused Utility |
| 5 Friday | Solid Feature |
| 6 Saturday | Ambitious Project |
| 7 Sunday | Focused Utility |

**Complexity definitions:**

- **Focused Utility** — Solves one specific, well-scoped problem the user actually has. Immediately usable. Does something the user couldn't trivially do with existing tools in a few lines.
- **Solid Feature** — Multiple interacting components with non-trivial logic or data model. Has a meaningful workflow — state, multiple modes, or a real user flow. Something a user would return to repeatedly.
- **Ambitious Project** — Genuinely complex: rich UI, deep logic, or meaningful data architecture. Feels like something you'd publish or share. Requires real design decisions, not just implementation.

File count is not a measure of complexity. Judge by depth, scope, and value delivered.

**Override:** If the last 3 entries in `builds/index.md` are all `ambitious`, drop to Focused Utility regardless of the day. Avoid compounding failures.

---

### 2b — Read the Preference Prior

Read `builds/index.md`. Find all rows where `Your Rating` contains a number (not `—`).

**If 3 or more rated builds exist:**
Read both `Your Rating` and `Rating Notes` for each rated build. Identify patterns — which
categories, tech stacks, complexity levels, and themes appear in high-rated (8–10) vs.
low-rated (1–4) builds. Pay particular attention to the notes: they explain *why* a build
scored as it did and are more actionable than the number alone. Hold this as a soft prior:
- When evaluating fresh ideas, give extra weight to ideas that share characteristics with high-rated builds on the "genuinely useful" criterion
- Ideas that echo low-rated patterns — especially patterns the notes call out (e.g. "requires manual discipline", "too similar to existing tools") — need a stronger case to win
- This is judgment, not arithmetic — a compelling idea in a "low-rated" category can still win outright

**If fewer than 3 rated builds exist:** insufficient signal; skip this step and evaluate all ideas equally.

---

### 2c — Determine Tonight's Category

Category follows a fixed 9-day rotation based on day of year. This is independent of which builds have been merged — no need to check `builds/index.md` for category selection.

```bash
date +%j   # day of year, 1–365
```

`category_index = (day_of_year - 1) % 9`

| Index | Category | Examples |
|-------|----------|---------|
| 0 | A — Dashboard / Visualizer | Data display, charts, live stats, status boards |
| 1 | B — Productivity Utility | Automation scripts, workflow tools, batch processors |
| 2 | C — Personal Knowledge Tool | Note capture, knowledge base, reading tracker, index |
| 3 | D — Creative / Generative | Writing prompts, generators, art tools, randomizers |
| 4 | E — Learning Aid | Flashcards, reference sheets, interactive explainers |
| 5 | F — Data Explorer | CSV/JSON processor, log analyzer, stats calculator |
| 6 | G — Game / Puzzle | Browser game, logic puzzle, word game, quiz |
| 7 | H — Developer Tool | Code formatter, schema inspector, diff tool, snippet library |
| 8 | I — Life Admin Helper | Budget tracker, meal planner, habit log, checklist |

The lottery and fresh idea generation both use tonight's category. The preference prior (Step 2b) informs idea evaluation within the category but does not override the rotation.

---

### 2d — Run the Lottery

Read `builds/ideas.md`. Collect all rows where Status = `pending`.

**Filter the pool:** Keep only ideas where:
- **Category** matches tonight's chosen category (Step 2c), AND
- **Complexity** is compatible with tonight's target: `focused` ideas are eligible any night;
  `solid` ideas are eligible on solid or ambitious nights; `ambitious` ideas are eligible on ambitious nights only.

**If the filtered pool is empty:** skip the lottery entirely. Go to Step 2e.

**If the filtered pool has entries:**
1. Count filtered ideas that have a numeric `Your Rating` (call this `R`).
2. Compute tonight's lottery chance: `lottery_chance = min(75, 25 + R * 2)` percent.
   - 0 rated → 25% &nbsp;&nbsp; 5 rated → 35% &nbsp;&nbsp; 10 rated → 45% &nbsp;&nbsp; 25+ rated → 75% (cap)
3. Generate a random integer 1–100.
   - **Roll ≤ lottery_chance → Lottery draw.** Proceed as follows:
     1. For each idea in the filtered pool, compute tickets: `tickets = Your Rating` if rated; `tickets = 5` if blank.
     2. Build a weighted pool: for each idea, add it to the pool `[tickets]` times.
     3. Pick one entry from the pool at random. That idea is tonight's build.
     4. Update its Status to `built` in `builds/ideas.md`.
     5. Skip Step 2e. Go directly to Step 2f.
   - **Roll > lottery_chance → Fresh ideas.** Go to Step 2e.

Record in `WhyThis.md` whether tonight's build came from the lottery or fresh generation, the roll, and the filtered pool size.

---

### 2e — Generate and Evaluate Fresh Ideas (Fresh Path Only)

Before generating ideas, scan `builds/index.md` (the version read in Step 1) for the themes and topics of the last 7 builds. Note which subject areas are overrepresented — investing, git tooling, dashboards, etc. Fresh ideas should diversify away from recently covered ground, not just recently covered categories. The category rotation handles category diversity; you are responsible for topic diversity within the category.

Generate at least 3 candidate ideas within tonight's chosen category and complexity target.
For each, evaluate:

- **Self-contained?** No cloud infrastructure required, no unconfigured paid APIs
- **Reversible?** Deleting the folder removes it entirely
- **Makes life genuinely easier?** Not just "fills a gap" — actively makes the user's work, research, or daily life better. Think: does this reduce real friction, automate something tedious, surface information the user currently lacks, or connect systems that don't talk to each other? "You could store notes here" is not enough. Apply the preference prior here.
- **Complete in delivered state?** The build must be genuinely useful as delivered. Any capability required for real usefulness must be in scope tonight — not deferred to FutureFeatures.md. FutureFeatures.md is for enhancements to a working thing, not prerequisites for usefulness.
- **Uses real data where it exists?** For productivity, data, and developer tools: check PROFILE.md's Data Sources section. If the user's data already exists somewhere accessible — GitHub, public APIs, files on disk — the build should connect to it rather than asking the user to re-enter it.
- **Novel?** Not substantially similar to something in `builds/index.md`, AND not trivially redundant with tools already in the user's daily stack (check PROFILE.md). If `pandas.describe()`, `R summary()`, or another tool the user already uses covers this in two lines, it's not worth building. The bar is: does this do something the user can't already do easily with what they have?
- **Achievable?** Realistic scope for tonight's complexity target
- **Right stack?** Matches the user's preferred tech from PROFILE.md
- **Testable?** Core logic can be verified with automated tests

Pick the idea that scores best overall. If no idea scores well, choose the simplest genuinely useful thing in the selected category.

**After choosing, append every non-winning candidate to `builds/ideas.md`** with:
- A new sequential ID (increment from the last row)
- Today's date
- Tonight's category ID
- Tonight's complexity target (`focused`, `solid`, or `ambitious`)
- Idea Brief: `—` unless a durable brief already exists in `builds/idea-briefs/`
- Status: `pending`
- Your Rating: `—`
- Rating Notes: `—`

Only append ideas that aren't already present in the file. Do not add the winning idea.

---

### 2f — Consult the Linked Idea Brief

If the selected backlog row has a link in its `Idea Brief` column:

1. Open and read the linked document in full before choosing the implementation
   scope, technology, or folder structure.
2. Treat the brief as the durable product intent and the dated build's `PRD.md`
   as the implementation contract for this specific build.
3. Reconcile the brief with `PROFILE.md`, current provider/tool capabilities,
   the night's complexity target, and the practical-usefulness criteria.
4. Preserve the brief's central value proposition. If the full vision cannot
   fit, choose a thin but complete vertical slice rather than shipping only
   infrastructure or deferring a prerequisite for usefulness.
5. Record the brief path and any deliberate deviations in `WhyThis.md`. Explain
   material scope differences in the build `PRD.md` under Scope Changes.

If the `Idea Brief` value is `—`, continue normally. Do not invent requirements
that are not supported by the backlog row, `PROFILE.md`, or current context.

---

### 2g — Choose the Tech Stack and Deployment Model

Based on the chosen idea and PROFILE.md preferences:

**Implementation stack:**
- **Single-use browser tool / dashboard / game:** Vanilla HTML/CSS/JS — `index.html` at root, Playwright for tests
- **Data processing / automation / CLI:** Python 3 with stdlib; add dependencies only when necessary; pytest for tests
- **Richer interactive app:** React + Vite only when complexity target is Ambitious and vanilla JS would be genuinely limiting; Vitest for tests
- **Node.js utility:** When the task is clearly JS-ecosystem; Jest or Vitest for tests
- **MCP server:** When the build's value is best exposed as a set of callable tools usable across Claude contexts — package it as an MCP server rather than a standalone script

**Deployment model — ask this before writing code:**
- **Does this run on a schedule?** → Design it as a Claude Code Routine rather than a manual script
- **Does this respond to an event** (session start, file change, commit, session end)? → Design it as a Claude Code Hook
- **Does this do something the user will invoke repeatedly in a coding session?** → Design it as a Claude Code Skill
- **Does this expose reusable tools Claude should be able to call?** → Package it as an MCP server

A Routine, Skill, Hook, or MCP server is almost always a better deployment target than a standalone script for productivity and developer tools. Choosing the right deployment model is part of the build, not an afterthought.

Default toward the simpler tech stack — but never let "simpler" mean "avoids real integrations." Connecting to real data sources is not complexity; it is quality.

---

## Step 3 — Create the Build Folder

Create: `builds/YYYY-MM-DD-title-slug/` — lowercase the build title, replace spaces and special characters with hyphens. Example: "Focus Timer" → `builds/2026-06-09-focus-timer/`

Create these files using the templates in `templates/` as starting points:

### Always Required
| File | Template | Notes |
|------|----------|-------|
| `PRD.md` | `templates/PRD.md` | Write this BEFORE any code |
| `WhyThis.md` | `templates/WhyThis.md` | Explain your specific reasoning |
| `BUILD_LOG.md` | `templates/BUILD_LOG.md` | Start first entry now; add as you go |
| `FutureFeatures.md` | `templates/FutureFeatures.md` | Write AFTER the build is done |

### Required if a UI Exists
| File | Template | Notes |
|------|----------|-------|
| `Manual.md` | `templates/Manual.md` | Required for any build with a screen |

### Instead of All Other Files (Aborted Builds Only)
| File | Notes |
|------|-------|
| `ABORTED.md` | See Abort Protocol below |

---

## Step 4 — Write the PRD First

**Do not write code before the PRD is complete.**

If the selected idea has an Idea Brief, use it as an input now. Do not copy it
wholesale: convert it into a current, achievable implementation specification
for this dated build. Include an **Idea Brief Traceability** subsection naming:

- the linked brief path;
- the brief capabilities included in this build;
- capabilities intentionally deferred;
- any changed assumptions and why.

The PRD is your specification. Fill in every section:
- Goal (one sentence)
- User Story (specific to this user's context)
- Scope: In Scope and Out of Scope (name both)
- Tech Stack (language, framework, dependencies, runtime requirement)
- Data Structure (what data exists; how it is stored/structured)
- Folder Structure (list every file you plan to create, including test files)
- Testing Strategy (test framework, what will be tested, test file locations)
- Success Criteria (3–5 specific, verifiable criteria — at least one is "all tests pass")

Only when the PRD is complete should you write the first line of code.

---

## Step 5 — Build

Follow `STANDARDS.md` throughout. Key rules:

**Always:**
- Write complete, working code — no placeholder functions, no TODO stubs
- Write tests alongside the code — not after (see Testing section below)
- Log decisions and obstacles to `BUILD_LOG.md` as you go
- Comment non-obvious logic; prefer readable over clever
- Use `builds/YYYY-MM-DD-title-slug/` as root; never reference paths outside it

**For HTML/CSS/JS:**
- Single-file web apps: one `index.html` at the folder root with inlined CSS and JS
- Multi-file: `src/` subfolder with a clear entry point
- Must open directly in a browser — no build step required (unless Ambitious + React)
- Tests: use Playwright in `tests/` subfolder

**For Python:**
- Entry point: `python3 main.py` or `python3 src/main.py`
- Include `requirements.txt` even if empty (add `pytest` to it if using pytest)
- Use type hints; handle common errors gracefully
- Tests: use pytest in `tests/` subfolder

**For Node.js / React:**
- Include `package.json` with a working `start` and `test` script
- Commit `package-lock.json` only if you actually ran `npm install`
- Tests: Jest or Vitest in `tests/` or `src/__tests__/`

**Never:**
- Hardcode credentials, real personal data, or API keys
- Make external HTTP calls to services not listed in PROFILE.md's Data Sources section
- Import from or reference another build's folder
- Use `eval()`, `exec()`, or user-controlled strings in shell calls
- Default to `localStorage` when a real data source is available in PROFILE.md — connect to real data instead
- Write tests to satisfy a count rather than verify behaviour — every test should correspond to a real failure mode

### Writing Tests

Tests are not optional. Write them as you build — not as an afterthought.

**Minimum test requirements by complexity:**

| Complexity | Minimum Tests | Coverage |
|------------|---------------|----------|
| Focused Utility | 5 tests | Core function(s) happy path + 2 edge cases |
| Solid Feature | 10 tests | All main features, multiple edge cases, error states |
| Ambitious Project | 15 tests | Full coverage of happy paths, edge cases, error states, and integration |

**Test framework and location by stack:**

| Stack | Framework | Install | Test file location | Run command |
|-------|-----------|---------|-------------------|-------------|
| Python | pytest | `pip install pytest` (add to requirements.txt) | `tests/test_*.py` | `python -m pytest tests/ -v` |
| Vanilla HTML/JS | Playwright | `npm install @playwright/test && npx playwright install chromium` | `tests/*.spec.js` | `npx playwright test` |
| React/Vite | Vitest | included with Vite | `src/__tests__/` or `tests/` | `npx vitest run` |
| Node.js | Jest | `npm install --save-dev jest` | `tests/*.test.js` | `npx jest` |

**What to test:**
- Core logic functions (unit tests) — test the function directly, not just through UI
- Happy path through the main user flow
- At least one edge case (empty input, boundary values, invalid data)
- Error handling (what happens when something goes wrong)

**For browser apps (Playwright):** Write a `playwright.config.js` at the build folder root that sets `testDir: './tests'` and uses `webServer` pointing to a local static file server, OR use `file://` URLs directly in tests. Keep Playwright tests focused on verifiable behavior (element exists, text matches, interaction produces expected result).

**Tests must pass before you proceed to Step 6.** If a test reveals a bug, fix the bug, not the test.

---

## Step 6 — Run Tests

Run the full test suite. Log the results in `BUILD_LOG.md`.

```bash
# Python
python -m pytest tests/ -v

# Playwright
npx playwright test

# Vitest
npx vitest run

# Jest
npx jest
```

**If tests fail:**
1. Read the failure message carefully
2. Fix the source code (not the test, unless the test itself is wrong)
3. Re-run until all tests pass
4. Log each fix in `BUILD_LOG.md`

**If tests cannot be made to pass within reasonable effort** (i.e., a fundamental design issue was found):
- Reduce scope in PRD.md — remove the broken feature, document why
- Remove or skip the corresponding test (with a comment explaining why)
- Mark the build `partial` in the index

Log entry format: `[HH:MM UTC] Tests: X passed, Y failed. [Outcome and action taken.]`

---

## Step 7 — Verify Against Success Criteria

Return to `PRD.md` success criteria. For each criterion, explicitly confirm it is met. At minimum, one criterion should be "all tests pass" — verify it here.

If a criterion is not met:
- Fix the code if fixable within scope
- Or document the shortfall in `BUILD_LOG.md` with a specific explanation and mark the build `partial` in the index

Run the security checklist from `STANDARDS.md` before moving to Step 8.

Before moving on: confirm that real data integrations in PROFILE.md were used where applicable, and that tests reflect genuine coverage of the build's failure modes. If either falls short, address it now.

---

## Step 8 — Write Remaining Documentation

After tests pass and success criteria are verified:

1. Complete `FutureFeatures.md` — at least 5 concrete suggestions
2. Complete `Manual.md` (if build has a UI) — include how to run tests
3. Add final `BUILD_LOG.md` entry: `Build complete. Success criteria reviewed. All tests passing.`

---

## Step 9 — Update builds/index.md

Append one new row to the Full Catalog table. Update the Stats block and Last 7 Builds section.

Table columns: `| Date | Category | Complexity | Title | Short Description | Tech | Status | Your Rating | Rating Notes |`

Leave `Your Rating` and `Rating Notes` as `—`. The user fills these in after reviewing the build.
Set `Complexity` to `focused`, `solid`, or `ambitious` to match what was built.

Status: `complete`, `partial`, or `aborted`

Do not rewrite or delete any existing rows.

---

## Step 10 — Commit, Push, and Open Pull Request

**Branch:** If currently on `main`, create a dedicated build branch before staging:
```bash
git checkout -b build/YYYY-MM-DD-title-slug
```
If already on a non-main branch (Routines sessions start on their own branch), stay on it.

Stage only:
- Everything in `builds/YYYY-MM-DD-title-slug/`
- `builds/index.md`
- `builds/ideas.md` if modified by lottery status updates or fresh idea appends

Do not stage any other files.

Commit message format:
```
build(YYYY-MM-DD): [Title] — [Category ID + Name]

[One sentence describing what was built and what it does.]
```

Push to origin:
```bash
git push -u origin $(git branch --show-current)
```

**Open a pull request targeting `main`:**
```bash
gh pr create \
  --base main \
  --title "build(YYYY-MM-DD): [Title] — [Category ID + Name]" \
  --body "## What was built
[One paragraph: what it is, why tonight, what problem it solves]

## Tech
[Stack and key dependencies]

## Test results
Tests: X passed, 0 failed

## Key files
- \`PRD.md\` — full spec
- \`BUILD_LOG.md\` — session log
- \`Manual.md\` — usage instructions (if applicable)"
```

If push fails, wait 4 seconds and retry once. If it fails again, log the failure in `BUILD_LOG.md` and stop — do not force push. Do not open a PR if the push failed.

---

## Abort Protocol

If at any point a build cannot be completed safely and reversibly, stop immediately.

**Abort if:**
- The build would require modifying files outside `builds/YYYY-MM-DD-title-slug/` and `builds/index.md`
- The build requires credentials not already in the environment
- The build cannot be self-contained (requires external infrastructure to function)
- A hard standard from `STANDARDS.md` cannot be met and there is no safe workaround

**When aborting:**
1. Create `builds/YYYY-MM-DD-title-slug/ABORTED.md` with:
   - Date and time (UTC)
   - What you were attempting to build
   - The specific reason for aborting
   - What would be needed to attempt it safely in the future
2. Update `builds/index.md` with status `aborted`
3. Commit and push with message: `build(YYYY-MM-DD): ABORTED — [brief reason]`

Never abort silently. The abort commit is the deliverable.

---

## Tone and Craft

Build things worth using. The user opens each build the morning after and decides whether it earns a place in their life — the best outcome is a tool they reach for again.

At every complexity level, the goal is the same: working code connected to real data, tested against real failure modes, with a clear and honest implementation. Focused builds are held to the same standard as ambitious ones — scope differs, quality does not.

Three things to get right in every build:

- **Real data over manual entry.** If the user's data exists somewhere accessible — GitHub, public APIs, files on disk — the build should work with it. Tools that pull from real sources deliver value automatically; tools that require the user to maintain them manually often go unused.
- **Honest tests.** Test the failure modes that actually matter for this logic. Tests that exist only to reach a minimum count add noise, not confidence.
- **Complete scope.** What ships must be genuinely useful in its delivered state. Features that are prerequisites for usefulness belong in this build, not in FutureFeatures.md.
