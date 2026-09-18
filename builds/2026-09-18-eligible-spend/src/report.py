"""Terminal, HTML dashboard, and flagged-CSV report rendering for
Eligible Spend.
"""

from __future__ import annotations

import csv
import html
import io
import json
from datetime import date

from rules import (
    STATUS_INELIGIBLE,
    STATUS_NO_BLOCKING_RULE,
    STATUS_OUTSIDE_PERIOD,
    STATUS_REQUIRES_JUSTIFICATION,
    Verdict,
)

STATUS_LABELS = {
    STATUS_OUTSIDE_PERIOD: "Outside Grant Period",
    STATUS_INELIGIBLE: "Ineligible",
    STATUS_REQUIRES_JUSTIFICATION: "Requires Justification",
    STATUS_NO_BLOCKING_RULE: "No Blocking Rule Found",
}

# Status palette per the dataviz skill's fixed status roles: critical for
# blocking flags, warning for items needing a human decision, good for
# "nothing fired" (never claimed as a clean bill of eligibility).
STATUS_COLORS = {
    STATUS_OUTSIDE_PERIOD: "#d03b3b",  # critical
    STATUS_INELIGIBLE: "#d03b3b",  # critical
    STATUS_REQUIRES_JUSTIFICATION: "#fab219",  # warning
    STATUS_NO_BLOCKING_RULE: "#0ca30c",  # good
}

STATUS_ICONS = {
    STATUS_OUTSIDE_PERIOD: "✕",  # x
    STATUS_INELIGIBLE: "✕",
    STATUS_REQUIRES_JUSTIFICATION: "!",
    STATUS_NO_BLOCKING_RULE: "✓",  # check
}

FLAGGED_STATUSES = (STATUS_OUTSIDE_PERIOD, STATUS_INELIGIBLE, STATUS_REQUIRES_JUSTIFICATION)

DISCLAIMER = (
    "This tool checks a budget against the general Tri-Agency (NSERC/CIHR/SSHRC) "
    "Guide on Financial Administration's public principles and specifically-named "
    "ineligible items. It is a decision-support heuristic, not legal or financial "
    "advice, and does not model institution-negotiated overhead/indirect-cost "
    "rates. A 'no blocking rule found' verdict is not a guarantee of eligibility. "
    "Always confirm with your institution's research grants or financial office "
    "before submitting a budget or filing an expense claim."
)


def render_terminal(verdicts: list[Verdict], grant_start: date, grant_end: date) -> str:
    lines: list[str] = []
    lines.append("=" * 60)
    lines.append("ELIGIBLE SPEND -- Tri-Agency Budget Compliance Check")
    lines.append("=" * 60)
    lines.append(f"Grant period: {grant_start.isoformat()} to {grant_end.isoformat()}")
    lines.append(f"Line items checked: {len(verdicts)}")
    lines.append("")

    totals = totals_by_status(verdicts)
    total_amount = sum(v.line.amount for v in verdicts)
    lines.append(f"Total budget:              ${total_amount:,.2f}")
    for status in (STATUS_OUTSIDE_PERIOD, STATUS_INELIGIBLE, STATUS_REQUIRES_JUSTIFICATION, STATUS_NO_BLOCKING_RULE):
        label = STATUS_LABELS[status]
        amt = totals.get(status, 0.0)
        count = sum(1 for v in verdicts if v.status == status)
        lines.append(f"{label + ':':<28}${amt:,.2f}  ({count} item{'s' if count != 1 else ''})")
    lines.append("")

    flagged = [v for v in verdicts if v.status in FLAGGED_STATUSES]
    if flagged:
        lines.append("-" * 60)
        lines.append(f"FLAGGED ITEMS ({len(flagged)})")
        lines.append("-" * 60)
        for v in flagged:
            lines.append(f"[{STATUS_LABELS[v.status]}] {v.line.item} -- ${v.line.amount:,.2f}")
            lines.append(f"    Reason: {v.reason}")
            lines.append(f"    {v.principle}")
            lines.append("")
    else:
        lines.append("No items flagged.")
        lines.append("")

    lines.append("-" * 60)
    lines.append("DISCLAIMER")
    lines.append("-" * 60)
    lines.append(DISCLAIMER)
    return "\n".join(lines)


def totals_by_status(verdicts: list[Verdict]) -> dict[str, float]:
    totals: dict[str, float] = {}
    for v in verdicts:
        totals[v.status] = totals.get(v.status, 0.0) + v.line.amount
    return totals


def write_flagged_csv(verdicts: list[Verdict], path: str) -> int:
    """Write only flagged (non-clean) line items to a CSV. Returns count written."""
    flagged = [v for v in verdicts if v.status in FLAGGED_STATUSES]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["item", "category", "amount", "date", "justification", "status", "reason", "principle"])
        for v in flagged:
            writer.writerow(
                [
                    v.line.item,
                    v.line.category,
                    f"{v.line.amount:.2f}",
                    v.line.item_date.isoformat(),
                    v.line.justification,
                    v.status,
                    v.reason,
                    v.principle,
                ]
            )
    return len(flagged)


def _verdict_to_dict(verdict: Verdict, ai_note: str | None) -> dict:
    return {
        "item": verdict.line.item,
        "category": verdict.line.category,
        "amount": verdict.line.amount,
        "date": verdict.line.item_date.isoformat(),
        "justification": verdict.line.justification,
        "status": verdict.status,
        "status_label": STATUS_LABELS[verdict.status],
        "reason": verdict.reason,
        "principle": verdict.principle,
        "ai_note": ai_note,
    }


def _bar_chart_html(totals: dict[str, float]) -> str:
    max_amount = max(totals.values(), default=0.0) or 1.0
    order = (STATUS_OUTSIDE_PERIOD, STATUS_INELIGIBLE, STATUS_REQUIRES_JUSTIFICATION, STATUS_NO_BLOCKING_RULE)
    rows = []
    for status in order:
        amt = totals.get(status, 0.0)
        pct = max(2.0, (amt / max_amount) * 100.0) if amt > 0 else 0.0
        color = STATUS_COLORS[status]
        icon = STATUS_ICONS[status]
        label = html.escape(STATUS_LABELS[status])
        rows.append(
            f'<div class="bar-row">'
            f'<div class="bar-label"><span class="bar-icon" style="color:{color}">{icon}</span>{label}</div>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{pct:.2f}%;background:{color}" '
            f'title="{label}: ${amt:,.2f}"></div></div>'
            f'<div class="bar-value">${amt:,.2f}</div>'
            f"</div>"
        )
    return "\n".join(rows)


def render_html(
    verdicts: list[Verdict],
    grant_start: date,
    grant_end: date,
    ai_notes: dict[int, str] | None = None,
) -> str:
    ai_notes = ai_notes or {}
    total_amount = sum(v.line.amount for v in verdicts)
    totals = totals_by_status(verdicts)
    flagged_count = sum(1 for v in verdicts if v.status in FLAGGED_STATUSES)

    rows_data = [_verdict_to_dict(v, ai_notes.get(i)) for i, v in enumerate(verdicts)]
    rows_json = json.dumps(rows_data).replace("</script>", "<\\/script>")

    bar_chart = _bar_chart_html(totals)

    tiles = [
        ("Total Budget", f"${total_amount:,.2f}", "#0b0b0b", "#ffffff"),
        ("Ineligible", f"${totals.get(STATUS_INELIGIBLE, 0.0) + totals.get(STATUS_OUTSIDE_PERIOD, 0.0):,.2f}", "#d03b3b", "#d03b3b"),
        ("Requires Justification", f"${totals.get(STATUS_REQUIRES_JUSTIFICATION, 0.0):,.2f}", "#fab219", "#fab219"),
        ("No Blocking Rule Found", f"${totals.get(STATUS_NO_BLOCKING_RULE, 0.0):,.2f}", "#0ca30c", "#0ca30c"),
    ]
    tiles_html = "\n".join(
        f'<div class="tile"><div class="tile-label">{html.escape(label)}</div>'
        f'<div class="tile-value" style="color:{light}">{html.escape(value)}</div></div>'
        for label, value, light, dark in tiles
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Eligible Spend -- Tri-Agency Budget Check</title>
<style>
  :root {{
    color-scheme: light;
    --surface-1: #fcfcfb;
    --page: #f9f9f7;
    --text-primary: #0b0b0b;
    --text-secondary: #52514e;
    --text-muted: #898781;
    --gridline: #e1e0d9;
    --border: rgba(11,11,11,0.10);
  }}
  @media (prefers-color-scheme: dark) {{
    :root:where(:not([data-theme="light"])) {{
      color-scheme: dark;
      --surface-1: #1a1a19;
      --page: #0d0d0d;
      --text-primary: #ffffff;
      --text-secondary: #c3c2b7;
      --text-muted: #898781;
      --gridline: #2c2c2a;
      --border: rgba(255,255,255,0.10);
    }}
  }}
  :root[data-theme="dark"] {{
    color-scheme: dark;
    --surface-1: #1a1a19;
    --page: #0d0d0d;
    --text-primary: #ffffff;
    --text-secondary: #c3c2b7;
    --text-muted: #898781;
    --gridline: #2c2c2a;
    --border: rgba(255,255,255,0.10);
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    background: var(--page);
    color: var(--text-primary);
    font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
    padding: 16px;
  }}
  .wrap {{ max-width: 980px; margin: 0 auto; }}
  h1 {{ font-size: 1.4rem; margin: 0 0 4px 0; }}
  .subtitle {{ color: var(--text-secondary); margin: 0 0 20px 0; font-size: 0.9rem; }}
  .disclaimer {{
    background: var(--surface-1);
    border: 1px solid var(--border);
    border-left: 4px solid #fab219;
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 0.85rem;
    color: var(--text-secondary);
    margin-bottom: 20px;
  }}
  .tiles {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 12px;
    margin-bottom: 24px;
  }}
  .tile {{
    background: var(--surface-1);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 14px 16px;
  }}
  .tile-label {{ font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 6px; }}
  .tile-value {{ font-size: 1.5rem; font-weight: 600; }}
  section {{
    background: var(--surface-1);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px;
    margin-bottom: 20px;
  }}
  h2 {{ font-size: 1.05rem; margin: 0 0 14px 0; }}
  .bar-row {{ display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }}
  .bar-label {{ width: 190px; font-size: 0.85rem; color: var(--text-secondary); display: flex; align-items: center; gap: 6px; flex-shrink: 0; }}
  .bar-icon {{ font-weight: 700; width: 16px; text-align: center; }}
  .bar-track {{ flex: 1; height: 20px; background: var(--gridline); border-radius: 4px; overflow: hidden; }}
  .bar-fill {{ height: 100%; border-radius: 4px; min-width: 2px; transition: width 0.3s; }}
  .bar-value {{ width: 100px; text-align: right; font-size: 0.85rem; font-variant-numeric: tabular-nums; color: var(--text-primary); flex-shrink: 0; }}
  .controls {{ display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }}
  select, input[type="search"] {{
    background: var(--page);
    color: var(--text-primary);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 0.85rem;
  }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; }}
  th, td {{ text-align: left; padding: 8px 6px; border-bottom: 1px solid var(--gridline); vertical-align: top; }}
  th {{ color: var(--text-muted); font-weight: 600; cursor: pointer; user-select: none; }}
  th:hover {{ color: var(--text-primary); }}
  .badge {{
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 2px 8px;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 600;
    white-space: nowrap;
  }}
  .reason {{ color: var(--text-secondary); font-size: 0.8rem; margin-top: 2px; }}
  .principle {{ color: var(--text-muted); font-size: 0.75rem; margin-top: 2px; }}
  .ai-note {{ color: var(--text-secondary); font-size: 0.8rem; margin-top: 4px; font-style: italic; }}
  .amount {{ font-variant-numeric: tabular-nums; white-space: nowrap; }}
  .empty {{ color: var(--text-muted); text-align: center; padding: 20px; }}
  @media (max-width: 600px) {{
    .bar-label {{ width: 110px; font-size: 0.75rem; }}
    .bar-value {{ width: 70px; font-size: 0.75rem; }}
    table, thead, tbody, th, td, tr {{ display: block; }}
    thead {{ display: none; }}
    td {{ border: none; padding: 2px 0; }}
    tr {{ border-bottom: 1px solid var(--gridline); padding: 10px 0; }}
    td::before {{ content: attr(data-label); color: var(--text-muted); font-size: 0.7rem; display: block; }}
  }}
</style>
</head>
<body>
<div class="wrap">
  <h1>Eligible Spend</h1>
  <p class="subtitle">Tri-Agency (NSERC/CIHR/SSHRC) budget compliance check &middot; grant period {html.escape(grant_start.isoformat())} to {html.escape(grant_end.isoformat())} &middot; {len(verdicts)} line items, {flagged_count} flagged</p>

  <div class="disclaimer">{html.escape(DISCLAIMER)}</div>

  <div class="tiles">
    {tiles_html}
  </div>

  <section>
    <h2>Budget by Verdict</h2>
    <div id="bar-chart">
      {bar_chart}
    </div>
    <table id="fallback-table" style="display:none">
      <thead><tr><th>Verdict</th><th>Amount</th></tr></thead>
      <tbody id="fallback-tbody"></tbody>
    </table>
  </section>

  <section>
    <h2>Line Items</h2>
    <div class="controls">
      <input type="search" id="search-box" placeholder="Search item, category, justification...">
      <select id="status-filter">
        <option value="">All statuses</option>
        <option value="{STATUS_OUTSIDE_PERIOD}">Outside Grant Period</option>
        <option value="{STATUS_INELIGIBLE}">Ineligible</option>
        <option value="{STATUS_REQUIRES_JUSTIFICATION}">Requires Justification</option>
        <option value="{STATUS_NO_BLOCKING_RULE}">No Blocking Rule Found</option>
      </select>
    </div>
    <table id="items-table">
      <thead>
        <tr>
          <th data-sort="item">Item</th>
          <th data-sort="category">Category</th>
          <th data-sort="amount">Amount</th>
          <th data-sort="date">Date</th>
          <th data-sort="status_label">Verdict</th>
        </tr>
      </thead>
      <tbody id="items-tbody"></tbody>
    </table>
    <div id="empty-state" class="empty" style="display:none">No line items match the current filter.</div>
  </section>

  <section>
    <h2>Export</h2>
    <p class="subtitle" style="margin-bottom:0">Flagged items were also written to <code>flagged_items.csv</code> alongside this report.</p>
  </section>
</div>

<script type="application/json" id="row-data">{rows_json}</script>
<script>
(function () {{
  "use strict";
  var STATUS_COLORS = {json.dumps(STATUS_COLORS)};
  var STATUS_ICONS = {json.dumps(STATUS_ICONS)};

  var rows = JSON.parse(document.getElementById("row-data").textContent);
  var tbody = document.getElementById("items-tbody");
  var emptyState = document.getElementById("empty-state");
  var searchBox = document.getElementById("search-box");
  var statusFilter = document.getElementById("status-filter");
  var sortKey = null;
  var sortDir = 1;

  function fmtAmount(n) {{
    return "$" + n.toLocaleString("en-CA", {{ minimumFractionDigits: 2, maximumFractionDigits: 2 }});
  }}

  function makeBadge(row) {{
    var badge = document.createElement("span");
    badge.className = "badge";
    var color = STATUS_COLORS[row.status];
    badge.style.background = color + "22";
    badge.style.color = color;
    badge.textContent = (STATUS_ICONS[row.status] || "") + " " + row.status_label;
    return badge;
  }}

  function cell(label) {{
    var td = document.createElement("td");
    td.setAttribute("data-label", label);
    return td;
  }}

  function renderRows(data) {{
    tbody.textContent = "";
    if (data.length === 0) {{
      emptyState.style.display = "block";
      return;
    }}
    emptyState.style.display = "none";
    data.forEach(function (row) {{
      var tr = document.createElement("tr");

      var tdItem = cell("Item");
      var itemStrong = document.createElement("div");
      itemStrong.textContent = row.item;
      tdItem.appendChild(itemStrong);
      if (row.reason) {{
        var reasonDiv = document.createElement("div");
        reasonDiv.className = "reason";
        reasonDiv.textContent = row.reason;
        tdItem.appendChild(reasonDiv);
      }}
      if (row.principle) {{
        var principleDiv = document.createElement("div");
        principleDiv.className = "principle";
        principleDiv.textContent = row.principle;
        tdItem.appendChild(principleDiv);
      }}
      if (row.ai_note) {{
        var aiDiv = document.createElement("div");
        aiDiv.className = "ai-note";
        aiDiv.textContent = "AI note: " + row.ai_note;
        tdItem.appendChild(aiDiv);
      }}
      tr.appendChild(tdItem);

      var tdCategory = cell("Category");
      tdCategory.textContent = row.category;
      tr.appendChild(tdCategory);

      var tdAmount = cell("Amount");
      tdAmount.className = "amount";
      tdAmount.textContent = fmtAmount(row.amount);
      tr.appendChild(tdAmount);

      var tdDate = cell("Date");
      tdDate.textContent = row.date;
      tr.appendChild(tdDate);

      var tdStatus = cell("Verdict");
      tdStatus.appendChild(makeBadge(row));
      tr.appendChild(tdStatus);

      tbody.appendChild(tr);
    }});
  }}

  function applyFilters() {{
    var q = searchBox.value.trim().toLowerCase();
    var statusVal = statusFilter.value;
    var filtered = rows.filter(function (row) {{
      var matchesQuery = !q || (
        row.item.toLowerCase().indexOf(q) !== -1 ||
        row.category.toLowerCase().indexOf(q) !== -1 ||
        (row.justification || "").toLowerCase().indexOf(q) !== -1
      );
      var matchesStatus = !statusVal || row.status === statusVal;
      return matchesQuery && matchesStatus;
    }});
    if (sortKey) {{
      filtered.sort(function (a, b) {{
        var av = a[sortKey], bv = b[sortKey];
        if (typeof av === "number" && typeof bv === "number") return (av - bv) * sortDir;
        return String(av).localeCompare(String(bv)) * sortDir;
      }});
    }}
    renderRows(filtered);
  }}

  searchBox.addEventListener("input", applyFilters);
  statusFilter.addEventListener("change", applyFilters);

  document.querySelectorAll("#items-table th[data-sort]").forEach(function (th) {{
    th.addEventListener("click", function () {{
      var key = th.getAttribute("data-sort");
      if (sortKey === key) {{
        sortDir = -sortDir;
      }} else {{
        sortKey = key;
        sortDir = 1;
      }}
      applyFilters();
    }});
  }});

  applyFilters();
}})();
</script>
</body>
</html>
"""
