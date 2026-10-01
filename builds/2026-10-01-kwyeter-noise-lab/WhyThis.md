# Why This? — Noise Lab

> **Date:** 2026-10-01

## How This Idea Was Selected
**Selection method:** Fresh generation. Day of year 274 gives category index 3 = D (Creative / Generative). `builds/ideas.md` had no pending D entries, so the lottery was skipped (no roll needed; pool size 0).

## The Decision
Noise Lab. The previous D build (AI Lecture Builder, rated 2) failed because one Claude prompt reproduces it. This one has no prompt equivalent: it does signal processing and gives you a sound plus a measurement of it. I weighed the earlier ratings: visual interface and a differentiating layer matter, and mock/localStorage-only data is penalised. Here there is no external data to mock, and the output is the thing itself.

## Connection to User Context
Kwyeter is about environmental noise, sensory sensitivity and tinnitus. Notched noise at the tinnitus pitch is a real research paradigm, and the A-weighting/spectrum readouts line up with what Kwyeter cares about. The profile also asks for tools that "just work" and are mobile-readable.

## Why Tonight
Category rotation. The recent run is dominated by finance and Python CLIs; this is a browser audio tool in a new domain (acoustics), with no finance, no GitHub, no Anthropic dependency.

## What I Hope the User Gets From This
1. A sleep/focus noise generator on a phone, with seamless loops that can be exported for any player.
2. A way to prototype Kwyeter-style soundscapes and spectra, and verify them numerically.
3. A reusable DSP module (`src/dsp.js`) that Kwyeter code could borrow.

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| Canada List product-description voice rewriter | D | AI rewriting is again replicable by a single prompt, which sank the Lecture Builder |
| Generative stress-and-coping case vignette studio | D | Same weakness: text generation without a differentiating layer |
| Generative lab-logo/figure palette tool | D | Pleasant but low utility versus the profile's priorities |
