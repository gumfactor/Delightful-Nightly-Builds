"""Deterministic packing list generator driven by weather + activity tags."""

from __future__ import annotations

from dataclasses import dataclass

ACTIVITY_TAGS = ("conference", "cottage", "boating", "golf", "outdoor", "business", "leisure")

RAIN_THRESHOLD_MM = 2.0
WIND_THRESHOLD_KMH = 40.0
MAX_CLOTHING_QUANTITY = 7  # beyond this, laundry is assumed rather than packing more

CATEGORY_CLOTHING = "Clothing"
CATEGORY_GEAR = "Gear"
CATEGORY_DOCS = "Documents & Admin"
CATEGORY_HEALTH = "Health & Comfort"
CATEGORIES = (CATEGORY_CLOTHING, CATEGORY_GEAR, CATEGORY_DOCS, CATEGORY_HEALTH)


@dataclass(frozen=True)
class WeatherSummary:
    avg_high_c: float
    avg_low_c: float
    any_rain: bool
    any_wind: bool
    temp_band: str  # 'cold' | 'cool' | 'mild' | 'hot'


def summarize_weather(daily_readings: list[dict]) -> WeatherSummary:
    if not daily_readings:
        raise ValueError("Cannot summarize an empty weather list.")

    highs = [d["temp_max_c"] for d in daily_readings]
    lows = [d["temp_min_c"] for d in daily_readings]
    avg_high = sum(highs) / len(highs)
    avg_low = sum(lows) / len(lows)
    any_rain = any(d["precip_mm"] > RAIN_THRESHOLD_MM for d in daily_readings)
    any_wind = any(d["wind_max_kmh"] > WIND_THRESHOLD_KMH for d in daily_readings)

    if avg_high < 5:
        band = "cold"
    elif avg_high < 15:
        band = "cool"
    elif avg_high < 25:
        band = "mild"
    else:
        band = "hot"

    return WeatherSummary(
        avg_high_c=round(avg_high, 1),
        avg_low_c=round(avg_low, 1),
        any_rain=any_rain,
        any_wind=any_wind,
        temp_band=band,
    )


def _clothing_items(weather: WeatherSummary, duration_days: int) -> list[str]:
    items: list[str] = []
    quantity = min(duration_days, MAX_CLOTHING_QUANTITY)
    suffix = " (laundry assumed for the rest of the trip)" if duration_days > MAX_CLOTHING_QUANTITY else ""
    items.append(f"{quantity} T-shirts/tops{suffix}")
    items.append(f"{quantity} pairs of socks & underwear{suffix}")

    if weather.temp_band == "cold":
        items += ["Thermal base layers", "Heavy insulated coat", "Insulated gloves & warm hat"]
    elif weather.temp_band == "cool":
        items += ["Warm layers (fleece or sweater)", "Light-to-mid jacket"]
    elif weather.temp_band == "mild":
        items += ["Light layers with a jacket for cooler evenings"]
    else:  # hot
        items += ["Lightweight breathable clothing", "Sun hat"]

    if weather.any_rain:
        items += ["Waterproof rain jacket", "Compact umbrella"]
    if weather.any_wind:
        items.append("Windbreaker (windy conditions expected)")

    return items


def _gear_items(weather: WeatherSummary, activity_tags: list[str]) -> list[str]:
    items = ["Phone charger & cable", "Reusable water bottle"]

    tag_gear = {
        "conference": ["Laptop & charger", "Notebook & pen", "Business cards"],
        "cottage": ["Bug spray", "Flashlight or headlamp", "Swimsuit"],
        "boating": [
            "Life jacket (bring your own or confirm one is provided)",
            "Waterproof dry bag",
            "Motion sickness remedy",
            "Polarized sunglasses",
        ],
        "golf": ["Golf glove", "Extra golf balls & tees", "Golf shoes/spikes"],
        "outdoor": ["Hiking boots", "First aid kit", "Trail map or offline GPS"],
        "business": ["Formal business attire", "Dress shoes"],
        "leisure": ["Casual comfortable clothing", "Book or entertainment for downtime"],
    }
    for tag in activity_tags:
        items += tag_gear.get(tag, [])

    if weather.temp_band == "hot":
        items.append("Sunscreen (SPF 30+)")
    if weather.temp_band == "cold":
        items.append("Hand & foot warmers")

    return items


def _docs_items(activity_tags: list[str], duration_days: int, destination_country: str, home_country: str) -> list[str]:
    items = ["Photo ID / driver's license", "Wallet & payment cards", "House/room keys"]

    if destination_country and destination_country.strip().lower() != home_country.strip().lower():
        items.append(f"Passport (destination is outside {home_country})")

    if duration_days >= 3:
        items.append("Prescription medications for the full trip")

    if "conference" in activity_tags or "business" in activity_tags:
        items.append("Printed or digital copy of itinerary and confirmations")

    return items


def _health_items(weather: WeatherSummary) -> list[str]:
    items = ["Any daily medications", "Basic toiletries"]

    if weather.temp_band == "hot":
        items += ["Sunscreen (SPF 30+)", "Extra water / electrolytes"]
    if weather.temp_band == "cold":
        items.append("Lip balm & moisturizer (dry cold air)")

    return items


def generate_packing_list(
    daily_readings: list[dict],
    duration_days: int,
    activity_tags: list[str],
    destination_country: str,
    home_country: str = "Canada",
) -> dict[str, list[str]]:
    """Return {category: [items]} for the four fixed categories.

    Raises ValueError for an empty weather list or non-positive duration.
    """
    if duration_days <= 0:
        raise ValueError("Trip duration must be at least 1 day.")

    weather = summarize_weather(daily_readings)
    activity_tags = [tag for tag in activity_tags if tag in ACTIVITY_TAGS]

    return {
        CATEGORY_CLOTHING: _clothing_items(weather, duration_days),
        CATEGORY_GEAR: _gear_items(weather, activity_tags),
        CATEGORY_DOCS: _docs_items(activity_tags, duration_days, destination_country, home_country),
        CATEGORY_HEALTH: _health_items(weather),
    }
