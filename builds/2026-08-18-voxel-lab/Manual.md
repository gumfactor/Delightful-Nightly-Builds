# Manual — Voxel Lab

## What it is
A self-contained browser trainer for two things: the standard fMRI preprocessing/analysis pipeline, and the multiple-comparisons ("dead salmon") problem — why testing tens of thousands of voxels without statistical correction produces false "activation" purely by chance. Everything is computed live in your browser from synthetic data. No real scan data, no network calls, nothing saved or sent anywhere.

## How to open it
No build step, no server, no install. Just open `index.html` directly in any modern browser:

```
open builds/2026-08-18-voxel-lab/index.html      # macOS
xdg-open builds/2026-08-18-voxel-lab/index.html  # Linux
```

Or double-click the file in a file browser.

## The three tabs

### Pipeline
Six canonical steps: Motion Correction, Slice Timing Correction, Spatial Normalization, Spatial Smoothing, HRF Convolution & GLM, Statistical Thresholding. Click the numbered circles to jump between steps. Each step shows a plain-English explanation, a live "Before"/"After" visual (toggle with the two buttons under the canvas), and a common pitfall if the step is skipped. The Smoothing step runs a real box-blur convolution on generated noise; the HRF/GLM step runs a real convolution and least-squares fit and reports the true-vs-recovered beta weight.

### Multiple Comparisons Lab
Set a voxel count (100–20,000), an alpha level (0.01–0.10), and a number of trials (1–200), then click **Run Simulation**. The tool generates pure-noise voxels — no true signal anywhere — and tests the *same* noise draw under four correction methods each trial: no correction, Bonferroni, Benjamini-Hochberg FDR, and cluster-extent. You'll see a per-method mean false-positive count, a bar chart, and four side-by-side "slices" showing exactly which voxels survived under each method on the last trial. At a few thousand voxels, expect uncorrected false positives in the hundreds while the corrected methods stay near zero — that's the point.

### Quiz
16 questions (10 conceptual multiple-choice, 6 "computed" questions whose correct answer and distractors are generated from the tool's real statistics functions each time you load the tab — not a fixed fact). Click a choice to see immediate feedback, then **Next**. A final score and grade appear after the last question.

## Running the tests
```
cd builds/2026-08-18-voxel-lab
npm install
npx playwright test
```
33 tests, all pass. See `PRD.md`'s Testing Strategy section for what's covered.

## Notes
- This is a teaching simulator, not a research analysis tool — it never loads or processes real neuroimaging data.
- Nothing you do in this tool is saved anywhere; refreshing the page resets everything.
