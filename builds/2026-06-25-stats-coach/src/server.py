"""Flask server for Stats Coach.

Routes:
  GET  /            → serve the single-page UI
  POST /api/advise  → accept design params, return test recommendation + AI explanation
"""

from __future__ import annotations
import os
from pathlib import Path

from flask import Flask, jsonify, request, render_template

from advisor import recommend_test
from ai_explainer import generate_explanation
from cache import AdviceCache

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "stats_coach.db"

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static"),
)

_cache: AdviceCache | None = None


def get_cache() -> AdviceCache:
    global _cache
    if _cache is None:
        _cache = AdviceCache(DB_PATH)
    return _cache


VALID_OUTCOME_TYPES = {"continuous", "categorical", "ordinal"}
VALID_NORMALITY = {"assumed", "violated", "unknown"}


def _validate_params(data: dict) -> tuple[dict, str | None]:
    """Parse and validate request params. Returns (params, error_message)."""
    outcome_type = data.get("outcome_type", "").strip().lower()
    if outcome_type not in VALID_OUTCOME_TYPES:
        return {}, f"outcome_type must be one of: {', '.join(sorted(VALID_OUTCOME_TYPES))}"

    try:
        num_groups = int(data.get("num_groups", 0))
    except (ValueError, TypeError):
        return {}, "num_groups must be an integer"
    if num_groups < 1:
        return {}, "num_groups must be >= 1"

    paired_raw = data.get("paired", "false")
    if isinstance(paired_raw, bool):
        paired = paired_raw
    else:
        paired = str(paired_raw).lower() in {"true", "1", "yes"}

    relationship_raw = data.get("relationship", "false")
    if isinstance(relationship_raw, bool):
        relationship = relationship_raw
    else:
        relationship = str(relationship_raw).lower() in {"true", "1", "yes"}

    normality = data.get("normality", "unknown").strip().lower()
    if normality not in VALID_NORMALITY:
        return {}, f"normality must be one of: {', '.join(sorted(VALID_NORMALITY))}"

    study_context = str(data.get("study_context", "")).strip()[:500]

    return {
        "outcome_type": outcome_type,
        "num_groups": num_groups,
        "paired": paired,
        "relationship": relationship,
        "normality": normality,
        "study_context": study_context,
    }, None


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/advise", methods=["POST"])
def advise():
    data = request.get_json(silent=True) or {}
    params, error = _validate_params(data)
    if error:
        return jsonify({"error": error}), 400

    cache = get_cache()

    # Cache key excludes free-text context so the same design reuses the explanation
    cache_params = {k: v for k, v in params.items() if k != "study_context"}
    cached = cache.get(cache_params)
    if cached:
        return jsonify({
            "test_name": cached["test_name"],
            "ai_explanation": cached["ai_explanation"],
            "r_code": cached["r_code"],
            "python_code": cached["python_code"],
            "interpretation": cached["interpretation"],
            "cached": True,
        })

    try:
        rec = recommend_test(**params)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    ai_explanation = generate_explanation(
        test_name=rec.test_name,
        outcome_type=params["outcome_type"],
        num_groups=params["num_groups"],
        paired=params["paired"],
        normality=params["normality"],
        relationship=params["relationship"],
        study_context=params["study_context"],
        assumptions=rec.assumptions,
    )

    result = {
        "test_name": rec.test_name,
        "family": rec.family,
        "assumptions": rec.assumptions,
        "ai_explanation": ai_explanation,
        "r_code": rec.r_snippet,
        "python_code": rec.python_snippet,
        "interpretation": rec.interpretation_notes,
    }

    cache.put(cache_params, {
        "test_name": rec.test_name,
        "ai_explanation": ai_explanation,
        "r_code": rec.r_snippet,
        "python_code": rec.python_snippet,
        "interpretation": rec.interpretation_notes,
    })

    return jsonify({**result, "cached": False})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
