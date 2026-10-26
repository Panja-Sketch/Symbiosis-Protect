"""TemplateExplainer: the deterministic answer. Always available; also the fallback for Gemini."""

from app.ai.retrieval import top_hits
from app.ai.schemas import GroundedAnswer, PolicyContext


def triggers(question: str, cfg: dict) -> list[str]:
    q = question.lower()
    return [name for name, phrases in cfg["handoff_triggers"].items() if any(p in q for p in phrases)]


def money(n) -> str:
    return f"${n:,.0f}"


def _cov_line(c: dict) -> str:
    bits = []
    if c.get("limit_usd"):
        bits.append(f"limit {money(c['limit_usd'])}")
    elif c.get("limit_note"):
        bits.append(c["limit_note"].lower())
    if c.get("deductible_usd"):
        bits.append(f"deductible {money(c['deductible_usd'])}")
    elif c.get("deductible_note"):
        bits.append(c["deductible_note"].lower())
    return f"({', '.join(bits)})" if bits else ""


class TemplateExplainer:
    name = "template"

    def __init__(self, cfg: dict):
        self.cfg = cfg

    def answer(self, question: str, ctx: PolicyContext) -> GroundedAnswer:
        cfg = self.cfg
        trig = triggers(question, cfg)
        hits = top_hits(ctx, question, cfg)
        policy_hits = [h for h in hits if h.kind in ("coverage", "endorsement", "exclusion")]
        notes = [h for h in hits if h.kind == "note"]
        gloss = [h for h in hits if h.kind == "glossary"]

        if not hits:
            topic = {"claim_decision": "I cannot decide how a specific loss would be handled. ",
                     "pricing": "I cannot speak to pricing or premiums. ",
                     "legal": "I cannot speak to legal questions. "}.get(trig[0] if trig else "", "")
            return GroundedAnswer(
                answer_plain=f"{topic}{cfg['no_match_text']} {cfg['handoff_text']} You can ask your agent, {ctx.agent['name']}, "
                             f"at {ctx.agent['email']}.",
                confidence="low", needs_agent=True,
                suggested_actions=[f"Ask {ctx.agent['name']} about this question."])

        parts: list[str] = []
        cited: list[str] = []
        actions: list[str] = []
        for h in policy_hits[:3]:
            cited.append(h.code)
            if h.kind == "coverage":
                c = h.data
                parts.append(f"Your policy summary describes “{c['name_plain']}” {_cov_line(c)}. "
                             f"It generally covers: {c['what_it_covers_plain']} "
                             f"It generally does not cover: {c['what_it_does_not_plain']}")
            elif h.kind == "endorsement":
                e = h.data
                if e["present"]:
                    parts.append(f"Your policy summary shows “{e['name_plain']}” is on your policy. {e['why_it_matters_plain']}")
                else:
                    parts.append(f"Your policy summary shows “{e['name_plain']}” is not on your policy. {e['why_it_matters_plain']}")
                    actions.append(f"Ask your agent about adding {e['name_plain']}.")
            else:
                x = h.data
                parts.append(f"Your policy summary lists “{x['title']}” as something generally left out. {x['plain']}")
        # Notes linked to what we cited add the \"sudden vs gradual\"-style nuance.
        for n in notes:
            if set(n.data["related_codes"]) & set(cited) or not policy_hits:
                parts.append(n.data["plain"])
                cited += [c for c in n.data["related_codes"] if c in ctx.codes() and c not in cited][:2]
                break
        # Related exclusions/endorsements worth mentioning that were not top hits.
        if policy_hits and policy_hits[0].kind == "coverage":
            for x in ctx.exclusions_plain:
                if x["code"] in {c for n in notes for c in n.data["related_codes"]} and x["code"] not in cited:
                    cited.append(x["code"])
        glossary_terms = [g.code for g in gloss[:1]]
        if gloss and not policy_hits:
            parts.append(f"{gloss[0].data['term']}: {gloss[0].data['plain']}")
            cited += [c for c in gloss[0].data.get("related_codes", []) if c in ctx.codes()][:2]
            if gloss[0].code == "Deductible":
                lines = [f"{c['name_plain']} {money(c['deductible_usd'])}" for c in ctx.coverages if c.get("deductible_usd")]
                if lines:
                    parts.append("Your policy summary lists these deductibles: " + "; ".join(dict.fromkeys(lines)) + ".")
                    cited += [c["code"] for c in ctx.coverages if c.get("deductible_usd")][:3]
            elif gloss[0].code == "Limit":
                lines = [f"{c['name_plain']} {money(c['limit_usd'])}" for c in ctx.coverages if c.get("limit_usd")][:6]
                if lines:
                    parts.append("Your policy summary lists these limits: " + "; ".join(lines) + ".")
                    cited += [c["code"] for c in ctx.coverages if c.get("limit_usd")][:6]

        needs_agent = bool(trig) or not (policy_hits or gloss or notes)
        if trig:
            kind = {"claim_decision": "how a specific loss would be decided", "pricing": "anything about pricing or premiums",
                    "legal": "anything legal"}[trig[0]]
            parts.append(f"I cannot speak to {kind}. {cfg['handoff_text']}")
            actions.append(f"Contact {ctx.agent['name']} ({ctx.agent['email']}) with the details of your situation.")
        else:
            parts.append(cfg["handoff_text"])
        top = hits[0].score
        conf = "high" if top >= cfg["retrieval"]["high_score"] and not trig else "medium" if not trig else "low"
        return GroundedAnswer(answer_plain=" ".join(parts), cited_coverage_codes=list(dict.fromkeys(cited)),
                              cited_glossary_terms=glossary_terms, confidence=conf, needs_agent=needs_agent,
                              suggested_actions=actions[:4])
