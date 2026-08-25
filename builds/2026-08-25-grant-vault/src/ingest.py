"""Orchestrates chunk -> classify -> score -> tag -> (optional AI) -> store."""

import sqlite3
from pathlib import Path

from src import ai_enrich, chunking, classifier, scorer, store, tagging

_ALLOWED_SUFFIXES = {".txt", ".md"}


def _collect_files(path: str) -> list[str]:
    target = Path(path)
    if target.is_file():
        return [str(target)]
    if target.is_dir():
        return sorted(
            str(f)
            for f in target.iterdir()
            if f.is_file() and f.suffix.lower() in _ALLOWED_SUFFIXES
        )
    raise FileNotFoundError(f"Path not found: {path}")


def ingest_path(
    path: str,
    conn: sqlite3.Connection,
    use_ai: bool = False,
    api_key: str | None = None,
) -> dict:
    """Ingest a single file or every .txt/.md file in a folder.

    Returns a summary dict: documents_processed, documents_skipped,
    chunks_inserted.
    """
    files = _collect_files(path)

    pending = []
    skipped_count = 0
    for file_path in files:
        text = Path(file_path).read_text(encoding="utf-8", errors="replace")
        content_hash = store.compute_content_hash(text)
        existing_hash = store.get_document_hash(conn, file_path)
        if existing_hash == content_hash:
            skipped_count += 1
            continue

        raw_chunks = chunking.split_into_chunks(text)
        chunk_records = []
        for index, chunk_text in enumerate(raw_chunks):
            section = classifier.classify_section(chunk_text)
            reuse_score, reuse_tier = scorer.score_reusability(chunk_text)
            chunk_records.append(
                {
                    "index": index,
                    "section": section,
                    "text": chunk_text,
                    "score": reuse_score,
                    "tier": reuse_tier,
                }
            )
        pending.append({"path": file_path, "hash": content_hash, "chunks": chunk_records})

    if not pending:
        return {
            "documents_processed": 0,
            "documents_skipped": skipped_count,
            "chunks_inserted": 0,
        }

    pending_paths = {doc["path"] for doc in pending}
    existing_texts = [
        c["text"] for c in store.get_all_chunks(conn) if c["document_path"] not in pending_paths
    ]
    new_texts = [chunk["text"] for doc in pending for chunk in doc["chunks"]]
    doc_freq, total_chunks = tagging.build_corpus_doc_freq(existing_texts + new_texts)

    chunks_inserted = 0
    for doc in pending:
        document_id = store.upsert_document(conn, doc["path"], doc["hash"])
        store.delete_chunks_for_document(conn, document_id)

        for chunk in doc["chunks"]:
            tags = tagging.extract_tags(chunk["text"], doc_freq, total_chunks)
            ai_summary = None
            if use_ai and api_key:
                enrichment = ai_enrich.enrich_chunk(chunk["text"], api_key)
                if enrichment:
                    ai_summary = enrichment["summary"]
                    if enrichment["tags"]:
                        tags = enrichment["tags"]

            store.insert_chunk(
                conn,
                document_id,
                chunk["index"],
                chunk["section"],
                chunk["text"],
                chunk["score"],
                chunk["tier"],
                tags,
                ai_summary,
            )
            chunks_inserted += 1

    return {
        "documents_processed": len(pending),
        "documents_skipped": skipped_count,
        "chunks_inserted": chunks_inserted,
    }
