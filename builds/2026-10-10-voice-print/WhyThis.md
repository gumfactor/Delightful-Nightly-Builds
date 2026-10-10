# Why This

**Source:** fresh generation (no pending Category D rows in the backlog, so no lottery roll; pool size 0).

**Topic diversity:** the last 10 builds are heavy on finance, GitHub and CLI report tools. This is a writing tool.

**Why it fits the profile:** PROFILE.md says the user dislikes obviously AI-generated writing, writes blogs, papers and a book, and keeps losing time editing. Past low ratings came from tools a single Claude prompt replaces (AI Lecture Builder, 2) or that lack depth. This build's differentiating layer is local and quantitative: a stylometric profile of the user's own voice plus located, explainable flags. A chat prompt cannot measure sentence-length burstiness against your own baseline, and it does not keep your voice profile between sessions.

**Design choices:** no API call from the page. Drafts stay on the device, and the tool works offline. The AI step is a generated revision prompt the user can paste into Claude. It is a style linter, not a detector, and says so.

**Rejected:** a live-weather generative landscape (delightful, but low in the user's value ranking); a lecture/case-vignette generator (duplicates the 06-24 build).
