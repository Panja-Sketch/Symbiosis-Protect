"""NOAA NCEI Storm Events (bulk CSV) -> data/derived/storm_events_az.json for persona counties."""

import re

import httpx
from lib import DERIVED, RAW, UA, download, load_locations, write_json
from storm_parse import read_events, summarize

BASE = "https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/"
YEARS = range(2016, 2026)  # last 10 complete years
# Event types relevant to the water/property perils in the playbooks.
RELEVANT = {
    "Flash Flood", "Flood", "Thunderstorm Wind", "Hail", "Heavy Rain", "Dust Storm", "Dust Devil",
    "Excessive Heat", "Heat", "Extreme Cold/Wind Chill", "Cold/Wind Chill", "Frost/Freeze",
    "Heavy Snow", "Winter Storm", "Winter Weather", "Lightning", "Strong Wind", "High Wind",
    "Funnel Cloud", "Tornado", "Wildfire", "Debris Flow", "Blizzard", "Ice Storm", "Drought",
}


def main():
    index = httpx.get(BASE, headers={"User-Agent": UA}, timeout=60).text
    locs = load_locations()
    events = []
    for y in YEARS:
        name = sorted(set(re.findall(rf"StormEvents_details-ftp_v1\.0_d{y}_c\d+\.csv\.gz", index)))[-1]
        path = download(BASE + name, RAW / "ncei" / name)
        events += read_events(path.read_bytes(), "ARIZONA", set())
    print("AZ events", len(events))
    out = {"provenance": "HISTORIC", "source": "NOAA NCEI Storm Events Database",
           "source_url": "https://www.ncei.noaa.gov/stormevents/", "years": [min(YEARS), max(YEARS)],
           "locations": {}}
    for loc in locs:
        # County rows (CZ_TYPE C) matched by county FIPS; forecast-zone rows (CZ_TYPE Z, e.g. heat and
        # freeze products issued by zone) matched by the location's own NWS zone number.
        cty_fips = loc["county_fips"][2:].lstrip("0")
        zone_num = loc["nws_zone"][3:].lstrip("0")
        mine = [e for e in events if e["event_type"] in RELEVANT and (
            (e["area_type"] == "C" and e["area_fips"].lstrip("0") == cty_fips)
            or (e["area_type"] == "Z" and e["area_fips"].lstrip("0") == zone_num))]
        out["locations"][loc["id"]] = {
            "county": loc["county"], "nws_zone": loc["nws_zone"], "summary": summarize(mine),
            # keep only significant rows (damage, injury, or large) to stay small
            "notable_events": sorted(
                (e for e in mine if e["property_damage_usd"] + e["crop_damage_usd"] >= 50_000
                 or e["injuries"] or e["deaths"]),
                key=lambda e: -(e["property_damage_usd"] + e["crop_damage_usd"]))[:25],
        }
        s = out["locations"][loc["id"]]["summary"]
        print(loc["id"], s["total_events"], list(s["by_type"].items())[:4])
    write_json(DERIVED / "storm_events_az.json", out)


if __name__ == "__main__":
    main()
