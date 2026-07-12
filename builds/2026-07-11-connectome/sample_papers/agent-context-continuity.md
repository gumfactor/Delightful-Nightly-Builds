# Context Continuity in Long-Running AI Agent Workflows

Abstract: Autonomous coding agents that operate across many short sessions
face a recurring failure mode — the working context built up during one
session is lost when the next session begins, forcing either expensive
re-derivation or silent loss of prior reasoning. We survey handoff strategies
across several agent frameworks and find that the most robust approaches
treat context reconstruction as a workflow design problem rather than a
note-taking problem: context is rebuilt automatically from structured
artifacts (commit history, checkpoint files, decision logs) rather than
relying on the agent or the user to manually summarize state at session end.

We evaluate three handoff strategies on a benchmark of multi-session coding
tasks: (1) freeform end-of-session summaries, (2) structured checkpoint
files capturing objective, decisions-with-rationale, and next steps, and (3)
fully automatic reconstruction from git history alone. Structured
checkpoints outperform freeform summaries on downstream task continuity,
while automatic reconstruction alone underperforms both — commit messages
capture *what* changed but rarely *why*, and the rationale behind a decision
is exactly what a new session most needs to inherit.

Implication for practitioners: session handoff tooling should preserve
decision rationale as a first-class artifact, not an afterthought bolted
onto commit messages.
