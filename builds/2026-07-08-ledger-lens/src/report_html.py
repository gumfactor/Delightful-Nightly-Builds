"""Self-contained dark-mode HTML dashboard renderer."""

from __future__ import annotations

import html
import json

CHARTJS_CDN = "https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"


def _escape(value) -> str:
    return html.escape(str(value), quote=True)


def render_html(
    summary: dict,
    monthly: list,
    categories: list,
    top_merchants: list,
    recurring: list,
    transactions: list,
    budget_status: list | None,
    insights: str,
    currency_symbol: str = "$",
) -> str:
    transaction_rows = [
        {
            "date": t.date.isoformat(),
            "description": t.description,
            "amount": round(t.amount, 2),
            "category": t.category,
            "recurring": t.recurring,
        }
        for t in sorted(transactions, key=lambda t: t.date, reverse=True)
    ]

    # Data is embedded as JSON inside a script tag (not loaded from an external file),
    # and "</script" sequences are escaped so an adversarial description can't break out.
    embedded_data = json.dumps({
        "summary": summary,
        "monthly": monthly,
        "categories": categories,
        "topMerchants": top_merchants,
        "recurring": recurring,
        "transactions": transaction_rows,
        "budgetStatus": budget_status,
        "currencySymbol": currency_symbol,
    }).replace("</script", "<\\/script")

    budget_section = ""
    if budget_status:
        rows = "\n".join(
            f'<div class="budget-row {"over" if b["over_budget"] else ""}">'
            f'<span class="budget-cat">{_escape(b["category"])}</span>'
            f'<div class="budget-bar-track"><div class="budget-bar-fill" '
            f'style="width:{min(b["pct_of_cap"], 100):.1f}%"></div></div>'
            f'<span class="budget-pct">{b["pct_of_cap"]:.0f}% of {currency_symbol}{b["monthly_cap"]:.0f}</span>'
            f"</div>"
            for b in budget_status
        )
        budget_section = f"""
        <section class="card">
          <h2>Budget vs. Actual (monthly average)</h2>
          <div class="budget-list">{rows}</div>
        </section>"""

    recurring_section = ""
    if recurring:
        items = "\n".join(
            f'<li><span class="rec-merchant">{_escape(r["merchant"])}</span>'
            f'<span class="rec-amount">{currency_symbol}{r["avg_amount"]:.2f}/mo</span>'
            f'<span class="rec-meta">{r["occurrences"]} charges &middot; {r["months_seen"]} months</span></li>'
            for r in recurring
        )
        recurring_monthly_total = sum(r["avg_amount"] for r in recurring)
        recurring_section = f"""
        <section class="card">
          <h2>Recurring Charges <span class="muted">({currency_symbol}{recurring_monthly_total:.2f}/mo total)</span></h2>
          <ul class="recurring-list">{items}</ul>
        </section>"""
    else:
        recurring_section = """
        <section class="card">
          <h2>Recurring Charges</h2>
          <p class="muted">No recurring charges detected across at least two months.</p>
        </section>"""

    recurring_badge = ' <span class="badge-recurring">recurring</span>'
    table_rows = "\n".join(
        f'<tr data-category="{_escape(t["category"])}" data-desc="{_escape(t["description"].lower())}">'
        f'<td>{_escape(t["date"])}</td>'
        f'<td>{_escape(t["description"])}{recurring_badge if t["recurring"] else ""}</td>'
        f'<td><span class="badge">{_escape(t["category"])}</span></td>'
        f'<td class="{"amount-neg" if t["amount"] < 0 else "amount-pos"}">'
        f'{currency_symbol}{t["amount"]:.2f}</td>'
        f"</tr>"
        for t in transaction_rows
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Ledger Lens — Spending Report</title>
<script src="{CHARTJS_CDN}"></script>
<style>
  :root {{
    --bg: #0f1117; --panel: #171a23; --border: #262b38; --text: #e6e8ee;
    --muted: #8b90a3; --accent: #6ea8fe; --pos: #4ade80; --neg: #f87171;
    --over: #f87171;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    background: var(--bg); color: var(--text); margin: 0; padding: 24px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  }}
  h1 {{ font-size: 1.5rem; margin: 0 0 4px 0; }}
  h2 {{ font-size: 1.05rem; margin: 0 0 16px 0; }}
  .muted {{ color: var(--muted); font-weight: normal; font-size: 0.85em; }}
  .subtitle {{ color: var(--muted); margin: 0 0 24px 0; }}
  .hero-grid {{
    display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 12px; margin-bottom: 24px;
  }}
  .stat {{
    background: var(--panel); border: 1px solid var(--border); border-radius: 10px;
    padding: 16px;
  }}
  .stat .label {{ color: var(--muted); font-size: 0.8rem; margin-bottom: 4px; }}
  .stat .value {{ font-size: 1.4rem; font-weight: 600; }}
  .grid {{
    display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
    gap: 16px; margin-bottom: 16px;
  }}
  .card {{
    background: var(--panel); border: 1px solid var(--border); border-radius: 10px;
    padding: 20px; overflow-x: auto;
  }}
  .insights {{
    background: var(--panel); border: 1px solid var(--border); border-left: 3px solid var(--accent);
    border-radius: 10px; padding: 16px 20px; margin-bottom: 24px; line-height: 1.5;
  }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
  th, td {{ text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--border); }}
  th {{ color: var(--muted); font-weight: 500; cursor: pointer; user-select: none; }}
  .amount-neg {{ color: var(--neg); }}
  .amount-pos {{ color: var(--pos); }}
  .badge {{
    background: #232838; border: 1px solid var(--border); border-radius: 999px;
    padding: 2px 10px; font-size: 0.78rem;
  }}
  .badge-recurring {{
    background: #2a2340; color: #c4b5fd; border-radius: 999px; padding: 1px 8px;
    font-size: 0.72rem; margin-left: 6px;
  }}
  #search {{
    width: 100%; padding: 10px 12px; margin-bottom: 12px; border-radius: 8px;
    border: 1px solid var(--border); background: #10131c; color: var(--text); font-size: 0.9rem;
  }}
  .recurring-list {{ list-style: none; padding: 0; margin: 0; }}
  .recurring-list li {{
    display: flex; justify-content: space-between; align-items: center;
    padding: 10px 0; border-bottom: 1px solid var(--border); gap: 12px;
  }}
  .recurring-list li:last-child {{ border-bottom: none; }}
  .rec-merchant {{ font-weight: 500; flex: 1; }}
  .rec-amount {{ color: var(--accent); font-weight: 600; }}
  .rec-meta {{ color: var(--muted); font-size: 0.8rem; white-space: nowrap; }}
  .budget-row {{ display: flex; align-items: center; gap: 12px; padding: 8px 0; }}
  .budget-cat {{ width: 130px; flex-shrink: 0; }}
  .budget-bar-track {{
    flex: 1; height: 10px; background: #10131c; border-radius: 6px; overflow: hidden;
  }}
  .budget-bar-fill {{ height: 100%; background: var(--accent); }}
  .budget-row.over .budget-bar-fill {{ background: var(--over); }}
  .budget-pct {{ width: 130px; text-align: right; color: var(--muted); font-size: 0.82rem; flex-shrink: 0; }}
  canvas {{ max-height: 280px; }}
  @media (max-width: 600px) {{
    body {{ padding: 12px; }}
    .budget-cat, .budget-pct {{ width: 90px; }}
  }}
</style>
</head>
<body>
<h1>Ledger Lens</h1>
<p class="subtitle">Spending report &middot; {summary['months_covered']} month(s) &middot; {summary['transaction_count']} transactions</p>

<div class="insights">{_escape(insights)}</div>

<div class="hero-grid">
  <div class="stat"><div class="label">Total Income</div><div class="value amount-pos">{currency_symbol}{summary['total_income']:.2f}</div></div>
  <div class="stat"><div class="label">Total Expenses</div><div class="value amount-neg">{currency_symbol}{summary['total_expenses']:.2f}</div></div>
  <div class="stat"><div class="label">Net</div><div class="value">{currency_symbol}{summary['net']:.2f}</div></div>
  <div class="stat"><div class="label">Avg Daily Spend</div><div class="value">{currency_symbol}{summary['avg_daily_spend']:.2f}</div></div>
</div>

<div class="grid">
  <section class="card">
    <h2>Spending by Category</h2>
    <canvas id="categoryChart"></canvas>
  </section>
  <section class="card">
    <h2>Monthly Income vs. Expenses</h2>
    <canvas id="trendChart"></canvas>
  </section>
</div>

<div class="grid">
  {recurring_section}
  {budget_section if budget_section else '<section class="card"><h2>Budget vs. Actual</h2><p class="muted">No budgets.json provided — pass --budgets to compare against monthly caps.</p></section>'}
</div>

<section class="card">
  <h2>Transactions</h2>
  <input id="search" type="text" placeholder="Search description or category...">
  <table id="txn-table">
    <thead>
      <tr>
        <th data-sort="date">Date</th>
        <th data-sort="desc">Description</th>
        <th data-sort="category">Category</th>
        <th data-sort="amount">Amount</th>
      </tr>
    </thead>
    <tbody>
      {table_rows}
    </tbody>
  </table>
</section>

<script id="ledger-data" type="application/json">{embedded_data}</script>
<script>
  const data = JSON.parse(document.getElementById('ledger-data').textContent);

  // Chart.js loads from a CDN; if that request fails (offline, blocked network),
  // skip the charts instead of throwing and breaking the search/sort below.
  if (typeof Chart === 'undefined') {{
    document.querySelectorAll('#categoryChart, #trendChart').forEach(canvas => {{
      const note = document.createElement('p');
      note.className = 'muted';
      note.textContent = 'Chart.js could not be loaded (no network access) — showing table data only.';
      canvas.replaceWith(note);
    }});
  }} else {{
    new Chart(document.getElementById('categoryChart'), {{
      type: 'doughnut',
      data: {{
        labels: data.categories.map(c => c.category),
        datasets: [{{
          data: data.categories.map(c => c.total),
          backgroundColor: [
            '#6ea8fe', '#f87171', '#4ade80', '#fbbf24', '#c084fc', '#22d3ee',
            '#fb923c', '#a3e635', '#f472b6', '#818cf8', '#2dd4bf', '#e879f9',
            '#facc15', '#94a3b8',
          ],
        }}]
      }},
      options: {{
        plugins: {{ legend: {{ position: 'right', labels: {{ color: '#e6e8ee', boxWidth: 12 }} }} }}
      }}
    }});

    new Chart(document.getElementById('trendChart'), {{
      type: 'line',
      data: {{
        labels: data.monthly.map(m => m.month),
        datasets: [
          {{ label: 'Income', data: data.monthly.map(m => m.income), borderColor: '#4ade80', tension: 0.2 }},
          {{ label: 'Expenses', data: data.monthly.map(m => m.expenses), borderColor: '#f87171', tension: 0.2 }},
        ]
      }},
      options: {{
        plugins: {{ legend: {{ labels: {{ color: '#e6e8ee' }} }} }},
        scales: {{
          x: {{ ticks: {{ color: '#8b90a3' }}, grid: {{ color: '#262b38' }} }},
          y: {{ ticks: {{ color: '#8b90a3' }}, grid: {{ color: '#262b38' }} }},
        }}
      }}
    }});
  }}

  const searchInput = document.getElementById('search');
  searchInput.addEventListener('input', () => {{
    const q = searchInput.value.toLowerCase();
    document.querySelectorAll('#txn-table tbody tr').forEach(row => {{
      const matches = row.dataset.desc.includes(q) || row.dataset.category.toLowerCase().includes(q);
      row.style.display = matches ? '' : 'none';
    }});
  }});

  let sortState = {{}};
  document.querySelectorAll('#txn-table th[data-sort]').forEach((th, colIndex) => {{
    th.addEventListener('click', () => {{
      const key = th.dataset.sort;
      const asc = !sortState[key];
      sortState = {{ [key]: asc }};
      const tbody = document.querySelector('#txn-table tbody');
      const rows = Array.from(tbody.querySelectorAll('tr'));
      rows.sort((a, b) => {{
        const av = a.children[colIndex].textContent.trim();
        const bv = b.children[colIndex].textContent.trim();
        const an = parseFloat(av.replace(/[^0-9.-]/g, ''));
        const bn = parseFloat(bv.replace(/[^0-9.-]/g, ''));
        let cmp;
        if (!isNaN(an) && !isNaN(bn) && key === 'amount') {{
          cmp = an - bn;
        }} else {{
          cmp = av.localeCompare(bv);
        }}
        return asc ? cmp : -cmp;
      }});
      rows.forEach(r => tbody.appendChild(r));
    }});
  }});
</script>
</body>
</html>
"""
