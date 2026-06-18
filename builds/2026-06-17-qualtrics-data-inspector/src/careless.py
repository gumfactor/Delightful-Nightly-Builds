"""Compute a per-respondent careless responding composite index."""


def compute_careless_index(quality, attention_results: dict = None) -> dict:
    """
    Compute a composite careless responding score for every flagged respondent.

    Five components, each normalised to [0.0, 1.0]:

    Component            Weight  Meaning
    ─────────────────    ──────  ───────────────────────────────────────────
    fast_response          1     Below timing threshold (binary)
    straight_liner         1     Same value across all scale items (binary)
    high_missing           1     > threshold of items blank (binary)
    outlier_breadth        1     n_outlier_columns / 3, capped at 1.0
    attention_fail_rate    1     n_failed_checks / n_total_checks (0 if none)

    Final score = mean of all applicable components.
    A respondent that fires every signal scores 1.0; a clean respondent scores 0.0.
    Respondents with no flags are included only if they appear in attention results.

    Returns:
    {
        respondent_id: {
            'score': float,         # 0.0–1.0 composite
            'components': dict,     # per-component scores
            'flags': list[str],     # human-readable flag labels
        }
    }
    """
    fast_set = set(quality.fast_response_ids)
    straight_set = set(quality.straight_liner_ids)
    high_missing_set = set(quality.high_missing_respondents)

    # Build the union of all flagged respondent IDs
    all_ids: set = set()
    all_ids.update(fast_set, straight_set, high_missing_set)
    all_ids.update(quality.respondent_outlier_counts.keys())

    # Attention failures per respondent: {id: n_failed}
    attn_fails: dict = {}
    n_checks = 0
    if attention_results:
        n_checks = len(attention_results)
        for col, res in attention_results.items():
            for rid in res.get("failed_ids") or []:
                attn_fails[rid] = attn_fails.get(rid, 0) + 1
                all_ids.add(rid)

    results: dict = {}
    for rid in all_ids:
        components: dict = {}
        flags: list = []

        # Fast response
        fast = 1.0 if rid in fast_set else 0.0
        components["fast_response"] = fast
        if fast:
            flags.append("fast_response")

        # Straight-lining
        straight = 1.0 if rid in straight_set else 0.0
        components["straight_liner"] = straight
        if straight:
            flags.append("straight_liner")

        # High missing
        missing = 1.0 if rid in high_missing_set else 0.0
        components["high_missing"] = missing
        if missing:
            flags.append("high_missing")

        # Outlier breadth: how many columns is this person an outlier on?
        # Cap at 3 (anything beyond is equally suspicious)
        n_outlier_cols = quality.respondent_outlier_counts.get(rid, 0)
        outlier_score = min(1.0, n_outlier_cols / 3)
        components["outlier_breadth"] = round(outlier_score, 3)
        if n_outlier_cols > 0:
            flags.append(f"outlier_{n_outlier_cols}col{'s' if n_outlier_cols > 1 else ''}")

        # Attention check failures
        if n_checks > 0:
            n_failed = attn_fails.get(rid, 0)
            attn_score = n_failed / n_checks
            components["attention_fail_rate"] = round(attn_score, 3)
            if n_failed > 0:
                flags.append(f"attn_fail_{n_failed}of{n_checks}")

        score = sum(components.values()) / len(components) if components else 0.0

        results[rid] = {
            "score": round(score, 4),
            "components": components,
            "flags": flags,
        }

    return results


def careless_summary(careless_index: dict, threshold: float = 0.4) -> dict:
    """
    Summarise the careless responding index.

    Returns a dict with:
      - n_flagged: respondents scoring >= threshold
      - threshold: the threshold used
      - mean_score: mean score across all indexed respondents
      - score_distribution: {'0.0-0.2': n, '0.2-0.4': n, ...}
    """
    if not careless_index:
        return {
            "n_flagged": 0,
            "threshold": threshold,
            "mean_score": None,
            "score_distribution": {},
        }

    scores = [v["score"] for v in careless_index.values()]
    n_flagged = sum(1 for s in scores if s >= threshold)
    mean_score = round(sum(scores) / len(scores), 4)

    bins = ["0.0–0.2", "0.2–0.4", "0.4–0.6", "0.6–0.8", "0.8–1.0"]
    dist = {b: 0 for b in bins}
    for s in scores:
        if s < 0.2:
            dist["0.0–0.2"] += 1
        elif s < 0.4:
            dist["0.2–0.4"] += 1
        elif s < 0.6:
            dist["0.4–0.6"] += 1
        elif s < 0.8:
            dist["0.6–0.8"] += 1
        else:
            dist["0.8–1.0"] += 1

    return {
        "n_flagged": n_flagged,
        "threshold": threshold,
        "mean_score": mean_score,
        "score_distribution": dist,
    }
