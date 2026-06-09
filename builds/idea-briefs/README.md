# Idea Briefs

This directory contains durable planning documents for backlog ideas that need
more detail than fits in `builds/ideas.md`.

An idea brief is an input to a future nightly build, not that build's final
specification. When a linked idea is selected, the builder must:

1. Read its brief before choosing the implementation scope or technology.
2. Reconcile the brief with `PROFILE.md`, current tools, and the night's
   complexity target.
3. Write a fresh `PRD.md` inside the dated build folder.
4. Preserve the brief's essential value proposition while documenting any
   deliberate scope changes in `WhyThis.md` and the build PRD.

Briefs remain here after an idea is built so the original intent and eventual
implementation can be compared.
