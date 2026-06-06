# STANDARDS.md — Build Quality Standards

> Every nightly build must pass ALL hard standards before being committed.
> Soft standards should be met; deviations must be documented in BUILD_LOG.md.
> Claude: treat this file as a checklist to execute, not documentation to absorb.

---

## Hard Standards (Violations Abort the Build)

### Safety & Reversibility
- [ ] All build output is entirely within `builds/YYYY-MM-DD/`
- [ ] The only file outside the build folder that is modified is `builds/index.md`
- [ ] No build file imports from, references, or modifies another build's folder
- [ ] No system-level operations (no `rm -rf`, no system file writes, no registry edits)
- [ ] No credentials, API keys, or passwords hardcoded in source files
- [ ] No personal data (real names, real emails, real addresses) hardcoded in code
- [ ] No external HTTP calls in the build scaffold itself (individual apps may make calls only to pre-configured services listed in PROFILE.md)

### Completeness
- [ ] `PRD.md` exists and all sections are filled — no `[YOUR ANSWER]` or `[TBD]` placeholders
- [ ] `WhyThis.md` exists and explains the specific rationale for tonight's choice
- [ ] `BUILD_LOG.md` exists and has at least one entry per major phase
- [ ] `FutureFeatures.md` exists and has at least 5 concrete suggestions
- [ ] All code runs without modification (no broken imports, missing files, missing dependencies)
- [ ] `builds/index.md` has been updated with this build's entry

### Documentation
- [ ] `Manual.md` exists for any build with a user interface
- [ ] Every function or class over 10 lines has a descriptive docstring or comment block

---

## Soft Standards (Deviations Must Be Documented in BUILD_LOG.md)

### Code Quality
- Prefer standard library over third-party dependencies
- No unused imports, variables, or dead code
- Consistent indentation: 2 spaces for JS/HTML/CSS, 4 spaces for Python
- Meaningful variable names — no single-letter names except loop counters (`i`, `j`, `k`)
- No `console.log` or `print` debug statements in production code (use a `DEBUG` flag or structured logging)

### HTML/CSS/JS Builds
- Must work in modern browsers without a build step (no compilation required)
- CSS uses custom properties (variables) for colors and key spacing values
- Mobile-responsive: at minimum, does not break on narrow screens
- No external CDN dependencies unless a local fallback is provided
- Accessible: semantic HTML elements, `alt` attributes on images, sufficient color contrast
- Dark/light mode considered even if only one is implemented

### Python Builds
- Type hints on all function signatures
- `if __name__ == "__main__":` guard in the entry point
- `requirements.txt` present even if empty (signals stdlib-only intent)
- Common error cases handled gracefully (file not found, malformed input, wrong argument count)

### Node.js / React Builds
- `package.json` with accurate `name`, `version`, `description`, and `main` or `scripts.start`
- `.gitignore` note for `node_modules/` inside the build folder's README or PRD
- Lock file (`package-lock.json`) committed if `npm install` was actually run

### Scope Discipline
- If scope had to shrink mid-build, add a "Scope Changes" subsection to PRD.md explaining what was dropped and why
- A partial build done well is better than an ambitious build done poorly
- If a feature can't be done correctly, remove it rather than shipping it broken

---

## Build Folder Structure Standard

```
builds/YYYY-MM-DD/          ← Everything lives here
├── PRD.md                  ← Required always
├── WhyThis.md              ← Required always
├── BUILD_LOG.md            ← Required always
├── FutureFeatures.md       ← Required always
├── Manual.md               ← Required if any UI exists
├── index.html              ← Single-file web apps: place at folder root
└── src/                    ← Multi-file builds: all code lives here
    ├── main.py             ← (or main.js, index.js, App.jsx, etc.)
    └── ...
```

For aborted builds:
```
builds/YYYY-MM-DD/
└── ABORTED.md              ← This file only; no other files
```

---

## Security Checklist (Run Before Every Commit)

Search your own created files for these patterns before committing:

- [ ] No `.env` files committed
- [ ] No occurrences of: `password`, `api_key`, `secret`, `token`, `private_key` with real values assigned
- [ ] No `eval()` or `exec()` on user-controlled input
- [ ] No `innerHTML` assignments from user-controlled data (XSS vector)
- [ ] No `os.system()` or `subprocess` calls with user-controlled arguments (injection vector)
- [ ] No file path traversal: user input must never be used directly in file paths
- [ ] No code that reads from paths outside the build's own folder

---

## "Done" Definition

A build is complete when ALL of the following are true:

1. All hard standards pass
2. The code runs as described in `Manual.md` (or `PRD.md` if no Manual)
3. `BUILD_LOG.md` final entry reads: `Build complete. Success criteria reviewed.`
4. `builds/index.md` has been updated with this build's row
5. All changes are committed and pushed to the remote
