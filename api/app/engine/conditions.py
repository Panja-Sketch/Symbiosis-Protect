"""Condition evaluators. Each returns a Hit; `hours` is time until the triggering event (for urgency)."""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from app.engine.context import Ctx
from app.models import Asset


@dataclass
class Hit:
    ok: bool
    facts: dict = field(default_factory=dict)
    reasons: list[str] = field(default_factory=list)
    hours: float | None = None
    alert_ids: list[str] = field(default_factory=list)
    asset_ids: list[str] = field(default_factory=list)
    provenance: set = field(default_factory=set)  # LIVE / SIMULATED / SYNTHETIC / HISTORIC
    event_driven: bool = False  # triggered by something that just happened (sensor/event), not a forecast or a schedule


NO = Hit(False)


def _md_to_date(md: str, year: int) -> date:
    return date(year, int(md[:2]), int(md[3:5]))


def _assets(ctx: Ctx, spec_asset, cand: Asset | None) -> list[Asset]:
    types = [spec_asset] if isinstance(spec_asset, str) else list(spec_asset)
    if cand is not None and cand.type in types:
        return [cand]
    return ctx.assets_of(types)


def _window_days(ctx: Ctx, within_hours: int):
    start = ctx.today
    end = (ctx.now + timedelta(hours=within_hours)).date()
    return [d for d in (ctx.forecast.daily if ctx.forecast else []) if start <= d.date <= end]


def _fprov(ctx: Ctx) -> str:
    return "SIMULATED" if ctx.forecast and ctx.forecast.provenance == "SIMULATED" else "LIVE"


def _hours_until(ctx: Ctx, d: date) -> float:
    start = datetime.combine(d, datetime.min.time(), tzinfo=ctx.tz)
    return max(0.0, (start - ctx.now).total_seconds() / 3600)


# ---- weather ---------------------------------------------------------------------------------

def _active_alerts(ctx: Ctx, names: list[str]):
    out = []
    for a in ctx.alerts:
        if a.event not in names:
            continue
        end = a.ends or a.expires
        if end and end < ctx.now:
            continue
        if a.onset and a.onset - ctx.now > timedelta(hours=12):
            continue  # not near enough to act on yet
        out.append(a)
    return out


def _nws(ctx: Ctx, names: list[str]) -> Hit:
    hits = _active_alerts(ctx, names)
    if not hits:
        return NO
    a = hits[0]
    src = "SIMULATED" if a.provenance == "SIMULATED" else "LIVE"
    onset_h = max(0.0, (a.onset - ctx.now).total_seconds() / 3600) if a.onset else 0.0
    label = "SIMULATED NWS-style alert" if src == "SIMULATED" else "Official NWS alert"
    return Hit(True, {"event": a.event, "alert_headline": a.headline},
               [f"{label}: {a.event} is in effect for {ctx.loc.city}."], onset_h, [x.id for x in hits],
               provenance={src})


def c_nws_group(ctx, spec, cand):
    return _nws(ctx, ctx.thresholds["nws_groups"][spec])


def c_nws_event(ctx, spec, cand):
    return _nws(ctx, spec)


def c_forecast_max_temp_f(ctx, spec, cand):
    days = [d for d in _window_days(ctx, spec.get("within_hours", 96)) if d.max_f is not None and d.max_f >= spec["gte"]]
    if len(days) < spec.get("min_days", 1):
        return NO
    mx = max(d.max_f for d in days)
    return Hit(True, {"max_temp_f": round(mx), "days": len(days), "first_hot_date": days[0].date.isoformat()},
               [f"Forecast high of {round(mx)}°F for {len(days)} day(s) at or above {spec['gte']}°F."],
               _hours_until(ctx, days[0].date), provenance={_fprov(ctx)})


def c_forecast_min_temp_f(ctx, spec, cand):
    days = [d for d in _window_days(ctx, spec.get("within_hours", 72)) if d.min_f is not None and d.min_f <= spec["lte"]]
    if len(days) < spec.get("min_days", 1):
        return NO
    mn = min(d.min_f for d in days)
    return Hit(True, {"min_temp_f": round(mn), "days": len(days)},
               [f"Forecast low of {round(mn)}°F (at or below {spec['lte']}°F)."],
               _hours_until(ctx, days[0].date), provenance={_fprov(ctx)})


def c_forecast_precip_in(ctx, spec, cand):
    days = [d for d in _window_days(ctx, spec.get("within_hours", 24)) if (d.precip_in or 0) >= spec["gte"]]
    if not days:
        return NO
    p = max(d.precip_in for d in days)
    return Hit(True, {"precip_in": round(p, 2)}, [f"Forecast rain of {p:.2f} in or more within {spec.get('within_hours', 24)} hours."],
               _hours_until(ctx, days[0].date), provenance={_fprov(ctx)})


def c_season(ctx, spec, cand):
    s = ctx.thresholds["seasons"][spec["name"]]
    y = ctx.today.year
    start, end = _md_to_date(s["start"], y), _md_to_date(s["end"], y)
    if start <= end:
        in_season = start <= ctx.today <= end
        if not in_season and ctx.today > end:
            start = _md_to_date(s["start"], y + 1)
    else:  # wraps the new year (e.g. 10-15 .. 04-30); when out of season, start is later this year
        in_season = ctx.today >= start or ctx.today <= end
    if in_season:
        return Hit(True, {"season_text": "The season is under way."},
                   [f"{spec['name'].replace('_', ' ').title()} season is under way."],
                   ctx.thresholds["season_in_progress_urgency_hours"], provenance={"HISTORIC"})
    days_to = (start - ctx.today).days
    if spec.get("approaching") and 0 < days_to <= ctx.thresholds["approaching_days"]:
        return Hit(True, {"season_text": f"The season starts in {days_to} days."},
                   [f"{spec['name'].replace('_', ' ').title()} season starts in {days_to} days."], days_to * 24.0,
                   provenance={"HISTORIC"})
    return NO


# ---- assets ----------------------------------------------------------------------------------

def _age_text(a: Asset, year: int) -> str:
    if a.install_year is None:
        return "of unknown age"
    n = year - a.install_year
    return f"{n} year{'s' if n != 1 else ''} old (installed {a.install_year})"


def _asset_facts(a: Asset) -> dict:
    return {"asset_label": a.label, "asset_id": a.id, "material": a.material,
            "last_service": a.last_service_date.isoformat() if a.last_service_date else None}


def c_asset_age_years(ctx, spec, cand):
    thr = spec["gte_hard_water"] if ctx.loc.hard_water_zone else spec["gte_default"]
    best = None
    for a in _assets(ctx, spec["asset"], cand):
        unknown = a.install_year is None
        age = None if unknown else ctx.today.year - a.install_year
        if (unknown and spec.get("or_unknown")) or (age is not None and age >= thr):
            if best is None or (age or 99) > (best[0] or 99):
                best = (age, a)
    if not best:
        return NO
    age, a = best
    over = 0 if age is None else age - thr
    return Hit(True, {**_asset_facts(a), "age_text": _age_text(a, ctx.today.year), "age_years": age,
                      "threshold_years": thr, "years_over_threshold": over, "age_unknown": age is None},
               [f"{a.label} is {_age_text(a, ctx.today.year)}; the {'hard-water' if ctx.loc.hard_water_zone else 'standard'} "
                f"check threshold is {thr} years."],
               ctx.thresholds["stale_asset_urgency_hours"], asset_ids=[a.id], provenance={"SYNTHETIC"})


def c_asset_last_service_months(ctx, spec, cand):
    best = None
    for a in _assets(ctx, spec["asset"], cand):
        if a.last_service_date is None:
            months = None
            ok = spec.get("or_unknown", False)
        else:
            months = (ctx.today - a.last_service_date).days / 30.44
            ok = months >= spec["gte"]
        if ok and (best is None or (months if months is not None else 1e9) > (best[0] if best[0] is not None else 1e9)):
            best = (months, a)
    if not best:
        return NO
    months, a = best
    when = "no service on file" if months is None else f"last service {a.last_service_date.isoformat()} ({months:.0f} months ago)"
    return Hit(True, {**_asset_facts(a), "months_since_service": None if months is None else round(months)},
               [f"{a.label}: {when}; check interval is {spec['gte']} months."],
               ctx.thresholds["stale_asset_urgency_hours"], asset_ids=[a.id], provenance={"SYNTHETIC"})


def c_asset_attr(ctx, spec, cand):
    for a in _assets(ctx, spec["asset"], cand):
        val = a.model_dump().get(spec["attr"]) if spec["attr"] in a.model_dump() else a.attributes.get(spec["attr"])
        if val == spec["equals"]:
            return Hit(True, _asset_facts(a), [f"{a.label}: {spec['attr']} is {val}."],
                       ctx.thresholds["onboarding_urgency_hours"], asset_ids=[a.id], provenance={"SYNTHETIC"})
    return NO


# ---- profile / events / units ----------------------------------------------------------------

def c_always(ctx, spec, cand):
    return Hit(bool(spec), {"occupancy_text": ctx.profile.occupancy.replace("_", " ")},
               [f"Property is {ctx.profile.occupancy.replace('_', ' ')}."],
               ctx.thresholds["stale_asset_urgency_hours"], provenance={"SYNTHETIC"})


def c_closure_within_days(ctx, spec, cand):
    for c in sorted(ctx.profile.scheduled_closures, key=lambda c: c["start"]):
        start, end = date.fromisoformat(c["start"]), date.fromisoformat(c["end"])
        if end >= ctx.today and (start - ctx.today).days <= spec:
            norm = {m["month"]: m for m in ctx.history.get("monthly_normals", [])}.get(start.month)
            facts = {"closure_label": c["label"], "closure_start": f"{start:%B} {start.day}",
                     "closure_month": start.strftime("%B"),
                     "normal_low_f": round(norm["mean_min_f"]) if norm else "unknown"}
            return Hit(True, facts,
                       [f"Scheduled closure: {c['label']} starts {start.isoformat()}."],
                       _hours_until(ctx, start), provenance={"SYNTHETIC", "HISTORIC"})
    return NO


def _below_unit(label: str) -> str | None:
    if len(label) >= 2 and label[:-1].isdigit() and int(label[:-1]) > 1:
        return f"{int(label[:-1]) - 1}{label[-1]}"
    return None


def c_recent_event(ctx, spec, cand):
    cutoff = ctx.now - timedelta(hours=spec["within_hours"])
    for e in sorted(ctx.events, key=lambda e: e["at"], reverse=True):
        if e["kind"] not in spec["kinds"] or datetime.fromisoformat(e["at"]) < cutoff:
            continue
        if spec.get("needs_unit") and not e.get("unit_label"):
            continue
        facts = {"event_time": datetime.fromisoformat(e["at"]).astimezone(ctx.tz).strftime("%b %d %H:%M"),
                 "trigger_text": f"A {e['kind'].replace('_', ' ')} was reported at {ctx.loc.label}."}
        reasons = [f"{e['kind'].replace('_', ' ').title()} event at {e.get('unit_label') or ctx.loc.label} ({e.get('source', 'device')})."]
        if e.get("unit_label"):
            below = _below_unit(e["unit_label"])
            if spec.get("needs_unit") and not below:
                continue
            facts.update({"upper_unit": e["unit_label"], "below_unit": below})
        return Hit(True, facts, reasons, 0.0, provenance={"SIMULATED" if e.get("simulated") else "LIVE"}, event_driven=True)
    return NO


def _units(ctx: Ctx) -> list[Asset]:
    return [a for a in ctx.assets if a.type == "unit"]


def _unit_list(units: list[Asset], limit: int = 12) -> str:
    labels = sorted(u.unit_label for u in units)
    return ", ".join(labels[:limit]) + (f" (+{len(labels) - limit} more)" if len(labels) > limit else "")


def c_register_incomplete(ctx, spec, cand):
    units = _units(ctx)
    bad = [u for u in units if any(u.attributes.get(k) in (None, "") for k in spec["required"])]
    if not bad:
        return NO
    missing = sorted({k for u in bad for k in spec["required"] if u.attributes.get(k) in (None, "")})
    return Hit(True, {"units_count": len(bad), "unit_total": len(units), "units": _unit_list(bad),
                      "missing_text": ", ".join(m.replace("_", " ") for m in missing)},
               [f"{len(bad)} of {len(units)} units have missing register fields."],
               ctx.thresholds["onboarding_urgency_hours"], asset_ids=[u.id for u in bad], provenance={"SYNTHETIC"})


def c_units_match(ctx, spec, cand):
    units, attr = _units(ctx), spec["attr"]
    hit = []
    for u in units:
        v = u.attributes.get(attr)
        if "within_days" in spec:
            ok = bool(v) and 0 <= (ctx.today - date.fromisoformat(v)).days <= spec["within_days"]
            for k, want in (spec.get("and_attr_equals") or {}).items():
                ok = ok and u.attributes.get(k) == want
        elif "age_gte_hard_water" in spec:
            thr = spec["age_gte_hard_water"] if ctx.loc.hard_water_zone else spec["age_gte_default"]
            ok = v is not None and ctx.today.year - int(v) >= thr
        elif "older_than_months" in spec:
            ok = v is None or (ctx.today - date.fromisoformat(v)).days / 30.44 >= spec["older_than_months"]
        else:
            ok = False
        if ok:
            hit.append(u)
    if not hit:
        return NO
    thr = None
    if "age_gte_hard_water" in spec:
        thr = spec["age_gte_hard_water"] if ctx.loc.hard_water_zone else spec["age_gte_default"]
    return Hit(True, {"units_count": len(hit), "units": _unit_list(hit), "window_days": spec.get("within_days"),
                      "threshold_years": thr},
               [f"{len(hit)} unit(s) match: {attr.replace('_', ' ')}."], ctx.thresholds["stale_asset_urgency_hours"],
               asset_ids=[u.id for u in hit], provenance={"SYNTHETIC"})


REGISTRY = {
    "always": c_always, "nws_group": c_nws_group, "nws_event": c_nws_event,
    "forecast_max_temp_f": c_forecast_max_temp_f, "forecast_min_temp_f": c_forecast_min_temp_f,
    "forecast_precip_in": c_forecast_precip_in, "season": c_season, "asset_age_years": c_asset_age_years,
    "asset_last_service_months": c_asset_last_service_months, "asset_attr": c_asset_attr,
    "closure_within_days": c_closure_within_days, "recent_event": c_recent_event,
    "register_incomplete": c_register_incomplete, "units_match": c_units_match,
}


def eval_condition(ctx: Ctx, cond: dict, cand: Asset | None) -> Hit:
    (name, spec), = cond.items()
    return REGISTRY[name](ctx, spec, cand)


def merge(hits: list[Hit]) -> Hit:
    facts, reasons, alert_ids, asset_ids, prov, hours = {}, [], [], [], set(), []
    event = any(h.event_driven for h in hits)
    for h in hits:
        for k, v in h.facts.items():
            facts.setdefault(k, v)
        reasons += h.reasons
        alert_ids += h.alert_ids
        asset_ids += h.asset_ids
        prov |= h.provenance
        if h.hours is not None:
            hours.append(h.hours)
    return Hit(True, facts, reasons, min(hours) if hours else None, list(dict.fromkeys(alert_ids)),
               list(dict.fromkeys(asset_ids)), prov, event_driven=event)


def eval_when(ctx: Ctx, when: dict, cand: Asset | None) -> Hit:
    """(any: at least one) AND (all: every one). Missing group is vacuously true."""
    any_c = when.get("any", [])
    all_c = when.get("all", []) + when.get("and", [])
    parts: list[Hit] = []
    if any_c:
        oks = [h for h in (eval_condition(ctx, c, cand) for c in any_c) if h.ok]
        if not oks:
            return NO
        parts.append(merge(oks))
    for c in all_c:
        h = eval_condition(ctx, c, cand)
        if not h.ok:
            return NO
        parts.append(h)
    return merge(parts) if parts else NO
