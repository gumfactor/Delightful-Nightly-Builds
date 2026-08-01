"""Text, JSON, and HTML report rendering for ItemScope."""

from __future__ import annotations

import html
import json

from itemscope.stats import TestStats


FLAG_LABELS = {
    "too_easy": "Too easy",
    "too_hard": "Too hard",
    "poor_discrimination": "Poor discrimination",
    "negative_discrimination": "Negative discrimination",
    "non_functioning_distractor": "Non-functioning distractor",
    "reversed_distractor_pull": "Reversed distractor pull",
}


def to_dict(stats: TestStats) -> dict:
    return {
        "n_students": stats.n_students,
        "n_items": stats.n_items,
        "mean_score": round(stats.mean_score, 3),
        "sd_score": round(stats.sd_score, 3),
        "sem": round(stats.sem, 3) if stats.sem is not None else None,
        "reliability_kr20": round(stats.kr20, 3) if stats.kr20 is not None else None,
        "reliability_note": stats.kr20_note,
        "items": [
            {
                "item_id": item.item_id,
                "p_value": round(item.p_value, 3),
                "discrimination": round(item.discrimination, 3)
                if item.discrimination is not None
                else None,
                "discrimination_note": item.discrimination_note,
                "flags": item.flags,
                "distractor_analysis": item.distractor_analysis,
            }
            for item in stats.items
        ],
    }


def render_json(stats: TestStats) -> str:
    return json.dumps(to_dict(stats), indent=2)


def render_text(stats: TestStats) -> str:
    lines = []
    lines.append("ItemScope — Item Analysis Report")
    lines.append("=" * 40)
    lines.append(f"Students: {stats.n_students}   Items: {stats.n_items}")
    lines.append(f"Mean score: {stats.mean_score:.2f}   SD: {stats.sd_score:.2f}")
    if stats.kr20 is not None:
        lines.append(f"Reliability (KR-20): {stats.kr20:.3f}")
    else:
        lines.append(f"Reliability (KR-20): n/a — {stats.kr20_note}")
    lines.append("")
    lines.append("Per-item summary:")
    for item in stats.items:
        disc = (
            f"{item.discrimination:.3f}"
            if item.discrimination is not None
            else item.discrimination_note
        )
        flag_str = ", ".join(FLAG_LABELS.get(f, f) for f in item.flags) or "none"
        lines.append(
            f"  {item.item_id:<12} p={item.p_value:.3f}  r={disc:<28}  flags: {flag_str}"
        )
    flagged = [item for item in stats.items if item.flags]
    lines.append("")
    if flagged:
        lines.append(f"Flagged items ({len(flagged)}):")
        for item in flagged:
            flag_str = ", ".join(FLAG_LABELS.get(f, f) for f in item.flags)
            lines.append(f"  - {item.item_id}: {flag_str}")
    else:
        lines.append("No items flagged.")
    return "\n".join(lines)


_HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>ItemScope Report</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  :root {
    --bg: #0f1115; --panel: #171a21; --border: #2a2f3a; --text: #e6e8ec;
    --muted: #9aa3b2; --accent: #6ea8fe; --bad: #f27878; --warn: #f2c078; --good: #7ed6a5;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; padding: 24px; background: var(--bg); color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  }
  h1 { font-size: 1.4rem; margin: 0 0 4px; }
  .subtitle { color: var(--muted); margin-bottom: 20px; }
  .stat-row { display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 20px; }
  .stat-tile {
    background: var(--panel); border: 1px solid var(--border); border-radius: 10px;
    padding: 12px 16px; min-width: 140px;
  }
  .stat-tile .label { color: var(--muted); font-size: 0.75rem; text-transform: uppercase; }
  .stat-tile .value { font-size: 1.4rem; font-weight: 600; }
  .panel {
    background: var(--panel); border: 1px solid var(--border); border-radius: 10px;
    padding: 16px; margin-bottom: 20px; overflow-x: auto;
  }
  .panel h2 { margin-top: 0; font-size: 1.1rem; }
  table { border-collapse: collapse; width: 100%; font-size: 0.9rem; }
  th, td { padding: 6px 10px; text-align: left; border-bottom: 1px solid var(--border); }
  th { cursor: pointer; color: var(--muted); user-select: none; }
  th.sorted::after { content: " \\25BE"; }
  .flag { display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 0.75rem; margin: 1px; }
  .flag.bad { background: rgba(242,120,120,0.15); color: var(--bad); }
  .flag.warn { background: rgba(242,192,120,0.15); color: var(--warn); }
  .flag.none { color: var(--good); }
  #search { width: 100%; max-width: 320px; padding: 8px 10px; margin-bottom: 12px;
    background: var(--bg); border: 1px solid var(--border); border-radius: 8px; color: var(--text); }
  canvas { background: #0b0d12; border-radius: 8px; max-width: 100%; }
  .quadrant-labels { display: flex; justify-content: space-between; color: var(--muted); font-size: 0.75rem; margin-top: 6px; }
</style>
</head>
<body>
  <h1>ItemScope Report</h1>
  <div class="subtitle">__SUBTITLE__</div>

  <div class="stat-row">
    __STAT_TILES__
  </div>

  <div class="panel">
    <h2>Difficulty vs. Discrimination</h2>
    <canvas id="quadrant" width="640" height="420"></canvas>
    <div class="quadrant-labels">
      <span>&larr; Harder</span><span>Easier &rarr;</span>
    </div>
  </div>

  <div class="panel">
    <h2>Flagged Items (__FLAGGED_COUNT__)</h2>
    <div id="flagged-list">__FLAGGED_LIST__</div>
  </div>

  <div class="panel">
    <h2>All Items</h2>
    <input id="search" type="text" placeholder="Search item ID...">
    <table id="item-table">
      <thead>
        <tr>
          <th data-key="item_id">Item</th>
          <th data-key="p_value">p-value</th>
          <th data-key="discrimination">Discrimination</th>
          <th data-key="flags">Flags</th>
        </tr>
      </thead>
      <tbody></tbody>
    </table>
  </div>

  <script id="report-data" type="application/json">__REPORT_JSON__</script>
  <script>
    const data = JSON.parse(document.getElementById('report-data').textContent);
    const flagLabels = __FLAG_LABELS_JSON__;
    const badFlags = new Set(['too_easy', 'too_hard', 'negative_discrimination', 'non_functioning_distractor']);

    function flagBadge(flag) {
      const cls = badFlags.has(flag) ? 'bad' : 'warn';
      const span = document.createElement('span');
      span.className = 'flag ' + cls;
      span.textContent = flagLabels[flag] || flag;
      return span;
    }

    function renderRows(items) {
      const tbody = document.querySelector('#item-table tbody');
      tbody.textContent = '';
      for (const item of items) {
        const tr = document.createElement('tr');
        const tdId = document.createElement('td');
        tdId.textContent = item.item_id;
        const tdP = document.createElement('td');
        tdP.textContent = item.p_value.toFixed(3);
        const tdR = document.createElement('td');
        tdR.textContent = item.discrimination !== null ? item.discrimination.toFixed(3) : (item.discrimination_note || 'n/a');
        const tdFlags = document.createElement('td');
        if (item.flags.length === 0) {
          const span = document.createElement('span');
          span.className = 'flag none';
          span.textContent = 'none';
          tdFlags.appendChild(span);
        } else {
          for (const f of item.flags) tdFlags.appendChild(flagBadge(f));
        }
        tr.append(tdId, tdP, tdR, tdFlags);
        tbody.appendChild(tr);
      }
    }

    function renderFlagged() {
      const container = document.getElementById('flagged-list');
      container.textContent = '';
      const flagged = data.items.filter(i => i.flags.length > 0);
      if (flagged.length === 0) {
        const p = document.createElement('p');
        p.textContent = 'No items flagged — nice exam.';
        container.appendChild(p);
        return;
      }
      for (const item of flagged) {
        const row = document.createElement('div');
        row.style.marginBottom = '8px';
        const strong = document.createElement('strong');
        strong.textContent = item.item_id + ': ';
        row.appendChild(strong);
        for (const f of item.flags) row.appendChild(flagBadge(f));
        container.appendChild(row);
      }
    }

    function drawQuadrant() {
      const canvas = document.getElementById('quadrant');
      const ctx = canvas.getContext('2d');
      const w = canvas.width, h = canvas.height;
      const pad = 40;
      ctx.clearRect(0, 0, w, h);
      ctx.strokeStyle = '#2a2f3a';
      ctx.lineWidth = 1;
      ctx.strokeRect(pad, pad, w - 2 * pad, h - 2 * pad);
      ctx.beginPath();
      ctx.moveTo(pad, h - pad - (h - 2 * pad) * 0.15);
      ctx.lineTo(w - pad, h - pad - (h - 2 * pad) * 0.15);
      ctx.moveTo(pad + (w - 2 * pad) * 0.2, pad);
      ctx.lineTo(pad + (w - 2 * pad) * 0.2, h - pad);
      ctx.moveTo(pad + (w - 2 * pad) * 0.95, pad);
      ctx.lineTo(pad + (w - 2 * pad) * 0.95, h - pad);
      ctx.strokeStyle = '#3a4152';
      ctx.setLineDash([4, 4]);
      ctx.stroke();
      ctx.setLineDash([]);

      for (const item of data.items) {
        const x = pad + item.p_value * (w - 2 * pad);
        const r = item.discrimination === null ? 0 : Math.max(-1, Math.min(1, item.discrimination));
        const y = h - pad - ((r + 1) / 2) * (h - 2 * pad);
        const flagged = item.flags.length > 0;
        ctx.beginPath();
        ctx.arc(x, y, 5, 0, Math.PI * 2);
        ctx.fillStyle = flagged ? '#f27878' : '#7ed6a5';
        ctx.globalAlpha = 0.85;
        ctx.fill();
        ctx.globalAlpha = 1;
      }
      ctx.fillStyle = '#9aa3b2';
      ctx.font = '11px sans-serif';
      ctx.fillText('p-value (difficulty) →', pad, h - 12);
      ctx.save();
      ctx.translate(14, h - pad);
      ctx.rotate(-Math.PI / 2);
      ctx.fillText('discrimination (r) →', 0, 0);
      ctx.restore();
    }

    let sortKey = 'p_value';
    let sortAsc = true;
    function applySort(items) {
      const sorted = [...items].sort((a, b) => {
        let av = a[sortKey], bv = b[sortKey];
        if (sortKey === 'flags') { av = a.flags.length; bv = b.flags.length; }
        if (sortKey === 'discrimination') { av = a.discrimination ?? -2; bv = b.discrimination ?? -2; }
        if (av < bv) return sortAsc ? -1 : 1;
        if (av > bv) return sortAsc ? 1 : -1;
        return 0;
      });
      return sorted;
    }

    document.querySelectorAll('#item-table th').forEach(th => {
      th.addEventListener('click', () => {
        const key = th.dataset.key;
        if (sortKey === key) sortAsc = !sortAsc; else { sortKey = key; sortAsc = true; }
        document.querySelectorAll('#item-table th').forEach(t => t.classList.remove('sorted'));
        th.classList.add('sorted');
        renderRows(applySort(filterItems()));
      });
    });

    function filterItems() {
      const q = document.getElementById('search').value.trim().toLowerCase();
      if (!q) return data.items;
      return data.items.filter(i => i.item_id.toLowerCase().includes(q));
    }

    document.getElementById('search').addEventListener('input', () => {
      renderRows(applySort(filterItems()));
    });

    renderRows(applySort(data.items));
    renderFlagged();
    drawQuadrant();
  </script>
</body>
</html>
"""


def render_html(stats: TestStats) -> str:
    data = to_dict(stats)
    subtitle = html.escape(
        f"{data['n_students']} students · {data['n_items']} items · "
        f"reliability (KR-20): "
        + (f"{data['reliability_kr20']:.3f}" if data['reliability_kr20'] is not None else "n/a")
    )
    tiles = [
        ("Students", data["n_students"]),
        ("Items", data["n_items"]),
        ("Mean score", data["mean_score"]),
        ("SD", data["sd_score"]),
        (
            "KR-20",
            f"{data['reliability_kr20']:.3f}" if data["reliability_kr20"] is not None else "n/a",
        ),
    ]
    stat_tiles_html = "".join(
        f'<div class="stat-tile"><div class="label">{html.escape(str(label))}</div>'
        f'<div class="value">{html.escape(str(value))}</div></div>'
        for label, value in tiles
    )
    flagged = [item for item in data["items"] if item["flags"]]
    flagged_count = len(flagged)
    flagged_list_html = ""
    if not flagged:
        flagged_list_html = "<p>No items flagged — nice exam.</p>"

    out = _HTML_TEMPLATE
    out = out.replace("__SUBTITLE__", subtitle)
    out = out.replace("__STAT_TILES__", stat_tiles_html)
    out = out.replace("__FLAGGED_COUNT__", str(flagged_count))
    out = out.replace("__FLAGGED_LIST__", flagged_list_html)
    out = out.replace("__REPORT_JSON__", _safe_embed(json.dumps(data)))
    out = out.replace("__FLAG_LABELS_JSON__", _safe_embed(json.dumps(FLAG_LABELS)))
    return out


def _safe_embed(json_text: str) -> str:
    """Prevent a '</script>' substring inside embedded JSON (e.g. from a
    malicious item ID) from closing the surrounding <script> tag early."""
    return json_text.replace("</", "<\\/")
