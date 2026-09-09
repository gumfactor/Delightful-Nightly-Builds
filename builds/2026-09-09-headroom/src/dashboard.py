"""Self-contained dark-mode HTML dashboard renderer.

All dynamic data is serialized once as JSON into a `<script type="application/json">`
block and read back out by the page's own JS via `JSON.parse` + `textContent`/
`createElement` DOM calls — never string-concatenated into HTML markup — so
no field value (a date, a dollar amount, or a briefing sentence) can break
out of its context. The embedded JSON also has any literal `</script>`
sequence escaped defensively before being written into the page.

Chart.js 4.4.4 is loaded from its pinned CDN URL for a cumulative-room
chart; if the CDN is unreachable the page falls back to a plain HTML table.
"""

from __future__ import annotations

import json

CHART_JS_CDN = "https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.4/chart.umd.min.js"


def _safe_json(data: dict) -> str:
    return json.dumps(data).replace("</", "<\\/")


def render_dashboard(context: dict) -> str:
    """`context` must be JSON-serializable (dates already converted to str)."""
    data_json = _safe_json(context)
    return f"""<!doctype html>
<html lang="en" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Headroom — RRSP/TFSA Contribution Tracker</title>
<script src="{CHART_JS_CDN}"></script>
<style>
  :root {{
    --bg: #0f1115; --panel: #171a21; --border: #262b36; --text: #e6e9ef;
    --muted: #9aa4b2; --accent: #5fb0ff; --good: #3ecf8e; --bad: #ff6b6b;
  }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; background: var(--bg); color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
  header {{ padding: 24px 20px 8px; }}
  h1 {{ margin: 0 0 4px; font-size: 1.5rem; }}
  .subtitle {{ color: var(--muted); font-size: 0.9rem; }}
  main {{ padding: 12px 20px 40px; max-width: 960px; margin: 0 auto; }}
  .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    gap: 16px; margin: 16px 0; }}
  .card {{ background: var(--panel); border: 1px solid var(--border); border-radius: 10px;
    padding: 16px; }}
  .card h2 {{ margin: 0 0 8px; font-size: 1rem; color: var(--muted); font-weight: 600; }}
  .amount {{ font-size: 1.8rem; font-weight: 700; }}
  .amount.good {{ color: var(--good); }}
  .amount.bad {{ color: var(--bad); }}
  .warning {{ background: #3a1f1f; border: 1px solid var(--bad); color: #ffd4d4;
    padding: 12px 16px; border-radius: 10px; margin: 16px 0; }}
  .briefing {{ background: var(--panel); border: 1px solid var(--border); border-radius: 10px;
    padding: 16px; margin: 16px 0; line-height: 1.5; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 8px; font-size: 0.9rem; }}
  th, td {{ text-align: left; padding: 6px 8px; border-bottom: 1px solid var(--border); }}
  th {{ color: var(--muted); font-weight: 600; }}
  .deadline-list {{ list-style: none; padding: 0; margin: 0; }}
  .deadline-list li {{ padding: 6px 0; border-bottom: 1px solid var(--border); }}
  #chart-fallback {{ display: none; }}
  canvas {{ max-width: 100%; }}
</style>
</head>
<body>
<header>
  <h1>Headroom</h1>
  <div class="subtitle" id="as-of-line"></div>
</header>
<main>
  <div id="warnings"></div>
  <div class="cards">
    <div class="card">
      <h2>TFSA Room</h2>
      <div class="amount" id="tfsa-amount"></div>
    </div>
    <div class="card">
      <h2>RRSP Room</h2>
      <div class="amount" id="rrsp-amount"></div>
    </div>
  </div>

  <div class="card">
    <h2>Deadlines</h2>
    <ul class="deadline-list" id="deadline-list"></ul>
  </div>

  <div class="briefing">
    <h2 style="margin-top:0;color:var(--muted);font-size:1rem;">Briefing</h2>
    <div id="briefing-text"></div>
  </div>

  <div class="card">
    <h2>Room Over Time</h2>
    <canvas id="room-chart" height="120"></canvas>
    <table id="chart-fallback">
      <thead><tr><th>Year</th><th>TFSA Balance</th><th>RRSP Balance</th></tr></thead>
      <tbody id="chart-fallback-body"></tbody>
    </table>
  </div>

  <div class="card">
    <h2>Contribution History</h2>
    <table>
      <thead><tr><th>Account</th><th>Date</th><th>Amount</th></tr></thead>
      <tbody id="history-body"></tbody>
    </table>
  </div>
</main>

<script id="headroom-data" type="application/json">{data_json}</script>
<script>
(function () {{
  var data = JSON.parse(document.getElementById('headroom-data').textContent);

  function money(n) {{
    var sign = n < 0 ? '-' : '';
    return sign + '$' + Math.abs(n).toLocaleString(undefined, {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
  }}

  document.getElementById('as-of-line').textContent = 'As of ' + data.as_of;

  var tfsaEl = document.getElementById('tfsa-amount');
  if (data.tfsa.is_overcontributed) {{
    tfsaEl.textContent = '-' + money(data.tfsa.overcontribution_amount);
    tfsaEl.classList.add('bad');
  }} else {{
    tfsaEl.textContent = money(data.tfsa.available_room);
    tfsaEl.classList.add('good');
  }}

  var rrspEl = document.getElementById('rrsp-amount');
  if (data.rrsp.is_overcontributed) {{
    rrspEl.textContent = '-' + money(data.rrsp.overcontribution_amount);
    rrspEl.classList.add('bad');
  }} else {{
    rrspEl.textContent = money(data.rrsp.available_room);
    rrspEl.classList.add('good');
  }}

  var warningsEl = document.getElementById('warnings');
  [data.tfsa, data.rrsp].forEach(function (acct, idx) {{
    if (acct.is_overcontributed) {{
      var div = document.createElement('div');
      div.className = 'warning';
      div.textContent = (idx === 0 ? 'TFSA' : 'RRSP') + ' is over-contributed by ' +
        money(acct.overcontribution_amount) + '. Estimated CRA tax: ' +
        money(acct.estimated_monthly_penalty) + '/month until resolved.';
      warningsEl.appendChild(div);
    }}
  }});

  var deadlineList = document.getElementById('deadline-list');
  data.deadlines.forEach(function (d) {{
    var li = document.createElement('li');
    li.textContent = d.label + ': ' + d.date + ' (' + d.days_until + ' days)';
    deadlineList.appendChild(li);
  }});

  document.getElementById('briefing-text').textContent = data.briefing;

  var historyBody = document.getElementById('history-body');
  data.history.forEach(function (row) {{
    var tr = document.createElement('tr');
    ['account', 'date', 'amount'].forEach(function (key) {{
      var td = document.createElement('td');
      td.textContent = key === 'amount' ? money(row[key]) : row[key];
      tr.appendChild(td);
    }});
    historyBody.appendChild(tr);
  }});

  var years = data.tfsa.year_snapshots.map(function (s) {{ return s.year; }});
  var tfsaBalances = data.tfsa.year_snapshots.map(function (s) {{ return s.ending_balance; }});
  var rrspByYear = {{}};
  data.rrsp.year_snapshots.forEach(function (s) {{ rrspByYear[s.year] = s.ending_balance; }});
  var rrspBalances = years.map(function (y) {{ return rrspByYear.hasOwnProperty(y) ? rrspByYear[y] : null; }});

  if (typeof Chart === 'undefined') {{
    document.getElementById('chart-fallback').style.display = 'table';
    var fbBody = document.getElementById('chart-fallback-body');
    years.forEach(function (y, i) {{
      var tr = document.createElement('tr');
      [y, money(tfsaBalances[i]), rrspBalances[i] === null ? '—' : money(rrspBalances[i])].forEach(function (v) {{
        var td = document.createElement('td');
        td.textContent = v;
        tr.appendChild(td);
      }});
      fbBody.appendChild(tr);
    }});
  }} else {{
    new Chart(document.getElementById('room-chart'), {{
      type: 'line',
      data: {{
        labels: years,
        datasets: [
          {{ label: 'TFSA balance', data: tfsaBalances, borderColor: '#5fb0ff', tension: 0.2 }},
          {{ label: 'RRSP balance', data: rrspBalances, borderColor: '#3ecf8e', tension: 0.2 }}
        ]
      }},
      options: {{ responsive: true, scales: {{ y: {{ beginAtZero: true }} }} }}
    }});
  }}
}})();
</script>
</body>
</html>
"""
