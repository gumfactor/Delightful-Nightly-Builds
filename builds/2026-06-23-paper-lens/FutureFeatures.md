# Future Features — Paper Lens

## 1. Additional Sources: Semantic Scholar & PubMed
Extend the fetcher to pull from Semantic Scholar API (free, returns citation counts and references) and PubMed (NCBI E-utilities, free, covers clinical neuroscience that arXiv misses). Semantic Scholar also returns open-access PDF links. This would triple coverage for affective and clinical neuroscience research.

## 2. Claude Code Skill: `/paper-brief [topic]`
Package the fetch + analyze pipeline as a Claude Code Skill that can be invoked during a coding session. Running `/paper-brief stress neuroscience` would search for recent papers, call the Anthropic API, and return a formatted markdown synthesis directly in the Claude Code session — useful when writing grants or preparing literature review sections.

## 3. Configurable Topic Profiles
Allow users to define their own search profiles in `config.json` instead of hard-coded topics. Each profile would have a name, arXiv query, max results, and a plain-language description of research interest. The Anthropic prompt would dynamically adapt to the profile description, making Paper Lens usable by any researcher, not just the default profile.

## 4. Weekly Synthesis Email / Routine
Package as a Claude Code Routine that runs Sunday night, collects all papers fetched during the week, and uses the Anthropic API to generate a "weekly synthesis" — one paragraph per research area summarizing the week's most significant findings and identifying emerging patterns across papers.

## 5. Citation Network: "Who cites this?"
After a paper is saved, fetch its citation count and top citing papers from Semantic Scholar's free API. Display the "influential citations" as a linked list on the paper card, enabling the user to follow a paper's intellectual lineage forward in time — useful for identifying which of their saved papers is generating follow-up work.

## 6. Note Annotations with AI Feedback
Add a `note` CLI command to attach a free-text note to any paper. When a note is added, send the abstract + note to Claude and ask: "What about this paper did the researcher find interesting? What questions does it raise for their work?" Save the AI response as a second annotation. This creates a private dialogue record that makes the knowledge base searchable by intellectual interest, not just keywords.

## 7. Export to Formatted Literature Review Section
Add an `export` command that takes a set of arxiv IDs and produces a formatted literature review draft — ordered by topic cluster, with citations in APA format. The Anthropic API would write a coherent synthesis paragraph for each cluster. Output as markdown with a LaTeX citation block.
