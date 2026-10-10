# Future Features

1. **Per-sentence voice distance**: score each sentence against the profile and shade the draft by how un-you it is, rather than only flagging known phrases.
2. **Profile from files**: drop a folder of .docx/.md/.txt (manuscripts, blog posts) and build the profile in one pass, with per-document weighting.
3. **Learned personal tells**: let the user mark flags as "I do write this" so the detector lexicon adapts per person; store in the profile.
4. **Draft history**: keep AI-tell and voice-match per saved draft in IndexedDB and chart the trend across a book's chapters.
5. **Optional API revision**: with a user-supplied `ANTHROPIC_API_KEY` in a local proxy script, apply the revision prompt and show a diff, keeping the browser page offline by default.
6. **Multiple voices**: separate profiles (academic, blog, email) with a selector, since one person writes differently by genre.
7. **Claude Code skill**: wrap `analyzer.js` in a Node CLI plus `/voice-check` skill so drafts in a repo can be checked before commit.
