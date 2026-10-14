# Future Features

1. **Snapshot history:** store each run's analysis in SQLite and chart week-over-week change in wasted minutes across invocations, not only within one window.
2. **Workflow YAML linting:** fetch the workflow file and confirm findings against it (missing `concurrency`, no `timeout-minutes`, no `paths` filter) and emit a ready-to-apply diff.
3. **Exact billing:** use the per-run timing and org billing endpoints when the token has the scope, replacing the estimate.
4. **Queue time analysis:** separate time waiting for a runner from execution time, using job `created_at` vs `started_at`.
5. **Matrix leg breakdown:** group jobs by matrix parameters to show which leg is the long pole.
6. **Routine packaging:** a weekly Claude Code Routine that runs the tool and notifies only when wasted minutes rise more than a set percentage.
7. **Failure clustering:** pull failed-step log tails and have Claude group failures by root cause.
