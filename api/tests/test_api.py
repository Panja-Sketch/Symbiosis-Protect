import pytest
from conftest import FakeWeather
from fastapi.testclient import TestClient

from app.config import Settings
from app.deps import build_container
from app.main import create_app
from app.store import MemoryStore


@pytest.fixture
def client():
    weather = FakeWeather()
    c = build_container(Settings(scheduler_enabled=False, demo_mode=True), MemoryStore(), weather=weather)
    app = create_app()
    app.dependency_overrides = {}
    import app.routes.v1 as v1

    app.dependency_overrides[v1.C] = lambda: c
    # Scenario provider sits in front of the fake weather; fake_now is unset so real "now" is used.
    return TestClient(app), c, weather


def test_personas_and_policy(client):
    tc, *_ = client
    p = tc.get("/api/v1/personas").json()
    assert [x["persona_id"] for x in p] == ["P1", "P2", "P3", "P4", "P5", "P6"]
    assert p[0]["preview_flag"] and not p[2]["preview_flag"]
    pol = tc.get("/api/v1/policies/pol-p1").json()
    assert pol["coverages"] and "water_sudden_vs_gradual" in pol["coverage_notes"]
    assert tc.get("/api/v1/accounts/nope").status_code == 404


def test_history_endpoint_is_labelled_historic(client):
    tc, *_ = client
    h = tc.get("/api/v1/locations/loc-p4/history").json()
    assert h["provenance"] == "HISTORIC" and h["weather"]["avg_per_year"]["nights_le_28f"] > 30
    assert h["risk_index"]["hazards"]["CWAV"]["eal_rating"]


def test_tasks_flow_complete_defer_decline(client):
    tc, c, _ = client
    assert tc.post("/api/v1/accounts/acct-p1/evaluate").status_code == 200
    body = tc.get("/api/v1/accounts/acct-p1/tasks?status=do_now").json()
    assert len(body["tasks"]) == 3 and body["readiness"]["done"] == 0
    t1, t2, t3 = body["tasks"]
    r = tc.post(f"/api/v1/tasks/{t1['id']}/complete", json={"level": "E0"})
    assert r.status_code == 200 and r.json()["status"] == "done"
    assert tc.post(f"/api/v1/tasks/{t1['id']}/complete", json={"level": "E0"}).status_code == 409
    assert tc.post(f"/api/v1/tasks/{t2['id']}/defer", json={"hours": 2}).json()["status"] == "deferred"
    assert tc.post(f"/api/v1/tasks/{t3['id']}/decline").json()["status"] == "declined"
    done = tc.get("/api/v1/accounts/acct-p1/tasks?status=done").json()
    assert len(done["tasks"]) == 1 and done["history"], "seeded history is returned alongside live tasks"
    ready = tc.get("/api/v1/accounts/acct-p1/tasks").json()["readiness"]
    assert ready["done"] == 1


def test_complete_rejects_unaccepted_level(client):
    tc, *_ = client
    tc.post("/api/v1/accounts/acct-p1/evaluate")
    t = tc.get("/api/v1/accounts/acct-p1/tasks?status=open").json()["tasks"][0]
    assert tc.post(f"/api/v1/tasks/{t['id']}/complete", json={"level": "E4"}).status_code == 409
    assert tc.post("/api/v1/tasks/missing/complete", json={}).status_code == 404


def test_director_inject_creates_simulated_tasks_alerts_and_ribbon(client):
    tc, c, weather = client
    r = tc.post("/api/v1/director/inject", json={"kind": "heat_phoenix"})
    assert r.status_code == 200 and r.json()["provenance"] == "SIMULATED"
    tasks = tc.get("/api/v1/accounts/acct-p1/tasks?status=open").json()["tasks"]
    cond = next(t for t in tasks if t["rule_id"] == "az.ho.condensate.heat.v1")
    assert cond["provenance"] == "SIMULATED" and "114" in cond["why"]
    alerts = tc.get("/api/v1/alerts", params={"account_id": "acct-p1"}).json()
    assert any(a["provenance"] == "SIMULATED" and "Extreme Heat" in a["title"] for a in alerts)
    rib = tc.get("/api/v1/locations/loc-p1/risk-ribbon").json()
    assert rib["provenance"] == "SIMULATED" and rib["days"][0]["risk"] == "high" and len(rib["days"]) == 7
    assert any(d["task_pins"] for d in rib["days"])
    # alert read
    a = alerts[0]
    assert tc.post(f"/api/v1/alerts/{a['id']}/read").json()["read_at"]
    # reset clears simulation
    tc.post("/api/v1/director/reset")
    assert not [t for t in tc.get("/api/v1/accounts/acct-p1/tasks?status=open").json()["tasks"]
                if t["rule_id"] == "az.ho.condensate.heat.v1"]


def test_director_unknown_scenario_and_demo_mode_gate(client):
    tc, c, _ = client
    assert tc.post("/api/v1/director/inject", json={"kind": "nope"}).status_code == 422
    c.settings.demo_mode = False
    from app.config import get_settings

    get_settings().demo_mode = False
    try:
        assert tc.post("/api/v1/director/reset").status_code == 404
    finally:
        get_settings().demo_mode = True


def test_time_travel_changes_engine_clock(client):
    tc, *_ = client
    r = tc.post("/api/v1/director/time-travel", json={"to": "2026-07-18T17:00:00+00:00"})
    assert r.status_code == 200
    w = tc.get("/api/v1/locations/loc-p1/weather").json()
    assert w["provenance"] == "SIMULATED" and w["now_local"].startswith("2026-07-18")
    assert w["daily"][0]["date"] == "2026-07-18"
    tc.post("/api/v1/director/time-travel", json={"to": None})


def test_weather_unavailable_returns_error_not_500(client):
    tc, _, weather = client
    weather.fail = True
    r = tc.get("/api/v1/locations/loc-p1/weather")
    assert r.status_code == 200 and r.json()["error"]
    assert tc.get("/api/v1/locations/loc-p1/risk-ribbon").status_code == 200


def test_internal_evaluate_requires_token_outside_demo(client):
    tc, c, _ = client
    from app.config import get_settings

    s = get_settings()
    s.demo_mode = False
    try:
        assert tc.post("/api/v1/internal/evaluate").status_code == 401
        ok = tc.post("/api/v1/internal/evaluate", headers={"x-scheduler-token": s.session_secret})
        assert ok.status_code == 200 and len(ok.json()["evaluated"]) == 6
    finally:
        s.demo_mode = True


def test_patch_asset_updates_tasks(client):
    tc, *_ = client
    tc.post("/api/v1/accounts/acct-p1/evaluate")
    before = [t["rule_id"] for t in tc.get("/api/v1/accounts/acct-p1/tasks?status=open").json()["tasks"]]
    assert "az.ho.water_heater_age.v1" in before
    r = tc.patch("/api/v1/assets/ast-p1-wh", json={"install_year": 2024})
    assert r.status_code == 200 and r.json()["asset"]["install_year"] == 2024
    assert tc.patch("/api/v1/assets/ast-p1-wh", json={"install_year": 1800}).status_code == 422
    assert tc.patch("/api/v1/assets/nope", json={}).status_code == 404
    listing = tc.get("/api/v1/accounts/acct-p1/assets").json()
    assert any(a["id"] == "ast-p1-wh" and a["install_year"] == 2024 for a in listing["assets"])


def test_director_reset_restores_seeded_assets(client):
    tc, *_ = client
    tc.patch("/api/v1/assets/ast-p1-wh", json={"install_year": 2024})
    tc.post("/api/v1/director/reset")
    wh = next(a for a in tc.get("/api/v1/accounts/acct-p1/assets").json()["assets"] if a["id"] == "ast-p1-wh")
    assert wh["install_year"] is None
    ids = [t["rule_id"] for t in tc.get("/api/v1/accounts/acct-p1/tasks?status=open").json()["tasks"]]
    assert "az.ho.water_heater_age.v1" in ids
