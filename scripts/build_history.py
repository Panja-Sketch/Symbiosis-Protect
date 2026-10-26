"""Open-Meteo Historical archive -> data/derived/history_{location_id}.json (idempotent; raw cached).

Free tier is non-commercial (see docs/DECISIONS.md)."""

import json
import sys
from datetime import date

from history_stats import build_history
from lib import DERIVED, RAW, get_json, load_locations, write_json

URL = "https://archive-api.open-meteo.com/v1/archive"
START = date(1991, 1, 1)
RECENT_YEARS = [2021, 2022, 2023, 2024, 2025]
NORMALS = (1991, 2020)


def fetch_rows(loc: dict) -> dict:
    cache = RAW / "openmeteo" / f"{loc['id']}.json"
    if cache.exists():
        return json.loads(cache.read_text())
    cache.parent.mkdir(parents=True, exist_ok=True)
    data = get_json(URL, {
        "latitude": loc["lat"], "longitude": loc["lon"],
        "start_date": START.isoformat(), "end_date": "2025-12-31",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "temperature_unit": "fahrenheit", "precipitation_unit": "inch", "timezone": "America/Phoenix",
    })
    cache.write_text(json.dumps(data))
    return data


def to_rows(data: dict) -> list[dict]:
    d = data["daily"]
    return [
        {"date": date.fromisoformat(t), "tmax": mx, "tmin": mn, "precip": p}
        for t, mx, mn, p in zip(d["time"], d["temperature_2m_max"], d["temperature_2m_min"],
                                d["precipitation_sum"], strict=True)
    ]


def main():
    for loc in load_locations():
        data = fetch_rows(loc)
        stats = build_history(to_rows(data), RECENT_YEARS, NORMALS)
        stats.update({
            "location_id": loc["id"], "city": loc["city"], "provenance": "HISTORIC",
            "source": "Open-Meteo Historical Weather API (ERA5-based reanalysis), non-commercial tier",
            "source_url": "https://open-meteo.com/en/docs/historical-weather-api",
            "grid_lat": data["latitude"], "grid_lon": data["longitude"],
        })
        write_json(DERIVED / f"history_{loc['id']}.json", stats)
        print(loc["id"], loc["city"], stats["avg_per_year"], file=sys.stderr)


if __name__ == "__main__":
    main()
