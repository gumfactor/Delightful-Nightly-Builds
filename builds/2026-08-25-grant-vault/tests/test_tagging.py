from src.tagging import build_corpus_doc_freq, extract_tags


def test_stopwords_and_short_tokens_filtered_out():
    chunk = "The and for are but not you all can her was one our out day."
    doc_freq, total = build_corpus_doc_freq([chunk])
    tags = extract_tags(chunk, doc_freq, total)
    assert tags == []


def test_rare_term_outranks_common_term():
    # "psychopathy" appears twice in the target chunk and in only 1 of 5
    # chunks corpus-wide, so its tf-idf-style weight clearly dominates
    # the single-occurrence, equally-rare "overlap"/"substantially" and
    # the higher-document-frequency "research".
    corpus = [
        "empathy research continues across every laboratory site",
        "empathy training programs expand across universities",
        "empathy measurement tools improve steadily",
        "empathy replication studies confirm earlier findings",
        "psychopathy and psychopathy research overlap substantially",
    ]
    doc_freq, total = build_corpus_doc_freq(corpus)
    tags = extract_tags(corpus[4], doc_freq, total, top_n=1)
    assert tags == ["psychopathy"]


def test_deterministic_output_for_same_input():
    chunk = "stress reactivity connectivity forensic neuroscience empathy accuracy"
    doc_freq, total = build_corpus_doc_freq([chunk])
    first = extract_tags(chunk, doc_freq, total)
    second = extract_tags(chunk, doc_freq, total)
    assert first == second


def test_empty_chunk_returns_empty_tags():
    doc_freq, total = build_corpus_doc_freq(["some corpus text here"])
    assert extract_tags("", doc_freq, total) == []


def test_top_n_limits_number_of_tags():
    chunk = "alpha bravo charlie delta echo foxtrot golf hotel"
    doc_freq, total = build_corpus_doc_freq([chunk])
    tags = extract_tags(chunk, doc_freq, total, top_n=3)
    assert len(tags) == 3


def test_ties_broken_alphabetically_for_determinism():
    chunk = "zeta alpha"
    doc_freq, total = build_corpus_doc_freq([chunk])
    tags = extract_tags(chunk, doc_freq, total, top_n=2)
    assert tags == ["alpha", "zeta"]


def test_build_corpus_doc_freq_counts_distinct_chunks_not_occurrences():
    corpus = ["repeated repeated repeated term", "repeated term appears once"]
    doc_freq, total = build_corpus_doc_freq(corpus)
    assert total == 2
    assert doc_freq["repeated"] == 2
