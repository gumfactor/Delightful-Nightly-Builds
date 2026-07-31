# Future Features

1. **Full BIDS entity coverage** — add `dir`, `rec`, `ce`, `part`, `chunk`,
   `space`, `hemi`, and the MEG/EEG/iEEG-specific entities so the tool
   covers more than the anatomical/task-fMRI subset it handles tonight.

2. **Fieldmap `IntendedFor` linking check** — verify that each fieldmap's
   sidecar JSON correctly references the functional runs it corrects,
   which is one of the most common real-world BIDS violations in fMRI
   labs and currently entirely out of scope.

3. **`.tsv` column-schema validation** — check that `events.tsv` files
   have the required `onset`/`duration` columns and that `participants.tsv`
   matches the subjects actually present in the dataset.

4. **Directory-aware renaming in `--apply`** — extend the safe-fix engine
   to also rename `sub-`/`ses-` *directories* (not just filenames) when a
   padding mismatch is consistent across an entire subject's folder,
   with the same overwrite-refusal and root-containment guarantees.

5. **BIDS-validator schema cross-check** — optionally shell out to the
   official `bids-validator` npm tool (if installed) and merge its
   findings with this tool's own, so users get full spec coverage when
   available and this tool's faster, dependency-free subset otherwise.

6. **Watch mode** — a `--watch` flag that re-scans a dataset directory on
   file-system changes (e.g. as RAs add new scan sessions) and prints only
   the *new* findings since the last run, turning this from a one-shot
   check into a standing QA layer during active data collection.
