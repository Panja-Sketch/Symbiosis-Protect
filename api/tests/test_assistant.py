"""Phase 5 DoD: 20 scripted Q&A tests - no uncited claims, refuses unknowns - plus guardrail, fallback, limit and log tests."""

from datetime import UTC, datetime, timedelta

import pytest
from conftest import FakeWeather

from app.ai.guard import validate
from app.ai.schemas import GroundedAnswer
from app.ai.service import Assistant, RateLimited
from app.config import Settings
from app.deps import build_container
from app.store import MemoryStore

NOW = datetime(2026, 10, 25, 15, 0, tzinfo=UTC)
FORBIDDEN = ["you are covered", "will be covered", "guaranteed", "definitely covered", "we will pay", "will be paid"]


@pytest.fixture(scope="module")
def container():
    return build_container(Settings(scheduler_enabled=False), MemoryStore(), weather=FakeWeather())


def ask(container, acct, q):
    return container.assistant.ask(acct, q, NOW + timedelta(seconds=hash((acct, q)) % 1000))


# (account, question, must_cite_any, must_mention_any, needs_agent)
SCRIPT = [
    ("acct-p1", "Is water from my AC covered?", ["HO_WATER_SUDDEN"], ["suddenly", "sudden"], False),
    ("acct-p1", "Am I covered for monsoon flooding?", ["EX_FLOOD"], ["flood"], False),
    ("acct-p1", "What does my water-backup endorsement do?", ["END_WATER_BACKUP"], ["not on your policy"], False),
    ("acct-p1", "What is my deductible?", ["HO_DWELLING", "HO_WATER_SUDDEN"], ["$2,500"], False),
    ("acct-p1", "Do I get a hotel if my house is unlivable?", ["HO_LOSS_OF_USE"], ["living"], False),
    ("acct-p2", "What happens if the home is vacant between tenants?", ["EX_VACANCY", "END_VACANCY_PERMIT"], ["60 days"], False),
    ("acct-p2", "Do I get lost rent if the house is unusable?", ["DF_RENTAL_INCOME"], ["rent"], False),
    ("acct-p3", "What if a guest slips on a wet floor?", ["BOP_GL", "BOP_MEDPAY"], ["liability", "guest"], False),
    ("acct-p3", "What happens to my income if we have to close?", ["BOP_BI"], ["income"], False),
    ("acct-p3", "Is my walk-in cooler food covered if it fails?", ["BOP_SPOILAGE"], ["spoil"], False),
    ("acct-p4", "Does my policy cover a pipe that freezes?", ["BOP_FREEZE_CONDITION"], ["heat"], False),
    ("acct-p4", "What is the heat-maintenance condition?", ["END_HEAT_MAINTAIN", "BOP_FREEZE_CONDITION"], ["heat"], False),
    ("acct-p5", "What if a tenant's leak damages the unit below?", ["CRE_WATER_ESCAPE"], ["below", "unit"], False),
    ("acct-p5", "What does water backup cover?", ["END_WATER_BACKUP"], ["$100,000"], False),
    ("acct-p5", "Do I cover residents' belongings?", ["EX_TENANT_PROP"], ["renters insurance"], False),
    ("acct-p6", "Does my policy cover spoiled produce if the cooler fails?", ["AG_SPOILAGE"], ["spoil"], False),
    ("acct-p6", "What if the power goes out during a monsoon storm?", ["AG_UTILITY", "END_UTILITY_SERVICES"], ["power", "24"], False),
    ("acct-p6", "Are crops in the field covered?", ["EX_FIELD_CROPS"], ["crops"], False),
]


@pytest.mark.parametrize("acct,q,cites,mentions,needs", SCRIPT)
def test_grounded_answers_cite_and_hedge(container, acct, q, cites, mentions, needs):
    r = ask(container, acct, q)
    text = r["answer_plain"].lower()
    assert set(r["cited_coverage_codes"]) & set(cites), (r["cited_coverage_codes"], text)
    assert any(m.lower() in text for m in mentions), text
    assert r["needs_agent"] == needs
    assert not any(f in text for f in FORBIDDEN)
    assert "your policy summary" in text or "your agent" in text
    assert r["citations"] and all(c["name"] for c in r["citations"]), "UI chips need names"
    assert r["source"] == "template" and r["provenance"] == "SYNTHETIC"  # no AI configured: honest label


def test_unknown_topic_is_refused_not_invented(container):
    r = ask(container, "acct-p1", "Do you cover my dog's vet bills?")
    assert r["needs_agent"] and r["cited_coverage_codes"] == [] and r["confidence"] == "low"
    assert "could not find" in r["answer_plain"].lower() and "Dana Whitfield" in r["answer_plain"]


def test_claim_decision_questions_route_to_agent(container):
    r = ask(container, "acct-p1", "Will my claim be paid if the washer hose bursts?")
    text = r["answer_plain"].lower()
    assert r["needs_agent"] and "i cannot" in text and "will be paid" not in text
    assert r["cited_coverage_codes"], "still shows what the policy summary says"
    assert any("Dana" in a for a in r["suggested_actions"])


def test_pricing_and_legal_questions_route_to_agent(container):
    assert ask(container, "acct-p3", "How much is my premium going to be?")["needs_agent"]
    legal = ask(container, "acct-p3", "Can I sue the contractor? I need a lawyer")
    assert legal["needs_agent"] and "legal" in legal["answer_plain"].lower()


def test_glossary_definition_cites_the_term(container):
    r = ask(container, "acct-p1", "What is a deductible?")
    assert r["cited_glossary_terms"] == ["Deductible"] and not r["needs_agent"]


def test_answers_never_leak_other_accounts_data(container):
    r = ask(container, "acct-p1", "What is the spoilage limit and the generator?")
    blob = str(r).lower()
    assert "spoilage from cooling" not in blob and "desert bloom" not in blob and "$250,000" not in blob


def test_starters_exist_for_every_lob(container):
    for i in range(1, 7):
        s = container.assistant.starters(f"acct-p{i}")
        assert len(s) >= 4
        r = ask(container, f"acct-p{i}", s[0])
        assert r["answer_plain"] and (r["cited_coverage_codes"] or r["needs_agent"])


# ---- guardrails and fallback ----------------------------------------------------------------------------------------

class FakeGemini:
    def __init__(self, **kw):
        self.kw, self.calls = kw, 0

    def answer(self, question, ctx):
        self.calls += 1
        if self.kw.get("raise_"):
            raise RuntimeError("vertex down")
        return GroundedAnswer(source="gemini", provenance="AI", **self.kw["answer"])


def assistant(gemini, limit=30):
    store = MemoryStore()
    c = build_container(Settings(scheduler_enabled=False, ai_asks_per_hour=limit), store, weather=FakeWeather(), gemini=gemini)
    return c, c.assistant


GOOD = {"answer_plain": "Your policy summary says sudden water leaks are generally part of your home coverage, with a $2,500 deductible. "
        "Your agent confirms final coverage decisions.", "cited_coverage_codes": ["HO_WATER_SUDDEN"], "confidence": "high",
        "needs_agent": False, "suggested_actions": []}


def test_valid_gemini_answer_is_used_and_labelled_ai():
    c, a = assistant(FakeGemini(answer=GOOD))
    r = a.ask("acct-p1", "Is a burst pipe covered?", NOW)
    assert r["source"] == "gemini" and r["provenance"] == "AI" and r["fallback_reason"] is None


@pytest.mark.parametrize("patch,why", [
    ({"cited_coverage_codes": ["MADE_UP_CODE"]}, "cites codes"),
    ({"answer_plain": "You are covered for sure. Your agent can help."}, "forbidden"),
    ({"answer_plain": "Your policy summary says it pays $999,999. Your agent confirms."}, "dollar amounts"),
    ({"answer_plain": "Water leaks are fine."}, "hedge"),
    ({"cited_coverage_codes": [], "needs_agent": False}, "no citation"),
])
def test_bad_gemini_answers_fall_back_to_template(patch, why):
    c, a = assistant(FakeGemini(answer={**GOOD, **patch}))
    r = a.ask("acct-p1", "Is a burst pipe covered?", NOW)
    assert r["source"] == "template" and why in r["fallback_reason"]
    assert r["cited_coverage_codes"] or r["needs_agent"]


def test_gemini_outage_falls_back_without_error():
    c, a = assistant(FakeGemini(raise_=True))
    r = a.ask("acct-p1", "Is water from my AC covered?", NOW)
    assert r["source"] == "template" and "unavailable" in r["fallback_reason"] and r["cited_coverage_codes"]


def test_gemini_is_not_called_for_claim_or_pricing_questions():
    g = FakeGemini(answer=GOOD)
    c, a = assistant(g)
    r = a.ask("acct-p1", "Will my claim be approved?", NOW)
    assert g.calls == 0 and r["needs_agent"]


def test_response_cache_avoids_second_model_call():
    g = FakeGemini(answer=GOOD)
    c, a = assistant(g)
    a.ask("acct-p1", "Is a burst pipe covered?", NOW)
    a.ask("acct-p1", "covered burst pipe is?", NOW + timedelta(seconds=5))
    assert g.calls == 1
    logs = c.store.list("ai_logs")
    assert len(logs) == 2 and any(row["cache_hit"] for row in logs)


def test_rate_limit_per_account_per_hour():
    c, a = assistant(None, limit=3)
    for i in range(3):
        a.ask("acct-p1", f"Q{i} water leak?", NOW + timedelta(minutes=i))
    with pytest.raises(RateLimited):
        a.ask("acct-p1", "one more water leak?", NOW + timedelta(minutes=10))
    a.ask("acct-p2", "water leak?", NOW + timedelta(minutes=10))  # other accounts unaffected
    a.ask("acct-p1", "water leak later?", NOW + timedelta(minutes=75))  # window slides


def test_every_call_is_logged_without_the_question_text():
    c, a = assistant(None)
    a.ask("acct-p1", "Is water from my AC covered? my secret detail 12345", NOW)
    row = c.store.list("ai_logs")[0]
    assert row["fallback_used"] and row["model"] == "template" and len(row["prompt_hash"]) == 16 and "secret" not in str(row)
    assert {"latency_ms", "cited", "needs_agent", "at", "account_id"} <= set(row)


def test_guard_accepts_the_template_answers_for_every_starter(container):
    a: Assistant = container.assistant
    for i in range(1, 7):
        ctx = a.context(f"acct-p{i}")
        for q in a.starters(f"acct-p{i}"):
            ans = a.template.answer(q, ctx)
            assert validate(ans, ctx, a.cfg) == [], (i, q)
