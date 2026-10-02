# Build Log — Replication Lab

- [Phase: orient] Today 2026-10-02, day 275, category index 4 = E Learning Aid. Latest complete build found on branch cool-sagan-ewo9z6 (Noise Lab, 2026-10-01), so no interrupted build to resume. Index and ideas copied from that branch. No pending E ideas: fresh generation.
- [Phase: PRD] PRD written before code.
- [Phase: build] Stats core first (seeded RNG, incomplete beta, t-test, power, peeking, forking, beta-binomial). 31 Node-side tests passed on the first run.
- [Phase: build] UI: five labs, predict-first flow, canvas charts, calibration score.
- Decision: Anthropic API left out. A deterministic offline simulator is the differentiator; a tutor needs a key-handling design that belongs in a later build.
- Decision: the Bayes lab is live and has no prediction prompt; the other four need a run button because they simulate.
- Visual check via screenshot at 390px: overlapping vertical-line labels in the winner's curse chart. Fixed by staggering label rows. The calibration score mixed units for the effect-size prediction; it now only counts percent-scale predictions.
- Not verified: only Chromium was tested; no real-device phone check.
- [Tests] Tests: 41 passed, 0 failed (31 stats, 10 UI).
- Security checklist: no innerHTML, no eval, no network calls, no credentials, no file paths from user input.
- Build complete. Success criteria reviewed. All tests passing.
