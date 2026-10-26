"""Assistant orchestration: context -> (cache) -> Gemini -> validate -> else template. Rate-limited and logged."""

import hashlib
import logging
import re
import time
import uuid
from datetime import datetime, timedelta

import yaml

from app.ai.guard import validate
from app.ai.retrieval import tokens
from app.ai.schemas import GroundedAnswer, PolicyContext
from app.ai.template import TemplateExplainer, triggers
from app.engine.playbooks import PLAYBOOK_DIR

log = logging.getLogger("assistant")


def load_cfg() -> dict:
    return yaml.safe_load((PLAYBOOK_DIR / "assistant.yaml").read_text(encoding="utf-8"))


class RateLimited(Exception):
    pass


def normalize(q: str, stop: set[str]) -> str:
    return " ".join(sorted(set(tokens(q, stop))))


class Assistant:
    def __init__(self, store, cache, cfg: dict, gemini=None, asks_per_hour: int = 30, model_name: str = "none"):
        self.store, self.cache, self.cfg = store, cache, cfg
        self.gemini, self.limit, self.model_name = gemini, asks_per_hour, model_name
        self.template = TemplateExplainer(cfg)

    # ---- grounding ----------------------------------------------------------------------------
    def context(self, account_id: str) -> PolicyContext:
        s = self.store
        acct = s.get("accounts", account_id)
        pol = s.list("policies", account_id=account_id)[0]
        notes = [n for n in s.list("coverage_notes")]
        tasks = [{"title": t["title"], "why": t["why"], "coverage_codes": t["coverage_codes"]}
                 for t in s.list("tasks", account_id=account_id) if t["status"] == "open"]
        agent = s.get("agents", acct["agent_id"])
        return PolicyContext(
            lob=pol["lob"], product_label=pol["product_label"], coverages=pol["coverages"],
            endorsements=pol["endorsements"], exclusions_plain=pol["exclusions_plain"], deductibles=pol["deductibles"],
            coverage_notes=notes, glossary=s.list("glossary"), open_tasks=tasks,
            agent={"name": agent["name"], "email": agent["email"], "agency": agent["agency_name"]})

    def starters(self, account_id: str) -> list[str]:
        pol = self.store.list("policies", account_id=account_id)[0]
        return self.cfg["starters"][pol["lob"]]

    # ---- rate limit ---------------------------------------------------------------------------
    def _check_rate(self, account_id: str, now: datetime) -> None:
        doc = self.store.get("ai_rate", account_id) or {"asks": []}
        cutoff = (now - timedelta(hours=1)).isoformat()
        asks = [a for a in doc["asks"] if a > cutoff]
        if len(asks) >= self.limit:
            raise RateLimited(self.cfg["rate_limit_text"])
        asks.append(now.isoformat())
        self.store.put("ai_rate", account_id, {"id": account_id, "asks": asks})

    # ---- main ---------------------------------------------------------------------------------
    def ask(self, account_id: str, question: str, now: datetime) -> dict:
        question = question.strip()[:500]
        self._check_rate(account_id, now)
        ctx = self.context(account_id)
        pol_id = self.store.list("policies", account_id=account_id)[0]["id"]
        stop = set(self.cfg["stopwords"])
        ckey = f"ai:{pol_id}:{normalize(question, stop)}"
        cached = self.cache.get(ckey)
        t0 = time.perf_counter()
        used_cache = False
        reason = None
        if cached:
            ans, used_cache = GroundedAnswer(**cached), True
        else:
            ans = None
            forced_template = bool(triggers(question, self.cfg))  # claim/pricing/legal: deterministic hand-off only
            if self.gemini and not forced_template:
                try:
                    cand = self.gemini.answer(question, ctx)
                    problems = validate(cand, ctx, self.cfg)
                    if problems:
                        reason = "validation: " + "; ".join(problems)
                    else:
                        ans = cand
                except Exception as e:  # noqa: BLE001 - AI must never break the app
                    reason = f"gemini unavailable: {e.__class__.__name__}"
            elif forced_template:
                reason = "hand-off topic: deterministic answer"
            else:
                reason = "gemini not configured"
            if ans is None:
                ans = self.template.answer(question, ctx)
                ans.fallback_reason = reason
                leftover = validate(ans, ctx, self.cfg)
                if leftover:  # a template bug must never reach the user
                    log.error("template answer failed validation: %s", leftover)
                    ans = GroundedAnswer(answer_plain=f"{self.cfg['no_match_text']} {self.cfg['handoff_text']}",
                                         confidence="low", needs_agent=True, fallback_reason="template-validation")
            self.cache.set(ckey, ans.model_dump(mode="json"), 3600)
        latency = int((time.perf_counter() - t0) * 1000)
        self.store.put("ai_logs", f"ailog-{uuid.uuid4().hex[:10]}", {
            "id": f"ailog-{uuid.uuid4().hex[:10]}", "at": now.isoformat(), "account_id": account_id,
            "prompt_hash": hashlib.sha256(question.encode()).hexdigest()[:16], "model": self.model_name if ans.source == "gemini" else "template",
            "latency_ms": latency, "fallback_used": ans.source != "gemini", "fallback_reason": ans.fallback_reason,
            "cache_hit": used_cache, "cited": ans.cited_coverage_codes, "needs_agent": ans.needs_agent})
        return self.present(ans, ctx)

    def present(self, ans: GroundedAnswer, ctx: PolicyContext) -> dict:
        by_code = {}
        for c in ctx.coverages:
            by_code[c["code"]] = {"code": c["code"], "kind": "coverage", "name": c["name_plain"], "limit_usd": c.get("limit_usd"),
                                  "deductible_usd": c.get("deductible_usd")}
        for e in ctx.endorsements:
            by_code[e["code"]] = {"code": e["code"], "kind": "endorsement", "name": e["name_plain"], "present": e["present"]}
        for x in ctx.exclusions_plain:
            by_code[x["code"]] = {"code": x["code"], "kind": "exclusion", "name": x["title"]}
        d = ans.model_dump(mode="json")
        d["citations"] = [by_code[c] for c in ans.cited_coverage_codes if c in by_code]
        d["agent"] = ctx.agent
        d["provenance"] = "AI" if ans.source == "gemini" else "SYNTHETIC"
        return d


def clean_question(q: str) -> str:
    return re.sub(r"\s+", " ", q).strip()
