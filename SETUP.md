# SETUP.md — Getting the System Running

> Read this after the system files have been committed. These are the steps
> only you can do — they require your Claude account and GitHub settings.

---

## Step 1: Fill Out PROFILE.md

This is the most important step. Open `PROFILE.md` and fill in every section.

The more specific you are, the more relevant the builds will be. Don't write
"I like music" — write "I play fingerpicking guitar and have been learning
Chet Atkins tunes for the last year." The difference in build quality is enormous.

**Tip:** If you have a previous conversation with Claude where you described
yourself, paste the relevant parts in. Claude cannot access other chat sessions,
so PROFILE.md is its only window into who you are.

---

## Step 2: Set Up Nightly Scheduling

### Option A: Claude Code Routines (Recommended — you have Pro/Max)

Routines run on Anthropic's cloud. No machine needs to be on. No GitHub minutes used.

1. Go to **[claude.ai/code/routines](https://claude.ai/code/routines)**
2. Click **New Routine**
3. Fill in:
   - **Name:** Nightly Build
   - **Repository:** `gumfactor/delightful-nightly-builds`
   - **Branch:** the branch this repo is on (or `main` once merged)
   - **Schedule:** Daily at your preferred time (e.g. 2:00 AM in your local timezone)
4. For the **Prompt**, paste this exactly:

```
You are running a scheduled nightly build session for the Delightful-Nightly-Builds repository.

Your full operating instructions are in CLAUDE.md at the root of this repo. Read it now before doing anything else.

Your task: build one new project tonight by following the process in CLAUDE.md exactly.

1. Read CLAUDE.md, PROFILE.md, and builds/index.md to orient yourself.
2. Decide what to build using the framework in CLAUDE.md Section 2.
3. Create builds/YYYY-MM-DD/ (today's UTC date).
4. Write PRD.md first — then build — then write all documentation.
5. Verify your build meets the PRD success criteria.
6. Update builds/index.md with tonight's entry.
7. Commit and push. Stage only builds/YYYY-MM-DD/ and builds/index.md.

Constraints:
- Do not modify any files outside builds/YYYY-MM-DD/ and builds/index.md.
- If you cannot complete the build safely, follow the Abort Protocol in CLAUDE.md.
- Do not ask for human input — make all decisions autonomously.
- Quality over quantity: a small, working, well-documented build is the goal.

Begin now.
```

5. Under **Permissions**, enable "Allow unrestricted branch pushes" so Claude can push the build commit.
6. Click **Save** and then **Run Now** to test it immediately.

### Option B: GitHub Actions (Fallback)

If you prefer GitHub Actions (or as a backup), the workflow is already at
`.github/workflows/nightly.yml`. You just need to add the API key:

1. Go to your repo on GitHub → **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Name: `ANTHROPIC_API_KEY`
4. Value: your Anthropic API key (from [console.anthropic.com](https://console.anthropic.com))
5. Save

The workflow runs at 2:00 AM UTC. To change the time, edit the `cron` line in
`.github/workflows/nightly.yml`.

To test immediately: go to **Actions** → **Nightly Build** → **Run workflow**.

---

## Step 3: Do a Test Run

Before relying on the nightly schedule, do a manual test run (Step 2 above).
After it runs, verify:

- [ ] A new `builds/YYYY-MM-DD/` folder exists with today's date
- [ ] It contains `PRD.md`, `WhyThis.md`, `BUILD_LOG.md`, `FutureFeatures.md`
- [ ] The code in the folder actually runs/opens
- [ ] `builds/index.md` has a new row appended
- [ ] The commit message follows the `build(YYYY-MM-DD): Title — Category` format
- [ ] No files outside `builds/YYYY-MM-DD/` and `builds/index.md` were modified

---

## Step 4: Review Builds in the Morning

Each morning, check the repo for last night's build:

```
builds/YYYY-MM-DD/
```

Read `WhyThis.md` to understand why Claude built what it built.
Read `PRD.md` to understand what it was supposed to do.
Try running it (`index.html` in a browser, `python3 main.py`, etc.).
Read `FutureFeatures.md` for ideas on where to take it.

**Your options:**
- **Keep as-is:** Do nothing. It's committed and safe.
- **Develop further:** Continue building in the same folder, or start a new session with context.
- **Delete:** Just delete the folder and commit the deletion. Clean and reversible.

---

## Running a Build's Tests Yourself

Each build includes a `tests/` folder with automated tests. To run them:

**Python builds:**
```bash
cd builds/YYYY-MM-DD
pip install -r requirements.txt   # if any
python -m pytest tests/ -v
```

**Vanilla HTML/JS builds (Playwright):**
```bash
cd builds/YYYY-MM-DD
npm install @playwright/test
npx playwright install chromium
npx playwright test
```

**React/Vite builds:**
```bash
cd builds/YYYY-MM-DD
npm install
npx vitest run
```

**Node.js builds:**
```bash
cd builds/YYYY-MM-DD
npm install
npx jest
```

---

## Session Resumption

If a nightly session hits a context/token limit mid-build, it ends without committing.
The next session automatically detects this (via `BUILD_LOG.md` — if it lacks "Build complete",
the build is considered incomplete) and resumes from where it left off before starting a new build.

For the GitHub Actions workflow: a second "Resume" job runs after the main job and handles this
automatically. For Routines: the CLAUDE.md Step 0 logic handles it on the next scheduled run.

---

## Tuning the System Over Time

**If builds feel generic:** Add more specific detail to `PROFILE.md`. The system is only as personal as the profile.

**If builds feel repetitive:** Check `builds/index.md` — Claude uses it to avoid repeats. If it's short, there may not be enough history yet.

**If builds are too ambitious / not working:** Note this in `PROFILE.md` under preferences. Claude reads it and will calibrate.

**If you want Claude to revisit a previous build:** Start a new Claude Code session, point it at the existing folder, and ask it to extend it.

**If you want to add a specific topic:** Add it to `PROFILE.md`'s "I wish I had a tool for" section. Claude will factor it in.

---

## What Claude Cannot Do (By Design)

- Access your other Claude chat history
- Use APIs you haven't listed in PROFILE.md
- Modify CLAUDE.md, PROFILE.md, STANDARDS.md, or templates/ (locked by settings.json)
- Force push or rewrite history
- Build things that touch files outside the dated build folder
