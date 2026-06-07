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
ls builds/ | grep -E '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' | sort
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

Read these three files IN ORDER before doing anything else:

1. `PROFILE.md` — who you are building for; their interests, job, preferences
2. `builds/index.md` — what has already been built; avoid repeating categories
3. `STANDARDS.md` — the non-negotiable quality and safety requirements

Get today's date in UTC. Your build folder will be `builds/YYYY-MM-DD/`.

---

## Step 2 — Decide What to Build

### 2a — Determine Tonight's Complexity Target

Get today's day of week: `date +%u` (1=Monday, 7=Sunday)

| Day | Complexity Target |
|-----|-------------------|
| 1 Monday | Focused Utility — 1–3 source files, usable in under 5 minutes |
| 2 Tuesday | Solid Feature — 3–8 source files, moderate scope |
| 3 Wednesday | Ambitious Project — 8+ source files, rich UI or deep logic |
| 4 Thursday | Focused Utility |
| 5 Friday | Solid Feature |
| 6 Saturday | Ambitious Project |
| 7 Sunday | Focused Utility |

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

### 2c — Choose Tonight's Category

Check the "Last 7 Builds" section of `builds/index.md`. Choose a category not recently used.
If the preference prior (Step 2b) revealed strong category preferences, factor that in —
but don't let it override the rotation entirely. Variety matters.

| ID | Category | Examples |
|----|----------|---------|
| A  | Dashboard / Visualizer | Data display, charts, live stats, status boards |
| B  | Productivity Utility | Automation scripts, workflow tools, batch processors |
| C  | Personal Knowledge Tool | Note capture, knowledge base, reading tracker, index |
| D  | Creative / Generative | Writing prompts, generators, art tools, randomizers |
| E  | Learning Aid | Flashcards, reference sheets, interactive explainers |
| F  | Data Explorer | CSV/JSON processor, log analyzer, stats calculator |
| G  | Game / Puzzle | Browser game, logic puzzle, word game, quiz |
| H  | Developer Tool | Code formatter, schema inspector, diff tool, snippet library |
| I  | Life Admin Helper | Budget tracker, meal planner, habit log, checklist |

Choose the category now. Both the lottery and fresh idea generation use it.

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

Generate at least 3 candidate ideas within tonight's chosen category and complexity target.
For each, evaluate:

- **Self-contained?** No cloud infrastructure required, no unconfigured paid APIs
- **Reversible?** Deleting the folder removes it entirely
- **Genuinely useful?** Connected to this specific user's life — apply preference prior here
- **Practically useful?** The build must be useful in its delivered state — not just theoretically useful if a future feature were added. Before committing to an idea, ask: "Is there a critical missing piece that would be needed before this is actually used?" If yes, that piece must be part of tonight's scope, not deferred to FutureFeatures.md. FutureFeatures.md is for enhancements to a working, useful thing — not prerequisites for usefulness.
- **Self-sustaining?** Prefer builds that deliver value automatically or reduce existing friction over builds that require the user to adopt a new manual habit. A tool that runs itself or removes a task is worth more than one that adds a task. (This criterion applies most to productivity/utility builds; it does not penalise games, learning aids, or creative tools.)
- **Novel?** Not substantially similar to something in `builds/index.md`
- **Achievable?** Realistic scope for tonight's complexity target
- **Right stack?** Matches the user's preferred tech from PROFILE.md
- **Testable?** Core logic can be verified with automated tests

Pick the idea that scores best overall. If no idea scores well, choose the simplest genuinely useful thing in the selected category.

**After choosing, append every non-winning candidate to `builds/ideas.md`** with:
- A new sequential ID (increment from the last row)
- Today's date
- Tonight's category ID
- Tonight's complexity target (`focused`, `solid`, or `ambitious`)
- Status: `pending`
- Your Rating: `—`
- Rating Notes: `—`

Only append ideas that aren't already present in the file. Do not add the winning idea.

---

### 2f — Choose the Tech Stack

Based on the chosen idea and PROFILE.md preferences:

- **Single-use browser tool / dashboard / game:** Vanilla HTML/CSS/JS — `index.html` at root, Playwright for tests
- **Data processing / automation / CLI:** Python 3 with stdlib; add dependencies only when necessary; pytest for tests
- **Richer interactive app:** React + Vite only when complexity target is Ambitious and vanilla JS would be genuinely limiting; Vitest for tests
- **Node.js utility:** When the task is clearly JS-ecosystem; Jest or Vitest for tests

Default toward the simpler option unless complexity genuinely requires more.

---

## Step 3 — Create the Build Folder

Create: `builds/YYYY-MM-DD/`

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
- Use `builds/YYYY-MM-DD/` as root; never reference paths outside it

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
- Make external HTTP calls from the build scaffold (app code may, if PROFILE.md lists pre-configured services)
- Import from or reference another build's folder
- Use `eval()`, `exec()`, or user-controlled strings in shell calls

### Writing Tests

Tests are not optional. Write them as you build — not as an afterthought.

**Minimum test requirements by complexity:**

| Complexity | Minimum Tests | Coverage |
|------------|---------------|----------|
| Focused Utility | 3 tests | Core function(s) happy path + 1 edge case |
| Solid Feature | 5 tests | All main features, 2+ edge cases |
| Ambitious Project | 8 tests | Happy paths, edge cases, error states |

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

## Step 10 — Commit and Push

Stage only:
- Everything in `builds/YYYY-MM-DD/`
- `builds/index.md`

Do not stage any other files.

Commit message format:
```
build(YYYY-MM-DD): [Title] — [Category ID + Name]

[One sentence describing what was built and what it does.]
```

Push to origin. If push fails, wait 4 seconds and retry once. If it fails again, log the failure in `BUILD_LOG.md` and stop — do not force push.

---

## Abort Protocol

If at any point a build cannot be completed safely and reversibly, stop immediately.

**Abort if:**
- The build would require modifying files outside `builds/YYYY-MM-DD/` and `builds/index.md`
- The build requires credentials not already in the environment
- The build cannot be self-contained (requires external infrastructure to function)
- A hard standard from `STANDARDS.md` cannot be met and there is no safe workaround

**When aborting:**
1. Create `builds/YYYY-MM-DD/ABORTED.md` with:
   - Date and time (UTC)
   - What you were attempting to build
   - The specific reason for aborting
   - What would be needed to attempt it safely in the future
2. Update `builds/index.md` with status `aborted`
3. Commit and push with message: `build(YYYY-MM-DD): ABORTED — [brief reason]`

Never abort silently. The abort commit is the deliverable.

---

## Tone and Craft

Build things worth keeping. Nightly does not mean rushed.

- A focused utility done beautifully and fully tested is better than an ambitious project done sloppily
- Build things that are practically useful now, not theoretically useful once a future feature is added — if a feature is required for the build to actually be used, it belongs in this build's scope
- If scope needs to shrink to maintain quality, shrink scope — document it in PRD.md
- Use real variable names, real error messages, real UI copy
- Tests document what the code is supposed to do — write them as if they are specifications
- Consider the user opening this 3 months from now with no context — will it make sense?
- The documentation and tests are part of the build, not afterthoughts
