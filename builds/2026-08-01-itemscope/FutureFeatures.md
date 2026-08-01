# Future Features — ItemScope

1. **Full option-universe input** — accept an optional `--options` file listing every valid answer choice per item (not just the ones observed in the data), so a distractor that nobody at all selected (not even middle-scoring students) can be flagged as truly non-functioning, rather than only detecting options absent among the extreme scoring groups.

2. **Partial-credit / polytomous items** — extend beyond binary right/wrong to rubric-scored items (e.g. 0–5 points), using item-total correlation on the continuous score instead of point-biserial, so short-answer and essay rubric scores can be analyzed alongside MCQ items in the same report.

3. **Multi-run history and item banking** — persist results per exam file (keyed by a stable exam ID) in local SQLite so the same exam's item performance can be tracked across multiple terms, showing whether a revised item actually improved after a previous flag.

4. **Blueprint/learning-objective tagging** — let the instructor tag each item with a topic or learning objective in a companion CSV, then roll up difficulty/discrimination by objective to see which course topics are systematically under-taught or over-tested.

5. **Differential item functioning (DIF) check** — given an optional grouping column (e.g. section, cohort), flag items where difficulty or discrimination differs substantially between groups, which can surface fairness issues invisible in an aggregate-only report.

6. **LMS export format support** — direct parsers for common LMS gradebook export shapes (Canvas quiz item analysis CSV, Blackboard item analysis export) instead of requiring the instructor to reformat into ItemScope's generic CSV shape first.
