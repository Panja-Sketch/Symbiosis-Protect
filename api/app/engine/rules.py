"""Rule evaluation: playbooks + context -> candidate tasks (deterministic; no AI involved)."""

import re
from dataclasses import dataclass, field

from app.engine.conditions import Hit, eval_when
from app.engine.context import Ctx
from app.engine.playbooks import Rule
from app.models import Asset

_VAR = re.compile(r"\{(\w+)(?:\|([^}]*))?\}")


def render(template: str, facts: dict) -> str:
    def sub(m):
        v = facts.get(m.group(1))
        if v is None or v == "":
            return m.group(2) if m.group(2) is not None else "unknown"
        return str(v)

    return " ".join(_VAR.sub(sub, template).split())


@dataclass
class Candidate:
    rule: Rule
    asset: Asset | None
    hit: Hit
    facts: dict = field(default_factory=dict)

    @property
    def key(self) -> tuple[str, str]:
        return self.rule.id, self.asset.id if self.asset else "-"


def applies(ctx: Ctx, rule: Rule) -> bool:
    if ctx.policy.lob not in rule.lob:
        return False
    a, p = rule.applies_if, ctx.profile
    checks = {
        "has_central_ac": lambda v: p.has_central_ac == v,
        "occupancy": lambda v: p.occupancy in v,
        "sprinkler_type": lambda v: p.sprinkler_type == v,
        "freeze_exposed_plumbing": lambda v: p.freeze_exposed_plumbing == v,
        "asset_exists": lambda v: bool(ctx.assets_of(v)),
        "elevation_gte_high_country":
            lambda v: (ctx.loc.elevation_ft >= ctx.thresholds["high_country_min_elevation_ft"]) == v,
    }
    return all(checks[k](v) for k, v in a.items())


def evaluate_rule(ctx: Ctx, rule: Rule) -> list[Candidate]:
    if not applies(ctx, rule):
        return []
    cands: list[Asset | None] = ctx.assets_of(rule.asset_types) if rule.scope == "asset" else [None]
    out = []
    for cand in cands:
        hit = eval_when(ctx, rule.when, cand)
        if not hit.ok:
            continue
        facts = {"city": ctx.loc.city, "elevation_ft": ctx.loc.elevation_ft,
                 "occupancy_text": ctx.profile.occupancy.replace("_", " "), **hit.facts}
        facts["trigger_text"] = " ".join(hit.reasons[:2])
        out.append(Candidate(rule, cand, hit, facts))
    return out


def evaluate_all(ctx: Ctx, rules: list[Rule]) -> list[Candidate]:
    return [c for r in rules for c in evaluate_rule(ctx, r)]
