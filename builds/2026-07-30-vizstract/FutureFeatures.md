# Future Features — Vizstract

1. **More study-design templates.** Case study/qualitative, mediation/moderation (three-node path diagram), and meta-analysis (forest-plot-style) templates would round out the coverage beyond the current 5 quantitative-leaning designs.

2. **Drag-to-reposition regions.** Currently each template's layout is fixed; letting the user nudge an icon box or the callout within the canvas (with the same non-overlap/text-fitting guarantees) would help for the occasional study whose default layout doesn't quite fit the content.

3. **Import a whole library as a single ZIP/JSON bundle.** Right now each saved abstract lives only in this browser's localStorage. An export-all/import-all JSON file would let the user move their library to another machine or back it up outside the browser.

4. **A "recent template" quick-duplicate action.** For a researcher producing several visual abstracts for a symposium or a multi-study paper, a "duplicate this saved entry as a starting point" action would save re-typing population/sample fields that repeat across studies from the same lab.

5. **PDF export.** SVG/PNG cover manuscript and slide use; a direct PDF export (via the browser's print-to-PDF on a dedicated print stylesheet) would match journals that require PDF-only supplementary figure uploads.

6. **A second AI-assisted step: suggest a headline finding from the raw stats.** Today AI extraction only pulls out fields already present in the pasted abstract text. A follow-on feature could take structured stats (effect size, p-value, direction) the user enters directly and have Claude draft a candidate headline-finding sentence for the user to accept or edit.

7. **Custom icon slots.** The built-in ~22-icon library was kept deliberately small and hand-authored for safety and simplicity. A future version could let advanced users register additional named icons (still inline SVG paths, still no external image uploads) for domains the default set doesn't cover well (e.g., neuroimaging-specific pictograms for fMRI/EEG studies).
