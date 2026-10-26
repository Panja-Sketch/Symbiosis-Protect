"""7-day Risk Ribbon: forecast tiles + risk colour + task pins. Thresholds come from thresholds.yaml."""

from datetime import timedelta

from app.models import Forecast


def day_risk(day, th: dict) -> tuple[str, str, list[str]]:
    """Returns (risk, icon, reasons). risk in none|elevated|high."""
    reasons, risk, icon = [], "none", "sun"

    def bump(level):
        nonlocal risk
        if level == "high" or risk == "none":
            risk = level

    if day.max_f is not None:
        if day.max_f >= th["heat_high_f"]:
            bump("high")
            icon = "heat"
            reasons.append(f"High of {round(day.max_f)}°F")
        elif day.max_f >= th["heat_elevated_f"]:
            bump("elevated")
            icon = "heat"
            reasons.append(f"High of {round(day.max_f)}°F")
    if day.min_f is not None:
        if day.min_f <= th["freeze_high_f"]:
            bump("high")
            icon = "freeze"
            reasons.append(f"Low of {round(day.min_f)}°F")
        elif day.min_f <= th["freeze_elevated_f"]:
            bump("elevated")
            icon = "freeze"
            reasons.append(f"Low of {round(day.min_f)}°F")
    if day.precip_in is not None:
        if day.precip_in >= th["rain_high_in"]:
            bump("high")
            icon = "storm"
            reasons.append(f"{day.precip_in:.2f} in of rain")
        elif day.precip_in >= th["rain_elevated_in"]:
            bump("elevated")
            icon = "rain"
            reasons.append(f"{day.precip_in:.2f} in of rain")
    return risk, icon, reasons


def build_ribbon(forecast: Forecast | None, alerts, tasks: list[dict], today, th: dict, days: int = 7) -> dict:
    by_date = {d.date: d for d in (forecast.daily if forecast else [])}
    out = []
    for i in range(days):
        d = today + timedelta(days=i)
        f = by_date.get(d)
        risk, icon, reasons = day_risk(f, th) if f else ("none", "unknown", [])
        evs = sorted({a.event for a in alerts if (a.onset or a.ends) and
                      (a.onset.date() if a.onset else d) <= d <= (a.ends.date() if a.ends else d)})
        if evs:
            risk = "high"
            reasons += [f"{e} (NWS)" if all(x.source == "NWS" for x in alerts if x.event == e) else f"{e} (SIMULATED)"
                        for e in evs]
        pins = [{"task_id": t["id"], "title": t["title"], "priority": t["priority"]}
                for t in tasks if t["status"] == "open" and t.get("relevant_date") and
                (t["relevant_date"] == d.isoformat() or (i == 0 and t["relevant_date"] < d.isoformat()))]
        out.append({"date": d.isoformat(), "max_f": f.max_f if f else None, "min_f": f.min_f if f else None,
                    "precip_in": f.precip_in if f else None, "icon": icon, "risk": risk, "reasons": reasons,
                    "alerts": evs, "task_pins": pins})
    return {"days": out, "provenance": forecast.provenance if forecast else None,
            "sources": forecast.sources if forecast else []}
