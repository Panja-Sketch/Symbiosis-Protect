"""Phase 6 DoD: leak -> alert -> action -> sensor-verified -> closed -> recurrence reopens. Uses an explicit clock."""

from datetime import UTC, datetime, timedelta

import pytest
from conftest import FakeWeather

from app.config import Settings
from app.deps import build_container
from app.sense import sim
from app.store import MemoryStore

T0 = datetime(2026, 10, 25, 20, 0, 0, tzinfo=UTC)


def s(sec):
    return T0 + timedelta(seconds=sec)


@pytest.fixture
def env():
    c = build_container(Settings(scheduler_enabled=False), MemoryStore(), weather=FakeWeather())
    c.store.put("scenario_state", "active", {"injections": [], "fake_now": T0.isoformat()})
    return c


def device(c, id):
    return c.store.get("devices", id)


def start_leak(c, dev="dev-p5-3b", scenario="slow_leak", fix_works=True):
    c.sense.connect(dev, T0)
    sim.set_scenario(c.store, device(c, dev), scenario, T0, fix_works)
    return c.sense.poll(dev, s(40))["case"]


def open_tasks(c, acct):
    return [t for t in c.store.list("tasks", account_id=acct) if t["status"] == "open"]


def test_simulated_readings_are_deterministic_and_labelled(env):
    env.sense.connect("dev-p5-3b", T0)
    a = sim.readings(env.store, "dev-p5-3b", T0 - timedelta(minutes=5))
    assert len(a) == 11 and all(r["provenance"] == "SIMULATED" and r["leak"] == 0 and r["flow_lpm"] < 0.3 for r in a)
    other = build_container(Settings(scheduler_enabled=False), MemoryStore(), weather=FakeWeather())
    other.sense.connect("dev-p5-3b", T0)
    b = sim.readings(other.store, "dev-p5-3b", T0 - timedelta(minutes=5))
    assert [r["flow_lpm"] for r in a] == [r["flow_lpm"] for r in b]


def test_disconnected_device_is_not_polled(env):
    assert env.sense.poll("dev-p5-3b", s(60))["new_readings"] == 0
    assert sim.readings(env.store, "dev-p5-3b", T0 - timedelta(days=1)) == []


def test_normal_readings_never_open_a_case(env):
    env.sense.connect("dev-p5-3b", T0)
    assert env.sense.poll("dev-p5-3b", s(600))["case"] is None


def test_leak_opens_case_alert_task_and_check_below_task(env):
    case = start_leak(env)
    assert case["state"] == "alerted" and case["kind"] == "leak" and case["unit_label"] == "3B"
    assert [e["state"] for e in case["timeline"]] == ["detected", "alerted"]
    tasks = open_tasks(env, "acct-p5")
    t = next(t for t in tasks if t["rule_id"] == "az.sense.leak.v1")
    assert "Unit 3B" in t["title"] and t["provenance"] == "SIMULATED" and t["proof_accepted"] == ["E4"] and t["bucket"] == "do_now"
    below = next(t for t in tasks if t["rule_id"] == "az.cre.upper_leak_notify_below.v1")
    assert below["title"] == "Leak in 3B — check unit 2B below"
    alerts = [a for a in env.store.list("alerts", account_id="acct-p5") if a["kind"] == "device"]
    assert alerts and alerts[0]["severity"] == "critical" and alerts[0]["provenance"] == "SIMULATED"


def test_full_closed_loop_verified_then_recurrence_reopens(env):
    case = start_leak(env)
    cid = case["id"]
    env.sense.shutoff(cid, s(45))
    assert env.store.get("cases", cid)["state"] == "acting"
    env.sense.poll("dev-p5-3b", s(55))
    flows = [r["flow_lpm"] for r in sim.readings(env.store, "dev-p5-3b", s(46))]
    assert flows and max(flows) == 0.0, "closing the valve stops the flow"
    env.sense.report_fix(cid, s(60))
    assert env.sense.poll("dev-p5-3b", s(70))["case"]["state"] == "verifying", "a wet sensor must not verify yet"
    final = env.sense.poll("dev-p5-3b", s(125))["case"]
    assert final["state"] == "verified" and final["manifest_sha256"] and len(final["manifest_sha256"]) == 64
    sensor_task = next(t for t in env.store.list("tasks", account_id="acct-p5") if t["rule_id"] == "az.sense.leak.v1")
    assert sensor_task["status"] == "done" and sensor_task["proof"][0]["level"] == "E4" and sensor_task["proof"][0]["type"] == "sensor"
    assert sensor_task["proof"][0]["sha256"] == final["manifest_sha256"]
    ev = env.store.get("case_evidence", cid)
    assert len(ev["manifest"]["readings"]) == 6 and all(r["leak"] == 0 for r in ev["manifest"]["readings"])
    assert final["timeline"][-1]["state"] == "verified"
    # recurrence inside the 24 h watch window reopens the same case with a fresh task
    sim.set_scenario(env.store, device(env, "dev-p5-3b"), "slow_leak", s(300))
    re = env.sense.poll("dev-p5-3b", s(340))["case"]
    assert re["id"] == cid and re["state"] == "reopened" and re["reopen_count"] == 1
    again = [t for t in open_tasks(env, "acct-p5") if t["rule_id"] == "az.sense.leak.v1"]
    assert len(again) == 1 and "Leak returned" in again[0]["title"]


def test_failed_fix_is_not_improving_never_verified(env):
    case = start_leak(env, fix_works=False)
    env.sense.report_fix(case["id"], s(60))
    out = env.sense.poll("dev-p5-3b", s(120))["case"]
    assert out["state"] == "not_improving"
    assert not any(e["state"] == "verified" for e in out["timeline"])
    assert next(t for t in env.store.list("tasks", account_id="acct-p5") if t["rule_id"] == "az.sense.leak.v1")["status"] == "open"
    sim.set_scenario(env.store, device(env, "dev-p5-3b"), "recovery", s(130))  # a real second fix this time
    env.sense.report_fix(case["id"], s(130))
    assert env.sense.poll("dev-p5-3b", s(200))["case"]["state"] == "verified"


def test_stale_data_is_inconclusive_not_verified(env):
    case = start_leak(env)
    env.sense.report_fix(case["id"], s(60))
    out = env.sense.poll("dev-p5-3b", s(60 + 3 * 3600))["case"]  # the device went quiet for hours
    assert out["state"] == "inconclusive" and out["manifest_sha256"] is None
    assert "stale" in out["timeline"][-1]["note"]


def test_cannot_report_fix_twice_or_for_unknown_case(env):
    case = start_leak(env)
    env.sense.report_fix(case["id"], s(60))
    with pytest.raises(ValueError):
        env.sense.report_fix(case["id"], s(61))
    with pytest.raises(KeyError):
        env.sense.shutoff("nope", s(1))


def test_burst_detected_for_homeowner_with_shutoff(env):
    c = env
    c.sense.connect("dev-p1-main", T0)
    sim.set_scenario(c.store, device(c, "dev-p1-main"), "burst", T0)
    case = c.sense.poll("dev-p1-main", s(20))["case"]
    assert case["state"] == "alerted" and case["unit_label"] is None
    c.sense.shutoff(case["id"], s(25))
    c.sense.poll("dev-p1-main", s(40))
    flows = [r["flow_lpm"] for r in sim.readings(c.store, "dev-p1-main", s(26))]
    assert flows and max(flows) == 0.0
    assert "az.cre.upper_leak_notify_below.v1" not in [t["rule_id"] for t in open_tasks(c, "acct-p1")], "no 'below' task for a house"


def test_device_without_valve_refuses_shutoff(env):
    env.sense.connect("dev-p1-laundry", T0)
    sim.set_scenario(env.store, device(env, "dev-p1-laundry"), "burst", T0)
    case = env.sense.poll("dev-p1-laundry", s(20))["case"]
    with pytest.raises(ValueError):
        env.sense.shutoff(case["id"], s(25))


def test_freeze_probe_and_cooler_probe_cases(env):
    env.sense.connect("dev-p4-riser", T0)
    sim.set_scenario(env.store, device(env, "dev-p4-riser"), "freeze_drop", T0)
    f = env.sense.poll("dev-p4-riser", s(60))["case"]
    assert f["kind"] == "freeze_risk"
    assert "Stockroom" in next(t["title"] for t in open_tasks(env, "acct-p4") if "freeze_risk" in t["rule_id"])
    env.sense.connect("dev-p6-cooler1", T0)
    sim.set_scenario(env.store, device(env, "dev-p6-cooler1"), "cooler_drift", T0)
    k = env.sense.poll("dev-p6-cooler1", s(120))["case"]
    assert k["kind"] == "cooler_temp" and k["state"] == "alerted"
    env.sense.report_fix(k["id"], s(125))
    assert env.sense.poll("dev-p6-cooler1", s(200))["case"]["state"] == "verified"


def test_scenario_must_match_device_kind(env):
    env.sense.connect("dev-p6-cooler1", T0)
    with pytest.raises(ValueError):
        sim.set_scenario(env.store, device(env, "dev-p6-cooler1"), "burst", T0)
