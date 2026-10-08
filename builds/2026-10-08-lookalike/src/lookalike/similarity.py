"""From-scratch string similarity (no third-party dependencies)."""
from __future__ import annotations


def jaro(first: str, second: str) -> float:
    if first == second:
        return 1.0 if first else 0.0
    if not first or not second:
        return 0.0
    window = max(max(len(first), len(second)) // 2 - 1, 0)
    first_flags = [False] * len(first)
    second_flags = [False] * len(second)
    matches = 0
    for i, char in enumerate(first):
        for j in range(max(0, i - window), min(len(second), i + window + 1)):
            if not second_flags[j] and second[j] == char:
                first_flags[i] = second_flags[j] = True
                matches += 1
                break
    if matches == 0:
        return 0.0
    transpositions = 0
    pointer = 0
    for i, flagged in enumerate(first_flags):
        if flagged:
            while not second_flags[pointer]:
                pointer += 1
            if first[i] != second[pointer]:
                transpositions += 1
            pointer += 1
    half = transpositions / 2
    return (matches / len(first) + matches / len(second) + (matches - half) / matches) / 3


def jaro_winkler(first: str, second: str, prefix_scale: float = 0.1) -> float:
    base = jaro(first, second)
    prefix = 0
    for a, b in zip(first[:4], second[:4]):
        if a != b:
            break
        prefix += 1
    return base + prefix * prefix_scale * (1 - base)


def token_jaccard(first: list[str], second: list[str]) -> float:
    left, right = set(first), set(second)
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def name_similarity(tokens_a: list[str], tokens_b: list[str]) -> float:
    """Best of: whole-string Jaro-Winkler, sorted-token Jaro-Winkler (word-order robust), token Jaccard."""
    if not tokens_a or not tokens_b:
        return 0.0
    whole = jaro_winkler(" ".join(tokens_a), " ".join(tokens_b))
    reordered = jaro_winkler(" ".join(sorted(tokens_a)), " ".join(sorted(tokens_b)))
    return max(whole, reordered, token_jaccard(tokens_a, tokens_b))
