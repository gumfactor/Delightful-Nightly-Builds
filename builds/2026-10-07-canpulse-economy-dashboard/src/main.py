"""CanPulse CLI: fetch Canadian macro data and render dashboard.html."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from canpulse import analysis, briefing, render, sources, store  # noqa: E402

DEFAULT_OUT = Path(__file__).resolve().parents[1] / "dashboard.html"


def build(series: dict, errors: dict, meta: dict, use_ai: bool = True) -> str:
    full, stats = analysis.analyze_all(series)
    brief = briefing.ai_briefing(full, stats) if use_ai else {
        "source": "rules", "lines": briefing.rule_based(full, stats), "error": None}
    return render.render_html(render.build_payload(full, stats, errors, brief, meta))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--offline", action="store_true", help="render from cache (or sample data); no network")
    ap.add_argument("--no-ai", action="store_true", help="skip the Anthropic briefing")
    ap.add_argument("--verify", action="store_true", help="check StatCan vector titles and exit")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args(argv)

    if args.verify:
        results = sources.verify_vectors()
        for r in results:
            print(("OK  " if r["ok"] else "FAIL"), r["id"], r["vector"], r["title"])
        return 0 if results and all(r["ok"] for r in results) else 1

    if args.offline:
        doc = store.load_any()
        if doc is None:
            print("No cache or sample data found.", file=sys.stderr)
            return 1
        series, errors = doc["series"], doc.get("errors", {})
        meta = {"fetched_at": doc["fetched_at"], "sample": bool(doc.get("sample"))}
    else:
        series, errors = sources.fetch_all()
        series, errors = store.merge_with_cache(series, errors, store.load_cache())
        if not series:
            print("All sources failed; falling back to cache/sample data.", file=sys.stderr)
            doc = store.load_any()
            if doc is None:
                return 1
            series, meta = doc["series"], {"fetched_at": doc["fetched_at"], "sample": bool(doc.get("sample"))}
        else:
            doc = store.save_cache(series, errors)
            meta = {"fetched_at": doc["fetched_at"], "sample": False}
    for sid, msg in errors.items():
        print(f"warning: {sid}: {msg}", file=sys.stderr)

    args.out.write_text(build(series, errors, meta, use_ai=not args.no_ai), encoding="utf-8")
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
