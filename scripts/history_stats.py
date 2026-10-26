"""Pure functions: daily weather rows -> HistoryStats. No I/O so they are unit-testable."""

from collections import defaultdict
from datetime import date

MONSOON_START = (6, 15)
MONSOON_END = (9, 30)


def _in_monsoon(d: date) -> bool:
    return MONSOON_START <= (d.month, d.day) <= MONSOON_END


def _longest_streak(flags: list[bool]) -> int:
    best = cur = 0
    for f in flags:
        cur = cur + 1 if f else 0
        best = max(best, cur)
    return best


def year_stats(rows: list[dict]) -> dict:
    """rows: [{date: date, tmax: float|None, tmin: float|None, precip: float|None}] for ONE year, sorted."""
    tmax = [r["tmax"] for r in rows if r["tmax"] is not None]
    tmin = [r["tmin"] for r in rows if r["tmin"] is not None]
    wet = [r for r in rows if r["precip"] is not None]
    mons = [r for r in wet if _in_monsoon(r["date"])]
    wettest = max(wet, key=lambda r: r["precip"], default=None)
    return {
        "days_observed": len(rows),
        "days_ge_100f": sum(t >= 100 for t in tmax),
        "days_ge_105f": sum(t >= 105 for t in tmax),
        "days_ge_110f": sum(t >= 110 for t in tmax),
        "days_ge_115f": sum(t >= 115 for t in tmax),
        "max_temp_f": round(max(tmax), 1) if tmax else None,
        "longest_streak_ge_110f": _longest_streak([(r["tmax"] or 0) >= 110 for r in rows]),
        "nights_le_32f": sum(t <= 32 for t in tmin),
        "nights_le_28f": sum(t <= 28 for t in tmin),
        "nights_le_20f": sum(t <= 20 for t in tmin),
        "min_temp_f": round(min(tmin), 1) if tmin else None,
        "nights_ge_90f": sum(t >= 90 for t in tmin),
        "precip_in": round(sum(r["precip"] for r in wet), 2),
        "monsoon_precip_in": round(sum(r["precip"] for r in mons), 2),
        "monsoon_days_ge_025in": sum(r["precip"] >= 0.25 for r in mons),
        "monsoon_days_ge_050in": sum(r["precip"] >= 0.5 for r in mons),
        "wettest_day": {"date": wettest["date"].isoformat(), "precip_in": round(wettest["precip"], 2)}
        if wettest and wettest["precip"] > 0 else None,
    }


def monthly_normals(rows: list[dict]) -> list[dict]:
    """Mean daily max/min and mean monthly precipitation across the supplied (30-year) rows."""
    by_month = defaultdict(lambda: {"tmax": [], "tmin": [], "years": set(), "precip": 0.0})
    for r in rows:
        m = by_month[r["date"].month]
        m["years"].add(r["date"].year)
        if r["tmax"] is not None:
            m["tmax"].append(r["tmax"])
        if r["tmin"] is not None:
            m["tmin"].append(r["tmin"])
        m["precip"] += r["precip"] or 0.0
    out = []
    for month in range(1, 13):
        m = by_month[month]
        if not m["years"]:
            continue
        out.append({
            "month": month,
            "mean_max_f": round(sum(m["tmax"]) / len(m["tmax"]), 1),
            "mean_min_f": round(sum(m["tmin"]) / len(m["tmin"]), 1),
            "mean_precip_in": round(m["precip"] / len(m["years"]), 2),
        })
    return out


def build_history(rows: list[dict], recent_years: list[int], normals_years: tuple[int, int]) -> dict:
    by_year = defaultdict(list)
    for r in rows:
        by_year[r["date"].year].append(r)
    per_year = {str(y): year_stats(by_year[y]) for y in recent_years if y in by_year}
    n = len(per_year) or 1

    def avg(key):
        vals = [s[key] for s in per_year.values() if s[key] is not None]
        return round(sum(vals) / len(vals), 1) if vals else None

    lo, hi = normals_years
    normals_rows = [r for r in rows if lo <= r["date"].year <= hi]
    all_tmax = [r for r in rows if r["tmax"] is not None]
    all_tmin = [r for r in rows if r["tmin"] is not None]
    hottest = max(all_tmax, key=lambda r: r["tmax"], default=None)
    coldest = min(all_tmin, key=lambda r: r["tmin"], default=None)
    return {
        "years": sorted(per_year, key=int),
        "per_year": per_year,
        "avg_per_year": {k: avg(k) for k in (
            "days_ge_105f", "days_ge_110f", "nights_le_32f", "nights_le_28f", "precip_in",
            "monsoon_precip_in", "monsoon_days_ge_050in", "longest_streak_ge_110f")},
        "years_count": n,
        "normals_period": f"{lo}-{hi}",
        "monthly_normals": monthly_normals(normals_rows),
        "record_in_period": {
            "hottest": {"date": hottest["date"].isoformat(), "temp_f": hottest["tmax"]} if hottest else None,
            "coldest": {"date": coldest["date"].isoformat(), "temp_f": coldest["tmin"]} if coldest else None,
        },
    }
