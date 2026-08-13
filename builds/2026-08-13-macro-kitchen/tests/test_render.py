import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import nutrition, planner, render
from src.recipes import RECIPES

RECIPES_BY_ID = {r["id"]: r for r in RECIPES}


def _sample_plan_row_and_meals():
    target = nutrition.full_target(
        sex="male", age=38, height_cm=178, weight_kg=76,
        activity_level="moderate", goal="maintain", goal_rate_kg_per_week=0,
    )
    meals_raw = planner.generate_plan(target.calories, target.protein_g)
    meals = [{**m, "id": i, "plan_id": 1, "day_note": None} for i, m in enumerate(meals_raw)]
    plan_row = {
        "id": 1, "created_at": "2026-08-13T00:00:00+00:00",
        "target_calories": target.calories, "target_protein_g": target.protein_g,
        "target_carbs_g": target.carbs_g, "target_fat_g": target.fat_g,
        "diet_filter": None, "exclude_filter": None,
    }
    return plan_row, meals


def test_build_dashboard_payload_has_7_days():
    plan_row, meals = _sample_plan_row_and_meals()
    payload = render.build_dashboard_payload(plan_row, meals, [])
    assert len(payload["days"]) == 7


def test_render_html_produces_valid_document():
    plan_row, meals = _sample_plan_row_and_meals()
    payload = render.build_dashboard_payload(plan_row, meals, [])
    html = render.render_html(payload)
    assert html.strip().startswith("<!doctype html>")
    assert "</html>" in html
    assert "Macro Kitchen" in html


def test_render_html_has_no_external_dependencies():
    plan_row, meals = _sample_plan_row_and_meals()
    payload = render.build_dashboard_payload(plan_row, meals, [])
    html = render.render_html(payload)
    assert "http://" not in html
    assert "https://" not in html


def test_script_injection_in_day_note_is_rendered_inert():
    plan_row, meals = _sample_plan_row_and_meals()
    payload_meals = [dict(m) for m in meals]
    payload_meals[0]["day_note"] = "</script><script>alert(1)</script>"
    payload = render.build_dashboard_payload(plan_row, payload_meals, [])
    html = render.render_html(payload)
    # The raw closing-script-then-opening-script sequence must never appear literally —
    # every '</' in the payload must be escaped to '<\/' inside the embedded JSON blob.
    assert "</script><script>alert(1)</script>" not in html
    assert "<\\/script><script>alert(1)<\\/script>" in html


def test_grocery_list_included_in_payload():
    plan_row, meals = _sample_plan_row_and_meals()
    grocery_list = [{"name": "eggs", "unit": "unit", "qty": 12}]
    payload = render.build_dashboard_payload(plan_row, meals, grocery_list)
    assert payload["grocery_list"] == grocery_list


def test_json_payload_is_parseable():
    import json

    plan_row, meals = _sample_plan_row_and_meals()
    payload = render.build_dashboard_payload(plan_row, meals, [])
    safe_json = render._safe_json_for_script_tag(payload)
    # Un-escape the </ neutralization the same way the browser's JSON.parse would
    # see it after HTML parses the <script> tag (HTML doesn't touch the '\/' at all,
    # so simulate what the raw text content is: the '<\/' sequence stays as literal
    # backslash-slash, which is valid JSON string escaping).
    parsed = json.loads(safe_json)
    assert parsed["plan"]["id"] == 1
