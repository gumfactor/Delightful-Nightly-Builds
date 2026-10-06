"""Self-contained HTML report (no network, no external assets)."""
from __future__ import annotations

import json
from datetime import date

from .forecast import Upcoming
from .models import Series


def series_to_dict(item: Series) -> dict:
    return {
        "merchant": item.merchant,
        "cadence": item.cadence,
        "status": item.status,
        "typical_amount": item.typical_amount,
        "monthly_cost": item.monthly_cost,
        "annual_cost": item.annual_cost,
        "variable": item.variable,
        "confidence": item.confidence,
        "first_seen": item.charges[0].date.isoformat(),
        "last_seen": item.last_date.isoformat(),
        "next_expected": item.next_expected.isoformat() if item.next_expected else None,
        "cancelled_on": item.cancelled_on.isoformat() if item.cancelled_on else None,
        "price_changes": [
            {"date": c.date.isoformat(), "old": c.old, "new": c.new, "delta": c.delta, "percent": c.percent}
            for c in item.price_changes
        ],
        "zombie_charges": [
            {"date": t.date.isoformat(), "amount": t.amount}
            for t in item.charges
            if item.cancelled_on and item.status == "zombie" and t.date > item.cancelled_on
        ],
        "charges": [{"date": t.date.isoformat(), "amount": t.amount} for t in item.charges],
    }


def build_json(series: list[Series], upcoming: list[Upcoming]) -> dict:
    return {
        "series": [series_to_dict(s) for s in series],
        "upcoming": [
            {"date": u.date.isoformat(), "merchant": u.merchant, "amount": u.amount, "cadence": u.cadence}
            for u in upcoming
        ],
    }


def _safe_json(data: dict) -> str:
    """JSON safe to embed inside a <script> element."""
    return json.dumps(data).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def render_html(series: list[Series], upcoming: list[Upcoming], today: date, purchase_count: int) -> str:
    payload = build_json(series, upcoming)
    payload["today"] = today.isoformat()
    payload["purchases"] = purchase_count
    return _TEMPLATE.replace("__DATA__", _safe_json(payload))


_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Recurring Charge Radar</title>
<style>
:root{--bg:#f6f7f9;--card:#fff;--ink:#16191d;--mute:#5d6671;--line:#e1e5ea;--accent:#2457d6;--warn:#b45309;--bad:#b42318;--ok:#17803d;--bar:#2457d6;--space:16px}
@media (prefers-color-scheme:dark){:root{--bg:#0f1216;--card:#181c22;--ink:#e8ebef;--mute:#9aa4b0;--line:#2a3039;--accent:#7aa2ff;--warn:#f0b15a;--bad:#ff8a80;--ok:#5fd18a;--bar:#7aa2ff}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.45 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
main{max-width:860px;margin:0 auto;padding:var(--space)}
h1{font-size:1.4rem;margin:.2rem 0}h2{font-size:1.05rem;margin:1.6rem 0 .6rem}
.sub{color:var(--mute);font-size:.9rem;margin:0 0 var(--space)}
.tiles{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}
@media(min-width:620px){.tiles{grid-template-columns:repeat(4,1fr)}}
.tile,.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px}
.tile b{display:block;font-size:1.35rem;font-variant-numeric:tabular-nums}.tile span{color:var(--mute);font-size:.82rem}
.alert{border-left:4px solid var(--bad);background:var(--card);border-radius:8px;padding:10px 12px;margin:8px 0;border-top:1px solid var(--line);border-right:1px solid var(--line);border-bottom:1px solid var(--line)}
.alert.warn{border-left-color:var(--warn)}
.controls{display:flex;gap:8px;flex-wrap:wrap;margin:8px 0}
button,select{font:inherit;padding:8px 12px;border-radius:8px;border:1px solid var(--line);background:var(--card);color:var(--ink);min-height:40px}
button[aria-pressed=true]{border-color:var(--accent);color:var(--accent)}
ul{list-style:none;padding:0;margin:0}
.row{background:var(--card);border:1px solid var(--line);border-radius:12px;margin:8px 0}
.row>button{all:unset;display:block;width:100%;padding:12px;cursor:pointer;box-sizing:border-box}
.row>button:focus-visible{outline:2px solid var(--accent);border-radius:12px}
.top{display:flex;justify-content:space-between;gap:10px;align-items:baseline}
.name{font-weight:600;overflow-wrap:anywhere}.amt{font-variant-numeric:tabular-nums;white-space:nowrap;font-weight:600}
.meta{color:var(--mute);font-size:.85rem;margin-top:2px}
.bar{height:6px;background:var(--line);border-radius:3px;margin-top:8px;overflow:hidden}.bar i{display:block;height:100%;background:var(--bar)}
.tag{display:inline-block;font-size:.72rem;padding:1px 8px;border-radius:999px;border:1px solid var(--line);margin-left:6px;vertical-align:middle}
.tag.zombie{color:var(--bad);border-color:var(--bad)}.tag.lapsed,.tag.cancelled{color:var(--mute)}.tag.up{color:var(--warn);border-color:var(--warn)}.tag.var{color:var(--accent);border-color:var(--accent)}
.detail{padding:0 12px 12px;font-size:.9rem}.detail table{width:100%;border-collapse:collapse}.detail td{padding:3px 0;border-top:1px solid var(--line);font-variant-numeric:tabular-nums}.detail td:last-child{text-align:right}
.spark{width:100%;height:46px;margin:6px 0}
.up-list li{display:flex;justify-content:space-between;gap:10px;padding:8px 0;border-top:1px solid var(--line)}
.up-list li:first-child{border-top:0}
.empty{color:var(--mute);padding:8px 0}
</style>
</head>
<body>
<main>
<h1>Recurring Charge Radar</h1>
<p class="sub" id="sub"></p>
<div class="tiles" id="tiles"></div>
<div id="alerts"></div>
<h2>Next charges</h2>
<div class="card"><ul class="up-list" id="upcoming"></ul></div>
<h2>All recurring charges</h2>
<div class="controls" role="group" aria-label="Filter and sort">
  <button data-filter="live" aria-pressed="true">Live</button>
  <button data-filter="lapsed" aria-pressed="false">Ended</button>
  <button data-filter="all" aria-pressed="false">All</button>
  <select id="sort" aria-label="Sort by">
    <option value="annual_cost">Cost (highest)</option>
    <option value="next_expected">Next charge (soonest)</option>
    <option value="merchant">Name</option>
  </select>
</div>
<ul id="list"></ul>
</main>
<script id="data" type="application/json">__DATA__</script>
<script>
(function(){
"use strict";
var data = JSON.parse(document.getElementById("data").textContent);
var money = function(n){ return "$" + Number(n).toLocaleString("en-CA",{minimumFractionDigits:2,maximumFractionDigits:2}); };
var el = function(tag, cls, text){ var n = document.createElement(tag); if (cls) n.className = cls; if (text !== undefined) n.textContent = text; return n; };
var live = function(s){ return s.status === "active" || s.status === "zombie"; };
var state = {filter:"live", sort:"annual_cost"};
var liveSeries = data.series.filter(live);
var monthly = liveSeries.reduce(function(a,s){ return a + s.monthly_cost; }, 0);
var annual = liveSeries.reduce(function(a,s){ return a + s.annual_cost; }, 0);

document.getElementById("sub").textContent = data.purchases + " purchases analysed locally. Nothing leaves this device. As of " + data.today + ".";

function tile(value, label){ var t = el("div","tile"); t.appendChild(el("b",null,value)); t.appendChild(el("span",null,label)); return t; }
var tiles = document.getElementById("tiles");
tiles.appendChild(tile(money(monthly), "per month, live"));
tiles.appendChild(tile(money(annual), "per year, live"));
tiles.appendChild(tile(String(liveSeries.length), "live recurring charges"));
var next7 = data.upcoming.filter(function(u){ return (new Date(u.date) - new Date(data.today)) / 864e5 <= 7; });
tiles.appendChild(tile(money(next7.reduce(function(a,u){ return a + u.amount; }, 0)), "due in next 7 days"));

var alerts = document.getElementById("alerts");
data.series.forEach(function(s){
  if (s.status === "zombie") {
    var total = s.zombie_charges.reduce(function(a,c){ return a + c.amount; }, 0);
    var a = el("div","alert", s.merchant + ": still charging after you cancelled on " + s.cancelled_on + ". " + s.zombie_charges.length + " charge(s) since, " + money(total) + " total. Dispute or contact the merchant.");
    alerts.appendChild(a);
  }
  s.price_changes.forEach(function(c){
    if (live(s) && c.delta > 0) {
      alerts.appendChild(el("div","alert warn", s.merchant + " went up " + money(c.delta) + " (+" + c.percent + "%) on " + c.date + ": " + money(c.old) + " to " + money(c.new) + "."));
    }
  });
});

var up = document.getElementById("upcoming");
if (!data.upcoming.length) up.appendChild(el("li","empty","Nothing expected in the forecast window."));
data.upcoming.forEach(function(u){
  var li = el("li");
  var left = el("span"); left.appendChild(el("b",null,u.date)); left.appendChild(document.createTextNode("  " + u.merchant));
  li.appendChild(left); li.appendChild(el("span","amt",money(u.amount)));
  up.appendChild(li);
});

function sparkline(charges){
  var ns = "http://www.w3.org/2000/svg";
  var svg = document.createElementNS(ns,"svg");
  svg.setAttribute("viewBox","0 0 300 46"); svg.setAttribute("class","spark"); svg.setAttribute("role","img");
  svg.setAttribute("aria-label","Charge amounts over time");
  var vals = charges.map(function(c){ return c.amount; });
  var lo = Math.min.apply(null, vals), hi = Math.max.apply(null, vals);
  var span = hi - lo || 1;
  var pts = vals.map(function(v,i){ return (vals.length === 1 ? 150 : 4 + i * 292 / (vals.length - 1)).toFixed(1) + "," + (40 - (v - lo) / span * 34).toFixed(1); });
  var line = document.createElementNS(ns,"polyline");
  line.setAttribute("points", pts.join(" ")); line.setAttribute("fill","none"); line.setAttribute("stroke","currentColor"); line.setAttribute("stroke-width","2");
  svg.style.color = "var(--accent)"; svg.appendChild(line);
  return svg;
}

function render(){
  var list = document.getElementById("list");
  list.textContent = "";
  var items = data.series.filter(function(s){
    return state.filter === "all" || (state.filter === "live" ? live(s) : !live(s));
  });
  items.sort(function(a,b){
    if (state.sort === "merchant") return a.merchant.localeCompare(b.merchant);
    if (state.sort === "next_expected") return (a.next_expected || "9999").localeCompare(b.next_expected || "9999");
    return b.annual_cost - a.annual_cost;
  });
  if (!items.length) list.appendChild(el("li","empty","No charges in this view."));
  var maxCost = Math.max.apply(null, [1].concat(items.map(function(s){ return s.annual_cost; })));
  items.forEach(function(s){
    var li = el("li","row");
    var btn = el("button"); btn.setAttribute("aria-expanded","false");
    var top = el("div","top");
    var name = el("span","name",s.merchant);
    if (s.status !== "active") name.appendChild(el("span","tag " + s.status, s.status === "lapsed" ? "ended" : s.status));
    if (s.price_changes.length) name.appendChild(el("span","tag up","price change"));
    if (s.variable) name.appendChild(el("span","tag var","varies"));
    top.appendChild(name);
    top.appendChild(el("span","amt",(s.variable ? "~" : "") + money(s.typical_amount) + " / " + s.cadence.replace("biweekly","2 wk").replace("weekly","wk").replace("monthly","mo").replace("quarterly","qtr").replace("annual","yr")));
    btn.appendChild(top);
    btn.appendChild(el("div","meta", money(s.monthly_cost) + "/mo, " + money(s.annual_cost) + "/yr" + (s.next_expected ? ", next " + s.next_expected : ", last " + s.last_seen)));
    var bar = el("div","bar"); var fill = el("i"); fill.style.width = (s.annual_cost / maxCost * 100).toFixed(1) + "%"; bar.appendChild(fill); btn.appendChild(bar);
    var detail = el("div","detail"); detail.hidden = true;
    detail.appendChild(sparkline(s.charges));
    var table = el("table");
    s.charges.slice().reverse().slice(0,12).forEach(function(c){
      var tr = el("tr"); tr.appendChild(el("td",null,c.date)); tr.appendChild(el("td",null,money(c.amount))); table.appendChild(tr);
    });
    detail.appendChild(table);
    detail.appendChild(el("div","meta","Confidence " + Math.round(s.confidence * 100) + "%. First seen " + s.first_seen + ", " + s.charges.length + " charges."));
    btn.addEventListener("click", function(){ detail.hidden = !detail.hidden; btn.setAttribute("aria-expanded", String(!detail.hidden)); });
    li.appendChild(btn); li.appendChild(detail); list.appendChild(li);
  });
}
document.querySelectorAll("[data-filter]").forEach(function(b){
  b.addEventListener("click", function(){
    state.filter = b.dataset.filter;
    document.querySelectorAll("[data-filter]").forEach(function(o){ o.setAttribute("aria-pressed", String(o === b)); });
    render();
  });
});
document.getElementById("sort").addEventListener("change", function(e){ state.sort = e.target.value; render(); });
render();
})();
</script>
</body>
</html>
"""
