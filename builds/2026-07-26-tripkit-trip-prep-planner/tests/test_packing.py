import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import packing  # noqa: E402


def _daily(temp_max, temp_min, precip=0.0, wind=10.0):
    return {"temp_max_c": temp_max, "temp_min_c": temp_min, "precip_mm": precip, "wind_max_kmh": wind, "weathercode": 1}


def test_cold_wet_boating_produces_rain_gear_and_lifejacket_reminder():
    days = [_daily(2.0, -3.0, precip=8.0) for _ in range(3)]
    result = packing.generate_packing_list(days, duration_days=3, activity_tags=["boating"], destination_country="Canada")

    gear = " ".join(result[packing.CATEGORY_GEAR])
    clothing = " ".join(result[packing.CATEGORY_CLOTHING])
    assert "life jacket" in gear.lower()
    assert "waterproof rain jacket" in clothing.lower()
    assert "thermal base layers" in clothing.lower()


def test_hot_dry_golf_produces_sun_protection_and_golf_gear_no_cold_items():
    days = [_daily(30.0, 22.0, precip=0.0, wind=5.0) for _ in range(2)]
    result = packing.generate_packing_list(days, duration_days=2, activity_tags=["golf"], destination_country="Canada")

    gear = " ".join(result[packing.CATEGORY_GEAR])
    clothing = " ".join(result[packing.CATEGORY_CLOTHING])
    assert "golf glove" in gear.lower()
    assert "sunscreen" in gear.lower()
    assert "lightweight breathable clothing" in clothing.lower()
    assert "insulated" not in clothing.lower()
    assert "waterproof rain jacket" not in clothing.lower()


def test_high_wind_adds_windbreaker_note():
    days = [_daily(15.0, 8.0, precip=0.0, wind=55.0)]
    result = packing.generate_packing_list(days, duration_days=1, activity_tags=["outdoor"], destination_country="Canada")
    clothing = " ".join(result[packing.CATEGORY_CLOTHING])
    assert "windbreaker" in clothing.lower()


def test_low_wind_does_not_add_windbreaker_note():
    days = [_daily(15.0, 8.0, precip=0.0, wind=10.0)]
    result = packing.generate_packing_list(days, duration_days=1, activity_tags=["outdoor"], destination_country="Canada")
    clothing = " ".join(result[packing.CATEGORY_CLOTHING])
    assert "windbreaker" not in clothing.lower()


def test_foreign_destination_adds_passport_reminder():
    days = [_daily(15.0, 8.0)]
    result = packing.generate_packing_list(days, duration_days=2, activity_tags=["leisure"], destination_country="United States")
    docs = " ".join(result[packing.CATEGORY_DOCS])
    assert "passport" in docs.lower()


def test_domestic_destination_has_no_passport_reminder():
    days = [_daily(15.0, 8.0)]
    result = packing.generate_packing_list(days, duration_days=2, activity_tags=["leisure"], destination_country="Canada")
    docs = " ".join(result[packing.CATEGORY_DOCS])
    assert "passport" not in docs.lower()


def test_clothing_quantity_scales_with_duration_but_is_capped():
    short_days = [_daily(15.0, 8.0)]
    short_result = packing.generate_packing_list(short_days, duration_days=3, activity_tags=["leisure"], destination_country="Canada")
    assert "3 T-shirts/tops" in short_result[packing.CATEGORY_CLOTHING][0]

    long_days = [_daily(15.0, 8.0)]
    long_result = packing.generate_packing_list(long_days, duration_days=21, activity_tags=["leisure"], destination_country="Canada")
    assert f"{packing.MAX_CLOTHING_QUANTITY} T-shirts/tops" in long_result[packing.CATEGORY_CLOTHING][0]
    assert "laundry assumed" in long_result[packing.CATEGORY_CLOTHING][0]


def test_generate_packing_list_rejects_non_positive_duration():
    days = [_daily(15.0, 8.0)]
    try:
        packing.generate_packing_list(days, duration_days=0, activity_tags=["leisure"], destination_country="Canada")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_multi_day_trip_of_three_or_more_days_reminds_medication_supply():
    days = [_daily(15.0, 8.0) for _ in range(4)]
    result = packing.generate_packing_list(days, duration_days=4, activity_tags=["leisure"], destination_country="Canada")
    docs = " ".join(result[packing.CATEGORY_DOCS])
    assert "prescription medications for the full trip" in docs.lower()
