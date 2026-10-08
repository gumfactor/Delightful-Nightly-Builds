"""Writers: deduped.csv, clusters.csv, merge_report.json, review.html (self-contained, escapes all data)."""
from __future__ import annotations

import csv
import html
import json
from pathlib import Path

from .cluster import Analysis, Cluster
from .match import PairResult
from .schema import CANONICAL, Record

CSV_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def csv_safe(value: str) -> str:
    """Neutralize spreadsheet formula injection (a leading =,+,-,@ in untrusted scraped text)."""
    return "'" + value if value.startswith(CSV_FORMULA_PREFIXES) and not _plain_number_or_phone(value) else value


def _plain_number_or_phone(value: str) -> bool:
    return value[:1] in "+-" and value[1:].replace(" ", "").replace("-", "").replace("(", "").replace(")", "").isdigit()


def deduped_rows(analysis: Analysis) -> list[dict[str, str]]:
    """One row per surviving record. Merged clusters collapse; needs_review clusters stay unmerged."""
    absorbed: dict[str, Cluster] = {}
    for cluster in analysis.clusters:
        if cluster.status == "merged":
            for member in cluster.members:
                absorbed[member] = cluster
    rows: list[dict[str, str]] = []
    emitted: set[str] = set()
    by_id = analysis.by_id
    for rec in analysis.records:
        cluster = absorbed.get(rec.id)
        if cluster is None:
            rows.append(_row(rec.id, rec.fields, rec.extra, "", ""))
        elif cluster.id not in emitted:
            emitted.add(cluster.id)
            rep = by_id[cluster.representative]
            rows.append(_row(cluster.representative, {**rep.fields, **cluster.merged}, rep.extra,
                             ";".join(cluster.members), cluster.id))
    return rows


def _row(rid: str, fields: dict[str, str], extra: dict[str, str], merged_from: str, cluster_id: str) -> dict[str, str]:
    row = {"id": rid}
    row.update({name: fields.get(name, "") for name in CANONICAL if name in fields})
    row.update(extra)
    row["merged_from"] = merged_from
    row["cluster_id"] = cluster_id
    return row


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    columns: list[str] = []
    for row in rows:
        for key in row:
            if key not in columns:
                columns.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: csv_safe(str(v)) for k, v in row.items()})


def cluster_rows(analysis: Analysis) -> list[dict[str, str]]:
    rows = []
    for cluster in analysis.clusters:
        for member in cluster.members:
            rows.append({"row_id": member, "cluster_id": cluster.id, "status": cluster.status,
                         "name": analysis.by_id[member].fields.get("name", ""),
                         "flags": " | ".join(cluster.flags)})
    return rows


def report_dict(analysis: Analysis, ai: dict | None = None) -> dict:
    def pair(p: PairResult) -> dict:
        key = f"{p.a}|{p.b}"
        entry = {"a": p.a, "b": p.b, "score": p.score, "label": p.label, "reasons": [list(r) for r in p.reasons]}
        if ai and (p.a, p.b) in ai:
            entry["ai"] = ai[(p.a, p.b)]
        entry["key"] = key
        return entry

    return {
        "summary": {
            "input_rows": len(analysis.records),
            "output_rows": len(deduped_rows(analysis)),
            "merged_clusters": sum(1 for c in analysis.clusters if c.status == "merged"),
            "needs_review_clusters": sum(1 for c in analysis.clusters if c.status == "needs_review"),
            "review_pairs": len(analysis.review_pairs),
            "branch_pairs": len(analysis.branch_pairs),
        },
        "clusters": [{"id": c.id, "status": c.status, "members": c.members, "flags": c.flags,
                      "merged": c.merged, "provenance": c.provenance, "representative": c.representative}
                     for c in analysis.clusters],
        "review_pairs": [pair(p) for p in analysis.review_pairs],
        "branch_pairs": [pair(p) for p in analysis.branch_pairs],
        "decisions_applied": analysis.decisions.to_json(),
    }


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False), encoding="utf-8")


# --------------------------------------------------------------------------- HTML
def _e(value: object) -> str:
    return html.escape(str(value), quote=True)


def _field_table(a: Record, b: Record) -> str:
    rows = []
    for name in CANONICAL:
        left, right = a.fields.get(name, ""), b.fields.get(name, "")
        if not left and not right:
            continue
        cls = "same" if left.strip().lower() == right.strip().lower() else ("miss" if not left or not right else "diff")
        rows.append(f'<tr class="{cls}"><th>{_e(name)}</th><td>{_e(left) or "—"}</td><td>{_e(right) or "—"}</td></tr>')
    return ('<table><thead><tr><th></th><th>' + _e(a.id) + '</th><th>' + _e(b.id) + '</th></tr></thead><tbody>'
            + "".join(rows) + "</tbody></table>")


def _pair_card(pair: PairResult, analysis: Analysis, ai: dict | None) -> str:
    a, b = analysis.by_id[pair.a], analysis.by_id[pair.b]
    reasons = "".join(f"<li>{_e(n)} <b>{w:+.2f}</b></li>" for n, w in pair.reasons)
    ai_html = ""
    if ai and (pair.a, pair.b) in ai:
        verdict = ai[(pair.a, pair.b)]
        ai_html = f'<p class="ai">AI suggestion (advisory): <b>{_e(verdict["verdict"])}</b> — {_e(verdict["reason"])}</p>'
    return (
        f'<article class="card" data-testid="pair-card" data-a="{_e(pair.a)}" data-b="{_e(pair.b)}">'
        f'<header><span class="score">{pair.score:.2f}</span><span class="badge {_e(pair.label)}">{_e(pair.label)}</span>'
        f'<span class="ids">{_e(pair.a)} ↔ {_e(pair.b)}</span></header>'
        f'{_field_table(a, b)}<ul class="reasons">{reasons}</ul>{ai_html}'
        f'<div class="actions"><button data-act="same" data-testid="btn-same">Same business</button>'
        f'<button data-act="different" data-testid="btn-different">Different</button>'
        f'<button data-act="clear" class="ghost">Undecided</button></div></article>')


def _cluster_card(cluster: Cluster, analysis: Analysis) -> str:
    names = "".join(f"<li><b>{_e(m)}</b> {_e(analysis.by_id[m].fields.get('name', ''))}</li>" for m in cluster.members)
    flags = "".join(f"<li class='flag'>{_e(f)}</li>" for f in cluster.flags)
    merged = ""
    if cluster.status == "merged":
        merged = "<table><tbody>" + "".join(
            f"<tr><th>{_e(k)}</th><td>{_e(v)}</td><td class='src'>from {_e(cluster.provenance.get(k, ''))}</td></tr>"
            for k, v in cluster.merged.items()) + "</tbody></table>"
    return (f'<article class="card" data-testid="cluster-card"><header><span class="badge {_e(cluster.status)}">'
            f'{_e(cluster.status.replace("_", " "))}</span><span class="ids">{_e(cluster.id)}</span></header>'
            f'<ul>{names}</ul>{"<ul>" + flags + "</ul>" if flags else ""}{merged}</article>')


STYLE = """
:root{--bg:#f6f7f9;--fg:#15181d;--card:#fff;--line:#d9dde3;--muted:#5b6573;--accent:#0b5fff;--ok:#12794a;--warn:#9a5b00;--bad:#b3261e;--diff:#fff3cd;--miss:#eef1f5}
@media (prefers-color-scheme:dark){:root{--bg:#10141a;--fg:#e8ebf0;--card:#181d25;--line:#2c3440;--muted:#9aa5b4;--accent:#6ea0ff;--ok:#4cc38a;--warn:#f0b04a;--bad:#ff8a80;--diff:#3a3216;--miss:#202733}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.45 system-ui,sans-serif}
main{max-width:980px;margin:0 auto;padding:16px}h1{font-size:1.4rem;margin:.2em 0}h2{margin-top:1.6em;font-size:1.1rem}
.stats{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0}.stat{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:8px 12px}
.stat b{display:block;font-size:1.3rem}.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px;margin:12px 0;overflow-x:auto}
.card[data-decision=same]{border-color:var(--ok)}.card[data-decision=different]{border-color:var(--bad)}
.card header{display:flex;gap:8px;align-items:center;flex-wrap:wrap}.score{font-weight:700}.ids{color:var(--muted)}
.badge{border-radius:99px;padding:1px 10px;font-size:.8rem;border:1px solid var(--line)}.badge.duplicate,.badge.merged{color:var(--ok)}.badge.review,.badge.needs_review{color:var(--warn)}.badge.branch{color:var(--accent)}
table{border-collapse:collapse;width:100%;margin:8px 0}th,td{border-top:1px solid var(--line);padding:4px 8px;text-align:left;vertical-align:top;word-break:break-word}
th{color:var(--muted);font-weight:600;white-space:nowrap}tr.diff td{background:var(--diff)}tr.miss td{background:var(--miss)}td.src{color:var(--muted)}
.reasons{margin:4px 0;padding-left:18px;color:var(--muted)}.flag{color:var(--bad)}.ai{background:var(--miss);padding:6px 8px;border-radius:6px}
.actions{display:flex;gap:8px;flex-wrap:wrap}button{font:inherit;border:1px solid var(--line);background:var(--card);color:var(--fg);border-radius:8px;padding:8px 14px;cursor:pointer;min-height:40px}
button.active{background:var(--accent);color:#fff;border-color:var(--accent)}button.ghost{color:var(--muted)}
.bar{position:sticky;bottom:0;background:var(--card);border-top:1px solid var(--line);padding:10px 16px;display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.bar span{color:var(--muted)}
"""

SCRIPT = """
(function(){
  var decisions={};
  function key(card){return card.getAttribute('data-a')+'|'+card.getAttribute('data-b');}
  function update(){
    var same=[],different=[];
    Object.keys(decisions).forEach(function(k){var p=k.split('|');(decisions[k]==='same'?same:different).push(p);});
    document.getElementById('count').textContent=same.length+' same, '+different.length+' different';
    return {same:same,different:different};
  }
  document.querySelectorAll('[data-testid=pair-card]').forEach(function(card){
    card.querySelectorAll('button').forEach(function(btn){
      btn.addEventListener('click',function(){
        var act=btn.getAttribute('data-act');
        if(act==='clear'){delete decisions[key(card)];card.removeAttribute('data-decision');}
        else{decisions[key(card)]=act;card.setAttribute('data-decision',act);}
        card.querySelectorAll('button').forEach(function(b){b.classList.toggle('active',b.getAttribute('data-act')===card.getAttribute('data-decision'));});
        update();
      });
    });
  });
  document.getElementById('download').addEventListener('click',function(){
    var blob=new Blob([JSON.stringify(update(),null,2)],{type:'application/json'});
    var a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='decisions.json';a.click();
  });
  update();
})();
"""


def render_html(analysis: Analysis, ai: dict | None = None, title: str = "Lookalike review") -> str:
    summary = report_dict(analysis, ai)["summary"]
    stats = "".join(f'<div class="stat"><b>{_e(v)}</b>{_e(k.replace("_", " "))}</div>' for k, v in summary.items())
    review = "".join(_pair_card(p, analysis, ai) for p in analysis.review_pairs) or "<p>No ambiguous pairs. Nothing needs a decision.</p>"
    clusters = "".join(_cluster_card(c, analysis) for c in analysis.clusters) or "<p>No duplicate clusters found.</p>"
    branches = "".join(
        f"<li>{_e(p.a)} ↔ {_e(p.b)}: {_e(analysis.by_id[p.a].fields.get('name', ''))} — "
        f"{_e(analysis.by_id[p.a].fields.get('city', ''))} / {_e(analysis.by_id[p.b].fields.get('city', ''))}</li>"
        for p in analysis.branch_pairs)
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>{_e(title)}</title><style>{STYLE}</style></head><body><main>'
        f'<h1>{_e(title)}</h1><div class="stats" data-testid="stats">{stats}</div>'
        f'<h2>Needs your decision ({len(analysis.review_pairs)})</h2><section data-testid="review">{review}</section>'
        f'<h2>Duplicate clusters</h2><section data-testid="clusters">{clusters}</section>'
        f'<h2>Same brand, different location (kept separate)</h2><ul data-testid="branches">{branches or "<li>None</li>"}</ul>'
        '</main><div class="bar"><button id="download" data-testid="download">Download decisions.json</button>'
        '<span id="count" data-testid="count"></span><span>Re-run with <code>--decisions decisions.json</code></span></div>'
        f'<script>{SCRIPT}</script></body></html>')
