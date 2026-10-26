"""Golden tests: given fixture weather + seed data, the rules produce exactly the expected tasks."""

from datetime import timedelta

import pytest
from conftest import NOW, alert, rule_ids

from app.engine.playbooks import load_rules

HEAT_STORM = {"hi": 114.0, "lo": 90.0}


def run(env, acct):
    engine, store, weather = env
    summary = engine.evaluate_account(acct)
    return engine, store, weather, summary


def test_baseline_calm_day_expected_tasks_per_persona(env):
    engine, *_ = env
    for acct in (f"acct-p{i}" for i in range(1, 7)):
        engine.evaluate_account(acct)
    assert rule_ids(engine, "acct-p1") == ["ho.hose_age", "ho.know_shutoff", "ho.water_heater_age"]
    assert rule_ids(engine, "acct-p2") == ["ho.hose_age", "ho.travel_vacancy_shutoff", "ho.water_heater_age"]
    assert rule_ids(engine, "acct-p3") == ["bop.ice_maker_lines", "bop.ice_maker_lines", "bop.monsoon_roof_drains",
                                           "bop.water_heater_age"]
    assert rule_ids(engine, "acct-p4") == ["bop.snow_load_roof", "bop.sprinkler_annual_inspection",
                                           "bop.water_heater_age"]
    assert rule_ids(engine, "acct-p5") == ["cre.risers_roof_drains", "cre.turnover_supply_lines",
                                           "cre.water_heater_by_unit"]
    assert rule_ids(engine, "acct-p6") == ["ag.heat_power_backup", "ag.preharvest_refrigeration",
                                           "ag.washdown_backflow"]


def test_every_persona_has_at_least_three_tasks_with_why_and_steps(env):
    engine, *_ = env
    for i in range(1, 7):
        engine.evaluate_account(f"acct-p{i}")
        tasks = engine.tasks(f"acct-p{i}", "open")
        assert len(tasks) >= 3
        for t in tasks:
            assert len(t["steps"]) >= 3 and t["why"] and "{" not in t["why"] + t["title"]
            assert t["inputs_snapshot"]["reasons"], "why-now must cite its inputs"


def test_do_now_is_capped_at_three(env):
    engine, *_ = env
    engine.evaluate_account("acct-p3")
    open_ = engine.tasks("acct-p3", "open")
    assert len(open_) == 4
    assert sum(t["bucket"] == "do_now" for t in open_) == 3
    # the lowest-scoring one is demoted
    assert min(open_, key=lambda t: t["score"])["bucket"] == "coming_up"


def test_heat_wave_creates_condensate_task_for_maya_with_simulated_provenance(env):
    engine, store, weather = env
    weather.set_days("loc-p1", hi=114.0, lo=90.0)
    weather.alerts["loc-p1"] = [alert("Extreme Heat Warning", sim=True)]
    summary = engine.evaluate_account("acct-p1")
    t = next(t for t in engine.tasks("acct-p1", "open") if t["rule_id"] == "az.ho.condensate.heat.v1")
    assert "114°F" in t["why"] and "unknown" in t["why"] and "Chandler" in t["why"]
    assert t["provenance"] == "SIMULATED" and t["bucket"] == "do_now" and t["priority"] == "high"
    assert t["coverage_note_key"] == "water_sudden_vs_gradual" and "HO_WATER_SUDDEN" in t["coverage_codes"]
    assert any(a.startswith("alert-") for a in summary["alerts"])
    assert engine.outbox.outbox, "email goes to the console outbox in dev mode"


def test_live_forecast_alone_triggers_without_nws_alert(env):
    engine, _, weather, _ = run(env, "acct-p1")
    weather.set_days("loc-p1", hi=112.0, lo=88.0)
    engine.evaluate_account("acct-p1")
    assert "ho.condensate.heat" in rule_ids(engine, "acct-p1")
    t = next(t for t in engine.tasks("acct-p1", "open") if "condensate" in t["rule_id"])
    assert t["provenance"] == "LIVE"


def test_recent_condensate_service_suppresses_heat_task(env):
    engine, store, weather = env
    a = store.get("assets", "ast-p1-ac")
    a["last_service_date"] = "2026-09-01"
    store.put("assets", "ast-p1-ac", a)
    weather.set_days("loc-p1", hi=114.0, lo=90.0)
    engine.evaluate_account("acct-p1")
    assert "ho.condensate.heat" not in rule_ids(engine, "acct-p1")


def test_storm_and_flash_flood_for_saguaro_grill(env):
    engine, _, weather = env
    weather.alerts["loc-p3"] = [alert("Severe Thunderstorm Warning", sim=True), alert("Flash Flood Warning", sim=True)]
    weather.set_days("loc-p3", hi=98.0, lo=78.0)
    engine.evaluate_account("acct-p3")
    ids = rule_ids(engine, "acct-p3")
    assert "bop.monsoon_roof_drains" in ids and "bop.wet_floor_response" in ids and "bop.flash_flood_readiness" in ids
    assert "bop.condensate_heat" not in ids
    wet = next(t for t in engine.tasks("acct-p3", "open") if "wet_floor" in t["rule_id"])
    assert wet["coverage_note_key"] == "slip_fall_liability"
    flood = next(t for t in engine.tasks("acct-p3", "open") if "flash_flood" in t["rule_id"])
    assert flood["coverage_note_key"] == "flood_exclusion" and "EX_FLOOD" in flood["coverage_codes"]


def test_freeze_for_flagstaff_sprinkler_rule_and_not_for_desert_stores(env):
    engine, _, weather = env
    weather.alerts["loc-p4"] = [alert("Freeze Warning", sim=True)]
    weather.set_days("loc-p4", hi=31.0, lo=18.0)
    engine.evaluate_account("acct-p4")
    engine.evaluate_account("acct-p3")
    p4 = next(t for t in engine.tasks("acct-p4", "open") if "freeze_sprinkler" in t["rule_id"])
    assert "18°F" in p4["why"] and p4["bucket"] == "do_now"
    assert "bop.freeze_sprinkler_40f" not in rule_ids(engine, "acct-p3")


def test_ho_freeze_only_applies_at_high_elevation(env):
    engine, _, weather = env
    weather.set_days("loc-p1", hi=40.0, lo=20.0)  # Chandler (1,220 ft): rule must not apply
    engine.evaluate_account("acct-p1")
    assert "ho.freeze_high_country" not in rule_ids(engine, "acct-p1")


def test_holiday_closure_via_time_travel_for_ponderosa(env):
    engine, store, _ = env
    store.put("scenario_state", "active", {"injections": [], "fake_now": "2026-12-20T17:00:00+00:00"})
    engine.evaluate_account("acct-p4")
    t = next(t for t in engine.tasks("acct-p4", "open") if "holiday_closure" in t["rule_id"])
    assert "Christmas closure" in t["why"] and "December 24" in t["why"]


def test_monsoon_season_time_travel_july_18(env):
    engine, store, _ = env
    store.put("scenario_state", "active", {"injections": [], "fake_now": "2026-07-18T17:00:00+00:00"})
    engine.evaluate_account("acct-p6")
    assert "ag.monsoon_outage_spoilage" in rule_ids(engine, "acct-p6")
    # Maya already completed her monsoon prep on 2026-06-06, so cooldown correctly suppresses a repeat.
    engine.evaluate_account("acct-p1")
    assert "ho.monsoon_roof_gutters" not in rule_ids(engine, "acct-p1")


def test_upper_unit_leak_creates_check_below_task(env):
    engine, store, _ = env
    store.put("events", "e1", {"id": "e1", "location_id": "loc-p5", "kind": "water_leak", "unit_label": "3B",
                               "at": (NOW - timedelta(minutes=5)).isoformat(), "source": "sensor", "simulated": True})
    engine.evaluate_account("acct-p5")
    t = next(t for t in engine.tasks("acct-p5", "open") if "upper_leak" in t["rule_id"])
    assert t["title"] == "Leak in 3B — check unit 2B below" and "2B" in " ".join(t["steps"])
    assert t["provenance"] == "SIMULATED"


def test_unit_register_rule_fires_when_fields_missing(env):
    engine, store, _ = env
    u = store.get("assets", "ast-p5-u1A")
    u["attributes"]["water_heater_year"] = None
    store.put("assets", "ast-p5-u1A", u)
    engine.evaluate_account("acct-p5")
    t = next(t for t in engine.tasks("acct-p5", "open") if "unit_register" in t["rule_id"])
    assert "1 of 48" in t["why"]


def test_completed_task_is_not_recreated_during_cooldown(env):
    engine, *_ = env
    engine.evaluate_account("acct-p1")
    t = next(t for t in engine.tasks("acct-p1", "open") if "hose_age" in t["rule_id"])
    done = engine.complete(t["id"], "E0")
    assert done["status"] == "done" and done["proof"][0]["sha256"] and len(done["proof"][0]["sha256"]) == 64
    engine.evaluate_account("acct-p1")
    assert "ho.hose_age" not in rule_ids(engine, "acct-p1")
    assert len(engine.tasks("acct-p1", "done")) == 1


def test_completion_rejects_unaccepted_proof_level(env):
    engine, *_ = env
    engine.evaluate_account("acct-p1")
    t = next(t for t in engine.tasks("acct-p1", "open") if "hose_age" in t["rule_id"])
    with pytest.raises(ValueError):
        engine.complete(t["id"], "E4")


def test_defer_hides_task_then_reopens(env):
    engine, store, _ = env
    engine.evaluate_account("acct-p1")
    t = next(t for t in engine.tasks("acct-p1", "open") if "know_shutoff" in t["rule_id"])
    engine.defer(t["id"], hours=24)
    engine.evaluate_account("acct-p1")
    assert "ho.know_shutoff" not in rule_ids(engine, "acct-p1")
    store.put("scenario_state", "active", {"injections": [], "fake_now": (NOW + timedelta(hours=30)).isoformat()})
    engine.evaluate_account("acct-p1")
    assert "ho.know_shutoff" in rule_ids(engine, "acct-p1")


def test_decline_is_private_and_blocks_recreation(env):
    engine, *_ = env
    engine.evaluate_account("acct-p1")
    t = next(t for t in engine.tasks("acct-p1", "open") if "know_shutoff" in t["rule_id"])
    d = engine.decline(t["id"])
    assert d["visibility"] == "private" and d["status"] == "declined"
    engine.evaluate_account("acct-p1")
    assert "ho.know_shutoff" not in rule_ids(engine, "acct-p1")


def test_task_expires_when_trigger_gone_after_window(env):
    engine, store, weather = env
    weather.set_days("loc-p1", hi=114.0, lo=90.0)
    engine.evaluate_account("acct-p1")
    assert "ho.condensate.heat" in rule_ids(engine, "acct-p1")
    weather.set_days("loc-p1")  # calm again
    engine.evaluate_account("acct-p1")
    assert "ho.condensate.heat" in rule_ids(engine, "acct-p1"), "still within expires_after_hours"
    store.put("scenario_state", "active", {"injections": [], "fake_now": (NOW + timedelta(hours=100)).isoformat()})
    engine.evaluate_account("acct-p1")
    assert "ho.condensate.heat" not in rule_ids(engine, "acct-p1")
    assert "ho.condensate.heat" in rule_ids(engine, "acct-p1", "expired")


def test_weather_outage_does_not_break_engine(env):
    engine, _, weather = env
    weather.fail = True
    s = engine.evaluate_account("acct-p1")
    assert s["weather_errors"]
    assert rule_ids(engine, "acct-p1") == ["ho.hose_age", "ho.know_shutoff", "ho.water_heater_age"]


def test_reevaluation_is_idempotent(env):
    engine, *_ = env
    engine.evaluate_account("acct-p5")
    first = {t["id"] for t in engine.tasks("acct-p5", "open")}
    s = engine.evaluate_account("acct-p5")
    assert not s["created"] and {t["id"] for t in engine.tasks("acct-p5", "open")} == first


def test_alerts_are_deduplicated(env):
    engine, store, weather = env
    weather.alerts["loc-p3"] = [alert("Flash Flood Warning", sim=True)]
    engine.evaluate_account("acct-p3")
    n = len(store.list("alerts", account_id="acct-p3"))
    engine.evaluate_account("acct-p3")
    assert len(store.list("alerts", account_id="acct-p3")) == n and n >= 1


def test_quiet_hours_suppress_email_but_not_critical(env):
    engine, store, weather = env
    store.put("scenario_state", "active", {"injections": [], "fake_now": "2026-10-26T08:00:00+00:00"})  # 01:00 AZ
    weather.alerts["loc-p3"] = [alert("Flash Flood Warning", sev="Severe", sim=True)]
    engine.evaluate_account("acct-p3")
    assert engine.outbox.outbox == []
    weather.alerts["loc-p3"] = [alert("Dust Storm Warning", sev="Extreme", sim=True)]
    engine.evaluate_account("acct-p3")
    assert any("Dust Storm" in m["subject"] for m in engine.outbox.outbox)


def test_playbooks_are_well_formed():
    rules = load_rules()
    assert len(rules) >= 24
    assert all(len(r.steps) >= 3 and r.sources and r.est_minutes for r in rules)
    seed_codes = set()
    import json

    from app.seed import SEED
    for p in json.loads((SEED / "policies.json").read_text()):
        seed_codes |= {x["code"] for k in ("coverages", "endorsements", "exclusions_plain") for x in p[k]}
    notes = {n["key"] for n in json.loads((SEED / "coverage_notes.json").read_text())}
    for r in rules:
        assert set(r.coverage_codes) <= seed_codes, r.id
        assert r.coverage_note_key in notes or r.coverage_note_key is None, r.id
