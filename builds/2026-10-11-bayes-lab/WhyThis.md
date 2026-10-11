# Why This? — Bayes Lab

> **Date:** 2026-10-11

## How This Idea Was Selected

**Selection method:** Fresh generation. Day of year 284 → category index 4 (E — Learning Aid). `builds/ideas.md` had no pending Category E rows, so the lottery was skipped (pool size 0, no roll).

Other candidates considered: (1) a neuroimaging-stats explainer (multiple comparisons / cluster correction visualised), (2) a Canadian-business classification trainer for Canada List QC, (3) this one. Candidates 1 and 2 are appended to `builds/ideas.md`.

## The Decision

Bayes Lab won because it hits the profile's explicit learning goal ("develop advanced Bayesian statistical workflows"), the user teaches psychologists and can reuse it in class, and it avoids the failure patterns in past ratings: it has a real interactive interface, no mock data (every number is computed live from inputs, including the user's own study counts/estimates), and it does something a single Claude prompt cannot — live manipulation with verified numerics. Finance/investment topics are saturated in the last 10 builds, so none were considered.

## Connection to User Context

PROFILE.md: "Develop advanced Bayesian statistical workflows", teaching "AI Applications for Psychologists", forensic/affective neuroscience (the base-rate lesson uses screening and lie-detection framings), and an evidence-driven temperament (the calibration quiz scores honesty about uncertainty). It works offline on a phone.

## Why Tonight

Category rotation said Learning Aid; the ambition floor requires it to be interactive, which this is. No AI/API layer was used deliberately: sending a student's data to an API from a static page wasn't worth the key-handling risk, and the value is in the live numerics.
