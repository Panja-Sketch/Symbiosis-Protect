"""Phase 7 DoD: role switch shows consistent data; private items are hidden from the underwriter; evidence export verifies."""

import base64
import hashlib
import io
import json
import zipfile

import pytest
from conftest import FakeWeather
from fastapi.testclient import TestClient

from app.adapters.storage import LocalStorage
from app.config import Settings
from app.deps import build_container
from app.main import create_app
from app.store import MemoryStore

PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")
UW = {"X-Demo-Role": "underwriter"}
AG = {"X-Demo-Role": "agent"}


@pytest.fixture
def client(tmp_path):
    c = build_container(Settings(scheduler_enabled=False), MemoryStore(), weather=FakeWeather(), storage=LocalStorage(tmp_path / "b"))
    app = create_app()
    import app.routes.v1 as v1

    app.dependency_overrides[v1.C] = lambda: c
    tc = TestClient(app)
    for i in range(1, 7):
        tc.post(f"/api/v1/accounts/acct-p{i}/evaluate")
    return tc, c


def open_tasks(tc, acct):
    return tc.get(f"/api/v1/accounts/{acct}/tasks?status=open").json()["tasks"]


def test_role_gates(client):
    tc, _ = client
    assert tc.get("/api/v1/agent/book").status_code == 403
    assert tc.get("/api/v1/agent/book", headers=UW).status_code == 403
    assert tc.get("/api/v1/underwriting/portfolio", headers=AG).status_code == 403
    assert tc.get("/api/v1/agent/book", headers=AG).status_code == 200
    assert tc.get("/api/v1/underwriting/portfolio", headers=UW).status_code == 200
    assert tc.get("/api/v1/agent/book", headers={"X-Demo-Role": "hacker"}).status_code == 400
    valid = {"account_id": "acct-p1", "title": "A valid title here", "why": "A valid reason here.", "steps": ["do it"]}
    assert tc.post("/api/v1/tasks/issue", json=valid).status_code == 403


def test_private_open_tasks_are_hidden_from_underwriter_and_agent(client):
    tc, _ = client
    luis = tc.get("/api/v1/underwriting/accounts/acct-p2", headers=UW).json()
    assert luis["tasks"] == [], "Luis shares nothing by default, so no task is visible"
    assert luis["row"]["open_high_priority"] == [] and luis["row"]["shares_by_default"] is False
    assert len(open_tasks(tc, "acct-p2")) >= 3, "but the policyholder still has all of them"
    maya = tc.get("/api/v1/underwriting/accounts/acct-p1", headers=AG).json()
    assert {t["id"] for t in maya["tasks"]} == {t["id"] for t in open_tasks(tc, "acct-p1")}


def test_toggling_visibility_changes_what_underwriter_sees_including_proofs(client):
    tc, _ = client
    t = next(t for t in open_tasks(tc, "acct-p2") if "hose" in t["rule_id"])
    assert tc.patch(f"/api/v1/tasks/{t['id']}/visibility", json={"visibility": "shared"}).status_code == 200
    seen = tc.get("/api/v1/underwriting/accounts/acct-p2", headers=UW).json()
    assert [x["id"] for x in seen["tasks"]] == [t["id"]]
    tc.post(f"/api/v1/tasks/{t['id']}/complete", data={"level": "E1"}, files={"file": ("h.png", PNG, "image/png")})
    seen = tc.get("/api/v1/underwriting/accounts/acct-p2", headers=UW).json()
    assert len(seen["proofs"]) == 1 and "uri" not in seen["proofs"][0] and seen["proofs"][0]["level"] == "E1"
    tc.patch(f"/api/v1/tasks/{t['id']}/visibility", json={"visibility": "private"})
    seen = tc.get("/api/v1/underwriting/accounts/acct-p2", headers=UW).json()
    assert seen["tasks"] == [] and seen["proofs"] == []


def test_declined_tasks_are_never_visible_and_cannot_be_shared(client):
    tc, _ = client
    t = open_tasks(tc, "acct-p1")[0]
    tc.post(f"/api/v1/tasks/{t['id']}/decline")
    assert t["id"] not in [x["id"] for x in tc.get("/api/v1/underwriting/accounts/acct-p1", headers=UW).json()["tasks"]]
    assert tc.patch(f"/api/v1/tasks/{t['id']}/visibility", json={"visibility": "shared"}).status_code == 409
    book = tc.get("/api/v1/agent/book", headers=AG).json()
    assert t["title"] not in json.dumps(book)


def test_portfolio_tiles(client):
    tc, _ = client
    p = tc.get("/api/v1/underwriting/portfolio", headers=UW).json()
    tiles = p["tiles"]
    assert tiles["participation"] == {"participating": 5, "total": 6, "pct": 83}
    assert tiles["task_completion"]["applicable"] > 0 and 0 <= tiles["task_completion"]["pct"] <= 100
    assert set(tiles["proof_mix"]) >= {"E1", "E2", "E3"}  # from seeded shared history
    assert len(p["accounts"]) == 6 and p["provenance"] == "SYNTHETIC"
    assert "private" in p["visibility_note"].lower()


def test_portfolio_excludes_luis_private_history_from_mix(client):
    tc, _ = client
    luis = tc.get("/api/v1/underwriting/accounts/acct-p2", headers=UW).json()
    assert luis["history"] == [] or all(h["visibility"] == "shared" for h in luis["history"])
    assert luis["row"]["proof_mix"] == {}


def test_insurer_issued_task_reaches_policyholder_and_is_never_capped(client):
    tc, c = client
    before = [t for t in open_tasks(tc, "acct-p1") if t["bucket"] == "do_now"]
    assert len(before) == 3
    r = tc.post("/api/v1/tasks/issue", headers=UW, json={
        "account_id": "acct-p1", "title": "Install a water-leak sensor at the water heater",
        "why": "Risk control recommends early leak detection near the water heater.", "steps": ["Place the sensor in the drain pan.", "Test it."],
        "priority": "high"})
    assert r.status_code == 200 and r.json()["source"] == "insurer" and r.json()["visibility"] == "shared"
    after = open_tasks(tc, "acct-p1")
    do_now = [t for t in after if t["bucket"] == "do_now"]
    assert len(do_now) == 4 and sum(t["source"] == "rule" for t in do_now) == 3, "cap applies to rule tasks only"
    assert any(a["kind"] == "agent" and "insurer" in a["title"] for a in tc.get("/api/v1/alerts", params={"account_id": "acct-p1"}).json())
    # re-evaluation must not expire or duplicate it
    tc.post("/api/v1/accounts/acct-p1/evaluate")
    assert len([t for t in open_tasks(tc, "acct-p1") if t["source"] == "insurer"]) == 1
    # insurer items cannot be made private by the policyholder
    assert tc.patch(f"/api/v1/tasks/{r.json()['id']}/visibility", json={"visibility": "private"}).status_code == 409
    # and the underwriter sees it
    assert any(t["source"] == "insurer" for t in tc.get("/api/v1/underwriting/accounts/acct-p1", headers=UW).json()["tasks"])


def test_issue_validation(client):
    tc, _ = client
    bad = {"account_id": "acct-p1", "title": "x", "why": "short", "steps": []}
    assert tc.post("/api/v1/tasks/issue", headers=UW, json=bad).status_code == 422
    ok = {"account_id": "nope", "title": "A valid title here", "why": "A valid reason here.", "steps": ["do it"]}
    assert tc.post("/api/v1/tasks/issue", headers=UW, json=ok).status_code == 404


def test_agent_book_content(client):
    tc, _ = client
    tc.post("/api/v1/director/inject", json={"kind": "heat_phoenix"})
    book = tc.get("/api/v1/agent/book", headers=AG).json()
    by = {c["persona_id"]: c for c in book["clients"]}
    assert set(by) == {"P1", "P2", "P3", "P4", "P5", "P6"}
    assert by["P1"]["exposure"]["active_alerts"][0]["provenance"] == "SIMULATED" and by["P1"]["exposure"]["high_risk_days"]
    assert by["P4"]["exposure"]["active_alerts"] == []
    assert any("Water backup" in p for p in by["P1"]["renewal_points"])
    assert any("claim" in p.lower() for p in by["P5"]["renewal_points"])
    only_agent_1 = tc.get("/api/v1/agent/book?agent_id=agent-3", headers=AG).json()["clients"]
    assert [c["persona_id"] for c in only_agent_1] == ["P4"]


def test_evidence_export_zip_is_verifiable_and_scoped(client):
    tc, _ = client
    t = next(t for t in open_tasks(tc, "acct-p1") if "hose" in t["rule_id"])
    done = tc.post(f"/api/v1/tasks/{t['id']}/complete", data={"level": "E1"}, files={"file": ("hoses.png", PNG, "image/png")}).json()
    proof = done["proof"][0]
    r = tc.post("/api/v1/evidence/pol-p1/export", headers=UW)
    assert r.status_code == 200 and r.headers["content-type"] == "application/zip"
    z = zipfile.ZipFile(io.BytesIO(r.content))
    manifest_bytes = z.read("manifest.json")
    assert hashlib.sha256(manifest_bytes).hexdigest() == r.headers["x-manifest-sha256"]
    assert z.read("manifest.sha256").decode().split()[0] == r.headers["x-manifest-sha256"]
    manifest = json.loads(manifest_bytes)
    assert manifest["scope"] == "shared_only" and manifest["created_by_role"] == "underwriter"
    for f in manifest["files"]:
        assert hashlib.sha256(z.read(f["path"])).hexdigest() == f["sha256"], f["path"]
    photo = next(f for f in manifest["files"] if f["path"].startswith("proof_files/"))
    assert photo["sha256"] == proof["sha256"] == hashlib.sha256(PNG).hexdigest()
    pkgs = tc.get("/api/v1/underwriting/accounts/acct-p1", headers=UW).json()["packages"]
    assert pkgs[0]["manifest_sha256"] == r.headers["x-manifest-sha256"]
    again = tc.get(f"/api/v1/evidence/packages/{r.headers['x-package-id']}/download")
    assert again.status_code == 200 and again.content == r.content


def test_underwriter_export_leaves_out_private_files(client):
    tc, _ = client
    t = next(t for t in open_tasks(tc, "acct-p2") if "hose" in t["rule_id"])  # Luis keeps everything private
    tc.post(f"/api/v1/tasks/{t['id']}/complete", data={"level": "E1"}, files={"file": ("secret.png", PNG, "image/png")})
    uw = zipfile.ZipFile(io.BytesIO(tc.post("/api/v1/evidence/pol-p2/export", headers=UW).content))
    assert not [n for n in uw.namelist() if n.startswith("proof_files/")]
    assert "hose" not in uw.read("tasks.json").decode().lower()
    own = zipfile.ZipFile(io.BytesIO(tc.post("/api/v1/evidence/pol-p2/export").content))
    assert [n for n in own.namelist() if n.startswith("proof_files/")], "the owner's own export includes everything"
    assert json.loads(own.read("manifest.json"))["scope"] == "all"


def test_sense_case_evidence_is_included_when_shared(client):
    tc, c = client
    from datetime import UTC, datetime, timedelta

    from app.sense import sim

    t0 = datetime.now(UTC)
    c.sense.connect("dev-p5-3b", t0 - timedelta(seconds=200))
    sim.set_scenario(c.store, c.store.get("devices", "dev-p5-3b"), "slow_leak", t0 - timedelta(seconds=150))
    case = c.sense.poll("dev-p5-3b", t0 - timedelta(seconds=110))["case"]
    c.sense.report_fix(case["id"], t0 - timedelta(seconds=100))
    assert c.sense.poll("dev-p5-3b", t0 - timedelta(seconds=30))["case"]["state"] == "verified"
    z = zipfile.ZipFile(io.BytesIO(tc.post("/api/v1/evidence/pol-p5/export", headers=UW).content))
    case_files = [n for n in z.namelist() if n.startswith("cases/")]
    assert case_files and json.loads(z.read(case_files[0]))["evidence"]["manifest_sha256"] == c.store.get("cases", case["id"])["manifest_sha256"]


def test_preferences_and_share_default_apply_to_new_tasks(client):
    tc, c = client
    assert tc.patch("/api/v1/accounts/acct-p3/preferences", json={"share_default": False}).json()["share_default"] is False
    for t in c.store.list("tasks", account_id="acct-p3"):
        c.store.delete("tasks", t["id"])
    tc.post("/api/v1/accounts/acct-p3/evaluate")
    fresh = open_tasks(tc, "acct-p3")
    assert fresh and all(t["visibility"] == "private" for t in fresh)
    assert tc.get("/api/v1/underwriting/accounts/acct-p3", headers=UW).json()["tasks"] == []
    assert tc.patch("/api/v1/accounts/acct-p3/preferences", json={"channels": []}).status_code == 422
    assert tc.patch("/api/v1/accounts/acct-p3/preferences", json={"channels": ["sms"]}).status_code == 422
