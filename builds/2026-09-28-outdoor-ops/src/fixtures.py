"""Bundled fixture data for the `demo` command — a realistic 7-day Toronto
snapshot with zero network calls, used for verification and first-run preview.
"""

from __future__ import annotations

# Deliberately distinct from cli.DEFAULT_LOCATION_NAME ("Toronto, ON"): demo
# rows share the real database file by default, and the upsert key is
# (location_name, forecast_date, sync_day). If this matched the live default
# location, running `demo` on the same day as a real `sync` — or vice versa —
# would silently overwrite real synced data with sample data for any
# overlapping forecast date.
DEMO_LOCATION_NAME = "Demo (Toronto, ON)"
DEMO_LAT = 43.6532
DEMO_LON = -79.3832

# A deliberately varied week: one washout day, one hot/smoky day, a couple of
# genuinely good days for each activity, so the dashboard has something to say.
DEMO_FORECAST = [
    dict(date="2026-09-28", temp_max=17.0, temp_min=10.0, precip_prob_max=10.0, precip_sum=0.0,
         wind_max=10.0, windgust_max=18.0, uv_index_max=4.0, weathercode=1),
    dict(date="2026-09-29", temp_max=14.0, temp_min=8.0, precip_prob_max=80.0, precip_sum=12.5,
         wind_max=28.0, windgust_max=45.0, uv_index_max=2.0, weathercode=63),
    dict(date="2026-09-30", temp_max=19.0, temp_min=11.0, precip_prob_max=5.0, precip_sum=0.0,
         wind_max=8.0, windgust_max=14.0, uv_index_max=5.0, weathercode=0),
    dict(date="2026-10-01", temp_max=27.0, temp_min=18.0, precip_prob_max=0.0, precip_sum=0.0,
         wind_max=6.0, windgust_max=10.0, uv_index_max=7.0, weathercode=0),
    dict(date="2026-10-02", temp_max=16.0, temp_min=9.0, precip_prob_max=30.0, precip_sum=1.0,
         wind_max=15.0, windgust_max=24.0, uv_index_max=3.0, weathercode=51),
    dict(date="2026-10-03", temp_max=12.0, temp_min=5.0, precip_prob_max=15.0, precip_sum=0.0,
         wind_max=11.0, windgust_max=19.0, uv_index_max=3.0, weathercode=2),
    dict(date="2026-10-04", temp_max=15.0, temp_min=7.0, precip_prob_max=0.0, precip_sum=0.0,
         wind_max=9.0, windgust_max=15.0, uv_index_max=4.0, weathercode=0),
]

DEMO_AIR_QUALITY = [
    dict(date="2026-09-28", aqi_max=42.0, aqi_mean=35.0, pm25_mean=8.0),
    dict(date="2026-09-29", aqi_max=25.0, aqi_mean=20.0, pm25_mean=5.0),
    dict(date="2026-09-30", aqi_max=48.0, aqi_mean=38.0, pm25_mean=9.0),
    dict(date="2026-10-01", aqi_max=135.0, aqi_mean=110.0, pm25_mean=42.0),
    dict(date="2026-10-02", aqi_max=55.0, aqi_mean=44.0, pm25_mean=11.0),
    dict(date="2026-10-03", aqi_max=30.0, aqi_mean=24.0, pm25_mean=6.0),
    dict(date="2026-10-04", aqi_max=33.0, aqi_mean=27.0, pm25_mean=7.0),
]
