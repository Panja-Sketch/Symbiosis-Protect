"""Pure parsers for NOAA NCEI Storm Events rows."""

import csv
import gzip
import io
import re
from collections import Counter, defaultdict

_DMG = re.compile(r"^\s*([0-9]*\.?[0-9]+)\s*([KMBkmb]?)\s*$")
_MULT = {"": 1, "K": 1e3, "M": 1e6, "B": 1e9}

KEEP = ("EVENT_ID", "STATE", "CZ_NAME", "EVENT_TYPE", "BEGIN_DATE_TIME", "CZ_TYPE", "CZ_FIPS",
        "INJURIES_DIRECT", "DEATHS_DIRECT", "DAMAGE_PROPERTY", "DAMAGE_CROPS", "MAGNITUDE",
        "MAGNITUDE_TYPE", "FLOOD_CAUSE", "BEGIN_LAT", "BEGIN_LON", "EPISODE_NARRATIVE")


def parse_damage(s: str | None) -> float:
    """'10.00K' -> 10000.0 ; '' / None / garbage -> 0.0"""
    if not s:
        return 0.0
    m = _DMG.match(s)
    return float(m.group(1)) * _MULT[m.group(2).upper()] if m else 0.0


def parse_ncei_date(s: str) -> str | None:
    """'15-JUL-21 16:30:00' -> '2021-07-15' (NCEI uses 2-digit years; 2-digit >50 means 19xx)."""
    m = re.match(r"(\d{1,2})-([A-Z]{3})-(\d{2}) ", s or "")
    if not m:
        return None
    months = "JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split()
    d, mon, yy = int(m.group(1)), months.index(m.group(2)) + 1, int(m.group(3))
    yr = 1900 + yy if yy > 50 else 2000 + yy
    return f"{yr:04d}-{mon:02d}-{d:02d}"


def read_events(raw_gz: bytes, state: str, counties: set[str]) -> list[dict]:
    """Filter a details CSV (gzip bytes) to `state` and county/zone names in `counties` (upper-case)."""
    out = []
    text = gzip.decompress(raw_gz).decode("utf-8", errors="replace")
    for row in csv.DictReader(io.StringIO(text)):
        if row["STATE"].upper() != state:
            continue
        # CZ_TYPE 'C' = county, 'Z' = forecast zone (names are zone names, not counties).
        date = parse_ncei_date(row["BEGIN_DATE_TIME"])
        if not date:
            continue
        out.append({
            "event_id": row["EVENT_ID"], "date": date, "event_type": row["EVENT_TYPE"],
            "area": row["CZ_NAME"].title(), "area_type": row["CZ_TYPE"], "area_fips": row["CZ_FIPS"],
            "property_damage_usd": parse_damage(row["DAMAGE_PROPERTY"]),
            "crop_damage_usd": parse_damage(row["DAMAGE_CROPS"]),
            "injuries": int(row["INJURIES_DIRECT"] or 0), "deaths": int(row["DEATHS_DIRECT"] or 0),
            "magnitude": float(row["MAGNITUDE"]) if row["MAGNITUDE"] else None,
            "magnitude_type": row["MAGNITUDE_TYPE"] or None,
            "flood_cause": row["FLOOD_CAUSE"] or None,
        })
    return out


def is_monsoon(date_iso: str) -> bool:
    md = (int(date_iso[5:7]), int(date_iso[8:10]))
    return (6, 15) <= md <= (9, 30)


def summarize(events: list[dict]) -> dict:
    by_type = Counter(e["event_type"] for e in events)
    monsoon = Counter(e["event_type"] for e in events if is_monsoon(e["date"]))
    per_year = defaultdict(int)
    for e in events:
        per_year[e["date"][:4]] += 1
    return {
        "total_events": len(events),
        "by_type": dict(by_type.most_common()),
        "monsoon_season_by_type": dict(monsoon.most_common()),
        "events_per_year": dict(sorted(per_year.items())),
        "property_damage_usd": round(sum(e["property_damage_usd"] for e in events)),
        "crop_damage_usd": round(sum(e["crop_damage_usd"] for e in events)),
        "injuries": sum(e["injuries"] for e in events),
        "deaths": sum(e["deaths"] for e in events),
    }
