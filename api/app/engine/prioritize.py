"""Deterministic prioritization (BUILD_SPEC §5.3):
score = severity(peril, lob) x priority x urgency(time_to_event) x exposure x (1 - completion_recency)."""

from datetime import datetime

from app.engine.context import Ctx
from app.engine.rules import Candidate


def urgency(scoring: dict, hours: float | None) -> float:
    h = 0.0 if hours is None else hours
    for row in scoring["urgency"]:
        if h <= row["within_hours"]:
            return row["value"]
    return scoring["urgency"][-1]["value"]


def exposure(ctx: Ctx, c: Candidate) -> float:
    s = ctx.config.scoring["exposure"]
    e = s["base"]
    f = c.facts
    if f.get("age_unknown"):
        e += s["unknown_age"]
    e += max(0, f.get("years_over_threshold") or 0) * s["per_year_over_threshold"]
    e += s["prior_claim_same_peril"] * sum(1 for cl in ctx.claims if cl.peril == c.rule.peril)
    code = ctx.config.scoring.get("nri_hazard_for_peril", {}).get(c.rule.peril)
    tract = (ctx.nri or {}).get("tract") or (ctx.nri or {}).get("county") or {}
    hz = tract.get("hazards", {}).get(code) if code else None
    pct = (hz or {}).get("az_tract_percentile")
    if pct is not None:
        e += s["nri_percentile_weight"] * pct / 100
    return min(e, s["cap"])


def completion_recency(ctx: Ctx, c: Candidate, last_done: datetime | None) -> float:
    if last_done is None:
        return 0.0
    decay = c.rule.cooldown_days or ctx.config.scoring["completion_recency"]["decay_days_default"]
    days = (ctx.now - last_done).total_seconds() / 86400
    return max(0.0, 1 - days / decay)


def score(ctx: Ctx, c: Candidate, last_done: datetime | None = None) -> float:
    sc = ctx.config.scoring
    sev = sc["severity_weight"].get(c.rule.peril, {}).get(ctx.policy.lob, 1.0)
    val = (sev * sc["priority_weight"][c.rule.priority] * urgency(sc, c.hit.hours) * exposure(ctx, c)
           * (1 - completion_recency(ctx, c, last_done)))
    return round(val, 4)
