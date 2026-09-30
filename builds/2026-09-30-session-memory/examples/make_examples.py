"""Regenerates the synthetic example transcripts in this folder (fictional content)."""
import json
from pathlib import Path

HERE = Path(__file__).parent


def claude_code(session_id, cwd, branch, turns):
    return [
        json.dumps({"type": role, "sessionId": session_id, "cwd": cwd, "gitBranch": branch, "timestamp": ts,
                    "message": {"role": role, "content": content}})
        for role, content, ts in turns
    ]


def edit(path):
    return {"type": "tool_use", "name": "Edit", "input": {"file_path": path}}


def text(value):
    return {"type": "text", "text": value}


sessions = {}
sessions["canada_list_encoding"] = claude_code("a1", "/work/canada-list", "main", [
    ("user", "The ingestion pipeline is dropping rows with accented province names. Can you find out why?", "2026-09-12T14:02:00Z"),
    ("assistant", [text("The CSV reader opens files with the default cp1252 codec, so 'Québec' is mangled before the province lookup. I'll switch to utf-8-sig."), edit("pipeline/load.py")], "2026-09-12T14:04:00Z"),
    ("user", [{"type": "tool_result", "content": "ok"}], "2026-09-12T14:04:10Z"),
    ("assistant", "Fixed. Decided to normalise province names with unicodedata NFC instead of maintaining an alias table.\n\nNext steps:\n- Add a regression test for Québec and Nunavut\n- Re-run the June batch through the loader", "2026-09-12T14:09:00Z"),
])
sessions["canada_list_dedupe"] = claude_code("a2", "/work/canada-list", "main", [
    ("user", "Let's add a duplicate-detection pass before insert. Fuzzy match on business name plus postal code.", "2026-09-19T10:00:00Z"),
    ("assistant", [text("We'll go with rapidfuzz token_set_ratio at 92 plus exact postal code match. Instead of a global pass I'll compare within postal-code buckets, which keeps it O(n) in practice."), edit("pipeline/dedupe.py"), edit("pipeline/load.py")], "2026-09-19T10:05:00Z"),
    ("user", "Good. What about franchises that share a name across cities?", "2026-09-19T10:07:00Z"),
    ("assistant", "Postal code bucketing handles that: same name in different buckets never compares.\n\nOpen questions:\n- Should chain locations be merged under one parent record?\n- What threshold do we use for names under 6 characters?", "2026-09-19T10:09:00Z"),
])
sessions["stress_book_ch4"] = claude_code("a3", "/work/stress-book", "draft", [
    ("user", "Outline chapter 4 on cortisol reactivity and coping style, aimed at general readers.", "2026-09-25T18:30:00Z"),
    ("assistant", "Chapter 4 outline: the stress response in plain language, why reactivity differs between people, coping style as a modifier, and three practices readers can test themselves.", "2026-09-25T18:33:00Z"),
])
for name, session_lines in sessions.items():
    (HERE / f"claude_code_{name}.jsonl").write_text("\n".join(session_lines) + "\n")

claude_ai = [{
    "uuid": "c1", "name": "Grant aim wording for empathy study", "created_at": "2026-09-02T13:00:00Z",
    "chat_messages": [
        {"sender": "human", "text": "Help me tighten Specific Aim 2 on vicarious pain and callous-unemotional traits.", "created_at": "2026-09-02T13:00:00Z"},
        {"sender": "assistant", "text": "Aim 2 currently makes three claims. Split it: (a) test whether CU traits blunt anterior insula response, (b) test moderation by attention to the victim's face. We decided to drop the developmental claim from this aim.", "created_at": "2026-09-02T13:02:00Z"},
    ],
}]
(HERE / "claude_ai_export.json").write_text(json.dumps(claude_ai, indent=1))


def node(node_id, parent, role, body, created):
    return {"id": node_id, "parent": parent, "message": {
        "author": {"role": role}, "create_time": created, "content": {"content_type": "text", "parts": [body]}}}


mapping = {
    "root": {"id": "root", "parent": None, "message": None},
    "n1": node("n1", "root", "user", "Best way to structure a Bayesian mixed model for repeated cortisol samples in R?", 1790000000),
    "n2": node("n2", "n1", "assistant", "Use brms with a random intercept and slope per participant, weakly informative priors, and a log link if cortisol is right skewed.", 1790000060),
}
chatgpt = [{"conversation_id": "g1", "title": "brms model for cortisol", "create_time": 1790000000, "current_node": "n2", "mapping": mapping}]
(HERE / "chatgpt_export.json").write_text(json.dumps(chatgpt, indent=1))
