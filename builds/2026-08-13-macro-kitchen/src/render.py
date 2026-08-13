"""Self-contained dark-mode HTML dashboard renderer.

All dynamic data is embedded as a JSON blob inside a <script type="application/json">
tag (never string-concatenated into HTML) and read back with JSON.parse +
textContent/createElement on the client side, so recipe names, ingredient names,
or day notes containing markup are always rendered as inert text.
"""
from __future__ import annotations

import json

from src.recipes import get_recipe


def _safe_json_for_script_tag(data: dict) -> str:
    """json.dumps, then neutralize '</' so a value can never close the <script> tag early."""
    return json.dumps(data).replace("</", "<\\/")


def build_dashboard_payload(plan_row: dict, meals: list, grocery_list: list) -> dict:
    recipes_by_id = {}
    day_meals: dict[int, list] = {}
    day_totals: dict[int, dict] = {}

    for meal in meals:
        recipe = get_recipe(meal["recipe_id"])
        recipes_by_id[meal["recipe_id"]] = recipe
        multiplier = meal.get("portion_multiplier", 1.0)
        day = meal["day_index"]
        day_meals.setdefault(day, []).append({**meal, "recipe": recipe, "multiplier": multiplier})
        totals = day_totals.setdefault(
            day, {"calories": 0.0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0}
        )
        totals["calories"] += recipe["calories"] * multiplier
        totals["protein_g"] += recipe["protein_g"] * multiplier
        totals["carbs_g"] += recipe["carbs_g"] * multiplier
        totals["fat_g"] += recipe["fat_g"] * multiplier

    days = []
    for day_index in sorted(day_meals):
        days.append(
            {
                "day_index": day_index,
                "totals": day_totals[day_index],
                "note": next(
                    (m["day_note"] for m in day_meals[day_index] if m.get("day_note")), None
                ),
                "meals": [
                    {
                        "slot": m["slot"],
                        "recipe_id": m["recipe_id"],
                        "name": m["recipe"]["name"],
                        "portion_multiplier": m["multiplier"],
                        "calories": round(m["recipe"]["calories"] * m["multiplier"], 1),
                        "protein_g": round(m["recipe"]["protein_g"] * m["multiplier"], 1),
                        "carbs_g": round(m["recipe"]["carbs_g"] * m["multiplier"], 1),
                        "fat_g": round(m["recipe"]["fat_g"] * m["multiplier"], 1),
                        "prep_minutes": m["recipe"]["prep_minutes"],
                        "tags": m["recipe"]["tags"],
                        "ingredients": m["recipe"]["ingredients"],
                    }
                    for m in sorted(day_meals[day_index], key=lambda x: x["slot"])
                ],
            }
        )

    return {
        "plan": {
            "id": plan_row["id"],
            "created_at": plan_row["created_at"],
            "target_calories": plan_row["target_calories"],
            "target_protein_g": plan_row["target_protein_g"],
            "target_carbs_g": plan_row["target_carbs_g"],
            "target_fat_g": plan_row["target_fat_g"],
            "diet_filter": plan_row["diet_filter"],
            "exclude_filter": plan_row["exclude_filter"],
        },
        "days": days,
        "grocery_list": grocery_list,
    }


def render_html(payload: dict) -> str:
    data_json = _safe_json_for_script_tag(payload)

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Macro Kitchen — Plan #{payload['plan']['id']}</title>
<style>
  :root {{
    --bg: #0f1115; --panel: #1a1d24; --panel-2: #22262f; --text: #e8e9ec;
    --muted: #9aa0ab; --accent: #6fd3a4; --accent-2: #f2b880; --border: #2c313c;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; background: var(--bg); color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    line-height: 1.5;
  }}
  header {{ padding: 24px 20px; border-bottom: 1px solid var(--border); }}
  header h1 {{ margin: 0 0 6px; font-size: 1.5rem; }}
  header p {{ margin: 0; color: var(--muted); font-size: 0.9rem; }}
  main {{ max-width: 1000px; margin: 0 auto; padding: 20px; }}
  .targets {{
    display: grid; grid-template-columns: repeat(auto-fit, minmax(110px, 1fr));
    gap: 10px; margin-bottom: 24px;
  }}
  .stat {{
    background: var(--panel); border: 1px solid var(--border); border-radius: 10px;
    padding: 12px; text-align: center;
  }}
  .stat .value {{ font-size: 1.3rem; font-weight: 600; color: var(--accent); }}
  .stat .label {{ font-size: 0.75rem; color: var(--muted); text-transform: uppercase; }}
  canvas {{ background: var(--panel); border: 1px solid var(--border); border-radius: 10px;
    width: 100%; height: 220px; margin-bottom: 24px; }}
  .day {{
    background: var(--panel); border: 1px solid var(--border); border-radius: 12px;
    padding: 16px; margin-bottom: 16px;
  }}
  .day-header {{ display: flex; justify-content: space-between; align-items: baseline;
    margin-bottom: 10px; }}
  .day-header h2 {{ margin: 0; font-size: 1.05rem; }}
  .day-header .totals {{ color: var(--muted); font-size: 0.85rem; }}
  .note {{ color: var(--accent-2); font-size: 0.85rem; margin: 0 0 10px; font-style: italic; }}
  .meal {{ background: var(--panel-2); border-radius: 8px; padding: 10px 12px; margin-bottom: 8px; }}
  .meal-top {{ display: flex; justify-content: space-between; font-weight: 600; }}
  .meal-slot {{ text-transform: uppercase; font-size: 0.7rem; color: var(--muted); letter-spacing: 0.04em; }}
  .meal-macros {{ font-size: 0.8rem; color: var(--muted); margin-top: 4px; }}
  .tags {{ margin-top: 4px; }}
  .tag {{ display: inline-block; background: #263229; color: var(--accent); border-radius: 6px;
    padding: 1px 6px; font-size: 0.7rem; margin-right: 4px; }}
  section h2.section-title {{ font-size: 1.1rem; border-top: 1px solid var(--border);
    padding-top: 20px; margin-top: 8px; }}
  .grocery-list {{ columns: 2; column-gap: 24px; }}
  .grocery-item {{ break-inside: avoid; padding: 4px 0; border-bottom: 1px dashed var(--border);
    font-size: 0.9rem; }}
  .grocery-qty {{ color: var(--muted); }}
  @media (max-width: 500px) {{ .grocery-list {{ columns: 1; }} }}
</style>
</head>
<body>
<header>
  <h1>Macro Kitchen</h1>
  <p id="plan-subtitle"></p>
</header>
<main>
  <div class="targets" id="targets"></div>
  <canvas id="calorie-chart" width="900" height="220"></canvas>
  <div id="days"></div>
  <section>
    <h2 class="section-title">Grocery List</h2>
    <div class="grocery-list" id="grocery"></div>
  </section>
</main>

<script type="application/json" id="plan-data">{data_json}</script>
<script>
(function() {{
  var data = JSON.parse(document.getElementById('plan-data').textContent);

  document.getElementById('plan-subtitle').textContent =
    'Plan #' + data.plan.id + ' — generated ' + data.plan.created_at.slice(0, 10) +
    (data.plan.diet_filter ? ' — diet: ' + data.plan.diet_filter : '') +
    (data.plan.exclude_filter ? ' — excludes: ' + data.plan.exclude_filter : '');

  var targets = document.getElementById('targets');
  var targetSpecs = [
    ['Calories', Math.round(data.plan.target_calories) + ' kcal'],
    ['Protein', Math.round(data.plan.target_protein_g) + ' g'],
    ['Carbs', Math.round(data.plan.target_carbs_g) + ' g'],
    ['Fat', Math.round(data.plan.target_fat_g) + ' g']
  ];
  targetSpecs.forEach(function(spec) {{
    var stat = document.createElement('div');
    stat.className = 'stat';
    var value = document.createElement('div');
    value.className = 'value';
    value.textContent = spec[1];
    var label = document.createElement('div');
    label.className = 'label';
    label.textContent = spec[0];
    stat.appendChild(value);
    stat.appendChild(label);
    targets.appendChild(stat);
  }});

  // Hand-drawn Canvas 2D line chart of daily calories vs target — no chart library.
  var canvas = document.getElementById('calorie-chart');
  var ctx = canvas.getContext('2d');
  var w = canvas.width, h = canvas.height, pad = 36;
  var calories = data.days.map(function(d) {{ return d.totals.calories; }});
  var target = data.plan.target_calories;
  var maxVal = Math.max.apply(null, calories.concat([target])) * 1.1;
  var minVal = Math.min.apply(null, calories.concat([target])) * 0.9;
  function xFor(i) {{ return pad + (i / (calories.length - 1)) * (w - pad * 2); }}
  function yFor(v) {{ return h - pad - ((v - minVal) / (maxVal - minVal)) * (h - pad * 2); }}

  ctx.strokeStyle = '#f2b880';
  ctx.setLineDash([4, 4]);
  ctx.beginPath();
  ctx.moveTo(pad, yFor(target));
  ctx.lineTo(w - pad, yFor(target));
  ctx.stroke();
  ctx.setLineDash([]);

  ctx.strokeStyle = '#6fd3a4';
  ctx.lineWidth = 2;
  ctx.beginPath();
  calories.forEach(function(v, i) {{
    var x = xFor(i), y = yFor(v);
    if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
  }});
  ctx.stroke();

  ctx.fillStyle = '#6fd3a4';
  calories.forEach(function(v, i) {{
    ctx.beginPath();
    ctx.arc(xFor(i), yFor(v), 3, 0, Math.PI * 2);
    ctx.fill();
  }});

  ctx.fillStyle = '#9aa0ab';
  ctx.font = '11px sans-serif';
  calories.forEach(function(v, i) {{
    ctx.fillText('Day ' + (i + 1), xFor(i) - 14, h - pad + 16);
  }});

  var daysEl = document.getElementById('days');
  data.days.forEach(function(day) {{
    var dayDiv = document.createElement('div');
    dayDiv.className = 'day';

    var headerDiv = document.createElement('div');
    headerDiv.className = 'day-header';
    var h2 = document.createElement('h2');
    h2.textContent = 'Day ' + (day.day_index + 1);
    var totalsSpan = document.createElement('span');
    totalsSpan.className = 'totals';
    totalsSpan.textContent = Math.round(day.totals.calories) + ' kcal · ' +
      Math.round(day.totals.protein_g) + 'g P · ' + Math.round(day.totals.carbs_g) + 'g C · ' +
      Math.round(day.totals.fat_g) + 'g F';
    headerDiv.appendChild(h2);
    headerDiv.appendChild(totalsSpan);
    dayDiv.appendChild(headerDiv);

    if (day.note) {{
      var noteP = document.createElement('p');
      noteP.className = 'note';
      noteP.textContent = day.note;
      dayDiv.appendChild(noteP);
    }}

    day.meals.forEach(function(meal) {{
      var mealDiv = document.createElement('div');
      mealDiv.className = 'meal';

      var top = document.createElement('div');
      top.className = 'meal-top';
      var slotSpan = document.createElement('span');
      slotSpan.className = 'meal-slot';
      slotSpan.textContent = meal.slot;
      var nameSpan = document.createElement('span');
      nameSpan.textContent = meal.name + (meal.portion_multiplier !== 1 ? ' (' + meal.portion_multiplier + '× portion)' : '');
      top.appendChild(slotSpan);
      top.appendChild(nameSpan);
      mealDiv.appendChild(top);

      var macros = document.createElement('div');
      macros.className = 'meal-macros';
      macros.textContent = meal.calories + ' kcal · ' + meal.protein_g + 'g P · ' +
        meal.carbs_g + 'g C · ' + meal.fat_g + 'g F · ' + meal.prep_minutes + ' min';
      mealDiv.appendChild(macros);

      if (meal.tags.length) {{
        var tagsDiv = document.createElement('div');
        tagsDiv.className = 'tags';
        meal.tags.forEach(function(tag) {{
          var tagSpan = document.createElement('span');
          tagSpan.className = 'tag';
          tagSpan.textContent = tag;
          tagsDiv.appendChild(tagSpan);
        }});
        mealDiv.appendChild(tagsDiv);
      }}

      dayDiv.appendChild(mealDiv);
    }});

    daysEl.appendChild(dayDiv);
  }});

  var groceryEl = document.getElementById('grocery');
  data.grocery_list.forEach(function(item) {{
    var itemDiv = document.createElement('div');
    itemDiv.className = 'grocery-item';
    var qtySpan = document.createElement('span');
    qtySpan.className = 'grocery-qty';
    qtySpan.textContent = item.qty + ' ' + item.unit + ' — ';
    itemDiv.appendChild(qtySpan);
    itemDiv.appendChild(document.createTextNode(item.name));
    groceryEl.appendChild(itemDiv);
  }});
}})();
</script>
</body>
</html>
"""
