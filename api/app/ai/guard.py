"""Post-validation of any answer (model or template). An answer that fails is replaced by the template answer."""

import re

from app.ai.schemas import GroundedAnswer, PolicyContext

_MONEY = re.compile(r"\$\s?([0-9][0-9,]*(?:\.[0-9]+)?)")


def _money_values(text: str) -> set[int]:
    return {int(float(m.replace(",", ""))) for m in _MONEY.findall(text)}


def allowed_money(ctx: PolicyContext, cited: list[str]) -> set[int]:
    """Dollar figures the policy data actually contains for the cited items (limits, deductibles, sub-limits)."""
    vals: set[int] = set()
    for c in ctx.coverages:
        if c["code"] in cited:
            vals |= {int(v) for v in (c.get("limit_usd"), c.get("deductible_usd")) if v}
    for d in ctx.deductibles.values():
        if isinstance(d, int):
            vals.add(d)
    # figures quoted in plain text of cited endorsements/coverages/notes
    for coll in (ctx.coverages, ctx.endorsements, ctx.exclusions_plain):
        for it in coll:
            if it["code"] in cited:
                vals |= _money_values(" ".join(str(v) for v in it.values()))
    for n in ctx.coverage_notes:
        vals |= _money_values(n["plain"])
    return vals


def validate(ans: GroundedAnswer, ctx: PolicyContext, cfg: dict) -> list[str]:
    """Return a list of problems; empty means the answer may be shown."""
    problems = []
    text = ans.answer_plain
    low = text.lower()
    codes = ctx.codes()
    bad = [c for c in ans.cited_coverage_codes if c not in codes]
    if bad:
        problems.append(f"cites codes not in the policy: {bad}")
    for phrase in cfg["forbidden_in_answer"]:
        if phrase in low:
            problems.append(f"forbidden phrase: {phrase!r}")
    if not any(h in low for h in cfg["required_hedge_any"]):
        problems.append("missing the 'your policy summary / your agent' hedge")
    if not (ans.cited_coverage_codes or ans.cited_glossary_terms or ans.needs_agent):
        problems.append("no citation and no hand-off")
    extra = _money_values(text) - allowed_money(ctx, ans.cited_coverage_codes)
    if extra:
        problems.append(f"dollar amounts not found in cited policy items: {sorted(extra)}")
    terms = {g["term"] for g in ctx.glossary}
    if [t for t in ans.cited_glossary_terms if t not in terms]:
        problems.append("cites unknown glossary term")
    if len(ans.suggested_actions) > 4:
        problems.append("too many suggested actions")
    return problems
