"""Pure helpers for FEMA National Risk Index rows."""

HAZARDS = {
    "HWAV": "Heat Wave", "CWAV": "Cold Wave", "IFLD": "Inland (riverine) Flooding", "HAIL": "Hail",
    "SWND": "Strong Wind", "WNTW": "Winter Weather", "ISTM": "Ice Storm", "LTNG": "Lightning",
    "TRND": "Tornado", "WFIR": "Wildfire", "DRGT": "Drought",
}


def _f(v: str) -> float | None:
    try:
        return float(v) if v not in ("", None) else None
    except ValueError:
        return None


def hazard_block(row: dict, code: str) -> dict:
    return {
        "name": HAZARDS[code],
        "eal_total_usd": _f(row.get(f"{code}_EALT", "")),
        "eal_score": _f(row.get(f"{code}_EALS", "")),   # national percentile 0-100
        "eal_rating": row.get(f"{code}_EALR") or None,
        "risk_score": _f(row.get(f"{code}_RISKS", "")),
        "risk_rating": row.get(f"{code}_RISKR") or None,
        "annual_frequency": _f(row.get(f"{code}_AFREQ", "")),
    }


def area_block(row: dict) -> dict:
    return {
        "population": _f(row.get("POPULATION", "")), "building_value_usd": _f(row.get("BUILDVALUE", "")),
        "risk_score": _f(row.get("RISK_SCORE", "")), "risk_rating": row.get("RISK_RATNG") or None,
        "eal_score": _f(row.get("EAL_SCORE", "")), "eal_total_usd": _f(row.get("EAL_VALT", "")),
        "social_vulnerability": row.get("SOVI_RATNG") or None,
        "community_resilience": row.get("RESL_RATNG") or None,
        "hazards": {c: hazard_block(row, c) for c in HAZARDS},
    }


def percentile_rank(value: float | None, population: list[float]) -> float | None:
    """Share of `population` strictly below value, 0-100 (None if no data)."""
    if value is None or not population:
        return None
    return round(100 * sum(v < value for v in population) / len(population), 1)
